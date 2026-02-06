"""
Testes unitários para módulos de segurança
"""

import pytest
import sys
from pathlib import Path

# Adicionar path do projeto
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.rate_limiter import get_real_ip, RATE_LIMITS
from src.utils.security_headers import SecurityHeadersMiddleware


class TestRateLimiterUtils:
    """Testes para utilitários do rate limiter"""
    
    def test_rate_limits_defined(self):
        """Rate limits devem estar definidos"""
        assert "default" in RATE_LIMITS
        assert "heavy" in RATE_LIMITS
        assert "light" in RATE_LIMITS
    
    def test_rate_limits_format(self):
        """Rate limits devem ter formato válido (X/minute)"""
        for key, value in RATE_LIMITS.items():
            assert "/" in value, f"Rate limit {key} deve ter formato X/unit"
            parts = value.split("/")
            assert len(parts) == 2
            assert parts[0].isdigit(), f"Rate limit {key} deve começar com número"


class TestGetRealIP:
    """Testes para função get_real_ip"""
    
    def test_get_real_ip_cloudflare(self):
        """Deve extrair IP do header Cloudflare"""
        class MockRequest:
            headers = {"CF-Connecting-IP": "1.2.3.4"}
            client = None
        
        ip = get_real_ip(MockRequest())
        assert ip == "1.2.3.4"
    
    def test_get_real_ip_xff(self):
        """Deve extrair IP do X-Forwarded-For"""
        class MockRequest:
            headers = {"X-Forwarded-For": "5.6.7.8, 10.0.0.1"}
            client = None
        
        ip = get_real_ip(MockRequest())
        assert ip == "5.6.7.8"  # Primeiro IP é o cliente real
    
    def test_get_real_ip_nginx(self):
        """Deve extrair IP do X-Real-IP (nginx)"""
        class MockRequest:
            headers = {"X-Real-IP": "9.10.11.12"}
            client = None
        
        ip = get_real_ip(MockRequest())
        assert ip == "9.10.11.12"
    
    def test_get_real_ip_fallback(self):
        """Deve usar client.host como fallback"""
        class MockClient:
            host = "13.14.15.16"
        
        class MockRequest:
            headers = {}
            client = MockClient()
        
        ip = get_real_ip(MockRequest())
        assert ip == "13.14.15.16"
    
    def test_get_real_ip_no_client(self):
        """Deve retornar localhost se não há cliente"""
        class MockRequest:
            headers = {}
            client = None
        
        ip = get_real_ip(MockRequest())
        assert ip == "127.0.0.1"


class TestSecurityHeadersMiddleware:
    """Testes para middleware de security headers"""
    
    def test_middleware_instantiable(self):
        """Middleware deve ser instanciável"""
        # Não pode testar completamente sem app, mas verifica importação
        assert SecurityHeadersMiddleware is not None
