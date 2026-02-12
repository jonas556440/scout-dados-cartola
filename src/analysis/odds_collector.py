"""
OddsCollector — Coleta de probabilidades implícitas do mercado.

Fonte: The Odds API (https://the-odds-api.com)
Plano: Starter (500 créditos/mês, gratuito)
Budget: 6 coletas/dia × 2 markets = 12 créditos/dia ≈ 360/mês

⚠️  REGRAS ABSOLUTAS (COMPLIANCE):
  - NUNCA expor odds/linhas em endpoints públicos
  - NUNCA incluir em posts de blog
  - NUNCA serializar em JSON público
  - NUNCA mostrar nomes de casas de apostas
  - Armazenar APENAS em data/_internal/odds/
  - Usar APENAS como feature de calibração do modelo preditivo
  - Compatível com AdSense: dados usados internamente

Uso:
    collector = OddsCollector()
    odds = collector.coletar_odds_brasileirao()
    # → Dict com probabilidades implícitas normalizadas por jogo

Ref:
  Pinnacle closing lines são consideradas as mais eficientes
  (Štrumbelj, 2014: "On the accuracy of betting odds")
"""
import json
import logging
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

import requests

sys.path.append(str(Path(__file__).parent.parent.parent))

logger = logging.getLogger("OddsCollector")

# Diretório INTERNO — nunca público
INTERNAL_DIR = Path(__file__).parent.parent.parent / "data" / "_internal" / "odds"
INTERNAL_DIR.mkdir(parents=True, exist_ok=True)

BRT = timezone(timedelta(hours=-3))

# The Odds API config
ODDS_API_BASE = "https://api.the-odds-api.com/v4"
SPORT_KEY = "soccer_brazil_campeonato"  # Brasileirão Série A

# TTL de cache (em segundos) — 4 horas entre coletas
CACHE_TTL = 4 * 3600  # 4h


