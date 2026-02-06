#!/usr/bin/env python3
"""
Previsão Rodada 2 - Brasileirão 2026
Sistema ScorePredictorV3 - Modo Híbrido
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.analysis.score_predictor import ScorePredictor, ModoPrevisao
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

# Jogos da Rodada 2
RODADA_2 = [
    ("Flamengo", "Internacional", 75, 65, 2, "brasileirao", False),
    ("Bragantino", "Atlético MG", 60, 60, 2, "brasileirao", False),
    ("Remo", "Mirassol", 40, 50, 2, "brasileirao", False),
    ("Santos", "São Paulo", 65, 70, 2, "brasileirao", True),  # Clássico
    ("Grêmio", "Botafogo", 65, 70, 2, "brasileirao", False),
    ("Palmeiras", "Vitória", 75, 50, 2, "brasileirao", False),
    ("Bahia", "Fluminense", 65, 70, 2, "brasileirao", False),
    ("Vasco", "Chapecoense", 60, 35, 2, "brasileirao", False),
    ("Cruzeiro", "Coritiba", 70, 40, 2, "brasileirao", False),
]

# Resultados reais da Rodada 1
RODADA_1_RESULTADOS = [
    ("Atlético MG", "Palmeiras", "1x3"),
    ("Coritiba", "Bragantino", "0x2"),
    ("Internacional", "Atlético PR", "1x1"),
    ("Vitória", "Remo", "1x0"),
    ("Fluminense", "Grêmio", "2x1"),
    ("Chapecoense", "Santos", "1x2"),
    ("Corinthians", "Bahia", "0x2"),
    ("São Paulo", "Flamengo", "1x2"),
    ("Mirassol", "Vasco", "2x2"),
    ("Botafogo", "Cruzeiro", "1x2"),
]


def calcular_pontos_rodada1():
    """Calcula quantos pontos teríamos feito na rodada 1"""
    
    console.print("\n[bold cyan]" + "="*80 + "[/bold cyan]")
    console.print("[bold yellow]📊 PONTUAÇÃO RODADA 1 - Sistema vs Marcelo[/bold yellow]")
    console.print("[bold cyan]" + "="*80 + "[/bold cyan]\n")
    
    predictor = ScorePredictor()
    
    # Jogos da rodada 1 com força dos times
    rodada_1_jogos = [
        ("Atlético MG", "Palmeiras", "1x3", 60, 75),
        ("Coritiba", "Bragantino", "0x2", 40, 60),
        ("Internacional", "Atlético PR", "1x1", 65, 60),
        ("Vitória", "Remo", "1x0", 50, 40),
        ("Fluminense", "Grêmio", "2x1", 70, 65),
        ("Chapecoense", "Santos", "1x2", 35, 60),
        ("Corinthians", "Bahia", "0x2", 60, 65),
        ("São Paulo", "Flamengo", "1x2", 70, 75),
        ("Mirassol", "Vasco", "2x2", 50, 60),
        ("Botafogo", "Cruzeiro", "1x2", 70, 70),
    ]
    
    pontos_total = 0
    acertos_exato = 0
    acertos_simples = 0
    
    table = Table(title="Análise Rodada 1")
    table.add_column("Jogo", style="cyan")
    table.add_column("Real", style="yellow")
    table.add_column("Previsto", style="magenta")
    table.add_column("Resultado", style="green")
    table.add_column("Pontos", justify="right")
    
    for mandante, visitante, placar_real, forca_m, forca_v in rodada_1_jogos:
        previsao = predictor.prever_confronto(
            mandante=mandante,
            visitante=visitante,
            forca_mandante=forca_m,
            forca_visitante=forca_v,
            rodada=1,
            campeonato="brasileirao",
            modo=ModoPrevisao.HIBRIDO
        )
        
        previsto = previsao.placar_provavel
        
        # Verificar acerto
        if previsto == placar_real:
            resultado = "✅ EXATO"
            pontos = 5
            acertos_exato += 1
        else:
            # Verificar acerto simples
            real_casa, real_fora = map(int, placar_real.split('x'))
            prev_casa, prev_fora = map(int, previsto.split('x'))
            
            # Determinar resultado
            if real_casa > real_fora:
                resultado_real = "casa"
            elif real_fora > real_casa:
                resultado_real = "fora"
            else:
                resultado_real = "empate"
            
            if prev_casa > prev_fora:
                resultado_prev = "casa"
            elif prev_fora > prev_casa:
                resultado_prev = "fora"
            else:
                resultado_prev = "empate"
            
            if resultado_real == resultado_prev:
                resultado = "✓ Simples"
                pontos = 3
                acertos_simples += 1
            else:
                resultado = "❌ Errou"
                pontos = 0
        
        pontos_total += pontos
        
        table.add_row(
            f"{mandante} x {visitante}",
            placar_real,
            f"{previsto} ({previsao.probabilidade_placar:.0f}%)",
            resultado,
            f"{pontos} pts"
        )
    
    console.print(table)
    
    # Resumo
    console.print(f"\n[bold cyan]{'='*80}[/bold cyan]")
    
    resumo = f"""
[bold yellow]📈 RESUMO RODADA 1:[/bold yellow]

[bold green]✅ Acertos Exato:[/bold green] {acertos_exato} x 5 pts = {acertos_exato * 5} pontos
[bold blue]✓ Acertos Simples:[/bold blue] {acertos_simples} x 3 pts = {acertos_simples * 3} pontos
[bold white]TOTAL:[/bold white] {pontos_total} pontos

[bold magenta]🎯 Marcelo (campeão):[/bold magenta] 4 acertos exatos = 20 pontos

