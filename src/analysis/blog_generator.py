"""
Gerador automático de posts de blog por rodada.

Gera análise de confrontos de cada rodada com:
- Previsões de placar (Poisson + Dixon-Coles V4)
- xG de cada jogo
- Dias de descanso entre rodadas
- Gols reais por time (histórico coletado)
- Calibração do modelo (auto-avaliação)
- Destaques/dicas para Cartola
- Análise dos times mandante/visitante

Chamado pelo scheduler_service.py a cada rodada.
Resultado salvo em data/blog_posts/ como JSON, servido pela API.
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.api.cartola_api import CartolaAPI
from src.analysis.score_predictor import ScorePredictor
from src.analysis.confrontos_analyzer import ConfrontosAnalyzer


POSTS_DIR = Path(__file__).parent.parent.parent / "data" / "blog_posts"
POSTS_DIR.mkdir(parents=True, exist_ok=True)


def _slugify(text: str) -> str:
    """Converte texto para slug URL-safe."""
    import re
    text = text.lower().strip()
    # Mapa de acentos
    replacements = {
        'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a',
        'é': 'e', 'ê': 'e', 'í': 'i', 'ó': 'o',
        'ô': 'o', 'õ': 'o', 'ú': 'u', 'ü': 'u',
        'ç': 'c',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def gerar_post_rodada(rodada: int, api: Optional[CartolaAPI] = None) -> Dict[str, Any]:
    """
    Gera um post automático de análise de confrontos para a rodada.
    
    Returns:
        Dict com slug, title, date, excerpt, content, tags, readTime
    """
    if api is None:
        api = CartolaAPI()
    
    predictor = ScorePredictor()
    analyzer = ConfrontosAnalyzer()
    
    # Inicializar DataCollector para dados enriquecidos
    descanso_rodada: Dict[int, Optional[int]] = {}
    gols_stats: Dict[int, Any] = {}
    calibracao: Optional[Dict] = None
    try:
        from src.analysis.data_collector import DataCollector
        collector = DataCollector(api)
        descanso_rodada = collector.dias_descanso_rodada(rodada)
        gols_stats = collector.gols_por_time()
        calibracao = collector.calibrar()
    except Exception:
        pass  # Graceful fallback se DataCollector falhar
    
    # Inicializar StatsEnricher para dados API-Football (xG, H2H, forma, etc.)
    enriched_data: Dict[str, Any] = {}
    enricher = None
    try:
        from src.analysis.stats_enricher import StatsEnricher
        from src.analysis.fixture_collector import CARTOLA_TO_APIFOOTBALL
        enricher = StatsEnricher()
        # Budget conservador: máx 25 req por geração de post
        partidas_data_temp = api.get_partidas(rodada)
        partidas_temp = partidas_data_temp.get("partidas", []) if partidas_data_temp else []
        if partidas_temp:
            enriched_data = enricher.enriquecer_rodada(partidas_temp, budget_max=25)
    except Exception:
        pass  # Graceful fallback

    # football-data.org: artilheiros + classificação 2025/26 (fallback/complemento)
    fdo_client = None
    fdo_artilheiros: List[Dict] = []
    fdo_classificacao: List[Dict] = []
    fdo_matches: List[Dict] = []
    try:
        from src.analysis.football_data_client import FootballDataClient
        fdo_client = FootballDataClient()
        fdo_artilheiros = fdo_client.artilheiros(limit=30) or []
        fdo_classificacao = fdo_client.classificacao() or []
        fdo_matches = fdo_client.jogos_rodada(rodada) or []
    except Exception:
        pass

    # MatchInsights: frases 100% factuais
    insights_gen = None
    try:
        from src.analysis.match_insights import MatchInsights
        insights_gen = MatchInsights()
    except Exception:
        pass
    
    # Buscar dados da rodada
    partidas_data = api.get_partidas(rodada)
    mercado = api.get_mercado()
    
    if not partidas_data or not mercado:
        return {}
    
    partidas = partidas_data.get("partidas", [])
    clubes = mercado.get("clubes", {})
    atletas = mercado.get("atletas", [])
    
    if not partidas:
        return {}
    
    # Calcular forças dos times REAIS baseadas na média dos atletas
    forcas = {}
    status = api.get_status_mercado()
    rodada_atual = status.get("rodada_atual", rodada) if status else rodada
    
    for clube_id, clube in clubes.items():
        cid = int(clube_id)
        # Calcular força baseada na média dos atletas do time
        atletas_time = [a for a in atletas if a.get("clube_id") == cid]
        if atletas_time:
            media_time = sum(a.get("media_num", 0) for a in atletas_time) / len(atletas_time)
            # Atacantes e meiocampistas contam mais para ataque
            atacantes = [a for a in atletas_time if a.get("posicao_id") in [4, 5]]
            media_ataque = sum(a.get("media_num", 0) for a in atacantes) / max(len(atacantes), 1) if atacantes else media_time
            # Zagueiros e goleiros contam mais para defesa
            defensores = [a for a in atletas_time if a.get("posicao_id") in [1, 2, 3]]
            media_defesa = sum(a.get("media_num", 0) for a in defensores) / max(len(defensores), 1) if defensores else media_time
            
            # Converter média (0-15) para força (20-80)
            forca_atq = max(20, min(80, 30 + media_ataque * 4))
            forca_def = max(20, min(80, 30 + media_defesa * 4))
        else:
            forca_atq, forca_def = 50, 50
        
        forcas[cid] = {
            "nome": clube.get("nome", ""),
            "abrev": clube.get("abreviacao", ""),
            "forca_ataque": forca_atq,
            "forca_defesa": forca_def,
        }
    
    # Gerar previsões para cada jogo
    jogos_analise = []
    for partida in partidas:
        mandante_id = partida.get("clube_casa_id", 0)
        visitante_id = partida.get("clube_visitante_id", 0)
        mandante_info = clubes.get(str(mandante_id), {})
        visitante_info = clubes.get(str(visitante_id), {})
        
        mandante_nome = mandante_info.get("nome", "Time A")
        visitante_nome = visitante_info.get("nome", "Time B")
        mandante_abrev = mandante_info.get("abreviacao", "???")
        visitante_abrev = visitante_info.get("abreviacao", "???")
        
        # Calcular forças simples baseadas nos atletas
        gols_m = sum(1 for a in atletas if a.get("clube_id") == mandante_id
                     and a.get("posicao_id") == 5 and a.get("media_num", 0) > 5)
        gols_v = sum(1 for a in atletas if a.get("clube_id") == visitante_id
                     and a.get("posicao_id") == 5 and a.get("media_num", 0) > 5)
        
        forca_m = forcas.get(mandante_id, {}).get("forca_ataque", 50)
        forca_v = forcas.get(visitante_id, {}).get("forca_ataque", 50)
        
        # Previsão via ScorePredictor
        try:
            # Dias de descanso de cada time
            desc_m = descanso_rodada.get(mandante_id)
            desc_v = descanso_rodada.get(visitante_id)
            
            previsao = predictor.prever_confronto(
                mandante=mandante_nome,
                visitante=visitante_nome,
                mandante_id=mandante_id,
                visitante_id=visitante_id,
                forca_mandante=forca_m,
                forca_visitante=forca_v,
                rodada=rodada,
                dias_descanso_mandante=desc_m,
                dias_descanso_visitante=desc_v,
            )
            
            # Gols reais históricos (se disponíveis)
            gols_m_stats = gols_stats.get(mandante_id, {})
            gols_v_stats = gols_stats.get(visitante_id, {})
            
            jogo = {
                "mandante": mandante_nome,
                "visitante": visitante_nome,
                "mandante_abrev": mandante_abrev,
                "visitante_abrev": visitante_abrev,
                "mandante_id": mandante_id,
                "visitante_id": visitante_id,
                "placar_provavel": previsao.placar_provavel,
                "xg_mandante": round(previsao.xg_mandante, 2),
                "xg_visitante": round(previsao.xg_visitante, 2),
                "prob_vitoria_casa": round(previsao.prob_vitoria_casa, 1),
                "prob_empate": round(previsao.prob_empate, 1),
                "prob_vitoria_fora": round(previsao.prob_vitoria_fora, 1),
                "over_25": round(previsao.prob_over_2_5, 1),
                "btts": round(previsao.prob_btts, 1),
                "top_placares": previsao.top_placares[:5],
                "confianca": round(previsao.confianca, 0),
                "local": partida.get("local", ""),
                "data": partida.get("partida_data", ""),
                "dias_descanso_mandante": desc_m,
                "dias_descanso_visitante": desc_v,
                "gols_reais_mandante": gols_m_stats,
                "gols_reais_visitante": gols_v_stats,
            }
            jogos_analise.append(jogo)
        except Exception:
            continue
    
    if not jogos_analise:
        return {}
    
    # Montar conteúdo markdown
    date_str = datetime.now().strftime("%Y-%m-%d")
    title = f"Análise Rodada {rodada} - Brasileirão 2026: Previsões e Confrontos"
    slug = f"analise-rodada-{rodada}-brasileirao-2026"
    
    # Encontrar o jogo destaque (maior confiança)
    destaque = max(jogos_analise, key=lambda j: j["confianca"])
    
    excerpt = (
        f"Análise completa dos {len(jogos_analise)} jogos da rodada {rodada} "
        f"do Brasileirão 2026. Destaque: {destaque['mandante']} x "
        f"{destaque['visitante']} ({destaque['placar_provavel']})."
    )
    
    # Gerar markdown
    md_lines = []
    md_lines.append(f"## Rodada {rodada} — Visão Geral\n")
    md_lines.append(
        f"O ScoutDados analisou os **{len(jogos_analise)} confrontos** da rodada {rodada} "
        f"usando nosso modelo **Poisson + Dixon-Coles V4** com correção de baixas pontuações, "
        f"decaimento temporal e ajuste de descanso. Confira as previsões:\n"
    )
    
    # Tabela resumo
    md_lines.append("| Jogo | Placar | 1 | X | 2 | Over 2.5 | BTTS |")
    md_lines.append("|------|--------|---|---|---|----------|------|")
    for j in jogos_analise:
        md_lines.append(
            f"| {j['mandante_abrev']} x {j['visitante_abrev']} "
            f"| **{j['placar_provavel']}** "
            f"| {j['prob_vitoria_casa']}% "
            f"| {j['prob_empate']}% "
            f"| {j['prob_vitoria_fora']}% "
            f"| {j['over_25']}% "
            f"| {j['btts']}% |"
        )
    md_lines.append("")
    
    # Análise detalhada de cada jogo
    md_lines.append("---\n")
    md_lines.append("## Análise Jogo a Jogo\n")
    
    for j in jogos_analise:
        md_lines.append(f"### {j['mandante']} x {j['visitante']}\n")
        if j.get("local"):
            md_lines.append(f"📍 {j['local']}\n")
        
        md_lines.append(f"**Placar provável:** {j['placar_provavel']}\n")
        md_lines.append(f"- xG {j['mandante_abrev']}: **{j['xg_mandante']}** | xG {j['visitante_abrev']}: **{j['xg_visitante']}**")
        md_lines.append(f"- Vitória {j['mandante_abrev']}: {j['prob_vitoria_casa']}% | Empate: {j['prob_empate']}% | Vitória {j['visitante_abrev']}: {j['prob_vitoria_fora']}%")
        md_lines.append(f"- Over 2.5: {j['over_25']}% | Ambos marcam: {j['btts']}%")
        md_lines.append(f"- Confiança do modelo: {j['confianca']}%\n")
        
        # Dias de descanso
        desc_m = j.get("dias_descanso_mandante")
        desc_v = j.get("dias_descanso_visitante")
        if desc_m is not None or desc_v is not None:
            descanso_parts = []
            if desc_m is not None:
                emoji_m = "🟢" if desc_m >= 7 else ("🟡" if desc_m >= 4 else "🔴")
                descanso_parts.append(f"{emoji_m} {j['mandante_abrev']}: {desc_m}d")
            if desc_v is not None:
                emoji_v = "🟢" if desc_v >= 7 else ("🟡" if desc_v >= 4 else "🔴")
                descanso_parts.append(f"{emoji_v} {j['visitante_abrev']}: {desc_v}d")
            md_lines.append(f"- **Descanso:** {' | '.join(descanso_parts)}\n")
        
        # Gols reais históricos
        gols_m = j.get("gols_reais_mandante", {})
        gols_v = j.get("gols_reais_visitante", {})
        if gols_m.get("jogos", 0) > 0 or gols_v.get("jogos", 0) > 0:
            md_lines.append("**Dados reais no campeonato:**\n")
            if gols_m.get("jogos", 0) > 0:
                media_m = gols_m.get('media_pro', 0) or (gols_m.get('gols_pro', 0) / gols_m['jogos'] if gols_m['jogos'] > 0 else 0)
                md_lines.append(
                    f"- {j['mandante_abrev']}: {gols_m.get('gols_pro', 0)} gols em "
                    f"{gols_m['jogos']} jogos (média {media_m:.1f})"
                )
            if gols_v.get("jogos", 0) > 0:
                media_v = gols_v.get('media_pro', 0) or (gols_v.get('gols_pro', 0) / gols_v['jogos'] if gols_v['jogos'] > 0 else 0)
                md_lines.append(
                    f"- {j['visitante_abrev']}: {gols_v.get('gols_pro', 0)} gols em "
                    f"{gols_v['jogos']} jogos (média {media_v:.1f})"
                )
            md_lines.append("")
        
        # ── Stats avançadas do API-Football (se disponíveis) ──
        if enricher and enriched_data:
            try:
                from src.analysis.fixture_collector import CARTOLA_TO_APIFOOTBALL
                af_m = CARTOLA_TO_APIFOOTBALL.get(j.get("mandante_id", 0))
                af_v = CARTOLA_TO_APIFOOTBALL.get(j.get("visitante_id", 0))
                
                # Forma e desempenho dos times (BSA 2024)
                ts_m = enriched_data.get("team_stats", {}).get(af_m) if af_m else None
                ts_v = enriched_data.get("team_stats", {}).get(af_v) if af_v else None
                
                if ts_m or ts_v:
                    liga_ref = ts_m.get("league", ts_v.get("league", "Série A")) if ts_m else ts_v.get("league", "Série A")
                    md_lines.append(f"**Retrospecto ({liga_ref} 2024):**\n")
                    if ts_m:
                        forma_m = (ts_m.get("forma") or "")[-5:]
                        fe = "".join("🟢" if c == "W" else ("🟡" if c == "D" else "🔴") for c in forma_m)
                        md_lines.append(
                            f"- {j['mandante_abrev']}: {fe} | "
                            f"{ts_m['vitorias']['total']}V {ts_m['empates']['total']}E {ts_m['derrotas']['total']}D | "
                            f"Gols: {ts_m['gols_pro']['media']}/jogo | "
                            f"CS: {ts_m['clean_sheets']['total']}"
                        )
                    if ts_v:
                        forma_v = (ts_v.get("forma") or "")[-5:]
                        fe = "".join("🟢" if c == "W" else ("🟡" if c == "D" else "🔴") for c in forma_v)
                        md_lines.append(
                            f"- {j['visitante_abrev']}: {fe} | "
                            f"{ts_v['vitorias']['total']}V {ts_v['empates']['total']}E {ts_v['derrotas']['total']}D | "
                            f"Gols: {ts_v['gols_pro']['media']}/jogo | "
                            f"CS: {ts_v['clean_sheets']['total']}"
                        )
                    md_lines.append("")
                
                # H2H (confrontos diretos)
                if af_m and af_v:
                    pair = f"{min(af_m, af_v)}-{max(af_m, af_v)}"
                    h2h = enriched_data.get("h2h", {}).get(pair)
                    if h2h and h2h.get("total", 0) > 0:
                        stats = h2h["stats"]
                        # Determinar quem é team1/team2 no H2H
                        if h2h.get("team1_id") == af_m:
                            w1, w2 = stats["team1_wins"], stats["team2_wins"]
                        else:
                            w1, w2 = stats["team2_wins"], stats["team1_wins"]
                        
                        md_lines.append(
                            f"**Histórico de confrontos ({h2h['total']} jogos, todas as competições):** "
                            f"{j['mandante_abrev']} {w1}V | {stats['draws']}E | "
                            f"{j['visitante_abrev']} {w2}V\n"
                        )
                        # Últimos 3 jogos
                        for jogo_h2h in h2h.get("ultimos_5", [])[:3]:
                            gm = jogo_h2h.get("gols_mandante")
                            gv = jogo_h2h.get("gols_visitante")
                            if gm is not None and gv is not None:
                                md_lines.append(
                                    f"- {jogo_h2h['data']}: {jogo_h2h['mandante']} "
                                    f"{gm}x{gv} {jogo_h2h['visitante']} ({jogo_h2h['liga']})"
                                )
                        md_lines.append("")
            except Exception:
                pass  # Graceful fallback

        # ── Insights factuais (100% dados reais, sem IA) ──
        if insights_gen:
            try:
                from src.analysis.fixture_collector import CARTOLA_TO_APIFOOTBALL
                af_m = CARTOLA_TO_APIFOOTBALL.get(j.get("mandante_id", 0))
                af_v = CARTOLA_TO_APIFOOTBALL.get(j.get("visitante_id", 0))

                # Team stats do enriquecimento
                ts_m = enriched_data.get("team_stats", {}).get(af_m) if af_m and enriched_data else None
                ts_v = enriched_data.get("team_stats", {}).get(af_v) if af_v and enriched_data else None

                # H2H do enriquecimento
                h2h_data = None
                if af_m and af_v and enriched_data:
                    pair = f"{min(af_m, af_v)}-{max(af_m, af_v)}"
                    h2h_data = enriched_data.get("h2h", {}).get(pair)

                # Artilheiros do football-data.org
                art_m = None
                art_v = None
                # Buscar IDs do football-data para este jogo
                fdo_m_id = 0
                fdo_v_id = 0
                for fm in fdo_matches:
                    fm_m_tla = fm.get("mandante_sigla", "")
                    fm_v_tla = fm.get("visitante_sigla", "")
                    if (fm_m_tla == j["mandante_abrev"] and
                            fm_v_tla == j["visitante_abrev"]):
                        fdo_m_id = fm.get("mandante_id", 0)
                        fdo_v_id = fm.get("visitante_id", 0)
                        break
                for a in fdo_artilheiros:
                    tid = a.get("time_id", 0)
                    if fdo_m_id and tid == fdo_m_id and not art_m:
                        art_m = a
                    if fdo_v_id and tid == fdo_v_id and not art_v:
                        art_v = a

                # Posição na tabela (football-data.org 2025/26 = ATUAL)
                pos_m = None
                pos_v = None
                for t in fdo_classificacao:
                    tid = t.get("time_id", 0)
                    if fdo_m_id and tid == fdo_m_id:
                        pos_m = t
                    if fdo_v_id and tid == fdo_v_id:
                        pos_v = t

                insights = insights_gen.gerar_insights_jogo(
                    mandante=j["mandante"],
                    visitante=j["visitante"],
                    mandante_abrev=j["mandante_abrev"],
                    visitante_abrev=j["visitante_abrev"],
                    team_stats_m=ts_m,
                    team_stats_v=ts_v,
                    h2h=h2h_data,
                    posicao_m=pos_m,
                    posicao_v=pos_v,
                    artilheiro_m=art_m,
                    artilheiro_v=art_v,
                    descanso_m=j.get("dias_descanso_mandante"),
                    descanso_v=j.get("dias_descanso_visitante"),
                    rodada=rodada,
                    mandante_api_id=af_m,
                    visitante_api_id=af_v,
                )

                if insights:
                    md_lines.append(insights_gen.formatar_secao_insights(insights))
            except Exception:
                pass

        # Top placares
        if j["top_placares"]:
            md_lines.append("**Top placares mais prováveis:**\n")
            for placar, prob in j["top_placares"]:
                md_lines.append(f"- {placar} ({prob}%)")
            md_lines.append("")
    
    # Classificação ATUAL (football-data.org 2025/26) — prioridade
    # Fallback: API-Football 2024
    standings_atual = fdo_classificacao if fdo_classificacao else None
    standings_ref = enriched_data.get("standings") if enriched_data else None

    if standings_atual:
        md_lines.append("---\n")
        md_lines.append("## Classificação — Brasileirão 2026\n")
        md_lines.append("| Pos | Time | P | J | V | E | D | GP | GC | SG |")
        md_lines.append("|-----|------|---|---|---|---|---|----|----|-----|")
        for t in standings_atual[:10]:
            md_lines.append(
                f"| {t['posicao']} | {t['time']} | **{t['pontos']}** "
                f"| {t['jogos']} | {t['vitorias']} | {t['empates']} "
                f"| {t['derrotas']} | {t['gols_pro']} | {t['gols_contra']} "
                f"| {t['saldo']} |"
            )
        md_lines.append("")
    elif standings_ref:
        md_lines.append("---\n")
        md_lines.append("## Classificação — Série A 2024 (Referência)\n")
        md_lines.append("| Pos | Time | P | J | V | E | D | GP | GC | SG |")
        md_lines.append("|-----|------|---|---|---|---|---|----|----|-----|")
        for t in standings_ref[:10]:
            md_lines.append(
                f"| {t['posicao']} | {t['time']} | **{t['pontos']}** "
                f"| {t['jogos']} | {t['vitorias']} | {t['empates']} "
                f"| {t['derrotas']} | {t['gols_pro']} | {t['gols_contra']} "
                f"| {t['saldo']} |"
            )
        md_lines.append("")

    # Artilheiros do campeonato (football-data.org — exclusivo, API-Football não tem)
    if fdo_artilheiros:
        md_lines.append("## Artilheiros — Brasileirão 2026\n")
        md_lines.append("| # | Jogador | Time | Gols | Assists | Jogos |")
        md_lines.append("|---|---------|------|------|---------|-------|")
        for i, a in enumerate(fdo_artilheiros[:10], 1):
            md_lines.append(
                f"| {i} | {a['jogador']} | {a['time']} | **{a['gols']}** "
                f"| {a.get('assists', 0)} | {a.get('jogos', 0)} |"
            )
        md_lines.append("")
    
    # Dicas Cartola
    md_lines.append("---\n")
    md_lines.append("## Dicas para o Cartola FC\n")
    
    # Jogos com mais gols esperados (bom para atacantes)
    mais_gols = sorted(jogos_analise, key=lambda j: j["xg_mandante"] + j["xg_visitante"], reverse=True)[:3]
    md_lines.append("### Jogos com mais gols esperados (bom para atacantes/meiocampistas)\n")
    for j in mais_gols:
        total_xg = j["xg_mandante"] + j["xg_visitante"]
        md_lines.append(f"- **{j['mandante_abrev']} x {j['visitante_abrev']}** — {total_xg:.2f} xG total")
    md_lines.append("")
    
    # Jogos para goleiros/defensores (menos gols)
    menos_gols = sorted(jogos_analise, key=lambda j: j["xg_mandante"] + j["xg_visitante"])[:3]
    md_lines.append("### Jogos para goleiros/zagueiros (menos gols esperados)\n")
    for j in menos_gols:
        total_xg = j["xg_mandante"] + j["xg_visitante"]
        md_lines.append(f"- **{j['mandante_abrev']} x {j['visitante_abrev']}** — {total_xg:.2f} xG total")
    md_lines.append("")
    
    # Seção de calibração do modelo (transparência)
    if calibracao and calibracao.get("jogos", 0) > 0:
        md_lines.append("---\n")
        md_lines.append("## Calibração do Modelo\n")
        md_lines.append(
            f"Nosso modelo V4 foi avaliado em **{calibracao['jogos']}** jogos reais "
            f"do campeonato atual:\n"
        )
        md_lines.append(f"- **Log-Loss:** {calibracao['log_loss']:.4f} ({calibracao['nota']})")
        if calibracao.get("brier_score"):
            md_lines.append(f"- **Brier Score:** {calibracao['brier_score']:.4f}")
        if calibracao.get("acertos_exatos") is not None:
            md_lines.append(
                f"- **Acertos exatos:** {calibracao['acertos_exatos']}/{calibracao['jogos']}"
            )
        if calibracao.get("acertos_ved") is not None:
            md_lines.append(
                f"- **Acertos V/E/D:** {calibracao['acertos_ved']}/{calibracao['jogos']} "
                f"({100*calibracao['acertos_ved']/calibracao['jogos']:.0f}%)"
            )
        md_lines.append("")
    
    md_lines.append(
        "*As projeções são resultado de modelos estatísticos (Poisson + Dixon-Coles V4, Monte Carlo) "
        "com fins informativos e educacionais. Não representam garantia de resultado.*"
    )
    
    content = "\n".join(md_lines)
    
    # ── Validação pré-publicação ──
    warnings = []
    
    # 1. Checar médias 0.0 quando há gols > 0
    for j in jogos_analise:
        for side, key_gols in [("mandante", "gols_reais_mandante"), ("visitante", "gols_reais_visitante")]:
            gols_data = j.get(key_gols, {})
            if gols_data.get("jogos", 0) > 0 and gols_data.get("gols_pro", 0) > 0:
                media = gols_data.get("media_pro", 0)
                if media == 0:
                    # Corrigir inline
                    gols_data["media_pro"] = round(gols_data["gols_pro"] / gols_data["jogos"], 2)
                    warnings.append(f"Média corrigida para {j[f'{side}_abrev']}")
    
    # 2. Checar diversidade de placares previstos
    placares = [j["placar_provavel"] for j in jogos_analise]
    placares_unicos = set(placares)
    if len(jogos_analise) >= 5 and len(placares_unicos) == 1:
        warnings.append(f"Baixa diversidade: todos os {len(jogos_analise)} placares são {placares[0]}")
    
    if warnings:
        print(f"[BlogGenerator] ⚠️ Validação da rodada {rodada}: {'; '.join(warnings)}")
    
    post = {
        "slug": slug,
        "title": title,
        "date": date_str,
        "excerpt": excerpt,
        "content": content,
        "tags": ["Brasileirão", f"Rodada {rodada}", "Previsão", "xG", "Dixon-Coles"],
        "readTime": max(5, len(jogos_analise)),
        "rodada": rodada,
        "jogos": jogos_analise,
        "calibracao": calibracao,
        "modelo": "V4_Dixon-Coles",
        "geradoEm": datetime.now().isoformat(),
        "tipo": "analise_rodada",
    }
    
    # Salvar em disco
    post_file = POSTS_DIR / f"{slug}.json"
    with open(post_file, "w", encoding="utf-8") as f:
        json.dump(post, f, ensure_ascii=False, indent=2)
    
    return post


def listar_posts_gerados() -> List[Dict[str, Any]]:
    """Lista todos os posts gerados automaticamente, mais recentes primeiro (por data)."""
    posts = []
    seen_slugs = set()
    for f in POSTS_DIR.glob("*.json"):
        try:
            with open(f, "r", encoding="utf-8") as fp:
                post = json.load(fp)
                slug = post["slug"]
                # Deduplicar por slug
                if slug in seen_slugs:
                    continue
                seen_slugs.add(slug)
                # Retornar sem o conteúdo completo (listing)
                posts.append({
                    "slug": slug,
                    "title": post["title"],
                    "date": post["date"],
                    "excerpt": post["excerpt"],
                    "tags": post["tags"],
                    "readTime": post["readTime"],
                    "tipo": post.get("tipo", "analise_rodada"),
                })
        except Exception:
            continue
    # Ordenar por data (campo JSON), mais recente primeiro
    posts.sort(key=lambda p: p.get("date", ""), reverse=True)
    return posts


def get_post_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    """Busca um post gerado pelo slug."""
    post_file = POSTS_DIR / f"{slug}.json"
    if post_file.exists():
        with open(post_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


# ========== POSTS POR TIME ==========

# Mapa de slugs para nomes dos 20 times do Brasileirão 2026
TIMES_MAP = {
    "atletico-mg": {"nome": "Atlético-MG", "abrev": "CAM"},
    "athletico-pr": {"nome": "Athletico-PR", "abrev": "CAP"},
    "bahia": {"nome": "Bahia", "abrev": "BAH"},
    "botafogo": {"nome": "Botafogo", "abrev": "BOT"},
    "corinthians": {"nome": "Corinthians", "abrev": "COR"},
    "cruzeiro": {"nome": "Cruzeiro", "abrev": "CRU"},
    "cuiaba": {"nome": "Cuiabá", "abrev": "CUI"},
    "flamengo": {"nome": "Flamengo", "abrev": "FLA"},
    "fluminense": {"nome": "Fluminense", "abrev": "FLU"},
    "fortaleza": {"nome": "Fortaleza", "abrev": "FOR"},
    "gremio": {"nome": "Grêmio", "abrev": "GRE"},
    "internacional": {"nome": "Internacional", "abrev": "INT"},
    "juventude": {"nome": "Juventude", "abrev": "JUV"},
    "mirassol": {"nome": "Mirassol", "abrev": "MIR"},
    "palmeiras": {"nome": "Palmeiras", "abrev": "PAL"},
    "santos": {"nome": "Santos", "abrev": "SAN"},
    "sao-paulo": {"nome": "São Paulo", "abrev": "SAO"},
    "sport": {"nome": "Sport", "abrev": "SPO"},
    "vasco": {"nome": "Vasco", "abrev": "VAS"},
    "vitoria": {"nome": "Vitória", "abrev": "VIT"},
    # Times adicionais da classificação atual
    "red-bull-bragantino": {"nome": "Red Bull Bragantino", "abrev": "RBB"},
    "chapecoense": {"nome": "Chapecoense", "abrev": "CHA"},
    "coritiba": {"nome": "Coritiba", "abrev": "CFC"},
    "remo": {"nome": "Remo", "abrev": "REM"},
}


def _find_team_id(clubes: Dict, abrev: str) -> Optional[int]:
    """Encontra o ID do time pela abreviação."""
    for cid, c in clubes.items():
        if c.get("abreviacao", "").upper() == abrev.upper():
            return int(cid)
    return None


def gerar_post_time(time_slug: str, api: Optional[CartolaAPI] = None) -> Dict[str, Any]:
    """
    Gera um post automático de análise para um time específico.
    Inclui: posição, probabilidades Monte Carlo, forma, próximos jogos.
    
    Args:
        time_slug: slug do time (ex: "flamengo")
        api: instância da API (criada se None)
    
    Returns:
        Dict com o post gerado, ou {} se falhou.
    """
    if time_slug not in TIMES_MAP:
        return {}
    
    info = TIMES_MAP[time_slug]
    nome = info["nome"]
    abrev = info["abrev"]
    
    if api is None:
        api = CartolaAPI()
    
    try:
        mercado = api.get_mercado()
        status = api.get_status_mercado()
        
        if not mercado or not status:
            return {}
        
        clubes = mercado.get("clubes", {})
        rodada_atual = status.get("rodada_atual", 1)
        
        # Encontrar o time nos clubes
        time_id = _find_team_id(clubes, abrev)
        if not time_id:
            return {}
        
        # Buscar partidas para tabela
        partidas_data = api.get_partidas(rodada_atual)
        partidas = partidas_data.get("partidas", []) if partidas_data else []
        
        # Buscar classificação (usa o endpoint já existente internamente)
        from src.analysis.match_analyzer import MatchAnalyzer
        from src.analysis.monte_carlo import MonteCarloSimulator
        
        ma = MatchAnalyzer()
        ma.carregar_estatisticas_times(clubes, partidas)
        
        # Dados do time
        stats = ma.estatisticas_times.get(time_id)
        if not stats:
            return {}
        
        pontos = stats.vitorias * 3 + stats.empates
        jogos = stats.jogos
        
        # Classificação completa para posição
        classificacao = []
        forca_times = {}
        for cid, s in ma.estatisticas_times.items():
            classificacao.append({
                "id": cid,
                "nome": s.nome,
                "abrev": s.abreviacao,
                "pontos": s.vitorias * 3 + s.empates,
                "jogos": s.jogos,
                "vitorias": s.vitorias,
                "empates": s.empates,
                "derrotas": s.derrotas,
                "gols_pro": s.gols_pro,
                "gols_contra": s.gols_contra,
            })
            forca_times[cid] = s.forca_geral
        
        classificacao.sort(
            key=lambda x: (x["pontos"], x["vitorias"],
                           x["gols_pro"] - x["gols_contra"], x["gols_pro"]),
            reverse=True,
        )
        posicao = next((i + 1 for i, t in enumerate(classificacao) if t["id"] == time_id), 0)
        
        # Monte Carlo para probabilidades
        prob_titulo = 0.0
        prob_g4 = 0.0
        prob_sula = 0.0
        prob_z4 = 0.0
        try:
            mc = MonteCarloSimulator(score_predictor=None, n_simulacoes=1000)
            time_ids = [t["id"] for t in classificacao]
            n = len(time_ids)
            jogos_restantes = []
            for r in range(rodada_atual + 1, 39):
                offset = (r - 1) % max(n - 1, 1)
                rotated = [time_ids[0]] + time_ids[1:]
                for _ in range(offset):
                    rotated = [rotated[0]] + [rotated[-1]] + rotated[1:-1]
                for j in range(n // 2):
                    m, v = rotated[j], rotated[n - 1 - j]
                    if r % 2 == 0:
                        m, v = v, m
                    jogos_restantes.append({"mandante_id": m, "visitante_id": v, "rodada": r})
            
            if jogos_restantes:
                resultados, _ = mc.simular_campeonato(classificacao, jogos_restantes, forca_times)
                for res in resultados:
                    if res.time_id == time_id:
                        prob_titulo = res.prob_titulo
                        prob_g4 = res.prob_libertadores
                        prob_sula = res.prob_sulamericana
                        prob_z4 = res.prob_rebaixamento
                        break
        except Exception:
            pass
        
        # Próximos jogos do time
        predictor = ScorePredictor()
        proximos = []
        for r in range(rodada_atual, min(rodada_atual + 5, 39)):
            try:
                pd = api.get_partidas(r)
                ps = pd.get("partidas", []) if pd else []
                for p in ps:
                    casa = p.get("clube_casa_id", 0)
                    fora = p.get("clube_visitante_id", 0)
                    if time_id in (casa, fora):
                        c_info = clubes.get(str(casa), {})
                        f_info = clubes.get(str(fora), {})
                        mand = c_info.get("nome", "?")
                        visit = f_info.get("nome", "?")
                        prev = predictor.prever_confronto(
                            mandante=mand, visitante=visit,
                            mandante_id=casa, visitante_id=fora,
                            forca_mandante=forca_times.get(casa, 50),
                            forca_visitante=forca_times.get(fora, 50),
                            rodada=r,
                        )
                        eh_casa = casa == time_id
                        proximos.append({
                            "rodada": r,
                            "adversario": visit if eh_casa else mand,
                            "local": "Casa" if eh_casa else "Fora",
                            "placar": prev.placar_provavel,
                            "prob_vitoria": round(
                                prev.prob_vitoria_casa if eh_casa else prev.prob_vitoria_fora, 1
                            ),
                            "xg_time": round(
                                prev.xg_mandante if eh_casa else prev.xg_visitante, 2
                            ),
                        })
                        break
            except Exception:
                continue
        
        # Montar markdown
        date_str = datetime.now().strftime("%Y-%m-%d")
        title = f"{nome} no Brasileirão: Probabilidades e Análise"
        slug = f"{time_slug}-brasileirao"
        
        # Faixa do time
        if posicao <= 4:
            faixa = "zona de classificação para a Libertadores (G4)"
        elif posicao <= 6:
            faixa = "pré-Libertadores"
        elif posicao <= 12:
            faixa = "briga por Sul-Americana"
        elif posicao <= 16:
            faixa = "meio de tabela"
        else:
            faixa = "zona de rebaixamento (Z4)"
        
        excerpt = (
            f"Análise completa do {nome} na rodada {rodada_atual} do Brasileirão 2026. "
            f"Atualmente em {posicao}º lugar com {pontos} pontos. "
            f"Probabilidade de título: {prob_titulo:.1f}%."
        )
        
        md = []
        md.append(f"## {nome} — Situação Atual\n")
        md.append(
            f"Na **rodada {rodada_atual}**, o {nome} ocupa a **{posicao}ª posição** com "
            f"**{pontos} pontos** em {jogos} jogos ({stats.vitorias}V {stats.empates}E {stats.derrotas}D), "
            f"na {faixa}.\n"
        )
        md.append(f"- Gols pró: **{stats.gols_pro}** | Gols contra: **{stats.gols_contra}** | "
                   f"Saldo: **{stats.gols_pro - stats.gols_contra:+d}**")
        if hasattr(stats, "forma_sequencia") and stats.forma_sequencia:
            md.append(f"- Forma recente: **{stats.forma_sequencia}**\n")
        else:
            md.append("")
        
        md.append("## Probabilidades (Monte Carlo)\n")
        md.append("| Objetivo | Probabilidade |")
        md.append("|----------|--------------|")
        md.append(f"| 🏆 Título | **{prob_titulo:.1f}%** |")
        md.append(f"| 🌎 Libertadores (G4) | **{prob_g4:.1f}%** |")
        md.append(f"| 🏅 Sul-Americana | **{prob_sula:.1f}%** |")
        md.append(f"| ⚠️ Rebaixamento | **{prob_z4:.1f}%** |")
        md.append("")
        
        if proximos:
            md.append("## Próximos Jogos\n")
            md.append("| Rod. | Adversário | Local | Placar | P(V) | xG |")
            md.append("|------|-----------|-------|--------|------|-----|")
            for pj in proximos:
                md.append(
                    f"| {pj['rodada']} | {pj['adversario']} | {pj['local']} | "
                    f"**{pj['placar']}** | {pj['prob_vitoria']}% | {pj['xg_time']} |"
                )
            md.append("")
        
        md.append("---\n")
        md.append(
            f"*Análise gerada pelo modelo estatístico Poisson V3 + Monte Carlo (1.000 simulações) "
            f"do ScoutDados. As probabilidades são estimativas com fins informativos.*"
        )
        
        content = "\n".join(md)
        
        post = {
            "slug": slug,
            "title": title,
            "date": date_str,
            "excerpt": excerpt,
            "content": content,
            "tags": [nome, "Brasileirão 2026", "Probabilidades"],
            "readTime": 4,
            "rodada": rodada_atual,
            "tipo": "analise_time",
            "time": time_slug,
            "geradoEm": datetime.now().isoformat(),
        }
        
        post_file = POSTS_DIR / f"{slug}.json"
        with open(post_file, "w", encoding="utf-8") as f:
            json.dump(post, f, ensure_ascii=False, indent=2)
        
        return post
    
    except Exception as e:
        print(f"[BlogGenerator] Erro ao gerar post do {nome}: {e}")
        return {}


def gerar_todos_posts_times(api: Optional[CartolaAPI] = None) -> int:
    """Gera posts para todos os 20 times. Retorna quantos foram gerados.
    Filtra aliases (mesma abrev) para evitar duplicatas."""
    if api is None:
        api = CartolaAPI()
    count = 0
    seen_abrevs = set()
    for slug, info in TIMES_MAP.items():
        abrev = info["abrev"]
        if abrev in seen_abrevs:
            continue
        seen_abrevs.add(abrev)
        result = gerar_post_time(slug, api)
        if result:
            count += 1
    return count


if __name__ == "__main__":
    # Teste manual
    post = gerar_post_rodada(3)
    if post:
        print(f"✅ Post gerado: {post['title']}")
        print(f"   Slug: {post['slug']}")
        print(f"   Jogos: {len(post.get('jogos', []))}")
        print(f"   Arquivo: data/blog_posts/{post['slug']}.json")
    else:
        print("❌ Não foi possível gerar o post")