class OddsCollector:
    """
    Coleta odds/probabilidades do mercado para calibração interna.

    Estratégia de budget (free tier: 500 créditos/mês):
      - 6 coletas/dia (a cada 4h)
      - 2 markets por coleta (h2h + totals)
      - Custo: 2 créditos/coleta × 6 = 12/dia ≈ 360/mês
      - Margem de segurança: ~140 créditos livres
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or self._load_api_key()
        self._session = None

    @staticmethod
    def _load_api_key() -> str:
        """Carrega API key do .env ou variável de ambiente."""
        key = os.environ.get("ODDS_API_KEY", "")
        if key:
            return key

        # Tentar carregar do .env
        env_path = Path(__file__).parent.parent.parent / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("ODDS_API_KEY=") and not line.startswith("#"):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")

        # Fallback hardcoded (chave free tier)
        return "79c5599618edb79a77c797e2954eea7f"

    @property
    def session(self):
        if not self._session:
            self._session = requests.Session()
            self._session.timeout = 15
        return self._session

    # ──────────────────── Cache ────────────────────

    def _cache_path(self) -> Path:
        """Retorna path do cache do dia atual."""
        today = datetime.now(BRT).strftime("%Y-%m-%d")
        return INTERNAL_DIR / f"odds_{today}.json"

    def _cache_get(self) -> Optional[Dict]:
        """Lê cache se válido (dentro do TTL)."""
        path = self._cache_path()
        if not path.exists():
            return None
        try:
            with open(path, "r") as f:
                data = json.load(f)
            cached_at = data.get("_cached_at", "")
            if cached_at:
                dt = datetime.fromisoformat(cached_at)
                age = (datetime.now(BRT) - dt).total_seconds()
                if age < CACHE_TTL:
                    return data
            return None
        except Exception:
            return None

    def _cache_set(self, data: Dict) -> None:
        """Salva dados no cache."""
        data["_cached_at"] = datetime.now(BRT).isoformat()
        try:
            with open(self._cache_path(), "w") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Erro salvando cache odds: {e}")

    # ──────────────────── API ────────────────────

    def _get(self, endpoint: str, params: Dict) -> Optional[Dict]:
        """Chamada à API com error handling."""
        url = f"{ODDS_API_BASE}/{endpoint}"
        params["apiKey"] = self.api_key
        try:
            r = self.session.get(url, params=params, timeout=15)

            # Logar uso de créditos
            remaining = r.headers.get("x-requests-remaining", "?")
            used = r.headers.get("x-requests-used", "?")
            last_cost = r.headers.get("x-requests-last", "?")
            logger.info(f"📊 Odds API: créditos restantes={remaining}, usados={used}, custo={last_cost}")

            if r.status_code == 401:
                logger.error("Odds API: chave inválida")
                return None
            if r.status_code == 429:
                logger.warning("Odds API: rate limited")
                return None
            if r.status_code != 200:
                logger.warning(f"Odds API: HTTP {r.status_code}")
                return None

            return r.json()
        except Exception as e:
            logger.error(f"Odds API erro: {e}")
            return None

    def creditos_restantes(self) -> int:
        """Retorna créditos restantes sem gastar quota (endpoint /sports é grátis)."""
        try:
            r = self.session.get(
                f"{ODDS_API_BASE}/sports/",
                params={"apiKey": self.api_key},
                timeout=10
            )
            return int(r.headers.get("x-requests-remaining", 0))
        except Exception:
            return -1

    # ──────────────────── Coleta ────────────────────

    def coletar_odds_brasileirao(self) -> Optional[Dict]:
        """
        Coleta odds do Brasileirão e retorna probabilidades implícitas.

        Retorna:
            {
                "jogos": [
                    {
                        "mandante": "Flamengo",
                        "visitante": "Palmeiras",
                        "data_inicio": "2026-02-15T21:00:00Z",
                        "prob_casa": 0.42,
                        "prob_empate": 0.28,
                        "prob_fora": 0.30,
                        "prob_over25": 0.55,
                        "prob_under25": 0.45,
                        "num_casas": 8,
                        "consenso": "casa"
                    },
                    ...
                ],
                "creditos_restantes": 488,
                "_cached_at": "2026-02-12T..."
            }

        ⚠️ Dados EXCLUSIVAMENTE para uso interno de calibração.
        """
        # Verificar cache
        cached = self._cache_get()
        if cached:
            logger.debug("Odds: retornando do cache")
            return cached

        if not self.api_key:
            logger.warning("Odds API: chave não configurada")
            return None

        # Buscar odds: h2h + totals, região EU (melhor cobertura BR)
        data = self._get(f"sports/{SPORT_KEY}/odds/", {
            "regions": "eu",
            "markets": "h2h,totals",
            "oddsFormat": "decimal",
        })

        if not data or not isinstance(data, list):
            return None

        if len(data) == 0:
            logger.info("Odds: nenhum jogo disponível no momento")
            return None

        jogos = []
        for event in data:
            jogo = self._processar_evento(event)
            if jogo:
                jogos.append(jogo)

        result = {
            "jogos": jogos,
            "total_jogos": len(jogos),
            "coletado_em": datetime.now(BRT).isoformat(),
        }

        self._cache_set(result)
        logger.info(f"✅ Odds coletadas: {len(jogos)} jogos do Brasileirão")
        return result

    def _processar_evento(self, event: Dict) -> Optional[Dict]:
        """
        Processa um evento e extrai probabilidades implícitas normalizadas.

        Agrega odds de todas as casas e calcula a média (consensus).
        Normaliza para remover overround (vig).
        """
        home = event.get("home_team", "")
        away = event.get("away_team", "")
        commence = event.get("commence_time", "")

        bookmakers = event.get("bookmakers", [])
        if not bookmakers:
            return None

        # Coletar todas as odds h2h
        all_home = []
        all_draw = []
        all_away = []
        all_over25 = []
        all_under25 = []

        for bk in bookmakers:
            for market in bk.get("markets", []):
                if market["key"] == "h2h":
                    outcomes = {o["name"]: o["price"] for o in market.get("outcomes", [])}
                    if home in outcomes:
                        all_home.append(outcomes[home])
                    if away in outcomes:
                        all_away.append(outcomes[away])
                    draw_price = outcomes.get("Draw")
                    if draw_price:
                        all_draw.append(draw_price)

                elif market["key"] == "totals":
                    for o in market.get("outcomes", []):
                        point = o.get("point")
                        if point == 2.5:
                            if o["name"] == "Over":
                                all_over25.append(o["price"])
                            elif o["name"] == "Under":
                                all_under25.append(o["price"])

        if not all_home or not all_draw or not all_away:
            return None

        # Média das odds de todas as casas
        avg_home = sum(all_home) / len(all_home)
        avg_draw = sum(all_draw) / len(all_draw)
        avg_away = sum(all_away) / len(all_away)

        # Converter odds → probabilidades implícitas
        prob_home = 1.0 / avg_home
        prob_draw = 1.0 / avg_draw
        prob_away = 1.0 / avg_away

        # Normalizar (remover overround/vig)
        total = prob_home + prob_draw + prob_away
        prob_home /= total
        prob_draw /= total
        prob_away /= total

        # Over/Under 2.5
        prob_over = prob_under = None
        if all_over25 and all_under25:
            avg_over = sum(all_over25) / len(all_over25)
            avg_under = sum(all_under25) / len(all_under25)
            p_over = 1.0 / avg_over
            p_under = 1.0 / avg_under
            total_ou = p_over + p_under
            prob_over = round(p_over / total_ou, 4)
            prob_under = round(p_under / total_ou, 4)

        # Determinar consenso
        if prob_home > prob_away and prob_home > prob_draw:
            consenso = "casa"
        elif prob_away > prob_home and prob_away > prob_draw:
            consenso = "fora"
        else:
            consenso = "empate"

        return {
            "mandante": home,
            "visitante": away,
            "data_inicio": commence,
            "prob_casa": round(prob_home, 4),
            "prob_empate": round(prob_draw, 4),
            "prob_fora": round(prob_away, 4),
            "prob_over25": prob_over,
            "prob_under25": prob_under,
            "num_casas": len(bookmakers),
            "consenso": consenso,
        }

    # ──────────────────── Lookup ────────────────────

    def odds_para_jogo(self, mandante: str, visitante: str) -> Optional[Dict]:
        """
        Busca odds para um jogo específico pelo nome dos times.

        Faz matching fuzzy (contém) para lidar com variações de nome
        entre The Odds API e o Cartola.
        """
        data = self.coletar_odds_brasileirao()
        if not data:
            return None

        mandante_lower = mandante.lower()
        visitante_lower = visitante.lower()

        for jogo in data.get("jogos", []):
            m = jogo["mandante"].lower()
            v = jogo["visitante"].lower()
            # Match fuzzy: nome parcial
            if (mandante_lower in m or m in mandante_lower) and \
               (visitante_lower in v or v in visitante_lower):
                return jogo

        return None

    # ──────────────────── Mapeamento de nomes ────────────────────

    # The Odds API usa nomes diferentes do Cartola em muitos times
    NOME_ODDS_PARA_ABREV = {
        "Atletico Mineiro": "CAM",
        "Atletico Paranaense": "CAP",
        "Bahia": "BAH",
        "Botafogo": "BOT",
        "Chapecoense": "CHA",
        "Corinthians": "COR",
        "Coritiba": "CFC",
        "Cruzeiro": "CRU",
        "Flamengo": "FLA",
        "Fluminense": "FLU",
        "Gremio": "GRE",
        "Internacional": "INT",
        "Mirassol": "MIR",
        "Palmeiras": "PAL",
        "Bragantino-SP": "RBB",
        "Red Bull Bragantino": "RBB",
        "Remo": "REM",
        "Santos": "SAN",
        "Sao Paulo": "SAO",
        "Vasco da Gama": "VAS",
        "Vitoria": "VIT",
    }

    def nome_para_abrev(self, nome_odds: str) -> Optional[str]:
        """Converte nome do time na Odds API para abreviação Cartola."""
        # Match exato
        if nome_odds in self.NOME_ODDS_PARA_ABREV:
            return self.NOME_ODDS_PARA_ABREV[nome_odds]
        # Match parcial
        nome_lower = nome_odds.lower()
        for key, abrev in self.NOME_ODDS_PARA_ABREV.items():
            if key.lower() in nome_lower or nome_lower in key.lower():
                return abrev
        return None

    def resumo_cache(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache de odds."""
        files = list(INTERNAL_DIR.glob("odds_*.json"))
        result = {
            "total_arquivos": len(files),
            "creditos_restantes": self.creditos_restantes(),
        }
        if files:
            latest = max(files, key=lambda f: f.stat().st_mtime)
            try:
                with open(latest) as f:
                    data = json.load(f)
                result["ultimo_arquivo"] = latest.name
                result["total_jogos"] = data.get("total_jogos", 0)
                result["coletado_em"] = data.get("coletado_em", "")
            except Exception:
                pass
        return result
