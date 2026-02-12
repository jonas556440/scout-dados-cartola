"""
FixtureCollector — Coleta de calendário multi-competição via API-Football v3.

Resolve o problema de dias de descanso falsos:
se um time jogou Copa do Brasil ou Carioca/Paulista entre rodadas do
Brasileirão, o descanso real é menor que o calculado apenas com API Cartola.

Estratégia (free tier: 100 req/dia, window rolling de 3 dias):
  1. Job diário coleta fixtures da data atual (todas as competições BR)
  2. Cache local em data/fixtures/YYYY-MM-DD.json (idempotente)  
  3. dias_descanso_real(team_id, data_ref) → busca último jogo ANTES da
     data_ref em qualquer competição
  4. Fallback: se não há dados suficientes, usa heurística (cap de 7 dias)

API-Football v3 (api-sports.io):
  - free tier: 100 req/dia, window ±1 dia do dia atual
  - cobre TODAS as competições BR (Série A, Copa do Brasil, Libertadores,
    Carioca, Paulista, Gaúcho, etc.)
  - auth via header x-apisports-key

Refs:
  Clark (2005): rest days impact ~3-5% on goal scoring
  FiveThirtyEight SPI: uses full calendar for fatigue adjustment
"""
import json
import logging
import sys
from datetime import datetime, timedelta, date, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

sys.path.append(str(Path(__file__).parent.parent.parent))

logger = logging.getLogger("FixtureCollector")

FIXTURES_DIR = Path(__file__).parent.parent.parent / "data" / "fixtures"
FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

# Fuso horário do Brasil (BRT = UTC-3)
# Jogos brasileiros acontecem em BRT; API-Football retorna UTC.
# Sem converter, um jogo de 07/02 21h BRT aparece como 08/02 00h UTC.
BRT = timezone(timedelta(hours=-3))

# ======== Mapeamento CartID → API-Football ID ========
# CartID = ID na API do Cartola FC
# AFID   = ID na API-Football (api-sports.io)
CARTOLA_TO_APIFOOTBALL: Dict[int, int] = {
    262: 127,    # FLA - Flamengo
    275: 121,    # PAL - Palmeiras
    264: 131,    # COR - Corinthians
    276: 126,    # SAO - São Paulo
    277: 128,    # SAN - Santos
    263: 120,    # BOT - Botafogo
    266: 124,    # FLU - Fluminense
    267: 133,    # VAS - Vasco da Gama
    284: 130,    # GRE - Grêmio
    285: 119,    # INT - Internacional
    282: 1062,   # CAM - Atlético-MG
    283: 135,    # CRU - Cruzeiro
    265: 118,    # BAH - Bahia
    287: 136,    # VIT - Vitória
    293: 134,    # CAP - Athletico-PR
    280: 794,    # RBB - Red Bull Bragantino
    315: 132,    # CHA - Chapecoense
    2305: 7848,  # MIR - Mirassol
    364: 1198,   # REM - Remo
    294: 147,    # CFC - Coritiba
}

# Reverso: AFID → CartID
APIFOOTBALL_TO_CARTOLA: Dict[int, int] = {v: k for k, v in CARTOLA_TO_APIFOOTBALL.items()}

# Cache de ID_APIFOOTBALL descobertos dinamicamente
_dynamic_ids: Dict[int, int] = {}


