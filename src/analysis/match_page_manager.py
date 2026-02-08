"""
MatchPageManager — Gerenciador progressivo de páginas de jogos.

1. Cria página base quando o jogo aparece no calendário (até 30 dias antes)
2. Atualiza com dados frescos 48h antes (forma, tabela, H2H)
3. Update final 6h antes (escalação se disponível)
4. Pós-jogo: adiciona placar + stats

Cada página é um JSON em data/match_pages/{slug}.json
servido pela API /api/jogos/{slug}

Timing (cron-safe):
  - Job diário 04:00: descobrir jogos próximos 30 dias → criar páginas novas
  - Job 4x/dia (06, 12, 18, 23:30): atualizar páginas em janela T-48h..T+6h
  
Ref: Google Helpful Content — "conteúdo útil criado para pessoas"
"""
import json
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

sys.path.append(str(Path(__file__).parent.parent.parent))

logger = logging.getLogger("MatchPageManager")

PAGES_DIR = Path(__file__).parent.parent.parent / "data" / "match_pages"
PAGES_DIR.mkdir(parents=True, exist_ok=True)

BRT = timezone(timedelta(hours=-3))


def _slugify(text: str) -> str:
    """Converte texto para slug URL-safe."""
    import re
    text = text.lower().strip()
    replacements = {
        'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a',
        'é': 'e', 'ê': 'e', 'í': 'i', 'ó': 'o',
        'ô': 'o', 'õ': 'o', 'ú': 'u', 'ü': 'u',
        'ç': 'c',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


class MatchPageManager:
    """
    Gerencia criação e atualização progressiva de páginas de jogos.
    
    Fluxo:
      1. discover_and_create() — cria páginas para jogos novos
      2. update_upcoming() — atualiza jogos nas janelas T-48h e T-6h
      3. update_post_game() — atualiza jogos finalizados com placar
    """

    def __init__(self):
        self._fdo = None
        self._enricher = None
        self._insights = None

    @property
    def fdo(self):
        if self._fdo is None:
            from src.analysis.football_data_client import FootballDataClient
            self._fdo = FootballDataClient()
        return self._fdo

    @property
    def enricher(self):
        if self._enricher is None:
            from src.analysis.stats_enricher import StatsEnricher
            self._enricher = StatsEnricher()
        return self._enricher

    @property
    def insights_gen(self):
        if self._insights is None:
            from src.analysis.match_insights import MatchInsights
            self._insights = MatchInsights()
        return self._insights

    # ──────────────────── Page I/O ────────────────────

    def _page_path(self, slug: str) -> Path:
        return PAGES_DIR / f"{slug}.json"

    def _load_page(self, slug: str) -> Optional[Dict]:
        path = self._page_path(slug)
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def _save_page(self, page: Dict) -> None:
        path = self._page_path(page["slug"])
        page["updated_at"] = datetime.now(BRT).isoformat()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(page, f, ensure_ascii=False, indent=2)

    # ──────────────────── 1. Discover & Create ────────────────────

    def discover_and_create(self, max_days_ahead: int = 30) -> Dict[str, int]:
        """
        Descobre jogos dos próximos N dias e cria páginas novas.
        
        Returns:
            {"criados": N, "existentes": M, "total": T}
        """
        today = datetime.now(BRT).date()
        date_from = today.isoformat()
        date_to = (today + timedelta(days=max_days_ahead)).isoformat()

        matches = self.fdo.jogos_periodo(date_from, date_to)
        if not matches:
            logger.warning("Nenhum jogo encontrado no período")
            return {"criados": 0, "existentes": 0, "total": 0}

        criados = 0
        existentes = 0

        for m in matches:
            slug = self._match_slug(m)
            existing = self._load_page(slug)
            if existing:
                existentes += 1
                continue

            # Criar página base
            page = self._create_base_page(m, slug)
            self._save_page(page)
            criados += 1
            logger.info(f"📄 Página criada: {slug}")

        result = {"criados": criados, "existentes": existentes, "total": len(matches)}
        logger.info(
            f"📄 Descoberta: {criados} criados, {existentes} existentes "
            f"de {len(matches)} jogos"
        )
        return result

    def _match_slug(self, match: Dict) -> str:
        """Gera slug único para um match."""
        m_nome = match.get("mandante", "time-a")
        v_nome = match.get("visitante", "time-b")
        data = match.get("data_brt", "")[:10]
        return _slugify(f"{m_nome}-x-{v_nome}-{data}")

    def _create_base_page(self, match: Dict, slug: str) -> Dict:
        """Cria estrutura base de uma página de jogo."""
        data_brt = match.get("data_brt", "")
        return {
            "slug": slug,
            "match_id_fdo": match.get("match_id"),
            "mandante": match.get("mandante", ""),
            "visitante": match.get("visitante", ""),
            "mandante_sigla": match.get("mandante_sigla", ""),
            "visitante_sigla": match.get("visitante_sigla", ""),
            "mandante_id_fdo": match.get("mandante_id", 0),
            "visitante_id_fdo": match.get("visitante_id", 0),
            "rodada": match.get("rodada"),
            "data_brt": data_brt,
            "data_utc": match.get("data_utc", ""),
            "estadio": match.get("estadio", ""),
            "arbitro": match.get("arbitro", ""),
            "competicao": match.get("competicao", "Brasileirão Série A"),
            "status": match.get("status", "SCHEDULED"),
            # Dados que serão preenchidos em updates
            "posicao_mandante": None,
            "posicao_visitante": None,
            "pontos_mandante": None,
            "pontos_visitante": None,
            "forma_mandante": None,
            "forma_visitante": None,
            "artilheiro_mandante": None,
            "artilheiro_visitante": None,
            "h2h": None,
            "insights": [],
            "placar_mandante": None,
            "placar_visitante": None,
            # Metadados
            "created_at": datetime.now(BRT).isoformat(),
            "updated_at": datetime.now(BRT).isoformat(),
            "last_enrichment": None,
            "enrichment_level": "base",  # base → pre_match → match_day → post_game
            # SEO
            "title": (
                f"{match.get('mandante', '')} x {match.get('visitante', '')} "
                f"— Brasileirão 2026 Rodada {match.get('rodada', '')}"
            ),
            "description": (
                f"Análise completa de {match.get('mandante', '')} x "
                f"{match.get('visitante', '')} pela rodada "
                f"{match.get('rodada', '')} do Brasileirão 2026. "
                f"Classificação, confronto direto, artilheiros e mais."
            ),
        }

    # ──────────────────── 2. Update Upcoming ────────────────────

    def update_upcoming(self) -> Dict[str, int]:
        """
        Atualiza páginas de jogos que estão nas janelas:
        - T-72h a T-48h: dados básicos (forma, tabela)
        - T-48h a T-6h: dados completos (H2H, insights, artilheiros)
        - T-6h a kickoff: update final
        
        Returns:
            {"atualizados": N, "ignorados": M}
        """
        now = datetime.now(BRT)
        atualizados = 0
        ignorados = 0

        # Carregar classificação e artilheiros (1 request cada, ou cache)
        classificacao = self.fdo.classificacao() or []
        artilheiros = self.fdo.artilheiros(limit=30) or []

        for page_file in PAGES_DIR.glob("*.json"):
            try:
                with open(page_file, "r", encoding="utf-8") as f:
                    page = json.load(f)

                # Skip se já é post_game
                if page.get("enrichment_level") == "post_game":
                    continue

                # Calcular tempo até o jogo
                data_brt = page.get("data_brt", "")
                if not data_brt:
                    continue
                try:
                    kickoff = datetime.fromisoformat(
                        data_brt.replace(" ", "T") + 
                        ("-03:00" if "+" not in data_brt and "-" not in data_brt[10:] else "")
                    )
                except Exception:
                    continue

                hours_to_kick = (kickoff - now).total_seconds() / 3600

                # Janelas de atualização
                if hours_to_kick > 72:
                    # Muito cedo — só criar se não existe
                    ignorados += 1
                    continue
                elif hours_to_kick > 48:
                    # T-72h a T-48h: dados básicos
                    if page.get("enrichment_level") in ("pre_match", "match_day"):
                        ignorados += 1
                        continue
                    self._enrich_basic(page, classificacao, artilheiros)
                    page["enrichment_level"] = "pre_match"
                elif hours_to_kick > 0:
                    # T-48h a kickoff: dados completos
                    self._enrich_full(page, classificacao, artilheiros)
                    page["enrichment_level"] = "match_day"
                elif hours_to_kick > -6:
                    # Jogo em andamento ou recém terminado
                    # Atualizar status
                    self._check_status(page)
                    page["enrichment_level"] = "match_day"
                else:
                    # Mais de 6h após kickoff — verificar pós-jogo
                    self._update_post_game(page)

                self._save_page(page)
                atualizados += 1

            except Exception as e:
                logger.error(f"Erro ao processar {page_file.name}: {e}")

        logger.info(f"📄 Update: {atualizados} atualizados, {ignorados} ignorados")
        return {"atualizados": atualizados, "ignorados": ignorados}

    def _enrich_basic(
        self, page: Dict, classificacao: List[Dict], artilheiros: List[Dict]
    ) -> None:
        """Enriquecimento básico: posição na tabela, forma, artilheiro."""
        m_id = page.get("mandante_id_fdo", 0)
        v_id = page.get("visitante_id_fdo", 0)

        for t in classificacao:
            if t.get("time_id") == m_id:
                page["posicao_mandante"] = t.get("posicao")
                page["pontos_mandante"] = t.get("pontos")
                page["forma_mandante"] = t.get("forma", "")
            if t.get("time_id") == v_id:
                page["posicao_visitante"] = t.get("posicao")
                page["pontos_visitante"] = t.get("pontos")
                page["forma_visitante"] = t.get("forma", "")

        for a in artilheiros:
            if a.get("time_id") == m_id and not page.get("artilheiro_mandante"):
                page["artilheiro_mandante"] = a
            if a.get("time_id") == v_id and not page.get("artilheiro_visitante"):
                page["artilheiro_visitante"] = a

        # Gerar insights básicos (classificação, artilheiros, forma)
        try:
            insights = self.insights_gen.gerar_insights_jogo(
                mandante=page.get("mandante", ""),
                visitante=page.get("visitante", ""),
                mandante_abrev=page.get("mandante_sigla", ""),
                visitante_abrev=page.get("visitante_sigla", ""),
                posicao_m={"posicao": page.get("posicao_mandante"),
                           "pontos": page.get("pontos_mandante"),
                           "forma": page.get("forma_mandante", "")} if page.get("posicao_mandante") else None,
                posicao_v={"posicao": page.get("posicao_visitante"),
                           "pontos": page.get("pontos_visitante"),
                           "forma": page.get("forma_visitante", "")} if page.get("posicao_visitante") else None,
                artilheiro_m=page.get("artilheiro_mandante"),
                artilheiro_v=page.get("artilheiro_visitante"),
            )
            if insights:
                page["insights"] = insights
        except Exception as e:
            logger.warning(f"Basic insights error: {e}")

        page["last_enrichment"] = datetime.now(BRT).isoformat()

    def _enrich_full(
        self, page: Dict, classificacao: List[Dict], artilheiros: List[Dict]
    ) -> None:
        """Enriquecimento completo: básico + H2H + insights factuais."""
        # Básico primeiro
        self._enrich_basic(page, classificacao, artilheiros)

        # H2H via football-data.org (se tiver match_id)
        match_id = page.get("match_id_fdo")
        if match_id and not page.get("h2h"):
            h2h = self.fdo.h2h(match_id, limit=10)
            if h2h:
                page["h2h"] = h2h

        # Gerar insights factuais
        try:
            from src.analysis.fixture_collector import CARTOLA_TO_APIFOOTBALL, APIFOOTBALL_TO_CARTOLA

            # Team stats do API-Football (se disponível no cache)
            ts_m = None
            ts_v = None
            # Tentar encontrar AF IDs para buscar team stats já cacheados
            for cart_id, af_id in CARTOLA_TO_APIFOOTBALL.items():
                cached = self.enricher._cache_get(
                    "team_stats", f"{af_id}_71_2024"
                )
                if not cached:
                    cached = self.enricher._cache_get(
                        "team_stats", f"{af_id}_72_2024"
                    )
                if cached:
                    # Mapear por nome (aproximado)
                    team_name = (cached.get("team_name") or "").lower()
                    if page.get("mandante", "").lower() in team_name or \
                       team_name in page.get("mandante", "").lower():
                        ts_m = cached
                    if page.get("visitante", "").lower() in team_name or \
                       team_name in page.get("visitante", "").lower():
                        ts_v = cached

            insights = self.insights_gen.gerar_insights_jogo(
                mandante=page.get("mandante", ""),
                visitante=page.get("visitante", ""),
                mandante_abrev=page.get("mandante_sigla", ""),
                visitante_abrev=page.get("visitante_sigla", ""),
                team_stats_m=ts_m,
                team_stats_v=ts_v,
                h2h=page.get("h2h"),
                posicao_m={"posicao": page.get("posicao_mandante"),
                           "pontos": page.get("pontos_mandante"),
                           "forma": page.get("forma_mandante", "")} if page.get("posicao_mandante") else None,
                posicao_v={"posicao": page.get("posicao_visitante"),
                           "pontos": page.get("pontos_visitante"),
                           "forma": page.get("forma_visitante", "")} if page.get("posicao_visitante") else None,
                artilheiro_m=page.get("artilheiro_mandante"),
                artilheiro_v=page.get("artilheiro_visitante"),
            )
            if insights:
                page["insights"] = insights

        except Exception as e:
            logger.warning(f"Insights error: {e}")

        page["last_enrichment"] = datetime.now(BRT).isoformat()

    def _check_status(self, page: Dict) -> None:
        """Verifica status atual do jogo (em andamento/terminado)."""
        match_id = page.get("match_id_fdo")
        if not match_id:
            return
        # Podemos verificar via jogos_rodada se mudou status
        rodada = page.get("rodada")
        if rodada:
            matches = self.fdo.jogos_rodada(rodada)
            if matches:
                for m in matches:
                    if m.get("match_id") == match_id:
                        page["status"] = m.get("status", page.get("status"))
                        if m.get("gols_mandante") is not None:
                            page["placar_mandante"] = m["gols_mandante"]
                            page["placar_visitante"] = m["gols_visitante"]
                        break

    def _update_post_game(self, page: Dict) -> None:
        """Atualiza página com resultado pós-jogo."""
        if page.get("enrichment_level") == "post_game":
            return

        self._check_status(page)

        if page.get("status") == "FINISHED":
            page["enrichment_level"] = "post_game"
            logger.info(
                f"✅ Pós-jogo: {page['mandante']} {page.get('placar_mandante', '?')}"
                f"x{page.get('placar_visitante', '?')} {page['visitante']}"
            )

    # ──────────────────── API Helpers ────────────────────

    def listar_paginas(self, limit: int = 50) -> List[Dict]:
        """Lista todas as páginas de jogos (resumo)."""
        pages = []
        for f in sorted(PAGES_DIR.glob("*.json"), reverse=True):
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    p = json.load(fp)
                pages.append({
                    "slug": p["slug"],
                    "mandante": p.get("mandante"),
                    "visitante": p.get("visitante"),
                    "data_brt": p.get("data_brt"),
                    "rodada": p.get("rodada"),
                    "status": p.get("status"),
                    "enrichment_level": p.get("enrichment_level"),
                    "placar": (
                        f"{p.get('placar_mandante', '')}x{p.get('placar_visitante', '')}"
                        if p.get("placar_mandante") is not None else None
                    ),
                })
            except Exception:
                continue
        return pages[:limit]

    def get_pagina(self, slug: str) -> Optional[Dict]:
        """Retorna página completa de um jogo."""
        return self._load_page(slug)

    def stats(self) -> Dict:
        """Estatísticas do sistema de páginas."""
        total = 0
        by_level = {"base": 0, "pre_match": 0, "match_day": 0, "post_game": 0}
        for f in PAGES_DIR.glob("*.json"):
            total += 1
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    p = json.load(fp)
                level = p.get("enrichment_level", "base")
                by_level[level] = by_level.get(level, 0) + 1
            except Exception:
                pass
        return {"total": total, "por_nivel": by_level}