[bold {'green' if pontos_total >= 20 else 'red'}]{'🏆 EMPATAMOS/GANHAMOS!' if pontos_total >= 20 else f'📊 Faltaram {20 - pontos_total} pontos'}[/bold {'green' if pontos_total >= 20 else 'red'}]
    """
    
    console.print(Panel(resumo, title="Resultado Final Rodada 1", border_style="green" if pontos_total >= 20 else "yellow"))
    
    return pontos_total


def prever_rodada2():
    """Gera previsões para a rodada 2"""
    
    console.print("\n[bold cyan]" + "="*80 + "[/bold cyan]")
    console.print("[bold yellow]🔮 PREVISÕES RODADA 2 - Brasileirão 2026[/bold yellow]")
    console.print("[bold cyan]" + "="*80 + "[/bold cyan]\n")
    
    predictor = ScorePredictor()
    
    table = Table(title="Palpites Rodada 2")
    table.add_column("Jogo", style="cyan", width=30)
    table.add_column("Palpite", style="bold yellow", justify="center")
    table.add_column("Prob%", justify="right")
    table.add_column("Análise", style="blue")
    table.add_column("Top 3 Alternativas", style="dim")
    
    palpites_resumo = []
    
    console.print("[bold yellow]⚠️  ANÁLISE CONTEXTUAL ATIVADA[/bold yellow]\n")
    console.print("[dim]Favorecendo times fortes em jogos desiguais (diff > 20)...[/dim]\n")
    
    for dados in RODADA_2:
        mandante, visitante, forca_m, forca_v, rodada, campeonato, eh_classico = dados
        
        # Análise contextual
        diff_forca = abs(forca_m - forca_v)
        
        # Escolher modo baseado no contexto
        if diff_forca > 20:
            modo_usar = ModoPrevisao.POISSON  # Favorece o mais forte
            analise = "💪 Favorito claro"
        elif diff_forca < 10:
            modo_usar = ModoPrevisao.HIBRIDO
            analise = "⚖️ Equilibrado"
        else:
            modo_usar = ModoPrevisao.HIBRIDO
            analise = "📊 Normal"
        
        if eh_classico:
            analise += " 🔥"
        
        previsao = predictor.prever_confronto(
            mandante=mandante,
            visitante=visitante,
            forca_mandante=forca_m,
            forca_visitante=forca_v,
            rodada=rodada,
            campeonato=campeonato,
            eh_classico=eh_classico,
            modo=modo_usar
        )
        
        top3 = ", ".join([f"{p}({prob:.0f}%)" for p, prob in previsao.top_placares[:3]])
        
        table.add_row(
            f"{mandante} x {visitante}",
            f"[bold]{previsao.placar_provavel}[/bold]",
            f"{previsao.probabilidade_placar:.1f}%",
            analise,
            top3
        )
        
        palpites_resumo.append({
            "jogo": f"{mandante} x {visitante}",
            "placar": previsao.placar_provavel,
            "prob": previsao.probabilidade_placar,
            "analise": analise
        })
    
    console.print(table)
    
    # Lista resumida para copiar
    console.print(f"\n[bold green]📋 PALPITES PARA COPIAR:[/bold green]\n")
    
    for p in palpites_resumo:
        console.print(f"[yellow]{p['jogo']}[/yellow] → [bold cyan]{p['placar']}[/bold cyan]")
    
    # Análise de estratégia
    console.print(f"\n[bold cyan]{'='*80}[/bold cyan]")
    console.print(f"[bold yellow]💡 ANÁLISE ESTRATÉGICA:[/bold yellow]\n")
    
    analises = {}
    for p in palpites_resumo:
        analise = p['analise']
        if analise not in analises:
            analises[analise] = []
        analises[analise].append(p)
    
    for analise, jogos in analises.items():
        console.print(f"[bold blue]{analise}[/bold blue] ({len(jogos)} jogos)")
        for j in jogos:
            console.print(f"  • {j['jogo']} → {j['placar']} ({j['prob']:.0f}%)")
        console.print()
    
    # Dicas
    dicas = """
[bold yellow]🎯 DICAS PARA RODADA 2:[/bold yellow]

1. [bold]Rodada 2 = INÍCIO ainda:[/bold] Fator casa ainda fraco (+5% apenas)
2. [bold]Santos x São Paulo:[/bold] Clássico paulista - placar pode ser mais aberto
3. [bold]Palmeiras x Vitória:[/bold] Grande diferença de força - esperar goleada
4. [bold]Cruzeiro x Coritiba:[/bold] Idem - Cruzeiro forte em casa
5. [bold]Flamengo x Inter:[/bold] Jogo equilibrado - empate ou vitória apertada

[bold cyan]💰 JOGOS "BANCO" (alta confiança):[/bold cyan]
- Palmeiras x Vitória (favorito claro)
- Cruzeiro x Coritiba (favorito claro)
- Vasco x Chapecoense (favorito em casa)

[bold red]⚠️ JOGOS ARRISCADOS:[/bold red]
- Flamengo x Internacional (muito equilibrado)
- Santos x São Paulo (clássico imprevisível)
- Grêmio x Botafogo (ambos fortes)
    """
    
    console.print(Panel(dicas, title="💡 Estratégia", border_style="yellow"))


def main():
    console.print(Panel.fit(
        "[bold yellow]⚽ Sistema de Palpites - Cartola FC 2026[/bold yellow]\n"
        "[dim]ScorePredictorV3 - Modo Híbrido (Poisson + Frequências)[/dim]",
        border_style="cyan"
    ))
    
    # Calcular pontos da rodada 1
    pontos_r1 = calcular_pontos_rodada1()
    
    # Prever rodada 2
    prever_rodada2()
    
    console.print(f"\n[bold green]✅ Análise concluída![/bold green]\n")


if __name__ == "__main__":
    main()
