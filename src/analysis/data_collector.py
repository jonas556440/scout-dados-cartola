"""
Data Collector — Coleta e persistência de dados históricos

Módulo responsável por:
1. Coletar e armazenar resultados reais (gols) de cada rodada
2. Calcular dias de descanso entre jogos por time
3. Armazenar previsões pré-jogo para backtest posterior
4. Gerar relatório de calibração automática (previsão vs resultado)

Fontes: API Cartola FC (/partidas/{rodada}) — 100% gratuita.
Persistência: JSON em data/historico/

Uso:
    collector = DataCollector(api)
    collector.coletar_rodada(1)          # Salva resultados reais
    collector.salvar_previsoes(3, [...]) # Salva previsões pré-jogo
    descanso = collector.dias_descanso(clube_id=262, rodada=5)
    relatorio = collector.calibrar()     # Compara previsões vs reais
"""

import sys
import json
import math
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict

sys.path.append(str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)

# Diretório de persistência
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "historico"


@dataclass
class ResultadoPartida:
    """Resultado real de uma partida."""
    partida_id: int
    rodada: int
    clube_casa_id: int
    clube_visitante_id: int
    clube_casa_abrev: str = ""
    clube_visitante_abrev: str = ""
    placar_mandante: int = 0
    placar_visitante: int = 0
    data_jogo: str = ""              # ISO format
    timestamp: int = 0
    local: str = ""
    posicao_mandante: int = 0
    posicao_visitante: int = 0
    aproveitamento_mandante: str = ""   # "v,e,d,v,v"
    aproveitamento_visitante: str = ""


@dataclass
class PrevisaoSalva:
    """Previsão pré-jogo salva para backtest."""
    partida_id: int
    rodada: int
    mandante: str
    visitante: str
    mandante_id: int
    visitante_id: int
    placar_previsto: str
    prob_placar: float
    lambda_casa: float
    lambda_fora: float
    prob_casa: float
    prob_empate: float
    prob_fora: float
    prob_over_25: float
    prob_btts: float
    confianca: float
    forca_mandante: float = 0.0
    forca_visitante: float = 0.0
    timestamp: str = ""


