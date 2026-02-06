"""
Calculador de Mínimo para Valorizar (MPV) - Cartola FC 2026

O MPV é a pontuação mínima que um jogador precisa fazer para valorizar.
Jogadores que pontuam ACIMA do MPV tendem a valorizar.
Jogadores que pontuam ABAIXO do MPV tendem a desvalorizar.

Fórmula aproximada:
MPV = (Preço * 2.5) - Média + 2

Variações por posição e contexto do jogo também influenciam.
"""
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

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
    scouts_historicos: List[Dict] = field(default_factory=list)
    
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
        }


class MPVCalculator:
    """
    Calculador de Mínimo para Valorizar
    
    Estratégias:
    1. MPV Clássico: Baseado em preço e média
    2. MPV Ajustado: Considera posição, adversário e momento
    3. MPV Histórico: Baseado em performances anteriores
    """
    
    # Fatores de ajuste por posição
    AJUSTE_POSICAO = {
        1: -0.5,   # Goleiros: mais fácil manter SG
        2: 0.0,    # Laterais
        3: 0.0,    # Zagueiros
        4: 0.5,    # Meias: mais volatilidade
        5: 1.0,    # Atacantes: dependem de gols
        6: -1.0,   # Técnicos: pontuação diferente
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
    
    def calcular_mpv_basico(self, preco: float, media: float) -> float:
        """
        Calcula o MPV básico usando a fórmula clássica
        
        MPV = (Preço * 2.5) - Média + 2
        
        Args:
            preco: Preço atual do jogador em cartoletas
            media: Média de pontos do jogador
            
        Returns:
            Pontuação mínima para valorizar
        """
        mpv = (preco * 2.5) - media + 2
        return round(max(0, mpv), 2)
    
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
        dificuldade_adversario: str = "medio"
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
        mpv: float
    ) -> float:
        """
        Calcula a probabilidade de o jogador valorizar
        
        Returns:
            Probabilidade entre 0 e 1
        """
        diferenca = pontuacao_esperada - mpv
        
        if diferenca >= 5:
            return 0.90
        elif diferenca >= 3:
            return 0.75
        elif diferenca >= 1:
            return 0.60
        elif diferenca >= 0:
            return 0.50
        elif diferenca >= -2:
            return 0.35
        elif diferenca >= -4:
            return 0.20
        else:
            return 0.10
    
    def determinar_risco(
        self,
        preco: float,
        media: float,
        jogos_num: int,
        variacao_recente: float = 0
    ) -> str:
        """
        Determina o nível de risco de escalar o jogador
        
        Fatores:
        - Consistência (desvio padrão)
        - Número de jogos
        - Variação de preço recente
        
        Returns:
            "baixo", "medio", ou "alto"
        """
        risco_score = 0
        
        # Poucos jogos = mais risco
        if jogos_num < 3:
            risco_score += 2
        elif jogos_num < 5:
            risco_score += 1
        
        # Média baixa com preço alto = risco
        if preco > 0 and media / preco < 0.5:
            risco_score += 1
        
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
        dificuldade_adversario: str = "medio"
    ) -> AnaliseJogador:
        """
        Análise completa de um jogador para escalação
        
        Args:
            atleta_data: Dados do atleta da API
            clube_abrev: Abreviação do clube
            posicao_abrev: Abreviação da posição
            scouts_historicos: Lista de scouts anteriores
            mandante: Se joga em casa
            dificuldade_adversario: Nível de dificuldade
            
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
            media, scouts_historicos, posicao_id, mandante, dificuldade_adversario
        )
        
        # Calcular tendência
        tendencia = self.calcular_tendencia_valorizar(pontuacao_esperada, mpv)
        
        # Determinar risco
        risco = self.determinar_risco(preco, media, jogos_num, variacao)
        
        return AnaliseJogador(
            atleta_id=atleta_id,
            nome=nome,
            apelido=apelido,
            clube_id=clube_id,  # NOVO v3
            clube_abrev=clube_abrev,
            posicao_abrev=posicao_abrev,
            preco=preco,
            media=media,
            mpv=mpv,
            tendencia_valorizar=tendencia,
            pontuacao_esperada=pontuacao_esperada,
            risco=risco,
            variacao=variacao,  # NOVO: passar variação
            scouts_historicos=scouts_historicos or []
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
