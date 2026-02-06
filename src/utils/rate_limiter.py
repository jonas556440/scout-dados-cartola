"""
Rate Limiter para FastAPI usando slowapi
=========================================
Protege contra DDoS e abuso de API
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

# Limiter global usando IP do cliente
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/minute"],  # Limite padrão
    storage_uri="memory://",  # Em produção, considerar Redis
    strategy="fixed-window"
)


def get_real_ip(request: Request) -> str:
    """
    Obtém IP real considerando proxies (Cloudflare, nginx).
    Headers verificados em ordem de prioridade.
    """
    # Cloudflare
    cf_ip = request.headers.get("CF-Connecting-IP")
    if cf_ip:
        return cf_ip
    
    # X-Forwarded-For (primeiro IP é o cliente real)
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    
    # X-Real-IP (nginx)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback para IP direto
    return request.client.host if request.client else "127.0.0.1"


# Atualizar limiter para usar IP real
limiter = Limiter(
    key_func=get_real_ip,
    default_limits=["200/minute"],
    storage_uri="memory://",
    strategy="fixed-window"
)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Handler customizado para rate limit excedido"""
    logger.warning(f"Rate limit excedido para IP: {get_real_ip(request)}")
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": "Muitas requisições. Tente novamente em alguns minutos.",
            "retry_after": exc.detail
        }
    )


def setup_rate_limiting(app: FastAPI):
    """
    Configura rate limiting na aplicação FastAPI.
    
    Uso:
        from src.utils.rate_limiter import limiter, setup_rate_limiting
        
        app = FastAPI()
        setup_rate_limiting(app)
        
        @app.get("/rota")
        @limiter.limit("30/minute")
        def minha_rota(request: Request):
            ...
    """
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
    logger.info("Rate limiting configurado: 200 req/min padrão")


# Limites recomendados por tipo de endpoint
RATE_LIMITS = {
    "default": "200/minute",         # Endpoints gerais
    "heavy": "30/minute",            # Endpoints pesados (escalação, análise)
    "light": "300/minute",           # Endpoints leves (status)
    "auth": "10/minute",             # Endpoints de autenticação (futuro)
    "webhook": "60/minute",          # Webhooks externos
}
