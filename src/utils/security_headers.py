"""
Security Headers Middleware para FastAPI
=========================================
Adiciona headers de segurança HTTP em todas as respostas
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Callable
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware que adiciona headers de segurança em todas as respostas.
    
    Headers adicionados:
    - X-Content-Type-Options: Previne MIME sniffing
    - X-Frame-Options: Previne clickjacking
    - X-XSS-Protection: Proteção XSS legada (browsers antigos)
    - Referrer-Policy: Controla informações de referrer
    - Permissions-Policy: Controla recursos do browser
    - Content-Security-Policy: Política de segurança de conteúdo
    - Strict-Transport-Security: Força HTTPS (HSTS)
    
    Uso:
        from src.utils.security_headers import SecurityHeadersMiddleware
        
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Headers de segurança essenciais
        security_headers = {
            # Previne MIME type sniffing
            "X-Content-Type-Options": "nosniff",
            
            # Previne clickjacking (iframe embedding)
            "X-Frame-Options": "DENY",
            
            # Proteção XSS para browsers antigos
            "X-XSS-Protection": "1; mode=block",
            
            # Controla informações enviadas no header Referer
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Desabilita recursos perigosos do browser
            "Permissions-Policy": (
                "accelerometer=(), "
                "camera=(), "
                "geolocation=(), "
                "gyroscope=(), "
                "magnetometer=(), "
                "microphone=(), "
                "payment=(), "
                "usb=()"
            ),
        }
        
        # Cache-Control inteligente por tipo de request
        if "Cache-Control" not in response.headers:
            path = request.url.path
            method = request.method.upper()
            if method == "GET" and path.startswith("/api/"):
                # APIs GET: cache curto para browser/proxy
                if any(p in path for p in ["/brasileirao/acuracia", "/times/forca", "/times/xg"]):
                    response.headers["Cache-Control"] = "public, max-age=300, stale-while-revalidate=60"
                elif any(p in path for p in ["/blog/", "/brasileirao/classificacao"]):
                    response.headers["Cache-Control"] = "public, max-age=120, stale-while-revalidate=30"
                else:
                    response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=15"
            else:
                # POST/PUT/DELETE e não-API: sem cache
                response.headers["Cache-Control"] = "no-store, max-age=0"
        
        # Apenas em HTTPS: adicionar HSTS
        if request.url.scheme == "https" or request.headers.get("X-Forwarded-Proto") == "https":
            # HSTS: força HTTPS por 1 ano, inclui subdomínios
            security_headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        
        # Aplicar headers (não sobrescrever se já existir)
        for header, value in security_headers.items():
            if header not in response.headers:
                response.headers[header] = value
        
        return response


class CSPMiddleware(BaseHTTPMiddleware):
    """
    Content Security Policy middleware separado para maior controle.
    
    CSP mais restritivo - use apenas se necessário.
    Pode quebrar integrações com CDNs e scripts externos.
    """
    
    def __init__(self, app, policy: str = None):
        super().__init__(app)
        self.policy = policy or self._default_policy()
    
    def _default_policy(self) -> str:
        """Política CSP padrão para API"""
        return "; ".join([
            "default-src 'self'",
            "script-src 'self'",
            "style-src 'self' 'unsafe-inline'",  # shadcn usa inline styles
            "img-src 'self' data: https:",
            "font-src 'self'",
            "connect-src 'self' https://api.cartolafc.globo.com",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'"
        ])
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Apenas para respostas HTML (não API JSON)
        content_type = response.headers.get("content-type", "")
        if "text/html" in content_type:
            response.headers["Content-Security-Policy"] = self.policy
        
        return response


# Função helper para configurar todos os middlewares de segurança
def setup_security_middlewares(app, include_csp: bool = False):
    """
    Configura todos os middlewares de segurança.
    
    Args:
        app: Aplicação FastAPI
        include_csp: Se True, adiciona CSP (pode quebrar alguns recursos)
    """
    app.add_middleware(SecurityHeadersMiddleware)
    
    if include_csp:
        app.add_middleware(CSPMiddleware)
    
    logger.info("Security headers middleware configurado")
