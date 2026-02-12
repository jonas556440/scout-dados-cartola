"""
Previsor de Placares - Cartola FC 2026 - V4

VERSÃO 4: Poisson + Dixon-Coles (Calibrado)
Reescrito para seguir melhores práticas de mercado.

Mudanças V3 → V4:
1. REMOVIDAS tabelas de frequência hardcoded (overfitting)
2. REMOVIDO fator casa "por rodada" (viés sem evidência estatística)
3. ADICIONADA correção Dixon-Coles (τ) para placares baixos
4. ADICIONADO decaimento temporal (time decay) na forma recente
5. RENOMEADO "xG" para "lambda" internamente (não é shot-based)
6. Fator casa = parâmetro ESTÁVEL por liga/campeonato
7. Baseline = média real de gols da liga (ancoragem)
8. ADICIONADA avaliação por log-loss (métrica probabilística)

Referências:
- Maher (1982) - "Modelling Association Football Scores"
- Dixon & Coles (1997) - "Modelling Association Football Scores
  and Inefficiencies in the Football Betting Market"
- Karlis & Ntzoufras (2003) - "Analysis of sports data by using
  bivariate Poisson models" - JRSS-D

Distribuição de Poisson:
P(k gols) = (λ^k * e^(-λ)) / k!
Onde λ = taxa de gols esperados
"""

import math
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
from functools import lru_cache
from enum import Enum

logger = logging.getLogger(__name__)


# ==================== ENUMS ====================

class ContextoJogo(Enum):
    """
    Contextos de jogo — usado para METADADOS e ajustes leves de confiança,
    NÃO para selecionar tabelas de frequência hardcoded.
    """
    REGIONAL_EQUILIBRADO = "regional_eq"
    INICIO_CAMPEONATO = "inicio"
    CLASSICO_DECISIVO = "classico"
    FAVORITO_DOMINANTE = "dominante"
    RETA_FINAL = "reta_final"
    INTERNACIONAL = "internacional"
    PADRAO = "padrao"


class ModoPrevisao(Enum):
    """Modos de previsão disponíveis"""
    POISSON = "poisson"           # Poisson independente (sem correção DC)
    DIXON_COLES = "dixon_coles"   # Poisson + correção Dixon-Coles (recomendado)
    HIBRIDO = "hibrido"           # Alias para DIXON_COLES (retrocompatibilidade V3)
    FREQUENCIA = "frequencia"     # Alias para DIXON_COLES (retrocompatibilidade V3)


# ==================== CONSTANTES CALIBRADAS ====================

# Médias de gols por jogo por liga (baseline de ancoragem)
# Fontes: Transfermarkt, FBref, Soccerway — temporadas 2022-2025
MEDIA_GOLS_POR_LIGA = {
    "brasileirao": 2.50, "brasileiro": 2.50, "serie a": 2.50,
    "paulista": 2.25, "carioca": 2.20, "gaucho": 2.15,
    "mineiro": 2.15, "pernambucano": 2.10, "regional": 2.15,
    "premier": 2.85, "premier_league": 2.85,
    "la_liga": 2.55, "bundesliga": 3.10,
    "serie_a_ita": 2.60, "ligue_1": 2.70,
    "champions": 2.95, "libertadores": 2.40, "europa": 2.80,
}

# Fator de vantagem de mando de campo por liga (parâmetro ESTÁVEL)
# Brasileirão 2012-2024 (~4600 jogos): mandante vence ~47%, empate ~25%, visitante ~28%
# Fator ~1.33-1.38 no λ do mandante
FATOR_CASA_POR_LIGA = {
    "brasileirao": 1.35, "brasileiro": 1.35, "serie a": 1.35,
    "paulista": 1.32, "carioca": 1.33, "gaucho": 1.30,
    "mineiro": 1.32, "pernambucano": 1.30, "regional": 1.30,
    "premier": 1.22, "premier_league": 1.22,
    "la_liga": 1.28, "bundesliga": 1.30,
    "serie_a_ita": 1.27, "ligue_1": 1.25,
    "champions": 1.18, "libertadores": 1.40, "europa": 1.20,
}

# Retrocompatibilidade: manter dict vazio para imports antigos
PLACARES_POR_CONTEXTO = {
    ContextoJogo.PADRAO: [
        ("1x0", 0.14), ("1x1", 0.12), ("2x1", 0.11), ("0x1", 0.10),
        ("2x0", 0.09), ("0x0", 0.08), ("1x2", 0.08), ("0x2", 0.07),
        ("2x2", 0.05), ("3x1", 0.04),
    ],
}


# ==================== DATACLASS DE RESULTADO ====================

