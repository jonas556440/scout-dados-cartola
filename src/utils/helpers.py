"""
Funções utilitárias - Cartola FC 2026
"""
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

sys.path.append(str(Path(__file__).parent.parent.parent))

from config.settings import settings


console = Console()


def formatar_cartoletas(valor: float) -> str:
    """Formata valor em cartoletas"""
    return f"C$ {valor:.2f}"


def formatar_pontos(valor: float) -> str:
    """Formata pontuação"""
    if valor >= 0:
        return f"+{valor:.1f}"
    return f"{valor:.1f}"


def get_status_emoji(status_id: int) -> str:
    """Retorna emoji para status do jogador"""
    emojis = {
        2: "🤕",   # Dúvida
        3: "🚫",   # Suspenso
        5: "💔",   # Contundido
        6: "❓",   # Nulo
        7: "✅",   # Provável
    }
    return emojis.get(status_id, "❓")


def get_posicao_emoji(posicao_id: int) -> str:
    """Retorna emoji para posição"""
    emojis = {
        1: "🧤",   # Goleiro
        2: "🔙",   # Lateral
        3: "🛡️",   # Zagueiro
        4: "⚙️",   # Meia
        5: "⚽",   # Atacante
        6: "📋",   # Técnico
    }
    return emojis.get(posicao_id, "👤")


def print_atleta(atleta: Dict[str, Any], mostrar_scouts: bool = False):
    """Imprime informações de um atleta formatadas"""
    status_emoji = get_status_emoji(atleta.get("status_id", 6))
    pos_emoji = get_posicao_emoji(atleta.get("posicao_id", 4))
    
    console.print(Panel(
        f"{pos_emoji} [bold]{atleta.get('apelido', 'N/A')}[/bold] {status_emoji}\n"
        f"Clube: {atleta.get('clube', 'N/A')} | "
        f"Posição: {atleta.get('posicao', 'N/A')}\n"
        f"Preço: [green]{formatar_cartoletas(atleta.get('preco_num', 0))}[/green] | "
        f"Média: [cyan]{atleta.get('media_num', 0):.2f}[/cyan]",
        title=f"Atleta #{atleta.get('atleta_id', 0)}",
        expand=False
    ))


def criar_tabela_atletas(
    atletas: List[Dict[str, Any]], 
    titulo: str = "Atletas"
) -> Table:
    """Cria tabela formatada de atletas"""
    tabela = Table(title=titulo, show_header=True, header_style="bold magenta")
    
    tabela.add_column("", style="dim", width=3)
    tabela.add_column("Nome", style="cyan", min_width=15)
    tabela.add_column("Clube", style="white", width=5)
    tabela.add_column("Pos", style="white", width=4)
    tabela.add_column("Status", style="white", width=3)
    tabela.add_column("Preço", style="green", justify="right")
    tabela.add_column("Média", style="yellow", justify="right")
    tabela.add_column("MPV", style="red", justify="right")
    
    for i, atleta in enumerate(atletas, 1):
        status_emoji = get_status_emoji(atleta.get("status_id", 6))
        pos_emoji = get_posicao_emoji(atleta.get("posicao_id", 4))
        
        tabela.add_row(
            str(i),
            atleta.get("apelido", "N/A")[:18],
            atleta.get("clube", "N/A"),
            settings.POSICOES.get(atleta.get("posicao_id", 0), {}).get("abrev", "???"),
            status_emoji,
            formatar_cartoletas(atleta.get("preco_num", 0)),
            f"{atleta.get('media_num', 0):.1f}",
            f"{atleta.get('mpv', 0):.1f}" if "mpv" in atleta else "-"
        )
    
    return tabela


