"""
Statistics Provider - Provedor de Estatísticas Externas
Cartola FC 2026

Fontes de dados:
1. API Cartola FC (oficial) - scouts, médias, preços
2. FBref (via soccerdata) - xG, xA, estatísticas avançadas
3. Sofascore (via soccerdata) - ratings, form
4. Transfermarkt - valor de mercado real
5. Football-Data - odds e probabilidades

O objetivo é usar ESTATÍSTICAS REAIS para prever desempenho,
não apenas preço como proxy.
"""
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging

sys.path.append(str(Path(__file__).parent.parent.parent))

from config.settings import settings

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EstatisticasJogador:
    """Estatísticas consolidadas de um jogador de múltiplas fontes"""
    atleta_id: int
    nome: str
    posicao: str
    clube: str
    
    # Dados Cartola
    preco: float = 0.0
    media_cartola: float = 0.0
    jogos: int = 0
    pontos_total: float = 0.0
    variacao_preco: float = 0.0
    
    # Estatísticas avançadas (xG, xA, etc.)
    xg: float = 0.0                    # Expected Goals
    xa: float = 0.0                    # Expected Assists
    xg_per_90: float = 0.0             # xG por 90 minutos
    xa_per_90: float = 0.0             # xA por 90 minutos
    shots_per_90: float = 0.0          # Finalizações por 90 min
    key_passes_per_90: float = 0.0     # Passes decisivos
    
    # Estatísticas defensivas
    tackles_per_90: float = 0.0
    interceptions_per_90: float = 0.0
    blocks_per_90: float = 0.0
    duels_won_pct: float = 0.0         # % duelos ganhos
    
    # Goleiros
    saves_per_90: float = 0.0
    save_pct: float = 0.0
    clean_sheets: int = 0
    
    # Scores calculados (0-100)
    score_potencial: float = 0.0       # Potencial de pontuação
    score_forma: float = 0.0           # Forma atual
    score_custo_beneficio: float = 0.0 # Custo-benefício
    score_valorizacao: float = 0.0     # Potencial de valorização
    
    # Tendência
    tendencia: str = "estavel"         # 'subindo', 'estavel', 'caindo'
    tendencia_score: float = 0.0       # -1 a 1
    
    # Metadados
    fontes: List[str] = field(default_factory=list)
    ultima_atualizacao: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "atleta_id": self.atleta_id,
            "nome": self.nome,
            "posicao": self.posicao,
            "clube": self.clube,
            "preco": self.preco,
            "media_cartola": self.media_cartola,
            "xg": self.xg,
            "xa": self.xa,
            "score_potencial": self.score_potencial,
            "score_forma": self.score_forma,
            "score_custo_beneficio": self.score_custo_beneficio,
            "tendencia": self.tendencia,
        }