@dataclass
class PrevisaoPlacar:
    """
    Resultado da previsão de um confronto.
    Interface 100% compatível com V3 para retrocompatibilidade.
    """
    mandante: str
    visitante: str
    mandante_id: int = 0
    visitante_id: int = 0

    # Lambda (taxa de gols) — exibido como "xG" no frontend por UX
    xg_mandante: float = 0.0
    xg_visitante: float = 0.0

    placar_provavel: str = "0x0"
    placar_casa: int = 0
    placar_fora: int = 0
    probabilidade_placar: float = 0.0
    top_placares: List[Tuple[str, float]] = field(default_factory=list)

    prob_vitoria_casa: float = 0.0
    prob_empate: float = 0.0
    prob_vitoria_fora: float = 0.0

    prob_over_1_5: float = 0.0
    prob_over_2_5: float = 0.0
    prob_over_3_5: float = 0.0
    prob_btts: float = 0.0

    confianca: float = 0.0
    fatores: Dict[str, Any] = field(default_factory=dict)

    contexto: str = "padrao"
    modo_previsao: str = "dixon_coles"
    peso_frequencia: float = 0.0  # V4: sempre 0


# ==================== CLASSE PRINCIPAL ====================

class ScorePredictor:
    """
    V4: Previsor de placares — Poisson + Dixon-Coles

    Metodologia:
    1. Calcular λ_casa e λ_fora (taxas de gols esperados)
       λ = média_liga_por_time × α_ataque × β_fraqueza_def_adv × γ_casa
    2. Calcular probabilidades de cada placar via Poisson
    3. Aplicar correção Dixon-Coles (τ) para 0-0, 1-0, 0-1, 1-1
    4. Normalizar e retornar distribuição completa

    Calibração:
    - Ataque/defesa: normalizados contra baseline da liga (44 = baseline V5)
    - Fator casa: parâmetro estável por liga (~1.22-1.40)
    - Dixon-Coles τ: ~0.05 (calibrado para ligas sul-americanas)
    - Decaimento temporal: peso exponencial em forma recente
    """

    MAX_GOLS = 7
    TAU = 0.05              # Dixon-Coles correlation parameter (calibrado)
    FORCA_BASELINE = 50.0   # Baseline V5 — auto-calibrado em prever_rodada()
    PESO_ODDS_BLEND = 0.25  # Peso das odds no blend V/E/D (25% mercado, 75% Poisson)

    def calibrar_baseline(self, estatisticas_times: Dict[int, Any]):
        """Auto-calibra FORCA_BASELINE para que α e β centrem em 1.0 para o time médio.
        
        α = forca_ataque / BASELINE  →  α_medio = 1.0
        β = (100 - forca_defesa) / BASELINE  →  β_medio = 1.0

        Chamado automaticamente por prever_rodada() com os dados reais.
        """
        ataques = []
        defesas_inv = []
        for stats in estatisticas_times.values():
            atk = getattr(stats, 'forca_ataque', None) or getattr(stats, 'forca_geral', 50)
            dfs = getattr(stats, 'forca_defesa', None) or getattr(stats, 'forca_geral', 50)
            ataques.append(atk)
            defesas_inv.append(100.0 - dfs)
        
        if ataques and defesas_inv:
            media_atk = sum(ataques) / len(ataques)
            media_def_inv = sum(defesas_inv) / len(defesas_inv)
            # Média geométrica para melhor calibração em produto α×β
            novo_baseline = (media_atk + media_def_inv) / 2.0
            if 20 < novo_baseline < 80:  # Sanity check
                self.FORCA_BASELINE = round(novo_baseline, 1)
    DECAY_RATE = 0.85       # Decaimento temporal por jogo

    def __init__(self):
        self.modo_padrao = ModoPrevisao.DIXON_COLES
        self._media_liga_real: Optional[float] = None  # Calculada do FDO quando disponível
        self._odds_collector = None  # Lazy-init
    
    def atualizar_media_liga_real(self, media_gols_por_jogo: float):
        """Atualiza média real de gols da liga calculada dos dados FDO.
        
        Chamado pelo MatchAnalyzer após carregar dados reais.
        Substitui o valor hardcoded de MEDIA_GOLS_POR_LIGA.
        """
        if 1.0 < media_gols_por_jogo < 5.0:  # Sanity check
            self._media_liga_real = round(media_gols_por_jogo, 3)
            logger.info(f"⚽ ScorePredictor: média liga real atualizada → {self._media_liga_real} gols/jogo")

    # ==================== POISSON ====================

    @staticmethod
    @lru_cache(maxsize=2000)
    def poisson_probability(lmbda: float, k: int) -> float:
        """P(X=k) via Poisson, usando log-space para estabilidade numérica."""
        if lmbda <= 0:
            return 1.0 if k == 0 else 0.0
        if k < 0:
            return 0.0
        log_prob = k * math.log(lmbda) - lmbda - math.lgamma(k + 1)
        return math.exp(log_prob)

    # ==================== DIXON-COLES ====================

    @staticmethod
    def dixon_coles_correction(
        gols_casa: int, gols_fora: int,
        lambda_casa: float, lambda_fora: float,
        tau: float
    ) -> float:
        """
        Correção Dixon-Coles para placares baixos.

        Poisson independente subestima 0-0 e 1-1, superestima 1-0 e 0-1.
        Ref: Dixon & Coles (1997), Equações 3-6.
        """
        if gols_casa == 0 and gols_fora == 0:
            return 1.0 + tau
        elif gols_casa == 1 and gols_fora == 0:
            denom = 1.0 + tau * lambda_casa * lambda_fora
            return 1.0 - tau * lambda_fora / denom if denom > 0 else 1.0
        elif gols_casa == 0 and gols_fora == 1:
            denom = 1.0 + tau * lambda_casa * lambda_fora
            return 1.0 - tau * lambda_casa / denom if denom > 0 else 1.0
        elif gols_casa == 1 and gols_fora == 1:
            return 1.0 + tau
        return 1.0

    # ==================== CÁLCULO DE LAMBDA ====================

    def calcular_lambda(
        self,
        forca_ataque: float,
        forca_defesa_adversario: float,
        eh_mandante: bool,
        campeonato: str = "brasileirao",
        forma_recente: str = "",
        posicao: int = 10,
        dias_descanso: int = -1,
        h2h_ajuste: float = 1.0,
    ) -> float:
        """
        Calcula λ (taxa de gols esperados) para um time.

        Fórmula (estilo Maher/Dixon-Coles):
            λ = média_liga/2 × α_ataque × β_fraqueza_def_adv × γ_casa × δ_descanso × ε_h2h

        Onde:
            α = forca_ataque / BASELINE (normalizado, centro=1.0)
            β = (100 - forca_defesa_adv) / BASELINE
            γ = fator de mando (>1 se mandante, 1.0 se visitante)
            δ = fator de descanso (ref: FiveThirtyEight, Clark 2005)
            ε = fator H2H (histórico de confrontos diretos, ±8% máx)
        """
        camp = campeonato.lower()
        # Priorizar média REAL da liga (FDO) sobre hardcoded
        if self._media_liga_real and camp in ("brasileirao", "brasileiro", "serie a"):
            media_liga = self._media_liga_real / 2.0
        else:
            media_liga = MEDIA_GOLS_POR_LIGA.get(camp, 2.50) / 2.0
        fator_casa = FATOR_CASA_POR_LIGA.get(camp, 1.33) if eh_mandante else 1.0

        alfa = max(0.35, min(2.5, forca_ataque / self.FORCA_BASELINE))
        beta = max(0.2, min(2.0, (100.0 - forca_defesa_adversario) / self.FORCA_BASELINE))

        lam = media_liga * alfa * beta * fator_casa

        # Ajuste forma recente (com decaimento temporal)
        if forma_recente:
            lam *= self._ajuste_forma(forma_recente)

        # Ajuste posição na tabela (±8% máx)
        lam *= self._ajuste_posicao(posicao)

        # Ajuste dias de descanso (±5% máx)
        if dias_descanso >= 0:
            lam *= self._ajuste_descanso(dias_descanso)

        # Ajuste H2H (confrontos diretos, ±8% máx)
        if h2h_ajuste != 1.0:
            lam *= max(0.92, min(1.08, h2h_ajuste))

        return max(0.2, min(4.0, lam))

    # Retrocompatibilidade: calcular_xg é alias de calcular_lambda
    def calcular_xg(
        self,
        forca_ataque_time: float,
        forca_defesa_adversario: float,
        eh_mandante: bool,
        posicao_time: int = 10,
        posicao_adversario: int = 10,
        forma_recente: str = "",
        rodada: int = 10,
        contexto: ContextoJogo = ContextoJogo.PADRAO
    ) -> float:
        """Retrocompatibilidade V3 — redireciona para calcular_lambda."""
        return self.calcular_lambda(
            forca_ataque=forca_ataque_time,
            forca_defesa_adversario=forca_defesa_adversario,
            eh_mandante=eh_mandante,
            forma_recente=forma_recente,
            posicao=posicao_time,
        )

    def _ajuste_forma(self, forma: str) -> float:
        """
        Ajuste de forma com DECAIMENTO TEMPORAL.

        Peso decrescente: último jogo = 1.0, anterior = 0.85, etc.
        V = +0.03 ponderado, D = -0.03 ponderado, E = neutro.
        """
        if not forma:
            return 1.0
        ajuste = 0.0
        peso_total = 0.0
        for i, r in enumerate(reversed(forma.upper())):
            peso = self.DECAY_RATE ** i
            peso_total += peso
            if r == 'V':
                ajuste += 0.03 * peso
            elif r == 'D':
                ajuste -= 0.03 * peso
        if peso_total > 0:
            ajuste /= peso_total
        return max(0.85, min(1.15, 1.0 + ajuste))

    def _ajuste_posicao(self, posicao: int) -> float:
        """Top 4: +8%, Top 10: +3%, Z4: -5%."""
        if posicao <= 0:
            return 1.0
        if posicao <= 4:
            return 1.08
        if posicao <= 10:
            return 1.03
        if posicao >= 17:
            return 0.95
        return 1.0

    @staticmethod
    def _ajuste_descanso(dias: int) -> float:
        """
        Ajuste por dias de descanso entre jogos.

        Referências:
        - Clark (2005): "Home advantage & rest" — descanso curto penaliza.
        - FiveThirtyEight SPI: usa rest days como variável.
        - Calibração: ~±5% no λ, suavizado.

        Benchmarks empíricos:
        - 2 dias (Tue→Thu): -4% (fadiga forte)
        - 3 dias (Wed→Sat): -2% (fadiga leve)
        - 4-6 dias: 0% (normal)
        - 7-10 dias: +2% (descanso bom)
        - 11+ dias: +1% (muito parado, perde ritmo)
        """
        if dias < 0:
            return 1.0
        if dias <= 2:
            return 0.96   # Fadiga forte
        if dias <= 3:
            return 0.98   # Fadiga leve
        if dias <= 6:
            return 1.0    # Normal
        if dias <= 10:
            return 1.02   # Descanso bom
        # 11+ dias: descansado mas sem ritmo
        return 1.01

    # ==================== CONTEXTO (informativo) ====================

    def identificar_contexto(
        self,
        mandante: str,
        visitante: str,
        rodada: int,
        forca_mandante: float,
        forca_visitante: float,
        campeonato: str = "brasileirao",
        eh_classico: bool = False,
        eh_decisao: bool = False
    ) -> ContextoJogo:
        """
        Identifica contexto do jogo — V4: apenas para METADADOS,
        NÃO para selecionar tabelas de frequência.
        """
        camp = campeonato.lower()
        diff = abs(forca_mandante - forca_visitante)

        if camp in ["paulista", "carioca", "gaucho", "mineiro", "regional", "pernambucano"]:
            if diff < 25 and not eh_classico:
                return ContextoJogo.REGIONAL_EQUILIBRADO

        if rodada <= 3 and camp in ["brasileirao", "brasileiro", "serie a"]:
            return ContextoJogo.INICIO_CAMPEONATO

        if rodada >= 30:
            return ContextoJogo.RETA_FINAL

        if diff > 20:
            return ContextoJogo.FAVORITO_DOMINANTE

        if eh_classico or eh_decisao:
            return ContextoJogo.CLASSICO_DECISIVO

        if camp in ["premier", "premier_league", "champions", "europa",
                     "libertadores", "la_liga", "bundesliga", "serie_a_ita", "ligue_1"]:
            return ContextoJogo.INTERNACIONAL

        return ContextoJogo.PADRAO

    # ==================== PROBABILIDADES DE PLACAR ====================

    def calcular_probabilidades_placar(
        self,
        lambda_casa: float,
        lambda_fora: float,
        usar_dixon_coles: bool = True
    ) -> Dict[str, float]:
        """
        Probabilidade de cada placar via Poisson + Dixon-Coles.

        P(i,j) = Poisson(i; λ_casa) × Poisson(j; λ_fora) × DC(i,j)
        """
        probs = {}
        for gc in range(self.MAX_GOLS + 1):
            for gf in range(self.MAX_GOLS + 1):
                p = self.poisson_probability(lambda_casa, gc) * \
                    self.poisson_probability(lambda_fora, gf)
                if usar_dixon_coles:
                    p *= self.dixon_coles_correction(gc, gf, lambda_casa, lambda_fora, self.TAU)
                probs[f"{gc}x{gf}"] = max(0, p)

        total = sum(probs.values())
        if total > 0:
            probs = {k: v / total for k, v in probs.items()}
        return probs

    def calcular_probabilidades_resultado(
        self,
        lambda_casa: float,
        lambda_fora: float
    ) -> Tuple[float, float, float]:
        """Probabilidades de V/E/D somando placares correspondentes."""
        probs = self.calcular_probabilidades_placar(lambda_casa, lambda_fora)
        v_casa = e = v_fora = 0.0
        for placar, prob in probs.items():
            gc, gf = map(int, placar.split('x'))
            if gc > gf:
                v_casa += prob
            elif gc == gf:
                e += prob
            else:
                v_fora += prob
        return v_casa, e, v_fora

    def calcular_probabilidades_gols(
        self,
        lambda_casa: float,
        lambda_fora: float
    ) -> Dict[str, float]:
        """Mercados de gols: Over 1.5/2.5/3.5 e BTTS."""
        probs = self.calcular_probabilidades_placar(lambda_casa, lambda_fora)
        o15 = o25 = o35 = btts = 0.0
        for placar, prob in probs.items():
            gc, gf = map(int, placar.split('x'))
            total = gc + gf
            if total > 1: o15 += prob
            if total > 2: o25 += prob
            if total > 3: o35 += prob
            if gc > 0 and gf > 0: btts += prob
        return {"over_1_5": o15, "over_2_5": o25, "over_3_5": o35, "btts": btts}

    # Retrocompatibilidade V3
    def obter_frequencias_contexto(self, contexto: ContextoJogo) -> Dict[str, float]:
        """Mantido para não quebrar imports. Retorna dict vazio útil."""
        return {p: prob for p, prob in PLACARES_POR_CONTEXTO.get(contexto, PLACARES_POR_CONTEXTO[ContextoJogo.PADRAO])}

    def combinar_probabilidades(self, probs_poisson, probs_freq, peso_freq=0.0):
        """Mantido para retrocompatibilidade. V4 ignora frequências (peso=0)."""
        return probs_poisson  # V4: retorna Poisson+DC direto

    # ==================== CONFIANÇA ====================

    def _calcular_confianca(self, f_mand, f_visit, prob_top, contexto):
        diff = abs(f_mand - f_visit)
        c_forca = min(40, diff * 1.2)
        c_placar = min(30, prob_top * 200)
        c_ctx = 10 if contexto == ContextoJogo.FAVORITO_DOMINANTE else \
                5 if contexto == ContextoJogo.CLASSICO_DECISIVO else 0
        return min(95, c_forca + c_placar + c_ctx)

    # ==================== PREVISÃO PRINCIPAL ====================

    def prever_confronto(
        self,
        mandante: str,
        visitante: str,
        mandante_id: int = 0,
        visitante_id: int = 0,
        forca_mandante: float = 50.0,
        forca_visitante: float = 50.0,
        posicao_mandante: int = 10,
        posicao_visitante: int = 10,
        forma_mandante: str = "",
        forma_visitante: str = "",
        rodada: int = 10,
        campeonato: str = "brasileirao",
        eh_classico: bool = False,
        eh_decisao: bool = False,
        modo: ModoPrevisao = None,
        dias_descanso_mandante: int = -1,
        dias_descanso_visitante: int = -1,
        forca_ataque_mandante: float = None,
        forca_defesa_mandante: float = None,
        forca_ataque_visitante: float = None,
        forca_defesa_visitante: float = None,
        h2h_ajuste_mandante: float = 1.0,
        h2h_ajuste_visitante: float = 1.0,
    ) -> PrevisaoPlacar:
        """
        Previsão completa de um confronto.
        Interface 100% compatível com V3 — mesma assinatura, mesmo retorno.
        """
        if modo is None:
            modo = self.modo_padrao
        # V4: todos os modos usam Dixon-Coles exceto POISSON puro
        usar_dc = modo != ModoPrevisao.POISSON

        # 1. Contexto (informativo)
        contexto = self.identificar_contexto(
            mandante, visitante, rodada,
            forca_mandante, forca_visitante,
            campeonato, eh_classico, eh_decisao
        )

        # 2. Resolver forças de ataque/defesa separadas (V5)
        atk_m = forca_ataque_mandante if forca_ataque_mandante is not None else forca_mandante
        def_m = forca_defesa_mandante if forca_defesa_mandante is not None else forca_mandante
        atk_v = forca_ataque_visitante if forca_ataque_visitante is not None else forca_visitante
        def_v = forca_defesa_visitante if forca_defesa_visitante is not None else forca_visitante

        # 3. Calcular λ (ataque do time × fraqueza defensiva do adversário)
        lambda_casa = self.calcular_lambda(
            forca_ataque=atk_m,
            forca_defesa_adversario=def_v,
            eh_mandante=True,
            campeonato=campeonato,
            forma_recente=forma_mandante,
            posicao=posicao_mandante,
            dias_descanso=dias_descanso_mandante,
            h2h_ajuste=h2h_ajuste_mandante,
        )
        lambda_fora = self.calcular_lambda(
            forca_ataque=atk_v,
            forca_defesa_adversario=def_m,
            eh_mandante=False,
            campeonato=campeonato,
            forma_recente=forma_visitante,
            posicao=posicao_visitante,
            dias_descanso=dias_descanso_visitante,
            h2h_ajuste=h2h_ajuste_visitante,
        )

        # 3. Ajuste de clássico (tensão → -5% gols)
        if eh_classico:
            lambda_casa *= 0.95
            lambda_fora *= 0.95

        # 4. Top 5 placares — seleção inteligente (Poisson + desempate xG)
        #    Usa Poisson puro (sem viés DC) para probabilidades base.
        #    Quando vários placares têm prob similar (cluster ≤ 1.5pp),
        #    escolhe o mais próximo dos gols esperados (xG),
        #    como fazem sites especialistas (FiveThirtyEight, Forebet).
        #    DC continua para V/E/D e mercados de gols (bem calibrados).
        probs_placar = self.calcular_probabilidades_placar(lambda_casa, lambda_fora, False)
        all_sorted = sorted(probs_placar.items(), key=lambda x: x[1], reverse=True)
        max_prob = all_sorted[0][1]

        # Cluster: placares com prob próxima do máximo (≤ 1.5pp)
        CLUSTER_THRESHOLD = 0.015
        cluster = [(p, pr) for p, pr in all_sorted if max_prob - pr <= CLUSTER_THRESHOLD]

        if len(cluster) > 1:
            # Desempate: placar mais próximo do xG (distância euclidiana²)
            def _xg_dist(placar: str) -> float:
                gc, gf = map(int, placar.split('x'))
                return (gc - lambda_casa) ** 2 + (gf - lambda_fora) ** 2
            best = min(cluster, key=lambda x: _xg_dist(x[0]))
            top5 = [best] + [(p, pr) for p, pr in all_sorted if p != best[0]][:4]
        else:
            top5 = all_sorted[:5]

        placar_top = top5[0][0]
        prob_top = top5[0][1]
        gc_top, gf_top = map(int, placar_top.split('x'))

        # 6. Resultado
        pv_casa, p_empate, pv_fora = self.calcular_probabilidades_resultado(lambda_casa, lambda_fora)

        # 6.1 Blend com odds de mercado (The Odds API) se disponível
        odds_jogo = self._buscar_odds_mercado(mandante, visitante)
        odds_info = {}
        if odds_jogo:
            peso_m = self.PESO_ODDS_BLEND
            peso_p = 1.0 - peso_m
            pv_casa_blend = pv_casa * peso_p + odds_jogo["prob_casa"] * peso_m
            p_empate_blend = p_empate * peso_p + odds_jogo["prob_empate"] * peso_m
            pv_fora_blend = pv_fora * peso_p + odds_jogo["prob_fora"] * peso_m
            # Normalizar
            total_blend = pv_casa_blend + p_empate_blend + pv_fora_blend
            if total_blend > 0:
                pv_casa = pv_casa_blend / total_blend
                p_empate = p_empate_blend / total_blend
                pv_fora = pv_fora_blend / total_blend
            odds_info = {
                "odds_mercado_casa": odds_jogo["prob_casa"],
                "odds_mercado_empate": odds_jogo["prob_empate"],
                "odds_mercado_fora": odds_jogo["prob_fora"],
                "odds_num_casas": odds_jogo.get("num_casas", 0),
                "odds_blend_peso": peso_m,
            }
            logger.debug(
                f"📊 Blend odds {mandante}x{visitante}: "
                f"Poisson={pv_casa:.2f}/{p_empate:.2f}/{pv_fora:.2f} | "
                f"Mercado={odds_jogo['prob_casa']:.2f}/{odds_jogo['prob_empate']:.2f}/{odds_jogo['prob_fora']:.2f}"
            )

        # 7. Mercados de gols
        pg = self.calcular_probabilidades_gols(lambda_casa, lambda_fora)

        # 8. Confiança
        confianca = self._calcular_confianca(forca_mandante, forca_visitante, prob_top, contexto)

        # 9. Metadados
        camp = campeonato.lower()
        fc = FATOR_CASA_POR_LIGA.get(camp, 1.33)

        return PrevisaoPlacar(
            mandante=mandante,
            visitante=visitante,
            mandante_id=mandante_id,
            visitante_id=visitante_id,
            xg_mandante=round(lambda_casa, 2),
            xg_visitante=round(lambda_fora, 2),
            placar_provavel=placar_top,
            placar_casa=gc_top,
            placar_fora=gf_top,
            probabilidade_placar=round(prob_top * 100, 1),
            top_placares=[(p, round(pr * 100, 1)) for p, pr in top5],
            prob_vitoria_casa=round(pv_casa * 100, 1),
            prob_empate=round(p_empate * 100, 1),
            prob_vitoria_fora=round(pv_fora * 100, 1),
            prob_over_1_5=round(pg["over_1_5"] * 100, 1),
            prob_over_2_5=round(pg["over_2_5"] * 100, 1),
            prob_over_3_5=round(pg["over_3_5"] * 100, 1),
            prob_btts=round(pg["btts"] * 100, 1),
            confianca=round(confianca, 1),
            contexto=contexto.value,
            modo_previsao="dixon_coles" if usar_dc else "poisson",
            peso_frequencia=0.0,
            fatores={
                "forca_mandante": forca_mandante,
                "forca_visitante": forca_visitante,
                "posicao_mandante": posicao_mandante,
                "posicao_visitante": posicao_visitante,
                "forma_mandante": forma_mandante,
                "forma_visitante": forma_visitante,
                "rodada": rodada,
                "campeonato": campeonato,
                "contexto_jogo": contexto.value,
                "lambda_casa": round(lambda_casa, 3),
                "lambda_fora": round(lambda_fora, 3),
                "fator_casa": fc,
                "dixon_coles_tau": self.TAU if usar_dc else 0,
                "dias_descanso_mandante": dias_descanso_mandante,
                "dias_descanso_visitante": dias_descanso_visitante,
                "modo": modo.value,
                "modelo": "V4_Dixon-Coles",
                **odds_info,
            }
        )

    # ==================== ODDS DE MERCADO ====================

    def _buscar_odds_mercado(self, mandante: str, visitante: str) -> Optional[Dict]:
        """
        Busca probabilidades implícitas do mercado (The Odds API).
        
        Lê apenas do cache interno — nunca gasta créditos.
        Retorna dict com prob_casa/prob_empate/prob_fora ou None.
        """
        try:
            if self._odds_collector is None:
                from src.analysis.odds_collector import OddsCollector
                self._odds_collector = OddsCollector()
            return self._odds_collector.odds_para_jogo(mandante, visitante)
        except Exception as e:
            logger.debug(f"Odds indisponíveis para {mandante}x{visitante}: {e}")
            return None

    # ==================== PREVISÃO DE RODADA ====================

    def prever_rodada(
        self,
        partidas: List[Dict],
        estatisticas_times: Dict[int, Any],
        descanso: Dict[int, Optional[int]] = None,
        h2h_ajustes: Dict[str, Tuple[float, float]] = None,
    ) -> List[PrevisaoPlacar]:
        """Prevê todos os confrontos de uma rodada.

        Args:
            descanso: Dict {clube_id: dias_descanso} - se fornecido,
                      injeta automaticamente nos cálculos de λ.
            h2h_ajustes: Dict {"mandante_abrev-visitante_abrev": (ajuste_mandante, ajuste_visitante)}
                         Multiplicadores H2H para λ de cada time (1.0 = neutro).
        """
        if descanso is None:
            descanso = {}
        if h2h_ajustes is None:
            h2h_ajustes = {}

        # Auto-calibrar baseline a partir dos dados reais da rodada
        self.calibrar_baseline(estatisticas_times)
        
        # Auto-calcular média de gols da liga a partir dos dados reais
        if not self._media_liga_real:
            total_gp = 0
            total_j = 0
            for stats in estatisticas_times.values():
                gp = getattr(stats, 'gols_pro', 0) or 0
                j = getattr(stats, 'jogos', 0) or 0
                total_gp += gp
                total_j += j
            if total_j >= 20:  # pelo menos ~2 jogos por time
                media_calc = (total_gp * 2) / total_j  # *2 porque gols_pro conta cada time
                self.atualizar_media_liga_real(media_calc)

        previsoes = []
        for partida in partidas:
            mandante_id = partida.get("clube_casa_id")
            visitante_id = partida.get("clube_visitante_id")
            sm = estatisticas_times.get(mandante_id)
            sv = estatisticas_times.get(visitante_id)
            if not sm or not sv:
                continue

            ma = partida.get("clube_casa_abrev", getattr(sm, 'abreviacao', "???"))
            va = partida.get("clube_visitante_abrev", getattr(sv, 'abreviacao', "???"))
            fm = getattr(sm, 'forca_geral', 50)
            fv = getattr(sv, 'forca_geral', 50)
            # v10: Forças casa/fora específicas — ataque do mandante EM CASA x defesa do visitante FORA
            fatk_m = getattr(sm, 'forca_ataque_casa', None) or getattr(sm, 'forca_ataque', fm)
            fdef_m = getattr(sm, 'forca_defesa_casa', None) or getattr(sm, 'forca_defesa', fm)
            fatk_v = getattr(sv, 'forca_ataque_fora', None) or getattr(sv, 'forca_ataque', fv)
            fdef_v = getattr(sv, 'forca_defesa_fora', None) or getattr(sv, 'forca_defesa', fv)
            pm = partida.get("clube_casa_posicao", getattr(sm, 'posicao', 10)) or 10
            pv = partida.get("clube_visitante_posicao", getattr(sv, 'posicao', 10)) or 10
            frm = getattr(sm, 'forma_sequencia', "")
            frv = getattr(sv, 'forma_sequencia', "")
            dm = descanso.get(mandante_id, -1) or -1
            dv = descanso.get(visitante_id, -1) or -1

            # H2H: lookup por chave "MANDxVISIT"
            h2h_key = f"{ma}-{va}"
            h2h_m, h2h_v = h2h_ajustes.get(h2h_key, (1.0, 1.0))

            previsoes.append(self.prever_confronto(
                mandante=ma, visitante=va,
                mandante_id=mandante_id, visitante_id=visitante_id,
                forca_mandante=fm, forca_visitante=fv,
                forca_ataque_mandante=fatk_m, forca_defesa_mandante=fdef_m,
                forca_ataque_visitante=fatk_v, forca_defesa_visitante=fdef_v,
                posicao_mandante=pm, posicao_visitante=pv,
                forma_mandante=frm, forma_visitante=frv,
                dias_descanso_mandante=dm,
                dias_descanso_visitante=dv,
                h2h_ajuste_mandante=h2h_m,
                h2h_ajuste_visitante=h2h_v,
            ))
        return previsoes

    # ==================== AVALIAÇÃO / BACKTEST ====================

    @staticmethod
    def log_loss_placar(
        previsoes: List[PrevisaoPlacar],
        resultados_reais: List[str]
    ) -> float:
        """
        Log-loss (cross-entropy) da distribuição de placares.
        Métrica padrão para forecast probabilístico. Quanto MENOR, melhor.

        log_loss = -1/N × Σ log(P(placar_real))
        """
        if not previsoes or len(previsoes) != len(resultados_reais):
            return float('inf')
        predictor = ScorePredictor()
        total = 0.0
        n = 0
        for prev, real in zip(previsoes, resultados_reais):
            probs = predictor.calcular_probabilidades_placar(prev.xg_mandante, prev.xg_visitante)
            p = max(0.001, probs.get(real, 0.001))
            total -= math.log(p)
            n += 1
        return total / n if n > 0 else float('inf')

    @staticmethod
    def avaliar_resultado(
        previsoes: List[PrevisaoPlacar],
        resultados_reais: List[str]
    ) -> Dict[str, Any]:
        """Avaliação completa: log-loss + acertos exatos + acertos V/E/D."""
        if not previsoes or len(previsoes) != len(resultados_reais):
            return {"erro": "Listas incompatíveis"}
        acertos_ex = acertos_res = 0
        n = len(previsoes)
        for prev, real in zip(previsoes, resultados_reais):
            if prev.placar_provavel == real:
                acertos_ex += 1
            gc_r, gf_r = map(int, real.split('x'))
            r_prev = "V" if prev.placar_casa > prev.placar_fora else ("E" if prev.placar_casa == prev.placar_fora else "D")
            r_real = "V" if gc_r > gf_r else ("E" if gc_r == gf_r else "D")
            if r_prev == r_real:
                acertos_res += 1
        ll = ScorePredictor.log_loss_placar(previsoes, resultados_reais)
        return {
            "jogos": n,
            "log_loss": round(ll, 4),
            "acertos_exatos": acertos_ex,
            "taxa_exato": round(acertos_ex / n * 100, 1),
            "acertos_resultado": acertos_res,
            "taxa_resultado": round(acertos_res / n * 100, 1),
            "nota": "Excelente" if ll < 2.5 else "Bom" if ll < 3.0 else "Regular" if ll < 3.5 else "Fraco",
        }


