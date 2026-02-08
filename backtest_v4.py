#!/usr/bin/env python3
"""
Backtest V4 — Avaliação com Log-Loss + Acertos

Compara ScorePredictor V4 (Dixon-Coles) contra:
  - Poisson puro (sem correção DC)
  - Baseline uniforme (1/64 = ~1.56%)
  - Baseline "sempre 1x0" (ingênuo)

Dados: 20 jogos reais (Rodada 1 Brasileirão + Regionais/Copas)
Métrica principal: LOG-LOSS (quanto menor, melhor)
"""

import sys
import math
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.analysis.score_predictor import ScorePredictor, ModoPrevisao, PrevisaoPlacar


# ==================== DADOS REAIS ====================

# Rodada 1 Brasileirão 2026
# (mandante, visitante, placar_real, força_mand, força_visit, rodada, campeonato, clássico)
RODADA_1_BRASILEIRAO = [
    ("CAM", "PAL", "1x3", 45, 75, 1, "brasileirao", False),
    ("CFC", "RBB", "0x2", 40, 60, 1, "brasileirao", False),
    ("INT", "CAP", "1x1", 65, 60, 1, "brasileirao", False),
    ("VIT", "REM", "1x0", 50, 40, 1, "brasileirao", False),
    ("FLU", "GRE", "2x1", 70, 65, 1, "brasileirao", False),
    ("CHA", "SAN", "1x2", 35, 60, 1, "brasileirao", False),
    ("COR", "BAH", "0x2", 60, 65, 1, "brasileirao", False),
    ("SAO", "FLA", "1x2", 70, 75, 1, "brasileirao", False),
    ("MIR", "VAS", "2x2", 50, 60, 1, "brasileirao", False),
    ("BOT", "CRU", "1x2", 70, 70, 1, "brasileirao", False),
]

# Regionais e Copas (rodada anterior ao campeonato)
JOGOS_REGIONAIS = [
    ("FLA", "COR", "3x1", 85, 70, 5, "copa", True),     # SuperCopa
    ("SAO", "SAN", "3x0", 75, 65, 3, "paulista", True),  # Clássico
    ("RBB", "SBC", "1x1", 55, 35, 2, "paulista", False),
    ("MIR", "NOV", "2x0", 45, 30, 2, "paulista", False),
    ("BSP", "PAL", "0x3", 30, 80, 2, "paulista", False),
    ("BOT", "FLU", "1x2", 75, 75, 5, "carioca", True),
    ("GRE", "JUV", "1x1", 60, 40, 2, "gaucho", False),
    ("CAX", "INT", "1x1", 35, 70, 2, "gaucho", False),
    ("SPO", "SCR", "2x1", 50, 40, 2, "pernambucano", False),
    ("TOT", "MCI", "2x2", 75, 80, 20, "premier", False),
]

ALL_GAMES = RODADA_1_BRASILEIRAO + JOGOS_REGIONAIS


# ==================== FUNÇÕES AUXILIARES ====================

def resultado_str(gc: int, gf: int) -> str:
    """'V', 'E' ou 'D' a partir de gols."""
    if gc > gf: return "V"
    if gc == gf: return "E"
    return "D"


def log_loss_single(prob: float) -> float:
    """Log-loss de uma previsão individual."""
    return -math.log(max(prob, 1e-6))


def gerar_previsoes(predictor, jogos, modo):
    """Gera previsões para uma lista de jogos."""
    previsoes = []
    for mand, visit, real, fm, fv, rod, camp, *extra in jogos:
        classico = extra[0] if extra else False
        prev = predictor.prever_confronto(
            mandante=mand, visitante=visit,
            forca_mandante=fm, forca_visitante=fv,
            rodada=rod, campeonato=camp,
            eh_classico=classico, modo=modo,
        )
        previsoes.append((prev, real))
    return previsoes


