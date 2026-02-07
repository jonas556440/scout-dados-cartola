"""
Middleware de métricas internas para a API FastAPI.
Rastreia: latência por endpoint, cache hit rate, taxa de erro, requests/min.
Endpoint: GET /api/admin/metrics
"""
import time
import logging
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Coletor de métricas in-memory com janela deslizante de 24h."""
    
    def __init__(self, window_hours: int = 24):
        self.window = timedelta(hours=window_hours)
        # Deques com (timestamp, value) para janela deslizante
        self._requests: deque = deque()
        self._latencies: Dict[str, deque] = defaultdict(deque)
        self._errors: deque = deque()
        self._status_codes: Dict[int, int] = defaultdict(int)
        self._cache_hits: int = 0
        self._cache_misses: int = 0
        self._total_requests: int = 0
        self._fonte_erros: Dict[str, int] = defaultdict(int)
    
    def _cleanup(self, dq: deque) -> None:
        """Remove entradas expiradas da deque."""
        cutoff = datetime.now() - self.window
        while dq and dq[0][0] < cutoff:
            dq.popleft()
    
    def record_request(self, path: str, method: str, status_code: int, latency_ms: float) -> None:
        """Registra uma request completa."""
        now = datetime.now()
        self._requests.append((now, path))
        self._latencies[path].append((now, latency_ms))
        self._status_codes[status_code] += 1
        self._total_requests += 1
        
        if status_code >= 400:
            self._errors.append((now, {"path": path, "status": status_code}))
    
    def record_cache(self, hit: bool) -> None:
        """Registra hit ou miss de cache."""
        if hit:
            self._cache_hits += 1
        else:
            self._cache_misses += 1
    
    def record_fonte_error(self, fonte: str) -> None:
        """Registra erro de uma fonte externa."""
        self._fonte_erros[fonte] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retorna métricas agregadas."""
        now = datetime.now()
        
        # Limpar entradas antigas
        self._cleanup(self._requests)
        self._cleanup(self._errors)
        for path in list(self._latencies.keys()):
            self._cleanup(self._latencies[path])
        
        # Requests nos últimos períodos
        one_min_ago = now - timedelta(minutes=1)
        five_min_ago = now - timedelta(minutes=5)
        
        reqs_1min = sum(1 for ts, _ in self._requests if ts >= one_min_ago)
        reqs_5min = sum(1 for ts, _ in self._requests if ts >= five_min_ago)
        
        # Latências agregadas
        all_latencies = []
        endpoint_stats = {}
        for path, dq in self._latencies.items():
            lats = [v for _, v in dq]
            if lats:
                all_latencies.extend(lats)
                sorted_lats = sorted(lats)
                endpoint_stats[path] = {
                    "count": len(lats),
                    "avg_ms": round(sum(lats) / len(lats), 1),
                    "p50_ms": round(sorted_lats[len(sorted_lats) // 2], 1),
                    "p95_ms": round(sorted_lats[int(len(sorted_lats) * 0.95)], 1) if len(sorted_lats) > 1 else round(sorted_lats[0], 1),
                    "p99_ms": round(sorted_lats[int(len(sorted_lats) * 0.99)], 1) if len(sorted_lats) > 1 else round(sorted_lats[0], 1),
                }
        
        # Latência global
        avg_latency = round(sum(all_latencies) / len(all_latencies), 1) if all_latencies else 0
        
        # Cache hit rate
        total_cache = self._cache_hits + self._cache_misses
        cache_hit_rate = round(self._cache_hits / total_cache, 3) if total_cache > 0 else 0
        
        # Error rate
        error_count_24h = len(self._errors)
        request_count_24h = len(self._requests)
        error_rate = round(error_count_24h / request_count_24h, 4) if request_count_24h > 0 else 0
        
        # Top endpoints por volume
        endpoint_volume = defaultdict(int)
        for _, path in self._requests:
            endpoint_volume[path] += 1
        top_endpoints = sorted(endpoint_volume.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Top endpoints mais lentos
        top_slow = sorted(
            [(path, stats["avg_ms"]) for path, stats in endpoint_stats.items()],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            "timestamp": now.isoformat(),
            "window": f"{self.window.total_seconds() / 3600:.0f}h",
            "total_requests": self._total_requests,
            "requests_24h": request_count_24h,
            "requests_per_min": reqs_1min,
            "requests_5min": reqs_5min,
            "avg_latency_ms": avg_latency,
            "cache_hit_rate": cache_hit_rate,
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "error_rate": error_rate,
            "errors_24h": error_count_24h,
            "status_codes": dict(self._status_codes),
            "fonte_erros": dict(self._fonte_erros),
            "top_endpoints": [{"path": p, "count": c} for p, c in top_endpoints],
            "top_slow_endpoints": [{"path": p, "avg_ms": l} for p, l in top_slow],
            "endpoint_stats": endpoint_stats,
        }


# Instância global
metrics = MetricsCollector()


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware que coleta métricas de cada request."""
    
    async def dispatch(self, request: Request, call_next):
        # Ignorar health checks e static files
        path = request.url.path
        if path in ("/health", "/favicon.ico", "/robots.txt"):
            return await call_next(request)
        
        start = time.perf_counter()
        
        try:
            response = await call_next(request)
            latency_ms = (time.perf_counter() - start) * 1000
            metrics.record_request(path, request.method, response.status_code, latency_ms)
            return response
        except Exception as e:
            latency_ms = (time.perf_counter() - start) * 1000
            metrics.record_request(path, request.method, 500, latency_ms)
            raise
