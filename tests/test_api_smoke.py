"""
Testes de Smoke para API Cartola FC 2026

Estes testes verificam que os endpoints principais estão funcionando.
Devem ser rápidos e executar em cada deploy.

Executar: pytest tests/ -m smoke
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Adicionar path do projeto
sys.path.insert(0, str(Path(__file__).parent.parent))

from api_server import app


@pytest.fixture
def client():
    """Cliente de teste para a API"""
    return TestClient(app)


class TestSmokeEndpoints:
    """Testes de smoke - endpoints críticos devem responder"""
    
    @pytest.mark.smoke
    def test_root_returns_200(self, client):
        """Endpoint raiz deve retornar informações da API"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "app" in data or "api" in data
        assert "version" in data
    
    @pytest.mark.smoke
    def test_status_returns_200_or_503(self, client):
        """
        Status deve retornar 200 com dados ou 503 se API Cartola indisponível.
        Ambos são comportamentos válidos.
        """
        response = client.get("/api/status")
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.json()
            # API pode retornar 'rodada' ou 'rodadaAtual'
            assert "rodada" in data or "rodadaAtual" in data
            assert "status" in data
    
    @pytest.mark.smoke
    def test_dashboard_returns_200_or_503(self, client):
        """Dashboard deve retornar dados ou erro de API externa"""
        response = client.get("/api/dashboard")
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.json()
            assert "mercado" in data
            assert "topValorizadores" in data
    
    @pytest.mark.smoke
    def test_mercado_atletas_returns_list(self, client):
        """Endpoint de atletas deve retornar lista"""
        response = client.get("/api/mercado/atletas")
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
    
    @pytest.mark.smoke
    def test_confrontos_returns_list(self, client):
        """Endpoint de confrontos deve retornar lista"""
        response = client.get("/api/confrontos")
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)


class TestSecurityHeaders:
    """Testes de segurança - headers devem estar presentes"""
    
    @pytest.mark.smoke
    def test_security_headers_present(self, client):
        """Headers de segurança devem estar presentes nas respostas"""
        response = client.get("/")
        headers = response.headers
        
        # Headers críticos de segurança
        assert "x-content-type-options" in headers
        assert headers["x-content-type-options"] == "nosniff"
        
        assert "x-frame-options" in headers
        assert headers["x-frame-options"] == "DENY"
        
        assert "x-xss-protection" in headers
    
    @pytest.mark.smoke
    def test_cors_not_wildcard(self, client):
        """CORS não deve permitir origem wildcard"""
        # Fazendo request de origem não autorizada
        response = client.get(
            "/api/status",
            headers={"Origin": "https://malicious-site.com"}
        )
        
        # Se CORS está configurado corretamente, não deve ter header Access-Control-Allow-Origin
        # para origens não autorizadas, ou deve rejeitar
        cors_header = response.headers.get("access-control-allow-origin", "")
        assert cors_header != "*", "CORS não deve permitir wildcard '*'"


class TestValidation:
    """Testes de validação de entrada"""
    
    @pytest.mark.smoke
    def test_escalacao_invalid_esquema(self, client):
        """Esquema inválido deve retornar erro"""
        response = client.get("/api/escalacao/gerar?esquema=9-9-9")
        # Deve retornar 400 (bad request) ou 422 (validation error) ou processar
        # O importante é não crashar (500)
        assert response.status_code != 500
    
    @pytest.mark.smoke
    def test_historico_rodada_invalid(self, client):
        """Rodada inválida deve ser tratada graciosamente"""
        response = client.get("/api/historico/rodada/999")
        assert response.status_code in [200, 404, 400]
        # Não deve crashar


class TestRateLimiting:
    """Testes de rate limiting"""
    
    @pytest.mark.slow
    def test_rate_limit_not_triggered_normal_usage(self, client):
        """Rate limit não deve ser acionado em uso normal"""
        # 5 requests rápidos - deve funcionar
        for _ in range(5):
            response = client.get("/api/status")
            assert response.status_code in [200, 503]
            # 429 = Too Many Requests
            assert response.status_code != 429
