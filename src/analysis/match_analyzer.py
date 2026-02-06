"""
Analisador de Confrontos - Cartola FC 2026

Análise completa considerando:
1. Adversário da rodada (força ofensiva/defensiva)
2. Mando de campo (casa vs fora)
3. Forma recente do time (últimos 5 jogos)
4. Histórico de confrontos diretos
5. Estatísticas do campeonato

Este é o módulo que faltava para fazer seleção inteligente como os sites especializados!
"""
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict

sys.path.append(str(Path(__file__).parent.parent.parent))

from config.settings import settings


@dataclass
class EstatisticasTime:
    """Estatísticas de um time no campeonato"""
    clube_id: int
    nome: str
    abreviacao: str
    
    # Posição e pontos
    posicao: int = 0
    pontos: int = 0
    jogos: int = 0
    
    # Resultados
    vitorias: int = 0
    empates: int = 0
    derrotas: int = 0
    
    # Gols
    gols_pro: int = 0
    gols_contra: int = 0
    saldo_gols: int = 0
    
    # Casa vs Fora
    vitorias_casa: int = 0
    vitorias_fora: int = 0
    gols_casa: int = 0
    gols_fora: int = 0
    gols_sofridos_casa: int = 0
    gols_sofridos_fora: int = 0
    
    # Forma (últimos 5 jogos: V=3, E=1, D=0)
    forma_pontos: int = 0  # 0-15
    forma_sequencia: str = ""  # Ex: "VVEVD"
    
    # Métricas calculadas
    media_gols_pro: float = 0.0
    media_gols_contra: float = 0.0
    aproveitamento: float = 0.0
    forca_ataque: float = 0.0  # 0-100
    forca_defesa: float = 0.0  # 0-100
    forca_geral: float = 0.0   # 0-100
    
    def calcular_metricas(self):
        """Calcula métricas derivadas"""
        if self.jogos > 0:
            self.media_gols_pro = self.gols_pro / self.jogos
            self.media_gols_contra = self.gols_contra / self.jogos
            pontos_possiveis = self.jogos * 3
            self.aproveitamento = (self.pontos / pontos_possiveis * 100) if pontos_possiveis > 0 else 0
            
            # Força de ataque (0-100): baseada em gols marcados
            # Liga média = ~1.2 gols/jogo, excelente = 2+
            self.forca_ataque = min(100, (self.media_gols_pro / 2.0) * 100)
            
            # Força de defesa (0-100): baseada em gols sofridos
            # Invertido: menos gols = mais força
            # Liga média = ~1.2 gols/jogo, excelente = 0.5
            if self.media_gols_contra <= 0.5:
                self.forca_defesa = 100
            elif self.media_gols_contra >= 2.0:
                self.forca_defesa = 0
            else:
                self.forca_defesa = 100 - ((self.media_gols_contra - 0.5) / 1.5 * 100)
            
            # Força geral
            self.forca_geral = (self.forca_ataque + self.forca_defesa) / 2


@dataclass
class Confronto:
    """Informações de um confronto específico"""
    partida_id: int
    rodada: int
    
    # Times
    clube_mandante_id: int
    clube_visitante_id: int
    mandante_nome: str
    visitante_nome: str
    mandante_abrev: str
    visitante_abrev: str
    
    # Estatísticas dos times
    mandante_stats: Optional[EstatisticasTime] = None
    visitante_stats: Optional[EstatisticasTime] = None
    
    # Análise
    favorito: str = "neutro"  # "mandante", "visitante", "neutro"
    prob_vitoria_mandante: float = 0.0
    prob_empate: float = 0.0
    prob_vitoria_visitante: float = 0.0
    
    # Expectativa de gols
    expectativa_gols_mandante: float = 0.0
    expectativa_gols_visitante: float = 0.0
    
    # Chance de SG (saldo de gols = não sofrer gol)
    chance_sg_mandante: float = 0.0
    chance_sg_visitante: float = 0.0
    
    # Score de dificuldade (0-100, maior = mais difícil)
    dificuldade_mandante: float = 0.0  # Dificuldade para o mandante
    dificuldade_visitante: float = 0.0  # Dificuldade para o visitante