class FixtureCollector:
    """Coleta e cacheia fixtures multi-competição via API-Football."""

    API_BASE = "https://v3.football.api-sports.io"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or self._load_api_key()
        self._session = None

    # ──────────────────── Config ────────────────────

    @staticmethod
    def _load_api_key() -> str:
        """Carrega API key de env var ou config."""
        import os
        key = os.environ.get("APIFOOTBALL_KEY", "")
        if not key:
            # Tentar ler de config/settings.py
            try:
                from config.settings import settings
                key = getattr(settings, "APIFOOTBALL_KEY", "")
            except Exception:
                pass
        if not key:
            # Fallback: mesma key usada pelo StatsEnricher
            key = "d354c8d1f1d70486fe3b6b69cc905381"
            logger.info("APIFOOTBALL_KEY: usando fallback hardcoded (mesma do StatsEnricher)")
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

    # ──────────────────── API calls ────────────────────

    def _get(self, endpoint: str, params: Dict) -> Optional[Dict]:
        """Faz chamada à API-Football com rate limit e error handling."""
        url = f"{self.API_BASE}/{endpoint}"
        try:
            r = self.session.get(url, params=params, timeout=15)
            if r.status_code != 200:
                logger.warning(f"API-Football {endpoint}: HTTP {r.status_code}")
                return None
            data = r.json()
            errors = data.get("errors", {})
            if errors:
                # Free tier pode retornar errors como dict com msg
                if isinstance(errors, dict) and errors:
                    logger.warning(f"API-Football {endpoint}: {errors}")
                    return None
                if isinstance(errors, list) and errors:
                    logger.warning(f"API-Football {endpoint}: {errors}")
                    return None
            return data
        except Exception as e:
            logger.error(f"API-Football {endpoint}: {e}")
            return None

    def status_conta(self) -> Dict:
        """Retorna status da conta (requests usados/restantes)."""
        data = self._get("status", {})
        if data:
            resp = data.get("response", {})
            return {
                "plan": resp.get("subscription", {}).get("plan", "?"),
                "used": resp.get("requests", {}).get("current", 0),
                "limit": resp.get("requests", {}).get("limit_day", 100),
            }
        return {"plan": "?", "used": 0, "limit": 100}

    # ──────────────────── Coleta de fixtures ────────────────────

    def coletar_fixtures_data(self, data: str) -> List[Dict]:
        """
        Coleta todos os fixtures de uma data (YYYY-MM-DD).
        Filtra apenas jogos de times brasileiros.
        Salva em cache local.

        Free tier: window rolling de ±1 dia relativo ao dia atual.
        """
        cache_file = FIXTURES_DIR / f"{data}.json"

        # Retornar do cache se já coletado
        if cache_file.exists():
            with open(cache_file, "r", encoding="utf-8") as f:
                cached = json.load(f)
            return cached.get("fixtures", [])

        resp = self._get("fixtures", {"date": data})
        if not resp:
            return []

        all_fixtures = resp.get("response", [])

        # Filtrar apenas Brasil
        br_fixtures = []
        for fix in all_fixtures:
            country = fix.get("league", {}).get("country", "").lower()
            if country in ("brazil", "brasil"):
                # Converter data UTC para BRT para ter a data correta no Brasil
                ts = fix["fixture"]["timestamp"]
                brt_date = datetime.fromtimestamp(ts, tz=BRT).strftime("%Y-%m-%dT%H:%M:%S-03:00")
                br_fixtures.append({
                    "fixture_id": fix["fixture"]["id"],
                    "date": brt_date,
                    "date_utc": fix["fixture"]["date"],
                    "timestamp": ts,
                    "status": fix["fixture"]["status"]["short"],
                    "league": fix["league"]["name"],
                    "league_id": fix["league"]["id"],
                    "home_id": fix["teams"]["home"]["id"],
                    "home_name": fix["teams"]["home"]["name"],
                    "away_id": fix["teams"]["away"]["id"],
                    "away_name": fix["teams"]["away"]["name"],
                    "goals_home": fix["goals"].get("home"),
                    "goals_away": fix["goals"].get("away"),
                })

        # Salvar em cache
        cache_data = {
            "date": data,
            "collected_at": datetime.now().isoformat(),
            "total_world": len(all_fixtures),
            "total_brazil": len(br_fixtures),
            "fixtures": br_fixtures,
        }
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)

        logger.info(f"📅 Fixtures {data}: {len(br_fixtures)} jogos BR (de {len(all_fixtures)} mundial)")
        return br_fixtures

    def coletar_hoje(self) -> List[Dict]:
        """Coleta fixtures de hoje e dias adjacentes (window do free tier)."""
        hoje = date.today()
        todos = []
        for delta in [0, -1, 1]:
            d = hoje + timedelta(days=delta)
            fixtures = self.coletar_fixtures_data(d.isoformat())
            todos.extend(fixtures)
        return todos

    def coletar_periodo(self, inicio: date, fim: date) -> List[Dict]:
        """Coleta fixtures de um período. Usa cache, só chama API se necessário."""
        todos = []
        d = inicio
        while d <= fim:
            fixtures = self.coletar_fixtures_data(d.isoformat())
            todos.extend(fixtures)
            d += timedelta(days=1)
        return todos

    # ──────────────────── Cálculo de descanso real ────────────────────

    def _carregar_fixtures_cache(self) -> List[Dict]:
        """Carrega todos os fixtures cacheados."""
        todas = []
        for f in sorted(FIXTURES_DIR.glob("*.json")):
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                todas.extend(data.get("fixtures", []))
            except Exception:
                continue
        return todas

    def _jogos_time_afid(self, af_team_id: int) -> List[Dict]:
        """Retorna todos os jogos finalizados de um time (API-Football ID), ordenados por data."""
        fixtures = self._carregar_fixtures_cache()
        jogos = []
        for fix in fixtures:
            if fix.get("status") not in ("FT", "AET", "PEN"):
                continue
            if fix["home_id"] == af_team_id or fix["away_id"] == af_team_id:
                jogos.append(fix)
        # Ordenar por timestamp
        jogos.sort(key=lambda x: x.get("timestamp", 0))
        return jogos

    def dias_descanso_real(
        self,
        cartola_id: int,
        data_ref: str,
        fallback_brasileirao: Optional[int] = None,
    ) -> Optional[int]:
        """
        Calcula dias de descanso REAL de um time considerando TODAS as competições.

        Args:
            cartola_id: ID do time na API Cartola
            data_ref: Data de referência (YYYY-MM-DD ou ISO timestamp)
            fallback_brasileirao: Descanso calculado só pelo Brasileirão (fallback)

        Returns:
            Dias de descanso real (ou None se sem dados)
        """
        af_id = CARTOLA_TO_APIFOOTBALL.get(cartola_id) or _dynamic_ids.get(cartola_id)
        if not af_id:
            # Sem mapeamento — usar fallback com cap
            if fallback_brasileirao is not None:
                return min(fallback_brasileirao, 7)  # Cap de 7 dias
            return None

        # Parse data_ref — converter tudo para date BRT
        try:
            if "T" in data_ref:
                ref_dt = datetime.fromisoformat(data_ref.replace("Z", "+00:00"))
                # Se não tem timezone, assumir BRT
                if ref_dt.tzinfo is None:
                    ref_dt = ref_dt.replace(tzinfo=BRT)
                ref_date = ref_dt.astimezone(BRT).date()
            elif " " in data_ref.strip():
                # Formato "2026-02-12 19:00:00" (Cartola, já em BRT)
                ref_dt = datetime.strptime(data_ref.strip()[:19], "%Y-%m-%d %H:%M:%S")
                ref_date = ref_dt.date()
            else:
                ref_date = datetime.strptime(data_ref.strip(), "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return fallback_brasileirao

        jogos = self._jogos_time_afid(af_id)

        # Encontrar último jogo ANTES de data_ref
        # Usar timestamp → BRT date para comparação correta
        ultimo_jogo_date = None
        for j in reversed(jogos):
            ts = j.get("timestamp", 0)
            if ts:
                jogo_date = datetime.fromtimestamp(ts, tz=BRT).date()
            else:
                try:
                    jogo_date = datetime.fromisoformat(
                        j["date"].replace("Z", "+00:00")
                    ).astimezone(BRT).date()
                except (ValueError, TypeError):
                    continue

            if jogo_date < ref_date:
                ultimo_jogo_date = jogo_date
                break

        if ultimo_jogo_date is None:
            # Sem dados de jogos anteriores no cache
            if fallback_brasileirao is not None:
                return min(fallback_brasileirao, 7)
            return None

        descanso = (ref_date - ultimo_jogo_date).days
        return max(1, descanso)

    def dias_descanso_rodada(
        self,
        partidas: List[Dict],
        fallback_brasileirao: Optional[Dict[int, Optional[int]]] = None,
    ) -> Dict[int, Optional[int]]:
        """
        Calcula descanso real para todos os times de uma rodada.

        Args:
            partidas: Lista de partidas do Cartola (com clubes e datas)
            fallback_brasileirao: Descanso calculado só pelo Brasileirão

        Returns:
            Dict[cartola_id, dias_descanso]
        """
        if fallback_brasileirao is None:
            fallback_brasileirao = {}

        descanso = {}
        for p in partidas:
            for campo_id, campo_data in [
                ("clube_casa_id", "partida_data"),
                ("clube_visitante_id", "partida_data"),
            ]:
                cid = p.get(campo_id)
                data_jogo = p.get(campo_data, "")
                if cid and data_jogo:
                    fb = fallback_brasileirao.get(cid)
                    descanso[cid] = self.dias_descanso_real(cid, data_jogo, fb)

        return descanso

    # ──────────────────── Busca dinâmica de IDs ────────────────────

    def buscar_id_time(self, nome_time: str) -> Optional[int]:
        """Busca ID API-Football de um time pelo nome (usa 1 request)."""
        resp = self._get("teams", {"search": nome_time})
        if resp:
            teams = resp.get("response", [])
            # Filtrar por país Brasil
            for t in teams:
                country = t.get("team", {}).get("country", "").lower()
                if country in ("brazil", "brasil"):
                    af_id = t["team"]["id"]
                    logger.info(f"🔍 {nome_time} → API-Football ID: {af_id}")
                    return af_id
        return None

    def completar_mapeamento(self, clubes: Dict) -> None:
        """
        Tenta completar IDs faltantes via busca por nome.
        Usa cache para não gastar requests repetidos.
        """
        global _dynamic_ids
        cache_file = FIXTURES_DIR / "_id_mapping.json"

        # Carregar cache de IDs dinâmicos
        if cache_file.exists():
            with open(cache_file, "r", encoding="utf-8") as f:
                _dynamic_ids.update({int(k): v for k, v in json.load(f).items()})

        for cid_str, clube in clubes.items():
            cid = int(cid_str)
            if cid in CARTOLA_TO_APIFOOTBALL or cid in _dynamic_ids:
                continue  # Já mapeado

            nome = clube.get("nome", "")
            if not nome:
                continue

            af_id = self.buscar_id_time(nome)
            if af_id:
                _dynamic_ids[cid] = af_id

        # Salvar cache
        if _dynamic_ids:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(_dynamic_ids, f)

    # ──────────────────── Odds (interno) ────────────────────

    def coletar_odds_fixture(self, fixture_id: int) -> Optional[Dict]:
        """
        Coleta odds de um fixture (uso INTERNO apenas — nunca expor no frontend).

        ⚠️  IMPORTANTE:
        - Odds NÃO devem ser expostas em endpoints públicos
        - NÃO devem aparecer em posts de blog
        - NÃO devem ser logadas em texto legível
        - Usar apenas como feature interna para calibração do modelo

        Retorna dict com probabilidades implícitas (não odds brutas):
          {prob_home, prob_draw, prob_away, over25_prob}
        """
        resp = self._get("odds", {"fixture": fixture_id, "bookmaker": 8})  # Bet365
        if not resp:
            return None

        bets = resp.get("response", [])
        if not bets:
            return None

        result = {}
        for bookmaker in bets:
            for bet in bookmaker.get("bookmakers", []):
                for market in bet.get("bets", []):
                    if market.get("name") == "Match Winner":
                        for val in market.get("values", []):
                            odd = float(val.get("odd", 0))
                            if odd > 0:
                                prob = 1.0 / odd
                                if val["value"] == "Home":
                                    result["prob_home"] = prob
                                elif val["value"] == "Draw":
                                    result["prob_draw"] = prob
                                elif val["value"] == "Away":
                                    result["prob_away"] = prob

                    if market.get("name") == "Goals Over/Under":
                        for val in market.get("values", []):
                            if val.get("value") == "Over 2.5":
                                odd = float(val.get("odd", 0))
                                if odd > 0:
                                    result["over25_prob"] = 1.0 / odd

        # Normalizar para somar 100%
        total = (result.get("prob_home", 0) + result.get("prob_draw", 0)
                 + result.get("prob_away", 0))
        if total > 0:
            result["prob_home"] = round(result.get("prob_home", 0) / total * 100, 1)
            result["prob_draw"] = round(result.get("prob_draw", 0) / total * 100, 1)
            result["prob_away"] = round(result.get("prob_away", 0) / total * 100, 1)
        if result.get("over25_prob"):
            result["over25_prob"] = round(result["over25_prob"] * 100, 1)

        return result if result else None

    # ──────────────────── Utilitários ────────────────────

    def resumo_cache(self) -> Dict:
        """Retorna estatísticas do cache de fixtures."""
        arquivos = list(FIXTURES_DIR.glob("*.json"))
        total_fixtures = 0
        datas = []
        for f in arquivos:
            if f.name.startswith("_"):
                continue
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                total_fixtures += len(data.get("fixtures", []))
                datas.append(f.stem)
            except Exception:
                continue

        return {
            "arquivos": len(arquivos),
            "total_fixtures_br": total_fixtures,
            "datas": sorted(datas),
            "primeira_data": min(datas) if datas else None,
            "ultima_data": max(datas) if datas else None,
        }