def criar_tabela_time(
    time_data: Dict[str, Any],
    titulo: str = "Time Escalado"
) -> Table:
    """Cria tabela formatada de um time"""
    tabela = Table(title=titulo, show_header=True, header_style="bold blue")
    
    tabela.add_column("Pos", style="dim", width=4)
    tabela.add_column("Nome", style="cyan", min_width=15)
    tabela.add_column("Clube", style="white", width=5)
    tabela.add_column("Preço", style="green", justify="right")
    tabela.add_column("Média", style="yellow", justify="right")
    tabela.add_column("Prev", style="magenta", justify="right")
    tabela.add_column("", style="bold", width=3)
    
    titulares = time_data.get("titulares", [])
    capitao_id = time_data.get("capitao_id")
    
    for atleta in titulares:
        cap_marker = "⭐" if atleta.get("atleta_id") == capitao_id else ""
        
        tabela.add_row(
            atleta.get("posicao", "???"),
            atleta.get("apelido", "N/A")[:18],
            atleta.get("clube", "N/A"),
            formatar_cartoletas(atleta.get("preco", 0)),
            f"{atleta.get('media', 0):.1f}",
            f"{atleta.get('pontuacao_esperada', 0):.1f}",
            cap_marker
        )
    
    return tabela


def print_resumo_rodada(dados: Dict[str, Any]):
    """Imprime resumo da rodada"""
    console.print("\n")
    console.rule("[bold blue]📊 Resumo da Rodada[/bold blue]")
    
    console.print(f"\n🎯 Rodada: [bold]{dados.get('rodada', 0)}[/bold]")
    console.print(f"📅 Status: {dados.get('status', 'N/A')}")
    
    if dados.get("time_valorizacao"):
        console.print("\n[green]📈 Time Valorização:[/green]")
        console.print(f"   Custo: {formatar_cartoletas(dados['time_valorizacao'].get('custo', 0))}")
        console.print(f"   Pontos Previstos: {dados['time_valorizacao'].get('pontos', 0):.1f}")
    
    if dados.get("time_pontuacao"):
        console.print("\n[yellow]🎯 Time Pontuação:[/yellow]")
        console.print(f"   Custo: {formatar_cartoletas(dados['time_pontuacao'].get('custo', 0))}")
        console.print(f"   Pontos Previstos: {dados['time_pontuacao'].get('pontos', 0):.1f}")


def print_destaques(destaques: List[Dict[str, Any]], titulo: str = "🌟 Destaques"):
    """Imprime lista de destaques"""
    console.print(f"\n[bold]{titulo}[/bold]")
    
    for i, d in enumerate(destaques[:10], 1):
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        console.print(f"  {emoji} {d.get('apelido', 'N/A')}: [green]{d.get('pontuacao', 0):.1f}[/green] pts")


def calcular_mpv_simples(preco: float, media: float) -> float:
    """Calcula MPV usando fórmula simplificada"""
    return max(0, (preco * 2.5) - media + 2)


def filtrar_por_status(atletas: List[Dict], status_ids: List[int] = None) -> List[Dict]:
    """Filtra atletas por status"""
    if status_ids is None:
        status_ids = [7]  # Apenas prováveis por padrão
    
    return [a for a in atletas if a.get("status_id") in status_ids]


def filtrar_por_preco(atletas: List[Dict], preco_min: float = 0, preco_max: float = 100) -> List[Dict]:
    """Filtra atletas por faixa de preço"""
    return [
        a for a in atletas 
        if preco_min <= a.get("preco_num", 0) <= preco_max
    ]


def filtrar_por_posicao(atletas: List[Dict], posicao_ids: List[int]) -> List[Dict]:
    """Filtra atletas por posição"""
    return [a for a in atletas if a.get("posicao_id") in posicao_ids]


def agrupar_por_posicao(atletas: List[Dict]) -> Dict[str, List[Dict]]:
    """Agrupa atletas por posição"""
    grupos = {}
    
    for atleta in atletas:
        pos_id = atleta.get("posicao_id", 0)
        pos_abrev = settings.POSICOES.get(pos_id, {}).get("abrev", "???")
        
        if pos_abrev not in grupos:
            grupos[pos_abrev] = []
        
        grupos[pos_abrev].append(atleta)
    
    return grupos