def avaliar(previsoes_resultados, label=""):
    """Avalia uma lista de (PrevisaoPlacar, placar_real)."""
    predictor = ScorePredictor()
    n = len(previsoes_resultados)
    ll_total = 0.0
    acertos_exato = 0
    acertos_resultado = 0
    detalhes = []

    for prev, real in previsoes_resultados:
        gc_r, gf_r = map(int, real.split('x'))
        res_real = resultado_str(gc_r, gf_r)

        # Probabilidade do placar real
        probs = predictor.calcular_probabilidades_placar(prev.xg_mandante, prev.xg_visitante)
        p_real = probs.get(real, 0.001)
        ll = log_loss_single(p_real)
        ll_total += ll

        # Acerto exato
        exato = prev.placar_provavel == real
        if exato:
            acertos_exato += 1

        # Acerto resultado (V/E/D)
        res_prev = resultado_str(prev.placar_casa, prev.placar_fora)
        acerto_ved = res_prev == res_real
        if acerto_ved:
            acertos_resultado += 1

        detalhes.append({
            "jogo": f"{prev.mandante} vs {prev.visitante}",
            "real": real,
            "previsto": prev.placar_provavel,
            "p_real": p_real,
            "ll": ll,
            "exato": exato,
            "ved_prev": res_prev,
            "ved_real": res_real,
            "acerto_ved": acerto_ved,
            "lambda_c": prev.xg_mandante,
            "lambda_f": prev.xg_visitante,
        })

    ll_medio = ll_total / n if n > 0 else float('inf')

    return {
        "label": label,
        "jogos": n,
        "log_loss": ll_medio,
        "log_loss_total": ll_total,
        "acertos_exatos": acertos_exato,
        "taxa_exato": acertos_exato / n * 100,
        "acertos_resultado": acertos_resultado,
        "taxa_resultado": acertos_resultado / n * 100,
        "detalhes": detalhes,
    }


def baseline_uniforme(jogos):
    """Baseline: distribuição uniforme sobre 8x8=64 placares."""
    p_uniforme = 1.0 / 64
    ll = -math.log(p_uniforme)
    return {
        "label": "Baseline Uniforme (1/64)",
        "jogos": len(jogos),
        "log_loss": ll,
        "acertos_exatos": 0,
        "taxa_exato": 0.0,
        "acertos_resultado": 0,
        "taxa_resultado": 0.0,
    }


def baseline_sempre_1x0(jogos):
    """Baseline ingênuo: sempre prever 1x0."""
    acertos_ex = sum(1 for j in jogos if j[2] == "1x0")
    acertos_res = 0
    for j in jogos:
        gc, gf = map(int, j[2].split('x'))
        if gc > gf:  # Prever 1x0 = vitória mandante
            acertos_res += 1

    return {
        "label": "Baseline 'Sempre 1x0'",
        "jogos": len(jogos),
        "log_loss": float('nan'),  # Sem modelo probabilístico
        "acertos_exatos": acertos_ex,
        "taxa_exato": acertos_ex / len(jogos) * 100,
        "acertos_resultado": acertos_res,
        "taxa_resultado": acertos_res / len(jogos) * 100,
    }


# ==================== MAIN ====================

