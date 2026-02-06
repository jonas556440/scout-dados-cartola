"""
Seletor de Times - Cartola FC 2026

Gera dois times por rodada:
1. Time Valorização: Jogadores com potencial de ganhar MAIS CARTOLETAS (otimizado!)
2. Time Pontuação: Jogadores para pontuar máximo

VERSÃO v8 - BASEADO EM DADOS REAIS R2 CARTOLA 2026:

Descobertas que fundamentam esta versão:
1. MPV REAL extraído da R2:
   C$2=1.5pts, C$5=2.7pts, C$8=4.4pts, C$10=5.0pts, C$15=12pts
   (fórmula antiga Preço*2.5-Média+2 era absurdamente errada)

2. Cada rodada é INDEPENDENTE (regra 2024+):
   R1 performance NÃO prediz R2 valorização (29% taxa para ambos bons e ruins R1)
   
3. Sweet spot CONFIRMADO: C$2-6
   C$2-4: 45-62% chance valorizar (MPV=1.5pts)
   C$4-6: 44-46% chance (MPV=2-2.7pts)
   C$8-10: 25-31% chance (MPV=4.4-5pts) 
   C$13+: 25% chance (MPV=9+pts)
   C$20+: 0% chance

4. Posições (taxa de valorização):
   TEC: 55% (MELHOR!) | ZAG: 45% | LAT: 40% | MEI: 37% | ATA: 36% | GOL: 33%
   ATA precisa avg 9.2pts para valorizar vs ZAG 5.3pts!

5. Perfil dos valorizados R2:
   Pts média=7.7, Preço médio=C$6.94
   Perfil dos desvalorizados:
   Pts média=1.4, Preço médio=C$7.90
"""
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

sys.path.append(str(Path(__file__).parent.parent.parent))

from config.settings import settings
from src.analysis.mpv_calculator import MPVCalculator, AnaliseJogador
from src.analysis.match_analyzer import MatchAnalyzer, Confronto


@dataclass
class TimeEscalado:
    """Estrutura para um time escalado"""
    tipo: str  # "valorizacao" ou "pontuacao"
    esquema: str
    titulares: List[AnaliseJogador]
    capitao: AnaliseJogador
    reservas: List[AnaliseJogador]
    custo_total: float
    cartoletas_restantes: float
    pontuacao_prevista: float
    valorizacao_esperada: float
    
    # NOVO v3: Informações de confronto
    analise_confrontos: Dict[int, Dict] = field(default_factory=dict)  # clube_id -> resumo confronto
    
    def get_por_posicao(self) -> Dict[str, List[AnaliseJogador]]:
        """Agrupa titulares por posição"""
        resultado = defaultdict(list)
        for atleta in self.titulares:
            resultado[atleta.posicao_abrev].append(atleta)
        return dict(resultado)
    
    def get_confronto_jogador(self, atleta: AnaliseJogador) -> Optional[Dict]:
        """Retorna informações do confronto para um jogador"""
        return self.analise_confrontos.get(atleta.clube_id)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            "tipo": self.tipo,
            "esquema": self.esquema,
            "titulares": [t.to_dict() for t in self.titulares],
            "capitao_id": self.capitao.atleta_id,
            "reservas": [r.to_dict() for r in self.reservas],
            "custo_total": self.custo_total,
            "cartoletas_restantes": self.cartoletas_restantes,
            "pontuacao_prevista": self.pontuacao_prevista,
            "valorizacao_esperada": self.valorizacao_esperada,
            "analise_confrontos": self.analise_confrontos,
        }