def ordenar_por_custo_beneficio(atletas: List[Dict]) -> List[Dict]:
    """Ordena atletas por custo-benefício (média/preço)"""
    def cb(a):
        preco = a.get("preco_num", 0)
        media = a.get("media_num", 0)
        return media / preco if preco > 0 else 0
    
    return sorted(atletas, key=cb, reverse=True)


def validar_time(atletas: List[Dict], esquema: str = "4-4-2") -> Dict[str, Any]:
    """
    Valida se um time está correto
    
    Returns:
        Dicionário com validação e erros
    """
    resultado = {
        "valido": True,
        "erros": [],
        "custo_total": 0
    }
    
    # Mapear esquema para necessidades
    esquemas = {
        "3-4-3": {"GOL": 1, "ZAG": 3, "LAT": 0, "MEI": 4, "ATA": 3, "TEC": 1},
        "3-5-2": {"GOL": 1, "ZAG": 3, "LAT": 0, "MEI": 5, "ATA": 2, "TEC": 1},
        "4-3-3": {"GOL": 1, "ZAG": 2, "LAT": 2, "MEI": 3, "ATA": 3, "TEC": 1},
        "4-4-2": {"GOL": 1, "ZAG": 2, "LAT": 2, "MEI": 4, "ATA": 2, "TEC": 1},
        "4-5-1": {"GOL": 1, "ZAG": 2, "LAT": 2, "MEI": 5, "ATA": 1, "TEC": 1},
        "5-3-2": {"GOL": 1, "ZAG": 3, "LAT": 2, "MEI": 3, "ATA": 2, "TEC": 1},
        "5-4-1": {"GOL": 1, "ZAG": 3, "LAT": 2, "MEI": 4, "ATA": 1, "TEC": 1},
    }
    
    necessidades = esquemas.get(esquema, esquemas["4-4-2"])
    
    # Contar por posição
    contagem = {}
    for atleta in atletas:
        pos_id = atleta.get("posicao_id", 0)
        pos_abrev = settings.POSICOES.get(pos_id, {}).get("abrev", "???")
        contagem[pos_abrev] = contagem.get(pos_abrev, 0) + 1
        resultado["custo_total"] += atleta.get("preco_num", 0)
    
    # Validar posições
    for pos, qtd in necessidades.items():
        atual = contagem.get(pos, 0)
        if atual != qtd:
            resultado["valido"] = False
            resultado["erros"].append(f"{pos}: esperado {qtd}, encontrado {atual}")
    
    # Validar orçamento
    if resultado["custo_total"] > 100:
        resultado["valido"] = False
        resultado["erros"].append(f"Orçamento excedido: C${resultado['custo_total']:.2f}")
    
    return resultado


def exportar_time_json(time_data: Dict[str, Any], caminho: str):
    """Exporta time para arquivo JSON"""
    import json
    
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(time_data, f, ensure_ascii=False, indent=2)


def importar_time_json(caminho: str) -> Dict[str, Any]:
    """Importa time de arquivo JSON"""
    import json
    
    with open(caminho, 'r', encoding='utf-8') as f:
        return json.load(f)


if __name__ == "__main__":
    # Teste das funções
    console.print("[bold]Teste de Helpers[/bold]\n")
    
    atleta_teste = {
        "atleta_id": 123,
        "apelido": "Alan Patrick",
        "clube": "INT",
        "posicao": "MEI",
        "posicao_id": 4,
        "status_id": 7,
        "preco_num": 8.0,
        "media_num": 6.5
    }
    
    print_atleta(atleta_teste)
    
    mpv = calcular_mpv_simples(8.0, 6.5)
    console.print(f"\nMPV calculado: [red]{mpv:.2f}[/red]")
