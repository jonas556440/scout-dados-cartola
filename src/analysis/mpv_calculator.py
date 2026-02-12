"""
Calculador de Mínimo para Valorizar (MPV) - Cartola FC 2026

VERSÃO v8 - BASEADO EM DADOS REAIS DA RODADA 2

O MPV é a pontuação mínima que um jogador precisa fazer para valorizar.
Jogadores que pontuam ACIMA do MPV tendem a valorizar.
Jogadores que pontuam ABAIXO do MPV tendem a desvalorizar.

TABELA MPV REAL (calculada com dados reais R2 2026):
  C$ 2: ~1.5 pts (62% chance valorizar)
  C$ 3: ~1.5 pts (42%)
  C$ 4: ~2.0 pts (45%)
  C$ 5: ~2.7 pts (44%)
  C$ 6: ~2.9 pts (48%)
  C$ 7: ~3.4 pts (38%)
  C$ 8: ~4.4 pts (31%)
  C$ 9: ~5.0 pts (25%)
  C$10: ~5.0 pts (32%)
  C$12: ~8.0 pts (25%)
  C$15: ~12 pts (33%)
  C$18+: ~13 pts (quase impossível)

A fórmula antiga MPV = (Preço * 2.5) - Média + 2 está ERRADA.
A fórmula real é aproximadamente: MPV ≈ 0.55 * Preço^1.15

DESCOBERTAS CHAVE (dados reais R2 2026):
1. Pontuação da rodada ATUAL é o que define valorização (NOT R1→R2 trend)
2. Cada rodada é INDEPENDENTE (regra 2024+: R2 não herda trend R1)
3. Jogadores baratos (C$2-6) precisam pouquíssimos pontos para valorizar
4. Jogadores caros (C$15+) precisam 12+ pts - quase impossível
5. Quem valorizou: pts média 7.7, preço médio C$6.94
6. Quem desvalorizou: pts média 1.4, preço médio C$7.90
7. ZAG (45%) e TEC (55%) são posições com mais chance de valorizar
"""
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import statistics as stats_lib

sys.path.append(str(Path(__file__).parent.parent.parent))

from config.settings import settings


@dataclass
class AnaliseJogador:
    """Estrutura para análise completa de um jogador"""
    atleta_id: int
    nome: str
    apelido: str
    clube_id: int  # NOVO v3: ID do clube para análise de confronto
    clube_abrev: str
    posicao_abrev: str
    preco: float
    media: float
    mpv: float
    tendencia_valorizar: float  # Probabilidade de valorizar (0-1)
    pontuacao_esperada: float
    risco: str  # "baixo", "medio", "alto"
    variacao: float = 0.0  # NOVO: variação de preço (negativo = desvalorizou)
    pontos_rodada: float = 0.0  # NOVO: pontuação da rodada atual (ao vivo)
    jogos_num: int = 0  # NOVO v7: número de jogos disputados
    status_id: int = 7  # NOVO v7: status do jogador (7=Provável, 6=Nulo, etc)
    scouts_historicos: List[Dict] = field(default_factory=list)
    consistencia: float = 0.0  # 0-100: quanto menor o desvio relativo, mais consistente
    xg_jogador: float = 0.0   # xG individual estimado a partir de finalizações dos scouts
    
    @property
    def margem_seguranca(self) -> float:
        """Diferença entre pontuação esperada e MPV"""
        return self.pontuacao_esperada - self.mpv
    
    @property
    def custo_beneficio(self) -> float:
        """Média dividida pelo preço"""
        return self.media / self.preco if self.preco > 0 else 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "atleta_id": self.atleta_id,
            "nome": self.nome,
            "apelido": self.apelido,
            "clube": self.clube_abrev,
            "posicao": self.posicao_abrev,
            "preco": self.preco,
            "media": self.media,
            "mpv": self.mpv,
            "tendencia_valorizar": self.tendencia_valorizar,
            "pontuacao_esperada": self.pontuacao_esperada,
            "margem_seguranca": self.margem_seguranca,
            "custo_beneficio": self.custo_beneficio,
            "risco": self.risco,
            "consistencia": self.consistencia,
            "xg_jogador": self.xg_jogador,
        }