class TeamSelector:
    """
    Seletor inteligente de times para o Cartola FC
    
    VERSÃO v3 - ANÁLISE COMPLETA DE CONFRONTOS
    
    Fatores considerados:
    1. Estatísticas do jogador (média, scouts, tendência)
    2. NOVO: Adversário da rodada (força ofensiva/defensiva)
    3. NOVO: Mando de campo (casa = +30% performance histórica)
    4. NOVO: Forma recente do time (últimos 5 jogos)
    5. NOVO: Chance de SG para defensores
    6. NOVO: Expectativa de gols para atacantes
    
    Como sites especializados (Cartola PFC, Gato Mestre, etc):
    - Analisa todos os confrontos da rodada
    - Prioriza jogadores com confrontos favoráveis
    - Considera forma recente dos times
    - Evita jogadores contra defesas fortes
    - Busca defensores contra ataques fracos
    """
    
    # Esquemas táticos disponíveis
    ESQUEMAS = {
        "3-4-3": {"ZAG": 3, "LAT": 0, "MEI": 4, "ATA": 3},
        "3-5-2": {"ZAG": 3, "LAT": 0, "MEI": 5, "ATA": 2},
        "4-3-3": {"ZAG": 2, "LAT": 2, "MEI": 3, "ATA": 3},
        "4-4-2": {"ZAG": 2, "LAT": 2, "MEI": 4, "ATA": 2},
        "4-5-1": {"ZAG": 2, "LAT": 2, "MEI": 5, "ATA": 1},
        "5-3-2": {"ZAG": 3, "LAT": 2, "MEI": 3, "ATA": 2},
        "5-4-1": {"ZAG": 3, "LAT": 2, "MEI": 4, "ATA": 1},
    }
    
    # Máximo de jogadores por clube (regra oficial Cartola FC)
    MAX_POR_CLUBE = 5
    
    # Orçamento padrão
    ORCAMENTO_PADRAO = 100.0
    
    # Número de reservas
    NUM_RESERVAS = 5
    
    def __init__(self, orcamento: float = None):
        self.orcamento = orcamento or self.ORCAMENTO_PADRAO
        self.mpv_calc = MPVCalculator()
        self.rodada_atual: int = 1  # v7: rodada global (não per-jogador)
        
        # NOVO v3: Analisador de confrontos
        self.match_analyzer = MatchAnalyzer()
        self.confrontos_rodada: List[Confronto] = []
        self.clubes: Dict[str, Any] = {}
    
    def configurar_confrontos(
        self, 
        partidas: List[Dict], 
        clubes: Dict[str, Any],
        partidas_anteriores: List[Dict] = None
    ):
        """
        Configura análise de confrontos para a rodada
        
        Args:
            partidas: Lista de partidas da rodada atual (da API)
            clubes: Dict de clubes (da API)
            partidas_anteriores: Lista de resultados anteriores para calcular forma
        """
        self.clubes = clubes
        
        # Inicializar estatísticas dos times COM DADOS REAIS DA API
        # IMPORTANTE: Passa partidas para usar posição e aproveitamento reais
        self.match_analyzer.carregar_estatisticas_times(clubes, partidas)
        
        # Atualizar com resultados anteriores se disponível
        if partidas_anteriores:
            self.match_analyzer.atualizar_com_resultados(partidas_anteriores)
        
        # Analisar confrontos da rodada
        self.confrontos_rodada = self.match_analyzer.analisar_partidas_rodada(
            partidas, clubes
        )
    
    def _verificar_conflito(self, candidato: AnaliseJogador, time_atual: List[AnaliseJogador]) -> bool:
        """
        Verifica se há conflito tático grave ao adicionar o candidato.
        Ex: Adicionar zagueiro contra atacante já escalado.
        
        Args:
            candidato: Jogador sendo considerado
            time_atual: Lista de jogadores já escolhidos
            
        Returns:
            True se houver conflito GRAVE, False caso contrário
        """
        if not self.confrontos_rodada:
            return False
            
        # Identificar adversário do candidato
        adversario_id = None
        for confronto in self.confrontos_rodada:
            if confronto.clube_mandante_id == candidato.clube_id:
                adversario_id = confronto.clube_visitante_id
                break
            elif confronto.clube_visitante_id == candidato.clube_id:
                adversario_id = confronto.clube_mandante_id
                break
        
        if not adversario_id:
            return False
            
        is_defesa = candidato.posicao_abrev in ["GOL", "ZAG", "LAT"]
        is_ataque = candidato.posicao_abrev in ["MEI", "ATA"]
        
        for jogador in time_atual:
            # Se jogador atual é do time adversário
            if jogador.clube_id == adversario_id:
                jogador_is_defesa = jogador.posicao_abrev in ["GOL", "ZAG", "LAT"]
                jogador_is_ataque = jogador.posicao_abrev in ["MEI", "ATA"]
                
                # Conflito 1: Defesa x Ataque (MATADOR DE SG)
                # Se eu tenho atacante do time A e coloco defensor do time B
                if is_defesa and jogador_is_ataque:
                    return True
                if is_ataque and jogador_is_defesa:
                    return True
                    
        return False

    def _calcular_score_pontuacao(self, atleta: AnaliseJogador) -> float:
        """
        Calcula score de potencial para TIME DE PONTUAÇÃO
        
        VERSÃO v3 - Com análise de confrontos!
        
        Fatores (com pesos):
        1. Qualidade do jogador (30%): média, preço, tendência
        2. NOVO: Confronto da rodada (35%): adversário, mando, SG
        3. Posição ofensiva (15%): ATA/MEI pontuam mais
        4. Risco (20%): histórico de cartões, contusões
        
        NÃO é baseado apenas em preço!
        """
        score = 0.0
        
        # v7: Detectar rodada usando rodada GLOBAL (não per-jogador)
        is_rodada_1 = self.rodada_atual <= 1
        jogador_sem_dados = atleta.media == 0 and atleta.jogos_num == 0
        
        # === FATOR 1: QUALIDADE DO JOGADOR (30 pontos máx) ===
        if is_rodada_1:
            # Na rodada 1, usar preço como proxy de qualidade
            # Jogadores mais caros tendem a ser melhores
            score += min(30, atleta.preco * 1.2)
        elif jogador_sem_dados:
            # v7: R2+ mas jogador NUNCA jogou = PENALIDADE FORTE
            # Não é "rodada 1", é jogador sem histórico — risco altíssimo
            score += max(0, atleta.preco * 0.4 - 5)  # Máx ~5pts para caros, ~0 para baratos
        else:
            # Com histórico: usar média real
            # Média 10 = 30 pontos
            score += min(30, atleta.media * 3)
        
        # v7: PENALIDADE por poucos jogos na R2+ (suplentes/reservas)
        if not is_rodada_1 and atleta.jogos_num >= 1 and atleta.jogos_num < 3:
            if atleta.media < 3.0:
                score -= 15  # Jogou pouco E mal
        
        # === FATOR 2: ANÁLISE DO CONFRONTO (35 pontos máx) === NOVO v3!
        if self.confrontos_rodada:
            # Calcular bônus de confronto
            bonus_confronto = self.match_analyzer.calcular_bonus_confronto(
                atleta.clube_id,
                self.confrontos_rodada,
                atleta.posicao_abrev
            )
            
            # Converter bônus multiplicador em pontos
            # 1.0 = neutro (17.5pts), 1.3 = excelente (35pts), 0.7 = ruim (0pts)
            pontos_confronto = (bonus_confronto - 0.7) / 0.6 * 35
            score += max(0, min(35, pontos_confronto))
            
            # Bônus extra para confrontos muito favoráveis
            resumo = self.match_analyzer.get_resumo_confronto(
                atleta.clube_id, self.confrontos_rodada
            )
            if resumo and "erro" not in resumo:
                # Bônus para jogo em casa
                if resumo.get("local") == "CASA":
                    score += 5
                
                # Bônus/penalidade por dificuldade
                dificuldade = resumo.get("dificuldade", "MÉDIO")
                if dificuldade == "FÁCIL":
                    score += 10
                elif dificuldade == "MUITO DIFÍCIL":
                    score -= 10
                
                # Para defensores: bônus por chance de SG
                if atleta.posicao_abrev in ["GOL", "ZAG", "LAT"]:
                    chance_sg = resumo.get("chance_sg", 50)
                    if chance_sg > 60:
                        score += 8
                    elif chance_sg < 30:
                        score -= 5
                
                # PENALIDADE EXTRA: Times fracos (força < 55)
                # Para PONTUAÇÃO, times fracos pontuam muito menos
                if resumo.get("dificuldade_score", 100) < 100:
                    # Buscar força do próprio time
                    stats = self.match_analyzer.estatisticas_times.get(atleta.clube_id)
                    if stats:
                        forca_time = stats.forca_geral
                        if forca_time < 50:
                            # PENALIDADE MÁXIMA para times muito fracos (< 50)
                            score -= 60  # Aumentado de 30 para 60
                            if atleta.posicao_abrev in ["ATA", "MEI"]:
                                score -= 20  # Extra para atacantes
                            
                            # Se for visitante, penalidade TRIPLA
                            if resumo.get("local") == "FORA":
                                score -= 30  # Visitante muito fraco pontua quase zero
                        elif forca_time < 60:
                            # PENALIDADE FORTE para times fracos (50-60)
                            score -= 40  # Aumentado de 30 para 40
                            if atleta.posicao_abrev in ["ATA", "MEI"]:
                                score -= 15  # Extra para atacantes
                            
                            # Se for visitante, penalidade DOBRADA
                            if resumo.get("local") == "FORA":
                                score -= 25  # Visitante fraco pontua muito pouco
                        elif forca_time < 70:
                            # Penalidade moderada para times abaixo da média
                            score -= 20  # Aumentado de 15 para 20
                            if resumo.get("local") == "FORA":
                                score -= 15  # Aumentado de 10 para 15
                
                # Para atacantes: bônus por expectativa de gols
                if atleta.posicao_abrev in ["ATA", "MEI"]:
                    expect_gols = resumo.get("expectativa_gols", 1.0)
                    if expect_gols > 1.5:
                        score += 8
                    elif expect_gols < 0.7:
                        score -= 5
        else:
            # Sem dados de confronto, usar bônus neutro
            score += 17.5
        
        # === FATOR 3: BÔNUS POR POSIÇÃO (15 pontos máx) ===
        if atleta.posicao_abrev == "ATA":
            score += 15  # Atacantes pontuam mais
        elif atleta.posicao_abrev == "MEI":
            score += 12
        elif atleta.posicao_abrev == "LAT":
            score += 8  # Laterais com assistências
        elif atleta.posicao_abrev == "ZAG":
            score += 5
        elif atleta.posicao_abrev == "GOL":
            score += 7  # Goleiros com defesas difíceis
        
        # === FATOR 4: RISCO E TENDÊNCIA (20 pontos máx) ===
        if atleta.risco == "baixo":
            score += 15
        elif atleta.risco == "medio":
            score += 8
        else:
            score -= 5
        
        # Tendência de valorizar (indica bom momento)
        if not is_rodada_1:
            if atleta.tendencia_valorizar > 0.7:
                score += 5
            elif atleta.tendencia_valorizar < 0.3:
                score -= 3
        
        return max(0, score)  # Nunca retornar score negativo
    
    def _calcular_score_valorizacao(self, atleta: AnaliseJogador) -> float:
        """
        Calcula score de potencial para TIME DE VALORIZAÇÃO
        
        VERSÃO v8 - BASEADO EM DADOS REAIS R2 CARTOLA 2026
        
        DESCOBERTAS CHAVE que motivam esta versão:
        1. MPV real é MUITO MENOR que o calculado pela fórmula antiga
           → C$5 precisa apenas ~2.7 pts. C$15 precisa ~12 pts
        2. Pontuação da rodada ATUAL define tudo (NÃO herança de rodadas anteriores) 
        3. Sweet spot é C$2-6 (45-62% chance) vs C$10+ (25-32%)
        4. ZAG (45%) e TEC (55%) são melhores posições para valorizar
        5. Quem valorizou: avg 7.7 pts na rodada, preço médio C$6.94
        6. Quem desvalorizou: avg 1.4 pts na rodada, preço médio C$7.90
        
        Estrutura:
        1. PREÇO IDEAL (30 pts) — baseado em taxa real de valorização por preço
        2. POSIÇÃO (20 pts) — baseado em taxa real por posição
        3. CONSTÂNCIA/QUALIDADE (25 pts) — média e capacidade de superar MPV
        4. CONFRONTO (20 pts) — adversário, mando de campo
        5. RISCO (15 pts) — jogos, status, variação
        6. BÔNUS/PENALIDADES adicionais
        """
        score = 0.0
        is_rodada_1 = self.rodada_atual <= 1
        jogador_sem_dados = atleta.media == 0 and atleta.jogos_num == 0
        
        # === FATOR 1: PREÇO IDEAL (30 pts) ===
        # v8: Baseado na TAXA REAL de valorização por faixa de preço
        # C$2-6 = sweet spot (45-62% chance real de valorizar)
        if 2.0 <= atleta.preco < 4.0:
            score += 30  # C$2-4: MPV=1.5pts, 45-62% chance - MELHOR
        elif 4.0 <= atleta.preco < 6.0:
            score += 28  # C$4-6: MPV=2-2.7pts, 44-45% - Excelente
        elif 6.0 <= atleta.preco < 7.0:
            score += 22  # C$6-7: MPV=2.9pts, 48% - Bom
        elif 7.0 <= atleta.preco < 8.0:
            score += 18  # C$7-8: MPV=3.4pts, 38% - Razoável
        elif 1.0 <= atleta.preco < 2.0:
            score += 15  # C$1-2: MPV=0.5pts mas poucos pontuam - Arriscado
        elif 8.0 <= atleta.preco < 10.0:
            score += 12  # C$8-10: MPV=4.4-5pts, 25-31% - Difícil
        elif 10.0 <= atleta.preco < 13.0:
            score += 5   # C$10-13: MPV=5-5.5pts, 31% - Caro
        elif atleta.preco < 1.0:
            score += 5   # C$<1: muito barato, pode nem jogar
        else:
            score -= 10  # C$13+: MPV > 9pts, quase impossível (25%)
        
        # === FATOR 2: POSIÇÃO (20 pts) ===
        # v8: Baseado em taxa REAL de valorização por posição
        if atleta.posicao_abrev == "TEC":
            score += 20  # 55% valorizam! Melhor posição
            if atleta.preco <= 6.0:
                score += 5  # TEC barato = ouro
        elif atleta.posicao_abrev == "ZAG":
            score += 18  # 45% valorizam - Melhor posição de linha
        elif atleta.posicao_abrev == "LAT":
            score += 16  # 40% valorizam
        elif atleta.posicao_abrev == "MEI":
            score += 14  # 37% valorizam + pontos de finalização/assistência
        elif atleta.posicao_abrev == "ATA":
            score += 12  # 36% MAS precisam avg 9.2pts! Alto risco/retorno
        else:  # GOL
            score += 13  # 33% valorizam
        
        # === FATOR 3: CONSTÂNCIA / QUALIDADE (25 pts) ===
        # v8: Foco em "vai bater o MPV?" (que agora é real)
        mpv_real = atleta.mpv  # Já calculado com tabela real
        
        if is_rodada_1:
            # R1: sem histórico, usar preço como proxy (jogadores mais caros = melhor time)
            # MAS para valorização, baratos são melhores!
            score += 15  # Neutro base
            if atleta.preco <= 6.0:
                score += 5  # Baratos com MPV baixo na R1 
        elif jogador_sem_dados:
            # R2+: nunca jogou = RISCO ALTO (suplente)
            score -= 5
        else:
            # Média real vs MPV real = capacidade de superar o threshold
            margem_real = atleta.media - mpv_real
            
            if margem_real >= 5.0:
                score += 25  # Supera MPV com folga enorme
            elif margem_real >= 3.0:
                score += 22  # Supera bem o MPV
            elif margem_real >= 1.5:
                score += 18  # Supera MPV com margem boa
            elif margem_real >= 0:
                score += 14  # Exatamente no MPV (~50/50)
            elif margem_real >= -1.5:
                score += 8   # Ligeiramente abaixo do MPV
            elif margem_real >= -3.0:
                score += 3   # Abaixo do MPV
            else:
                score -= 5   # Muito abaixo - provavelmente não valoriza
        
        # === FATOR 4: CONFRONTO DA RODADA (20 pts) ===
        if self.confrontos_rodada:
            bonus_confronto = self.match_analyzer.calcular_bonus_confronto(
                atleta.clube_id,
                self.confrontos_rodada,
                atleta.posicao_abrev
            )
            # Converter: 1.0 = neutro (10pts), 1.3 = excelente (20pts), 0.7 = ruim (0pts)
            pontos_confronto = (bonus_confronto - 0.7) / 0.6 * 20
            score += max(0, min(20, pontos_confronto))
            
            resumo = self.match_analyzer.get_resumo_confronto(
                atleta.clube_id, self.confrontos_rodada
            )
            if resumo and "erro" not in resumo:
                # Mando de campo: jogar em casa = ~30% mais pontuação
                if resumo.get("local") == "CASA":
                    score += 5
                elif resumo.get("local") == "FORA":
                    score -= 8  # Visitante pontua menos = mais difícil bater MPV
                    if atleta.posicao_abrev in ["ATA", "MEI"]:
                        score -= 5  # Extra para ofensivos fora
                
                # Dificuldade do adversário
                dificuldade = resumo.get("dificuldade", "MÉDIO")
                if dificuldade == "FÁCIL":
                    score += 6
                elif dificuldade == "DIFÍCIL":
                    score -= 8
                elif dificuldade == "MUITO DIFÍCIL":
                    score -= 15
                
                # Para defensores: chance de SG (bônus de pontuação grande)
                if atleta.posicao_abrev in ["GOL", "ZAG", "LAT"]:
                    chance_sg = resumo.get("chance_sg", 50)
                    if chance_sg > 60:
                        score += 6  # SG = bônus de pontos = mais chance de bater MPV
                    elif chance_sg < 30:
                        score -= 3
            
            # Força do próprio time
            stats = self.match_analyzer.estatisticas_times.get(atleta.clube_id)
            if stats and stats.forca_geral < 50:
                score -= 20  # Time muito fraco não pontua
            elif stats and stats.forca_geral < 60:
                score -= 10  # Time fraco
        else:
            score += 10  # Neutro
        
        # === FATOR 5: RISCO (15 pts) ===
        if atleta.risco == "baixo":
            score += 15
        elif atleta.risco == "medio":
            score += 7
        else:
            score -= 5  # Alto risco = penalidade
        
        # === BÔNUS/PENALIDADES SITUACIONAIS ===
        
        # v8: Bônus desvalorização (jogador bom em má fase = oportunidade)
        # CONDIÇÃO: média >= MPV real (pode bater) E jogou
        if hasattr(atleta, 'variacao') and not is_rodada_1:
            if atleta.variacao < 0:
                if atleta.media >= mpv_real + 1.0 and atleta.jogos_num >= 1:
                    # Jogador BOM que desvalorizou = preço caiu, MPV caiu, mais fácil valorizar!
                    bonus_desval = min(20, abs(atleta.variacao) * 8)
                    score += bonus_desval
                elif atleta.media >= mpv_real and atleta.jogos_num >= 1:
                    # Jogador na fronteira, mas preço caiu = MPV mais baixo
                    bonus_desval = min(10, abs(atleta.variacao) * 4)
                    score += bonus_desval
                else:
                    # Jogador RUIM que desvalorizou = NÃO é oportunidade
                    score -= min(10, abs(atleta.variacao) * 3)
            elif atleta.variacao > 1.5:
                # Já valorizou muito = preço subiu, MPV subiu, mais difícil repetir
                penalidade_val = min(20, atleta.variacao * 6)
                score -= penalidade_val
        
        # v8: Penalidade para jogadores sem jogos (suplentes/banco)
        if not is_rodada_1:
            if atleta.jogos_num == 0:
                score -= 20  # Nunca jogou = provavelmente não joga
            elif atleta.jogos_num == 1 and atleta.media < 1.5:
                score -= 10  # Jogou 1x e foi mal
        
        # v8: Penalidade para caros com alta média (já caros, MPV alto)
        if atleta.preco > 12.0:
            score -= 15  # C$12+ quase impossível valorizar
        elif atleta.preco > 10.0 and atleta.media >= 5.0:
            score -= 10  # Caro E bom = preço alto demais
        
        return max(0, score)
    
    def selecionar_time_valorizacao(
        self,
        atletas_analisados: List[AnaliseJogador],
        esquema: str = "4-4-2",
        preco_maximo_jogador: float = 8.0
    ) -> Optional[TimeEscalado]:
        """
        Seleciona time focado em valorização
        
        VERSÃO v8 - Baseado em dados reais R2 2026:
        - preco_maximo_jogador reduzido de 10 para 8 (C$8+ tem só 25-31% chance)
        - Sweet spot C$2-6 priorizado pelo score
        - Filtros adaptativos por rodada mantidos do v7
        
        Prioriza:
        1. Preço C$2-6 (MPV=1.5-2.7pts, 45-62% chance)
        2. Posições ZAG/TEC (45-55% chance)
        3. Confronto favorável (casa, adversário fraco)
        4. Baixo risco
        5. Média >= MPV real
        2. Preço baixo (maior potencial de ganho)
        3. Baixo risco
        4. Margem de segurança positiva
        
        Args:
            atletas_analisados: Lista de atletas analisados
            esquema: Esquema tático desejado
            preco_maximo_jogador: Preço máximo por jogador
            
        Returns:
            TimeEscalado ou None se não conseguir formar time
        """
        if esquema not in self.ESQUEMAS:
            esquema = "4-4-2"
        
        necessidades = self.ESQUEMAS[esquema].copy()
        necessidades["GOL"] = 1
        necessidades["TEC"] = 1
        
        # Filtrar jogadores elegíveis
        # v7: Filtros adaptativos por rodada
        is_rodada_1 = self.rodada_atual <= 1
        
        elegiveis = []
        for a in atletas_analisados:
            if a.preco > preco_maximo_jogador:
                continue
            
            # v7: Na R2+, filtrar jogadores de times muito fracos
            if not is_rodada_1 and self.confrontos_rodada:
                stats = self.match_analyzer.estatisticas_times.get(a.clube_id)
                if stats and stats.forca_geral < 45:
                    continue  # Time muito fraco não valoriza
            
            # v7: Na R2+, filtrar jogadores que nunca jogaram E são baratos (suplentes)
            if not is_rodada_1 and a.jogos_num == 0 and a.preco < 3.0:
                continue  # Suplente barato = não vai jogar
            
            # v7: Risco alto = excluir (mais rigoroso agora com jogos_num)
            if a.risco == "alto":
                continue
            
            # v8: Tendência >= 0.25 (relaxado, pois taxa real é 35-46% no sweet spot)
            if a.tendencia_valorizar >= 0.25 or is_rodada_1:
                elegiveis.append(a)
        
        # Se não houver suficientes, relaxar filtro (manter filtro de time fraco)
        if len(elegiveis) < 15:
            elegiveis = [
                a for a in atletas_analisados
                if a.preco <= preco_maximo_jogador
                and a.risco != "alto"
            ]
        
        # Ordenar por critérios de valorização usando SCORE calculado!
        # MUDANÇA v4.2: Usar _calcular_score_valorizacao ao invés de ordenar apenas por preço
        elegiveis_com_score = [
            (a, self._calcular_score_valorizacao(a)) for a in elegiveis
        ]
        elegiveis_com_score.sort(key=lambda x: x[1], reverse=True)
        elegiveis = [a for a, score in elegiveis_com_score]
        
        return self._montar_time(
            elegiveis, necessidades, esquema, "valorizacao"
        )
    
    def selecionar_time_pontuacao(
        self,
        atletas_analisados: List[AnaliseJogador],
        esquema: str = "4-4-2",
        evitar_conflitos: bool = True
    ) -> Optional[TimeEscalado]:
        """
        Seleciona time focado em pontuação máxima
        
        NOVA ABORDAGEM (v2):
        - Calcula score de potencial para cada jogador
        - Ordena por score (não por preço!)
        - Monta time com melhores jogadores que cabem no orçamento
        - Usa algoritmo de otimização para maximizar potencial total
        
        O score considera:
        - Média de pontos (peso 40%)
        - Pontuação esperada (peso 30%)
        - Tendência de desempenho (peso 15%)
        - Risco (peso 15%)
        - NOVO: Força do time e local do confronto (penalty forte para fracos)
        """
        if esquema not in self.ESQUEMAS:
            esquema = "4-4-2"
        
        necessidades = self.ESQUEMAS[esquema].copy()
        necessidades["GOL"] = 1
        necessidades["TEC"] = 1
        
        # FILTRO INICIAL: Remover jogadores de perfil ruim para pontuação
        is_rodada_1 = self.rodada_atual <= 1
        atletas_filtrados = []
        for a in atletas_analisados:
            # v7.1: Na R2+, filtrar jogadores que NUNCA jogaram
            # Se nunca entrou em campo, não tem como prever pontuação
            if not is_rodada_1 and a.jogos_num == 0:
                continue
            
            # v7.1: Na R2+, filtrar jogadores com média negativa ou muito baixa
            # Não faz sentido escalar alguém que pontua negativo
            if not is_rodada_1 and a.media < 0.5 and a.jogos_num >= 1:
                continue
            
            # Buscar força do time
            stats = self.match_analyzer.estatisticas_times.get(a.clube_id)
            if stats:
                forca_time = stats.forca_geral
                
                # Filtro 1: Jogadores MUITO baratos de times MUITO fracos
                # C$ < 2.5 + força < 45 = evitar
                if forca_time < 45 and a.preco < 2.5:
                    continue
                
                # Filtro 2: Times péssimos (força < 40) - evitar todos
                if forca_time < 40:
                    continue
                
                # Filtro 3: Verificar se é visitante muito fraco
                eh_visitante = False
                for c in self.confrontos_rodada:
                    if c.clube_visitante_id == a.clube_id:
                        eh_visitante = True
                        break
                
                # Visitante muito fraco (< 50) com jogador barato (< 3.0) - evitar
                if eh_visitante and forca_time < 50 and a.preco < 3.0:
                    continue
            
            atletas_filtrados.append(a)
        
        # Calcular score de potencial para cada jogador
        atletas_com_score = []
        for a in atletas_filtrados:
            score = self._calcular_score_pontuacao(a)
            atletas_com_score.append((a, score))
        
        # Agrupar por posição e ordenar por SCORE (não preço!)
        por_posicao = defaultdict(list)
        for atleta, score in atletas_com_score:
            por_posicao[atleta.posicao_abrev].append((atleta, score))
        
        for pos in por_posicao:
            # Ordenar por score decrescente
            por_posicao[pos].sort(key=lambda x: x[1], reverse=True)
        
        # === FASE 1: Montar time inicial com melhores por posição ===
        # Que cabem no orçamento usando algoritmo guloso inteligente
        
        # Primeiro, pegar o jogador mais barato de cada posição para garantir viabilidade
        preco_minimo_por_pos = {}
        for pos, qtd in necessidades.items():
            if qtd > 0:
                candidatos = [a for a, s in por_posicao.get(pos, [])]
                candidatos.sort(key=lambda x: x.preco)
                if len(candidatos) >= qtd:
                    # Custo mínimo para preencher essa posição
                    preco_minimo_por_pos[pos] = sum(c.preco for c in candidatos[:qtd])
                else:
                    return None  # Impossível montar time
        
        custo_minimo_total = sum(preco_minimo_por_pos.values())
        if custo_minimo_total > self.orcamento:
            return None  # Não cabe nem o time mais barato
        
        # Orçamento disponível para upgrades
        orcamento_extra = self.orcamento - custo_minimo_total
        
        # === FASE 2: Selecionar melhores jogadores que cabem no orçamento ===
        titulares = []
        custo_total = 0.0
        contagem_clubes = defaultdict(int)
        ids_usados = set()
        
        # Ordenar posições por importância ofensiva (ATA/MEI primeiro)
        ordem_posicoes = ["ATA", "MEI", "LAT", "ZAG", "GOL", "TEC"]
        
        for pos in ordem_posicoes:
            qtd_necessaria = necessidades.get(pos, 0)
            if qtd_necessaria == 0:
                continue
            
            candidatos = por_posicao.get(pos, [])
            selecionados = 0
            
            for atleta, score in candidatos:
                if selecionados >= qtd_necessaria:
                    break
                
                if atleta.atleta_id in ids_usados:
                    continue
                
                if contagem_clubes[atleta.clube_abrev] >= self.MAX_POR_CLUBE:
                    continue
                
                # Verificar conflito tático (Defesa x Ataque)
                if evitar_conflitos and self._verificar_conflito(atleta, titulares):
                    continue

                # Calcular quanto orçamento precisamos reservar
                posicoes_restantes = []
                for p, q in necessidades.items():
                    qtd_atual = len([t for t in titulares if t.posicao_abrev == p])
                    if p == pos:
                        qtd_atual += 1  # Contando este que vamos adicionar
                    faltam = q - qtd_atual
                    if faltam > 0:
                        posicoes_restantes.append((p, faltam))
                
                # Calcular custo mínimo para preencher restantes
                reserva_necessaria = 0.0
                for p, faltam in posicoes_restantes:
                    cands = [a for a, s in por_posicao.get(p, []) 
                             if a.atleta_id not in ids_usados and a.atleta_id != atleta.atleta_id]
                    cands.sort(key=lambda x: x.preco)
                    if len(cands) >= faltam:
                        reserva_necessaria += sum(c.preco for c in cands[:faltam])
                    else:
                        reserva_necessaria += 999  # Impossível
                
                # Verificar se cabe
                if custo_total + atleta.preco + reserva_necessaria > self.orcamento:
                    continue
                
                # Adicionar jogador
                titulares.append(atleta)
                custo_total += atleta.preco
                contagem_clubes[atleta.clube_abrev] += 1
                ids_usados.add(atleta.atleta_id)
                selecionados += 1
        
        # Validar se conseguiu montar o time completo
        for pos, qtd in necessidades.items():
            qtd_atual = len([t for t in titulares if t.posicao_abrev == pos])
            if qtd_atual < qtd:
                return None
        
        # === FASE 3: Tentar upgrades finais se sobrar orçamento ===
        orcamento_restante = self.orcamento - custo_total
        
        if orcamento_restante > 1.0:
            melhorou = True
            max_iteracoes = 20
            iteracao = 0
            
            while melhorou and iteracao < max_iteracoes:
                melhorou = False
                iteracao += 1
                
                for pos in ordem_posicoes:
                    # Encontrar titular com menor score nessa posição
                    titulares_pos = [(t, self._calcular_score_pontuacao(t)) 
                                     for t in titulares if t.posicao_abrev == pos]
                    if not titulares_pos:
                        continue
                    
                    titulares_pos.sort(key=lambda x: x[1])
                    pior_titular, pior_score = titulares_pos[0]
                    
                    # Buscar substituto melhor
                    for atleta, score in por_posicao.get(pos, []):
                        if atleta.atleta_id in ids_usados:
                            continue
                        
                        if score <= pior_score:
                            continue  # Não é upgrade
                        
                        custo_upgrade = atleta.preco - pior_titular.preco
                        
                        if custo_upgrade > orcamento_restante:
                            continue
                        
                        # Verificar limite de clube
                        if atleta.clube_abrev != pior_titular.clube_abrev:
                            if contagem_clubes[atleta.clube_abrev] >= self.MAX_POR_CLUBE:
                                continue
                        
                        # Verificar conflito tático com o time resultante
                        titulares_temp = [t for t in titulares if t.atleta_id != pior_titular.atleta_id]
                        if evitar_conflitos and self._verificar_conflito(atleta, titulares_temp):
                            continue

                        # Fazer upgrade
                        titulares.remove(pior_titular)
                        titulares.append(atleta)
                        custo_total = custo_total - pior_titular.preco + atleta.preco
                        orcamento_restante = self.orcamento - custo_total
                        ids_usados.remove(pior_titular.atleta_id)
                        ids_usados.add(atleta.atleta_id)
                        contagem_clubes[pior_titular.clube_abrev] -= 1
                        contagem_clubes[atleta.clube_abrev] += 1
                        melhorou = True
                        break
                    
                    if melhorou:
                        break
        
        # === Selecionar Reservas (melhores disponíveis por posição) ===
        # Regra: Reserva TEM QUE ser mais barato que o titular da posição
        reservas = []
        min_preco_titular = {}
        
        # Encontrar o titular mais barato de cada posição
        for atleta in titulares:
            pos = atleta.posicao_abrev
            if pos not in min_preco_titular or atleta.preco < min_preco_titular[pos]:
                min_preco_titular[pos] = atleta.preco

        for pos in ["GOL", "ZAG", "MEI", "ATA", "LAT"]:
            # Verificar se já temos reserva para esta posição (caso de duplicação)
            if any(r.posicao_abrev == pos for r in reservas):
                continue
                
            preco_titular = min_preco_titular.get(pos, 999)
            
            for atleta, score in por_posicao.get(pos, []):
                if atleta.atleta_id not in ids_usados:
                    # REGRA DE OURO: Reserva deve ser mais barato que o titular
                    if atleta.preco < preco_titular:
                        reservas.append(atleta)
                        ids_usados.add(atleta.atleta_id)
                        break
        
        # Capitão: jogador com maior SCORE (não maior preço!)
        # v7: Validar capitão com critérios mínimos na R2+
        capitao = max(titulares, key=lambda x: self._calcular_score_pontuacao(x))
        
        if self.rodada_atual >= 2:
            candidatos_capitao = [
                t for t in titulares
                if t.media >= 3.0 and t.jogos_num >= 1
            ]
            if candidatos_capitao:
                capitao = max(candidatos_capitao, key=lambda x: self._calcular_score_pontuacao(x))
        
        # Pontuação prevista
        pontuacao_prevista = sum(
            (a.pontuacao_esperada if a.media > 0 else a.preco * 0.5) * (1.5 if a == capitao else 1.0)
            for a in titulares
        )
        
        # NOVO v3: Montar análise de confrontos
        analise_confrontos = {}
        for atleta in titulares:
            if self.confrontos_rodada:
                resumo = self.match_analyzer.get_resumo_confronto(
                    atleta.clube_id, self.confrontos_rodada
                )
                if resumo and "erro" not in resumo:
                    analise_confrontos[atleta.clube_id] = resumo
        
        return TimeEscalado(
            tipo="pontuacao",
            esquema=esquema,
            titulares=titulares,
            capitao=capitao,
            reservas=reservas,
            custo_total=round(custo_total, 1),
            cartoletas_restantes=round(self.orcamento - custo_total, 1),
            pontuacao_prevista=round(pontuacao_prevista, 1),
            valorizacao_esperada=0.0,
            analise_confrontos=analise_confrontos
        )
    
    def _montar_time(
        self,
        atletas_ordenados: List[AnaliseJogador],
        necessidades: Dict[str, int],
        esquema: str,
        tipo: str
    ) -> Optional[TimeEscalado]:
        """
        Monta o time respeitando restrições
        
        Args:
            atletas_ordenados: Lista ordenada por prioridade
            necessidades: Quantos jogadores por posição
            esquema: Esquema tático
            tipo: "valorizacao" ou "pontuacao"
            
        Returns:
            TimeEscalado ou None
        """
        titulares = []
        reservas = []
        custo_total = 0.0
        contagem_clubes = defaultdict(int)
        posicoes_preenchidas = defaultdict(int)
        
        # Primeira passada: preencher titulares
        for atleta in atletas_ordenados:
            pos = atleta.posicao_abrev
            
            # Verificar se ainda precisa desta posição
            if posicoes_preenchidas[pos] >= necessidades.get(pos, 0):
                continue
            
            # Verificar limite por clube
            if contagem_clubes[atleta.clube_abrev] >= self.MAX_POR_CLUBE:
                continue
            
            # Verificar orçamento
            if custo_total + atleta.preco > self.orcamento:
                continue
            
            # Adicionar ao time
            titulares.append(atleta)
            custo_total += atleta.preco
            contagem_clubes[atleta.clube_abrev] += 1
            posicoes_preenchidas[pos] += 1
        
        # Verificar se preencheu todas as posições
        for pos, qtd in necessidades.items():
            if posicoes_preenchidas[pos] < qtd:
                return None  # Não conseguiu montar time completo
        
        # Segunda passada: selecionar reservas
        atletas_usados = {a.atleta_id for a in titulares}
        reservas_candidatos = [
            a for a in atletas_ordenados
            if a.atleta_id not in atletas_usados
        ]
        
        # Encontrar o titular mais barato de cada posição
        min_preco_titular = {}
        for atleta in titulares:
            pos = atleta.posicao_abrev
            if pos not in min_preco_titular or atleta.preco < min_preco_titular[pos]:
                min_preco_titular[pos] = atleta.preco
        
        # Reservas: 1 por posição prioritária
        posicoes_reserva = ["GOL", "ZAG", "MEI", "ATA", "LAT"]
        posicoes_reserva_preenchidas = set()
        
        for atleta in reservas_candidatos:
            if len(reservas) >= self.NUM_RESERVAS:
                break
            
            pos = atleta.posicao_abrev
            
            # REGRA DE OURO: Reserva deve ser mais barato que o titular
            preco_titular = min_preco_titular.get(pos, 999)
            if atleta.preco >= preco_titular:
                continue

            if pos in posicoes_reserva and pos not in posicoes_reserva_preenchidas:
                reservas.append(atleta)
                posicoes_reserva_preenchidas.add(pos)
        
        # v7: Escolher capitão CORRETAMENTE
        # Usar _calcular_score_valorizacao ao invés de pontuacao_esperada
        # (pontuacao_esperada pode ser 0 para jogadores sem dados → seleção aleatória)
        if tipo == "valorizacao":
            capitao = max(titulares, key=lambda x: self._calcular_score_valorizacao(x))
        else:
            capitao = max(titulares, key=lambda x: self._calcular_score_pontuacao(x))
        
        # v7: Validar capitão mínimo (R2+: deve ter média >= 3.0 ou jogos >= 2)
        if self.rodada_atual >= 2:
            candidatos_capitao = [
                t for t in titulares
                if t.media >= 3.0 and t.jogos_num >= 1
            ]
            if candidatos_capitao:
                if tipo == "valorizacao":
                    capitao = max(candidatos_capitao, key=lambda x: self._calcular_score_valorizacao(x))
                else:
                    capitao = max(candidatos_capitao, key=lambda x: self._calcular_score_pontuacao(x))
            # Se nenhum atende critérios, fica com o melhor por score (fallback)
        
        # Calcular métricas
        pontuacao_prevista = sum(
            a.pontuacao_esperada * (1.5 if a == capitao else 1.0)
            for a in titulares
        )
        
        valorizacao_esperada = sum(
            (a.tendencia_valorizar - 0.5) * a.preco * 0.1
            for a in titulares
        )
        
        # NOVO v3: Montar análise de confrontos
        analise_confrontos = {}
        for atleta in titulares:
            if self.confrontos_rodada:
                resumo = self.match_analyzer.get_resumo_confronto(
                    atleta.clube_id, self.confrontos_rodada
                )
                if resumo and "erro" not in resumo:
                    analise_confrontos[atleta.clube_id] = resumo
        
        return TimeEscalado(
            tipo=tipo,
            esquema=esquema,
            titulares=titulares,
            capitao=capitao,
            reservas=reservas,
            custo_total=round(custo_total, 1),
            cartoletas_restantes=round(self.orcamento - custo_total, 1),
            pontuacao_prevista=round(pontuacao_prevista, 1),
            valorizacao_esperada=round(valorizacao_esperada, 2),
            analise_confrontos=analise_confrontos
        )
    
    def sugerir_capitao(
        self,
        titulares: List[AnaliseJogador],
        tipo_time: str = "pontuacao"
    ) -> AnaliseJogador:
        """
        Sugere o melhor capitão para o time
        
        Args:
            titulares: Lista de titulares
            tipo_time: "valorizacao" ou "pontuacao"
            
        Returns:
            Melhor candidato a capitão
        """
        if tipo_time == "valorizacao":
            # Para valorização, capitão deve ter alta tendência e bom custo
            return max(
                titulares,
                key=lambda x: x.tendencia_valorizar * x.pontuacao_esperada
            )
        else:
            # Para pontuação, capitão com maior pontuação esperada
            return max(titulares, key=lambda x: x.pontuacao_esperada)
    
    def comparar_esquemas(
        self,
        atletas_analisados: List[AnaliseJogador],
        tipo: str = "valorizacao"
    ) -> Dict[str, TimeEscalado]:
        """
        Compara times em diferentes esquemas táticos
        
        Args:
            atletas_analisados: Lista de atletas analisados
            tipo: "valorizacao" ou "pontuacao"
            
        Returns:
            Dicionário com melhor time para cada esquema
        """
        resultados = {}
        
        for esquema in self.ESQUEMAS:
            if tipo == "valorizacao":
                time = self.selecionar_time_valorizacao(atletas_analisados, esquema)
            else:
                time = self.selecionar_time_pontuacao(atletas_analisados, esquema)
            
            if time:
                resultados[esquema] = time
        
        return resultados
    
    def gerar_times_rodada(
        self,
        atletas_analisados: List[AnaliseJogador],
        esquema: str = "4-4-2",
        rodada_atual: int = 1
    ) -> Tuple[Optional[TimeEscalado], Optional[TimeEscalado]]:
        """
        Gera os dois times para a rodada
        
        VERSÃO v7 - Recebe rodada_atual para ajustar algoritmos
        
        Args:
            atletas_analisados: Lista de atletas analisados
            esquema: Esquema tático preferido
            rodada_atual: Número da rodada atual (afeta pesos e filtros)
            
        Returns:
            Tupla (time_valorizacao, time_pontuacao)
        """
        # v7: Definir rodada global
        self.rodada_atual = rodada_atual
        
        # Salvar orçamento original
        orcamento_original = self.orcamento
        
        # 1. Gerar time de valorização (focado em ganhar cartoletas)
        time_valor = self.selecionar_time_valorizacao(atletas_analisados, esquema)
        
        # 2. Lógica de orçamento progressivo para Time de Pontuação
        # O objetivo é tentar manter o orçamento próximo ao do time de valorização (User Request),
        # mas relaxar a restrição se não for possível montar um time válido.
        
        custo_referencia = time_valor.custo_total if time_valor else 85.0
        
        # Lista de multiplicadores para tentar: 
        # 1.15 (Muito restrito, pedido do usuário)
        # 1.25 (Um pouco mais folgado)
        # 1.35 (Razoável)
        # 2.00 (Usa o que tiver até o limite do usuário)
        multiplicadores = [1.15, 1.25, 1.35, 2.0]
        
        time_pontos = None
        
        for mult in multiplicadores:
            # Calcular orçamento teto para esta tentativa
            if self.orcamento < 110:
                # Se o user já é pobre, tenta restringir
                orcamento_tentativa = min(orcamento_original, custo_referencia * mult)
            else:
                # Se o user é rico, o "1.15" é pra evitar gastar 180 qdo o time de valor custa 80
                # Mas se precisar gastar mais pra fechar o time, gasta.
                orcamento_tentativa = min(orcamento_original, max(custo_referencia * mult, 100.0))
            
            self.orcamento = orcamento_tentativa
            
            # Tentar gerar com verificação de conflitos (Estrito)
            time_pontos = self.selecionar_time_pontuacao(atletas_analisados, esquema, evitar_conflitos=True)
            
            if time_pontos:
                # Sucesso com restrições e orçamento atual
                break
                
            # Se falhou, tentar sem verificação de conflitos (Permissivo) mas com orçamento atual
            time_pontos = self.selecionar_time_pontuacao(atletas_analisados, esquema, evitar_conflitos=False)
            
            if time_pontos:
                # Sucesso sem restrições mas com orçamento atual
                break
        
        # 3. Fallback Final: Se tudo falhou (muito improvável), tenta com orçamento total
        if time_pontos is None:
            self.orcamento = orcamento_original
            time_pontos = self.selecionar_time_pontuacao(atletas_analisados, esquema, evitar_conflitos=False)

        # Restaurar orçamento original
        self.orcamento = orcamento_original
        
        return time_valor, time_pontos


