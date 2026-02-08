"""
Previsão de Placares - Cartela Placar do Jota (08/02/2026)
Usando lógica V4 corrigida:
1. Poisson puro (sem frequências hardcoded)
2. Correção Dixon-Coles (ajusta placares 0-0, 1-0, 0-1, 1-1)
3. Fator casa REAL (~1.33 constante, baseado em dados históricos)
4. Lambda calculado com forças realistas
"""

import math
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass

sys.path.append(str(Path(__file__).parent))


# ==================== MODELO V4 CORRIGIDO ====================

class ScorePredictorV4:
    """
    Poisson + Dixon-Coles correction
    Sem frequências hardcoded, sem anulação de fator casa
    """
    
    # Médias históricas reais
    MEDIA_GOLS_LIGA = {
        "premier_league": 2.85,   # PL média ~2.8-2.9 gols/jogo
        "la_liga": 2.55,          # La Liga ~2.5-2.6
        "carioca": 2.20,          # Estaduais brasileiros ~2.1-2.3
        "mineiro": 2.15,          # Estaduais brasileiros
        "paulista": 2.30,         # Paulistão um pouco mais gols
        "brasileirao": 2.50,      # Brasileirão ~2.4-2.6
    }
    
    # Fator casa REAL por liga (baseado em dados históricos)
    FATOR_CASA = {
        "premier_league": 1.25,   # PL: vantagem casa menor (estádios cheios sempre)
        "la_liga": 1.30,          # La Liga: vantagem moderada
        "carioca": 1.35,          # Estaduais BR: vantagem alta
        "mineiro": 1.33,          # Estaduais BR
        "paulista": 1.32,         # Paulistão
        "brasileirao": 1.35,      # Brasileirão: vantagem alta
    }
    
    MAX_GOLS = 7
    
    # Dixon-Coles tau parameter (correlação para placares baixos)
    # Calibrado para futebol: tau ~ 0.12 (Karlis & Ntzoufras, 2009)
    TAU = 0.12
    
    @staticmethod
    def poisson_prob(lmbda: float, k: int) -> float:
        """P(X=k) via Poisson"""
        if lmbda <= 0:
            return 1.0 if k == 0 else 0.0
        log_prob = k * math.log(lmbda) - lmbda - math.lgamma(k + 1)
        return math.exp(log_prob)
    
    def dixon_coles_correction(self, gols_casa: int, gols_fora: int, 
                                lambda_casa: float, lambda_fora: float, tau: float) -> float:
        """
        Correção Dixon-Coles para placares baixos (0-0, 1-0, 0-1, 1-1)
        
        Referência: Dixon & Coles (1997) - "Modelling Association Football Scores 
        and Inefficiencies in the Football Betting Market"
        
        A correção τ ajusta a correlação entre gols dos dois times
        que o modelo Poisson independente ignora.
        """
        if gols_casa == 0 and gols_fora == 0:
            return 1.0 + tau  # 0-0 é MAIS provável que Poisson puro prevê
        elif gols_casa == 1 and gols_fora == 0:
            return 1.0 - tau * lambda_fora / (1 + tau * lambda_casa * lambda_fora)
        elif gols_casa == 0 and gols_fora == 1:
            return 1.0 - tau * lambda_casa / (1 + tau * lambda_casa * lambda_fora)
        elif gols_casa == 1 and gols_fora == 1:
            return 1.0 + tau  # 1-1 também é mais provável
        else:
            return 1.0  # Sem correção para outros placares
    
    def calcular_lambdas(
        self,
        forca_ataque_casa: float,
        forca_defesa_casa: float,
        forca_ataque_fora: float,
        forca_defesa_fora: float,
        liga: str = "brasileirao",
        eh_classico: bool = False,
        eh_decisao: bool = False,
    ) -> Tuple[float, float]:
        """
        Calcula λ (lambda) para cada time
        
        Fórmula Dixon-Coles:
        λ_casa = α_casa × β_fora × γ × média_liga
        λ_fora = α_fora × β_casa × média_liga
        
        Onde:
        α = força de ataque normalizada
        β = fraqueza defensiva normalizada (inverso da força)
        γ = fator casa
        """
        media_liga = self.MEDIA_GOLS_LIGA.get(liga, 2.50) / 2  # Dividir por 2 = média por time
        fator_casa = self.FATOR_CASA.get(liga, 1.33)
        
        # Normalizar forças para fator multiplicativo (centrado em 1.0)
        # Força 50 = 1.0 (média), Força 80 = 1.4, Força 30 = 0.7
        alfa_casa = max(0.4, min(2.0, forca_ataque_casa / 55))
        beta_fora_fraqueza = max(0.5, min(2.0, (110 - forca_defesa_fora) / 55))
        
        alfa_fora = max(0.4, min(2.0, forca_ataque_fora / 55))
        beta_casa_fraqueza = max(0.5, min(2.0, (110 - forca_defesa_casa) / 55))
        
        # λ_casa = ataque_casa × fraqueza_defesa_fora × fator_casa × média_liga
        lambda_casa = media_liga * alfa_casa * beta_fora_fraqueza * fator_casa
        
        # λ_fora = ataque_fora × fraqueza_defesa_casa × média_liga (sem fator casa)
        lambda_fora = media_liga * alfa_fora * beta_casa_fraqueza
        
        # Ajustes para clássicos (mais tensão = menos gols geralmente)
        if eh_classico:
            lambda_casa *= 0.95
            lambda_fora *= 0.95
        
        # Limitar a valores razoáveis
        lambda_casa = max(0.3, min(3.8, lambda_casa))
        lambda_fora = max(0.2, min(3.2, lambda_fora))
        
        return lambda_casa, lambda_fora
    
    def prever_jogo(
        self,
        mandante: str,
        visitante: str,
        forca_ataque_casa: float,
        forca_defesa_casa: float,
        forca_ataque_fora: float,
        forca_defesa_fora: float,
        liga: str = "brasileirao",
        eh_classico: bool = False,
        eh_decisao: bool = False,
        forma_casa: str = "",
        forma_fora: str = "",
    ) -> dict:
        """Previsão completa com Poisson + Dixon-Coles"""
        
        # 1. Calcular lambdas
        lam_casa, lam_fora = self.calcular_lambdas(
            forca_ataque_casa, forca_defesa_casa,
            forca_ataque_fora, forca_defesa_fora,
            liga, eh_classico, eh_decisao
        )
        
        # 2. Ajuste por forma recente (±5% por resultado)
        if forma_casa:
            v = forma_casa.upper().count('V')
            d = forma_casa.upper().count('D')
            ajuste = 1.0 + (v - d) * 0.025
            lam_casa *= max(0.85, min(1.15, ajuste))
        
        if forma_fora:
            v = forma_fora.upper().count('V')
            d = forma_fora.upper().count('D')
            ajuste = 1.0 + (v - d) * 0.025
            lam_fora *= max(0.85, min(1.15, ajuste))
        
        # 3. Calcular probabilidades de cada placar COM correção Dixon-Coles
        probabilidades = {}
        for gc in range(self.MAX_GOLS + 1):
            for gf in range(self.MAX_GOLS + 1):
                p_casa = self.poisson_prob(lam_casa, gc)
                p_fora = self.poisson_prob(lam_fora, gf)
                p_placar = p_casa * p_fora
                
                # Aplicar correção Dixon-Coles
                dc_corr = self.dixon_coles_correction(gc, gf, lam_casa, lam_fora, self.TAU)
                p_placar *= dc_corr
                
                probabilidades[f"{gc}x{gf}"] = max(0, p_placar)
        
        # Normalizar
        total = sum(probabilidades.values())
        if total > 0:
            probabilidades = {k: v/total for k, v in probabilidades.items()}
        
        # 4. Top 5 placares
        top5 = sorted(probabilidades.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # 5. Resultado mais provável
        prob_v_casa = sum(v for k, v in probabilidades.items() if int(k.split('x')[0]) > int(k.split('x')[1]))
        prob_empate = sum(v for k, v in probabilidades.items() if int(k.split('x')[0]) == int(k.split('x')[1]))
        prob_v_fora = sum(v for k, v in probabilidades.items() if int(k.split('x')[0]) < int(k.split('x')[1]))
        
        # 6. Over/Under e BTTS
        prob_over25 = sum(v for k, v in probabilidades.items() 
                         if int(k.split('x')[0]) + int(k.split('x')[1]) > 2)
        prob_over15 = sum(v for k, v in probabilidades.items() 
                         if int(k.split('x')[0]) + int(k.split('x')[1]) > 1)
        prob_btts = sum(v for k, v in probabilidades.items() 
                       if int(k.split('x')[0]) > 0 and int(k.split('x')[1]) > 0)
        
        return {
            "mandante": mandante,
            "visitante": visitante,
            "liga": liga,
            "lambda_casa": round(lam_casa, 2),
            "lambda_fora": round(lam_fora, 2),
            "placar_provavel": top5[0][0],
            "prob_placar": round(top5[0][1] * 100, 1),
            "top5": [(p, round(prob*100, 1)) for p, prob in top5],
            "prob_vitoria_casa": round(prob_v_casa * 100, 1),
            "prob_empate": round(prob_empate * 100, 1),
            "prob_vitoria_fora": round(prob_v_fora * 100, 1),
            "prob_over_2_5": round(prob_over25 * 100, 1),
            "prob_btts": round(prob_btts * 100, 1),
            "eh_classico": eh_classico,
        }


# ==================== DADOS DOS JOGOS DA CARTELA ====================

predictor = ScorePredictorV4()

jogos = [
    {
        "mandante": "Liverpool",
        "visitante": "Manchester City", 
        "liga": "premier_league",
        # Liverpool: Líder da PL, ataque avassalador (Salah, Díaz), defesa sólida
        "fa_casa": 92, "fd_casa": 88,
        # City: Fase irregular 2025/26, mas elenco top, defesa sofrendo mais
        "fa_fora": 85, "fd_fora": 72,
        "classico": True,
        "forma_casa": "VVVVV",   # Liverpool em grande fase
        "forma_fora": "VEVDV",   # City oscilando
    },
    {
        "mandante": "Valencia",
        "visitante": "Real Madrid",
        "liga": "la_liga",
        # Valencia: Time médio da La Liga, ataque fraco, defesa razoável
        "fa_casa": 48, "fd_casa": 52,
        # Real Madrid: Top mundial, Mbappé+Vini+Bellingham
        "fa_fora": 95, "fd_fora": 85,
        "classico": False,
        "forma_casa": "DEVDE",   # Valencia perdendo bastante
        "forma_fora": "VVVVE",   # Real Madrid dominando
    },
    {
        "mandante": "Vasco da Gama",
        "visitante": "Botafogo",
        "liga": "carioca",
        # Vasco: Time tradicional, elenco médio para estadual
        "fa_casa": 62, "fd_casa": 55,
        # Botafogo: Campeão Libertadores 2024, elenco forte
        "fa_fora": 82, "fd_fora": 80,
        "classico": True,  # Clássico carioca
        "forma_casa": "VEV",     # Início de estadual
        "forma_fora": "VVE",     # Início de estadual
    },
    {
        "mandante": "Cruzeiro",
        "visitante": "América MG",
        "liga": "mineiro",
        # Cruzeiro: Grande de MG, investimento forte
        "fa_casa": 72, "fd_casa": 68,
        # América MG: Time menor, defesa frágil historicamente
        "fa_fora": 45, "fd_fora": 48,
        "classico": True,  # Clássico mineiro
        "forma_casa": "VEV",
        "forma_fora": "EVD",
    },
    {
        "mandante": "Corinthians",
        "visitante": "Palmeiras",
        "liga": "paulista",
        # Corinthians: Elenco reformulado, Memphis + reforços
        "fa_casa": 72, "fd_casa": 62,
        # Palmeiras: Maior investimento do Brasil, elenco completo
        "fa_fora": 88, "fd_fora": 90,
        "classico": True,  # Derby Paulista
        "forma_casa": "VEVD",
        "forma_fora": "VVVE",
    },
]


# ==================== EXECUTAR PREVISÕES ====================

print("=" * 80)
print("⚽ PREVISÃO DE PLACARES — CARTELA PLACAR DO JOTA — 08/02/2026")
print("   Modelo: Poisson + Dixon-Coles Correction (V4)")
print("   Sem frequências hardcoded | Fator casa REAL por liga")
print("=" * 80)

for jogo in jogos:
    resultado = predictor.prever_jogo(
        mandante=jogo["mandante"],
        visitante=jogo["visitante"],
        forca_ataque_casa=jogo["fa_casa"],
        forca_defesa_casa=jogo["fd_casa"],
        forca_ataque_fora=jogo["fa_fora"],
        forca_defesa_fora=jogo["fd_fora"],
        liga=jogo["liga"],
        eh_classico=jogo["classico"],
        forma_casa=jogo.get("forma_casa", ""),
        forma_fora=jogo.get("forma_fora", ""),
    )
    
    liga_nome = jogo["liga"].replace("_", " ").upper()
    
    print(f"\n{'─' * 80}")
    print(f"  🏆 {liga_nome}")
    print(f"  🏠 {resultado['mandante']}  vs  {resultado['visitante']} 🚌")
    if resultado['eh_classico']:
        print(f"  ⚡ CLÁSSICO")
    print(f"{'─' * 80}")
    
    print(f"  📊 λ (gols esperados): {resultado['mandante'][:3]} = {resultado['lambda_casa']}  |  {resultado['visitante'][:3]} = {resultado['lambda_fora']}")
    
    print(f"\n  🎯 PLACAR MAIS PROVÁVEL: {resultado['placar_provavel']}  ({resultado['prob_placar']}%)")
    
    print(f"\n  📈 Probabilidades de Resultado:")
    print(f"     Vitória {resultado['mandante'][:12]:<12}: {resultado['prob_vitoria_casa']:>5.1f}%")
    print(f"     Empate              : {resultado['prob_empate']:>5.1f}%")
    print(f"     Vitória {resultado['visitante'][:12]:<12}: {resultado['prob_vitoria_fora']:>5.1f}%")
    
    print(f"\n  🔝 Top 5 Placares Mais Prováveis:")
    for i, (placar, prob) in enumerate(resultado['top5'], 1):
        barra = "█" * int(prob)
        print(f"     {i}. {placar:>4}  {prob:>5.1f}%  {barra}")
    
    print(f"\n  ⚽ Mercados:")
    print(f"     Over 2.5 gols: {resultado['prob_over_2_5']:>5.1f}%")
    print(f"     BTTS (ambos marcam): {resultado['prob_btts']:>5.1f}%")

print(f"\n{'═' * 80}")
print(f"  📋 RESUMO — PALPITES PARA A CARTELA:")
print(f"{'═' * 80}")

for jogo in jogos:
    resultado = predictor.prever_jogo(
        mandante=jogo["mandante"],
        visitante=jogo["visitante"],
        forca_ataque_casa=jogo["fa_casa"],
        forca_defesa_casa=jogo["fd_casa"],
        forca_ataque_fora=jogo["fa_fora"],
        forca_defesa_fora=jogo["fd_fora"],
        liga=jogo["liga"],
        eh_classico=jogo["classico"],
        forma_casa=jogo.get("forma_casa", ""),
        forma_fora=jogo.get("forma_fora", ""),
    )
    
    # Escolher o melhor palpite considerando top 3
    top3 = resultado['top5'][:3]
    palpite = top3[0][0]
    
    # Análise qualitativa
    if resultado['prob_vitoria_casa'] > resultado['prob_vitoria_fora'] + 10:
        tendencia = f"Favorito: {resultado['mandante'][:3]} (casa)"
    elif resultado['prob_vitoria_fora'] > resultado['prob_vitoria_casa'] + 10:
        tendencia = f"Favorito: {resultado['visitante'][:3]} (fora)"
    else:
        tendencia = "Jogo equilibrado"
    
    # Segundo palpite (alternativa)
    alt_palpite = top3[1][0] if len(top3) > 1 else "-"
    
    print(f"\n  {resultado['mandante']:>15} vs {resultado['visitante']:<15}  →  🎯 {palpite}  (alt: {alt_palpite})")
    print(f"  {'':>15}    {'':15}     {tendencia}")

print(f"\n{'═' * 80}")
print(f"  ℹ️  Modelo: Poisson (base) + Correção Dixon-Coles (τ=0.12)")
print(f"  ℹ️  Fator casa real por liga | Sem viés de frequências fixas")
print(f"  ℹ️  Dados: forças estimadas por elenco + forma recente")
print(f"{'═' * 80}")


# ==================== COMPARAÇÃO V3 vs V4 ====================

print(f"\n\n{'=' * 80}")
print(f"  🔬 COMPARAÇÃO: MODELO ATUAL (V3) vs MODELO CORRIGIDO (V4)")
print(f"{'=' * 80}")

# Carregar predictor V3
try:
    from src.analysis.score_predictor import ScorePredictor, ModoPrevisao
    
    v3 = ScorePredictor()
    
    # Mapeamento de jogos para parâmetros do V3
    jogos_v3 = [
        ("LIV", "MCI", 92, 72, "premier"),
        ("VAL", "RMA", 48, 95, "la_liga"),
        ("VAS", "BOT", 62, 82, "carioca"),
        ("CRU", "AME", 72, 45, "mineiro"),
        ("COR", "PAL", 72, 90, "paulista"),
    ]
    
    print(f"\n  {'Jogo':<20} {'V3 Placar':>12} {'V3 Prob':>8} {'V4 Placar':>12} {'V4 Prob':>8} {'Diferença':>12}")
    print(f"  {'─'*20} {'─'*12} {'─'*8} {'─'*12} {'─'*8} {'─'*12}")
    
    for i, (m, v, fm, fv, camp) in enumerate(jogos_v3):
        # V3
        prev_v3 = v3.prever_confronto(
            mandante=m, visitante=v,
            forca_mandante=fm, forca_visitante=fv,
            campeonato=camp, rodada=5,
            eh_classico=jogos[i]["classico"]
        )
        
        # V4
        resultado_v4 = predictor.prever_jogo(
            mandante=jogos[i]["mandante"],
            visitante=jogos[i]["visitante"],
            forca_ataque_casa=jogos[i]["fa_casa"],
            forca_defesa_casa=jogos[i]["fd_casa"],
            forca_ataque_fora=jogos[i]["fa_fora"],
            forca_defesa_fora=jogos[i]["fd_fora"],
            liga=jogos[i]["liga"],
            eh_classico=jogos[i]["classico"],
            forma_casa=jogos[i].get("forma_casa", ""),
            forma_fora=jogos[i].get("forma_fora", ""),
        )
        
        nome_jogo = f"{m} x {v}"
        diff = "✅ Igual" if prev_v3.placar_provavel == resultado_v4['placar_provavel'] else "⚠️ Diferente"
        
        print(f"  {nome_jogo:<20} {prev_v3.placar_provavel:>12} {prev_v3.probabilidade_placar:>7.1f}% {resultado_v4['placar_provavel']:>12} {resultado_v4['prob_placar']:>7.1f}% {diff:>12}")
        
        # Mostrar contexto V3 para comparação
        print(f"  {'':20} Contexto V3: {prev_v3.contexto} | Modo: {prev_v3.modo_previsao} | Peso freq: {prev_v3.peso_frequencia}")

except ImportError as e:
    print(f"  ⚠️ Não foi possível carregar V3 para comparação: {e}")

print(f"\n{'=' * 80}")
