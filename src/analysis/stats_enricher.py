"""
StatsEnricher — Enriquecimento de dados via API-Football v3.

Coleta e cacheia dados avançados para uso em:
  1. Blog posts (stats reais, xG, artilheiros, série, classificação)
  2. Modelo preditivo (xG, clean sheets, gols por período, forma)
  3. Odds como feature interna (calibração do modelo)

Estratégia de budget (free tier: 100 req/dia):
  - fixtures/dia: 3 req (hoje ± 1) — FixtureCollector
  - stats/rodada: ~12 req (10 jogos stats + 1 standings + 1 status)
  - team stats: 20 req (1 por time, cache semanal)
  - h2h: 10 req (1 por jogo, cache permanente)
  - Total: ~45 req = metade do budget, margem segura

Cache em data/stats_cache/ — NUNCA chama API se cache válido existe.
Odds isoladas em data/_internal/ (nunca servidas em rotas públicas).

Uso:
    enricher = StatsEnricher()
    stats = enricher.stats_fixture(fixture_id)         # xG, chutes, posse
    team = enricher.stats_time_temporada(127, 71, 2024) # stats completas
    h2h = enricher.historico_h2h(127, 131)             # confrontos diretos
    standings = enricher.classificacao(71, 2024)       # tabela completa

Refs:
  Anderson & Sally (2013): The Numbers Game
  Sumpter (2016): Soccermatics
"""
import json
import logging
import sys
from datetime import datetime, timedelta, date, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

sys.path.append(str(Path(__file__).parent.parent.parent))

logger = logging.getLogger("StatsEnricher")

# Diretórios de cache
CACHE_DIR = Path(__file__).parent.parent.parent / "data" / "stats_cache"
INTERNAL_DIR = Path(__file__).parent.parent.parent / "data" / "_internal"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
INTERNAL_DIR.mkdir(parents=True, exist_ok=True)

BRT = timezone(timedelta(hours=-3))

# TTL de cache (em segundos)
CACHE_TTL = {
    "fixture_stats": 30 * 86400,     # stats de jogo finalizado: 30 dias (não muda)
    "fixture_events": 30 * 86400,    # events de jogo: 30 dias
    "team_stats": 7 * 86400,         # stats de time por temporada: 7 dias
    "standings": 1 * 86400,          # classificação: 1 dia
    "h2h": 30 * 86400,               # H2H: 30 dias (histórico estável)
}


