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
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict

sys.path.append(str(Path(__file__).parent.parent.parent))

from config.settings import settings
from src.analysis.fixture_collector import CARTOLA_TO_APIFOOTBALL

logger = logging.getLogger("MatchAnalyzer")

# Diretório do cache de stats (API-Football)
STATS_CACHE_DIR = Path(__file__).parent.parent.parent / "data" / "stats_cache"
# Diretório do cache FDO (football-data.org)
FDO_CACHE_DIR = Path(__file__).parent.parent.parent / "data" / "fdo_cache"


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
    
    # v10: Forças SEPARADAS para casa e fora (calculadas com dados reais)
    forca_ataque_casa: float = 0.0   # Força ofensiva jogando em casa
    forca_ataque_fora: float = 0.0   # Força ofensiva jogando fora
    forca_defesa_casa: float = 0.0   # Solidez defensiva em casa
    forca_defesa_fora: float = 0.0   # Solidez defensiva fora
    forca_casa: float = 0.0          # Força geral em casa
    forca_fora: float = 0.0          # Força geral fora
    
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
    PESO_ODDS_MERCADO = 0.35  # Peso das odds de mercado no blend (0.35 = 35%)
    
    def __init__(self):
        self.estatisticas_times: Dict[int, EstatisticasTime] = {}
        self.confrontos_rodada: Dict[int, List[Confronto]] = {}
        self.resultados_anteriores: List[Dict] = []
        self._stats_cache: Dict[int, Dict] = {}  # cartola_id → stats reais API-Football
        self._fdo_classificacao: Dict[int, Dict] = {}  # cartola_id → dados classificação FDO
        self._odds_collector = None  # Inicializado sob demanda

    @staticmethod
    def _carregar_fdo_classificacao() -> Dict[int, Dict]:
        """
        Carrega dados REAIS do football-data.org (fonte PRIMÁRIA para 2026).
        
        Combina standings (classificação) + matches (jogos finalizados)
        para obter splits casa/fora REAIS e clean_sheets contados.
        
        Retorna Dict[cartola_id, stats_dict] com formato compatível com _stats_cache.
        """
        result: Dict[int, Dict] = {}
        
        try:
            from src.analysis.football_data_client import FootballDataClient
            from src.utils.team_mapping import get_cartola_id_from_fdo
            from collections import defaultdict
            
            fdo = FootballDataClient()
            classificacao = fdo.classificacao()
            
            if not classificacao:
                logger.warning("⚠️ FDO: sem dados de classificação")
                return result
            
            # ── Buscar JOGOS finalizados para splits casa/fora REAIS ──
            jogos_reais = defaultdict(lambda: {
                'jogos_casa': 0, 'jogos_fora': 0,
                'gols_casa': 0, 'gols_fora': 0,
                'gols_sofridos_casa': 0, 'gols_sofridos_fora': 0,
                'vit_casa': 0, 'vit_fora': 0,
                'clean_sheets': 0,
            })
            
            try:
                matches = fdo.jogos_periodo('2026-01-01', '2026-12-31')
                if matches:
                    for j in matches:
                        if j.get('status') != 'FINISHED':
                            continue
                        m_id = j.get('mandante_id', 0)
                        v_id = j.get('visitante_id', 0)
                        gm = j.get('gols_mandante') or 0
                        gv = j.get('gols_visitante') or 0
                        
                        # Mandante (casa)
                        jogos_reais[m_id]['jogos_casa'] += 1
                        jogos_reais[m_id]['gols_casa'] += gm
                        jogos_reais[m_id]['gols_sofridos_casa'] += gv
                        if gm > gv:
                            jogos_reais[m_id]['vit_casa'] += 1
                        if gv == 0:
                            jogos_reais[m_id]['clean_sheets'] += 1
                        
                        # Visitante (fora)
                        jogos_reais[v_id]['jogos_fora'] += 1
                        jogos_reais[v_id]['gols_fora'] += gv
                        jogos_reais[v_id]['gols_sofridos_fora'] += gm
                        if gv > gm:
                            jogos_reais[v_id]['vit_fora'] += 1
                        if gm == 0:
                            jogos_reais[v_id]['clean_sheets'] += 1
                    
                    logger.info(f"⚽ FDO matches: {len(matches)} jogos → stats casa/fora para {len(jogos_reais)} times")
            except Exception as me:
                logger.warning(f"⚠️ FDO matches indisponível, usando splits aproximados: {me}")
            
            for time_fdo in classificacao:
                fdo_id = time_fdo.get("time_id", 0)
                cartola_id = get_cartola_id_from_fdo(fdo_id)
                if not cartola_id:
                    continue
                
                jogos = time_fdo.get("jogos", 0)
                if jogos == 0:
                    continue
                
                gols_pro = time_fdo.get("gols_pro", 0)
                gols_contra = time_fdo.get("gols_contra", 0)
                vitorias_total = time_fdo.get("vitorias", 0)
                
                # Usar splits REAIS dos matches (não dividir por 2!)
                jr = jogos_reais.get(fdo_id, {})
                jogos_casa = jr.get('jogos_casa', 0)
                jogos_fora = jr.get('jogos_fora', 0)
                gols_casa = jr.get('gols_casa', 0)
                gols_fora = jr.get('gols_fora', 0)
                gols_sofridos_casa = jr.get('gols_sofridos_casa', 0)
                gols_sofridos_fora = jr.get('gols_sofridos_fora', 0)
                vit_casa = jr.get('vit_casa', 0)
                vit_fora = jr.get('vit_fora', 0)
                clean_sheets = jr.get('clean_sheets', 0)
                
                # Se não temos dados de matches, fallback conservador
                if jogos_casa + jogos_fora == 0:
                    jogos_casa = (jogos + 1) // 2
                    jogos_fora = jogos // 2
                
                result[cartola_id] = {
                    "team_name": time_fdo.get("time", "?"),
                    "fdo_id": fdo_id,
                    "posicao": time_fdo.get("posicao", 0),
                    "pontos": time_fdo.get("pontos", 0),
                    "forma": time_fdo.get("forma", ""),
                    "jogos": {
                        "total": jogos,
                        "casa": jogos_casa,
                        "fora": jogos_fora,
                    },
                    "gols_pro": {
                        "total": gols_pro,
                        "media": round(gols_pro / jogos, 2) if jogos else 0,
                        "casa": gols_casa,
                        "fora": gols_fora,
                    },
                    "gols_contra": {
                        "total": gols_contra,
                        "media": round(gols_contra / jogos, 2) if jogos else 0,
                        "casa": gols_sofridos_casa,
                        "fora": gols_sofridos_fora,
                    },
                    "vitorias": {
                        "total": vitorias_total,
                        "casa": vit_casa,
                        "fora": vit_fora,
                    },
                    "clean_sheets": {
                        "total": clean_sheets,
                    },
                    "_fonte": "football-data.org",
                    "_temporada": "2026",
                }
            
            logger.info(f"⚽ FDO classificação: {len(result)} times com dados REAIS 2026")
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar FDO classificação: {e}")
        
        return result

    @staticmethod
    def _carregar_stats_cache() -> Dict[int, Dict]:
        """
        Carrega stats reais do cache API-Football (data/stats_cache/team_stats/).
        Retorna Dict[cartola_id, stats_dict] para cada time mapeado.
        
        Prioridade de liga: Serie A (71) > Serie B (72) > Copa BR (75).
        """
        cache_dir = STATS_CACHE_DIR / "team_stats"
        if not cache_dir.exists():
            return {}

        result: Dict[int, Dict] = {}
        for cartola_id, af_id in CARTOLA_TO_APIFOOTBALL.items():
            # Tentar ligas na ordem de prioridade, season 2026 primeiro, fallback 2024
            for season in [2026, 2024]:
                for league in [71, 72, 75]:
                    path = cache_dir / f"{af_id}_{league}_{season}.json"
                    if path.exists():
                        try:
                            with open(path, "r", encoding="utf-8") as f:
                                data = json.load(f)
                            jogos = data.get("jogos", {})
                            if isinstance(jogos, dict) and jogos.get("total", 0) > 0:
                                result[cartola_id] = data
                                break
                        except (json.JSONDecodeError, OSError) as e:
                            logger.warning(f"Cache corrompido {path.name}: {e}")
                            continue
                if cartola_id in result:
                    break
        logger.info(f"📊 Stats cache: {len(result)}/{len(CARTOLA_TO_APIFOOTBALL)} times com dados reais")
        return result
    
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
        # Ranking FALLBACK — usado APENAS se FDO estiver indisponível
        # Baseado em estrutura, elenco e tradição (pré-temporada 2026)
        RANKING_HISTORICO_FALLBACK = {
            "FLA": 85, "PAL": 84, "BOT": 82, "INT": 79, "FLU": 79, "CAM": 78,
            "SAO": 77, "COR": 76, "GRE": 75, "CRU": 73, "SAN": 73,
            "BAH": 76, "VAS": 74, "RBB": 75, "CAP": 74, "VIT": 71,
            "MIR": 71, "CFC": 69, "CHA": 70, "REM": 68,
        }
        RANKING_ATAQUE_FALLBACK = {
            "FLA": 87, "PAL": 83, "BOT": 81, "INT": 77, "FLU": 76, "CAM": 76,
            "SAO": 78, "COR": 74, "GRE": 73, "CRU": 71, "SAN": 71,
            "BAH": 75, "VAS": 72, "RBB": 75, "CAP": 72, "VIT": 69,
            "MIR": 70, "CFC": 67, "CHA": 68, "REM": 65,
        }
        RANKING_DEFESA_FALLBACK = {
            "FLA": 83, "PAL": 86, "BOT": 83, "INT": 81, "FLU": 82, "CAM": 75,
            "SAO": 75, "COR": 77, "GRE": 76, "CRU": 73, "SAN": 72,
            "BAH": 74, "VAS": 75, "RBB": 72, "CAP": 74, "VIT": 71,
            "MIR": 72, "CFC": 70, "CHA": 71, "REM": 68,
        }
        
        estatisticas = {}
        
        # Extrair posições reais das partidas
        posicoes_reais = {}
        aproveitamentos = {}
        jogos_disputados = 0  # Para calcular peso do ranking histórico
        
        # Carregar dados REAIS: FDO (2026) como primário, API-Football (2024) como fallback
        self._fdo_classificacao = self._carregar_fdo_classificacao()
        self._stats_cache = self._carregar_stats_cache()
        
        # Mesclar: FDO tem prioridade (dados 2026 reais), API-Football como complemento
        # Para times que estão no FDO, usa FDO; para times só no API-Football, usa AF
        stats_merged: Dict[int, Dict] = {}
        for cid, stats in self._stats_cache.items():
            stats_merged[cid] = stats
        for cid, fdo_stats in self._fdo_classificacao.items():
            # FDO sobrescreve API-Football (dados mais recentes/corretos)
            stats_merged[cid] = fdo_stats
        self._stats_cache = stats_merged
        
        if self._fdo_classificacao:
            logger.info(f"✅ Usando {len(self._fdo_classificacao)} times com dados FDO 2026 (primário)")
        
        # ── Computar rankings DINÂMICOS a partir dos dados FDO reais ──
        # Substitui os rankings hardcoded quando temos dados reais
        RANKING_HISTORICO = dict(RANKING_HISTORICO_FALLBACK)
        RANKING_ATAQUE = dict(RANKING_ATAQUE_FALLBACK)
        RANKING_DEFESA = dict(RANKING_DEFESA_FALLBACK)
        
        if self._fdo_classificacao:
            # Calcular média da liga para referência
            total_gols_pro = 0
            total_gols_contra = 0
            total_jogos = 0
            for fdo_s in self._fdo_classificacao.values():
                gp = fdo_s.get("gols_pro", {})
                gc = fdo_s.get("gols_contra", {})
                j = fdo_s.get("jogos", {})
                total_gols_pro += gp.get("total", 0) if isinstance(gp, dict) else 0
                total_gols_contra += gc.get("total", 0) if isinstance(gc, dict) else 0
                total_jogos += j.get("total", 0) if isinstance(j, dict) else 0
            
            media_liga_gols = (total_gols_pro / total_jogos) if total_jogos > 0 else 1.25
            
            for cid, fdo_s in self._fdo_classificacao.items():
                abrev_fdo = fdo_s.get("team_name", "")
                # Buscar abreviação do time no clubes dict
                abrev_match = None
                for cid_str, cinfo in clubes.items():
                    if int(cid_str) == cid:
                        abrev_match = cinfo.get("abreviacao", "???")
                        break
                if not abrev_match:
                    continue
                
                pos = fdo_s.get("posicao", 10)
                jogos_fdo = fdo_s.get("jogos", {}).get("total", 0) if isinstance(fdo_s.get("jogos"), dict) else 0
                gp_info = fdo_s.get("gols_pro", {})
                gc_info = fdo_s.get("gols_contra", {})
                gp_total = gp_info.get("total", 0) if isinstance(gp_info, dict) else 0
                gc_total = gc_info.get("total", 0) if isinstance(gc_info, dict) else 0
                
                # Ranking geral: posição → 90 (1º) a 50 (20º)
                ranking_pos = max(50, 90 - (pos - 1) * 2.1)
                
                if jogos_fdo >= 2:
                    media_atk = gp_total / jogos_fdo
                    media_def = gc_total / jogos_fdo
                    
                    # Ataque: base + bônus por gols acima da média
                    bonus_atk = min(8, max(-8, (media_atk - media_liga_gols) * 8))
                    # Defesa: base + bônus por gols ABAIXO da média (menos sofridos = melhor)
                    bonus_def = min(8, max(-8, (media_liga_gols - media_def) * 8))
                    
                    ranking_atk = max(50, min(95, ranking_pos + bonus_atk))
                    ranking_def = max(50, min(95, ranking_pos + bonus_def))
                else:
                    ranking_atk = ranking_pos
                    ranking_def = ranking_pos
                
                # Ponderação: FDO dinâmico vs fallback histórico
                # Início do campeonato: mais peso no histórico
                # Avanço: mais peso no dinâmico
                peso_dinamico = min(0.8, jogos_fdo / 10.0) if jogos_fdo > 0 else 0.0
                peso_fallback = 1.0 - peso_dinamico
                
                fb_geral = RANKING_HISTORICO_FALLBACK.get(abrev_match, 50)
                fb_atk = RANKING_ATAQUE_FALLBACK.get(abrev_match, fb_geral)
                fb_def = RANKING_DEFESA_FALLBACK.get(abrev_match, fb_geral)
                
                RANKING_HISTORICO[abrev_match] = round(ranking_pos * peso_dinamico + fb_geral * peso_fallback, 1)
                RANKING_ATAQUE[abrev_match] = round(ranking_atk * peso_dinamico + fb_atk * peso_fallback, 1)
                RANKING_DEFESA[abrev_match] = round(ranking_def * peso_dinamico + fb_def * peso_fallback, 1)
            
            logger.info(f"📊 Rankings dinâmicos: {len(RANKING_HISTORICO)} times (FDO + fallback ponderado)")
        
        # Usar posições do FDO como posições reais (mais confiável que Cartola API)
        for cid, fdo_stats in self._fdo_classificacao.items():
            posicao_fdo = fdo_stats.get("posicao", 0)
            if posicao_fdo > 0:
                posicoes_reais[cid] = posicao_fdo
        
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
            
            # 1. Força do RANKING HISTÓRICO (geral + ataque + defesa)
            forca_historico = RANKING_HISTORICO.get(abrev, 50)
            forca_hist_ataque = RANKING_ATAQUE.get(abrev, forca_historico)
            forca_hist_defesa = RANKING_DEFESA.get(abrev, forca_historico)
            
            # 2. Força da POSIÇÃO ATUAL
            posicao = posicoes_reais.get(clube_id)
            if posicao:
                # V5: Spread progressivo — posição importa pouco no início,
                # muito no fim do campeonato. Evita reversões com 2-3 jogos.
                spread = min(3.5, 0.5 + jogos_disputados * 0.20)
                forca_posicao = max(40, 100 - (posicao - 1) * spread)
            else:
                forca_posicao = forca_historico  # Fallback para histórico
            
            # 3. Força PONDERADA (ranking histórico + posição atual)
            forca_base = (forca_historico * peso_historico) + (forca_posicao * peso_posicao)
            forca_base_ataque = (forca_hist_ataque * peso_historico) + (forca_posicao * peso_posicao)
            forca_base_defesa = (forca_hist_defesa * peso_historico) + (forca_posicao * peso_posicao)
            
            # 4. Bônus de FORMA RECENTE (últimos 5 jogos) - até ±10 pontos
            aprov = aproveitamentos.get(clube_id, [])
            vitorias = sum(1 for r in aprov if r and r.lower() == 'v')
            empates = sum(1 for r in aprov if r and r.lower() == 'e')
            derrotas = sum(1 for r in aprov if r and r.lower() == 'd')
            
            # Cada vitória +2, empate 0, derrota -2 (máx ±10)
            forma_bonus = (vitorias * 2) - (derrotas * 2)
            forma_bonus = max(-10, min(10, forma_bonus))
            
            # V5: Escalar bonus pela confiança — poucos jogos = bonus reduzido
            jogos_totais = vitorias + empates + derrotas
            confianca_forma = min(1.0, jogos_totais / 5.0)
            forma_bonus = forma_bonus * confianca_forma
            
            # 5. Força final = base + forma
            forca_final = min(100, max(20, forca_base + forma_bonus))
            # v9: Forças SEPARADAS para ataque e defesa
            forca_final_ataque = min(100, max(20, forca_base_ataque + forma_bonus))
            forca_final_defesa = min(100, max(20, forca_base_defesa + forma_bonus))
            
            # Calcular jogos totais a partir do aproveitamento
            jogos_totais = vitorias + empates + derrotas
            pontos_totais = (vitorias * 3) + empates
            
            # Estimar gols baseado na força do time e resultados
            # PRIORIDADE: dados reais do API-Football > heurística
            gols_estimados_pro = 0
            gols_estimados_contra = 0
            media_gols_pro = 0.0
            media_gols_contra = 0.0
            clean_sheets = 0
            jogos_real = 0
            usa_dados_reais = False
            
            real_stats = self._stats_cache.get(clube_id)
            if real_stats:
                # Dados REAIS da API-Football (gols, clean sheets, etc.)
                gp = real_stats.get("gols_pro", {})
                gc = real_stats.get("gols_contra", {})
                cs = real_stats.get("clean_sheets", {})
                jogos_info = real_stats.get("jogos", {})
                jogos_real = jogos_info.get("total", 0) if isinstance(jogos_info, dict) else 0
                
                if jogos_real > 0:
                    usa_dados_reais = True
                    gols_estimados_pro = gp.get("total", 0) if isinstance(gp, dict) else 0
                    gols_estimados_contra = gc.get("total", 0) if isinstance(gc, dict) else 0
                    media_gols_pro = float(gp.get("media", 0)) if isinstance(gp, dict) else 0.0
                    media_gols_contra = float(gc.get("media", 0)) if isinstance(gc, dict) else 0.0
                    clean_sheets = cs.get("total", 0) if isinstance(cs, dict) else 0
                    
                    # v10: Se jogos_real >> jogos atuais → dados de temporada anterior
                    # Reduzir confiança para não inflar com dados obsoletos
                    # Ex: jogos_real=38 mas rodada 3 → fator_atualidade=0.15
                    confianca_gols = min(1.0, jogos_real / 10.0)
                    if jogos_real > jogos_totais + 5:
                        fator_atualidade = max(0.15, jogos_totais / jogos_real)
                        confianca_gols *= fator_atualidade
                    
                    # Ataque: muitos gols = ataque forte (média liga ≈ 1.2)
                    ajuste_ataque = min(8, max(-8, (media_gols_pro - 1.2) * 6)) * confianca_gols
                    forca_final_ataque = min(100, max(20, forca_final_ataque + ajuste_ataque))
                    # Defesa: poucos gols sofridos = defesa forte
                    ajuste_defesa = min(8, max(-8, (1.2 - media_gols_contra) * 6)) * confianca_gols
                    forca_final_defesa = min(100, max(20, forca_final_defesa + ajuste_defesa))
                    # Bônus clean sheets (>25% = boa defesa)
                    if jogos_real >= 5:
                        pct_cs = clean_sheets / jogos_real
                        bonus_cs = min(4, max(-2, (pct_cs - 0.20) * 20)) * confianca_gols
                        forca_final_defesa = min(100, max(20, forca_final_defesa + bonus_cs))
            
            if not usa_dados_reais and jogos_totais > 0:
                # Tentar dados FDO do standings (gols_pro/contra reais) como segundo recurso
                fdo_stats_fallback = self._fdo_classificacao.get(clube_id)
                if fdo_stats_fallback:
                    gp_fdo = fdo_stats_fallback.get("gols_pro", {})
                    gc_fdo = fdo_stats_fallback.get("gols_contra", {})
                    gp_t = gp_fdo.get("total", 0) if isinstance(gp_fdo, dict) else 0
                    gc_t = gc_fdo.get("total", 0) if isinstance(gc_fdo, dict) else 0
                    j_fdo = fdo_stats_fallback.get("jogos", {}).get("total", 0) if isinstance(fdo_stats_fallback.get("jogos"), dict) else 0
                    if j_fdo > 0 and gp_t > 0:
                        usa_dados_reais = True
                        gols_estimados_pro = gp_t
                        gols_estimados_contra = gc_t
                        media_gols_pro = gp_t / j_fdo
                        media_gols_contra = gc_t / j_fdo
                        jogos_real = j_fdo
                        confianca_gols = min(1.0, j_fdo / 10.0)
                        ajuste_ataque = min(8, max(-8, (media_gols_pro - 1.2) * 6)) * confianca_gols
                        forca_final_ataque = min(100, max(20, forca_final_ataque + ajuste_ataque))
                        ajuste_defesa = min(8, max(-8, (1.2 - media_gols_contra) * 6)) * confianca_gols
                        forca_final_defesa = min(100, max(20, forca_final_defesa + ajuste_defesa))
                
                if not usa_dados_reais:
                    # Último fallback: heurística com penalidade de confiança baixa
                    gols_estimados_pro = (vitorias * 2) + empates + (derrotas * 1)
                    gols_estimados_contra = (derrotas * 2) + empates + int(vitorias * 0.5)
                    gols_estimados_pro = int(gols_estimados_pro)
                    gols_estimados_contra = int(gols_estimados_contra)
                    
                    if jogos_totais >= 2:
                        media_gols_pro = gols_estimados_pro / jogos_totais
                        media_gols_contra = gols_estimados_contra / jogos_totais
                        confianca_gols = min(1.0, jogos_totais / 8.0) * 0.5  # Penalizar por ser heurística
                        ajuste_ataque = min(8, max(-8, (media_gols_pro - 1.2) * 6)) * confianca_gols
                        forca_final_ataque = min(100, max(20, forca_final_ataque + ajuste_ataque))
                        ajuste_defesa = min(8, max(-8, (1.2 - media_gols_contra) * 6)) * confianca_gols
                        forca_final_defesa = min(100, max(20, forca_final_defesa + ajuste_defesa))
            
            # Enriquecer com dados reais de jogos (casa/fora) se disponível
            vitorias_casa = 0
            vitorias_fora = 0
            gols_casa = 0
            gols_fora = 0
            gols_sofridos_casa = 0
            gols_sofridos_fora = 0
            
            if real_stats:
                vit_info = real_stats.get("vitorias", {})
                vitorias_casa = vit_info.get("casa", 0) if isinstance(vit_info, dict) else 0
                vitorias_fora = vit_info.get("fora", 0) if isinstance(vit_info, dict) else 0
                gp = real_stats.get("gols_pro", {})
                gc = real_stats.get("gols_contra", {})
                gols_casa = gp.get("casa", 0) if isinstance(gp, dict) else 0
                gols_fora = gp.get("fora", 0) if isinstance(gp, dict) else 0
                gols_sofridos_casa = gc.get("casa", 0) if isinstance(gc, dict) else 0
                gols_sofridos_fora = gc.get("fora", 0) if isinstance(gc, dict) else 0
            
            # v10: Calcular forças de ataque/defesa SEPARADAS para casa e fora
            # Usa dados reais de gols marcados/sofridos em casa vs fora
            jogos_casa_real = 0
            jogos_fora_real = 0
            if real_stats:
                jogos_info_cf = real_stats.get("jogos", {})
                if isinstance(jogos_info_cf, dict):
                    jogos_casa_real = jogos_info_cf.get("casa", 0)
                    jogos_fora_real = jogos_info_cf.get("fora", 0)
            
            # Calcular forças casa/fora com base em gols reais
            # MEDIA_LIGA_REF calculada dinamicamente dos dados FDO
            MEDIA_LIGA_REF = 1.25  # fallback
            if self._fdo_classificacao:
                _total_gp = sum(
                    s.get("gols_pro", {}).get("total", 0) 
                    for s in self._fdo_classificacao.values() 
                    if isinstance(s.get("gols_pro"), dict)
                )
                _total_j = sum(
                    s.get("jogos", {}).get("total", 0)
                    for s in self._fdo_classificacao.values()
                    if isinstance(s.get("jogos"), dict)
                )
                if _total_j > 0:
                    MEDIA_LIGA_REF = round(_total_gp / _total_j, 3)
            
            if jogos_casa_real >= 2 and gols_casa > 0:
                media_atk_casa = gols_casa / jogos_casa_real
                media_def_casa = gols_sofridos_casa / jogos_casa_real
                confianca_cf = min(1.0, jogos_casa_real / 8.0)
                # v10: Reduzir confiança se dados são de temporada anterior
                if jogos_casa_real > jogos_totais + 3:
                    fator_cf = max(0.15, jogos_totais / jogos_casa_real)
                    confianca_cf *= fator_cf
                ajuste_atk_casa = min(10, max(-10, (media_atk_casa - MEDIA_LIGA_REF) * 7)) * confianca_cf
                ajuste_def_casa = min(10, max(-10, (MEDIA_LIGA_REF - media_def_casa) * 7)) * confianca_cf
                f_atk_casa = min(100, max(20, forca_final_ataque + ajuste_atk_casa))
                f_def_casa = min(100, max(20, forca_final_defesa + ajuste_def_casa))
            else:
                # v10: Sem dados reais casa — bônus conservador (+2 pts fixo)
                # Antes: *1.05 inflava demais (PAL defesa 94 → casa 99!)
                f_atk_casa = min(100, forca_final_ataque + 2)
                f_def_casa = min(100, forca_final_defesa + 2)
            
            if jogos_fora_real >= 2 and (gols_fora > 0 or gols_sofridos_fora > 0):
                media_atk_fora = gols_fora / jogos_fora_real
                media_def_fora = gols_sofridos_fora / jogos_fora_real
                confianca_cf = min(1.0, jogos_fora_real / 8.0)
                # v10: Reduzir confiança se dados são de temporada anterior
                if jogos_fora_real > jogos_totais + 3:
                    fator_cf = max(0.15, jogos_totais / jogos_fora_real)
                    confianca_cf *= fator_cf
                ajuste_atk_fora = min(10, max(-10, (media_atk_fora - MEDIA_LIGA_REF) * 7)) * confianca_cf
                ajuste_def_fora = min(10, max(-10, (MEDIA_LIGA_REF - media_def_fora) * 7)) * confianca_cf
                f_atk_fora = min(100, max(20, forca_final_ataque + ajuste_atk_fora))
                f_def_fora = min(100, max(20, forca_final_defesa + ajuste_def_fora))
            else:
                # v10: Sem dados reais fora — penalidade conservadora (-3 pts fixo)
                # Antes: *0.92 era inconsistente com a escala
                f_atk_fora = max(20, forca_final_ataque - 3)
                f_def_fora = max(20, forca_final_defesa - 3)
            
            f_casa = (f_atk_casa + f_def_casa) / 2
            f_fora = (f_atk_fora + f_def_fora) / 2
            
            stats = EstatisticasTime(
                clube_id=clube_id,
                nome=clube_info.get("nome", ""),
                abreviacao=abrev,
                posicao=posicao or 0,
                # Cap: se stats vêm de season passada (ex: 2024, jogos=38),
                # usar mínimo entre jogos_real e rodada Cartola atual
                jogos=min(jogos_real, jogos_totais) if usa_dados_reais and jogos_totais > 0 else (jogos_real if usa_dados_reais else jogos_totais),
                vitorias=vitorias,
                empates=empates,
                derrotas=derrotas,
                # Usar pontos REAIS do FDO quando disponível
                pontos=real_stats.get("pontos", pontos_totais) if real_stats and real_stats.get("_fonte") == "football-data.org" else pontos_totais,
                gols_pro=gols_estimados_pro,
                gols_contra=gols_estimados_contra,
                saldo_gols=gols_estimados_pro - gols_estimados_contra,
                vitorias_casa=vitorias_casa,
                vitorias_fora=vitorias_fora,
                gols_casa=gols_casa,
                gols_fora=gols_fora,
                gols_sofridos_casa=gols_sofridos_casa,
                gols_sofridos_fora=gols_sofridos_fora,
                media_gols_pro=media_gols_pro,
                media_gols_contra=media_gols_contra,
                forca_ataque=forca_final_ataque,
                forca_defesa=forca_final_defesa,
                forca_geral=forca_final,
                # v10: Forças casa/fora reais
                forca_ataque_casa=round(f_atk_casa, 1),
                forca_ataque_fora=round(f_atk_fora, 1),
                forca_defesa_casa=round(f_def_casa, 1),
                forca_defesa_fora=round(f_def_fora, 1),
                forca_casa=round(f_casa, 1),
                forca_fora=round(f_fora, 1),
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
        Calcula probabilidades e expectativas para um confronto.
        
        V11: Blend com odds de mercado quando disponíveis.
        Peso: 65% modelo heurístico + 35% mercado (The Odds API).
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
        
        # Probabilidades básicas (modelo heurístico)
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
        
        prob_modelo_casa = prob_m * (1 - prob_empate)
        prob_modelo_empate = prob_empate
        prob_modelo_fora = prob_v * (1 - prob_empate)
        
        # Normalizar modelo
        soma_modelo = prob_modelo_casa + prob_modelo_empate + prob_modelo_fora
        if soma_modelo > 0:
            prob_modelo_casa /= soma_modelo
            prob_modelo_empate /= soma_modelo
            prob_modelo_fora /= soma_modelo
        
        # ── Blend com odds de mercado (The Odds API) ──
        odds_jogo = self._buscar_odds_jogo(
            confronto.mandante_nome, confronto.visitante_nome
        )
        
        if odds_jogo:
            peso_mercado = self.PESO_ODDS_MERCADO
            peso_modelo = 1.0 - peso_mercado
            
            confronto.prob_vitoria_mandante = (
                prob_modelo_casa * peso_modelo +
                odds_jogo["prob_casa"] * peso_mercado
            )
            confronto.prob_empate = (
                prob_modelo_empate * peso_modelo +
                odds_jogo["prob_empate"] * peso_mercado
            )
            confronto.prob_vitoria_visitante = (
                prob_modelo_fora * peso_modelo +
                odds_jogo["prob_fora"] * peso_mercado
            )
            logger.debug(
                f"📊 Blend odds {confronto.mandante_abrev}x{confronto.visitante_abrev}: "
                f"modelo={prob_modelo_casa:.2f}/{prob_modelo_empate:.2f}/{prob_modelo_fora:.2f} | "
                f"mercado={odds_jogo['prob_casa']:.2f}/{odds_jogo['prob_empate']:.2f}/{odds_jogo['prob_fora']:.2f}"
            )
        else:
            confronto.prob_vitoria_mandante = prob_modelo_casa
            confronto.prob_empate = prob_modelo_empate
            confronto.prob_vitoria_visitante = prob_modelo_fora
        
        # Re-normalizar após blend
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
        
        # Dificuldade do confronto — v10: RELATIVA à média da liga
        # Calcula desvio da força do adversário em relação à média
        forcas = [s.forca_geral for s in self.estatisticas_times.values() if hasattr(s, 'forca_geral')]
        media_liga = sum(forcas) / len(forcas) if forcas else 60.0
        
        # Para o mandante: dificuldade = quão acima da média é o visitante
        # REM (70.1) vs média liga (73) = -2.9 → fácil
        # FLA (82) vs média liga (73) = +9 → difícil
        desvio_visit = visitante_stats.forca_geral - media_liga
        confronto.dificuldade_mandante = 50 + desvio_visit  # 50 = neutro
        
        # Para o visitante: força do mandante + vantagem casa
        desvio_mand = mandante_stats.forca_geral - media_liga
        confronto.dificuldade_visitante = 50 + desvio_mand + 10  # +10 = penalidade jogar fora
    
    def _buscar_odds_jogo(self, mandante_nome: str, visitante_nome: str) -> Optional[Dict]:
        """
        Busca probabilidades implícitas do mercado (The Odds API) para um jogo.
        
        Usa cache interno (data/_internal/odds/). Nunca gasta créditos —
        lê apenas o que o scheduler já coletou.
        
        Retorna dict com prob_casa/prob_empate/prob_fora ou None.
        """
        try:
            if self._odds_collector is None:
                from src.analysis.odds_collector import OddsCollector
                self._odds_collector = OddsCollector()
            
            jogo = self._odds_collector.odds_para_jogo(mandante_nome, visitante_nome)
            if jogo:
                return jogo
        except Exception as e:
            logger.debug(f"Odds indisponíveis para {mandante_nome}x{visitante_nome}: {e}")
        return None
    
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
        
        # v9: Usar força DIFERENCIADA do adversário por posição
        # Defensores se importam com ataque do adversário
        # Ofensivos se importam com defesa do adversário
        if is_mandante:
            stats_adversario = confronto.visitante_stats
        else:
            stats_adversario = confronto.mandante_stats
        
        if posicao in ["GOL", "ZAG", "LAT"]:
            # Defensores: bônus/penalidade por chance de SG
            # v9: Usar forca_ataque do adversário (ataque fraco = mais SG)
            if chance_sg > 70:
                bonus *= 1.20
            elif chance_sg > 50:
                bonus *= 1.10
            elif chance_sg < 40:
                bonus *= 0.80
            elif chance_sg < 30:
                bonus *= 0.70
            
            # v9: Penalidade extra se adversário tem ataque forte
            if stats_adversario and stats_adversario.forca_ataque > 80:
                bonus *= 0.90  # Adversário com ataque forte = menos SG
            elif stats_adversario and stats_adversario.forca_ataque < 45:
                bonus *= 1.10  # Adversário com ataque fraco = mais SG
        
        elif posicao in ["MEI", "ATA"]:
            # Ofensivos: bônus por expectativa de gols
            # v9: Usar forca_defesa do adversário (defesa fraca = mais gols)
            if expect_gols > 1.5:
                bonus *= 1.20
            elif expect_gols > 1.0:
                bonus *= 1.10
            elif expect_gols < 0.7:
                bonus *= 0.80
            elif expect_gols < 0.5:
                bonus *= 0.70
            
            # v9: Bônus extra se adversário tem defesa fraca
            if stats_adversario and stats_adversario.forca_defesa < 45:
                bonus *= 1.10  # Defesa fraca = mais gols
            elif stats_adversario and stats_adversario.forca_defesa > 85:
                bonus *= 0.90  # Defesa forte = menos gols
        
        # Ajustar por dificuldade geral (escala relativa: 50 = neutro)
        if dificuldade < 40:
            bonus *= 1.20  # Adversário bem abaixo da média
        elif dificuldade < 48:
            bonus *= 1.10  # Adversário abaixo da média
        elif dificuldade > 62:
            bonus *= 0.70  # Adversário muito acima da média
        elif dificuldade > 55:
            bonus *= 0.80  # Adversário acima da média
        
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
        
        # Classificar dificuldade (escala relativa: 50 = neutro)
        if dificuldade < 40:
            dificuldade_texto = "FÁCIL"
        elif dificuldade < 52:
            dificuldade_texto = "MÉDIO"
        elif dificuldade < 62:
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
