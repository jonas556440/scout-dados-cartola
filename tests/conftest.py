"""
Configurações compartilhadas para testes pytest
"""

import pytest
import sys
from pathlib import Path

# Adicionar path do projeto
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def api_url():
    """URL base da API para testes de integração"""
    return "http://localhost:8000"


@pytest.fixture(scope="session")
def project_root():
    """Diretório raiz do projeto"""
    return Path(__file__).parent.parent


@pytest.fixture
def sample_atleta():
    """Atleta de exemplo para testes"""
    return {
        "atleta_id": 12345,
        "nome": "Teste Player",
        "apelido": "Teste",
        "posicao_id": 5,  # ATA
        "clube_id": 1,
        "preco_num": 10.5,
        "media_num": 5.0,
        "pontos_num": 8.5,
        "jogos_num": 5,
        "status_id": 7,  # Provável
        "variacao_num": 0.5,
        "scout": {"G": 2, "A": 1, "FS": 3}
    }


@pytest.fixture
def sample_confronto():
    """Confronto de exemplo para testes"""
    return {
        "mandante_id": 1,
        "visitante_id": 2,
        "mandante_posicao": 5,
        "visitante_posicao": 12,
        "local": "Maracanã",
        "hora": "16:00"
    }
