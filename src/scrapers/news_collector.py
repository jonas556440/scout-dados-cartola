"""
News Collector - Coletor de Notícias e Escalações
Cartola FC 2026

Busca informações externas para melhorar análise:
1. Escalações prováveis dos times
2. Desfalques confirmados
3. Jogadores suspensos/lesionados
4. Times jogando com reservas (copas)
5. Notícias relevantes sobre times

Fontes:
- GE.globo.com (oficial)
- API Cartola (atletas e status)
"""
import sys
import re
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict

sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_SCRAPING = True
except ImportError:
    HAS_SCRAPING = False

from config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class InfoTime:
    """Informações coletadas sobre um time"""
    clube_id: int
    abrev: str
    nome: str
    
    # Desfalques
    suspensos: List[str] = field(default_factory=list)
    lesionados: List[str] = field(default_factory=list)
    duvidas: List[str] = field(default_factory=list)
    
    # Contexto
    jogando_reservas: bool = False
    motivo_reservas: str = ""  # "copa", "poupar", etc
    foco_copa: bool = False
    
    # Força ajustada
    penalizacao: float = 0.0  # Redução na força (0-30)
    
    # Metadados
    ultima_atualizacao: datetime = field(default_factory=datetime.now)
    fonte: str = ""
    
    def calcular_penalizacao(self) -> float:
        """Calcula penalização baseada nos desfalques"""
        penalizacao = 0.0
        
        # Cada titular importante que não joga = -3 a -5 pontos de força
        penalizacao += len(self.suspensos) * 4
        penalizacao += len(self.lesionados) * 3
        penalizacao += len(self.duvidas) * 1.5
        
        # Jogando reservas = grande penalização
        if self.jogando_reservas:
            penalizacao += 15
        
        # Foco em copa = penalização moderada
        if self.foco_copa:
            penalizacao += 8
        
        self.penalizacao = min(30, penalizacao)  # Máximo 30 pontos
        return self.penalizacao