class StatsEnricher:
    """Coleta e cacheia stats avançadas via API-Football."""

    API_BASE = "https://v3.football.api-sports.io"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or self._load_api_key()
        self._session = None
        self._last_request_time = 0.0  # Rate limiter: 10 req/min

    @staticmethod
    def _load_api_key() -> str:
        import os
        key = os.environ.get("APIFOOTBALL_KEY", "")
        if not key:
            try:
                from config.settings import settings
                key = getattr(settings, "APIFOOTBALL_KEY", "")
            except Exception:
                pass
        if not key:
            key = "d354c8d1f1d70486fe3b6b69cc905381"
        return key

    @property
    def session(self):
        if self._session is None:
            import requests
            self._session = requests.Session()
            self._session.headers.update({
                "x-apisports-key": self.api_key,
                "Accept": "application/json",
            })
        return self._session

    # ──────────────────── Cache ────────────────────

    def _cache_path(self, category: str, key: str) -> Path:
        """Retorna path do cache para uma categoria e chave."""
        subdir = CACHE_DIR / category
        subdir.mkdir(parents=True, exist_ok=True)
        return subdir / f"{key}.json"

    def _cache_get(self, category: str, key: str) -> Optional[Dict]:
        """Lê do cache se válido."""
        path = self._cache_path(category, key)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Verificar TTL
            cached_at = data.get("_cached_at", "")
            ttl = CACHE_TTL.get(category, 86400)
            if cached_at:
                dt = datetime.fromisoformat(cached_at)
                if (datetime.now() - dt).total_seconds() > ttl:
                    return None  # Expirado
            return data
        except Exception:
            return None

    def _cache_set(self, category: str, key: str, data: Dict) -> None:
        """Salva no cache."""
        data["_cached_at"] = datetime.now().isoformat()
        path = self._cache_path(category, key)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ──────────────────── API calls ────────────────────

    def _get(self, endpoint: str, params: Dict) -> Optional[Dict]:
        """Chamada à API com error handling e rate limiting (10 req/min)."""
        import time

        # Rate limiter: mínimo 7s entre requests (< 10 req/min)
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < 7.0:
            wait = 7.0 - elapsed
            logger.debug(f"Rate limit: aguardando {wait:.1f}s")
            time.sleep(wait)

        url = f"{self.API_BASE}/{endpoint}"
        try:
            self._last_request_time = time.time()
            r = self.session.get(url, params=params, timeout=15)
            if r.status_code != 200:
                logger.warning(f"API-Football {endpoint}: HTTP {r.status_code}")
                return None
            data = r.json()
            errors = data.get("errors", {})
            if errors and (isinstance(errors, dict) and errors or isinstance(errors, list) and errors):
                # Se for rate limit, esperar e tentar 1 vez mais
                if isinstance(errors, dict) and "rateLimit" in errors:
                    logger.warning(f"Rate limit atingido, aguardando 60s...")
                    time.sleep(60)
                    self._last_request_time = time.time()
                    r = self.session.get(url, params=params, timeout=15)
                    if r.status_code == 200:
                        data = r.json()
                        errors = data.get("errors", {})
                        if not errors:
                            return data
                logger.warning(f"API-Football {endpoint}: {errors}")
                return None
            return data
        except Exception as e:
            logger.error(f"API-Football {endpoint}: {e}")
            return None

    def requests_restantes(self) -> int:
        """Retorna quantos requests sobram no dia."""
        data = self._get("status", {})
        if data:
            req = data.get("response", {}).get("requests", {})
            return req.get("limit_day", 100) - req.get("current", 0)
        return 0

    # ──────────────────── Fixture Statistics ────────────────────

    def stats_fixture(self, fixture_id: int) -> Optional[Dict]:
        """
        Coleta estatísticas de um fixture finalizado.

        Retorna:
            {home: {xg, chutes, posse, ...}, away: {xg, chutes, posse, ...}}
        """
        cache_key = str(fixture_id)
        cached = self._cache_get("fixture_stats", cache_key)
        if cached:
            return cached

        resp = self._get("fixtures/statistics", {"fixture": fixture_id})
        if not resp:
            return None

        stats_raw = resp.get("response", [])
        if not stats_raw:
            return None

        result = {"fixture_id": fixture_id}
        for team_data in stats_raw:
            team_name = team_data.get("team", {}).get("name", "?")
            team_id = team_data.get("team", {}).get("id", 0)
            side = "home" if team_data == stats_raw[0] else "away"

            stats = {}
            for s in team_data.get("statistics", []):
                stat_type = s["type"].lower().replace(" ", "_")
                val = s["value"]
                # Converter "65%" para 65.0
                if isinstance(val, str) and val.endswith("%"):
                    try:
                        val = float(val.rstrip("%"))
                    except ValueError:
                        pass
                stats[stat_type] = val

            result[side] = {
                "team_name": team_name,
                "team_id": team_id,
                "xg": stats.get("expected_goals"),
                "chutes_gol": stats.get("shots_on_goal", 0),
                "chutes_fora": stats.get("shots_off_goal", 0),
                "chutes_total": stats.get("total_shots", 0),
                "chutes_bloqueados": stats.get("blocked_shots", 0),
                "chutes_dentro_area": stats.get("shots_insidebox", 0),
                "chutes_fora_area": stats.get("shots_outsidebox", 0),
                "posse": stats.get("ball_possession"),
                "passes_total": stats.get("total_passes", 0),
                "passes_certo": stats.get("passes_accurate", 0),
                "passes_pct": stats.get("passes_%"),
                "escanteios": stats.get("corner_kicks", 0),
                "faltas": stats.get("fouls", 0),
                "impedimentos": stats.get("offsides", 0),
                "cartoes_amarelos": stats.get("yellow_cards", 0),
                "cartoes_vermelhos": stats.get("red_cards", 0),
                "defesas_goleiro": stats.get("goalkeeper_saves", 0),
                "gols_impedidos": stats.get("goals_prevented"),
            }

        self._cache_set("fixture_stats", cache_key, result)
        logger.info(f"📊 Stats fixture {fixture_id}: {result.get('home',{}).get('team_name','?')} vs {result.get('away',{}).get('team_name','?')}")
        return result

    # ──────────────────── Fixture Events ────────────────────

    def events_fixture(self, fixture_id: int) -> Optional[List[Dict]]:
        """
        Coleta eventos de um fixture (gols, cartões, substituições).

        Retorna lista de events com minuto, tipo, jogador, time.
        Ideal para posts de blog detalhados.
        """
        cache_key = str(fixture_id)
        cached = self._cache_get("fixture_events", cache_key)
        if cached:
            return cached.get("events", [])

        resp = self._get("fixtures/events", {"fixture": fixture_id})
        if not resp:
            return None

        events_raw = resp.get("response", [])
        events = []
        for e in events_raw:
            events.append({
                "minuto": e["time"]["elapsed"],
                "minuto_extra": e["time"].get("extra"),
                "tipo": e["type"],
                "detalhe": e.get("detail", ""),
                "jogador": e.get("player", {}).get("name", ""),
                "jogador_id": e.get("player", {}).get("id"),
                "time": e.get("team", {}).get("name", ""),
                "time_id": e.get("team", {}).get("id"),
                "assistente": e.get("assist", {}).get("name"),
            })

        self._cache_set("fixture_events", cache_key, {"fixture_id": fixture_id, "events": events})
        logger.info(f"📋 Events fixture {fixture_id}: {len(events)} eventos")
        return events

    # ──────────────────── Team Statistics ────────────────────

    def stats_time_temporada(self, team_id: int, league_id: int = 71, season: int = 2024) -> Optional[Dict]:
        """
        Coleta estatísticas completas de um time numa temporada.

        Dados incluem: forma, gols (total, média, por minuto),
        vitórias/empates/derrotas (casa/fora), clean sheets, pênaltis.

        NOTA: Free tier só suporta seasons 2022-2024.
        """
        cache_key = f"{team_id}_{league_id}_{season}"
        cached = self._cache_get("team_stats", cache_key)
        if cached:
            return cached

        resp = self._get("teams/statistics", {
            "team": team_id,
            "league": league_id,
            "season": season,
        })
        if not resp:
            return None

        raw = resp.get("response", {})
        if not raw:
            return None

        goals_for = raw.get("goals", {}).get("for", {})
        goals_against = raw.get("goals", {}).get("against", {})
        fixtures = raw.get("fixtures", {})
        clean = raw.get("clean_sheet", {})
        penalty = raw.get("penalty", {})

        # Gols por minuto (para análise de quando o time marca)
        gols_minuto = {}
        for period, vals in goals_for.get("minute", {}).items():
            if vals.get("total"):
                gols_minuto[period] = {
                    "total": vals["total"],
                    "pct": vals.get("percentage", "0%"),
                }

        result = {
            "team_id": team_id,
            "team_name": raw.get("team", {}).get("name", "?"),
            "league": raw.get("league", {}).get("name", "?"),
            "season": season,
            "forma": raw.get("form", ""),
            "jogos": {
                "total": fixtures.get("played", {}).get("total", 0),
                "casa": fixtures.get("played", {}).get("home", 0),
                "fora": fixtures.get("played", {}).get("away", 0),
            },
            "vitorias": {
                "total": fixtures.get("wins", {}).get("total", 0),
                "casa": fixtures.get("wins", {}).get("home", 0),
                "fora": fixtures.get("wins", {}).get("away", 0),
            },
            "empates": {
                "total": fixtures.get("draws", {}).get("total", 0),
                "casa": fixtures.get("draws", {}).get("home", 0),
                "fora": fixtures.get("draws", {}).get("away", 0),
            },
            "derrotas": {
                "total": fixtures.get("loses", {}).get("total", 0),
                "casa": fixtures.get("loses", {}).get("home", 0),
                "fora": fixtures.get("loses", {}).get("away", 0),
            },
            "gols_pro": {
                "total": goals_for.get("total", {}).get("total", 0),
                "media": goals_for.get("average", {}).get("total", "0"),
                "casa": goals_for.get("total", {}).get("home", 0),
                "fora": goals_for.get("total", {}).get("away", 0),
                "media_casa": goals_for.get("average", {}).get("home", "0"),
                "media_fora": goals_for.get("average", {}).get("away", "0"),
            },
            "gols_contra": {
                "total": goals_against.get("total", {}).get("total", 0),
                "media": goals_against.get("average", {}).get("total", "0"),
                "casa": goals_against.get("total", {}).get("home", 0),
                "fora": goals_against.get("total", {}).get("away", 0),
                "media_casa": goals_against.get("average", {}).get("home", "0"),
                "media_fora": goals_against.get("average", {}).get("away", "0"),
            },
            "gols_por_minuto": gols_minuto,
            "clean_sheets": {
                "total": clean.get("total", 0),
                "casa": clean.get("home", 0),
                "fora": clean.get("away", 0),
            },
            "penaltis": {
                "marcados": penalty.get("scored", {}).get("total", 0),
                "perdidos": penalty.get("missed", {}).get("total", 0),
                "total": penalty.get("total", 0),
                "pct": penalty.get("scored", {}).get("percentage", "0%"),
            },
            "maior_sequencia": {
                "vitorias": raw.get("biggest", {}).get("streak", {}).get("wins", 0),
                "derrotas": raw.get("biggest", {}).get("streak", {}).get("loses", 0),
                "invicto": raw.get("biggest", {}).get("streak", {}).get("draws", 0),
            },
            "maior_vitoria_casa": raw.get("biggest", {}).get("wins", {}).get("home", ""),
            "maior_vitoria_fora": raw.get("biggest", {}).get("wins", {}).get("away", ""),
            "maior_derrota_casa": raw.get("biggest", {}).get("loses", {}).get("home", ""),
            "maior_derrota_fora": raw.get("biggest", {}).get("loses", {}).get("away", ""),
        }

        # Não cachear se o time não tem jogos nesta liga/season
        if result["jogos"]["total"] == 0:
            logger.info(f"⚠️ {result['team_name']}: 0 jogos em {league_id}/{season} — não cacheado")
            return None

        self._cache_set("team_stats", cache_key, result)
        logger.info(f"📊 Team stats: {result['team_name']} ({league_id}/{season})")
        return result

    # ──────────────────── H2H ────────────────────

    def historico_h2h(self, team1_afid: int, team2_afid: int, last: int = 20) -> Optional[Dict]:
        """
        Coleta histórico de confrontos entre dois times.

        Retorna últimos confrontos com placar, competição e data.
        O parâmetro `last` limita aos N jogos mais recentes (padrão 20).
        """
        # Ordenar IDs para cache consistente
        pair = f"{min(team1_afid, team2_afid)}-{max(team1_afid, team2_afid)}"
        cache_key = pair

        cached = self._cache_get("h2h", cache_key)
        if cached:
            return cached

        params = {"h2h": f"{team1_afid}-{team2_afid}", "last": str(last)}
        resp = self._get("fixtures/headtohead", params)
        if not resp:
            return None

        fixtures = resp.get("response", [])
        if not fixtures:
            return {"pair": pair, "total": 0, "jogos": []}

        jogos = []
        stats = {"team1_wins": 0, "team2_wins": 0, "draws": 0}

        for fix in fixtures:
            home = fix["teams"]["home"]
            away = fix["teams"]["away"]
            gh = fix["goals"]["home"]
            ga = fix["goals"]["away"]

            if gh is not None and ga is not None:
                if home["id"] == team1_afid:
                    if gh > ga:
                        stats["team1_wins"] += 1
                    elif ga > gh:
                        stats["team2_wins"] += 1
                    else:
                        stats["draws"] += 1
                else:
                    if gh > ga:
                        stats["team2_wins"] += 1
                    elif ga > gh:
                        stats["team1_wins"] += 1
                    else:
                        stats["draws"] += 1

            jogos.append({
                "data": fix["fixture"]["date"][:10],
                "liga": fix["league"]["name"],
                "mandante": home["name"],
                "mandante_id": home["id"],
                "visitante": away["name"],
                "visitante_id": away["id"],
                "gols_mandante": gh,
                "gols_visitante": ga,
            })

        # Ordenar por data (mais recente primeiro)
        jogos.sort(key=lambda x: x["data"], reverse=True)

        result = {
            "pair": pair,
            "team1_id": team1_afid,
            "team2_id": team2_afid,
            "team1_name": "",
            "team2_name": "",
            "total": len(jogos),
            "stats": stats,
            "ultimos_5": jogos[:5],
            "todos": jogos,
        }

        # Preencher nomes
        for j in jogos:
            if j["mandante_id"] == team1_afid:
                result["team1_name"] = j["mandante"]
                result["team2_name"] = j["visitante"]
                break
            elif j["visitante_id"] == team1_afid:
                result["team1_name"] = j["visitante"]
                result["team2_name"] = j["mandante"]
                break

        self._cache_set("h2h", cache_key, result)
        logger.info(f"🤝 H2H: {result['team1_name']} vs {result['team2_name']}: {len(jogos)} jogos")
        return result

    # ──────────────────── Standings ────────────────────

    def classificacao(self, league_id: int = 71, season: int = 2024) -> Optional[List[Dict]]:
        """
        Coleta classificação completa de uma liga/temporada.
        """
        cache_key = f"{league_id}_{season}"
        cached = self._cache_get("standings", cache_key)
        if cached:
            return cached.get("standings", [])

        resp = self._get("standings", {"league": league_id, "season": season})
        if not resp:
            return None

        raw = resp.get("response", [])
        if not raw:
            return None

        standings = []
        for team in raw[0]["league"]["standings"][0]:
            standings.append({
                "posicao": team["rank"],
                "time": team["team"]["name"],
                "time_id": team["team"]["id"],
                "pontos": team["points"],
                "jogos": team["all"]["played"],
                "vitorias": team["all"]["win"],
                "empates": team["all"]["draw"],
                "derrotas": team["all"]["lose"],
                "gols_pro": team["all"]["goals"]["for"],
                "gols_contra": team["all"]["goals"]["against"],
                "saldo": team["goalsDiff"],
                "forma": team.get("form", ""),
            })

        self._cache_set("standings", cache_key, {"league_id": league_id, "season": season, "standings": standings})
        logger.info(f"🏆 Standings {league_id}/{season}: {len(standings)} times")
        return standings

    # ──────────────────── Odds Internas ────────────────────

    def _coletar_probabilidades_mercado(self, fixture_id: int) -> Optional[Dict]:
        """
        Coleta probabilidades implícitas do mercado (USO INTERNO APENAS).

        ⚠️  REGRAS ABSOLUTAS:
        - NUNCA expor em endpoints públicos
        - NUNCA incluir em posts de blog
        - NUNCA logar payload com valores
        - NUNCA serializar em JSON público
        - Armazenar APENAS em data/_internal/
        - Usar APENAS como feature de calibração do modelo

        Retorna probabilidades normalizadas (sem menção a casas/linhas).
        """
        cache_path = INTERNAL_DIR / f"mkt_{fixture_id}.json"
        if cache_path.exists():
            try:
                with open(cache_path, "r") as f:
                    return json.load(f)
            except Exception:
                pass

        resp = self._get("odds", {"fixture": fixture_id, "bookmaker": 8})
        if not resp:
            return None

        bets = resp.get("response", [])
        if not bets:
            return None

        result = {"fixture_id": fixture_id}
        for bookmaker in bets:
            for bet in bookmaker.get("bookmakers", []):
                for market in bet.get("bets", []):
                    if market.get("name") == "Match Winner":
                        for val in market.get("values", []):
                            odd = float(val.get("odd", 0))
                            if odd > 0:
                                prob = 1.0 / odd
                                if val["value"] == "Home":
                                    result["prob_casa"] = prob
                                elif val["value"] == "Draw":
                                    result["prob_empate"] = prob
                                elif val["value"] == "Away":
                                    result["prob_fora"] = prob

                    if market.get("name") == "Goals Over/Under":
                        for val in market.get("values", []):
                            if val.get("value") == "Over 2.5":
                                odd = float(val.get("odd", 0))
                                if odd > 0:
                                    result["prob_over25"] = 1.0 / odd

        # Normalizar 1x2
        total = result.get("prob_casa", 0) + result.get("prob_empate", 0) + result.get("prob_fora", 0)
        if total > 0:
            result["prob_casa"] = round(result.get("prob_casa", 0) / total, 4)
            result["prob_empate"] = round(result.get("prob_empate", 0) / total, 4)
            result["prob_fora"] = round(result.get("prob_fora", 0) / total, 4)
        if result.get("prob_over25"):
            result["prob_over25"] = round(result["prob_over25"], 4)

        # Salvar em diretório INTERNO (nunca público)
        with open(cache_path, "w") as f:
            json.dump(result, f)

        return result if len(result) > 1 else None

    # ──────────────────── Enriquecimento de Rodada ────────────────────

    def enriquecer_rodada(
        self,
        partidas: List[Dict],
        league_id: int = 71,
        season: int = 2024,
        budget_max: int = 30,
    ) -> Dict[str, Any]:
        """
        Enriquece dados de uma rodada inteira com stats da API-Football.

        Coleta standings, team stats, H2H para cada jogo.
        Respeita budget de requests.

        Args:
            partidas: Lista de partidas (formato Cartola)
            league_id: ID da liga na API-Football
            season: Temporada para stats
            budget_max: Máximo de requests a usar

        Returns:
            {standings, team_stats: {afid: stats}, h2h: {pair: h2h}}
        """
        from src.analysis.fixture_collector import CARTOLA_TO_APIFOOTBALL

        requests_used = 0
        result = {
            "standings": None,
            "team_stats": {},
            "h2h": {},
        }

        # 1. Classificação (1 request ou cache)
        standings = self.classificacao(league_id, season)
        if standings:
            result["standings"] = standings
            # Checar se gastou request (se veio do cache, não gastou)
            cached = self._cache_get("standings", f"{league_id}_{season}")
            if not cached:
                requests_used += 1

        # 2. Team stats para cada time da rodada
        # Aceita dois formatos:
        #   - clube_casa_id / clube_visitante_id: IDs Cartola (convertidos via CARTOLA_TO_APIFOOTBALL)
        #   - mandante_id / visitante_id: IDs API-Football diretos (sem conversão)
        teams_done = set()
        for p in partidas:
            for campo_cart, campo_af in [
                ("clube_casa_id", "mandante_id"),
                ("clube_visitante_id", "visitante_id"),
            ]:
                # Tentar obter AF ID diretamente ou via conversão Cartola
                af_id = p.get(campo_af)
                if not af_id:
                    cid = p.get(campo_cart)
                    af_id = CARTOLA_TO_APIFOOTBALL.get(cid) if cid else None
                if not af_id or af_id in teams_done:
                    continue

                # Checar cache primeiro (incluindo outras leagues como fallback)
                # Ordem: liga solicitada (71=SA), depois Serie B (72), Copa do Brasil (75)
                fallback_leagues = [league_id, 72, 75] if league_id == 71 else [league_id]
                found = False
                for try_league in fallback_leagues:
                    cached = self._cache_get("team_stats", f"{af_id}_{try_league}_{season}")
                    if cached:
                        result["team_stats"][af_id] = cached
                        teams_done.add(af_id)
                        found = True
                        break
                if found:
                    continue

                if requests_used >= budget_max:
                    break

                # Tentar coletar: liga principal, depois fallback Serie B / Copa BR
                stats = None
                for try_league in fallback_leagues:
                    stats = self.stats_time_temporada(af_id, try_league, season)
                    requests_used += 1
                    if stats:
                        break
                    if requests_used >= budget_max:
                        break
                if stats:
                    result["team_stats"][af_id] = stats
                teams_done.add(af_id)

        # 3. H2H para cada confronto
        for p in partidas:
            # Obter AF IDs (direto ou via conversão Cartola)
            af_casa = p.get("mandante_id")
            if not af_casa:
                cid = p.get("clube_casa_id")
                af_casa = CARTOLA_TO_APIFOOTBALL.get(cid) if cid else None
            af_visit = p.get("visitante_id")
            if not af_visit:
                cid = p.get("clube_visitante_id")
                af_visit = CARTOLA_TO_APIFOOTBALL.get(cid) if cid else None
            if not af_casa or not af_visit:
                continue

            pair = f"{min(af_casa, af_visit)}-{max(af_casa, af_visit)}"

            # Checar cache
            cached = self._cache_get("h2h", pair)
            if cached:
                result["h2h"][pair] = cached
                continue

            if requests_used >= budget_max:
                break

            h2h = self.historico_h2h(af_casa, af_visit)
            if h2h:
                result["h2h"][pair] = h2h
                requests_used += 1

        logger.info(f"📊 Rodada enriquecida: {len(result['team_stats'])} teams, {len(result['h2h'])} h2h, ~{requests_used} requests")
        return result

    # ──────────────────── Helpers para Blog ────────────────────

    def resumo_time_para_post(self, af_team_id: int, season: int = 2024) -> Optional[Dict]:
        """
        Gera resumo formatado de um time para uso em posts de blog.

        Retorna dict com strings prontas para inserção no markdown.
        """
        stats = self.stats_time_temporada(af_team_id, season=season)
        if not stats:
            return None

        forma = stats.get("forma", "")
        ultimos_5 = forma[-5:] if len(forma) >= 5 else forma

        # Converter forma para emoji
        forma_emoji = ""
        for c in ultimos_5:
            if c == "W":
                forma_emoji += "🟢"
            elif c == "D":
                forma_emoji += "🟡"
            elif c == "L":
                forma_emoji += "🔴"

        return {
            "nome": stats["team_name"],
            "forma_emoji": forma_emoji,
            "forma_texto": f"{stats['vitorias']['total']}V {stats['empates']['total']}E {stats['derrotas']['total']}D",
            "gols_pro_media": stats["gols_pro"]["media"],
            "gols_contra_media": stats["gols_contra"]["media"],
            "gols_pro_total": stats["gols_pro"]["total"],
            "gols_contra_total": stats["gols_contra"]["total"],
            "clean_sheets": stats["clean_sheets"]["total"],
            "maior_sequencia_vitorias": stats["maior_sequencia"]["vitorias"],
            "penaltis": f"{stats['penaltis']['marcados']}/{stats['penaltis']['total']}",
            "gols_por_minuto": stats.get("gols_por_minuto", {}),
            "desempenho_casa": f"{stats['vitorias']['casa']}V {stats['empates']['casa']}E {stats['derrotas']['casa']}D ({stats['gols_pro']['media_casa']} gols/jogo)",
            "desempenho_fora": f"{stats['vitorias']['fora']}V {stats['empates']['fora']}E {stats['derrotas']['fora']}D ({stats['gols_pro']['media_fora']} gols/jogo)",
        }

    def resumo_h2h_para_post(self, team1_afid: int, team2_afid: int) -> Optional[Dict]:
        """
        Gera resumo de H2H formatado para posts de blog.
        """
        h2h = self.historico_h2h(team1_afid, team2_afid)
        if not h2h or not h2h.get("ultimos_5"):
            return None

        stats = h2h["stats"]
        ultimos = h2h["ultimos_5"]

        # Formatar últimos jogos
        jogos_txt = []
        for j in ultimos[:3]:
            jogos_txt.append(f"{j['data']}: {j['mandante']} {j['gols_mandante']}x{j['gols_visitante']} {j['visitante']} ({j['liga']})")

        return {
            "team1": h2h["team1_name"],
            "team2": h2h["team2_name"],
            "total_jogos": h2h["total"],
            "vitorias_team1": stats["team1_wins"],
            "empates": stats["draws"],
            "vitorias_team2": stats["team2_wins"],
            "ultimos_jogos": jogos_txt,
        }

    def resumo_cache(self) -> Dict:
        """Retorna estatísticas do cache."""
        stats = {}
        for category in ["fixture_stats", "fixture_events", "team_stats", "standings", "h2h"]:
            subdir = CACHE_DIR / category
            if subdir.exists():
                files = list(subdir.glob("*.json"))
                stats[category] = len(files)
            else:
                stats[category] = 0

        internal = list(INTERNAL_DIR.glob("*.json"))
        stats["internal_data"] = len(internal)

        return stats