class DataCollector:
    """
    Coleta, persiste e analisa dados históricos do Brasileirão.

    Fluxo automático (scheduler):
    1. Pré-jogo: salvar_previsoes(rodada, previsoes)
    2. Pós-jogo: coletar_rodada(rodada)
    3. Calibração: calibrar() compara tudo
    """

    def __init__(self, api=None):
        """
        Args:
            api: instância de CartolaAPI (None = importa automaticamente)
        """
        if api is None:
            from src.api.cartola_api import CartolaAPI
            api = CartolaAPI()
        self.api = api
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    # ==================== COLETAR RESULTADOS ====================

    def coletar_rodada(self, rodada: int, clubes: Dict[int, Any] = None) -> List[ResultadoPartida]:
        """
        Coleta resultados reais de uma rodada da API Cartola e salva em JSON.

        Args:
            rodada: número da rodada
            clubes: dict de clubes {id: {abreviacao, ...}} — se None, tenta buscar

        Returns:
            Lista de ResultadoPartida (vazia se rodada não jogada)
        """
        data = self.api.get_partidas(rodada)
        if not data:
            logger.warning(f"Sem dados para rodada {rodada}")
            return []

        partidas = data if isinstance(data, list) else data.get("partidas", [])

        # Buscar abreviações se não fornecidas
        if not clubes:
            try:
                mercado = self.api.get_mercado()
                clubes = mercado.get("clubes", {}) if mercado else {}
            except Exception:
                clubes = {}

        resultados = []
        for p in partidas:
            placar_m = p.get("placar_oficial_mandante")
            placar_v = p.get("placar_oficial_visitante")

            # Pular jogos sem placar (ainda não jogados)
            if placar_m is None or placar_v is None:
                continue

            casa_id = p.get("clube_casa_id", 0)
            visit_id = p.get("clube_visitante_id", 0)

            # Abreviações
            casa_info = clubes.get(str(casa_id), clubes.get(casa_id, {}))
            visit_info = clubes.get(str(visit_id), clubes.get(visit_id, {}))

            abrev_m = casa_info.get("abreviacao", str(casa_id)) if isinstance(casa_info, dict) else str(casa_id)
            abrev_v = visit_info.get("abreviacao", str(visit_id)) if isinstance(visit_info, dict) else str(visit_id)

            # Aproveitamento (lista de strings → "v,e,d,...")
            aprov_m = ",".join(p.get("aproveitamento_mandante", []))
            aprov_v = ",".join(p.get("aproveitamento_visitante", []))

            resultados.append(ResultadoPartida(
                partida_id=p.get("partida_id", 0),
                rodada=rodada,
                clube_casa_id=casa_id,
                clube_visitante_id=visit_id,
                clube_casa_abrev=abrev_m,
                clube_visitante_abrev=abrev_v,
                placar_mandante=placar_m,
                placar_visitante=placar_v,
                data_jogo=p.get("partida_data", ""),
                timestamp=p.get("timestamp", 0),
                local=p.get("local", ""),
                posicao_mandante=p.get("clube_casa_posicao", 0),
                posicao_visitante=p.get("clube_visitante_posicao", 0),
                aproveitamento_mandante=aprov_m,
                aproveitamento_visitante=aprov_v,
            ))

        if resultados:
            self._salvar_resultados(rodada, resultados)
            logger.info(f"✅ Rodada {rodada}: {len(resultados)} resultados coletados")

        return resultados

    def coletar_todas_rodadas(self, ate_rodada: int = 38) -> Dict[int, List[ResultadoPartida]]:
        """Coleta todas as rodadas disponíveis."""
        todos = {}
        clubes = None
        try:
            mercado = self.api.get_mercado()
            clubes = mercado.get("clubes", {}) if mercado else {}
        except Exception:
            pass

        for r in range(1, ate_rodada + 1):
            resultados = self.coletar_rodada(r, clubes)
            if resultados:
                todos[r] = resultados
            else:
                break  # Se rodada vazia, parar (não jogada ainda)

        logger.info(f"📊 Total: {sum(len(v) for v in todos.values())} jogos em {len(todos)} rodadas")
        return todos

    # ==================== SALVAR PREVISÕES PRÉ-JOGO ====================

    def salvar_previsoes(self, rodada: int, previsoes: list) -> None:
        """
        Salva previsões pré-jogo para backtest posterior.

        Args:
            rodada: número da rodada
            previsoes: lista de PrevisaoPlacar (do ScorePredictor)
        """
        previsoes_data = []
        for p in previsoes:
            previsoes_data.append(asdict(PrevisaoSalva(
                partida_id=getattr(p, 'mandante_id', 0) * 1000 + getattr(p, 'visitante_id', 0),
                rodada=rodada,
                mandante=p.mandante,
                visitante=p.visitante,
                mandante_id=getattr(p, 'mandante_id', 0),
                visitante_id=getattr(p, 'visitante_id', 0),
                placar_previsto=p.placar_provavel,
                prob_placar=p.probabilidade_placar,
                lambda_casa=p.xg_mandante,
                lambda_fora=p.xg_visitante,
                prob_casa=p.prob_vitoria_casa,
                prob_empate=p.prob_empate,
                prob_fora=p.prob_vitoria_fora,
                prob_over_25=p.prob_over_2_5,
                prob_btts=p.prob_btts,
                confianca=p.confianca,
                forca_mandante=p.fatores.get("forca_mandante", 0),
                forca_visitante=p.fatores.get("forca_visitante", 0),
                timestamp=datetime.now().isoformat(),
            )))

        filepath = DATA_DIR / f"previsoes_rodada_{rodada}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({
                "rodada": rodada,
                "timestamp": datetime.now().isoformat(),
                "modelo": "V4_Dixon-Coles",
                "previsoes": previsoes_data,
            }, f, ensure_ascii=False, indent=2)

        logger.info(f"📝 {len(previsoes_data)} previsões salvas para rodada {rodada}")

    # ==================== DIAS DE DESCANSO ====================

    def dias_descanso(self, clube_id: int, rodada: int) -> Optional[int]:
        """
        Calcula dias de descanso de um time antes de uma rodada.

        Busca a data do jogo mais recente anterior àquela rodada.
        Retorna None se não houver dados suficientes.
        """
        # Buscar jogo da rodada anterior
        for r in range(rodada - 1, 0, -1):
            resultados = self._carregar_resultados(r)
            if not resultados:
                continue
            for res in resultados:
                if res["clube_casa_id"] == clube_id or res["clube_visitante_id"] == clube_id:
                    data_anterior = res.get("data_jogo", "")
                    if not data_anterior:
                        continue
                    # Buscar data do jogo atual
                    data_atual = self._data_jogo_clube(clube_id, rodada)
                    if data_atual and data_anterior:
                        try:
                            dt_ant = datetime.strptime(data_anterior[:19], "%Y-%m-%d %H:%M:%S")
                            dt_atu = datetime.strptime(data_atual[:19], "%Y-%m-%d %H:%M:%S")
                            return (dt_atu - dt_ant).days
                        except ValueError:
                            pass
                    return None
        return None

    def dias_descanso_rodada(self, rodada: int) -> Dict[int, Optional[int]]:
        """
        Calcula dias de descanso para TODOS os times de uma rodada.

        Prioridade:
        1. Multi-competição via FixtureCollector (API-Football) — descanso REAL
        2. Fallback: apenas Brasileirão (pode superestimar se time jogou outra copa)
        3. Heurística: se >10 dias, cap em 7 (provavelmente jogou algo fora do BSA)

        Returns:
            Dict {clube_id: dias_descanso}. None se não determinável.
        """
        descanso_bsa = {}  # fallback: só Brasileirão

        # Buscar partidas da rodada atual (para saber quais times jogam e quando)
        data = self.api.get_partidas(rodada)
        if not data:
            return descanso_bsa

        partidas = data if isinstance(data, list) else data.get("partidas", [])

        for p in partidas:
            for chave_id, chave_data in [
                ("clube_casa_id", "partida_data"),
                ("clube_visitante_id", "partida_data"),
            ]:
                clube_id = p.get(chave_id)
                data_atual = p.get(chave_data, "")
                if not clube_id or not data_atual:
                    continue

                # Fallback: último jogo no Brasileirão
                dias = self._buscar_ultimo_jogo(clube_id, rodada, data_atual)
                descanso_bsa[clube_id] = dias

        # Tentar FixtureCollector para descanso multi-competição
        try:
            from src.analysis.fixture_collector import FixtureCollector
            fc = FixtureCollector()
            descanso_real = fc.dias_descanso_rodada(partidas, descanso_bsa)
            if descanso_real:
                # Mesclar: priorize real, mas preencha gaps com BSA (com cap)
                resultado = {}
                for cid in set(list(descanso_bsa.keys()) + list(descanso_real.keys())):
                    real = descanso_real.get(cid)
                    bsa = descanso_bsa.get(cid)
                    if real is not None:
                        resultado[cid] = real
                    elif bsa is not None:
                        resultado[cid] = min(bsa, 7)  # cap heurístico
                    else:
                        resultado[cid] = None
                logger.info(f"📅 Descanso rodada {rodada}: multi-competição ativo ({len(descanso_real)} times)")
                return resultado
        except Exception as e:
            logger.warning(f"⚠️ FixtureCollector indisponível, usando só BSA: {e}")

        # Fallback puro: aplicar cap para valores absurdos
        for cid, dias in descanso_bsa.items():
            if dias is not None and dias > 10:
                descanso_bsa[cid] = min(dias, 7)
        return descanso_bsa

    def _buscar_ultimo_jogo(self, clube_id: int, rodada_atual: int, data_atual: str) -> Optional[int]:
        """Busca data do último jogo de um time antes de uma rodada."""
        for r in range(rodada_atual - 1, 0, -1):
            resultados = self._carregar_resultados(r)
            if not resultados:
                continue
            for res in resultados:
                if res["clube_casa_id"] == clube_id or res["clube_visitante_id"] == clube_id:
                    data_anterior = res.get("data_jogo", "")
                    if data_anterior:
                        try:
                            dt_ant = datetime.strptime(data_anterior[:19], "%Y-%m-%d %H:%M:%S")
                            dt_atu = datetime.strptime(data_atual[:19], "%Y-%m-%d %H:%M:%S")
                            return max(0, (dt_atu - dt_ant).days)
                        except ValueError:
                            pass
                    return None
        return None

    def _data_jogo_clube(self, clube_id: int, rodada: int) -> Optional[str]:
        """Busca data do jogo de um time em determinada rodada."""
        data = self.api.get_partidas(rodada)
        if not data:
            return None
        partidas = data if isinstance(data, list) else data.get("partidas", [])
        for p in partidas:
            if p.get("clube_casa_id") == clube_id or p.get("clube_visitante_id") == clube_id:
                return p.get("partida_data", "")
        return None

    # ==================== CALIBRAÇÃO AUTOMÁTICA ====================

    def calibrar(self, rodada_inicio: int = 1, rodada_fim: int = 38) -> Dict[str, Any]:
        """
        Compara previsões salvas vs resultados reais.
        Gera relatório de calibração com log-loss, acertos, e Brier score.

        Returns:
            Dict com métricas de calibração
        """
        from src.analysis.score_predictor import ScorePredictor
        predictor = ScorePredictor()

        todas_previsoes = []
        todos_resultados = []

        for r in range(rodada_inicio, rodada_fim + 1):
            previsoes = self._carregar_previsoes(r)
            resultados = self._carregar_resultados(r)

            if not previsoes or not resultados:
                continue

            # Match por time (mandante + visitante)
            resultados_por_time = {}
            for res in resultados:
                key = (res["clube_casa_id"], res["clube_visitante_id"])
                resultados_por_time[key] = res

            for prev in previsoes:
                key = (prev["mandante_id"], prev["visitante_id"])
                res = resultados_por_time.get(key)
                if not res:
                    continue

                placar_real = f"{res['placar_mandante']}x{res['placar_visitante']}"
                todas_previsoes.append(prev)
                todos_resultados.append(placar_real)

        if not todas_previsoes:
            return {"erro": "Sem dados pareados para calibração", "jogos": 0}

        # === Métricas ===
        n = len(todas_previsoes)
        log_loss_total = 0.0
        brier_total = 0.0
        acertos_exatos = 0
        acertos_resultado = 0

        for prev, real in zip(todas_previsoes, todos_resultados):
            lc = prev["lambda_casa"]
            lf = prev["lambda_fora"]

            # Log-loss
            probs = predictor.calcular_probabilidades_placar(lc, lf)
            p_real = max(0.001, probs.get(real, 0.001))
            log_loss_total -= math.log(p_real)

            # Acerto exato
            if prev["placar_previsto"] == real:
                acertos_exatos += 1

            # Acerto V/E/D
            gc_p, gf_p = map(int, prev["placar_previsto"].split("x"))
            gc_r, gf_r = map(int, real.split("x"))
            res_prev = "V" if gc_p > gf_p else ("E" if gc_p == gf_p else "D")
            res_real = "V" if gc_r > gf_r else ("E" if gc_r == gf_r else "D")
            if res_prev == res_real:
                acertos_resultado += 1

            # Brier score (1X2)
            p_casa = prev["prob_casa"] / 100
            p_empate = prev["prob_empate"] / 100
            p_fora = prev["prob_fora"] / 100
            real_casa = 1.0 if gc_r > gf_r else 0.0
            real_empate = 1.0 if gc_r == gf_r else 0.0
            real_fora = 1.0 if gc_r < gf_r else 0.0
            brier_total += (
                (p_casa - real_casa) ** 2 +
                (p_empate - real_empate) ** 2 +
                (p_fora - real_fora) ** 2
            )

        ll_medio = log_loss_total / n
        brier_medio = brier_total / n

        # Nota
        if ll_medio < 2.5:
            nota = "EXCELENTE"
        elif ll_medio < 3.0:
            nota = "BOM"
        elif ll_medio < 3.5:
            nota = "REGULAR"
        else:
            nota = "FRACO"

        relatorio = {
            "jogos": n,
            "rodadas": f"{rodada_inicio}-{rodada_fim}",
            "log_loss": round(ll_medio, 4),
            "brier_score": round(brier_medio, 4),
            "acertos_exatos": acertos_exatos,
            "taxa_exato_pct": round(acertos_exatos / n * 100, 1),
            "acertos_resultado": acertos_resultado,
            "taxa_resultado_pct": round(acertos_resultado / n * 100, 1),
            "nota": nota,
            "modelo": "V4_Dixon-Coles",
            "timestamp": datetime.now().isoformat(),
        }

        # Salvar relatório
        filepath = DATA_DIR / "calibracao_atual.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(relatorio, f, ensure_ascii=False, indent=2)

        logger.info(
            f"📊 Calibração: {n} jogos | LL={ll_medio:.4f} | "
            f"Exatos={acertos_exatos}/{n} | V/E/D={acertos_resultado}/{n} | "
            f"Nota={nota}"
        )

        return relatorio

    # ==================== ESTATÍSTICAS DE GOLS ====================

    def gols_por_time(self, rodada_inicio: int = 1, rodada_fim: int = 38) -> Dict[int, Dict[str, Any]]:
        """
        Estatísticas de gols reais por time (ataque + defesa).

        Returns:
            Dict {clube_id: {abrev, gols_pro, gols_contra, jogos, media_pro, media_contra}}
        """
        stats = {}

        for r in range(rodada_inicio, rodada_fim + 1):
            resultados = self._carregar_resultados(r)
            if not resultados:
                continue

            for res in resultados:
                casa_id = res["clube_casa_id"]
                visit_id = res["clube_visitante_id"]
                gm = res["placar_mandante"]
                gv = res["placar_visitante"]

                for cid, gp, gc, abrev in [
                    (casa_id, gm, gv, res.get("clube_casa_abrev", "")),
                    (visit_id, gv, gm, res.get("clube_visitante_abrev", "")),
                ]:
                    if cid not in stats:
                        stats[cid] = {"abrev": abrev, "gols_pro": 0, "gols_contra": 0, "jogos": 0}
                    stats[cid]["gols_pro"] += gp
                    stats[cid]["gols_contra"] += gc
                    stats[cid]["jogos"] += 1

        # Calcular médias
        for cid, s in stats.items():
            j = s["jogos"] or 1
            s["media_pro"] = round(s["gols_pro"] / j, 2)
            s["media_contra"] = round(s["gols_contra"] / j, 2)
            s["saldo"] = s["gols_pro"] - s["gols_contra"]

        return stats

    # ==================== PERSISTÊNCIA ====================

    def _salvar_resultados(self, rodada: int, resultados: List[ResultadoPartida]) -> None:
        filepath = DATA_DIR / f"resultados_rodada_{rodada}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({
                "rodada": rodada,
                "timestamp": datetime.now().isoformat(),
                "resultados": [asdict(r) for r in resultados],
            }, f, ensure_ascii=False, indent=2)

    def _carregar_resultados(self, rodada: int) -> List[Dict]:
        filepath = DATA_DIR / f"resultados_rodada_{rodada}.json"
        if not filepath.exists():
            return []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("resultados", [])
        except (json.JSONDecodeError, IOError):
            return []

    def _carregar_previsoes(self, rodada: int) -> List[Dict]:
        filepath = DATA_DIR / f"previsoes_rodada_{rodada}.json"
        if not filepath.exists():
            return []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("previsoes", [])
        except (json.JSONDecodeError, IOError):
            return []

    # ==================== UTILIDADES ====================

    def status(self) -> Dict[str, Any]:
        """Retorna status dos dados coletados."""
        rodadas_resultados = []
        rodadas_previsoes = []
        total_jogos = 0

        for r in range(1, 39):
            res = self._carregar_resultados(r)
            prev = self._carregar_previsoes(r)
            if res:
                rodadas_resultados.append(r)
                total_jogos += len(res)
            if prev:
                rodadas_previsoes.append(r)

        calibracao_path = DATA_DIR / "calibracao_atual.json"
        calibracao = None
        if calibracao_path.exists():
            try:
                with open(calibracao_path, "r") as f:
                    calibracao = json.load(f)
            except Exception:
                pass

        return {
            "diretorio": str(DATA_DIR),
            "rodadas_com_resultados": rodadas_resultados,
            "rodadas_com_previsoes": rodadas_previsoes,
            "total_jogos": total_jogos,
            "calibracao": calibracao,
        }