class MPVCalculator:
    """
    Calculador de Mínimo para Valorizar
    
    Estratégias:
    1. MPV Clássico: Baseado em preço e média
    2. MPV Ajustado: Considera posição, adversário e momento
    3. MPV Histórico: Baseado em performances anteriores
    """
    
    # Fatores de ajuste por posição - v8: BASEADO EM DADOS REAIS R2
    # ZAG e TEC valorizam MAIS que ATA (confirmado por dados)
    AJUSTE_POSICAO = {
        1: -0.3,   # Goleiros: 33% valorizam, MPV mín 3.2
        2: 0.0,    # Laterais: 40% valorizam, MPV mín 2.9
        3: -0.5,   # Zagueiros: 45% valorizam (MELHOR posição linha!) - MPV reduzido
        4: 0.3,    # Meias: 37% valorizam, mais voláteis
        5: 1.5,    # Atacantes: 36% valorizam, precisam MUITO mais pts (avg 9.2!)
        6: -0.8,   # Técnicos: 55% valorizam (MELHOR POSIÇÃO!) - MPV reduzido
    }
    
    # v8: TABELA MPV REAL baseada em dados reais R2 Cartola 2026
    # Formato: (preco_min, preco_max): mpv_real
    # Calculado empiricamente com dados de todos jogadores pontuados R2
    MPV_TABELA_REAL = {
        (0, 2): 0.5,     # C$0-2: quase qualquer pontuação valoriza
        (2, 3): 1.5,     # C$2-3: 1.5 pts para valorizar (62% chance!)
        (3, 4): 1.5,     # C$3-4: mesma faixa
        (4, 5): 2.0,     # C$4-5: 2 pts (45%)
        (5, 6): 2.7,     # C$5-6: ~3 pts (44%)
        (6, 7): 2.9,     # C$6-7: ~3 pts (48%)
        (7, 8): 3.4,     # C$7-8: ~3.5 pts (38%)
        (8, 9): 4.4,     # C$8-9: ~4.5 pts (31%)
        (9, 10): 5.0,    # C$9-10: 5 pts (25%)
        (10, 11): 5.0,   # C$10-11: 5 pts (32%)
        (11, 13): 5.5,   # C$11-13: ~6 pts (25-38%)
        (13, 15): 8.9,   # C$13-15: ~9 pts (25%)
        (15, 18): 12.0,  # C$15-18: ~12 pts (33%)
        (18, 25): 13.0,  # C$18+: impossível valorizar (0-29%)
    }
    
    # v8: Taxa de sucesso de valorização por faixa de preço (dados reais R2)
    TAXA_VALORIZACAO_POR_PRECO = {
        (0, 2): 0.33,    # 33%
        (2, 4): 0.45,    # 45% - SWEET SPOT INFERIOR
        (4, 6): 0.46,    # 46% - SWEET SPOT SUPERIOR  
        (6, 8): 0.40,    # 40% - Ainda razoável
        (8, 10): 0.28,   # 28% - Começou a ficar difícil
        (10, 13): 0.31,  # 31% - Difícil
        (13, 16): 0.50,  # 50% - Amostra pequena (apenas top players)
        (16, 20): 0.29,  # 29% - Muito difícil
        (20, 30): 0.00,  # 0% - Impossível
    }
    
    # v8: Taxa de sucesso por posição (dados reais R2)
    TAXA_VALORIZACAO_POR_POSICAO = {
        1: 0.33,  # GOL: 33%
        2: 0.40,  # LAT: 40%
        3: 0.45,  # ZAG: 45% - Melhor posição de linha!
        4: 0.37,  # MEI: 37%
        5: 0.36,  # ATA: 36%
        6: 0.55,  # TEC: 55% - Melhor posição GERAL!
    }
    
    # Fatores de dificuldade do adversário (1 = fácil, 3 = difícil)
    DIFICULDADE_ADVERSARIO = {
        "facil": 0.9,      # Adversário fraco, jogo fácil
        "medio": 1.0,      # Adversário médio
        "dificil": 1.15,   # Adversário forte
        "classico": 1.2,   # Clássicos e jogos decisivos
    }
    
    # Fator de mando de campo
    FATOR_MANDANTE = 0.95   # Jogar em casa facilita
    FATOR_VISITANTE = 1.05  # Jogar fora dificulta
    
    def __init__(self):
        self.scouts_peso = settings.SCOUTS

    # ==================== SCOUTS ANALYSIS ====================

    def calcular_pontuacao_scout(self, scout_data: Dict[str, Any]) -> float:
        """Calcula pontuação a partir dos scouts usando pesos oficiais do Cartola.
        
        Usa settings.SCOUTS para aplicar os pesos reais de cada scout.
        Exemplo: G=8pts, A=5pts, CA=-1pt, etc.
        
        Args:
            scout_data: Dicionário com scouts {"G": 1, "A": 0, "CA": 1, ...}
        Returns:
            Pontuação total calculada
        """
        pontuacao = 0.0
        for scout_abrev, peso in self.scouts_peso.items():
            valor = scout_data.get(scout_abrev, 0) or 0
            pontuacao += valor * peso
        return round(pontuacao, 2)

    def calcular_xg_jogador(self, scouts_historicos: List[Dict]) -> float:
        """Calcula xG individual do jogador baseado em scouts de finalizações.
        
        Usa taxa de conversão real (gols / finalizações totais) e volume
        recente de finalizações para estimar Expected Goals por jogo.
        
        Args:
            scouts_historicos: Lista de scouts das rodadas anteriores
        Returns:
            xG estimated per game
        """
        if not scouts_historicos:
            return 0.0
        
        total_finalizacoes = 0
        total_gols = 0
        
        for scout in scouts_historicos:
            total_finalizacoes += (
                (scout.get("FD", 0) or 0) +
                (scout.get("FF", 0) or 0) +
                (scout.get("FT", 0) or 0) +
                (scout.get("G", 0) or 0)
            )
            total_gols += scout.get("G", 0) or 0
        
        if total_finalizacoes == 0:
            return 0.0
        
        conversao = total_gols / total_finalizacoes
        
        # Média de finalizações por jogo nas últimas rodadas
        ultimos = scouts_historicos[-5:] if len(scouts_historicos) >= 5 else scouts_historicos
        fins_recentes = sum(
            (s.get("FD", 0) or 0) + (s.get("FF", 0) or 0) +
            (s.get("FT", 0) or 0) + (s.get("G", 0) or 0)
            for s in ultimos
        )
        fins_por_jogo = fins_recentes / max(1, len(ultimos))
        
        return round(fins_por_jogo * conversao, 3)

    def calcular_consistencia(self, scouts_historicos: List[Dict]) -> float:
        """Calcula índice de consistência do jogador (0-100).
        
        Baseado no coeficiente de variação (desvio padrão / média).
        Quanto MENOR o CV, MAIS consistente → score mais alto.
        
        100 = perfeitamente consistente
        0 = extremamente volátil
        
        Args:
            scouts_historicos: Lista de scouts com campo 'pontuacao'
        Returns:
            Índice de consistência (0-100)
        """
        if not scouts_historicos or len(scouts_historicos) < 2:
            return 0.0
        
        pontuacoes = [s.get("pontuacao", 0) for s in scouts_historicos if s.get("pontuacao") is not None]
        if len(pontuacoes) < 2:
            return 0.0
        
        media = sum(pontuacoes) / len(pontuacoes)
        if media <= 0:
            return 0.0
        
        desvio = stats_lib.stdev(pontuacoes)
        cv = desvio / media  # Coeficiente de variação
        
        # Converter para score 0-100 (CV=0 → 100, CV=2 → 0)
        return round(max(0, min(100, 100 - (cv * 50))), 1)
    
    def calcular_mpv_basico(self, preco: float, media: float) -> float:
        """
        Calcula o MPV básico usando tabela REAL (dados R2 2026)
        
        VERSÃO v8: Substituiu fórmula teórica por tabela empírica.
        
        A fórmula antiga (Preço * 2.5 - Média + 2) produzia MPVs absurdos:
        - Jogador C$8 media 6: MPV = 16 pts (IMPOSSÍVEL!) 
        - Real: MPV ≈ 4.4 pts
        
        Nova fórmula baseada em regressão dos dados reais:
        MPV ≈ 0.55 * Preço^1.15 (para preço > 2)
        
        Para preços extremos, cai na tabela direta.
        
        Args:
            preco: Preço atual do jogador em cartoletas
            media: Média de pontos do jogador (NÃO usado no cálculo - MPV depende só do preço!)
            
        Returns:
            Pontuação mínima para valorizar
        """
        # Usar tabela real primeiro
        for (pmin, pmax), mpv in self.MPV_TABELA_REAL.items():
            if pmin <= preco < pmax:
                return round(mpv, 2)
        
        # Para preços fora da tabela (> C$25), usar fórmula de regressão
        if preco >= 25:
            return round(0.55 * (preco ** 1.15), 2)
        
        # Fallback para preço 0 ou negativo
        return 0.0
    
    def calcular_mpv_ajustado(
        self, 
        preco: float, 
        media: float,
        posicao_id: int,
        mandante: bool = True,
        dificuldade_adversario: str = "medio"
    ) -> float:
        """
        Calcula MPV com ajustes por posição, mando e adversário
        
        Args:
            preco: Preço atual do jogador
            media: Média de pontos
            posicao_id: ID da posição (1-6)
            mandante: Se está jogando em casa
            dificuldade_adversario: "facil", "medio", "dificil", "classico"
            
        Returns:
            MPV ajustado
        """
        mpv_base = self.calcular_mpv_basico(preco, media)
        
        # Ajuste por posição
        ajuste_pos = self.AJUSTE_POSICAO.get(posicao_id, 0)
        
        # Ajuste por mando
        fator_mando = self.FATOR_MANDANTE if mandante else self.FATOR_VISITANTE
        
        # Ajuste por adversário
        fator_adversario = self.DIFICULDADE_ADVERSARIO.get(dificuldade_adversario, 1.0)
        
        # Aplicar ajustes
        mpv_ajustado = (mpv_base + ajuste_pos) * fator_mando * fator_adversario
        
        return round(max(0, mpv_ajustado), 2)
    
    def estimar_pontuacao(
        self,
        media: float,
        scouts_historicos: List[Dict] = None,
        posicao_id: int = 4,
        mandante: bool = True,
        dificuldade_adversario: str = "medio",
        preco: float = 0.0
    ) -> float:
        """
        Estima a pontuação esperada do jogador
        
        Considera:
        - Média histórica (peso 40%)
        - Últimas 3 rodadas (peso 30%)
        - Última rodada (peso 20%)
        - Contexto do jogo (peso 10%)
        
        Returns:
            Pontuação estimada
        """
        if not scouts_historicos:
            # Sem histórico, usar apenas média com ajustes
            base = media
            # Fallback para R1: sem jogos disputados, média=0
            if base == 0:
                # Estimar com base no preço (proxy de qualidade)
                if preco > 0:
                    base = preco * 0.5
                else:
                    base = 3.0  # Pontuação mínima razoável
        else:
            # Ponderar histórico
            ultimas_pontuacoes = [s.get("pontuacao", 0) for s in scouts_historicos[:5]]
            
            if len(ultimas_pontuacoes) >= 3:
                media_3 = sum(ultimas_pontuacoes[:3]) / 3
                ultima = ultimas_pontuacoes[0]
                base = (media * 0.4) + (media_3 * 0.3) + (ultima * 0.2) + (media * 0.1)
            elif len(ultimas_pontuacoes) >= 1:
                ultima = ultimas_pontuacoes[0]
                base = (media * 0.6) + (ultima * 0.4)
            else:
                base = media
        
        # Ajustes contextuais
        ajuste_pos = self.AJUSTE_POSICAO.get(posicao_id, 0) * 0.3
        fator_mando = 1.05 if mandante else 0.95
        fator_adversario = 1.0 / self.DIFICULDADE_ADVERSARIO.get(dificuldade_adversario, 1.0)
        
        pontuacao_esperada = (base + ajuste_pos) * fator_mando * fator_adversario
        
        return round(pontuacao_esperada, 2)
    
    def calcular_tendencia_valorizar(
        self,
        pontuacao_esperada: float,
        mpv: float,
        preco: float = 5.0,
        posicao_id: int = 4
    ) -> float:
        """
        Calcula a probabilidade de o jogador valorizar
        
        VERSÃO v8: Usa dados reais de taxa de sucesso por preço E posição.
        
        A taxa base vem da faixa de preço (dados reais R2).
        A diferença pontuação-MPV modula a probabilidade para cima ou para baixo.
        
        Args:
            pontuacao_esperada: Pontuação estimada do jogador
            mpv: MPV calculado (baseado no preço)
            preco: Preço atual (para taxa base)
            posicao_id: Posição do jogador
            
        Returns:
            Probabilidade entre 0 e 1
        """
        # Taxa base pela faixa de preço (dados reais R2)
        taxa_base = 0.35  # default
        for (pmin, pmax), taxa in self.TAXA_VALORIZACAO_POR_PRECO.items():
            if pmin <= preco < pmax:
                taxa_base = taxa
                break
        
        # Ajuste pela posição (dados reais R2)
        taxa_posicao = self.TAXA_VALORIZACAO_POR_POSICAO.get(posicao_id, 0.37)
        
        # Combinar taxa base de preço com taxa de posição (60/40)
        taxa_combinada = taxa_base * 0.6 + taxa_posicao * 0.4
        
        # Modular pela diferença pontuação vs MPV
        diferenca = pontuacao_esperada - mpv
        
        if diferenca >= 5:
            # Muito acima do MPV: quase certo valorizar
            return min(0.95, taxa_combinada + 0.40)
        elif diferenca >= 3:
            return min(0.90, taxa_combinada + 0.25)
        elif diferenca >= 1:
            return min(0.80, taxa_combinada + 0.10)
        elif diferenca >= 0:
            # Exatamente no MPV: chance ~50/50
            return taxa_combinada
        elif diferenca >= -2:
            return max(0.10, taxa_combinada - 0.15)
        elif diferenca >= -4:
            return max(0.05, taxa_combinada - 0.25)
        else:
            # Muito abaixo do MPV: quase impossível
            return max(0.02, taxa_combinada - 0.35)
    
    def determinar_risco(
        self,
        preco: float,
        media: float,
        jogos_num: int,
        variacao_recente: float = 0,
        rodada_atual: int = 1
    ) -> str:
        """
        Determina o nível de risco de escalar o jogador
        
        VERSÃO v7 - Penaliza mais jogadores sem jogos na R2+
        
        Fatores:
        - Consistência (desvio padrão)
        - Número de jogos (MUITO mais importante na R2+)
        - Variação de preço recente
        
        Returns:
            "baixo", "medio", ou "alto"
        """
        risco_score = 0
        
        # v7.1: Calcular participação relativa ao máximo possível
        # Na R3 o max de jogos é 2 (rodadas 1 e 2 disputadas)
        rodadas_disputadas = max(rodada_atual - 1, 0)
        
        # Poucos jogos = mais risco (relativo às rodadas disputadas)
        if jogos_num == 0:
            if rodadas_disputadas >= 2:
                risco_score += 4  # Nunca jogou em 2+ rodadas = muito arriscado
            elif rodadas_disputadas == 1:
                risco_score += 3  # Não jogou na única rodada que teve
            else:
                risco_score += 1  # R1: normal, ninguém jogou ainda
        elif rodadas_disputadas > 0:
            # Calcular taxa de participação
            taxa_participacao = jogos_num / rodadas_disputadas
            if taxa_participacao < 0.5:
                risco_score += 2  # Jogou menos da metade das rodadas
            elif taxa_participacao < 0.75:
                risco_score += 1  # Jogou a maioria mas não todas
        
        # Média baixa com preço alto = risco (v7: skip na R1 onde todos têm media=0)
        if preco > 0 and media / preco < 0.5 and (rodada_atual >= 2 or media > 0):
            risco_score += 1
        
        # v7: Média muito baixa na R2+ = risco alto (jogou e foi mal)
        if rodada_atual >= 2 and jogos_num >= 1 and media < 1.5:
            risco_score += 2
        
        # Desvalorização recente = risco
        if variacao_recente < -1:
            risco_score += 1
        
        if risco_score >= 3:
            return "alto"
        elif risco_score >= 1:
            return "medio"
        else:
            return "baixo"
    
    def analisar_jogador(
        self,
        atleta_data: Dict[str, Any],
        clube_abrev: str = "???",
        posicao_abrev: str = "???",
        scouts_historicos: List[Dict] = None,
        mandante: bool = True,
        dificuldade_adversario: str = "medio",
        rodada_atual: int = 1
    ) -> AnaliseJogador:
        """
        Análise completa de um jogador para escalação
        
        VERSÃO v7 - Recebe rodada_atual para ajustar riscos
        
        Args:
            atleta_data: Dados do atleta da API
            clube_abrev: Abreviação do clube
            posicao_abrev: Abreviação da posição
            scouts_historicos: Lista de scouts anteriores
            mandante: Se joga em casa
            dificuldade_adversario: Nível de dificuldade
            rodada_atual: Número da rodada atual (1+)
            
        Returns:
            AnaliseJogador com todos os dados calculados
        """
        atleta_id = atleta_data.get("atleta_id", 0)
        nome = atleta_data.get("nome", "")
        apelido = atleta_data.get("apelido", "")
        preco = atleta_data.get("preco_num", 0.0)
        media = atleta_data.get("media_num", 0.0)
        posicao_id = atleta_data.get("posicao_id", 4)
        jogos_num = atleta_data.get("jogos_num", 0)
        variacao = atleta_data.get("variacao_num", 0.0)
        clube_id = atleta_data.get("clube_id", 0)  # NOVO v3
        
        # Calcular MPV
        mpv = self.calcular_mpv_ajustado(
            preco, media, posicao_id, mandante, dificuldade_adversario
        )
        
        # Estimar pontuação
        pontuacao_esperada = self.estimar_pontuacao(
            media, scouts_historicos, posicao_id, mandante, dificuldade_adversario, preco
        )
        
        # Calcular tendência (v8: agora usa preço e posição)
        tendencia = self.calcular_tendencia_valorizar(
            pontuacao_esperada, mpv, preco, posicao_id
        )
        
        # Determinar risco (v7: com rodada_atual)
        risco = self.determinar_risco(preco, media, jogos_num, variacao, rodada_atual)

        # Calcular consistência e xG individual a partir de scouts
        consistencia = self.calcular_consistencia(scouts_historicos) if scouts_historicos else 0.0
        xg_jogador = self.calcular_xg_jogador(scouts_historicos) if scouts_historicos else 0.0
        
        return AnaliseJogador(
            atleta_id=atleta_id,
            nome=nome,
            apelido=apelido,
            clube_id=clube_id,
            clube_abrev=clube_abrev,
            posicao_abrev=posicao_abrev,
            preco=preco,
            media=media,
            mpv=mpv,
            tendencia_valorizar=tendencia,
            pontuacao_esperada=pontuacao_esperada,
            risco=risco,
            variacao=variacao,
            jogos_num=jogos_num,
            status_id=atleta_data.get("status_id", 7),
            scouts_historicos=scouts_historicos or [],
            consistencia=consistencia,
            xg_jogador=xg_jogador,
        )
    
    def filtrar_valorizadores(
        self,
        analises: List[AnaliseJogador],
        min_tendencia: float = 0.5,
        max_risco: str = "alto"
    ) -> List[AnaliseJogador]:
        """
        Filtra jogadores com potencial de valorização
        
        Args:
            analises: Lista de análises de jogadores
            min_tendencia: Tendência mínima para considerar (0-1)
            max_risco: Risco máximo aceitável
            
        Returns:
            Lista filtrada e ordenada por potencial
        """
        riscos_ordem = {"baixo": 1, "medio": 2, "alto": 3}
        max_risco_valor = riscos_ordem.get(max_risco, 3)
        
        filtrados = [
            a for a in analises
            if a.tendencia_valorizar >= min_tendencia
            and riscos_ordem.get(a.risco, 3) <= max_risco_valor
        ]
        
        # Ordenar por margem de segurança (pontuação esperada - MPV)
        filtrados.sort(key=lambda x: x.margem_seguranca, reverse=True)
        
        return filtrados


# Instância global
mpv_calculator = MPVCalculator()


if __name__ == "__main__":
    # Exemplo de uso
    calc = MPVCalculator()
    
    # Jogador exemplo
    jogador = {
        "atleta_id": 123,
        "nome": "Alan Patrick da Silva",
        "apelido": "Alan Patrick",
        "preco_num": 8.0,
        "media_num": 6.5,
        "posicao_id": 4,
        "jogos_num": 10,
        "variacao_num": 0.5
    }
    
    analise = calc.analisar_jogador(
        jogador,
        clube_abrev="INT",
        posicao_abrev="MEI",
        mandante=True,
        dificuldade_adversario="medio"
    )
    
    print(f"📊 Análise: {analise.apelido} ({analise.clube_abrev})")
    print(f"   Preço: C$ {analise.preco}")
    print(f"   Média: {analise.media}")
    print(f"   MPV: {analise.mpv}")
    print(f"   Pont. Esperada: {analise.pontuacao_esperada}")
    print(f"   Tendência Valorizar: {analise.tendencia_valorizar:.0%}")
    print(f"   Margem Segurança: {analise.margem_seguranca}")
    print(f"   Risco: {analise.risco}")
