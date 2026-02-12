"""
FootballDataClient — Cliente para football-data.org API v4.

Fonte GRATUITA complementar/fallback para API-Football.
Cobre Brasileirão Série A (BSA) com:
  - Fixtures (jogos agendados e resultados)
  - Standings (classificação)
  - Scorers (artilheiros com gols/assists)
  - H2H (head-to-head via match ID)
  - Team info (elenco, competições)

Rate limit: 10 req/min (free tier).
Auth: header X-Auth-Token.

Ref: https://www.football-data.org/documentation/quickstart
"""
import json
import logging
import sys
import time
from datetime import datetime, timedelta, date, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

sys.path.append(str(Path(__file__).parent.parent.parent))

logger = logging.getLogger("FootballDataClient")

CACHE_DIR = Path(__file__).parent.parent.parent / "data" / "fdo_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

BRT = timezone(timedelta(hours=-3))

# TTLs por categoria (em segundos)
CACHE_TTL = {
    "matches": 3600,        # 1h — jogos mudam status
    "standings": 7200,      # 2h  
    "scorers": 86400,       # 1d
    "teams": 604800,        # 7d
    "h2h": 2592000,         # 30d
    "team_matches": 86400,  # 1d
}

# Competição BSA
BSA = "BSA"
BSA_SEASON = 2026  # temporada 2026 do Brasileirão Série A