class StatisticsProvider:
    """
    Provedor central de estatísticas para seleção de times
    
    Combina dados de múltiplas fontes para criar um score
    de potencial real de cada jogador.
    """
    
    def __init__(self):
        self.cache_stats: Dict[int, EstatisticasJogador] = {}
        self.soccerdata_available = self._check_soccerdata()
    
    def _check_soccerdata(self) -> bool:
        """Verifica se soccerdata está disponível"""
        try:
            import soccerdata as sd
            return True
        except ImportError:
            logger.warning(
                "soccerdata não instalado. "
                "Instale com: pip install soccerdata"
            )
            return False
    
    # ==================== CARTOLA FC API ====================
    
    def get_estatisticas_cartola(
        self, 
        atletas: List[Dict[str, Any]],
        scouts_anteriores: Dict[int, List[Dict]] = None
    ) -> Dict[int, EstatisticasJogador]:
        """
        Extrai estatísticas dos dados da API do Cartola
        
        Args:
            atletas: Lista de atletas do mercado
            scouts_anteriores: Dict {atleta_id: [scouts das rodadas]}
            
        Returns:
            Dict {atleta_id: EstatisticasJogador}
        """
        stats = {}
        
        for atleta in atletas:
            atleta_id = atleta.get("atleta_id")
            
            stat = EstatisticasJogador(
                atleta_id=atleta_id,
                nome=atleta.get("apelido", ""),
                posicao=str(atleta.get("posicao_id", 0)),
                clube=str(atleta.get("clube_id", 0)),
                preco=atleta.get("preco_num", 0.0),
                media_cartola=atleta.get("media_num", 0.0),
                jogos=atleta.get("jogos_num", 0),
                pontos_total=atleta.get("pontos_num", 0.0),
                variacao_preco=atleta.get("variacao_num", 0.0),
            )
            
            # Calcular tendência de pontuação das últimas rodadas
            if scouts_anteriores and atleta_id in scouts_anteriores:
                scouts = scouts_anteriores[atleta_id]
                stat = self._calcular_tendencia_scouts(stat, scouts)
            
            stat.fontes.append("cartola_api")
            stats[atleta_id] = stat
        
        return stats
    
    def _calcular_tendencia_scouts(
        self, 
        stat: EstatisticasJogador, 
        scouts: List[Dict]
    ) -> EstatisticasJogador:
        """Calcula tendência baseada nos scouts anteriores"""
        if len(scouts) < 2:
            stat.tendencia = "estavel"
            stat.tendencia_score = 0.0
            return stat
        
        # Ordenar por rodada (mais recente primeiro)
        scouts_ordenados = sorted(scouts, key=lambda x: x.get("rodada", 0), reverse=True)
        
        # Pegar últimas 3-5 rodadas
        ultimos = scouts_ordenados[:5]
        
        pontuacoes = [s.get("pontuacao", 0) for s in ultimos if s.get("entrou_em_campo")]
        
        if len(pontuacoes) < 2:
            stat.tendencia = "estavel"
            stat.tendencia_score = 0.0
            return stat
        
        # Calcular tendência (pontuação recente vs média geral)
        media_recente = sum(pontuacoes[:3]) / min(3, len(pontuacoes))
        media_geral = stat.media_cartola if stat.media_cartola > 0 else sum(pontuacoes) / len(pontuacoes)
        
        if media_geral > 0:
            variacao_pct = (media_recente - media_geral) / media_geral
        else:
            variacao_pct = 0.0
        
        stat.tendencia_score = max(-1, min(1, variacao_pct))
        
        if variacao_pct > 0.15:
            stat.tendencia = "subindo"
        elif variacao_pct < -0.15:
            stat.tendencia = "caindo"
        else:
            stat.tendencia = "estavel"
        
        return stat
    
    # ==================== SOCCERDATA (FBREF, SOFASCORE) ====================
    
    def get_estatisticas_fbref(
        self, 
        temporada: str = "2026",
        liga: str = "BRA-Serie A"
    ) -> Dict[str, Dict[str, Any]]:
        """
        Busca estatísticas avançadas do FBref via soccerdata
        
        Args:
            temporada: Ano da temporada
            liga: Liga (BRA-Serie A)
            
        Returns:
            Dict {nome_jogador: estatisticas}
        """
        if not self.soccerdata_available:
            return {}
        
        try:
            import soccerdata as sd
            
            fbref = sd.FBref(liga, temporada)
            
            # Estatísticas padrão de jogadores
            player_stats = fbref.read_player_season_stats(stat_type="standard")
            
            # Estatísticas de chutes (xG)
            shooting_stats = fbref.read_player_season_stats(stat_type="shooting")
            
            # Estatísticas de passes (xA)
            passing_stats = fbref.read_player_season_stats(stat_type="passing")
            
            # Combinar em um dict por nome do jogador
            stats_por_jogador = {}
            
            for idx, row in player_stats.iterrows():
                nome = row.get("player", str(idx))
                stats_por_jogador[nome] = {
                    "minutos": row.get("minutes", 0),
                    "gols": row.get("goals", 0),
                    "assistencias": row.get("assists", 0),
                    "xg": row.get("xg", 0),
                    "xa": row.get("xa", 0),
                }
            
            logger.info(f"FBref: carregados {len(stats_por_jogador)} jogadores")
            
            return stats_por_jogador
            
        except Exception as e:
            logger.error(f"Erro ao buscar FBref: {e}")
            return {}
    
    # ==================== CÁLCULO DE SCORES ====================
    
    def calcular_scores(
        self, 
        estatisticas: Dict[int, EstatisticasJogador]
    ) -> Dict[int, EstatisticasJogador]:
        """
        Calcula os scores de potencial para cada jogador
        
        Scores (0-100):
        - score_potencial: Capacidade de fazer pontos
        - score_forma: Forma atual do jogador
        - score_custo_beneficio: Relação pontos/preço
        - score_valorizacao: Probabilidade de valorizar
        
        Args:
            estatisticas: Dict de estatísticas por atleta
            
        Returns:
            Dict atualizado com scores calculados
        """
        # Encontrar máximos para normalização
        max_media = max((s.media_cartola for s in estatisticas.values()), default=1)
        max_preco = max((s.preco for s in estatisticas.values()), default=1)
        
        for atleta_id, stat in estatisticas.items():
            # Score de Potencial (baseado em média, xG, xA)
            if stat.media_cartola > 0:
                base_potencial = (stat.media_cartola / max_media) * 50
            else:
                base_potencial = (stat.preco / max_preco) * 30  # Proxy pela preço
            
            xg_bonus = min(20, stat.xg * 5) if stat.xg > 0 else 0
            xa_bonus = min(10, stat.xa * 3) if stat.xa > 0 else 0
            tendencia_bonus = stat.tendencia_score * 10
            
            stat.score_potencial = min(100, max(0, base_potencial + xg_bonus + xa_bonus + tendencia_bonus))
            
            # Score de Forma (baseado em tendência e últimos jogos)
            forma_base = 50  # Neutro
            forma_base += stat.tendencia_score * 30  # -30 a +30
            
            if stat.tendencia == "subindo":
                forma_base += 10
            elif stat.tendencia == "caindo":
                forma_base -= 10
            
            stat.score_forma = min(100, max(0, forma_base))
            
            # Score de Custo-Benefício
            if stat.preco > 0 and stat.media_cartola > 0:
                cb_ratio = stat.media_cartola / stat.preco
                # Normalizar: 0.5 = regular, 1.0 = bom, 2.0 = excelente
                stat.score_custo_beneficio = min(100, cb_ratio * 50)
            else:
                stat.score_custo_beneficio = 30  # Incerto
            
            # Score de Valorização (para time de valorização)
            val_base = 50
            if stat.variacao_preco > 0:
                val_base += min(30, stat.variacao_preco * 10)
            elif stat.variacao_preco < 0:
                val_base += max(-20, stat.variacao_preco * 5)
            
            # Jogadores baratos em boa forma têm mais potencial
            if stat.preco < 8 and stat.tendencia == "subindo":
                val_base += 20
            
            stat.score_valorizacao = min(100, max(0, val_base))
        
        return estatisticas
    
    # ==================== RANKING FINAL ====================
    
    def rankear_jogadores(
        self,
        estatisticas: Dict[int, EstatisticasJogador],
        tipo: str = "pontuacao",
        posicao: str = None
    ) -> List[EstatisticasJogador]:
        """
        Rankeia jogadores baseado no tipo de time desejado
        
        Args:
            estatisticas: Dict de estatísticas
            tipo: 'pontuacao' ou 'valorizacao'
            posicao: Filtrar por posição
            
        Returns:
            Lista ordenada de jogadores
        """
        jogadores = list(estatisticas.values())
        
        if posicao:
            jogadores = [j for j in jogadores if j.posicao == posicao]
        
        if tipo == "pontuacao":
            # Priorizar: potencial > forma > custo-benefício
            jogadores.sort(
                key=lambda x: (
                    x.score_potencial * 0.5 +
                    x.score_forma * 0.3 +
                    x.score_custo_beneficio * 0.2
                ),
                reverse=True
            )
        else:  # valorizacao
            # Priorizar: valorização > custo-benefício > forma
            jogadores.sort(
                key=lambda x: (
                    x.score_valorizacao * 0.5 +
                    x.score_custo_beneficio * 0.3 +
                    x.score_forma * 0.2
                ),
                reverse=True
            )
        
        return jogadores


