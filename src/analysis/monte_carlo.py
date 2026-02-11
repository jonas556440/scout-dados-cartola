"""
Simulador Monte Carlo - Campeonato Brasileiro 2025

Simula o restante do campeonato N vezes usando o ScorePredictor para gerar
probabilidades de cada time: título, Libertadores (G4), Sul-Americana (G6-G12),
rebaixamento (Z4).

Referências:
- Método Monte Carlo para previsões esportivas
- Integração com ScorePredictor V3 (Poisson + frequências contextuais)
"""

import random
import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict


@dataclass
class TimeClassificacao:
    """Dados de um time na classificação."""
    id: int
    nome: str
    abrev: str
    pontos: int = 0
    jogos: int = 0
    vitorias: int = 0
    empates: int = 0
    derrotas: int = 0
    gols_pro: int = 0
    gols_contra: int = 0
    
    @property
    def saldo_gols(self) -> int:
        return self.gols_pro - self.gols_contra
    
    @property
    def aproveitamento(self) -> float:
        if self.jogos == 0:
            return 0
        return (self.pontos / (self.jogos * 3)) * 100


@dataclass
class ResultadoSimulacao:
    """Resultado consolidado de N simulações."""
    time_id: int
    nome: str
    abrev: str
    simulacoes: int
    pontos_medio: float = 0
    pontos_min: int = 999
    pontos_max: int = 0
    prob_titulo: float = 0        # % campeão
    prob_libertadores: float = 0  # % G4
    prob_sulamericana: float = 0  # % G5-G12 (pré-libertadores + sula)
    prob_rebaixamento: float = 0  # % Z4
    posicao_media: float = 0


@dataclass
class PontosNecessarios:
    """Pontos mínimos necessários para cada objetivo por probabilidade."""
    probabilidade: int  # 50, 70, 80, 90, 95, 99, 100
    titulo: int = 0
    libertadores: int = 0       # G4
    sulamericana: int = 0       # G5-G12
    permanencia: int = 0        # Fora do Z4


