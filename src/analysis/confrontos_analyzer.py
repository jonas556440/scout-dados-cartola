"""
Analisador de Confrontos Detalhado - Cartola FC 2026

Este módulo oferece análise detalhada de confrontos para ajudar
na tomada de decisão. Mostra:

1. Melhores times para escalar (confrontos favoráveis)
2. Times para evitar (confrontos difíceis)
3. Análise por posição (onde investir)
4. Probabilidade de SG (saldo de gols)
5. Expectativa de gols por jogo

Como os sites especializados fazem:
- Cartola PFC
- Gato Mestre
- ge.globo.com/cartola
"""
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from src.analysis.match_analyzer import MatchAnalyzer, Confronto, EstatisticasTime


@dataclass
class ResumoTime:
    """Resumo de um time para a rodada"""
    clube_id: int
    nome: str
    abreviacao: str
    adversario: str
    local: str  # "CASA" ou "FORA"
    dificuldade: str
    dificuldade_score: float
    chance_sg: float
    expectativa_gols: float
    recomendacao: str  # "ESCALAR", "EVITAR", "NEUTRO"
    score_geral: float  # 0-100


class ConfrontosAnalyzer:
    """
    Analisador detalhado de confrontos para uma rodada
    
    Uso:
        analyzer = ConfrontosAnalyzer()
        analyzer.analisar_rodada(partidas, clubes)
        
        # Melhores times para atacantes
        melhores_ata = analyzer.get_melhores_para_posicao("ATA")
        
        # Melhores times para defensores (SG)
        melhores_def = analyzer.get_melhores_para_sg()
        
        # Times para evitar
        evitar = analyzer.get_times_para_evitar()
    """
    
    def __init__(self):
        self.match_analyzer = MatchAnalyzer()
        self.confrontos: List[Confronto] = []
        self.resumos: List[ResumoTime] = []
        self.clubes: Dict[str, Any] = {}
    
    def analisar_rodada(
        self, 
        partidas: List[Dict], 
        clubes: Dict[str, Any]
    ) -> List[ResumoTime]:
        """
        Analisa todos os confrontos de uma rodada
        
        Args:
            partidas: Lista de partidas da API
            clubes: Dict de clubes da API
            
        Returns:
            Lista de resumos ordenada por score
        """
        self.clubes = clubes
        
        # Inicializar estatísticas COM DADOS REAIS das partidas
        # IMPORTANTE: Passa partidas para usar posição e aproveitamento reais
        self.match_analyzer.carregar_estatisticas_times(clubes, partidas)
        self.confrontos = self.match_analyzer.analisar_partidas_rodada(partidas, clubes)
        
        # Gerar resumos para cada time
        self.resumos = []
        
        for confronto in self.confrontos:
            # Resumo do mandante
            mandante_resumo = self._criar_resumo_time(confronto, is_mandante=True)
            self.resumos.append(mandante_resumo)
            
            # Resumo do visitante
            visitante_resumo = self._criar_resumo_time(confronto, is_mandante=False)
            self.resumos.append(visitante_resumo)
        
        # Ordenar por score geral
        self.resumos.sort(key=lambda x: x.score_geral, reverse=True)
        
        return self.resumos
    
    def _criar_resumo_time(self, confronto: Confronto, is_mandante: bool) -> ResumoTime:
        """Cria resumo de um time baseado no confronto"""
        if is_mandante:
            clube_id = confronto.clube_mandante_id
            nome = confronto.mandante_nome
            abrev = confronto.mandante_abrev
            adversario = confronto.visitante_abrev
            local = "CASA"
            dificuldade_score = confronto.dificuldade_mandante
            chance_sg = confronto.chance_sg_mandante
            expectativa_gols = confronto.expectativa_gols_mandante
        else:
            clube_id = confronto.clube_visitante_id
            nome = confronto.visitante_nome
            abrev = confronto.visitante_abrev
            adversario = confronto.mandante_abrev
            local = "FORA"
            dificuldade_score = confronto.dificuldade_visitante
            chance_sg = confronto.chance_sg_visitante
            expectativa_gols = confronto.expectativa_gols_visitante
        
        # Classificar dificuldade
        if dificuldade_score < 40:
            dificuldade = "FÁCIL"
        elif dificuldade_score < 60:
            dificuldade = "MÉDIO"
        elif dificuldade_score < 75:
            dificuldade = "DIFÍCIL"
        else:
            dificuldade = "MUITO DIFÍCIL"
        
        # Calcular score geral (0-100)
        # Combina: dificuldade baixa + chance de gols + mando
        score_geral = 100 - dificuldade_score  # Inversão (fácil = alto score)
        score_geral += expectativa_gols * 10  # Bônus por gols esperados
        if local == "CASA":
            score_geral += 15  # Bônus mando
        score_geral = min(100, max(0, score_geral))
        
        # Determinar recomendação
        if score_geral >= 70:
            recomendacao = "ESCALAR"
        elif score_geral >= 40:
            recomendacao = "NEUTRO"
        else:
            recomendacao = "EVITAR"
        
        return ResumoTime(
            clube_id=clube_id,
            nome=nome,
            abreviacao=abrev,
            adversario=adversario,
            local=local,
            dificuldade=dificuldade,
            dificuldade_score=dificuldade_score,
            chance_sg=chance_sg,
            expectativa_gols=expectativa_gols,
            recomendacao=recomendacao,
            score_geral=score_geral
        )
    
    def get_melhores_para_posicao(self, posicao: str, top_n: int = 5) -> List[ResumoTime]:
        """
        Retorna os melhores times para escalar jogadores de uma posição
        
        Args:
            posicao: "GOL", "ZAG", "LAT", "MEI", "ATA"
            top_n: Quantidade a retornar
            
        Returns:
            Lista dos melhores times
        """
        if posicao in ["GOL", "ZAG", "LAT"]:
            # Para defensores: priorizar SG
            ordenados = sorted(self.resumos, key=lambda x: x.chance_sg, reverse=True)
        elif posicao in ["MEI", "ATA"]:
            # Para ofensivos: priorizar expectativa de gols + confronto fácil
            ordenados = sorted(
                self.resumos, 
                key=lambda x: (x.expectativa_gols * 30) + (100 - x.dificuldade_score),
                reverse=True
            )
        else:
            # TEC: usar score geral
            ordenados = sorted(self.resumos, key=lambda x: x.score_geral, reverse=True)
        
        return ordenados[:top_n]
    
    def get_melhores_para_sg(self, top_n: int = 5) -> List[ResumoTime]:
        """Retorna times com maior chance de não sofrer gols"""
        ordenados = sorted(self.resumos, key=lambda x: x.chance_sg, reverse=True)
        return ordenados[:top_n]
    
    def get_melhores_para_gols(self, top_n: int = 5) -> List[ResumoTime]:
        """Retorna times com maior expectativa de marcar gols"""
        ordenados = sorted(self.resumos, key=lambda x: x.expectativa_gols, reverse=True)
        return ordenados[:top_n]
    
    def get_times_para_evitar(self, top_n: int = 5) -> List[ResumoTime]:
        """Retorna times com confrontos muito difíceis"""
        evitar = [r for r in self.resumos if r.recomendacao == "EVITAR"]
        return evitar[:top_n]
    
    def get_times_para_escalar(self, top_n: int = 10) -> List[ResumoTime]:
        """Retorna times com confrontos favoráveis"""
        escalar = [r for r in self.resumos if r.recomendacao == "ESCALAR"]
        return escalar[:top_n]
    
    def get_resumo_time(self, clube_id: int) -> ResumoTime:
        """Busca resumo de um time específico"""
        for resumo in self.resumos:
            if resumo.clube_id == clube_id:
                return resumo
        return None
    
    def formatar_relatorio(self) -> str:
        """Gera relatório completo de confrontos"""
        linhas = []
        
        linhas.append("\n" + "=" * 70)
        linhas.append("📊 ANÁLISE COMPLETA DE CONFRONTOS DA RODADA")
        linhas.append("=" * 70)
        
        # Times para escalar
        escalar = self.get_times_para_escalar(10)
        if escalar:
            linhas.append("\n🟢 TIMES PARA ESCALAR (confrontos favoráveis):")
            linhas.append("-" * 70)
            for i, r in enumerate(escalar, 1):
                local = "🏠" if r.local == "CASA" else "✈️"
                linhas.append(
                    f"  {i}. {r.abreviacao} {local} vs {r.adversario} | "
                    f"SG: {r.chance_sg:.0f}% | Gols: {r.expectativa_gols:.1f} | "
                    f"Score: {r.score_geral:.0f}"
                )
        
        # Times para evitar
        evitar = self.get_times_para_evitar(5)
        if evitar:
            linhas.append("\n🔴 TIMES PARA EVITAR (confrontos difíceis):")
            linhas.append("-" * 70)
            for r in evitar:
                local = "🏠" if r.local == "CASA" else "✈️"
                linhas.append(
                    f"  ⚠️ {r.abreviacao} {local} vs {r.adversario} | "
                    f"Dificuldade: {r.dificuldade} | Score: {r.score_geral:.0f}"
                )
        
        # Melhores para SG
        sg = self.get_melhores_para_sg(5)
        if sg:
            linhas.append("\n🛡️ MELHORES PARA SG (defensores):")
            linhas.append("-" * 70)
            for r in sg:
                local = "🏠" if r.local == "CASA" else "✈️"
                linhas.append(
                    f"  • {r.abreviacao} {local} vs {r.adversario} | "
                    f"Chance SG: {r.chance_sg:.0f}%"
                )
        
        # Melhores para gols
        gols = self.get_melhores_para_gols(5)
        if gols:
            linhas.append("\n⚽ MELHORES PARA GOLS (atacantes/meias):")
            linhas.append("-" * 70)
            for r in gols:
                local = "🏠" if r.local == "CASA" else "✈️"
                linhas.append(
                    f"  • {r.abreviacao} {local} vs {r.adversario} | "
                    f"Expectativa: {r.expectativa_gols:.1f} gols"
                )
        
        linhas.append("")
        linhas.append("=" * 70)
        linhas.append("💡 DICAS:")
        linhas.append("  • Priorize jogadores de times com confrontos FÁCEIS")
        linhas.append("  • Para SG: busque goleiros/zagueiros de times com alta chance")
        linhas.append("  • Para gols: busque atacantes de times com alta expectativa")
        linhas.append("  • Jogos em casa (🏠) tendem a render mais pontos")
        linhas.append("=" * 70)
        
        return "\n".join(linhas)


# Instância global
confrontos_analyzer = ConfrontosAnalyzer()