class NewsCollector:
    """
    Coletor de notícias e informações sobre times
    
    Utiliza dados da própria API do Cartola + fontes externas
    para identificar desfalques e times jogando com reservas.
    """
    
    # Times que tradicionalmente poupam no Brasileirão
    TIMES_COPAS = {
        "FLA", "PAL", "CAM", "INT", "FLU", "BOT", "SÃO", "COR", "GRE"
    }
    
    # Mapeamento de status de jogadores na API Cartola
    STATUS_PROVAVEL = 7  # Provável titular
    STATUS_DUVIDA = 5    # Dúvida
    STATUS_SUSPENSO = 3  # Suspenso
    STATUS_CONTUNDIDO = 4  # Contundido
    STATUS_NULL = 2      # Sem status
    
    def __init__(self, api_client=None):
        self.api = api_client
        self.cache_info: Dict[int, InfoTime] = {}
        self.ultima_atualizacao = None
        
    def analisar_desfalques_api(self, atletas: List[Dict], clubes: Dict) -> Dict[int, InfoTime]:
        """
        Analisa desfalques usando dados da própria API Cartola
        
        Identifica:
        - Jogadores suspensos
        - Jogadores contundidos
        - Jogadores em dúvida
        """
        info_times: Dict[int, InfoTime] = {}
        
        # Agrupar atletas por time
        atletas_por_time: Dict[int, List[Dict]] = defaultdict(list)
        for atleta in atletas:
            clube_id = atleta.get("clube_id")
            if clube_id:
                atletas_por_time[clube_id].append(atleta)
        
        for clube_id, atletas_time in atletas_por_time.items():
            clube_info = clubes.get(str(clube_id), {})
            abrev = clube_info.get("abreviacao", "???")
            nome = clube_info.get("nome_fantasia", clube_info.get("nome", ""))
            
            info = InfoTime(
                clube_id=clube_id,
                abrev=abrev,
                nome=nome
            )
            
            for atleta in atletas_time:
                nome_atleta = atleta.get("apelido", "")
                status_id = atleta.get("status_id", 0)
                
                # Só considerar atletas "importantes" (preço > 8 ou média > 4)
                preco = atleta.get("preco_num", 0)
                media = atleta.get("media_num", 0)
                
                if preco < 5 and media < 3:
                    continue  # Jogador reserva, não impacta muito
                
                if status_id == self.STATUS_SUSPENSO:
                    info.suspensos.append(nome_atleta)
                elif status_id == self.STATUS_CONTUNDIDO:
                    info.lesionados.append(nome_atleta)
                elif status_id == self.STATUS_DUVIDA:
                    info.duvidas.append(nome_atleta)
            
            info.calcular_penalizacao()
            info_times[clube_id] = info
        
        self.cache_info = info_times
        self.ultima_atualizacao = datetime.now()
        
        return info_times
    
    def verificar_reservas_copa(
        self, 
        rodada: int,
        partidas_copa: List[Dict] = None
    ) -> Dict[str, bool]:
        """
        Verifica se times grandes estão jogando reservas por causa de copa
        
        Heurística:
        - Jogo de copa importante próximo (até 4 dias)
        - Time grande (top 6)
        - Adversário fraco no Brasileirão
        """
        times_reservas = {}
        
        # TODO: Integrar com calendário de copas (Libertadores, CdB, Sulamericana)
        # Por enquanto, apenas marca potencial
        
        for abrev in self.TIMES_COPAS:
            # Verificar se tem jogo de copa na semana
            # Por enquanto, não vamos assumir nada sem dados concretos
            times_reservas[abrev] = False
        
        return times_reservas
    
    def analisar_confronto_especial(
        self,
        mandante_abrev: str,
        visitante_abrev: str,
        mandante_pos: int,
        visitante_pos: int
    ) -> Tuple[float, float, str]:
        """
        Analisa se há situação especial no confronto
        
        Retorna (penalizacao_mandante, penalizacao_visitante, motivo)
        """
        pen_mandante = 0.0
        pen_visitante = 0.0
        motivo = ""
        
        # Times recém-promovidos da Série B têm estrutura menor
        RECEM_PROMOVIDOS = {
            "REM": 8,   # Remo - estrutura menor, primeiro ano na A
            "MIR": 0,   # Mirassol - campeão B, time organizado
            "CHA": 5,   # Chapecoense
            "JUV": 3,   # Juventude - já oscilou muito
            "SPT": 2,   # Sport - estrutura boa
            "AME": 2,   # América-MG - experiência recente na A
        }
        
        if mandante_abrev in RECEM_PROMOVIDOS:
            pen_mandante = RECEM_PROMOVIDOS[mandante_abrev]
            motivo = f"{mandante_abrev} recém-promovido"
        
        if visitante_abrev in RECEM_PROMOVIDOS:
            pen_visitante = RECEM_PROMOVIDOS[visitante_abrev]
            if motivo:
                motivo += f"; {visitante_abrev} recém-promovido"
            else:
                motivo = f"{visitante_abrev} recém-promovido"
        
        # Diferença grande de posição = time pior tem menos qualidade técnica
        if mandante_pos and visitante_pos:
            diff = abs(mandante_pos - visitante_pos)
            if diff > 10:
                if mandante_pos > visitante_pos:
                    pen_mandante += diff * 0.5
                    if motivo:
                        motivo += f"; {mandante_abrev} muito atrás na tabela"
                else:
                    pen_visitante += diff * 0.5
                    if motivo:
                        motivo += f"; {visitante_abrev} muito atrás na tabela"
        
        return pen_mandante, pen_visitante, motivo
    
    def get_info_time(self, clube_id: int) -> Optional[InfoTime]:
        """Retorna informações em cache de um time"""
        return self.cache_info.get(clube_id)
    
    def get_penalizacao_time(self, clube_id: int) -> float:
        """Retorna penalização de um time"""
        info = self.cache_info.get(clube_id)
        return info.penalizacao if info else 0.0
    
    def exportar_alertas(self) -> List[Dict]:
        """Exporta alertas sobre times com desfalques importantes"""
        alertas = []
        
        for clube_id, info in self.cache_info.items():
            if info.penalizacao > 5:  # Só alertas significativos
                alerta = {
                    "clube_id": clube_id,
                    "clube": info.abrev,
                    "nome": info.nome,
                    "penalizacao": info.penalizacao,
                    "suspensos": info.suspensos,
                    "lesionados": info.lesionados,
                    "duvidas": info.duvidas,
                    "jogando_reservas": info.jogando_reservas,
                    "motivo": info.motivo_reservas,
                }
                alertas.append(alerta)
        
        # Ordenar por penalização
        alertas.sort(key=lambda x: x["penalizacao"], reverse=True)
        
        return alertas