def main():
    predictor = ScorePredictor()

    print("=" * 80)
    print("  BACKTEST V4 — Poisson + Dixon-Coles")
    print("  20 jogos reais (R1 Brasileirão + Regionais)")
    print("=" * 80)

    # === Modelo V4: Dixon-Coles ===
    prev_dc = gerar_previsoes(predictor, ALL_GAMES, ModoPrevisao.DIXON_COLES)
    res_dc = avaliar(prev_dc, "V4 Dixon-Coles")

    # === Modelo V4: Poisson Puro ===
    prev_pp = gerar_previsoes(predictor, ALL_GAMES, ModoPrevisao.POISSON)
    res_pp = avaliar(prev_pp, "V4 Poisson Puro")

    # === Baselines ===
    res_uni = baseline_uniforme(ALL_GAMES)
    res_1x0 = baseline_sempre_1x0(ALL_GAMES)

    # ==================== DETALHES POR JOGO ====================
    print(f"\n{'─' * 80}")
    print(f"  DETALHES POR JOGO (Dixon-Coles)")
    print(f"{'─' * 80}")
    print(f"{'Jogo':<22} {'Real':>5} {'Prev':>5} {'P(real)':>8} {'LL':>7} {'V/E/D':>6} {'Exato':>6}")
    print(f"{'─' * 80}")

    for d in res_dc["detalhes"]:
        marker_ex = " ✓" if d["exato"] else ""
        marker_ved = "✓" if d["acerto_ved"] else "✗"
        print(
            f"{d['jogo']:<22} {d['real']:>5} {d['previsto']:>5} "
            f"{d['p_real']:>7.1%} {d['ll']:>7.3f} "
            f"{d['ved_prev']}/{d['ved_real']:>1}={marker_ved:<2} {marker_ex}"
        )

    # ==================== COMPARAÇÃO ====================
    print(f"\n{'=' * 80}")
    print(f"  COMPARAÇÃO DE MODELOS")
    print(f"{'=' * 80}")
    print(f"{'Modelo':<28} {'Log-Loss':>9} {'Exatos':>8} {'%Exato':>8} {'V/E/D':>7} {'%V/E/D':>8}")
    print(f"{'─' * 80}")

    for res in [res_dc, res_pp, res_uni, res_1x0]:
        ll_str = f"{res['log_loss']:.4f}" if not math.isnan(res.get('log_loss', float('nan'))) else "N/A"
        print(
            f"{res['label']:<28} {ll_str:>9} "
            f"{res['acertos_exatos']:>5}/{res['jogos']:<2} "
            f"{res['taxa_exato']:>6.1f}% "
            f"{res['acertos_resultado']:>4}/{res['jogos']:<2} "
            f"{res['taxa_resultado']:>6.1f}%"
        )

    # ==================== ANÁLISE ====================
    print(f"\n{'=' * 80}")
    print("  ANÁLISE")
    print(f"{'=' * 80}")

    # Diferença DC vs Poisson
    diff_ll = res_pp["log_loss"] - res_dc["log_loss"]
    melhor = "Dixon-Coles" if diff_ll > 0 else "Poisson Puro"
    print(f"\n  Dixon-Coles vs Poisson Puro:")
    print(f"    Δ Log-Loss: {diff_ll:+.4f} (melhor: {melhor})")
    print(f"    DC exatos: {res_dc['acertos_exatos']}, Poisson exatos: {res_pp['acertos_exatos']}")

    # Vs uniforme
    diff_uni = res_uni["log_loss"] - res_dc["log_loss"]
    print(f"\n  Dixon-Coles vs Uniforme:")
    print(f"    Δ Log-Loss: {diff_uni:+.4f} (economia informacional)")
    print(f"    Uniforme LL = {res_uni['log_loss']:.4f} (entropia máxima)")

    # Qualidade
    ll = res_dc["log_loss"]
    if ll < 2.5:
        nota = "EXCELENTE"
    elif ll < 3.0:
        nota = "BOM"
    elif ll < 3.5:
        nota = "REGULAR"
    else:
        nota = "FRACO"

    print(f"\n  Nota V4 Dixon-Coles: {nota} (LL={ll:.4f})")
    print(f"  Referências:")
    print(f"    < 2.5 = Excelente (modelos calibrados com dados abundantes)")
    print(f"    < 3.0 = Bom (nível competitivo)")
    print(f"    < 3.5 = Regular (melhor que random)")
    print(f"    > 3.5 = Fraco (revisar calibração)")

    # ==================== CALIBRAÇÃO ====================
    print(f"\n{'=' * 80}")
    print("  CALIBRAÇÃO: P(Real) por faixa de confiança")
    print(f"{'=' * 80}")

    # Agrupar por faixa de probabilidade prevista
    faixas = {"0-5%": [], "5-10%": [], "10-15%": [], "15%+": []}
    for d in res_dc["detalhes"]:
        p = d["p_real"] * 100
        if p < 5:
            faixas["0-5%"].append(d)
        elif p < 10:
            faixas["5-10%"].append(d)
        elif p < 15:
            faixas["10-15%"].append(d)
        else:
            faixas["15%+"].append(d)

    for faixa, jogos in faixas.items():
        if jogos:
            p_medio = sum(d["p_real"] for d in jogos) / len(jogos) * 100
            ll_medio = sum(d["ll"] for d in jogos) / len(jogos)
            print(f"  {faixa}: {len(jogos)} jogos, P(real) médio={p_medio:.1f}%, LL médio={ll_medio:.3f}")

    print(f"\n{'=' * 80}")
    print("  Backtest concluído")
    print(f"{'=' * 80}")

    return res_dc


if __name__ == "__main__":
    main()
