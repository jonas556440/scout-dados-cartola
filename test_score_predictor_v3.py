#!/usr/bin/env python3
"""
Teste do ScorePredictorV3 - Validação com dados reais das rodadas 1 e 2

Objetivo: Verificar se o sistema acerta os mesmos 8 placares que o Marcelo acertou
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.analysis.score_predictor import ScorePredictor, ModoPrevisao, ContextoJogo
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

# Dados reais das rodadas
RODADA_1_BRASILEIRAO = [
    ("Atlético MG", "Palmeiras", "1x3", 45, 75, 1, "brasileirao"),
    ("Coritiba", "Bragantino", "0x2", 40, 60, 1, "brasileirao"),
    ("Internacional", "Atlético PR", "1x1", 65, 60, 1, "brasileirao"),
    ("Vitória", "Remo", "1x0", 50, 40, 1, "brasileirao"),
    ("Fluminense", "Grêmio", "2x1", 70, 65, 1, "brasileirao"),
    ("Chapecoense", "Santos", "1x2", 35, 60, 1, "brasileirao"),
    ("Corinthians", "Bahia", "0x2", 60, 65, 1, "brasileirao"),
    ("São Paulo", "Flamengo", "1x2", 70, 75, 1, "brasileirao"),
    ("Mirassol", "Vasco", "2x2", 50, 60, 1, "brasileirao"),
    ("Botafogo", "Cruzeiro", "1x2", 70, 70, 1, "brasileirao"),
]

RODADA_FDS_REGIONAIS = [
    ("Flamengo", "Corinthians", "3x1", 85, 70, 5, "copa", True),  # SuperCopa
    ("São Paulo", "Santos", "3x0", 75, 65, 3, "paulista", True),  # Clássico
    ("Bragantino", "São Bernardo", "1x1", 55, 35, 2, "paulista"),  # Regional
    ("Mirassol", "Novorizontino", "2x0", 45, 30, 2, "paulista"),  # Regional
    ("Botafogo SP", "Palmeiras", "0x3", 30, 80, 2, "paulista"),  # Dominante
    ("Botafogo", "Fluminense", "1x2", 75, 75, 5, "carioca", True),  # Clássico
    ("Grêmio", "Juventude", "1x1", 60, 40, 2, "gaucho"),  # Regional
    ("Caxias", "Internacional", "1x1", 35, 70, 2, "gaucho"),  # Regional
    ("Sport", "Santa Cruz", "2x1", 50, 40, 2, "pernambucano"),  # Regional
    ("Tottenham", "M. City", "2x2", 75, 80, 20, "premier"),  # Internacional
]


def testar_previsoes(predictor: ScorePredictor, jogos: list, nome_rodada: str, modo: ModoPrevisao):
    """Testa previsões e compara com resultados reais"""
    
    console.print(f"\n[bold cyan]{'='*80}[/bold cyan]")
    console.print(f"[bold yellow]🎯 Testando {nome_rodada} - Modo: {modo.value.upper()}[/bold yellow]")
    console.print(f"[bold cyan]{'='*80}[/bold cyan]\n")
    
    acertos = 0
    erros = 0
    detalhes = []
    
    for mandante, visitante, placar_real, forca_m, forca_v, rodada, campeonato, *extra in jogos:
        eh_classico = extra[0] if extra else False
        
        # Prever
        previsao = predictor.prever_confronto(
            mandante=mandante,
            visitante=visitante,
            forca_mandante=forca_m,
            forca_visitante=forca_v,
            rodada=rodada,
            campeonato=campeonato,
            eh_classico=eh_classico,
            modo=modo
        )
        
        # Verificar acerto
        acertou = previsao.placar_provavel == placar_real
        if acertou:
            acertos += 1
            emoji = "✅"
        else:
            erros += 1
            emoji = "❌"
        
        detalhes.append({
            "jogo": f"{mandante} x {visitante}",
            "real": placar_real,
            "previsto": previsao.placar_provavel,
            "prob": previsao.probabilidade_placar,
            "contexto": previsao.contexto,
            "peso_freq": previsao.peso_frequencia,
            "acertou": acertou,
            "emoji": emoji,
            "top3": previsao.top_placares[:3]
        })
    
    # Exibir tabela de resultados
    table = Table(title=f"Resultados - {nome_rodada}")
    table.add_column("Jogo", style="cyan")
    table.add_column("Real", style="yellow")
    table.add_column("Previsto", style="magenta")
    table.add_column("Prob%", justify="right")
    table.add_column("Contexto", style="blue")
    table.add_column("Peso Freq", justify="right")
    table.add_column("Top 3", style="dim")
    table.add_column("✓", justify="center")
    
    for d in detalhes:
        top3_str = ", ".join([f"{p}({prob}%)" for p, prob in d["top3"]])
        table.add_row(
            d["jogo"],
            d["real"],
            d["previsto"],
            f"{d['prob']:.1f}%",
            d["contexto"],
            f"{d['peso_freq']*100:.0f}%",
            top3_str,
            d["emoji"]
        )
    
    console.print(table)
    
    # Resumo
    total = acertos + erros
    taxa_acerto = (acertos / total * 100) if total > 0 else 0
    
    resumo = f"""
    [bold green]✅ Acertos: {acertos}/{total}[/bold green]
    [bold red]❌ Erros: {erros}/{total}[/bold red]
    [bold yellow]📊 Taxa de Acerto: {taxa_acerto:.1f}%[/bold yellow]
    
    [bold cyan]🎯 Meta Marcelo: 40% (4 de 10)[/bold cyan]
    [bold {'green' if taxa_acerto >= 40 else 'red'}]{'✅ SUPEROU' if taxa_acerto >= 40 else '❌ NÃO ATINGIU'} a meta![/bold {'green' if taxa_acerto >= 40 else 'red'}]
    """
    
    console.print(Panel(resumo, title="📈 Resumo", border_style="green" if taxa_acerto >= 40 else "red"))
    
    return acertos, total


def main():
    console.print(Panel.fit(
        "[bold yellow]🧪 Teste ScorePredictorV3 - Validação Marcelo[/bold yellow]\n"
        "[dim]Comparando previsões com os 8 acertos do Marcelo em 20 jogos[/dim]",
        border_style="cyan"
    ))
    
    predictor = ScorePredictor()
    
    # Testar diferentes modos
    modos = [ModoPrevisao.HIBRIDO, ModoPrevisao.POISSON, ModoPrevisao.FREQUENCIA]
    
    resultados_gerais = {}
    
    for modo in modos:
        console.print(f"\n[bold magenta]{'#'*80}[/bold magenta]")
        console.print(f"[bold white]TESTANDO MODO: {modo.value.upper()}[/bold white]")
        console.print(f"[bold magenta]{'#'*80}[/bold magenta]")
        
        # Rodada 1
        acertos_r1, total_r1 = testar_previsoes(
            predictor, 
            RODADA_1_BRASILEIRAO, 
            "Rodada 1 - Brasileirão",
            modo
        )
        
        # Rodada Fim de Semana
        acertos_r2, total_r2 = testar_previsoes(
            predictor, 
            RODADA_FDS_REGIONAIS, 
            "Rodada Fim de Semana - Regionais",
            modo
        )
        
        # Total geral
        acertos_total = acertos_r1 + acertos_r2
        total_geral = total_r1 + total_r2
        taxa_geral = (acertos_total / total_geral * 100) if total_geral > 0 else 0
        
        resultados_gerais[modo.value] = {
            "acertos": acertos_total,
            "total": total_geral,
            "taxa": taxa_geral
        }
    
    # Comparação final
    console.print(f"\n[bold cyan]{'='*80}[/bold cyan]")
    console.print(f"[bold yellow]📊 COMPARAÇÃO GERAL - Todos os Modos[/bold yellow]")
    console.print(f"[bold cyan]{'='*80}[/bold cyan]\n")
    
    table_final = Table(title="Comparação de Modos")
    table_final.add_column("Modo", style="cyan")
    table_final.add_column("Acertos", justify="right")
    table_final.add_column("Total", justify="right")
    table_final.add_column("Taxa %", justify="right")
    table_final.add_column("vs Marcelo (40%)", justify="center")
    
    for modo, resultado in resultados_gerais.items():
        acertos = resultado["acertos"]
        total = resultado["total"]
        taxa = resultado["taxa"]
        vs_marcelo = "✅ MELHOR" if taxa > 40 else ("✓ IGUAL" if taxa == 40 else "❌ PIOR")
        
        table_final.add_row(
            modo.upper(),
            str(acertos),
            str(total),
            f"{taxa:.1f}%",
            vs_marcelo
        )
    
    console.print(table_final)
    
    # Melhor modo
    melhor_modo = max(resultados_gerais.items(), key=lambda x: x[1]["taxa"])
    
    console.print(Panel(
        f"[bold green]🏆 MELHOR MODO: {melhor_modo[0].upper()}[/bold green]\n"
        f"[yellow]Taxa de Acerto: {melhor_modo[1]['taxa']:.1f}%[/yellow]\n"
        f"[cyan]Acertos: {melhor_modo[1]['acertos']}/{melhor_modo[1]['total']}[/cyan]\n\n"
        f"[dim]Marcelo acertou 8/20 (40%) usando padrões simples[/dim]\n"
        f"[bold]{'✅ Nosso sistema SUPEROU o Marcelo!' if melhor_modo[1]['taxa'] > 40 else '⚠️  Precisamos ajustar o sistema'}[/bold]",
        title="🎯 Conclusão",
        border_style="green" if melhor_modo[1]["taxa"] > 40 else "yellow"
    ))


if __name__ == "__main__":
    main()