class TeamFormatter:
    """Formatador de times para exibição - VERSÃO v3 com confrontos"""
    
    POSICAO_ORDEM = ["GOL", "LAT", "ZAG", "MEI", "ATA", "TEC"]
    
    # Emojis para dificuldade
    DIFICULDADE_EMOJI = {
        "FÁCIL": "🟢",
        "MÉDIO": "🟡", 
        "DIFÍCIL": "🟠",
        "MUITO DIFÍCIL": "🔴"
    }
    
    @staticmethod
    def formatar_time(time: TimeEscalado) -> str:
        """Formata time para exibição em texto com análise de confrontos"""
        linhas = []
        
        tipo_emoji = "📈" if time.tipo == "valorizacao" else "🎯"
        linhas.append(f"\n{tipo_emoji} TIME DE {time.tipo.upper()} - Esquema {time.esquema}")
        linhas.append("=" * 70)
        
        # NOVO v3: Exibir análise de confrontos
        if time.analise_confrontos:
            linhas.append("\n📊 ANÁLISE DE CONFRONTOS DO TIME:")
            clubes_mostrados = set()
            for clube_id, confronto in time.analise_confrontos.items():
                if clube_id in clubes_mostrados:
                    continue
                clubes_mostrados.add(clube_id)
                
                emoji = TeamFormatter.DIFICULDADE_EMOJI.get(confronto.get("dificuldade", "MÉDIO"), "⚪")
                local = "🏠" if confronto.get("local") == "CASA" else "✈️"
                linhas.append(
                    f"   {local} vs {confronto.get('adversario', '???')} "
                    f"| {emoji} {confronto.get('dificuldade', 'MÉDIO')} "
                    f"| SG: {confronto.get('chance_sg', 50):.0f}% "
                    f"| Gols: {confronto.get('expectativa_gols', 1.0):.1f}"
                )
            linhas.append("")
        
        # Agrupar por posição
        por_posicao = time.get_por_posicao()
        
        for pos in TeamFormatter.POSICAO_ORDEM:
            if pos in por_posicao:
                linhas.append(f"📍 {pos}:")
                for atleta in por_posicao[pos]:
                    cap = " ⭐(C)" if atleta == time.capitao else ""
                    
                    # NOVO v3: Adicionar info do confronto do jogador
                    confronto_info = ""
                    if time.analise_confrontos:
                        confronto = time.analise_confrontos.get(atleta.clube_id)
                        if confronto:
                            local = "🏠" if confronto.get("local") == "CASA" else "✈️"
                            emoji = TeamFormatter.DIFICULDADE_EMOJI.get(
                                confronto.get("dificuldade", "MÉDIO"), "⚪"
                            )
                            confronto_info = f" {local}{emoji}"
                    
                    linhas.append(
                        f"   {atleta.apelido} ({atleta.clube_abrev}) - "
                        f"C${atleta.preco:.1f} | Média: {atleta.media:.1f} | "
                        f"MPV: {atleta.mpv:.1f}{cap}{confronto_info}"
                    )
        
        linhas.append(f"\n💰 Custo Total: C${time.custo_total}")
        linhas.append(f"💵 Restante: C${time.cartoletas_restantes}")
        linhas.append(f"📊 Pontuação Prevista: {time.pontuacao_prevista:.1f}")
        
        if time.tipo == "valorizacao":
            linhas.append(f"📈 Valorização Esperada: C${time.valorizacao_esperada:.2f}")
        
        if time.reservas:
            linhas.append(f"\n🪑 RESERVAS:")
            for res in time.reservas:
                linhas.append(f"   {res.apelido} ({res.posicao_abrev}/{res.clube_abrev}) - C${res.preco:.1f}")
        
        return "\n".join(linhas)
    
    @staticmethod
    def formatar_comparacao(time_valor: TimeEscalado, time_pontos: TimeEscalado) -> str:
        """Formata comparação entre os dois times"""
        linhas = []
        
        linhas.append("\n" + "=" * 70)
        linhas.append("📊 COMPARAÇÃO DOS TIMES DA RODADA")
        linhas.append("=" * 70)
        
        linhas.append(f"\n{'Métrica':<25} {'Valorização':>20} {'Pontuação':>20}")
        linhas.append("-" * 70)
        linhas.append(f"{'Custo Total':<25} C${time_valor.custo_total:>18.1f} C${time_pontos.custo_total:>18.1f}")
        linhas.append(f"{'Cartoletas Restantes':<25} C${time_valor.cartoletas_restantes:>18.1f} C${time_pontos.cartoletas_restantes:>18.1f}")
        linhas.append(f"{'Pontuação Prevista':<25} {time_valor.pontuacao_prevista:>20.1f} {time_pontos.pontuacao_prevista:>20.1f}")
        
        # NOVO v3: Comparar qualidade de confrontos
        if time_valor.analise_confrontos or time_pontos.analise_confrontos:
            linhas.append("")
            linhas.append("🎯 QUALIDADE DOS CONFRONTOS:")
            
            def contar_confrontos(time: TimeEscalado) -> Dict[str, int]:
                contagem = {"FÁCIL": 0, "MÉDIO": 0, "DIFÍCIL": 0, "MUITO DIFÍCIL": 0, "CASA": 0}
                for confronto in time.analise_confrontos.values():
                    dif = confronto.get("dificuldade", "MÉDIO")
                    contagem[dif] = contagem.get(dif, 0) + 1
                    if confronto.get("local") == "CASA":
                        contagem["CASA"] += 1
                return contagem
            
            c_valor = contar_confrontos(time_valor)
            c_pontos = contar_confrontos(time_pontos)
            
            linhas.append(f"{'Jogos em Casa':<25} {c_valor.get('CASA', 0):>20} {c_pontos.get('CASA', 0):>20}")
            linhas.append(f"{'Confrontos Fáceis':<25} {c_valor.get('FÁCIL', 0):>20} {c_pontos.get('FÁCIL', 0):>20}")
            linhas.append(f"{'Confrontos Difíceis':<25} {c_valor.get('DIFÍCIL', 0) + c_valor.get('MUITO DIFÍCIL', 0):>20} {c_pontos.get('DIFÍCIL', 0) + c_pontos.get('MUITO DIFÍCIL', 0):>20}")
        
        return "\n".join(linhas)