class CartolaScoutAnalyzer:
    """
    Analisador de scouts do Cartola FC
    
    Usa os scouts (estatísticas de jogo) para calcular
    métricas avançadas similares a xG/xA.
    """
    
    # Pesos dos scouts para estimar potencial ofensivo
    SCOUTS_OFENSIVOS = {
        "G": 8.0,    # Gol
        "A": 5.0,    # Assistência
        "FD": 1.2,   # Finalização defendida
        "FF": 0.8,   # Finalização pra fora
        "FT": 1.5,   # Finalização na trave
        "FS": 0.5,   # Falta sofrida
    }
    
    # Pesos para potencial defensivo
    SCOUTS_DEFENSIVOS = {
        "SG": 5.0,   # Saldo de gols (sem sofrer)
        "DS": 1.3,   # Desarme
        "RB": 1.5,   # Roubada de bola
        "DD": 3.0,   # Defesa difícil (goleiro)
        "DP": 7.0,   # Defesa de pênalti
    }
    
    def calcular_xg_cartola(self, scouts: List[Dict]) -> float:
        """
        Calcula um 'Expected Goals' baseado nos scouts do Cartola
        
        Usa finalizações e conversão para estimar xG
        """
        total_finalizacoes = 0
        total_gols = 0
        
        for scout in scouts:
            total_finalizacoes += (
                scout.get("FD", 0) + 
                scout.get("FF", 0) + 
                scout.get("FT", 0) +
                scout.get("G", 0)
            )
            total_gols += scout.get("G", 0)
        
        if total_finalizacoes == 0:
            return 0.0
        
        # Taxa de conversão
        conversao = total_gols / total_finalizacoes if total_finalizacoes > 0 else 0.1
        
        # xG = finalizações recentes * taxa de conversão
        ultimos_scouts = scouts[-5:] if len(scouts) >= 5 else scouts
        finalizacoes_recentes = sum(
            s.get("FD", 0) + s.get("FF", 0) + s.get("FT", 0) + s.get("G", 0)
            for s in ultimos_scouts
        )
        
        return (finalizacoes_recentes / max(1, len(ultimos_scouts))) * conversao
    
    def calcular_pontuacao_esperada(
        self, 
        atleta: Dict[str, Any],
        scouts_anteriores: List[Dict] = None,
        posicao: str = None
    ) -> float:
        """
        Calcula pontuação esperada para a próxima rodada
        
        Considera:
        - Média de pontos
        - Tendência recente
        - Tipo de posição
        - Scouts positivos vs negativos
        """
        media = atleta.get("media_num", 0)
        
        if not scouts_anteriores:
            # Sem histórico, usar média ou proxy por preço
            if media > 0:
                return media
            return atleta.get("preco_num", 5) * 0.5
        
        # Calcular média ponderada (rodadas recentes pesam mais)
        pesos = [1.0, 0.9, 0.8, 0.7, 0.6]  # Últimas 5 rodadas
        pontuacoes = []
        
        for i, scout in enumerate(scouts_anteriores[-5:][::-1]):  # Mais recente primeiro
            if scout.get("entrou_em_campo"):
                peso = pesos[i] if i < len(pesos) else 0.5
                pontuacoes.append((scout.get("pontuacao", 0), peso))
        
        if not pontuacoes:
            return media if media > 0 else atleta.get("preco_num", 5) * 0.5
        
        # Média ponderada
        soma_ponderada = sum(p * w for p, w in pontuacoes)
        soma_pesos = sum(w for _, w in pontuacoes)
        
        return soma_ponderada / soma_pesos if soma_pesos > 0 else media


# Instância global
stats_provider = StatisticsProvider()
scout_analyzer = CartolaScoutAnalyzer()
