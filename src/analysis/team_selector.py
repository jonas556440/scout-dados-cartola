"""
Seletor de Times - Cartola FC 2026

Gera dois times por rodada:
1. Time Valorização: Jogadores com potencial de ganhar MAIS CARTOLETAS (otimizado!)
2. Time Pontuação: Jogadores para pontuar máximo

VERSÃO v6 - CORRIGIDO BASEADO EM DADOS REAIS DA RODADA 1:
- ✅ Usa estatísticas reais (média, scouts, tendência)
- ✅ Calcula score de potencial por jogador
- ✅ Considera adversário da rodada
- ✅ Considera mando de campo (casa/fora)
- ✅ Analisa força do adversário
- ✅ Considera forma recente dos times
- ✅ Calcula chance de SG (saldo de gols)
- 🆕 NOVO v6: Prioriza C$3-6 (SWEET SPOT CONFIRMADO!) - 35%
- 🆕 NOVO v6: C$2-3 também muito bom (alta % valorização)
- 🆕 NOVO v6: Penaliza C$10+ (valorizam menos %)
- ✅ Constância (média de pontos) - 20%
- ✅ Risco balanceado (15%)

Dados REAIS rodada 1 (preço ANTES da valorização):
- Gabriel Menino C$6→C$10.77 (+4.77, +79.5%)
- Léo Derik C$2→C$5.14 (+3.14, +157%)
- vs Danilo C$10→C$14.21 (+4.21, +42.1%)
Jogadores baratos C$2-7 valorizam MUITO MAIS percentualmente!

Fatores de análise (como sites especializados):
- CONSTÂNCIA: média de pontos (novo peso 30%!)
- Preço ideal: C$3-6 é o sweet spot risco/retorno
- Adversário da rodada: força ofensiva/defensiva
- Mando de campo: time em casa pontua ~30% mais
- Forma recente: últimos 5 jogos (vitórias/derrotas)
- Chance de SG: importante para defensores
- Expectativa de gols: importante para atacantes

Regras:
- Orçamento: 100 cartoletas (ou cartoletas disponíveis)
- Esquemas permitidos: 3-4-3, 3-5-2, 4-3-3, 4-4-2, 4-5-1, 5-3-2, 5-4-1
- 12 titulares (1 GOL + 10 linha + 1 TEC)
- Capitão recebe 1.5x os pontos
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
        
        # Detectar se é rodada 1 (sem médias)
        is_rodada_1 = atleta.media == 0
        
        # === FATOR 1: QUALIDADE DO JOGADOR (30 pontos máx) ===
        if is_rodada_1:
            # Na rodada 1, usar preço como proxy de qualidade
            # Jogadores mais caros tendem a ser melhores
            # C$1 = 2pts, C$25 = 30pts
            score += min(30, atleta.preco * 1.2)
        else:
            # Com histórico: usar média real
            # Média 10 = 30 pontos
            score += min(30, atleta.media * 3)
        
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
        
        VERSÃO v5 - BASEADO NAS ESTRATÉGIAS DO GATO MESTRE (ge.globo.com)
        
        REGRAS OFICIAIS DE VALORIZAÇÃO:
        1. Preferência a jogadores < C$10 (quanto mais barato, menos pontos precisa)
        2. Bons e Baratos têm tendência maior a valorizar
        3. Técnicos baratos tendem a valorizar mais na 1ª rodada
        4. Não mais de 2 defensores do mesmo time (SG arriscado)
        5. Dá pra gastar mais no ataque buscando gol/assistência
        
        FÓRMULA VALORIZAÇÃO: pontuação > (preço * fator)
        - Quanto menor o preço, mais fácil valorizar!
        """
        score = 0.0
        
        # 1. PREÇO IDEAL (35%) - CRITÉRIO PRINCIPAL!
        # Dados REAIS rodada 1: Jogadores C$2-7 valorizaram MUITO MAIS!
        # Gabriel Menino C$6→C$10.77 (+79%), Léo Derik C$2→C$5.14 (+157%)
        # vs Danilo C$10→C$14.21 (+42%), Breno Bidon C$10→C$13.34 (+33%)
        if 3.0 <= atleta.preco <= 6.0:
            score += 35  # MELHOR: sweet spot - bons e baratos valorizam MUITO
        elif 2.0 <= atleta.preco < 3.0:
            score += 32  # ÓTIMO: muito baratos, alta % mas precisam jogar
        elif 6.0 < atleta.preco <= 8.0:
            score += 28  # BOM: ainda valorizam bem
        elif 8.0 < atleta.preco <= 10.0:
            score += 18  # RAZOÁVEL: valorização moderada (reduzido de 22)
        elif atleta.preco < 2.0:
            score += 15  # ARRISCADO: podem não jogar/pontuar
        elif 10.0 < atleta.preco <= 12.0:
            score -= 10  # CARO: PENALIDADE! Difícil valorizar (era +15)
        else:
            score -= 20  # MUITO CARO: GRANDE PENALIDADE (era +8)
        
        # 2. POSIÇÃO (20%) - Técnicos baratos valorizam mais na R1
        if atleta.posicao_abrev == "TEC":
            if atleta.preco <= 5.0:
                score += 25  # Técnico barato = OURO na R1!
            else:
                score += 15  # Técnico caro ainda é bom
        elif atleta.posicao_abrev in ["ATA", "MEI"]:
            # Gol/assistência = valorização garantida
            score += 20  # Atacantes e meias ofensivos
        elif atleta.posicao_abrev == "LAT":
            score += 18  # Laterais têm bom potencial (assistências)
        elif atleta.posicao_abrev == "ZAG":
            score += 15  # Zagueiros dependem de SG
        else:  # GOL
            score += 12  # Goleiros dependem muito de SG
        
        # 3. CONSTÂNCIA (20%) - Média de pontos histórica
        # Na rodada 1, usa preço como proxy
        media_pontos = atleta.media
        if media_pontos >= 5.0:
            score += 20  # Jogador muito constante
        elif media_pontos >= 3.0:
            score += 15  # Boa constância
        elif media_pontos > 0:
            score += 10  # Alguma constância
        else:
            # R1: sem histórico, usar preço como proxy
            score += 12  # Neutro na R1
        
        # 4. Tendência de valorizar (5%)
        if atleta.tendencia_valorizar > 0.7:
            score += 5  # Bônus para alta tendência
        
        # 5. Confronto favorável (20% - aumentado!)
        if self.confrontos_rodada:
            bonus_confronto = self.match_analyzer.calcular_bonus_confronto(
                atleta.clube_id,
                self.confrontos_rodada,
                atleta.posicao_abrev
            )
            pontos_confronto = (bonus_confronto - 0.7) / 0.6 * 20  # Aumentado de 15 para 20
            score += max(0, min(20, pontos_confronto))
            
            resumo = self.match_analyzer.get_resumo_confronto(
                atleta.clube_id, self.confrontos_rodada
            )
            if resumo and "erro" not in resumo:
                if resumo.get("local") == "CASA":
                    score += 5  # Aumentado de 3 para 5
                elif resumo.get("local") == "FORA":
                    # PENALIDADE GRANDE para jogos fora no time de valorização
                    # Valorizar depende de gols/assistências, mais difícil fora
                    score -= 15  # PENALIDADE BASE
                    # Penalidade EXTRA para atacantes e meias fora (menos gols/assistências)
                    if atleta.posicao_abrev in ["ATA", "MEI"]:
                        score -= 15  # Total -30 pts para atacantes/meias fora!
                    
                if resumo.get("dificuldade") == "FÁCIL":
                    score += 8  # Aumentado de 4 para 8
                elif resumo.get("dificuldade") == "DIFÍCIL":
                    score -= 12  # Aumentado penalidade de 6 para 12
                elif resumo.get("dificuldade") == "MUITO DIFÍCIL":
                    score -= 20  # Aumentado penalidade de 6 para 20
                    
                # NOVA PENALIDADE: Times muito fracos (força < 50)
                # Mesmo baratos, times fracos pontuam pouco = não valorizam
                if resumo.get("dificuldade_score", 100) < 50:
                    # Time adversário é muito fraco, então o time do jogador é fraco
                    # Na verdade, dificuldade_score é a força do adversário
                    pass
                    
            # PENALIDADE EXTRA: Verificar força do próprio time
            # Buscar força do time nas estatísticas
            stats = self.match_analyzer.estatisticas_times.get(atleta.clube_id)
            if stats and stats.forca_geral < 50:
                # Time muito fraco: grande penalidade mesmo se barato
                score -= 25  # Grande penalidade para times ruins
                if atleta.posicao_abrev in ["ATA", "MEI"]:
                    score -= 10  # Penalidade extra para atacantes de times fracos
                    
            # BÔNUS CIENTÍFICO: Priorizar times na análise de confrontos
            # Integra match_analyzer com seleção de jogadores
            try:
                analise_confrontos = self.match_analyzer.analisar_partidas_rodada(
                    self.confrontos_rodada,
                    self.match_analyzer.clubes if hasattr(self.match_analyzer, 'clubes') else {}
                )
                times_escalar = analise_confrontos.get('timesParaEscalar', [])
                
                # Buscar abreviação do clube do atleta
                clube_abrev = None
                for clube_id, clube_info in self.match_analyzer.clubes.items():
                    if clube_id == atleta.clube_id:
                        clube_abrev = clube_info.get('abreviacao', clube_info.get('nome', '')[:3].upper())
                        break
                
                if clube_abrev:
                    # Verificar posição no ranking científico
                    for i, time_rec in enumerate(times_escalar[:10]):  # TOP 10
                        if time_rec.get('abrev') == clube_abrev or time_rec.get('nome') == clube_abrev:
                            if i < 2:  # TOP 2: bônus MUITO forte (supera diferença de C$3-4)
                                score += 40
                            elif i < 5:  # TOP 5: bônus forte
                                score += 28
                            elif i < 8:  # TOP 8: bônus médio
                                score += 18
                            elif i < 10:  # TOP 10: bônus leve
                                score += 10
                            break
            except Exception as e:
                # Se falhar análise científica, continuar sem bônus
                pass
        else:
            score += 10  # Neutro
        
        # 5. Margem de segurança (15%) - Mantém
        if atleta.margem_seguranca > 0:
            score += min(15, atleta.margem_seguranca * 4)
        else:
            score += max(0, 7 + atleta.margem_seguranca * 2)
        
        # 6. Risco (15%) - Aumentado de 10% para 15%
        if atleta.risco == "baixo":
            score += 15  # Aumentado
        elif atleta.risco == "medio":
            score += 7   # Aumentado
        else:
            score -= 5   # Penalidade maior
        
        # 7. BÔNUS/PENALIDADE POR VARIAÇÃO (CRÍTICO para R2+!)
        # Desvalorizados = OPORTUNIDADE, Valorizados = JÁ SUBIRAM
        if hasattr(atleta, 'variacao'):
            if atleta.variacao < 0:
                # BÔNUS FORTE para desvalorizados - são as melhores oportunidades!
                # Quanto mais desvalorizou, maior o bônus (max +40 pts)
                bonus_desval = min(40, abs(atleta.variacao) * 12)
                score += bonus_desval
            elif atleta.variacao > 1.0:
                # PENALIDADE para quem já valorizou muito - potencial futuro menor
                # Quanto mais valorizou, maior a penalidade (max -25 pts)
                penalidade_val = min(25, atleta.variacao * 8)
                score -= penalidade_val
        
        # 8. PENALIDADE EXTRA PARA CAROS COM ALTA CONSTÂNCIA
        # Evita que constância compense preço alto
        if atleta.preco > 10.0 and atleta.media >= 5.0:
            score -= 15  # Penalidade adicional - já valorizou demais
        
        return max(0, score)
    
    def selecionar_time_valorizacao(
        self,
        atletas_analisados: List[AnaliseJogador],
        esquema: str = "4-4-2",
        preco_maximo_jogador: float = 10.0
    ) -> Optional[TimeEscalado]:
        """
        Seleciona time focado em valorização
        
        Prioriza:
        1. Alta tendência de valorizar
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
        # Na rodada 1, todos têm média 0, então ajustamos os filtros
        elegiveis = [
            a for a in atletas_analisados
            if a.preco <= preco_maximo_jogador
            and (a.tendencia_valorizar >= 0.4 or a.media == 0)  # Aceita todos na R1
            and a.risco != "alto"
        ]
        
        # Se não houver suficientes, relaxar filtro
        if len(elegiveis) < 12:
            elegiveis = [
                a for a in atletas_analisados
                if a.preco <= preco_maximo_jogador
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
        atletas_filtrados = []
        for a in atletas_analisados:
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
        capitao = max(titulares, key=lambda x: self._calcular_score_pontuacao(x))
        
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
        
        # Escolher capitão (maior pontuação esperada)
        capitao = max(titulares, key=lambda x: x.pontuacao_esperada)
        
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
        esquema: str = "4-4-2"
    ) -> Tuple[Optional[TimeEscalado], Optional[TimeEscalado]]:
        """
        Gera os dois times para a rodada
        
        Args:
            atletas_analisados: Lista de atletas analisados
            esquema: Esquema tático preferido
            
        Returns:
            Tupla (time_valorizacao, time_pontuacao)
        """
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
