"""
Cache multi-backend: Redis (produção) ou Memory (dev).
Circuit Breaker para fontes externas.
"""
import os
import json
import time
import logging
from typing import Optional, Any, Callable
from functools import wraps
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# ============ Cache Backend ============

class MemoryCache:
    """Cache in-memory simples (dev only / fallback)."""
    
    def __init__(self):
        self._store = {}
    
    def get(self, key: str) -> Optional[str]:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if expires_at and time.time() > expires_at:
            del self._store[key]
            return None
        return value
    
    def set(self, key: str, value: str, ttl: int = 300) -> None:
        expires_at = time.time() + ttl if ttl > 0 else None
        self._store[key] = (value, expires_at)
    
    def delete(self, key: str) -> None:
        self._store.pop(key, None)
    
    def flush(self) -> None:
        self._store.clear()
    
    @property
    def backend_name(self) -> str:
        return "memory"


class RedisCache:
    """Cache com Redis (produção)."""
    
    def __init__(self, url: str = "redis://localhost:6379/0"):
        try:
            import redis
            self._client = redis.from_url(url, decode_responses=True, socket_timeout=3)
            self._client.ping()
            self._available = True
            logger.info(f"Redis conectado: {url}")
        except Exception as e:
            logger.warning(f"Redis indisponível ({e}), usando fallback memory cache")
            self._available = False
            self._fallback = MemoryCache()
    
    def get(self, key: str) -> Optional[str]:
        if not self._available:
            return self._fallback.get(key)
        try:
            return self._client.get(key)
        except Exception as e:
            logger.warning(f"Redis GET erro: {e}")
            return self._fallback.get(key) if hasattr(self, '_fallback') else None
    
    def set(self, key: str, value: str, ttl: int = 300) -> None:
        if not self._available:
            if hasattr(self, '_fallback'):
                self._fallback.set(key, value, ttl)
            return
        try:
            self._client.setex(key, ttl, value)
        except Exception as e:
            logger.warning(f"Redis SET erro: {e}")
            if hasattr(self, '_fallback'):
                self._fallback.set(key, value, ttl)
    
    def delete(self, key: str) -> None:
        if not self._available:
            return
        try:
            self._client.delete(key)
        except Exception:
            pass
    
    def flush(self) -> None:
        if not self._available:
            return
        try:
            self._client.flushdb()
        except Exception:
            pass
    
    @property
    def backend_name(self) -> str:
        return "redis" if self._available else "memory (redis fallback)"


def create_cache() -> Any:
    """Factory: cria cache baseado na env var CACHE_BACKEND."""
    backend = os.getenv("CACHE_BACKEND", "memory").lower()
    
    if backend == "redis":
        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        return RedisCache(url)
    
    return MemoryCache()


# Singleton
cache = create_cache()


def cached(key_prefix: str, ttl: int = 300):
    """Decorator para cachear resultado de funções."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Gerar chave com args
            key_parts = [key_prefix]
            for a in args[1:]:  # Skip self
                key_parts.append(str(a))
            for k, v in sorted(kwargs.items()):
                if v is not None:
                    key_parts.append(f"{k}={v}")
            cache_key = ":".join(key_parts)
            
            # Tentar cache
            from src.utils.metrics import metrics
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                metrics.record_cache(hit=True)
                return json.loads(cached_value)
            
            metrics.record_cache(hit=False)
            
            # Executar e cachear
            result = await func(*args, **kwargs)
            try:
                cache.set(cache_key, json.dumps(result, default=str), ttl)
            except (TypeError, ValueError) as e:
                logger.warning(f"Cache serialization error: {e}")
            
            return result
        return wrapper
    return decorator


# ============ Circuit Breaker ============

class CircuitBreaker:
    """
    Circuit breaker para fontes externas.
    
    Estados:
    - CLOSED: requests passam normalmente
    - OPEN: requests falham imediatamente (após N falhas)
    - HALF_OPEN: tenta 1 request para ver se recuperou
    """
    
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"
    
    def __init__(self, name: str, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = self.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.success_count = 0
        self._half_open_lock = False
    
    def can_execute(self) -> bool:
        """Verifica se pode executar request."""
        if self.state == self.CLOSED:
            return True
        
        if self.state == self.OPEN:
            # Verificar se recovery_timeout passou
            if self.last_failure_time and \
               time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = self.HALF_OPEN
                self._half_open_lock = False
                logger.info(f"CircuitBreaker [{self.name}]: OPEN → HALF_OPEN")
                return True
            return False
        
        # HALF_OPEN: permitir apenas 1 request
        if self.state == self.HALF_OPEN and not self._half_open_lock:
            self._half_open_lock = True
            return True
        
        return False
    
    def record_success(self) -> None:
        """Registra sucesso."""
        if self.state == self.HALF_OPEN:
            self.state = self.CLOSED
            self.failure_count = 0
            self.success_count = 0
            logger.info(f"CircuitBreaker [{self.name}]: HALF_OPEN → CLOSED (recuperado)")
        self.success_count += 1
    
    def record_failure(self) -> None:
        """Registra falha."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == self.HALF_OPEN:
            self.state = self.OPEN
            logger.warning(f"CircuitBreaker [{self.name}]: HALF_OPEN → OPEN (falhou no teste)")
            return
        
        if self.failure_count >= self.failure_threshold:
            self.state = self.OPEN
            logger.warning(
                f"CircuitBreaker [{self.name}]: CLOSED → OPEN "
                f"({self.failure_count} falhas consecutivas)"
            )
    
    def get_status(self) -> dict:
        """Retorna status atual do circuit breaker."""
        return {
            "name": self.name,
            "state": self.state,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout_s": self.recovery_timeout,
            "last_failure": datetime.fromtimestamp(self.last_failure_time).isoformat() if self.last_failure_time else None,
            "time_until_retry": max(0, self.recovery_timeout - (time.time() - self.last_failure_time)) if self.last_failure_time and self.state == self.OPEN else 0,
        }


# ============ Circuit Breakers por fonte ============

circuit_breakers = {
    "api_cartola": CircuitBreaker("api_cartola", failure_threshold=5, recovery_timeout=60),
    "football_data": CircuitBreaker("football_data", failure_threshold=3, recovery_timeout=120),
    "fbref": CircuitBreaker("fbref", failure_threshold=3, recovery_timeout=300),
    "api_football": CircuitBreaker("api_football", failure_threshold=3, recovery_timeout=180),
    "ge_globo": CircuitBreaker("ge_globo", failure_threshold=5, recovery_timeout=120),
}


def with_circuit_breaker(source_name: str):
    """Decorator para aplicar circuit breaker a uma função."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cb = circuit_breakers.get(source_name)
            if cb is None:
                return await func(*args, **kwargs)
            
            if not cb.can_execute():
                raise CircuitOpenError(
                    f"Circuit breaker [{source_name}] está ABERTO. "
                    f"Retry em {cb.get_status()['time_until_retry']:.0f}s"
                )
            
            try:
                result = await func(*args, **kwargs)
                cb.record_success()
                return result
            except Exception as e:
                cb.record_failure()
                # Registrar em métricas
                try:
                    from src.utils.metrics import metrics
                    metrics.record_fonte_error(source_name)
                except ImportError:
                    pass
                raise
        return wrapper
    return decorator


class CircuitOpenError(Exception):
    """Exceção quando circuit breaker está aberto."""
    pass