# ============ Funções auxiliares ============

def classificar_forca_time(abrev: str, posicao: int = None) -> str:
    """
    Classifica a força de um time
    
    Returns: "elite", "forte", "medio", "fraco", "rebaixamento"
    """
    # Histórico de força
    ELITE = {"FLA", "PAL", "BOT", "CAM", "INT", "FLU"}
    FORTES = {"SÃO", "COR", "GRE", "CRU", "SAN", "FOR", "BAH"}
    MEDIOS = {"VAS", "BRA", "ATH", "RBB", "CAP", "CEA", "VIT", "CUI"}
    FRACOS = {"MIR", "CFC", "JUV", "SPT", "CHA", "AME", "GOI"}
    REBAIXAMENTO = {"REM"}  # Recém-promovidos com menor estrutura
    
    # Priorizar posição real se disponível
    if posicao:
        if posicao <= 4:
            return "elite"
        elif posicao <= 8:
            return "forte"
        elif posicao <= 14:
            return "medio"
        elif posicao <= 17:
            return "fraco"
        else:
            return "rebaixamento"
    
    # Fallback para classificação histórica
    if abrev in ELITE:
        return "elite"
    elif abrev in FORTES:
        return "forte"
    elif abrev in MEDIOS:
        return "medio"
    elif abrev in FRACOS:
        return "fraco"
    elif abrev in REBAIXAMENTO:
        return "rebaixamento"
    else:
        return "medio"  # Desconhecido = médio


def calcular_bonus_confronto(
    mandante_forca: str,
    visitante_forca: str,
    mandante_pos: int = None,
    visitante_pos: int = None
) -> Tuple[float, float]:
    """
    Calcula bônus/penalidade para cada time no confronto
    
    Returns: (bonus_mandante, bonus_visitante)
    """
    # Tabela de ajuste: diferença de categoria
    AJUSTES = {
        # (mandante, visitante): (bonus_m, bonus_v)
        ("elite", "rebaixamento"): (10, -10),
        ("elite", "fraco"): (7, -5),
        ("elite", "medio"): (4, -2),
        ("elite", "forte"): (2, 0),
        ("elite", "elite"): (0, 0),
        
        ("forte", "rebaixamento"): (8, -8),
        ("forte", "fraco"): (5, -4),
        ("forte", "medio"): (2, -1),
        ("forte", "forte"): (0, 0),
        ("forte", "elite"): (-2, 2),
        
        ("medio", "rebaixamento"): (5, -5),
        ("medio", "fraco"): (3, -2),
        ("medio", "medio"): (0, 0),
        ("medio", "forte"): (-2, 1),
        ("medio", "elite"): (-4, 3),
        
        ("fraco", "rebaixamento"): (3, -3),
        ("fraco", "fraco"): (0, 0),
        ("fraco", "medio"): (-1, 1),
        ("fraco", "forte"): (-4, 3),
        ("fraco", "elite"): (-7, 5),
        
        ("rebaixamento", "rebaixamento"): (0, 0),
        ("rebaixamento", "fraco"): (-2, 2),
        ("rebaixamento", "medio"): (-4, 3),
        ("rebaixamento", "forte"): (-6, 5),
        ("rebaixamento", "elite"): (-10, 8),
    }
    
    key = (mandante_forca, visitante_forca)
    return AJUSTES.get(key, (0, 0))