# Instâncias globais
team_selector = TeamSelector()
team_formatter = TeamFormatter()


if __name__ == "__main__":
    from src.analysis.mpv_calculator import MPVCalculator
    
    # Teste com dados simulados
    calc = MPVCalculator()
    
    jogadores_teste = [
        {"atleta_id": 1, "nome": "Goleiro 1", "apelido": "Gabriel", "preco_num": 6.0, "media_num": 4.0, "posicao_id": 1, "jogos_num": 10, "variacao_num": 0},
        {"atleta_id": 2, "nome": "Zagueiro 1", "apelido": "Mercado", "preco_num": 5.0, "media_num": 3.5, "posicao_id": 3, "jogos_num": 10, "variacao_num": 0},
        {"atleta_id": 3, "nome": "Zagueiro 2", "apelido": "Maicon", "preco_num": 5.0, "media_num": 3.0, "posicao_id": 3, "jogos_num": 10, "variacao_num": 0},
        {"atleta_id": 4, "nome": "Lateral 1", "apelido": "Mateus Silva", "preco_num": 3.0, "media_num": 2.5, "posicao_id": 2, "jogos_num": 10, "variacao_num": 0},
        {"atleta_id": 5, "nome": "Lateral 2", "apelido": "Ramon", "preco_num": 5.0, "media_num": 3.5, "posicao_id": 2, "jogos_num": 10, "variacao_num": 0},
        {"atleta_id": 6, "nome": "Meia 1", "apelido": "Alan Patrick", "preco_num": 8.0, "media_num": 6.5, "posicao_id": 4, "jogos_num": 10, "variacao_num": 0},
        {"atleta_id": 7, "nome": "Meia 2", "apelido": "Bruno Gomes", "preco_num": 6.0, "media_num": 4.5, "posicao_id": 4, "jogos_num": 10, "variacao_num": 0},
        {"atleta_id": 8, "nome": "Meia 3", "apelido": "Baralhas", "preco_num": 6.0, "media_num": 4.0, "posicao_id": 4, "jogos_num": 10, "variacao_num": 0},
        {"atleta_id": 9, "nome": "Meia 4", "apelido": "Sebastián Gómez", "preco_num": 4.0, "media_num": 3.0, "posicao_id": 4, "jogos_num": 10, "variacao_num": 0},
        {"atleta_id": 10, "nome": "Atacante 1", "apelido": "Borré", "preco_num": 8.0, "media_num": 5.5, "posicao_id": 5, "jogos_num": 10, "variacao_num": 0},
        {"atleta_id": 11, "nome": "Atacante 2", "apelido": "Pedro Rocha", "preco_num": 7.0, "media_num": 5.0, "posicao_id": 5, "jogos_num": 10, "variacao_num": 0},
        {"atleta_id": 12, "nome": "Técnico", "apelido": "Jair Ventura", "preco_num": 5.0, "media_num": 3.5, "posicao_id": 6, "jogos_num": 10, "variacao_num": 0},
    ]
    
    clubes = ["VIT", "INT", "CFC", "VIT", "VIT", "INT", "INT", "VIT", "CFC", "INT", "CFC", "VIT"]
    posicoes = ["GOL", "ZAG", "ZAG", "LAT", "LAT", "MEI", "MEI", "MEI", "MEI", "ATA", "ATA", "TEC"]
    
    # Analisar jogadores
    analisados = []
    for i, jog in enumerate(jogadores_teste):
        analise = calc.analisar_jogador(jog, clubes[i], posicoes[i])
        analisados.append(analise)
    
    # Gerar times
    selector = TeamSelector()
    time_valor, time_pontos = selector.gerar_times_rodada(analisados)
    
    if time_valor:
        print(TeamFormatter.formatar_time(time_valor))
    
    if time_pontos:
        print(TeamFormatter.formatar_time(time_pontos))
    
    if time_valor and time_pontos:
        print(TeamFormatter.formatar_comparacao(time_valor, time_pontos))