class FootballDataClient:
    """
    Cliente para football-data.org v4.
    
    Fallback/complemento ao API-Football para:
    - Artilheiros (não disponível no API-Football free)
    - Standings redundantes (validação cruzada)
    - H2H via match_id
    - Fixtures com odds
    """

    API_BASE = "https://api.football-data.org/v4"

    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or self._load_token()
        self._session = None
        self._last_request_time = 0.0
        self._request_count_minute = 0
        self._minute_start = 0.0

    @staticmethod
    def _load_token() -> str:
        import os
        token = os.environ.get("FOOTBALL_DATA_TOKEN", "")
        if not token:
            try:
                from config.settings import settings
                token = getattr(settings, "FOOTBALL_DATA_TOKEN", "")
            except Exception:
                pass
        if not token:
            token = "f66575040e5349b1860b729baccdf1bc"
        return token

    @property
    def session(self):
        if self._session is None:
            import requests
            self._session = requests.Session()
            self._session.headers.update({
                "X-Auth-Token": self.api_token,
                "Accept": "application/json",
            })
        return self._session

    # ──────────────────── Cache ────────────────────

    def _cache_path(self, category: str, key: str) -> Path:
        subdir = CACHE_DIR / category
        subdir.mkdir(parents=True, exist_ok=True)
        return subdir / f"{key}.json"

    def _cache_get(self, category: str, key: str) -> Optional[Dict]:
        path = self._cache_path(category, key)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            cached_at = data.get("_cached_at", "")
            ttl = CACHE_TTL.get(category, 86400)
            if cached_at:
                dt = datetime.fromisoformat(cached_at)
                if (datetime.now() - dt).total_seconds() > ttl:
                    return None
            return data
        except Exception:
            return None

    def _cache_set(self, category: str, key: str, data: Any) -> None:
        if isinstance(data, dict):
            data["_cached_at"] = datetime.now().isoformat()
        elif isinstance(data, list):
            data = {"_data": data, "_cached_at": datetime.now().isoformat()}
        path = self._cache_path(category, key)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ──────────────────── Rate Limiter ────────────────────

    def _rate_limit(self):
        """Respeita 10 req/min com margem de segurança (max 8 req/min)."""
        now = time.time()

        # Reset counter a cada minuto
        if now - self._minute_start > 60:
            self._request_count_minute = 0
            self._minute_start = now

        # Se atingiu 8 req neste minuto, esperar
        if self._request_count_minute >= 8:
            wait = 60 - (now - self._minute_start) + 1
            if wait > 0:
                logger.debug(f"Rate limit: aguardando {wait:.1f}s")
                time.sleep(wait)
            self._request_count_minute = 0
            self._minute_start = time.time()

        # Mínimo 3s entre requests
        elapsed = now - self._last_request_time
        if elapsed < 3.0:
            time.sleep(3.0 - elapsed)

    # ──────────────────── API calls ────────────────────

    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Chamada à API com rate limiting e retry."""
        self._rate_limit()
        url = f"{self.API_BASE}/{endpoint}"
        try:
            self._last_request_time = time.time()
            self._request_count_minute += 1
            r = self.session.get(url, params=params or {}, timeout=15)

            if r.status_code == 429:
                # Rate limited — esperar e retry
                retry = int(r.headers.get("X-RequestCounter-Reset", 60))
                logger.warning(f"football-data.org rate limited, aguardando {retry}s")
                time.sleep(retry + 1)
                self._request_count_minute = 0
                self._minute_start = time.time()
                self._last_request_time = time.time()
                r = self.session.get(url, params=params or {}, timeout=15)

            if r.status_code != 200:
                logger.warning(f"football-data.org {endpoint}: HTTP {r.status_code}")
                return None

            return r.json()
        except Exception as e:
            logger.error(f"football-data.org {endpoint}: {e}")
            return None

    # ──────────────────── Matches/Fixtures ────────────────────

    def jogos_rodada(self, rodada: int, season: int = BSA_SEASON) -> Optional[List[Dict]]:
        """Busca jogos de uma rodada específica do BSA."""
        cache_key = f"bsa_{season}_md{rodada}"
        cached = self._cache_get("matches", cache_key)
        if cached:
            return cached.get("_data", cached.get("matches", []))

        data = self._get(f"competitions/{BSA}/matches", {
            "matchday": rodada,
            "season": season,
        })
        if not data:
            return None

        matches = data.get("matches", [])
        if not matches:
            return None

        result = []
        for m in matches:
            result.append(self._parse_match(m))

        self._cache_set("matches", cache_key, result)
        logger.info(f"⚽ football-data: {len(result)} jogos rodada {rodada}")
        return result

    def jogos_periodo(
        self, date_from: str, date_to: str, season: int = BSA_SEASON
    ) -> Optional[List[Dict]]:
        """Busca jogos num período (formato YYYY-MM-DD)."""
        cache_key = f"bsa_{season}_{date_from}_{date_to}"
        cached = self._cache_get("matches", cache_key)
        if cached:
            return cached.get("_data", cached.get("matches", []))

        data = self._get(f"competitions/{BSA}/matches", {
            "dateFrom": date_from,
            "dateTo": date_to,
            "season": season,
        })
        if not data:
            return None

        matches = data.get("matches", [])
        result = [self._parse_match(m) for m in matches]
        if result:
            self._cache_set("matches", cache_key, result)
        return result

    def jogos_time(
        self, team_id: int, status: str = "SCHEDULED",
        limit: int = 15, season: Optional[int] = None
    ) -> Optional[List[Dict]]:
        """Busca jogos de um time específico."""
        cache_key = f"team_{team_id}_{status}_{season or 'all'}_{limit}"
        cached = self._cache_get("team_matches", cache_key)
        if cached:
            return cached.get("_data", [])

        params: Dict[str, Any] = {"status": status, "limit": limit}
        if season:
            params["season"] = season
        data = self._get(f"teams/{team_id}/matches", params)
        if not data:
            return None

        matches = data.get("matches", [])
        result = [self._parse_match(m) for m in matches]
        if result:
            self._cache_set("team_matches", cache_key, result)
        return result

    def h2h(self, match_id: int, limit: int = 10) -> Optional[Dict]:
        """Busca head-to-head de um match_id."""
        cache_key = f"match_{match_id}"
        cached = self._cache_get("h2h", cache_key)
        if cached:
            return cached

        data = self._get(f"matches/{match_id}/head2head", {"limit": limit})
        if not data:
            return None

        agg = data.get("aggregates", {})
        matches = data.get("matches", [])

        result = {
            "match_id": match_id,
            "total_jogos": agg.get("numberOfMatches", 0),
            "home_team_id": agg.get("homeTeam", {}).get("id"),
            "away_team_id": agg.get("awayTeam", {}).get("id"),
            "vitorias_casa": agg.get("homeTeam", {}).get("wins", 0),
            "empates": agg.get("homeTeam", {}).get("draws", 0),
            "vitorias_fora": agg.get("awayTeam", {}).get("wins", 0),
            "home_team": agg.get("homeTeam", {}).get("name", ""),
            "away_team": agg.get("awayTeam", {}).get("name", ""),
            "ultimos": [],
        }

        for m in matches[:10]:
            ht = m.get("homeTeam", {})
            at = m.get("awayTeam", {})
            sc = m.get("score", {}).get("fullTime", {})
            result["ultimos"].append({
                "data": m.get("utcDate", "")[:10],
                "mandante": ht.get("shortName", ht.get("name", "?")),
                "mandante_id": ht.get("id"),
                "visitante": at.get("shortName", at.get("name", "?")),
                "visitante_id": at.get("id"),
                "gols_m": sc.get("home"),
                "gols_v": sc.get("away"),
                "competicao": m.get("competition", {}).get("name", "?"),
            })

        self._cache_set("h2h", cache_key, result)
        logger.info(f"⚔️ H2H match {match_id}: {result['total_jogos']} jogos")
        return result

    def h2h_por_times(self, fdo_id1: int, fdo_id2: int, limit: int = 10) -> Optional[Dict]:
        """
        Busca H2H entre dois times por FDO team IDs.

        Encontra automaticamente um match_id entre os times,
        depois chama h2h(match_id) para obter o histórico completo.
        Funciona com jogos FINISHED ou SCHEDULED.
        """
        # Cache por par de times (ordenado)
        pair_key = f"pair_{min(fdo_id1, fdo_id2)}_{max(fdo_id1, fdo_id2)}"
        cached = self._cache_get("h2h", pair_key)
        if cached:
            return cached

        # Buscar jogos finalizados de um dos times para encontrar um match_id
        match_id = None
        for status in ["FINISHED", "SCHEDULED"]:
            data = self._get(f"teams/{fdo_id1}/matches", {
                "status": status,
                "limit": 50,
            })
            if data:
                for m in data.get("matches", []):
                    ht_id = m.get("homeTeam", {}).get("id")
                    at_id = m.get("awayTeam", {}).get("id")
                    if {ht_id, at_id} == {fdo_id1, fdo_id2}:
                        match_id = m.get("id")
                        break
            if match_id:
                break

        if not match_id:
            logger.info(f"FDO H2H: nenhum jogo encontrado entre {fdo_id1} e {fdo_id2}")
            return None

        # Buscar H2H usando o match_id
        result = self.h2h(match_id, limit=limit)
        if result:
            # Cache por par de times também
            self._cache_set("h2h", pair_key, result)
        return result

    # ──────────────────── Standings ────────────────────

    def classificacao(self, season: int = BSA_SEASON) -> Optional[List[Dict]]:
        """Classificação atual do BSA."""
        cache_key = f"bsa_{season}"
        cached = self._cache_get("standings", cache_key)
        if cached:
            return cached.get("_data", [])

        data = self._get(f"competitions/{BSA}/standings", {"season": season})
        if not data:
            return None

        standings = data.get("standings", [])
        if not standings:
            return None

        # Pega a tabela TOTAL (pode ter HOME/AWAY também)
        table = None
        for s in standings:
            if s.get("type") == "TOTAL":
                table = s.get("table", [])
                break
        if not table:
            table = standings[0].get("table", [])

        result = []
        for t in table:
            team = t.get("team", {})
            result.append({
                "posicao": t.get("position", 0),
                "time": team.get("shortName", team.get("name", "?")),
                "time_id": team.get("id", 0),
                "escudo": team.get("crest", ""),
                "jogos": t.get("playedGames", 0),
                "pontos": t.get("points", 0),
                "vitorias": t.get("won", 0),
                "empates": t.get("draw", 0),
                "derrotas": t.get("lost", 0),
                "gols_pro": t.get("goalsFor", 0),
                "gols_contra": t.get("goalsAgainst", 0),
                "saldo": t.get("goalDifference", 0),
                "forma": t.get("form", ""),
            })

        self._cache_set("standings", cache_key, result)
        logger.info(f"📊 Classificação BSA {season}: {len(result)} times")
        return result

    # ──────────────────── Scorers/Artilheiros ────────────────────

    def artilheiros(self, limit: int = 20, season: int = BSA_SEASON) -> Optional[List[Dict]]:
        """Top scorers do Brasileirão — EXCLUSIVO (API-Football free não tem)."""
        cache_key = f"bsa_{season}_top{limit}"
        cached = self._cache_get("scorers", cache_key)
        if cached:
            return cached.get("_data", [])

        data = self._get(f"competitions/{BSA}/scorers", {
            "limit": limit,
            "season": season,
        })
        if not data:
            return None

        scorers = data.get("scorers", [])
        result = []
        for s in scorers:
            player = s.get("player", {})
            team = s.get("team", {})
            result.append({
                "jogador": player.get("name", "?"),
                "jogador_id": player.get("id", 0),
                "time": team.get("shortName", team.get("name", "?")),
                "time_id": team.get("id", 0),
                "gols": s.get("goals", 0),
                "assists": s.get("assists", 0),
                "penaltis": s.get("penalties", 0),
                "jogos": s.get("playedMatches", 0),
                "nacionalidade": player.get("nationality", ""),
            })

        self._cache_set("scorers", cache_key, result)
        logger.info(f"🏆 Artilheiros BSA: {len(result)} jogadores")
        return result

    # ──────────────────── Team Info ────────────────────

    def info_time(self, team_id: int) -> Optional[Dict]:
        """Informações completas de um time (elenco, técnico, etc.)."""
        cache_key = f"team_{team_id}"
        cached = self._cache_get("teams", cache_key)
        if cached:
            return cached

        data = self._get(f"teams/{team_id}")
        if not data:
            return None

        result = {
            "id": data.get("id"),
            "nome": data.get("name", ""),
            "nome_curto": data.get("shortName", ""),
            "sigla": data.get("tla", ""),
            "escudo": data.get("crest", ""),
            "fundacao": data.get("founded"),
            "estadio": data.get("venue", ""),
            "tecnico": data.get("coach", {}).get("name", ""),
            "tecnico_nacionalidade": data.get("coach", {}).get("nationality", ""),
            "elenco_count": len(data.get("squad", [])),
        }

        self._cache_set("teams", cache_key, result)
        return result

    # ──────────────────── Helpers ────────────────────

    def _parse_match(self, m: Dict) -> Dict:
        """Converte um match raw da API para formato padronizado."""
        ht = m.get("homeTeam", {})
        at = m.get("awayTeam", {})
        sc = m.get("score", {})
        ft = sc.get("fullTime", {})
        ht_sc = sc.get("halfTime", {})

        # Converter UTC para BRT
        utc_date = m.get("utcDate", "")
        data_brt = ""
        if utc_date:
            try:
                dt = datetime.fromisoformat(utc_date.replace("Z", "+00:00"))
                data_brt = dt.astimezone(BRT).strftime("%Y-%m-%d %H:%M")
            except Exception:
                data_brt = utc_date[:16]

        # Converter siglas FDO→Cartola (PAU→SAO, FBP→GRE, SCI→INT, etc.)
        try:
            from src.utils.team_mapping import normalize_fdo_sigla
            mandante_sigla = normalize_fdo_sigla(ht.get("tla", ""))
            visitante_sigla = normalize_fdo_sigla(at.get("tla", ""))
        except ImportError:
            mandante_sigla = ht.get("tla", "")
            visitante_sigla = at.get("tla", "")

        return {
            "match_id": m.get("id"),
            "rodada": m.get("matchday"),
            "status": m.get("status", ""),
            "data_utc": utc_date,
            "data_brt": data_brt,
            "mandante": ht.get("shortName", ht.get("name", "?")),
            "mandante_id": ht.get("id", 0),
            "mandante_sigla": mandante_sigla,
            "visitante": at.get("shortName", at.get("name", "?")),
            "visitante_id": at.get("id", 0),
            "visitante_sigla": visitante_sigla,
            "gols_mandante": ft.get("home"),
            "gols_visitante": ft.get("away"),
            "gols_ht_m": ht_sc.get("home"),
            "gols_ht_v": ht_sc.get("away"),
            "competicao": m.get("competition", {}).get("name", "BSA"),
            "estadio": m.get("venue", ""),
            "arbitro": (m.get("referees") or [{}])[0].get("name", "") if m.get("referees") else "",
        }

    def artilheiro_time(self, team_id: int, season: int = BSA_SEASON) -> Optional[Dict]:
        """Retorna o artilheiro de um time específico (usa cache de artilheiros)."""
        artilheiros = self.artilheiros(limit=30, season=season)
        if not artilheiros:
            return None
        for a in artilheiros:
            if a["time_id"] == team_id:
                return a
        return None

    def posicao_time(self, team_id: int, season: int = BSA_SEASON) -> Optional[Dict]:
        """Retorna posição e dados de classificação de um time."""
        classificacao = self.classificacao(season=season)
        if not classificacao:
            return None
        for t in classificacao:
            if t["time_id"] == team_id:
                return t
        return None

    def resumo_cache(self) -> Dict[str, int]:
        """Contagem de itens no cache."""
        result = {}
        for cat in CACHE_TTL:
            subdir = CACHE_DIR / cat
            if subdir.exists():
                result[cat] = len(list(subdir.glob("*.json")))
            else:
                result[cat] = 0
        return result
