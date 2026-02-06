"""
Previsor de Jogos Customizados + Recursos Avançados
Cartola FC 2026

Este módulo adiciona:
1. Previsão de qualquer jogo (não só Cartola)
2. Sistema de desfalques integrado
3. Histórico de confrontos diretos
4. Preparação para Machine Learning
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.analysis.score_predictor import ScorePredictor, PrevisaoPlacar


@dataclass
class HistoricoConfronto:
    """Histórico de um confronto direto entre dois times"""
    mandante: str
    visitante: str
    jogos_totais: int = 0
    vitorias_mandante: int = 0
    empates: int = 0
    vitorias_visitante: int = 0
    gols_mandante_total: int = 0
    gols_visitante_total: int = 0
    ultimos_5_resultados: List[str] = field(default_factory=list)  # ["V", "E", "D", ...]
    
    def get_tendencia_mandante(self) -> float:
        """Retorna tendência do mandante baseado no histórico (0-100)"""
        if self.jogos_totais == 0:
            return 50.0
        
        taxa_vitoria = (self.vitorias_mandante / self.jogos_totais) * 100
        return min(100, max(0, taxa_vitoria))


@dataclass
class Desfalque:
    """Representa um desfalque de time"""
    jogador: str
    tipo: str  # "lesionado", "suspenso", "duvida"
    importancia: int = 5  # 1-10 (10 = muito importante)
    posicao: str = ""
    
    def get_penalizacao(self) -> float:
        """Calcula penalização baseada no tipo e importância"""
        base_penalty = {
            "lesionado": 0.03,
            "suspenso": 0.04,
            "duvida": 0.015
        }
        
        penalty = base_penalty.get(self.tipo, 0.02)
        return penalty * (self.importancia / 5)  # Ajusta pela importância


class AdvancedScorePredictor(ScorePredictor):
    """
    Previsor avançado com funcionalidades extras:
    - Histórico de confrontos diretos
    - Sistema de desfalques
    - Preparado para Machine Learning
    """
    
    def __init__(self):
        super().__init__()
        self.historico_confrontos: Dict[str, HistoricoConfronto] = {}
        self.desfalques_times: Dict[str, List[Desfalque]] = {}
    
    def adicionar_historico_confronto(
        self,
        mandante: str,
        visitante: str,
        historico: HistoricoConfronto
    ):
        """Adiciona histórico de confronto direto"""
        chave = f"{mandante}_vs_{visitante}"
        self.historico_confrontos[chave] = historico
    
    def adicionar_desfalques(
        self,
        time: str,
        desfalques: List[Desfalque]
    ):
        """Adiciona desfalques de um time"""
        self.desfalques_times[time] = desfalques
    
    def aplicar_ajustes_historico(
        self,
        mandante: str,
        visitante: str,
        forca_mandante: float,
        forca_visitante: float
    ) -> Tuple[float, float]:
        """
        Ajusta forças baseado no histórico de confrontos diretos
        
        Estudos mostram que histórico direto tem peso de ~20% na previsão
        """
        chave = f"{mandante}_vs_{visitante}"
        historico = self.historico_confrontos.get(chave)
        
        if not historico or historico.jogos_totais < 3:
            # Sem histórico suficiente, não ajustar
            return forca_mandante, forca_visitante
        
        # Calcular tendência do histórico
        tendencia_mandante = historico.get_tendencia_mandante()
        tendencia_visitante = 100 - tendencia_mandante
        
        # Ajustar forças com peso de 20%
        PESO_HISTORICO = 0.2
        
        ajuste_mandante = (tendencia_mandante - 50) * PESO_HISTORICO
        ajuste_visitante = (tendencia_visitante - 50) * PESO_HISTORICO
        
        forca_mandante_ajustada = forca_mandante + ajuste_mandante
        forca_visitante_ajustada = forca_visitante + ajuste_visitante
        
        return forca_mandante_ajustada, forca_visitante_ajustada
    
    def aplicar_penalizacoes_desfalques(
        self,
        time: str,
        xg_base: float
    ) -> float:
        """
        Aplica penalizações por desfalques
        
        Cada desfalque reduz xG baseado em:
        - Tipo (lesionado/suspenso/dúvida)
        - Importância do jogador (1-10)
        """
        desfalques = self.desfalques_times.get(time, [])
        
        if not desfalques:
            return xg_base
        
        penalizacao_total = 0.0
        for desfalque in desfalques:
            penalizacao_total += desfalque.get_penalizacao()
        
        # Limitar penalização máxima a 30%
        penalizacao_total = min(0.30, penalizacao_total)
        
        xg_ajustado = xg_base * (1 - penalizacao_total)
        return max(0.3, xg_ajustado)  # Mínimo de 0.3 xG
    
    def prever_confronto_avancado(
        self,
        mandante: str,
        visitante: str,
        mandante_id: int = 0,
        visitante_id: int = 0,
        forca_mandante: float = 50.0,
        forca_visitante: float = 50.0,
        posicao_mandante: int = 10,
        posicao_visitante: int = 10,
        forma_mandante: str = "",
        forma_visitante: str = "",
        usar_historico: bool = True,
        usar_desfalques: bool = True
    ) -> PrevisaoPlacar:
        """
        Previsão avançada com todos os recursos
        
        Args:
            usar_historico: Se True, aplica ajustes de histórico direto
            usar_desfalques: Se True, aplica penalizações por desfalques
        """
        # 1. Ajustar forças com histórico
        if usar_historico:
            forca_mandante, forca_visitante = self.aplicar_ajustes_historico(
                mandante, visitante, forca_mandante, forca_visitante
            )
        
        # 2. Calcular xG base
        xg_mandante = self.calcular_xg(
            forca_ataque_time=forca_mandante,
            forca_defesa_adversario=forca_visitante,
            eh_mandante=True,
            posicao_time=posicao_mandante,
            posicao_adversario=posicao_visitante,
            forma_recente=forma_mandante
        )
        
        xg_visitante = self.calcular_xg(
            forca_ataque_time=forca_visitante,
            forca_defesa_adversario=forca_mandante,
            eh_mandante=False,
            posicao_time=posicao_visitante,
            posicao_adversario=posicao_mandante,
            forma_recente=forma_visitante
        )
        
        # 3. Aplicar penalizações por desfalques
        if usar_desfalques:
            xg_mandante = self.aplicar_penalizacoes_desfalques(mandante, xg_mandante)
            xg_visitante = self.aplicar_penalizacoes_desfalques(visitante, xg_visitante)
        
        # 4. Calcular probabilidades de cada placar
        probs_placar = self.calcular_probabilidades_placar(xg_mandante, xg_visitante)
        
        # 5. Encontrar top 5 placares mais prováveis
        placares_ordenados = sorted(
            probs_placar.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        # Placar mais provável
        placar_provavel = placares_ordenados[0][0]
        prob_placar_provavel = placares_ordenados[0][1]
        partes = placar_provavel.split('x')
        gols_casa = int(partes[0])
        gols_fora = int(partes[1])
        
        # 6. Calcular probabilidades de resultado
        prob_v_casa, prob_empate, prob_v_fora = self.calcular_probabilidades_resultado(
            xg_mandante, xg_visitante
        )
        
        # 7. Calcular probabilidades de gols
        probs_gols = self.calcular_probabilidades_gols(xg_mandante, xg_visitante)
        
        # 8. Calcular confiança
        diff_forca = abs(forca_mandante - forca_visitante)
        confianca_forca = min(50, diff_forca)
        confianca_placar = prob_placar_provavel * 200
        confianca = min(90, confianca_forca + confianca_placar)
        
        # 9. Preparar fatores (para ML futuro)
        fatores = {
            "forca_mandante": forca_mandante,
            "forca_visitante": forca_visitante,
            "posicao_mandante": posicao_mandante,
            "posicao_visitante": posicao_visitante,
            "forma_mandante": forma_mandante,
            "forma_visitante": forma_visitante,
            "vantagem_casa": "Sim (+35% xG)",
            "desfalques_mandante": len(self.desfalques_times.get(mandante, [])),
            "desfalques_visitante": len(self.desfalques_times.get(visitante, [])),
            "historico_usado": usar_historico,
        }
        
        # 10. Montar resultado
        return PrevisaoPlacar(
            mandante=mandante,
            visitante=visitante,
            mandante_id=mandante_id,
            visitante_id=visitante_id,
            xg_mandante=round(xg_mandante, 2),
            xg_visitante=round(xg_visitante, 2),
            placar_provavel=placar_provavel,
            placar_casa=gols_casa,
            placar_fora=gols_fora,
            probabilidade_placar=round(prob_placar_provavel * 100, 1),
            top_placares=[(p, round(prob * 100, 1)) for p, prob in placares_ordenados],
            prob_vitoria_casa=round(prob_v_casa * 100, 1),
            prob_empate=round(prob_empate * 100, 1),
            prob_vitoria_fora=round(prob_v_fora * 100, 1),
            prob_over_1_5=round(probs_gols["over_1_5"] * 100, 1),
            prob_over_2_5=round(probs_gols["over_2_5"] * 100, 1),
            prob_over_3_5=round(probs_gols["over_3_5"] * 100, 1),
            prob_btts=round(probs_gols["btts"] * 100, 1),
            confianca=round(confianca, 1),
            fatores=fatores
        )


# ==================== PREDITOR DE JOGOS CUSTOMIZADOS ====================

def prever_jogo_customizado(
    mandante: str,
    visitante: str,
    forca_mandante: float = 50.0,
    forca_visitante: float = 50.0,
    desfalques_mandante: List[Tuple[str, str, int]] = None,
    desfalques_visitante: List[Tuple[str, str, int]] = None,
    historico_vitorias_casa: int = 0,
    historico_empates: int = 0,
    historico_vitorias_fora: int = 0
) -> PrevisaoPlacar:
    """
    Prevê um jogo customizado com desfalques e histórico
    
    Args:
        mandante: Nome do time da casa
        visitante: Nome do time visitante
        forca_mandante: Força do mandante (0-100)
        forca_visitante: Força do visitante (0-100)
        desfalques_mandante: Lista de (nome, tipo, importancia)
        desfalques_visitante: Lista de (nome, tipo, importancia)
        historico_vitorias_casa: Vitórias do mandante em confrontos diretos
        historico_empates: Empates em confrontos diretos
        historico_vitorias_fora: Vitórias do visitante em confrontos diretos
    
    Returns:
        PrevisaoPlacar completa
    """
    predictor = AdvancedScorePredictor()
    
    # Adicionar histórico se fornecido
    if historico_vitorias_casa or historico_empates or historico_vitorias_fora:
        total_jogos = historico_vitorias_casa + historico_empates + historico_vitorias_fora
        historico = HistoricoConfronto(
            mandante=mandante,
            visitante=visitante,
            jogos_totais=total_jogos,
            vitorias_mandante=historico_vitorias_casa,
            empates=historico_empates,
            vitorias_visitante=historico_vitorias_fora
        )
        predictor.adicionar_historico_confronto(mandante, visitante, historico)
    
    # Adicionar desfalques se fornecidos
    if desfalques_mandante:
        desfalques = [
            Desfalque(jogador=nome, tipo=tipo, importancia=imp)
            for nome, tipo, imp in desfalques_mandante
        ]
        predictor.adicionar_desfalques(mandante, desfalques)
    
    if desfalques_visitante:
        desfalques = [
            Desfalque(jogador=nome, tipo=tipo, importancia=imp)
            for nome, tipo, imp in desfalques_visitante
        ]
        predictor.adicionar_desfalques(visitante, desfalques)
    
    # Prever
    return predictor.prever_confronto_avancado(
        mandante=mandante,
        visitante=visitante,
        forca_mandante=forca_mandante,
        forca_visitante=forca_visitante,
        usar_historico=True,
        usar_desfalques=True
    )


# ==================== TESTE ====================
if __name__ == "__main__":
    print("=" * 75)
    print("⚽ PREVISOR AVANÇADO - JOGOS CUSTOMIZADOS")
    print("=" * 75)
    
    # Jogos do fim de semana
    jogos = [
        # Super Copa do Brasil
        ("Flamengo", "Corinthians", 95, 76, [], [], 3, 2, 2),
        
        # Jogos Regionais
        ("São Paulo", "Santos", 78, 70, [], [], 5, 3, 4),
        ("Bragantino", "São Bernardo", 60, 45, [], [], 0, 0, 0),
        ("Mirassol", "Novorizontino", 82, 55, [], [], 0, 0, 0),
        ("Botafogo SP", "Palmeiras", 40, 92, [], [], 1, 2, 10),
        ("Botafogo", "Fluminense", 88, 80, [], [], 8, 5, 7),
        ("Grêmio", "Juventude", 74, 50, [], [], 12, 4, 3),
        ("Caxias", "Internacional", 35, 85, [], [], 1, 1, 8),
        ("Sport", "Santa Cruz", 52, 42, [], [], 4, 3, 2),
        
        # Jogo Internacional
        ("Tottenham", "M. City", 85, 88, [], [], 3, 6, 8),
    ]
    
    print("\n🎯 PREVISÕES DOS JOGOS DO FIM DE SEMANA:\n")
    
    for mandante, visitante, f_casa, f_fora, desf_casa, desf_fora, v_casa, emp, v_fora in jogos:
        previsao = prever_jogo_customizado(
            mandante=mandante,
            visitante=visitante,
            forca_mandante=f_casa,
            forca_visitante=f_fora,
            desfalques_mandante=desf_casa,
            desfalques_visitante=desf_fora,
            historico_vitorias_casa=v_casa,
            historico_empates=emp,
            historico_vitorias_fora=v_fora
        )
        
        print(f"📊 {mandante} vs {visitante}")
        print(f"   🎯 PLACAR PROVÁVEL: {previsao.placar_provavel} ({previsao.probabilidade_placar}%)")
        print(f"   📈 xG: {previsao.xg_mandante} vs {previsao.xg_visitante}")
        print(f"   📊 Prob: {mandante[:3]} {previsao.prob_vitoria_casa}% | Empate {previsao.prob_empate}% | {visitante[:3]} {previsao.prob_vitoria_fora}%")
        print(f"   ⚽ Over 2.5: {previsao.prob_over_2_5}% | BTTS: {previsao.prob_btts}%")
        print()
    
    print("=" * 75)
    print("✅ Recursos Implementados:")
    print("   ✅ Previsão de jogos customizados")
    print("   ✅ Sistema de desfalques integrado")
    print("   ✅ Histórico de confrontos diretos")
    print("   ✅ Preparado para Machine Learning")
    print("=" * 75)
