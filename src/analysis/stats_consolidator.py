"""
StatsConsolidator — Cache consolidado de dados por rodada.

Combina dados de múltiplas fontes em um único JSON por rodada:
  - Team stats (API-Football): gols, clean sheets, forma
  - H2H (API-Football): confrontos diretos
  - Notícias (GE scraping): lesões, suspensões
  - Descanso (FixtureCollector): dias desde último jogo

Armazenado em data/stats_cache/consolidado/rodada_{N}.json
TTL: 4 horas (dados podem mudar com notícias/escalações)
"""
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List

sys.path.append(str(Path(__file__).parent.parent.parent))

logger = logging.getLogger("StatsConsolidator")

CONSOLIDADO_DIR = Path(__file__).parent.parent.parent / "data" / "stats_cache" / "consolidado"
CONSOLIDADO_DIR.mkdir(parents=True, exist_ok=True)

CONSOLIDADO_TTL = 4 * 3600  # 4 horas


class StatsConsolidator:
    """Consolida todos os dados disponíveis para uma rodada."""

    @staticmethod
    def path_rodada(rodada: int) -> Path:
        return CONSOLIDADO_DIR / f"rodada_{rodada}.json"

    @classmethod
    def carregar(cls, rodada: int) -> Optional[Dict]:
        """Carrega consolidado do cache se válido."""
        path = cls.path_rodada(rodada)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Verificar TTL
            cached_at = data.get("_cached_at", "")
            if cached_at:
                dt = datetime.fromisoformat(cached_at)
                if (datetime.now() - dt).total_seconds() > CONSOLIDADO_TTL:
                    return None
            return data
        except Exception:
            return None

    @classmethod
    def salvar(cls, rodada: int, data: Dict) -> None:
        """Salva consolidado no cache."""
        data["_cached_at"] = datetime.now().isoformat()
        data["rodada"] = rodada
        path = cls.path_rodada(rodada)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"📦 Consolidado rodada {rodada} salvo ({path.stat().st_size // 1024}KB)")

    @classmethod
    def consolidar_rodada(
        cls,
        rodada: int,
        partidas: List[Dict],
        estatisticas_times: Dict[int, Any],
        descanso: Dict[int, int] = None,
        h2h_ajustes: Dict[str, tuple] = None,
        noticias_impacto: Dict[str, Dict] = None,
    ) -> Dict:
        """
        Consolida todos os dados de uma rodada em um único Dict.
        
        Args:
            rodada: Número da rodada
            partidas: Lista de partidas da Cartola API
            estatisticas_times: Dict {clube_id: EstatisticasTime}
            descanso: Dict {clube_id: dias_descanso}
            h2h_ajustes: Dict {"MANDxVISIT": (ajuste_m, ajuste_v)}
            noticias_impacto: Dict {"ABREV": {lesionados: int, suspensos: int, ...}}
        """
        consolidado = {
            "rodada": rodada,
            "total_jogos": len(partidas),
            "jogos": [],
            "times": {},
            "fontes": {
                "stats_cache": False,
                "h2h": False,
                "noticias": False,
                "descanso": False,
            }
        }

        if descanso:
            consolidado["fontes"]["descanso"] = True
        if h2h_ajustes:
            consolidado["fontes"]["h2h"] = True
        if noticias_impacto:
            consolidado["fontes"]["noticias"] = True

        # Coletar info de cada time
        for clube_id, stats in estatisticas_times.items():
            abrev = getattr(stats, 'abreviacao', '???')
            consolidado["times"][abrev] = {
                "clube_id": clube_id,
                "nome": getattr(stats, 'nome', ''),
                "posicao": getattr(stats, 'posicao', 0),
                "jogos": getattr(stats, 'jogos', 0),
                "gols_pro": getattr(stats, 'gols_pro', 0),
                "gols_contra": getattr(stats, 'gols_contra', 0),
                "media_gols_pro": round(getattr(stats, 'media_gols_pro', 0), 2),
                "media_gols_contra": round(getattr(stats, 'media_gols_contra', 0), 2),
                "forca_ataque": round(getattr(stats, 'forca_ataque', 50), 1),
                "forca_defesa": round(getattr(stats, 'forca_defesa', 50), 1),
                "forca_geral": round(getattr(stats, 'forca_geral', 50), 1),
                "forma": getattr(stats, 'forma_sequencia', ''),
                "descanso_dias": descanso.get(clube_id, -1) if descanso else -1,
                "noticias": noticias_impacto.get(abrev, {}) if noticias_impacto else {},
            }
            # Marcar se tem stats reais
            if getattr(stats, 'jogos', 0) > 5 and getattr(stats, 'media_gols_pro', 0) > 0:
                consolidado["fontes"]["stats_cache"] = True

        # Mapear clube_id → abreviação a partir das estatísticas
        id_to_abrev = {}
        for cid, stats in estatisticas_times.items():
            abrev = getattr(stats, 'abreviacao', '???')
            id_to_abrev[cid] = abrev

        # Info por jogo
        for p in partidas:
            casa_id = p.get("clube_casa_id")
            visit_id = p.get("clube_visitante_id")
            casa_abrev = p.get("clube_casa_abrev") or id_to_abrev.get(casa_id, "???")
            visit_abrev = p.get("clube_visitante_abrev") or id_to_abrev.get(visit_id, "???")
            h2h_key = f"{casa_abrev}-{visit_abrev}"
            h2h = h2h_ajustes.get(h2h_key) if h2h_ajustes else None

            jogo = {
                "mandante": casa_abrev,
                "visitante": visit_abrev,
                "mandante_id": p.get("clube_casa_id"),
                "visitante_id": p.get("clube_visitante_id"),
                "h2h_ajuste": {"mandante": round(h2h[0], 3), "visitante": round(h2h[1], 3)} if h2h else None,
            }
            consolidado["jogos"].append(jogo)

        return consolidado