# ==================== TESTE ====================
if __name__ == "__main__":
    predictor = ScorePredictor()

    print("=" * 70)
    print("⚽ PREVISOR DE PLACARES V4 — Poisson + Dixon-Coles")
    print("=" * 70)

    confrontos = [
        ("FLA", "INT", 82, 75, 3, 8, "VVE", "EVD"),
        ("PAL", "COR", 88, 65, 1, 12, "VVVV", "EDVD"),
        ("BOT", "FLU", 85, 72, 2, 6, "VVV", "VEE"),
        ("REM", "MIR", 40, 55, 19, 7, "DDD", "VVV"),
        ("SAN", "SAO", 60, 75, 15, 4, "DEV", "VVE"),
    ]

    for m, v, fm, fv, pm, pv, frm, frv in confrontos:
        prev = predictor.prever_confronto(
            mandante=m, visitante=v,
            forca_mandante=fm, forca_visitante=fv,
            posicao_mandante=pm, posicao_visitante=pv,
            forma_mandante=frm, forma_visitante=frv,
            campeonato="brasileirao", rodada=10,
        )
        print(f"\n{m} vs {v}")
        print(f"  λ: {prev.xg_mandante} vs {prev.xg_visitante}")
        print(f"  Placar: {prev.placar_provavel} ({prev.probabilidade_placar}%)")
        print(f"  V/E/D: {prev.prob_vitoria_casa}% / {prev.prob_empate}% / {prev.prob_vitoria_fora}%")
        print(f"  Over 2.5: {prev.prob_over_2_5}% | BTTS: {prev.prob_btts}%")
        print(f"  Top 3: {prev.top_placares[:3]}")
        print(f"  Modelo: {prev.fatores.get('modelo')}")