# ==================== TESTE ====================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    collector = DataCollector()

    print("=" * 70)
    print("  DATA COLLECTOR — Coleta de Dados Históricos")
    print("=" * 70)

    # 1. Coletar todas as rodadas disponíveis
    print("\n📥 Coletando resultados de todas as rodadas...")
    todos = collector.coletar_todas_rodadas()

    # 2. Estatísticas de gols
    if todos:
        print("\n⚽ Gols por time:")
        stats = collector.gols_por_time()
        for cid, s in sorted(stats.items(), key=lambda x: x[1]["media_pro"], reverse=True):
            print(
                f"  {s['abrev']:>4} | GP={s['gols_pro']:>2} GC={s['gols_contra']:>2} "
                f"Saldo={s['saldo']:>+2} | MediaGP={s['media_pro']:.2f} MediaGC={s['media_contra']:.2f}"
            )

    # 3. Dias de descanso para próxima rodada
    print("\n😴 Dias de descanso (próxima rodada):")
    status = collector.api.get_status_mercado()
    if status:
        rodada_atual = status.get("rodada_atual", 3)
        descanso = collector.dias_descanso_rodada(rodada_atual)
        for cid, dias in sorted(descanso.items()):
            print(f"  Clube {cid}: {dias if dias is not None else '?'} dias")

    # 4. Status
    print("\n📊 Status:")
    st = collector.status()
    print(f"  Rodadas com resultados: {st['rodadas_com_resultados']}")
    print(f"  Total de jogos: {st['total_jogos']}")
    print(f"  Rodadas com previsões: {st['rodadas_com_previsoes']}")

    print("\n✅ Coleta concluída")