class MonteCarloSimulator:
    """
    Simula o restante do Campeonato Brasileiro usando Monte Carlo.
    
    Usa xG do ScorePredictor para gerar gols via Poisson e acumula
    posições finais em N simulações.
    """
    
    def __init__(self, score_predictor=None, n_simulacoes: int = 1000):
        self.score_predictor = score_predictor
        self.n_simulacoes = n_simulacoes
    
    def _gols_poisson(self, xg: float) -> int:
        """Gera gols aleatórios via distribuição de Poisson."""
        L = math.exp(-xg)
        k = 0
        p = 1.0
        while True:
            k += 1
            p *= random.random()
            if p < L:
                return k - 1
    
    def _classificar(self, times: Dict[int, TimeClassificacao]) -> List[TimeClassificacao]:
        """Ordena tabela por pontos > vitórias > saldo > gols pro."""
        return sorted(
            times.values(),
            key=lambda t: (t.pontos, t.vitorias, t.saldo_gols, t.gols_pro),
            reverse=True
        )
    
    def simular_campeonato(
        self,
        classificacao_atual: List[Dict],
        jogos_restantes: List[Dict],
        forca_times: Dict[int, float],
        forca_ataque_times: Optional[Dict[int, float]] = None,
        forca_defesa_times: Optional[Dict[int, float]] = None,
        xg_cache: Optional[Dict[Tuple[int, int], Tuple[float, float]]] = None,
    ) -> List[ResultadoSimulacao]:
        """
        Executa N simulações Monte Carlo.
        
        Args:
            classificacao_atual: Lista com dados atuais de cada time
            jogos_restantes: Partidas que ainda não ocorreram
            forca_times: Dict[time_id] -> força geral (0-100)
            forca_ataque_times: Dict[time_id] -> força de ataque (V5)
            forca_defesa_times: Dict[time_id] -> força de defesa (V5)
        
        Returns:
            Lista de ResultadoSimulacao ordenada por posição média
        """
        n = self.n_simulacoes

        # Garantir que xg_cache existe para evitar recalcular prever_confronto
        # em cada simulação (380 jogos × 300 sims = 114k chamadas redundantes)
        if xg_cache is None:
            xg_cache = {}

        # Contadores por time
        contadores: Dict[int, Dict] = {}
        # Rastrear distribuição pontos × posição para "Pontos Necessários"
        # pontos_posicao[pontos] = {"titulo": count, "g4": count, "sula": count, "z4": count, "total": count}
        pontos_posicao: Dict[int, Dict[str, int]] = {}
        
        for time_data in classificacao_atual:
            tid = time_data["id"]
            contadores[tid] = {
                "nome": time_data.get("nome", ""),
                "abrev": time_data.get("abrev", ""),
                "titulos": 0,
                "g4": 0,
                "sula": 0,  # posições 5-12
                "z4": 0,
                "pontos_total": 0,
                "pontos_min": 999,
                "pontos_max": 0,
                "posicao_total": 0,
            }
        
        for _ in range(n):
            # Copiar classificação atual
            times: Dict[int, TimeClassificacao] = {}
            for td in classificacao_atual:
                times[td["id"]] = TimeClassificacao(
                    id=td["id"],
                    nome=td.get("nome", ""),
                    abrev=td.get("abrev", ""),
                    pontos=td.get("pontos", 0),
                    jogos=td.get("jogos", 0),
                    vitorias=td.get("vitorias", 0),
                    empates=td.get("empates", 0),
                    derrotas=td.get("derrotas", 0),
                    gols_pro=td.get("gols_pro", 0),
                    gols_contra=td.get("gols_contra", 0),
                )
            
            # Simular cada jogo restante
            for jogo in jogos_restantes:
                mid = jogo["mandante_id"]
                vid = jogo["visitante_id"]
                
                if mid not in times or vid not in times:
                    continue
                
                fm = forca_times.get(mid, 50)
                fv = forca_times.get(vid, 50)

                # Usar cache de xG quando disponível (evita chamadas repetidas ao predictor)
                cache_key = (mid, vid)
                if xg_cache and cache_key in xg_cache:
                    xg_m, xg_v = xg_cache[cache_key]
                else:
                    # Calcular xG determinístico com fator casa (variância vem do Poisson)
                    xg_m = max(0.3, (fm / 50) * 1.2)
                    xg_v = max(0.3, (fv / 50) * 0.9)
                    
                    # Se temos ScorePredictor, usamos xG dele (V5: forças separadas)
                    if self.score_predictor:
                        try:
                            # V5: Extrair forças ataque/defesa separadas se disponíveis
                            fatk_m = forca_ataque_times.get(mid, fm) if forca_ataque_times else fm
                            fdef_m = forca_defesa_times.get(mid, fm) if forca_defesa_times else fm
                            fatk_v = forca_ataque_times.get(vid, fv) if forca_ataque_times else fv
                            fdef_v = forca_defesa_times.get(vid, fv) if forca_defesa_times else fv
                            previsao = self.score_predictor.prever_confronto(
                                mandante=times[mid].abrev,
                                visitante=times[vid].abrev,
                                mandante_id=mid,
                                visitante_id=vid,
                                forca_mandante=fm,
                                forca_visitante=fv,
                                forca_ataque_mandante=fatk_m,
                                forca_defesa_mandante=fdef_m,
                                forca_ataque_visitante=fatk_v,
                                forca_defesa_visitante=fdef_v,
                            )
                            xg_m = previsao.xg_mandante
                            xg_v = previsao.xg_visitante
                        except Exception:
                            pass
                    # Cachear para reutilizar nas próximas simulações
                    if xg_cache is not None:
                        xg_cache[cache_key] = (xg_m, xg_v)
                
                gols_m = self._gols_poisson(xg_m)
                gols_v = self._gols_poisson(xg_v)
                
                # Atualizar tabela
                tm = times[mid]
                tv = times[vid]
                
                tm.jogos += 1
                tv.jogos += 1
                tm.gols_pro += gols_m
                tm.gols_contra += gols_v
                tv.gols_pro += gols_v
                tv.gols_contra += gols_m
                
                if gols_m > gols_v:
                    tm.pontos += 3
                    tm.vitorias += 1
                    tv.derrotas += 1
                elif gols_m < gols_v:
                    tv.pontos += 3
                    tv.vitorias += 1
                    tm.derrotas += 1
                else:
                    tm.pontos += 1
                    tv.pontos += 1
                    tm.empates += 1
                    tv.empates += 1
            
            # Classificação final
            tabela = self._classificar(times)
            
            for pos, time in enumerate(tabela, 1):
                c = contadores.get(time.id)
                if not c:
                    continue
                
                c["posicao_total"] += pos
                c["pontos_total"] += time.pontos
                c["pontos_min"] = min(c["pontos_min"], time.pontos)
                c["pontos_max"] = max(c["pontos_max"], time.pontos)
                
                if pos == 1:
                    c["titulos"] += 1
                if pos <= 4:
                    c["g4"] += 1
                if 5 <= pos <= 12:
                    c["sula"] += 1
                if pos >= 17:  # Z4 do Brasileirão
                    c["z4"] += 1
                
                # Rastrear distribuição pontos × posição
                pts = time.pontos
                if pts not in pontos_posicao:
                    pontos_posicao[pts] = {"titulo": 0, "g4": 0, "g12": 0, "z4": 0, "permanencia": 0, "total": 0}
                pontos_posicao[pts]["total"] += 1
                if pos == 1:
                    pontos_posicao[pts]["titulo"] += 1
                if pos <= 4:
                    pontos_posicao[pts]["g4"] += 1
                if pos <= 12:
                    pontos_posicao[pts]["g12"] += 1  # G-12 = Sul-Americana ou melhor
                if pos >= 17:
                    pontos_posicao[pts]["z4"] += 1
                if pos <= 16:
                    pontos_posicao[pts]["permanencia"] += 1
        
        # Montar resultados
        resultados = []
        for tid, c in contadores.items():
            resultados.append(ResultadoSimulacao(
                time_id=tid,
                nome=c["nome"],
                abrev=c["abrev"],
                simulacoes=n,
                pontos_medio=round(c["pontos_total"] / n, 1),
                pontos_min=c["pontos_min"] if c["pontos_min"] < 999 else 0,
                pontos_max=c["pontos_max"],
                prob_titulo=round(c["titulos"] / n * 100, 1),
                prob_libertadores=round(c["g4"] / n * 100, 1),
                prob_sulamericana=round(c["sula"] / n * 100, 1),
                prob_rebaixamento=round(c["z4"] / n * 100, 1),
                posicao_media=round(c["posicao_total"] / n, 1),
            ))
        
        resultados.sort(key=lambda r: r.posicao_media)
        
        # Calcular pontos necessários por probabilidade
        pontos_necessarios = self._calcular_pontos_necessarios(pontos_posicao, n)
        
        return resultados, pontos_necessarios
    
    def _calcular_pontos_necessarios(
        self, 
        pontos_posicao: Dict[int, Dict[str, int]], 
        n_simulacoes: int
    ) -> List[PontosNecessarios]:
        """
        Calcula os pontos mínimos necessários para cada objetivo em cada faixa de probabilidade.
        
        Para cada faixa de probabilidade (50%, 70%, 80%, 90%, 95%, 99%, 100%),
        calcula quantos pontos são necessários para ter pelo menos essa probabilidade
        de atingir cada objetivo (título, G4, sulamericana, permanência).
        """
        faixas = [50, 70, 80, 90, 95, 99, 100]
        objetivos = ["titulo", "g4", "g12", "permanencia"]
        
        # Ordenar pontos decrescente
        pontos_ordenados = sorted(pontos_posicao.keys(), reverse=True)
        
        resultado = []
        for faixa in faixas:
            pn = PontosNecessarios(probabilidade=faixa)
            
            for objetivo in objetivos:
                # Acumular de cima para baixo: encontrar o menor pontos
                # onde a probabilidade acumulada >= faixa%
                acum_objetivo = 0
                acum_total = 0
                pontos_encontrado = 0
                
                for pts in pontos_ordenados:
                    dados = pontos_posicao[pts]
                    acum_objetivo += dados.get(objetivo, 0)
                    acum_total += dados["total"]
                    
                    if acum_total > 0:
                        prob = (acum_objetivo / acum_total) * 100
                        if prob >= faixa:
                            pontos_encontrado = pts
                
                # Para permanência, queremos o mínimo de pontos para ficar fora do Z4
                # Para os demais, queremos o mínimo de pontos para atingir o objetivo
                if objetivo == "titulo":
                    pn.titulo = pontos_encontrado
                elif objetivo == "g4":
                    pn.libertadores = pontos_encontrado
                elif objetivo == "g12":
                    pn.sulamericana = pontos_encontrado
                elif objetivo == "permanencia":
                    pn.permanencia = pontos_encontrado
            
            resultado.append(pn)
        
        return resultado


