"""
Cache Warmup — Funções de pré-aquecimento de cache
====================================================
Desacoplado do api_server.py para evitar imports circulares no scheduler.
Faz HTTP requests locais para popular o cache dos endpoints pesados.
"""
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

API_BASE = "http://127.0.0.1:8000"
TIMEOUT = 30  # segundos


def _warm_endpoint(path: str, label: str) -> bool:
    """Faz GET no endpoint local para popular o cache."""
    try:
        resp = requests.get(f"{API_BASE}{path}", timeout=TIMEOUT)
        if resp.status_code == 200:
            logger.info(f"✅ Cache de {label} pré-aquecido")
            return True
        else:
            logger.warning(f"⚠️  Cache {label}: status {resp.status_code}")
            return False
    except requests.RequestException as e:
        logger.error(f"❌ Erro ao pré-aquecer cache de {label}: {e}")
        return False


def warm_classificacao_cache(force: bool = False) -> bool:
    """Pré-aquece o cache de classificação do Brasileirão."""
    return _warm_endpoint("/api/brasileirao/classificacao", "classificação")


def warm_confrontos_cache(force: bool = False) -> bool:
    """Pré-aquece o cache de confrontos da rodada atual."""
    return _warm_endpoint("/api/confrontos", "confrontos")


def warm_forca_cache(force: bool = False) -> bool:
    """Pré-aquece o cache de força dos times."""
    return _warm_endpoint("/api/times/forca", "força dos times")


def warm_acuracia_cache(force: bool = False) -> bool:
    """Pré-aquece o cache de acurácia."""
    return _warm_endpoint("/api/brasileirao/acuracia", "acurácia")


def warm_noticias_cache(force: bool = False) -> bool:
    """Pré-aquece o cache de notícias (rodada atual via dashboard)."""
    return _warm_endpoint("/api/dashboard", "dashboard/notícias")


def warm_escalacao_cache(force: bool = False) -> bool:
    """Pré-aquece o cache de escalação (via mercado de atletas)."""
    return _warm_endpoint("/api/mercado/atletas", "escalação/mercado")
