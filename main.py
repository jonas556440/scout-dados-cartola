"""
Cartola FC 2026 - Sistema Inteligente de Escalação
===================================================

Aplicação principal com CLI interativo.

Comandos principais:
    - mercado: Exibe atletas disponíveis
    - escalar: Gera times otimizados
    - coletar: Coleta scouts da rodada
    - status: Status do mercado
    - historico: Histórico de escalações
"""
import sys
import os
from pathlib import Path

# Adicionar diretório raiz ao path
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

import argparse
from datetime import datetime
from typing import Optional, List

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm

from config.settings import settings
from src.api.cartola_api import CartolaAPI
from src.database.db_manager import DatabaseManager
from src.database.history_manager import HistoryManager
from src.analysis.mpv_calculator import MPVCalculator
from src.analysis.team_selector import TeamSelector, TeamFormatter
from src.analysis.stats_analyzer import StatsAnalyzer
from src.scrapers.scout_collector import ScoutCollector
from src.utils.helpers import (
    criar_tabela_atletas, print_destaques, 
    calcular_mpv_simples, filtrar_por_status,
    filtrar_por_preco, ordenar_por_custo_beneficio
)


console = Console()


class CartolaApp:
    """
    Aplicação principal do Cartola FC 2026
    
    Funcionalidades:
    - Gerar times otimizados (valorização e pontuação)
    - Coletar e armazenar scouts históricos
    - Analisar jogadores e tendências
    - Acompanhar evolução do patrimônio
    """
    
    def __init__(self):
        console.print("[dim]Inicializando Cartola FC 2026...[/dim]")
        
        self.api = CartolaAPI()
        self.db = DatabaseManager()
        self.history = HistoryManager()
        self.mpv_calc = MPVCalculator()
        self.team_selector = TeamSelector()
        self.stats = StatsAnalyzer()
        self.collector = ScoutCollector(self.api, self.db)
        
        self._cache_mercado = None
        self._cache_status = None
    
    def get_mercado(self, force_refresh: bool = False):
        """Obtém dados do mercado (com cache)"""
        if self._cache_mercado is None or force_refresh:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                progress.add_task("Carregando mercado...", total=None)
                self._cache_mercado = self.api.get_mercado()
        
        return self._cache_mercado
    
    def get_status(self, force_refresh: bool = False):
        """Obtém status do mercado"""
        if self._cache_status is None or force_refresh:
            self._cache_status = self.api.get_status_mercado()
        return self._cache_status
    
    def cmd_status(self):
        """Exibe status do mercado"""
        status = self.get_status(force_refresh=True)
        
        if not status:
            console.print("[red]❌ Erro ao obter status do mercado[/red]")
            return
        
        rodada = status.get("rodada_atual", 0)
        status_mercado = status.get("status_mercado", 0)
        
        status_texto = {
            1: "[green]🟢 Aberto[/green]",
            2: "[yellow]🟡 Fechando[/yellow]",
            4: "[red]🔴 Fechado[/red]"
        }.get(status_mercado, "[dim]❓ Desconhecido[/dim]")
        
        console.print(Panel(
            f"[bold]Rodada Atual:[/bold] {rodada}\n"
            f"[bold]Status:[/bold] {status_texto}\n"
            f"[bold]Atualizado:[/bold] {datetime.now().strftime('%H:%M:%S')}",
            title="📊 Status do Mercado",
            expand=False
        ))
    
    def cmd_mercado(self, posicao: str = None, preco_max: float = None, 
                    apenas_provaveis: bool = True, limite: int = 20):
        """Exibe atletas do mercado"""
        mercado = self.get_mercado()
        
        if not mercado:
            console.print("[red]❌ Erro ao obter mercado[/red]")
            return
        
        atletas = mercado.get("atletas", [])
        clubes = mercado.get("clubes", {})
        
        # Filtrar por status
        if apenas_provaveis:
            atletas = filtrar_por_status(atletas, [7])
        
        # Filtrar por posição
        if posicao:
            pos_map = {"GOL": 1, "LAT": 2, "ZAG": 3, "MEI": 4, "ATA": 5, "TEC": 6}
            pos_id = pos_map.get(posicao.upper())
            if pos_id:
                atletas = [a for a in atletas if a.get("posicao_id") == pos_id]
        
        # Filtrar por preço
        if preco_max:
            atletas = filtrar_por_preco(atletas, 0, preco_max)
        
        # Adicionar clube abrev
        for atleta in atletas:
            clube_id = atleta.get("clube_id")
            clube_info = clubes.get(str(clube_id), {})
            atleta["clube"] = clube_info.get("abreviacao", "???")
        
        # Calcular MPV
        for atleta in atletas:
            atleta["mpv"] = calcular_mpv_simples(
                atleta.get("preco_num", 0),
                atleta.get("media_num", 0)
            )
        
        # Ordenar por custo-benefício
        atletas = ordenar_por_custo_beneficio(atletas)
        
        # Limitar resultados
        atletas = atletas[:limite]
        
        # Criar tabela
        titulo = f"📋 Mercado"
        if posicao:
            titulo += f" - {posicao.upper()}"
        if preco_max:
            titulo += f" (até C${preco_max})"
        
        tabela = criar_tabela_atletas(atletas, titulo)
        console.print(tabela)
        
        console.print(f"\n[dim]Total: {len(atletas)} atletas[/dim]")
    
    def cmd_confrontos(self):
        """Exibe análise completa dos confrontos da rodada"""
        console.print("\n[bold blue]⚽ Analisando Confrontos da Rodada[/bold blue]\n")
        
        mercado = self.get_mercado()
        status = self.get_status()
        
        if not mercado:
            console.print("[red]❌ Erro ao obter mercado[/red]")
            return
        
        clubes = mercado.get("clubes", {})
        rodada = status.get("rodada_atual", 1) if status else 1
        
        # Buscar partidas
        partidas_response = self.api.get_partidas(rodada)
        
        if isinstance(partidas_response, dict):
            partidas = partidas_response.get("partidas", [])
        elif isinstance(partidas_response, list):
            partidas = partidas_response
        else:
            partidas = []
        
        if not partidas:
            console.print("[yellow]⚠️ Partidas não disponíveis para esta rodada[/yellow]")
            return
        
        # Importar analisador
        from src.analysis.confrontos_analyzer import ConfrontosAnalyzer
        
        analyzer = ConfrontosAnalyzer()
        analyzer.analisar_rodada(partidas, clubes)
        
        # Exibir relatório
        relatorio = analyzer.formatar_relatorio()
        console.print(relatorio)
        
        # Dica adicional
        console.print("\n[dim]Use 'python main.py escalar' para gerar times otimizados com base nos confrontos[/dim]")
    
    def cmd_escalar(self, esquema: str = "4-4-2", preco_max: float = 12.0):
        """Gera times otimizados para a rodada"""
        console.print("\n[bold blue]🎯 Gerando Times da Rodada[/bold blue]\n")
        
        mercado = self.get_mercado()
        
        if not mercado:
            console.print("[red]❌ Erro ao obter mercado[/red]")
            return
        
        atletas = mercado.get("atletas", [])
        clubes = mercado.get("clubes", {})
        
        # Obter rodada atual
        status = self.get_status()
        rodada = status.get("rodada_atual", 1) if status else 1
        
        # NOVO v3: Buscar partidas da rodada para análise de confrontos
        console.print(f"[dim]Analisando confrontos da rodada {rodada}...[/dim]")
        partidas_response = self.api.get_partidas(rodada)
        
        # Extrair lista de partidas do response (pode ser dict ou list)
        if isinstance(partidas_response, dict):
            partidas = partidas_response.get("partidas", [])
        elif isinstance(partidas_response, list):
            partidas = partidas_response
        else:
            partidas = []
        
        if partidas:
            console.print(f"[green]✅ {len(partidas)} partidas encontradas[/green]")
            
            # Exibir resumo dos confrontos
            console.print("\n[bold]📊 Confrontos da Rodada:[/bold]")
            for p in partidas[:5]:  # Mostrar primeiros 5
                mandante_id = p.get("clube_casa_id") or p.get("clube_mandante_id")
                visitante_id = p.get("clube_visitante_id")
                m_info = clubes.get(str(mandante_id), {})
                v_info = clubes.get(str(visitante_id), {})
                console.print(f"  • {m_info.get('abreviacao', '???')} x {v_info.get('abreviacao', '???')}")
            if len(partidas) > 5:
                console.print(f"  [dim]... e mais {len(partidas) - 5} jogos[/dim]")
            
            # Configurar confrontos no seletor
            self.team_selector.configurar_confrontos(partidas, clubes)
        else:
            console.print("[yellow]⚠️ Partidas não disponíveis - usando análise básica[/yellow]")
        
        # Filtrar apenas prováveis
        atletas = filtrar_por_status(atletas, [7])
        
        if not atletas:
            console.print("[yellow]⚠️ Nenhum atleta provável encontrado[/yellow]")
            return
        
        console.print(f"\n[dim]Analisando {len(atletas)} atletas prováveis...[/dim]\n")
        
        # Analisar cada atleta (v7: com rodada_atual)
        analisados = []
        for atleta in atletas:
            clube_id = atleta.get("clube_id")
            clube_info = clubes.get(str(clube_id), {})
            clube_abrev = clube_info.get("abreviacao", "???")
            
            pos_id = atleta.get("posicao_id", 4)
            pos_abrev = settings.POSICOES.get(pos_id, {}).get("abrev", "???")
            
            analise = self.mpv_calc.analisar_jogador(
                atleta,
                clube_abrev=clube_abrev,
                posicao_abrev=pos_abrev,
                rodada_atual=rodada
            )
            analisados.append(analise)
        
        # Gerar times (v7: com rodada_atual)
        time_valor, time_pontos = self.team_selector.gerar_times_rodada(
            analisados, esquema, rodada_atual=rodada
        )
        
        # Exibir time de valorização
        if time_valor:
            console.print(TeamFormatter.formatar_time(time_valor))
            
            # Salvar no banco
            status = self.get_status()
            rodada = status.get("rodada_atual", 1) if status else 1
            
            self.db.salvar_escalacao(
                rodada_id=rodada,
                tipo="valorizacao",
                esquema=esquema,
                atletas_ids=[a.atleta_id for a in time_valor.titulares],
                capitao_id=time_valor.capitao.atleta_id,
                custo_total=time_valor.custo_total,
                pontuacao_prevista=time_valor.pontuacao_prevista
            )
        else:
            console.print("[yellow]⚠️ Não foi possível gerar time de valorização[/yellow]")
        
        # Exibir time de pontuação
        if time_pontos:
            console.print(TeamFormatter.formatar_time(time_pontos))
            
            # Salvar no banco
            status = self.get_status()
            rodada = status.get("rodada_atual", 1) if status else 1
            
            self.db.salvar_escalacao(
                rodada_id=rodada,
                tipo="pontuacao",
                esquema=esquema,
                atletas_ids=[a.atleta_id for a in time_pontos.titulares],
                capitao_id=time_pontos.capitao.atleta_id,
                custo_total=time_pontos.custo_total,
                pontuacao_prevista=time_pontos.pontuacao_prevista
            )
        else:
            console.print("[yellow]⚠️ Não foi possível gerar time de pontuação[/yellow]")
        
        # Comparação
        if time_valor and time_pontos:
            console.print(TeamFormatter.formatar_comparacao(time_valor, time_pontos))
    
    def cmd_coletar(self, rodada: int = None):
        """Coleta scouts da rodada"""
        console.print("\n[bold blue]📥 Coletando Scouts[/bold blue]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            # Atualizar mercado
            progress.add_task("Atualizando mercado...", total=None)
            res_mercado = self.collector.coletar_mercado_atualizado(rodada)
            
            if res_mercado["sucesso"]:
                console.print(f"[green]✅ {res_mercado['total_atletas']} atletas atualizados[/green]")
            else:
                console.print(f"[yellow]⚠️ Mercado: {res_mercado.get('erro', 'Erro')}[/yellow]")
        
        # Coletar scouts
        console.print("\n[dim]Coletando pontuações...[/dim]")
        res_scouts = self.collector.coletar_scouts_rodada(rodada)
        
        if res_scouts["sucesso"]:
            console.print(f"[green]✅ {res_scouts['total_jogadores']} scouts registrados[/green]")
            
            # Mostrar destaques
            if res_scouts.get("destaques"):
                print_destaques(res_scouts["destaques"], "🌟 Destaques da Rodada")
            
            # Mostrar decepções
            if res_scouts.get("decepcoes"):
                console.print("\n[red]💔 Decepções:[/red]")
                for d in res_scouts["decepcoes"][:5]:
                    console.print(f"   {d['apelido']}: [red]{d['pontuacao']:.1f}[/red] pts")
        else:
            console.print(f"[yellow]⚠️ {res_scouts.get('erro', 'Sem dados')}[/yellow]")
    
    def cmd_sincronizar(self):
        """Sincroniza todos os dados com o banco"""
        console.print("\n[bold blue]🔄 Sincronizando Dados[/bold blue]\n")
        
        # Atualizar mercado
        res_mercado = self.collector.coletar_mercado_atualizado()
        console.print(f"Atletas: {res_mercado.get('total_atletas', 0)}")
        console.print(f"Clubes: {res_mercado.get('total_clubes', 0)}")
        
        # Estatísticas do banco
        stats = self.db.get_estatisticas_gerais()
        
        console.print(Panel(
            f"Total Atletas: {stats['total_atletas']}\n"
            f"Atletas Prováveis: {stats['atletas_provaveis']}\n"
            f"Total Clubes: {stats['total_clubes']}\n"
            f"Total Scouts: {stats['total_scouts']}\n"
            f"Total Escalações: {stats['total_escalacoes']}",
            title="📊 Estatísticas do Banco"
        ))
    
    def cmd_valorizadores(self, preco_max: float = 10.0, limite: int = 20):
        """Lista jogadores com potencial de valorização"""
        console.print("\n[bold green]📈 Potenciais Valorizadores[/bold green]\n")
        
        mercado = self.get_mercado()
        
        if not mercado:
            console.print("[red]❌ Erro ao obter mercado[/red]")
            return
        
        atletas = mercado.get("atletas", [])
        clubes = mercado.get("clubes", {})
        
        # Filtrar
        atletas = filtrar_por_status(atletas, [7])
        atletas = filtrar_por_preco(atletas, 0, preco_max)
        
        # Analisar
        analisados = []
        for atleta in atletas:
            clube_id = atleta.get("clube_id")
            clube_info = clubes.get(str(clube_id), {})
            clube_abrev = clube_info.get("abreviacao", "???")
            
            pos_id = atleta.get("posicao_id", 4)
            pos_abrev = settings.POSICOES.get(pos_id, {}).get("abrev", "???")
            
            atleta["clube"] = clube_abrev
            atleta["mpv"] = self.mpv_calc.calcular_mpv_basico(
                atleta.get("preco_num", 0),
                atleta.get("media_num", 0)
            )
            
            # Score de valorização
            media = atleta.get("media_num", 0)
            preco = atleta.get("preco_num", 1)
            mpv = atleta["mpv"]
            
            atleta["score"] = (media / preco) * max(0.1, (media - mpv + 5))
            analisados.append(atleta)
        
        # Ordenar por score
        analisados.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        # Limitar
        analisados = analisados[:limite]
        
        # Exibir tabela
        tabela = Table(title=f"📈 Top {limite} Valorizadores (até C${preco_max})")
        
        tabela.add_column("#", style="dim", width=3)
        tabela.add_column("Nome", style="cyan", min_width=15)
        tabela.add_column("Clube", width=5)
        tabela.add_column("Pos", width=4)
        tabela.add_column("Preço", style="green", justify="right")
        tabela.add_column("Média", style="yellow", justify="right")
        tabela.add_column("MPV", style="red", justify="right")
        tabela.add_column("Margem", style="magenta", justify="right")
        
        for i, a in enumerate(analisados, 1):
            margem = a.get("media_num", 0) - a.get("mpv", 0)
            margem_str = f"+{margem:.1f}" if margem >= 0 else f"{margem:.1f}"
            
            tabela.add_row(
                str(i),
                a.get("apelido", "N/A")[:18],
                a.get("clube", "???"),
                settings.POSICOES.get(a.get("posicao_id", 0), {}).get("abrev", "???"),
                f"C${a.get('preco_num', 0):.1f}",
                f"{a.get('media_num', 0):.1f}",
                f"{a.get('mpv', 0):.1f}",
                margem_str
            )
        
        console.print(tabela)
    
    def cmd_historico(self, rodada: int = None):
        """Exibe histórico de escalações"""
        console.print("\n[bold blue]📜 Histórico de Escalações[/bold blue]\n")
        
        if rodada:
            escalacoes = self.db.get_escalacoes_rodada(rodada)
        else:
            # Obter rodada atual
            status = self.get_status()
            rodada = status.get("rodada_atual", 1) if status else 1
            escalacoes = self.db.get_escalacoes_rodada(rodada)
        
        if not escalacoes:
            console.print(f"[dim]Nenhuma escalação encontrada para rodada {rodada}[/dim]")
            return
        
        for esc in escalacoes:
            tipo_emoji = "📈" if esc.tipo == "valorizacao" else "🎯"
            
            console.print(Panel(
                f"[bold]Esquema:[/bold] {esc.esquema}\n"
                f"[bold]Custo:[/bold] C${esc.custo_total:.1f}\n"
                f"[bold]Pontuação Prevista:[/bold] {esc.pontuacao_prevista:.1f}\n"
                f"[bold]Capitão ID:[/bold] {esc.capitao_id}\n"
                f"[bold]Atletas:[/bold] {len(esc.atletas_ids)} jogadores",
                title=f"{tipo_emoji} Time {esc.tipo.title()} - Rodada {esc.rodada_id}"
            ))
    
    def cmd_patrimonio(self):
        """Exibe evolução do patrimônio (cartoletas)"""
        console.print("\n[bold green]💰 Evolução do Patrimônio[/bold green]\n")
        
        # Obter resumo geral
        resumo = self.history.get_resumo_geral()
        
        # Tabela de resumo
        tabela = Table(title="📊 Resumo por Tipo de Time")
        tabela.add_column("Métrica", style="cyan")
        tabela.add_column("Valorização", style="green", justify="right")
        tabela.add_column("Pontuação", style="yellow", justify="right")
        
        for tipo in ["valorizacao", "pontuacao"]:
            dados = resumo.get(tipo, {})
            if tipo == "valorizacao":
                val_data = dados
            else:
                pont_data = dados
        
        tabela.add_row(
            "Cartoletas Atuais",
            f"C${val_data.get('cartoletas_atuais', 100):.1f}",
            f"C${pont_data.get('cartoletas_atuais', 100):.1f}"
        )
        tabela.add_row(
            "Lucro/Prejuízo",
            f"C${val_data.get('lucro_total', 0):+.1f}",
            f"C${pont_data.get('lucro_total', 0):+.1f}"
        )
        tabela.add_row(
            "Rodadas Jogadas",
            str(val_data.get('rodadas_jogadas', 0)),
            str(pont_data.get('rodadas_jogadas', 0))
        )
        tabela.add_row(
            "Pontuação Total",
            f"{val_data.get('pontuacao_total', 0):.1f}",
            f"{pont_data.get('pontuacao_total', 0):.1f}"
        )
        tabela.add_row(
            "Média por Rodada",
            f"{val_data.get('media_pontuacao', 0):.1f}",
            f"{pont_data.get('media_pontuacao', 0):.1f}"
        )
        tabela.add_row(
            "Maior Pontuação",
            f"{val_data.get('maior_pontuacao', 0):.1f}",
            f"{pont_data.get('maior_pontuacao', 0):.1f}"
        )
        
        console.print(tabela)
        
        # Evolução por rodada
        console.print("\n[bold]📈 Evolução por Rodada[/bold]\n")
        
        for tipo in ["valorizacao", "pontuacao"]:
            evolucao = self.history.get_evolucao_patrimonio(tipo)
            
            if not evolucao:
                continue
            
            emoji = "📈" if tipo == "valorizacao" else "🎯"
            console.print(f"{emoji} [bold]{tipo.title()}[/bold]:")
            
            for e in evolucao[-5:]:  # Últimas 5 rodadas
                diff = e.cartoletas_fim - e.cartoletas_inicio
                diff_str = f"[green]+{diff:.1f}[/green]" if diff >= 0 else f"[red]{diff:.1f}[/red]"
                
                console.print(
                    f"   R{e.rodada_id}: C${e.cartoletas_fim:.1f} ({diff_str}) | "
                    f"Pts: {e.pontuacao_rodada:.1f}"
                )
            
            console.print()
    
    def cmd_registrar_resultado(self, rodada: int = None):
        """Registra resultado de uma rodada após encerrar"""
        console.print("\n[bold blue]📝 Registrando Resultado da Rodada[/bold blue]\n")
        
        if not rodada:
            status = self.get_status()
            rodada = status.get("rodada_atual", 1) - 1 if status else 1
        
        if rodada < 1:
            console.print("[yellow]⚠️ Nenhuma rodada anterior para registrar[/yellow]")
            return
        
        # Coletar scouts se ainda não coletou
        console.print(f"[dim]Coletando scouts da rodada {rodada}...[/dim]")
        self.collector.coletar_scouts_rodada(rodada)
        
        # Registrar resultado
        resultado = self.history.registrar_resultado_rodada(rodada)
        
        if "erro" in resultado:
            console.print(f"[red]❌ {resultado['erro']}[/red]")
            return
        
        console.print(f"[green]✅ Resultado da rodada {rodada} registrado![/green]\n")
        
        for tipo, dados in resultado.items():
            emoji = "📈" if tipo == "valorizacao" else "🎯"
            diff = dados["diferenca"]
            diff_str = f"[green]+{diff:.1f}[/green]" if diff >= 0 else f"[red]{diff:.1f}[/red]"
            
            console.print(Panel(
                f"[bold]Previsto:[/bold] {dados['pontuacao_prevista']:.1f} pts\n"
                f"[bold]Real:[/bold] {dados['pontuacao_real']:.1f} pts\n"
                f"[bold]Diferença:[/bold] {diff_str}",
                title=f"{emoji} {tipo.title()}"
            ))
    
    def cmd_salvar_escalacao(self, esquema: str = "4-4-2"):
        """Salva escalação atual no histórico com cartoletas corretas"""
        console.print("\n[bold blue]💾 Salvando Escalação[/bold blue]\n")
        
        # Gerar times
        mercado = self.get_mercado()
        if not mercado:
            console.print("[red]❌ Erro ao obter mercado[/red]")
            return
        
        atletas = mercado.get("atletas", [])
        clubes = mercado.get("clubes", {})
        
        atletas = filtrar_por_status(atletas, [7])
        
        analisados = []
        for atleta in atletas:
            clube_id = atleta.get("clube_id")
            clube_info = clubes.get(str(clube_id), {})
            clube_abrev = clube_info.get("abreviacao", "???")
            pos_id = atleta.get("posicao_id", 4)
            pos_abrev = settings.POSICOES.get(pos_id, {}).get("abrev", "???")
            
            analise = self.mpv_calc.analisar_jogador(
                atleta, clube_abrev=clube_abrev, posicao_abrev=pos_abrev
            )
            analisados.append(analise)
        
        # Obter cartoletas disponíveis
        cartoletas_valor = self.history.get_cartoletas_atuais("valorizacao")
        cartoletas_pontos = self.history.get_cartoletas_atuais("pontuacao")
        
        console.print(f"[dim]Cartoletas Valorização: C${cartoletas_valor:.1f}[/dim]")
        console.print(f"[dim]Cartoletas Pontuação: C${cartoletas_pontos:.1f}[/dim]\n")
        
        # Gerar times com orçamento correto
        selector_valor = TeamSelector(orcamento=cartoletas_valor)
        selector_pontos = TeamSelector(orcamento=cartoletas_pontos)
        
        time_valor = selector_valor.selecionar_time_valorizacao(analisados, esquema)
        time_pontos = selector_pontos.selecionar_time_pontuacao(analisados, esquema)
        
        # Salvar no histórico
        status = self.get_status()
        rodada = status.get("rodada_atual", 1) if status else 1
        
        if time_valor:
            self.history.salvar_time_escalado(time_valor, rodada, cartoletas_valor)
            console.print(f"[green]✅ Time Valorização salvo (C${time_valor.custo_total:.1f})[/green]")
            console.print(TeamFormatter.formatar_time(time_valor))
        
        if time_pontos:
            self.history.salvar_time_escalado(time_pontos, rodada, cartoletas_pontos)
            console.print(f"[green]✅ Time Pontuação salvo (C${time_pontos.custo_total:.1f})[/green]")
            console.print(TeamFormatter.formatar_time(time_pontos))
        
        if time_valor and time_pontos:
            console.print(TeamFormatter.formatar_comparacao(time_valor, time_pontos))    
    def run_interativo(self):
        """Modo interativo"""
        console.print(Panel(
            "[bold]Cartola FC 2026[/bold]\n"
            "Sistema Inteligente de Escalação\n\n"
            "[dim]Digite 'ajuda' para ver comandos disponíveis[/dim]",
            title="⚽",
            expand=False
        ))
        
        while True:
            try:
                comando = Prompt.ask("\n[bold cyan]cartola[/bold cyan]")
                
                if not comando:
                    continue
                
                partes = comando.lower().split()
                cmd = partes[0]
                args = partes[1:]
                
                if cmd in ("sair", "exit", "q"):
                    console.print("[dim]Até a próxima! ⚽[/dim]")
                    break
                
                elif cmd in ("ajuda", "help", "h"):
                    self._mostrar_ajuda()
                
                elif cmd == "status":
                    self.cmd_status()
                
                elif cmd == "mercado":
                    posicao = args[0] if args else None
                    self.cmd_mercado(posicao=posicao)
                
                elif cmd == "escalar":
                    esquema = args[0] if args else "4-4-2"
                    self.cmd_escalar(esquema=esquema)
                
                elif cmd == "coletar":
                    rodada = int(args[0]) if args else None
                    self.cmd_coletar(rodada)
                
                elif cmd == "sync":
                    self.cmd_sincronizar()
                
                elif cmd == "valorizadores":
                    preco = float(args[0]) if args else 10.0
                    self.cmd_valorizadores(preco_max=preco)
                
                elif cmd == "historico":
                    rodada = int(args[0]) if args else None
                    self.cmd_historico(rodada)
                
                elif cmd == "patrimonio":
                    self.cmd_patrimonio()
                
                elif cmd == "resultado":
                    rodada = int(args[0]) if args else None
                    self.cmd_registrar_resultado(rodada)
                
                elif cmd == "salvar":
                    esquema = args[0] if args else "4-4-2"
                    self.cmd_salvar_escalacao(esquema)
                
                else:
                    console.print(f"[yellow]Comando desconhecido: {cmd}[/yellow]")
                    console.print("[dim]Digite 'ajuda' para ver comandos[/dim]")
                    
            except KeyboardInterrupt:
                console.print("\n[dim]Interrompido. Digite 'sair' para encerrar.[/dim]")
            except Exception as e:
                console.print(f"[red]Erro: {e}[/red]")
    
    def _mostrar_ajuda(self):
        """Mostra ajuda dos comandos"""
        console.print(Panel(
            "[bold]Comandos Disponíveis:[/bold]\n\n"
            "[bold cyan]📊 MERCADO[/bold cyan]\n"
            "[cyan]status[/cyan]              - Status do mercado\n"
            "[cyan]mercado[/cyan] [pos]       - Lista atletas (pos: GOL/LAT/ZAG/MEI/ATA/TEC)\n"
            "[cyan]valorizadores[/cyan] [max] - Potenciais valorizadores (max = preço)\n"
            "[cyan]sync[/cyan]                - Sincroniza banco de dados\n\n"
            "[bold cyan]⚽ ESCALAÇÃO[/bold cyan]\n"
            "[cyan]escalar[/cyan] [esquema]   - Gera times (ex: 4-4-2, 3-5-2)\n"
            "[cyan]salvar[/cyan] [esquema]    - Salva escalação com cartoletas atuais\n"
            "[cyan]coletar[/cyan] [rodada]    - Coleta scouts da rodada\n\n"
            "[bold cyan]📈 HISTÓRICO[/bold cyan]\n"
            "[cyan]historico[/cyan] [rodada]  - Histórico de escalações\n"
            "[cyan]patrimonio[/cyan]          - Evolução das cartoletas\n"
            "[cyan]resultado[/cyan] [rodada]  - Registra resultado da rodada\n\n"
            "[bold cyan]🔧 SISTEMA[/bold cyan]\n"
            "[cyan]ajuda[/cyan]               - Mostra esta ajuda\n"
            "[cyan]sair[/cyan]                - Encerra o programa",
            title="📖 Ajuda"
        ))


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description="Cartola FC 2026 - Sistema Inteligente de Escalação"
    )
    
    subparsers = parser.add_subparsers(dest="comando", help="Comandos disponíveis")
    
    # status
    subparsers.add_parser("status", help="Status do mercado")
    
    # mercado
    parser_mercado = subparsers.add_parser("mercado", help="Lista atletas do mercado")
    parser_mercado.add_argument("-p", "--posicao", help="Filtrar por posição")
    parser_mercado.add_argument("-m", "--max", type=float, help="Preço máximo")
    parser_mercado.add_argument("-l", "--limite", type=int, default=20)
    
    # confrontos - NOVO v3
    subparsers.add_parser("confrontos", help="Análise de confrontos da rodada")
    
    # escalar
    parser_escalar = subparsers.add_parser("escalar", help="Gera times otimizados")
    parser_escalar.add_argument("-e", "--esquema", default="4-4-2")
    parser_escalar.add_argument("-m", "--max", type=float, default=12.0)
    
    # coletar
    parser_coletar = subparsers.add_parser("coletar", help="Coleta scouts")
    parser_coletar.add_argument("-r", "--rodada", type=int)
    
    # sync
    subparsers.add_parser("sync", help="Sincroniza dados")
    
    # valorizadores
    parser_valor = subparsers.add_parser("valorizadores", help="Lista valorizadores")
    parser_valor.add_argument("-m", "--max", type=float, default=10.0)
    parser_valor.add_argument("-l", "--limite", type=int, default=20)
    
    # historico
    parser_hist = subparsers.add_parser("historico", help="Histórico de escalações")
    parser_hist.add_argument("-r", "--rodada", type=int)
    
    # patrimonio
    subparsers.add_parser("patrimonio", help="Evolução do patrimônio")
    
    # resultado
    parser_resultado = subparsers.add_parser("resultado", help="Registra resultado da rodada")
    parser_resultado.add_argument("-r", "--rodada", type=int)
    
    # salvar
    parser_salvar = subparsers.add_parser("salvar", help="Salva escalação com cartoletas atuais")
    parser_salvar.add_argument("-e", "--esquema", default="4-4-2")
    
    args = parser.parse_args()
    
    app = CartolaApp()
    
    if args.comando == "status":
        app.cmd_status()
    elif args.comando == "mercado":
        app.cmd_mercado(
            posicao=args.posicao,
            preco_max=args.max,
            limite=args.limite
        )
    elif args.comando == "confrontos":
        app.cmd_confrontos()
    elif args.comando == "escalar":
        app.cmd_escalar(esquema=args.esquema, preco_max=args.max)
    elif args.comando == "coletar":
        app.cmd_coletar(args.rodada)
    elif args.comando == "sync":
        app.cmd_sincronizar()
    elif args.comando == "valorizadores":
        app.cmd_valorizadores(preco_max=args.max, limite=args.limite)
    elif args.comando == "historico":
        app.cmd_historico(args.rodada)
    elif args.comando == "patrimonio":
        app.cmd_patrimonio()
    elif args.comando == "resultado":
        app.cmd_registrar_resultado(args.rodada)
    elif args.comando == "salvar":
        app.cmd_salvar_escalacao(args.esquema)
    else:
        # Modo interativo
        app.run_interativo()


if __name__ == "__main__":
    main()