if __name__ == "__main__":
    # Teste rápido com dados fictícios
    sim = MonteCarloSimulator(n_simulacoes=500)
    
    times_teste = [
        {"id": 1, "nome": "Time A", "abrev": "TMA", "pontos": 30, "jogos": 15, "vitorias": 9, "empates": 3, "derrotas": 3, "gols_pro": 25, "gols_contra": 12},
        {"id": 2, "nome": "Time B", "abrev": "TMB", "pontos": 28, "jogos": 15, "vitorias": 8, "empates": 4, "derrotas": 3, "gols_pro": 22, "gols_contra": 14},
        {"id": 3, "nome": "Time C", "abrev": "TMC", "pontos": 15, "jogos": 15, "vitorias": 4, "empates": 3, "derrotas": 8, "gols_pro": 12, "gols_contra": 20},
        {"id": 4, "nome": "Time D", "abrev": "TMD", "pontos": 10, "jogos": 15, "vitorias": 2, "empates": 4, "derrotas": 9, "gols_pro": 8, "gols_contra": 25},
    ]
    
    jogos = [
        {"mandante_id": 1, "visitante_id": 3, "rodada": 16},
        {"mandante_id": 2, "visitante_id": 4, "rodada": 16},
        {"mandante_id": 3, "visitante_id": 2, "rodada": 17},
        {"mandante_id": 4, "visitante_id": 1, "rodada": 17},
    ]
    
    forcas = {1: 70, 2: 65, 3: 40, 4: 30}
    
    resultados, pontos_nec = sim.simular_campeonato(times_teste, jogos, forcas)
    
    print(f"{'Time':<10} {'Pos Média':>10} {'Pts Médio':>10} {'Título':>8} {'G4':>8} {'Z4':>8}")
    print("-" * 60)
    for r in resultados:
        print(f"{r.abrev:<10} {r.posicao_media:>10.1f} {r.pontos_medio:>10.1f} {r.prob_titulo:>7.1f}% {r.prob_libertadores:>7.1f}% {r.prob_rebaixamento:>7.1f}%")
