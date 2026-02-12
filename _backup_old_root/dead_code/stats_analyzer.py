"""
Analisador de Estatísticas - Cartola FC 2026

Análise profunda de dados históricos para tomada de decisão.
Inclui análise de scouts, tendências e padrões de performance.
"""
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime, timedelta
import statistics

sys.path.append(str(Path(__file__).parent.parent.parent))

from config.settings import settings


@dataclass
class EstatisticasJogador:
    """Estatísticas completas de um jogador"""
    atleta_id: int
    apelido: str
    posicao: str
    clube: str
    
    # Básicas
    jogos: int
    pontuacao_total: float
    media: float
    preco_atual: float
    
    # Avançadas
    desvio_padrao: float
    maior_pontuacao: float
    menor_pontuacao: float
    
    # Scouts agregados
    gols: int = 0
    assistencias: int = 0
    saldo_gols: int = 0
    defesas_dificeis: int = 0
    desarmes: int = 0
    cartoes_amarelos: int = 0
    cartoes_vermelhos: int = 0
    
    # Tendência
    tendencia: str = "estavel"  # "subindo", "descendo", "estavel"
    valorizacao_acumulada: float = 0.0
    
    @property
    def consistencia(self) -> float:
        """Índice de consistência (quanto menor o desvio, mais consistente)"""
        if self.media > 0:
            return max(0, 100 - (self.desvio_padrao / self.media * 100))
        return 0
    
    @property
    def gols_por_jogo(self) -> float:
        """Média de gols por jogo"""
        return self.gols / self.jogos if self.jogos > 0 else 0
    
    @property
    def participacoes_gol(self) -> int:
        """Gols + Assistências"""
        return self.gols + self.assistencias
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "atleta_id": self.atleta_id,
            "apelido": self.apelido,
            "posicao": self.posicao,
            "clube": self.clube,
            "jogos": self.jogos,
            "pontuacao_total": self.pontuacao_total,
            "media": self.media,
            "preco_atual": self.preco_atual,
            "desvio_padrao": self.desvio_padrao,
            "consistencia": self.consistencia,
            "maior_pontuacao": self.maior_pontuacao,
            "menor_pontuacao": self.menor_pontuacao,
            "gols": self.gols,
            "assistencias": self.assistencias,
            "tendencia": self.tendencia,
        }


@dataclass
class AnaliseClube:
    """Análise agregada de um clube"""
    clube_id: int
    nome: str
    abreviacao: str
    
    # Scouts do time
    gols_marcados: int = 0
    gols_sofridos: int = 0
    saldo_gols_rodada: int = 0
    
    # Médias
    media_pontos_ataque: float = 0.0
    media_pontos_defesa: float = 0.0
    media_pontos_geral: float = 0.0
    
    # Jogadores destaque
    artilheiro: str = ""
    melhor_media: str = ""
    
    # Performance
    jogos_sem_sofrer_gol: int = 0
    sequencia_vitorias: int = 0


