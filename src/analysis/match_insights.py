"""
MatchInsights — Gerador de frases 100% factuais para análise de jogos.

NÃO USA IA. Cada frase é um fato estatístico verificável,
gerado a partir de dados reais (standings, H2H, forma, artilheiros).

Válido para AdSense: são fatos organizados, não opinião/AI.

Categorias de insights:
  1. Momento (sequência de vitórias/derrotas)
  2. Mando de campo (desempenho em casa/fora)
  3. Confronto direto (H2H)
  4. Gols (média, artilheiro)
  5. Classificação (posição, distância)
  6. Descanso (dias entre jogos)
  7. Último jogo H2H

Ref:
  footballpredictions.net — usa mesma abordagem factual
  Google Helpful Content: "fatos verificáveis = conteúdo útil"
"""
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

sys.path.append(str(Path(__file__).parent.parent.parent))

logger = logging.getLogger("MatchInsights")


class MatchInsights:
    """
    Gera frases factuais a partir de dados estatísticos reais.
    
    Não inventa nada — cada frase tem um dado por trás.
    Se o dado não existe, a frase não é gerada.
    """

    def gerar_insights_jogo(
        self,
        mandante: str,
        visitante: str,
        mandante_abrev: str,
        visitante_abrev: str,
        team_stats_m: Optional[Dict] = None,
        team_stats_v: Optional[Dict] = None,
        h2h: Optional[Dict] = None,
        posicao_m: Optional[Dict] = None,
        posicao_v: Optional[Dict] = None,
        artilheiro_m: Optional[Dict] = None,
        artilheiro_v: Optional[Dict] = None,
        descanso_m: Optional[int] = None,
        descanso_v: Optional[int] = None,
        rodada: Optional[int] = None,
        mandante_api_id: Optional[int] = None,
        visitante_api_id: Optional[int] = None,
    ) -> List[str]:
        """
        Gera lista de frases factuais sobre o jogo.
        
        Cada frase é um FATO verificável. Se não há dados
        suficientes, a frase simplesmente não é incluída.
        
        Returns:
            Lista de strings com insights factuais
        """
        insights: List[str] = []

        # 1. MOMENTO / SEQUÊNCIA
        insights.extend(
            self._insights_momento(mandante, visitante, team_stats_m, team_stats_v)
        )

        # 2. MANDO DE CAMPO
        insights.extend(
            self._insights_mando(
                mandante, visitante, mandante_abrev, visitante_abrev,
                team_stats_m, team_stats_v
            )
        )

        # 3. CONFRONTO DIRETO (H2H)
        insights.extend(
            self._insights_h2h(mandante, visitante, h2h,
                               mandante_api_id=mandante_api_id,
                               visitante_api_id=visitante_api_id)
        )

        # 4. GOLS
        insights.extend(
            self._insights_gols(
                mandante, visitante, mandante_abrev, visitante_abrev,
                team_stats_m, team_stats_v
            )
        )

        # 5. ARTILHEIROS
        insights.extend(
            self._insights_artilheiros(mandante, visitante, artilheiro_m, artilheiro_v)
        )

        # 6. CLASSIFICAÇÃO
        insights.extend(
            self._insights_classificacao(
                mandante, visitante, posicao_m, posicao_v
            )
        )

        # 7. DESCANSO
        insights.extend(
            self._insights_descanso(
                mandante, visitante, mandante_abrev, visitante_abrev,
                descanso_m, descanso_v
            )
        )

        return insights

    # ──────────────────── MOMENTO ────────────────────

    def _insights_momento(
        self,
        mandante: str,
        visitante: str,
        ts_m: Optional[Dict],
        ts_v: Optional[Dict],
    ) -> List[str]:
        """Sequência de resultados recentes."""
        insights = []

        for time, ts in [(mandante, ts_m), (visitante, ts_v)]:
            if not ts:
                continue
            forma = ts.get("forma") or ""
            if not forma:
                continue

            # Sequência de vitórias/derrotas consecutivas (últimos)
            seq_v = self._contar_sequencia_final(forma, "W")
            seq_d = self._contar_sequencia_final(forma, "L")
            seq_inv = self._contar_invicto_final(forma)
            seq_sem_vencer = self._contar_sem_vencer_final(forma)

            if seq_v >= 3:
                insights.append(
                    f"{time} vem embalado com {seq_v} vitórias consecutivas."
                )
            elif seq_d >= 3:
                insights.append(
                    f"{time} vive má fase com {seq_d} derrotas consecutivas."
                )

            if seq_inv >= 5:
                insights.append(
                    f"{time} está invicto há {seq_inv} jogos."
                )
            elif seq_sem_vencer >= 4 and seq_d < 3:
                insights.append(
                    f"{time} não vence há {seq_sem_vencer} jogos."
                )

        return insights

    # ──────────────────── MANDO DE CAMPO ────────────────────

    def _insights_mando(
        self,
        mandante: str,
        visitante: str,
        abrev_m: str,
        abrev_v: str,
        ts_m: Optional[Dict],
        ts_v: Optional[Dict],
    ) -> List[str]:
        """Desempenho em casa (mandante) e fora (visitante)."""
        insights = []

        # Mandante em casa
        if ts_m:
            v_casa = ts_m.get("vitorias", {}).get("casa", 0)
            j_casa = ts_m.get("jogos", {}).get("casa", 0)
            d_casa = ts_m.get("derrotas", {}).get("casa", 0)
            
            if j_casa > 0:
                pct_v = round(v_casa / j_casa * 100) if j_casa else 0
                if v_casa >= 8 and pct_v >= 60:
                    insights.append(
                        f"{mandante} é forte em casa: {v_casa} vitórias em "
                        f"{j_casa} jogos ({pct_v}% de aproveitamento)."
                    )
                elif d_casa == 0 and j_casa >= 5:
                    insights.append(
                        f"{mandante} ainda não perdeu em casa nesta temporada "
                        f"({j_casa} jogos)."
                    )
                elif d_casa >= 5:
                    insights.append(
                        f"{mandante} já perdeu {d_casa} vezes em casa "
                        f"nesta temporada."
                    )

        # Visitante fora
        if ts_v:
            v_fora = ts_v.get("vitorias", {}).get("fora", 0)
            j_fora = ts_v.get("jogos", {}).get("fora", 0)
            d_fora = ts_v.get("derrotas", {}).get("fora", 0)
            
            if j_fora > 0:
                pct_v = round(v_fora / j_fora * 100) if j_fora else 0
                if v_fora >= 7 and pct_v >= 50:
                    insights.append(
                        f"{visitante} tem bom desempenho fora de casa: "
                        f"{v_fora} vitórias em {j_fora} jogos como visitante."
                    )
                elif d_fora >= 8:
                    insights.append(
                        f"{visitante} sofre fora de casa: {d_fora} derrotas "
                        f"em {j_fora} jogos como visitante."
                    )

        return insights

    # ──────────────────── H2H ────────────────────

    def _insights_h2h(
        self,
        mandante: str,
        visitante: str,
        h2h: Optional[Dict],
        mandante_api_id: Optional[int] = None,
        visitante_api_id: Optional[int] = None,
    ) -> List[str]:
        """Confrontos diretos históricos."""
        insights = []
        if not h2h:
            return insights

        total = h2h.get("total", h2h.get("total_jogos", 0))
        if total == 0:
            return insights

        # Determinar vitórias de cada lado
        # w_mandante = vitórias do mandante, w_visitante = vitórias do visitante
        w_mandante = 0
        w_visitante = 0
        draws = 0

        # Formato StatsEnricher
        stats = h2h.get("stats", {})
        if stats:
            t1_id = h2h.get("team1_id")
            t2_id = h2h.get("team2_id")
            t1_wins = stats.get("team1_wins", 0)
            t2_wins = stats.get("team2_wins", 0)
            draws = stats.get("draws", 0)
            # Remapear: quem é team1? Usar API IDs para determinar
            if mandante_api_id is not None and t1_id is not None:
                if t1_id == mandante_api_id:
                    w_mandante, w_visitante = t1_wins, t2_wins
                else:
                    w_mandante, w_visitante = t2_wins, t1_wins
            else:
                # Fallback sem IDs: team1=mandante (pode estar errado)
                w_mandante, w_visitante = t1_wins, t2_wins
        # Formato FootballDataClient
        elif "vitorias_casa" in h2h:
            w_mandante = h2h.get("vitorias_casa", 0)
            w_visitante = h2h.get("vitorias_fora", 0)
            draws = h2h.get("empates", 0)
        else:
            return insights

        if total >= 5:
            # Domínio claro
            if w_mandante >= w_visitante * 2 and w_mandante >= 3:
                insights.append(
                    f"No histórico geral de confrontos, {mandante} domina com {w_mandante} vitórias "
                    f"contra {w_visitante} do {visitante} nos últimos {total} jogos."
                )
            elif w_visitante >= w_mandante * 2 and w_visitante >= 3:
                insights.append(
                    f"No histórico geral de confrontos, {visitante} domina com {w_visitante} vitórias "
                    f"contra {w_mandante} do {mandante} nos últimos {total} jogos."
                )
            elif abs(w_mandante - w_visitante) <= 2:
                insights.append(
                    f"Histórico equilibrado: {w_mandante} vitórias do {mandante}, "
                    f"{draws} empates e {w_visitante} do {visitante} nos últimos {total} jogos."
                )

        # Último jogo
        ultimos = h2h.get("ultimos_5", h2h.get("ultimos", []))
        if ultimos:
            ult = ultimos[0]
            gm = ult.get("gols_mandante", ult.get("gols_m"))
            gv = ult.get("gols_visitante", ult.get("gols_v"))
            data = ult.get("data", "")[:10]
            m_nome = ult.get("mandante", "")
            v_nome = ult.get("visitante", "")
            if gm is not None and gv is not None:
                insights.append(
                    f"Último confronto: {m_nome} {gm}x{gv} {v_nome} "
                    f"({data})."
                )
                # Goleada?
                diff = abs(gm - gv)
                if diff >= 4:
                    vencedor = m_nome if gm > gv else v_nome
                    insights.append(
                        f"No último encontro, {vencedor} aplicou goleada "
                        f"de {max(gm,gv)} a {min(gm,gv)}."
                    )

        return insights

    # ──────────────────── GOLS ────────────────────

    def _insights_gols(
        self,
        mandante: str,
        visitante: str,
        abrev_m: str,
        abrev_v: str,
        ts_m: Optional[Dict],
        ts_v: Optional[Dict],
    ) -> List[str]:
        """Estatísticas de gols (ataque/defesa)."""
        insights = []

        for time, abrev, ts, local in [
            (mandante, abrev_m, ts_m, "casa"),
            (visitante, abrev_v, ts_v, "fora"),
        ]:
            if not ts:
                continue

            gp = ts.get("gols_pro", {})
            gc = ts.get("gols_contra", {})
            cs = ts.get("clean_sheets", {})
            jogos_total = ts.get("jogos", {}).get("total", 0)

            if jogos_total == 0:
                continue

            # Média de gols
            try:
                media_gp = float(gp.get("media", 0))
                media_gc = float(gc.get("media", 0))
            except (ValueError, TypeError):
                continue

            if media_gp >= 2.0:
                insights.append(
                    f"{time} é um time ofensivo: média de {media_gp} gols por jogo."
                )
            elif media_gp <= 0.8:
                insights.append(
                    f"{time} tem dificuldade para marcar: média de apenas "
                    f"{media_gp} gol por jogo."
                )

            if media_gc >= 2.0:
                insights.append(
                    f"{time} sofre defensivamente: média de {media_gc} gols "
                    f"sofridos por jogo."
                )

            # Clean sheets
            cs_total = cs.get("total", 0)
            if cs_total >= 10 and jogos_total >= 20:
                pct_cs = round(cs_total / jogos_total * 100)
                insights.append(
                    f"{time} tem defesa sólida: {cs_total} jogos sem sofrer "
                    f"gol ({pct_cs}%)."
                )

            # Gols em casa vs fora
            gp_casa = gp.get("casa", 0)
            gp_fora = gp.get("fora", 0)
            j_casa = ts.get("jogos", {}).get("casa", 0)
            j_fora = ts.get("jogos", {}).get("fora", 0)

            if j_casa > 5 and j_fora > 5:
                media_casa = gp_casa / j_casa
                media_fora = gp_fora / j_fora
                if media_casa >= media_fora * 1.5 and media_casa >= 1.5:
                    insights.append(
                        f"{time} marca muito mais em casa ({gp_casa} gols) "
                        f"do que fora ({gp_fora} gols)."
                    )

        return insights

    # ──────────────────── ARTILHEIROS ────────────────────

    def _insights_artilheiros(
        self,
        mandante: str,
        visitante: str,
        art_m: Optional[Dict],
        art_v: Optional[Dict],
    ) -> List[str]:
        """Destaque para artilheiros dos times."""
        insights = []

        for time, art in [(mandante, art_m), (visitante, art_v)]:
            if not art:
                continue
            gols = art.get("gols") or 0
            nome = art.get("jogador", "")
            if gols >= 5 and nome:
                assists = art.get("assists") or 0
                extra = f" e {assists} assistências" if assists >= 3 else ""
                insights.append(
                    f"Destaque para {nome}, artilheiro do {time} "
                    f"com {gols} gols{extra} na temporada."
                )

        return insights

    # ──────────────────── CLASSIFICAÇÃO ────────────────────

    def _insights_classificacao(
        self,
        mandante: str,
        visitante: str,
        pos_m: Optional[Dict],
        pos_v: Optional[Dict],
    ) -> List[str]:
        """Contexto de classificação e posição na tabela."""
        insights = []

        if pos_m and pos_v:
            pm = pos_m.get("posicao", 0)
            pv = pos_v.get("posicao", 0)
            pts_m = pos_m.get("pontos", 0)
            pts_v = pos_v.get("pontos", 0)

            if pm <= 4 and pv <= 4:
                insights.append(
                    f"Confronto direto na parte de cima da tabela: "
                    f"{mandante} ({pm}º, {pts_m}pts) x "
                    f"{visitante} ({pv}º, {pts_v}pts)."
                )
            elif pm >= 17 and pv >= 17:
                insights.append(
                    f"Confronto direto na zona de rebaixamento: "
                    f"{mandante} ({pm}º) x {visitante} ({pv}º). "
                    f"Jogo de seis pontos."
                )
            elif pm <= 6 and pv >= 15:
                insights.append(
                    f"Contraste na tabela: {mandante} ({pm}º, briga por "
                    f"título/Libertadores) x {visitante} ({pv}º, "
                    f"{'zona de rebaixamento' if pv >= 17 else 'parte inferior'})."
                )
            elif pv <= 6 and pm >= 15:
                insights.append(
                    f"Contraste na tabela: {mandante} ({pm}º, "
                    f"{'zona de rebaixamento' if pm >= 17 else 'parte inferior'}) "
                    f"x {visitante} ({pv}º, briga por título/Libertadores)."
                )

            # Distância entre eles
            diff_pts = abs(pts_m - pts_v)
            if diff_pts <= 3 and abs(pm - pv) <= 3:
                insights.append(
                    f"Times separados por apenas {diff_pts} pontos "
                    f"na tabela ({mandante} {pm}º x {visitante} {pv}º)."
                )

        # Forma individual
        for time, pos in [(mandante, pos_m), (visitante, pos_v)]:
            if not pos:
                continue
            forma = pos.get("forma", "")
            if forma:
                # Contar últimos 5
                f5 = forma.replace(",", "")[-5:]
                v = f5.count("W")
                d = f5.count("L")
                e = f5.count("D")
                if v >= 4:
                    insights.append(
                        f"{time} em grande fase: {v} vitórias nos últimos 5 jogos."
                    )
                elif d >= 4:
                    insights.append(
                        f"{time} em crise: {d} derrotas nos últimos 5 jogos."
                    )

        return insights

    # ──────────────────── DESCANSO ────────────────────

    def _insights_descanso(
        self,
        mandante: str,
        visitante: str,
        abrev_m: str,
        abrev_v: str,
        desc_m: Optional[int],
        desc_v: Optional[int],
    ) -> List[str]:
        """Diferença de descanso entre os times."""
        insights = []
        if desc_m is None or desc_v is None:
            return insights

        diff = abs(desc_m - desc_v)
        if diff >= 3:
            mais = mandante if desc_m > desc_v else visitante
            menos = visitante if desc_m > desc_v else mandante
            d_mais = max(desc_m, desc_v)
            d_menos = min(desc_m, desc_v)
            insights.append(
                f"Vantagem de descanso para o {mais} ({d_mais} dias) "
                f"contra {d_menos} dias do {menos}."
            )

        if desc_m <= 2:
            insights.append(
                f"{mandante} joga com curto intervalo de descanso "
                f"({desc_m} dias)."
            )
        if desc_v <= 2:
            insights.append(
                f"{visitante} joga com curto intervalo de descanso "
                f"({desc_v} dias)."
            )

        return insights

    # ──────────────────── Helpers ────────────────────

    @staticmethod
    def _contar_sequencia_final(forma: str, char: str) -> int:
        """Conta sequência consecutiva de `char` no final da forma."""
        count = 0
        for c in reversed(forma):
            if c == char:
                count += 1
            else:
                break
        return count

    @staticmethod
    def _contar_invicto_final(forma: str) -> int:
        """Conta sequência sem derrota (W ou D) no final."""
        count = 0
        for c in reversed(forma):
            if c in ("W", "D"):
                count += 1
            else:
                break
        return count

    @staticmethod
    def _contar_sem_vencer_final(forma: str) -> int:
        """Conta sequência sem vitória (L ou D) no final."""
        count = 0
        for c in reversed(forma):
            if c in ("L", "D"):
                count += 1
            else:
                break
        return count

    # ──────────────────── Formatação para Markdown ────────────────────

    def formatar_secao_insights(self, insights: List[str]) -> str:
        """Formata insights como bloco markdown para publicação."""
        if not insights:
            return ""
        lines = ["**📋 O que esperar deste jogo:**\n"]
        for frase in insights:
            lines.append(f"- {frase}")
        lines.append("")
        return "\n".join(lines)

    def formatar_forma_emoji(self, forma: str, ultimos: int = 5) -> str:
        """Converte string de forma (WDLWW) em emoji."""
        if not forma:
            return ""
        trecho = forma[-ultimos:]
        mapa = {"W": "🟢", "D": "🟡", "L": "🔴"}
        return " ".join(mapa.get(c, "⚪") for c in trecho)