class MatchAnalyzer:
    """
    Analisador de confrontos e força dos times
    
    Usa dados reais das partidas para calcular:
    - Força ofensiva/defensiva de cada time
    - Dificuldade de cada confronto
    - Probabilidades de vitória/empate/derrota
    - Chances de SG (clean sheet)
    """
    
    # Fatores de ajuste
    VANTAGEM_CASA = 1.3  # Multiplicador para time da casa
    PESO_FORMA_RECENTE = 0.4  # Peso da forma recente vs histórico
    
    def __init__(self):
        self.estatisticas_times: Dict[int, EstatisticasTime] = {}
        self.confrontos_rodada: Dict[int, List[Confronto]] = {}
        self.resultados_anteriores: List[Dict] = []
    
    def carregar_estatisticas_times(
        self, 
        clubes: Dict[str, Any],
        partidas: List[Dict] = None
    ) -> Dict[int, EstatisticasTime]:
        """
        Inicializa estatísticas dos times usando dados REAIS da API
        
        Prioridade:
        1. Posição real no campeonato (clube_casa_posicao/clube_visitante_posicao)
        2. Aproveitamento últimos 5 jogos (aproveitamento_mandante/visitante)
        3. Ranking histórico PONDERADO com posição atual
        
        IMPORTANTE: No início do campeonato (rodadas 1-10), usamos mais o ranking
        histórico. Conforme o campeonato avança, a classificação atual ganha mais peso.
        """
        # Ranking histórico baseado em estrutura, elenco e tradição
        # ATUALIZADO para o Brasileirão 2026
        RANKING_HISTORICO = {
            # Top 6 - Grandes do Brasil (elencos caros, estrutura)
            "FLA": 95, "PAL": 93, "BOT": 90, "INT": 85, "CAM": 83, "FLU": 82,
            # Grandes tradicionais
            "SAO": 80, "COR": 78, "GRE": 76, "CRU": 74, "SAN": 72,
            # Série A estabelecidos
            "BAH": 70, "VAS": 68, "RBB": 66, "CAP": 64, "VIT": 55,
            # Recém-promovidos / menor estrutura
            "MIR": 52,  # Campeão Série B - time organizado mas menor
            "CFC": 50,  # Coritiba
            "CHA": 48,  # Chapecoense
            "REM": 40,  # Remo - recém-promovido, menor estrutura
        }
        
        estatisticas = {}
        
        # Extrair posições reais das partidas
        posicoes_reais = {}
        aproveitamentos = {}
        jogos_disputados = 0  # Para calcular peso do ranking histórico
        
        if partidas:
            for p in partidas:
                casa_id = p.get("clube_casa_id")
                visit_id = p.get("clube_visitante_id")
                
                if casa_id and p.get("clube_casa_posicao"):
                    posicoes_reais[casa_id] = p.get("clube_casa_posicao")
                if visit_id and p.get("clube_visitante_posicao"):
                    posicoes_reais[visit_id] = p.get("clube_visitante_posicao")
                
                # Aproveitamento últimos 5 jogos (array de "v", "e", "d")
                if casa_id and p.get("aproveitamento_mandante"):
                    aprov = p.get("aproveitamento_mandante", [])
                    aproveitamentos[casa_id] = aprov
                    # Contar jogos disputados (entradas não vazias)
                    jogos = sum(1 for r in aprov if r)
                    jogos_disputados = max(jogos_disputados, jogos)
                if visit_id and p.get("aproveitamento_visitante"):
                    aprov = p.get("aproveitamento_visitante", [])
                    aproveitamentos[visit_id] = aprov
                    jogos = sum(1 for r in aprov if r)
                    jogos_disputados = max(jogos_disputados, jogos)
        
        # Calcular peso do ranking histórico:
        # - Rodadas 1-5: 80% histórico, 20% posição atual
        # - Rodadas 6-15: diminui gradualmente
        # - Rodadas 16+: 30% histórico, 70% posição atual
        if jogos_disputados <= 5:
            peso_historico = 0.80
        elif jogos_disputados <= 15:
            # Diminui de 0.80 para 0.30 entre rodadas 6-15
            peso_historico = 0.80 - ((jogos_disputados - 5) * 0.05)
        else:
            peso_historico = 0.30
        
        peso_posicao = 1.0 - peso_historico
        
        for clube_id_str, clube_info in clubes.items():
            clube_id = int(clube_id_str)
            abrev = clube_info.get("abreviacao", "???")
            
            # 1. Força do RANKING HISTÓRICO
            forca_historico = RANKING_HISTORICO.get(abrev, 50)
            
            # 2. Força da POSIÇÃO ATUAL
            posicao = posicoes_reais.get(clube_id)
            if posicao:
                # Posição 1 = 100, posição 20 = 30
                forca_posicao = max(30, 100 - (posicao - 1) * 3.5)
            else:
                forca_posicao = forca_historico  # Fallback para histórico
            
            # 3. Força PONDERADA (ranking histórico + posição atual)
            forca_base = (forca_historico * peso_historico) + (forca_posicao * peso_posicao)
            
            # 4. Bônus de FORMA RECENTE (últimos 5 jogos) - até ±10 pontos
            aprov = aproveitamentos.get(clube_id, [])
            vitorias = sum(1 for r in aprov if r and r.lower() == 'v')
            empates = sum(1 for r in aprov if r and r.lower() == 'e')
            derrotas = sum(1 for r in aprov if r and r.lower() == 'd')
            
            # Cada vitória +2, empate 0, derrota -2 (máx ±10)
            forma_bonus = (vitorias * 2) - (derrotas * 2)
            forma_bonus = max(-10, min(10, forma_bonus))
            
            # 5. Força final = base + forma
            forca_final = min(100, max(20, forca_base + forma_bonus))
            
            # Calcular jogos totais a partir do aproveitamento
            jogos_totais = vitorias + empates + derrotas
            pontos_totais = (vitorias * 3) + empates
            
            # Estimar gols baseado na força do time e resultados
            # Times fortes marcam mais gols, times fracos sofrem mais
            gols_estimados_pro = 0
            gols_estimados_contra = 0
            
            if jogos_totais > 0:
                # Estimativa simples: vitória = ~2 gols pró, derrota = ~1 gol pró e ~2 contra
                gols_estimados_pro = (vitorias * 2) + empates + (derrotas * 1)
                gols_estimados_contra = (derrotas * 2) + empates + (vitorias * 0.5)
                gols_estimados_pro = int(gols_estimados_pro)
                gols_estimados_contra = int(gols_estimados_contra)
            
            stats = EstatisticasTime(
                clube_id=clube_id,
                nome=clube_info.get("nome", ""),
                abreviacao=abrev,
                posicao=posicao or 0,
                jogos=jogos_totais,
                vitorias=vitorias,
                empates=empates,
                derrotas=derrotas,
                pontos=pontos_totais,
                gols_pro=gols_estimados_pro,
                gols_contra=gols_estimados_contra,
                saldo_gols=gols_estimados_pro - gols_estimados_contra,
                forca_ataque=forca_final,
                forca_defesa=forca_final,
                forca_geral=forca_final,
                # Salvar forma
                forma_pontos=forma_bonus,
                forma_sequencia="".join([r.upper() for r in aprov if r]),
            )
            
            estatisticas[clube_id] = stats
        
        self.estatisticas_times = estatisticas
        return estatisticas
    
    def atualizar_com_resultados(self, partidas: List[Dict]):
        """
        Atualiza estatísticas com resultados reais das partidas
        """
        for partida in partidas:
            mandante_id = partida.get("clube_mandante_id")
            visitante_id = partida.get("clube_visitante_id")
            gols_mandante = partida.get("placar_oficial_mandante")
            gols_visitante = partida.get("placar_oficial_visitante")
            
            if gols_mandante is None or gols_visitante is None:
                continue  # Partida ainda não realizada
            
            # Atualizar mandante
            if mandante_id in self.estatisticas_times:
                stats = self.estatisticas_times[mandante_id]
                stats.jogos += 1
                stats.gols_pro += gols_mandante
                stats.gols_contra += gols_visitante
                stats.gols_casa += gols_mandante
                stats.gols_sofridos_casa += gols_visitante
                
                if gols_mandante > gols_visitante:
                    stats.vitorias += 1
                    stats.vitorias_casa += 1
                    stats.pontos += 3
                elif gols_mandante == gols_visitante:
                    stats.empates += 1
                    stats.pontos += 1
                else:
                    stats.derrotas += 1
                
                stats.saldo_gols = stats.gols_pro - stats.gols_contra
                stats.calcular_metricas()
            
            # Atualizar visitante
            if visitante_id in self.estatisticas_times:
                stats = self.estatisticas_times[visitante_id]
                stats.jogos += 1
                stats.gols_pro += gols_visitante
                stats.gols_contra += gols_mandante
                stats.gols_fora += gols_visitante
                stats.gols_sofridos_fora += gols_mandante
                
                if gols_visitante > gols_mandante:
                    stats.vitorias += 1
                    stats.vitorias_fora += 1
                    stats.pontos += 3
                elif gols_visitante == gols_mandante:
                    stats.empates += 1
                    stats.pontos += 1
                else:
                    stats.derrotas += 1
                
                stats.saldo_gols = stats.gols_pro - stats.gols_contra
                stats.calcular_metricas()
    
    def analisar_partidas_rodada(
        self, 
        partidas: List[Dict],
        clubes: Dict[str, Any]
    ) -> List[Confronto]:
        """
        Analisa todas as partidas de uma rodada
        
        Args:
            partidas: Lista de partidas da API
            clubes: Dict de clubes da API
            
        Returns:
            Lista de Confrontos analisados
        """
        # Garantir que temos estatísticas dos times COM DADOS REAIS DA API
        if not self.estatisticas_times:
            self.carregar_estatisticas_times(clubes, partidas)
        
        confrontos = []
        
        for partida in partidas:
            mandante_id = partida.get("clube_casa_id") or partida.get("clube_mandante_id")
            visitante_id = partida.get("clube_visitante_id")
            
            if not mandante_id or not visitante_id:
                continue
            
            mandante_info = clubes.get(str(mandante_id), {})
            visitante_info = clubes.get(str(visitante_id), {})
            
            confronto = Confronto(
                partida_id=partida.get("partida_id", 0),
                rodada=partida.get("rodada", 0),
                clube_mandante_id=mandante_id,
                clube_visitante_id=visitante_id,
                mandante_nome=mandante_info.get("nome", ""),
                visitante_nome=visitante_info.get("nome", ""),
                mandante_abrev=mandante_info.get("abreviacao", "???"),
                visitante_abrev=visitante_info.get("abreviacao", "???"),
                mandante_stats=self.estatisticas_times.get(mandante_id),
                visitante_stats=self.estatisticas_times.get(visitante_id),
            )
            
            # Calcular análise do confronto
            self._analisar_confronto(confronto)
            
            confrontos.append(confronto)
        
        return confrontos
    
    def _analisar_confronto(self, confronto: Confronto):
        """
        Calcula probabilidades e expectativas para um confronto
        """
        mandante_stats = confronto.mandante_stats
        visitante_stats = confronto.visitante_stats
        
        if not mandante_stats or not visitante_stats:
            # Sem dados, assume neutro com leve vantagem casa
            confronto.prob_vitoria_mandante = 0.40
            confronto.prob_empate = 0.28
            confronto.prob_vitoria_visitante = 0.32
            confronto.favorito = "neutro"
            confronto.dificuldade_mandante = 50
            confronto.dificuldade_visitante = 50
            return
        
        # Força base dos times
        forca_mandante = mandante_stats.forca_geral
        forca_visitante = visitante_stats.forca_geral
        
        # Diferença de força (positivo = mandante mais forte)
        diff_forca = forca_mandante - forca_visitante
        
        # Vantagem de jogar em casa: ~15% (estudos mostram 10-20% no Brasil)
        # Mas essa vantagem diminui se o visitante for MUITO mais forte
        vantagem_casa = 12  # Pontos de bônus para mandante
        
        # Se visitante for muito mais forte, reduz vantagem de casa
        if diff_forca < -20:
            vantagem_casa = 5  # Time muito inferior, pouca vantagem
        elif diff_forca < -10:
            vantagem_casa = 8
        elif diff_forca > 20:
            vantagem_casa = 15  # Mandante muito superior, maximiza vantagem
        
        # Força ajustada
        forca_mandante_adj = forca_mandante + vantagem_casa
        forca_visitante_adj = forca_visitante
        
        total = forca_mandante_adj + forca_visitante_adj
        
        # Probabilidades básicas
        if total > 0:
            prob_m = forca_mandante_adj / total
            prob_v = forca_visitante_adj / total
        else:
            prob_m = 0.5
            prob_v = 0.5
        
        # Ajustar para incluir empate
        # Empate mais provável quando times são equilibrados
        diff_prob = abs(prob_m - prob_v)
        if diff_prob < 0.1:
            prob_empate = 0.30  # Times muito equilibrados
        elif diff_prob < 0.2:
            prob_empate = 0.27
        else:
            prob_empate = 0.23  # Grande diferença, menos chance empate
        
        confronto.prob_empate = prob_empate
        confronto.prob_vitoria_mandante = prob_m * (1 - prob_empate)
        confronto.prob_vitoria_visitante = prob_v * (1 - prob_empate)
        
        # Normalizar
        soma = confronto.prob_vitoria_mandante + confronto.prob_empate + confronto.prob_vitoria_visitante
        if soma > 0:
            confronto.prob_vitoria_mandante /= soma
            confronto.prob_empate /= soma
            confronto.prob_vitoria_visitante /= soma
        
        # Determinar favorito (considerar margem de erro)
        if confronto.prob_vitoria_mandante > confronto.prob_vitoria_visitante + 0.08:
            confronto.favorito = "mandante"
        elif confronto.prob_vitoria_visitante > confronto.prob_vitoria_mandante + 0.05:
            confronto.favorito = "visitante"
        else:
            confronto.favorito = "neutro"
        
        # Expectativa de gols (mais realista)
        # Média Brasileirão: ~2.5 gols por jogo
        media_gols_jogo = 2.5
        
        # Proporção de gols baseada na força
        prop_mandante = forca_mandante_adj / total if total > 0 else 0.5
        
        confronto.expectativa_gols_mandante = media_gols_jogo * prop_mandante * 1.1  # Leve vantagem casa
        confronto.expectativa_gols_visitante = media_gols_jogo * (1 - prop_mandante) * 0.9
        
        # Chance de SG (clean sheet)
        # Baseado na força defensiva e expectativa de gols do adversário
        confronto.chance_sg_mandante = max(0, min(100, 
            100 - confronto.expectativa_gols_visitante * 40
        ))
        confronto.chance_sg_visitante = max(0, min(100,
            100 - confronto.expectativa_gols_mandante * 35  # Mais difícil manter SG fora
        ))
        
        # Dificuldade do confronto
        # Para o mandante: baseado na força do visitante
        confronto.dificuldade_mandante = visitante_stats.forca_geral
        # Para o visitante: força do mandante + vantagem casa
        confronto.dificuldade_visitante = min(100, mandante_stats.forca_geral * self.VANTAGEM_CASA)
    
    def get_confronto_por_clube(
        self, 
        clube_id: int, 
        confrontos: List[Confronto]
    ) -> Optional[Tuple[Confronto, bool]]:
        """
        Retorna o confronto de um clube e se joga em casa
        
        Args:
            clube_id: ID do clube
            confrontos: Lista de confrontos
            
        Returns:
            Tuple (Confronto, is_mandante) ou None
        """
        for confronto in confrontos:
            if confronto.clube_mandante_id == clube_id:
                return (confronto, True)
            elif confronto.clube_visitante_id == clube_id:
                return (confronto, False)
        return None
    
    def calcular_bonus_confronto(
        self,
        clube_id: int,
        confrontos: List[Confronto],
        posicao: str
    ) -> float:
        """
        Calcula bônus/penalidade baseado no confronto
        
        Args:
            clube_id: ID do clube do jogador
            confrontos: Lista de confrontos da rodada
            posicao: Posição do jogador (GOL, ZAG, LAT, MEI, ATA)
            
        Returns:
            Multiplicador (1.0 = neutro, >1 = bom, <1 = ruim)
        """
        resultado = self.get_confronto_por_clube(clube_id, confrontos)
        
        if not resultado:
            return 1.0
        
        confronto, is_mandante = resultado
        
        bonus = 1.0
        
        # Bônus por mando de campo (MAIOR IMPACTO v3)
        if is_mandante:
            bonus *= 1.15  # 15% de bônus para mandante
        else:
            bonus *= 0.90  # 10% de penalidade para visitante
        
        # Pegar dificuldade e chance de gols
        if is_mandante:
            dificuldade = confronto.dificuldade_mandante
            expect_gols = confronto.expectativa_gols_mandante
            chance_sg = confronto.chance_sg_mandante
        else:
            dificuldade = confronto.dificuldade_visitante
            expect_gols = confronto.expectativa_gols_visitante
            chance_sg = confronto.chance_sg_visitante
        
        # Ajustar por posição (MAIOR IMPACTO v3)
        if posicao in ["GOL", "ZAG", "LAT"]:
            # Defensores: bônus/penalidade maior por chance de SG
            if chance_sg > 70:
                bonus *= 1.20  # Excelente chance de SG
            elif chance_sg > 50:
                bonus *= 1.10
            elif chance_sg < 40:
                bonus *= 0.80  # Alta chance de sofrer gol
            elif chance_sg < 30:
                bonus *= 0.70  # Muito alta chance de sofrer gol
        
        elif posicao in ["MEI", "ATA"]:
            # Ofensivos: bônus maior por expectativa de gols
            if expect_gols > 1.5:
                bonus *= 1.20  # Excelente para atacar
            elif expect_gols > 1.0:
                bonus *= 1.10
            elif expect_gols < 0.7:
                bonus *= 0.80  # Difícil marcar gol
            elif expect_gols < 0.5:
                bonus *= 0.70  # Muito difícil marcar gol
        
        # Ajustar por dificuldade geral (MAIOR IMPACTO v3)
        # Confronto fácil (dificuldade < 45) = bônus grande
        # Confronto difícil (dificuldade > 65) = penalidade grande
        if dificuldade < 45:
            bonus *= 1.20  # Confronto muito fácil
        elif dificuldade < 60:
            bonus *= 1.10  # Confronto fácil
        elif dificuldade > 75:
            bonus *= 0.70  # Confronto muito difícil
        elif dificuldade > 65:
            bonus *= 0.80  # Confronto difícil
        
        return round(bonus, 2)
    
    def get_resumo_confronto(self, clube_id: int, confrontos: List[Confronto]) -> Dict[str, Any]:
        """
        Retorna resumo do confronto para exibição
        """
        resultado = self.get_confronto_por_clube(clube_id, confrontos)
        
        if not resultado:
            return {"erro": "Confronto não encontrado"}
        
        confronto, is_mandante = resultado
        
        if is_mandante:
            adversario = confronto.visitante_abrev
            local = "CASA"
            dificuldade = confronto.dificuldade_mandante
            chance_sg = confronto.chance_sg_mandante
            expect_gols = confronto.expectativa_gols_mandante
        else:
            adversario = confronto.mandante_abrev
            local = "FORA"
            dificuldade = confronto.dificuldade_visitante
            chance_sg = confronto.chance_sg_visitante
            expect_gols = confronto.expectativa_gols_visitante
        
        # Classificar dificuldade
        if dificuldade < 45:
            dificuldade_texto = "FÁCIL"
        elif dificuldade < 60:
            dificuldade_texto = "MÉDIO"
        elif dificuldade < 75:
            dificuldade_texto = "DIFÍCIL"
        else:
            dificuldade_texto = "MUITO DIFÍCIL"
        
        return {
            "adversario": adversario,
            "local": local,
            "dificuldade": dificuldade_texto,
            "dificuldade_score": dificuldade,
            "chance_sg": round(chance_sg, 1),
            "expectativa_gols": round(expect_gols, 2),
            "favorito": confronto.favorito,
        }


# Instância global
match_analyzer = MatchAnalyzer()