class StatsAnalyzer:
    """
    Analisador avançado de estatísticas
    
    Funcionalidades:
    - Calcular estatísticas individuais
    - Identificar tendências
    - Comparar jogadores
    - Analisar clubes
    - Prever performances
    """
    
    def __init__(self):
        self.scouts_config = settings.SCOUTS
    
    def calcular_estatisticas_jogador(
        self,
        atleta_data: Dict[str, Any],
        scouts_historicos: List[Dict[str, Any]] = None
    ) -> EstatisticasJogador:
        """
        Calcula estatísticas completas de um jogador
        
        Args:
            atleta_data: Dados do atleta
            scouts_historicos: Lista de scouts das rodadas anteriores
            
        Returns:
            EstatisticasJogador com todas as métricas
        """
        atleta_id = atleta_data.get("atleta_id", 0)
        apelido = atleta_data.get("apelido", "")
        posicao = settings.POSICOES.get(atleta_data.get("posicao_id", 0), {}).get("abrev", "???")
        clube = atleta_data.get("clube_abrev", "???")
        jogos = atleta_data.get("jogos_num", 0)
        pontuacao_total = atleta_data.get("pontos_num", 0.0)
        media = atleta_data.get("media_num", 0.0)
        preco = atleta_data.get("preco_num", 0.0)
        
        # Calcular a partir de scouts históricos
        pontuacoes = []
        gols = 0
        assistencias = 0
        saldo_gols = 0
        defesas_dificeis = 0
        desarmes = 0
        cartoes_amarelos = 0
        cartoes_vermelhos = 0
        
        if scouts_historicos:
            for scout in scouts_historicos:
                pontuacoes.append(scout.get("pontuacao", 0))
                gols += scout.get("G", 0) or scout.get("gol", 0) or 0
                assistencias += scout.get("A", 0) or scout.get("assistencia", 0) or 0
                saldo_gols += scout.get("SG", 0) or scout.get("saldo_gols", 0) or 0
                defesas_dificeis += scout.get("DD", 0) or scout.get("defesa_dificil", 0) or 0
                desarmes += scout.get("DS", 0) or scout.get("desarme", 0) or 0
                cartoes_amarelos += scout.get("CA", 0) or scout.get("cartao_amarelo", 0) or 0
                cartoes_vermelhos += scout.get("CV", 0) or scout.get("cartao_vermelho", 0) or 0
        
        # Estatísticas básicas
        if pontuacoes:
            desvio_padrao = statistics.stdev(pontuacoes) if len(pontuacoes) > 1 else 0
            maior = max(pontuacoes)
            menor = min(pontuacoes)
        else:
            desvio_padrao = 0
            maior = 0
            menor = 0
        
        # Tendência
        tendencia = self._calcular_tendencia(pontuacoes)
        
        # Valorização acumulada
        variacao = atleta_data.get("variacao_num", 0.0)
        
        return EstatisticasJogador(
            atleta_id=atleta_id,
            apelido=apelido,
            posicao=posicao,
            clube=clube,
            jogos=jogos,
            pontuacao_total=pontuacao_total,
            media=media,
            preco_atual=preco,
            desvio_padrao=round(desvio_padrao, 2),
            maior_pontuacao=maior,
            menor_pontuacao=menor,
            gols=gols,
            assistencias=assistencias,
            saldo_gols=saldo_gols,
            defesas_dificeis=defesas_dificeis,
            desarmes=desarmes,
            cartoes_amarelos=cartoes_amarelos,
            cartoes_vermelhos=cartoes_vermelhos,
            tendencia=tendencia,
            valorizacao_acumulada=variacao
        )
    
    def _calcular_tendencia(self, pontuacoes: List[float], janela: int = 3) -> str:
        """
        Calcula tendência baseada nas últimas pontuações
        
        Args:
            pontuacoes: Lista de pontuações (mais recente primeiro)
            janela: Número de rodadas para análise
            
        Returns:
            "subindo", "descendo" ou "estavel"
        """
        if len(pontuacoes) < janela:
            return "estavel"
        
        recentes = pontuacoes[:janela]
        media_recente = sum(recentes) / len(recentes)
        
        anteriores = pontuacoes[janela:janela*2] if len(pontuacoes) >= janela*2 else pontuacoes[janela:]
        if not anteriores:
            return "estavel"
        
        media_anterior = sum(anteriores) / len(anteriores)
        
        diferenca = media_recente - media_anterior
        
        if diferenca > 1:
            return "subindo"
        elif diferenca < -1:
            return "descendo"
        else:
            return "estavel"
    
    def comparar_jogadores(
        self,
        jogadores: List[EstatisticasJogador],
        criterio: str = "media"
    ) -> List[Tuple[int, EstatisticasJogador]]:
        """
        Compara jogadores e retorna ranking
        
        Args:
            jogadores: Lista de estatísticas de jogadores
            criterio: "media", "consistencia", "gols", "custo_beneficio"
            
        Returns:
            Lista de tuplas (posição, jogador) ordenada
        """
        if criterio == "media":
            key_func = lambda x: x.media
        elif criterio == "consistencia":
            key_func = lambda x: x.consistencia
        elif criterio == "gols":
            key_func = lambda x: x.gols
        elif criterio == "custo_beneficio":
            key_func = lambda x: x.media / x.preco_atual if x.preco_atual > 0 else 0
        else:
            key_func = lambda x: x.media
        
        ordenados = sorted(jogadores, key=key_func, reverse=True)
        return list(enumerate(ordenados, 1))
    
    def calcular_pontuacao_scout(self, scout_data: Dict[str, Any]) -> float:
        """
        Calcula pontuação a partir dos scouts
        
        Args:
            scout_data: Dicionário com scouts
            
        Returns:
            Pontuação total calculada
        """
        pontuacao = 0.0
        
        for scout_abrev, peso in self.scouts_config.items():
            valor = scout_data.get(scout_abrev, 0) or 0
            pontuacao += valor * peso
        
        return round(pontuacao, 2)
    
    def analisar_aproveitamento_posicao(
        self,
        jogadores: List[EstatisticasJogador]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Analisa estatísticas agregadas por posição
        
        Args:
            jogadores: Lista de estatísticas de jogadores
            
        Returns:
            Dicionário com análise por posição
        """
        por_posicao = defaultdict(list)
        for jog in jogadores:
            por_posicao[jog.posicao].append(jog)
        
        resultado = {}
        for posicao, lista in por_posicao.items():
            medias = [j.media for j in lista]
            precos = [j.preco_atual for j in lista]
            
            resultado[posicao] = {
                "quantidade": len(lista),
                "media_geral": round(sum(medias) / len(medias), 2) if medias else 0,
                "preco_medio": round(sum(precos) / len(precos), 2) if precos else 0,
                "melhor_media": max(lista, key=lambda x: x.media).apelido if lista else "",
                "melhor_cb": max(lista, key=lambda x: x.media/x.preco_atual if x.preco_atual > 0 else 0).apelido if lista else "",
            }
        
        return resultado
    
    def identificar_jogadores_quentes(
        self,
        jogadores: List[EstatisticasJogador],
        limite: int = 10
    ) -> List[EstatisticasJogador]:
        """
        Identifica jogadores em boa fase
        
        Critérios:
        - Tendência subindo
        - Alta consistência
        - Valorização positiva
        
        Returns:
            Lista dos jogadores mais quentes
        """
        quentes = [
            j for j in jogadores
            if j.tendencia == "subindo" or j.consistencia > 70
        ]
        
        # Ordenar por combinação de fatores
        quentes.sort(
            key=lambda x: (
                1 if x.tendencia == "subindo" else 0,
                x.consistencia,
                x.media
            ),
            reverse=True
        )
        
        return quentes[:limite]
    
    def identificar_jogadores_frios(
        self,
        jogadores: List[EstatisticasJogador],
        limite: int = 10
    ) -> List[EstatisticasJogador]:
        """
        Identifica jogadores em má fase (evitar)
        
        Returns:
            Lista dos jogadores a evitar
        """
        frios = [
            j for j in jogadores
            if j.tendencia == "descendo" or j.consistencia < 30
        ]
        
        frios.sort(key=lambda x: x.consistencia)
        
        return frios[:limite]
    
    def sugerir_valorizadores(
        self,
        jogadores: List[EstatisticasJogador],
        preco_maximo: float = 10.0,
        limite: int = 20
    ) -> List[EstatisticasJogador]:
        """
        Sugere jogadores com potencial de valorização
        
        Critérios:
        - Preço baixo
        - Tendência subindo ou estável
        - Boa consistência
        - Custo-benefício alto
        
        Returns:
            Lista de potenciais valorizadores
        """
        candidatos = [
            j for j in jogadores
            if j.preco_atual <= preco_maximo
            and j.tendencia != "descendo"
            and j.media > 0
        ]
        
        # Score de valorização
        def score_valorizacao(j: EstatisticasJogador) -> float:
            cb = j.media / j.preco_atual if j.preco_atual > 0 else 0
            tendencia_bonus = 1.2 if j.tendencia == "subindo" else 1.0
            consistencia_bonus = 1 + (j.consistencia / 200)
            return cb * tendencia_bonus * consistencia_bonus
        
        candidatos.sort(key=score_valorizacao, reverse=True)
        
        return candidatos[:limite]
    
    def gerar_relatorio_rodada(
        self,
        jogadores_pontuados: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Gera relatório completo de uma rodada finalizada
        
        Args:
            jogadores_pontuados: Lista com pontuações da rodada
            
        Returns:
            Relatório com destaques e estatísticas
        """
        if not jogadores_pontuados:
            return {}
        
        pontuacoes = [j.get("pontuacao", 0) for j in jogadores_pontuados]
        
        # Estatísticas gerais
        relatorio = {
            "total_jogadores": len(jogadores_pontuados),
            "media_geral": round(sum(pontuacoes) / len(pontuacoes), 2) if pontuacoes else 0,
            "maior_pontuacao": max(pontuacoes) if pontuacoes else 0,
            "menor_pontuacao": min(pontuacoes) if pontuacoes else 0,
            "jogadores_negativos": sum(1 for p in pontuacoes if p < 0),
            "jogadores_zerados": sum(1 for p in pontuacoes if p == 0),
        }
        
        # Top 10
        ordenados = sorted(jogadores_pontuados, key=lambda x: x.get("pontuacao", 0), reverse=True)
        relatorio["top_10"] = [
            {
                "atleta_id": j.get("atleta_id"),
                "apelido": j.get("apelido", ""),
                "pontuacao": j.get("pontuacao", 0)
            }
            for j in ordenados[:10]
        ]
        
        # Flops
        relatorio["flops_5"] = [
            {
                "atleta_id": j.get("atleta_id"),
                "apelido": j.get("apelido", ""),
                "pontuacao": j.get("pontuacao", 0)
            }
            for j in ordenados[-5:]
        ]
        
        return relatorio


# Instância global
stats_analyzer = StatsAnalyzer()


if __name__ == "__main__":
    # Exemplo de uso
    analyzer = StatsAnalyzer()
    
    # Dados de teste
    atleta = {
        "atleta_id": 123,
        "apelido": "Alan Patrick",
        "posicao_id": 4,
        "clube_abrev": "INT",
        "jogos_num": 10,
        "pontos_num": 65.0,
        "media_num": 6.5,
        "preco_num": 8.0,
        "variacao_num": 0.5
    }
    
    scouts = [
        {"pontuacao": 8.5, "G": 1, "A": 0},
        {"pontuacao": 5.2, "G": 0, "A": 1},
        {"pontuacao": 7.8, "G": 1, "A": 0},
        {"pontuacao": 4.1, "G": 0, "A": 0},
        {"pontuacao": 6.9, "G": 0, "A": 1},
    ]
    
    stats = analyzer.calcular_estatisticas_jogador(atleta, scouts)
    
    print(f"📊 Estatísticas: {stats.apelido}")
    print(f"   Posição: {stats.posicao}")
    print(f"   Média: {stats.media}")
    print(f"   Desvio Padrão: {stats.desvio_padrao}")
    print(f"   Consistência: {stats.consistencia:.1f}%")
    print(f"   Tendência: {stats.tendencia}")
    print(f"   Gols: {stats.gols}")
    print(f"   Assistências: {stats.assistencias}")
