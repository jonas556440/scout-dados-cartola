"""
API REST para Cartola FC 2026
Endpoints para integrar com o frontend React

Framework: FastAPI
Formato: JSON compatível com src/types/cartola.ts do frontend
"""
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response as FastAPIResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import sys
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Adicionar path do projeto
sys.path.append(str(Path(__file__).parent.parent))

from src.api.cartola_api import CartolaAPI
from src.analysis.mpv_calculator import MPVCalculator
from src.analysis.team_selector import TeamSelector, TimeEscalado
from src.analysis.match_analyzer import MatchAnalyzer
from src.analysis.confrontos_analyzer import ConfrontosAnalyzer
from src.analysis.score_predictor import ScorePredictor
from src.scrapers.web_scraper import WebScraper
from src.database.db_manager import DatabaseManager
from src.database.history_manager import HistoryManager
from config.settings import settings

# Segurança e Observabilidade
from src.utils.rate_limiter import limiter, setup_rate_limiting, RATE_LIMITS
from src.utils.security_headers import SecurityHeadersMiddleware
from src.utils.metrics import MetricsMiddleware, metrics
from src.utils.cache import cache, circuit_breakers
import os


# ============ Modelos Pydantic (compatíveis com frontend) ============

class PlayerResponse(BaseModel):
    """Compatível com interface Player do frontend"""
    id: int
    nome: str
    apelido: str
    posicao: str  # 'GOL' | 'ZAG' | 'LAT' | 'MEI' | 'ATA' | 'TEC'
    posicaoId: int
    clubeId: int
    clubeAbrev: str
    clubeNome: str
    clubeEscudo: Optional[str] = None
    preco: float
    media: float
    pontuacao: float = 0
    jogos: int = 0
    status: str = "provavel"  # 'provavel' | 'duvida' | 'suspenso' | 'contundido' | 'nulo'
    scouts: Optional[Dict[str, int]] = None
    tendencia: Optional[float] = None
    potencial: Optional[float] = None
    valorizacao: Optional[float] = None
    mpv_score: Optional[float] = None  # Score MPV calculado para "Top Valorizadores"
    
    # Dados de confronto (NOVO!)
    confronto: Optional[Dict[str, Any]] = None


class ClubResponse(BaseModel):
    """Compatível com interface Club do frontend"""
    id: int
    nome: str
    abrev: str
    escudo: Optional[str] = None
    posicao: Optional[int] = None
    pontos: Optional[int] = None
    jogos: Optional[int] = None
    vitorias: Optional[int] = None
    empates: Optional[int] = None
    derrotas: Optional[int] = None
    golsPro: Optional[int] = None
    golsContra: Optional[int] = None
    forcaCasa: Optional[float] = None
    forcaFora: Optional[float] = None


class MatchResponse(BaseModel):
    """Compatível com interface Match do frontend"""
    id: int
    rodada: int
    mandanteId: int
    mandante: ClubResponse
    visitanteId: int
    visitante: ClubResponse
    local: str = ""
    data: Optional[str] = None
    hora: Optional[str] = None
    aproveitamentoMandante: Optional[float] = None
    aproveitamentoVisitante: Optional[float] = None
    probabilidadeMandante: Optional[float] = None
    probabilidadeEmpate: Optional[float] = None
    probabilidadeVisitante: Optional[float] = None
    
    # Dados extras de análise
    dificuldadeMandante: Optional[Any] = None  # Pode ser string ou score numérico
    dificuldadeVisitante: Optional[Any] = None
    chanceSgMandante: Optional[float] = None
    chanceSgVisitante: Optional[float] = None
    expectativaGolsMandante: Optional[float] = None
    expectativaGolsVisitante: Optional[float] = None
    
    # Previsão de placar (Distribuição de Poisson)
    placarProvavel: Optional[str] = None
    probabilidadePlacar: Optional[float] = None
    xgMandante: Optional[float] = None
    xgVisitante: Optional[float] = None
    over25: Optional[float] = None
    btts: Optional[float] = None
    topPlacares: Optional[List[dict]] = None
    confianca: Optional[float] = None


class TeamResponse(BaseModel):
    """Compatível com interface Team do frontend"""
    id: Optional[int] = None
    nome: str
    tipo: str  # 'valorizacao' | 'pontuacao'
    esquema: str
    rodada: int
    titulares: List[PlayerResponse]
    reservas: List[PlayerResponse]
    capitao: Optional[PlayerResponse] = None
    custoTotal: float
    cartoletasRestantes: float
    pontuacaoPrevista: float
    valorizacaoEsperada: Optional[float] = None
    analiseConfrontos: Optional[Dict[str, Any]] = None

class SaveTeamRequest(BaseModel):
    """Requisição para salvar time"""
    tipo: str
    rodada: int
    titulares_ids: List[int]
    capitao_id: int
    esquema: str = "4-3-3"
    cartoletas: float
    pontuacaoEsperada: Optional[float] = None
    pontuacaoReal: Optional[float] = None
    
    # Análise de confrontos
    analiseConfrontos: Optional[Dict[int, Dict]] = None


class MercadoStatusResponse(BaseModel):
    """Status do mercado"""
    rodadaAtual: int
    status: str  # 'aberto' | 'fechado' | 'em_andamento'
    fechamento: Optional[Any] = None  # Pode ser timestamp int ou string ISO


class PatrimonyResponse(BaseModel):
    """Evolução do patrimônio"""
    rodada: int
    cartoletas: float
    valorTime: float
    pontuacaoTotal: float
    variacao: float
    data: str


class DashboardStatsResponse(BaseModel):
    """Estatísticas para o Dashboard"""
    mercado: Dict[str, Any]
    patrimonio: Optional[float] = None
    topValorizadores: List[PlayerResponse]
    topPontuadores: List[PlayerResponse]
    confrontos: List[MatchResponse]


# ============ Configuração de Segurança ============

# Origens permitidas para CORS
ALLOWED_ORIGINS = [
    "https://scoutdados.com.br",
    "https://www.scoutdados.com.br",
]

# Apenas em desenvolvimento
if os.getenv("ENV") == "development" or os.getenv("DEBUG") == "1":
    ALLOWED_ORIGINS.extend([
        "http://localhost:5176",
        "http://127.0.0.1:5176",
        "http://localhost:3000",
        "http://localhost:8000",
    ])


# ============ Inicialização ============

app = FastAPI(
    title="Cartola FC 2026 API",
    description="Backend inteligente para escalação do Cartola FC",
    version="3.0.0"
)

# CORS restrito - apenas domínios específicos
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Admin-Key", "X-Blog-Key", "Authorization"],
    max_age=3600,  # Cache preflight por 1 hora
)

# Security Headers (X-Frame-Options, X-Content-Type-Options, etc)
app.add_middleware(SecurityHeadersMiddleware)

# Rate Limiting (proteção contra DDoS/abuso)
setup_rate_limiting(app)

# Métricas de performance
app.add_middleware(MetricsMiddleware)

# Instâncias globais
api = CartolaAPI()
mpv_calc = MPVCalculator()
team_selector = TeamSelector()
match_analyzer = MatchAnalyzer()
confrontos_analyzer = ConfrontosAnalyzer()
db = DatabaseManager()
history = HistoryManager()
web_scraper = WebScraper(cache_duration_minutes=60)  # Cache de 1h para notícias


# ============ Helpers ============

def converter_atleta_para_response(
    atleta: Dict, 
    clubes: Dict,
    confronto_info: Dict = None
) -> PlayerResponse:
    """Converte atleta da API Cartola para formato do frontend"""
    clube_id = atleta.get("clube_id", 0)
    clube_info = clubes.get(str(clube_id), {})
    
    pos_id = atleta.get("posicao_id", 4)
    pos_map = {1: "GOL", 2: "LAT", 3: "ZAG", 4: "MEI", 5: "ATA", 6: "TEC"}
    posicao = pos_map.get(pos_id, "MEI")
    
    status_id = atleta.get("status_id", 7)
    status_map = {7: "provavel", 5: "duvida", 2: "suspenso", 3: "contundido"}
    status = status_map.get(status_id, "nulo")
    
    # Calcular valorização percentual
    preco_atual = atleta.get("preco_num", 0.0)
    variacao_absoluta = atleta.get("variacao_num", 0.0)  # Variação em C$
    
    # Preço anterior = preço atual - variação
    preco_anterior = preco_atual - variacao_absoluta if preco_atual > 0 else 0
    
    # Calcular percentual
    valorizacao_pct = 0.0
    if preco_anterior > 0:
        valorizacao_pct = round((variacao_absoluta / preco_anterior) * 100, 2)
    
    return PlayerResponse(
        id=atleta.get("atleta_id", 0),
        nome=atleta.get("nome", ""),
        apelido=atleta.get("apelido", ""),
        posicao=posicao,
        posicaoId=pos_id,
        clubeId=clube_id,
        clubeAbrev=clube_info.get("abreviacao", "???"),
        clubeNome=clube_info.get("nome", ""),
        clubeEscudo=clube_info.get("escudos", {}).get("60x60"),
        preco=atleta.get("preco_num", 0.0),
        media=atleta.get("media_num", 0.0),
        pontuacao=atleta.get("pontos_num", 0.0),
        jogos=atleta.get("jogos_num", 0),
        status=status,
        scouts=atleta.get("scout", {}),
        tendencia=valorizacao_pct,  # Agora é percentual, não C$
        potencial=atleta.get("preco_num", 0) * 5,  # Estimativa
        valorizacao=valorizacao_pct,  # Mesmo valor que tendencia
        confronto=confronto_info
    )


def converter_partida_para_response(
    partida: Dict, 
    clubes: Dict,
    confronto_analise: Dict = None
) -> MatchResponse:
    """Converte partida para formato do frontend"""
    mandante_id = partida.get("clube_casa_id") or partida.get("clube_mandante_id", 0)
    visitante_id = partida.get("clube_visitante_id", 0)
    
    mandante_info = clubes.get(str(mandante_id), {})
    visitante_info = clubes.get(str(visitante_id), {})
    
    mandante = ClubResponse(
        id=mandante_id,
        nome=mandante_info.get("nome", ""),
        abrev=mandante_info.get("abreviacao", "???"),
        escudo=mandante_info.get("escudos", {}).get("60x60"),
        # Adicionar posição real da API
        posicao=partida.get("clube_casa_posicao"),
    )
    
    visitante = ClubResponse(
        id=visitante_id,
        nome=visitante_info.get("nome", ""),
        abrev=visitante_info.get("abreviacao", "???"),
        escudo=visitante_info.get("escudos", {}).get("60x60"),
        # Adicionar posição real da API
        posicao=partida.get("clube_visitante_posicao"),
    )
    
    response = MatchResponse(
        id=partida.get("partida_id", 0),
        rodada=partida.get("rodada", 1),
        mandanteId=mandante_id,
        mandante=mandante,
        visitanteId=visitante_id,
        visitante=visitante,
        local=partida.get("local", ""),
        data=partida.get("partida_data"),
    )
    
    # Adicionar análise se disponível
    if confronto_analise:
        response.dificuldadeMandante = confronto_analise.get("dificuldade_mandante")
        response.dificuldadeVisitante = confronto_analise.get("dificuldade_visitante")
        response.chanceSgMandante = confronto_analise.get("chance_sg_mandante")
        response.chanceSgVisitante = confronto_analise.get("chance_sg_visitante")
        response.expectativaGolsMandante = confronto_analise.get("expectativa_gols_mandante")
        response.expectativaGolsVisitante = confronto_analise.get("expectativa_gols_visitante")
        response.probabilidadeMandante = confronto_analise.get("prob_vitoria_mandante")
        response.probabilidadeEmpate = confronto_analise.get("prob_empate")
        response.probabilidadeVisitante = confronto_analise.get("prob_vitoria_visitante")
    
    return response


# ============ Endpoints ============

@app.get("/")
def root():
    """Health check"""
    return {
        "app": "Cartola FC 2026 API",
        "version": "3.0.0",
        "status": "online",
        "features": [
            "Análise de confrontos",
            "Seleção inteligente de times",
            "Histórico de patrimônio"
        ]
    }


@app.get("/api/status", response_model=MercadoStatusResponse)
@limiter.limit(RATE_LIMITS["light"])  # 300/min - endpoint leve
def get_status(request: Request):
    """Retorna status atual do mercado"""
    try:
        status = api.get_status_mercado()
        
        if not status:
            raise HTTPException(status_code=503, detail="API Cartola indisponível no momento. Tente novamente em alguns segundos.")
        
        status_map = {1: "aberto", 2: "fechando", 4: "fechado"}
        
        # Fechamento pode ser dict com timestamp ou direto o valor
        fechamento_data = status.get("fechamento")
        if isinstance(fechamento_data, dict):
            fechamento = fechamento_data.get("timestamp")
        else:
            fechamento = fechamento_data
        
        return MercadoStatusResponse(
            rodadaAtual=status.get("rodada_atual", 1),
            status=status_map.get(status.get("status_mercado", 4), "fechado"),
            fechamento=fechamento
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro interno: {e}", exc_info=True)

        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@app.get("/api/mercado/atletas", response_model=List[PlayerResponse])
def get_atletas(
    posicao: Optional[str] = None,
    preco_max: Optional[float] = None,
    apenas_provaveis: bool = True,
    limite: int = Query(default=100, le=500)
):
    """Lista atletas do mercado com filtros"""
    try:
        mercado = api.get_mercado()
        
        if not mercado:
            raise HTTPException(status_code=503, detail="API Cartola indisponível. Tente novamente.")
        
        atletas = mercado.get("atletas", [])
        clubes = mercado.get("clubes", {})
        
        # Filtrar
        if apenas_provaveis:
            atletas = [a for a in atletas if a.get("status_id") == 7]
        
        if posicao:
            pos_map = {"GOL": 1, "LAT": 2, "ZAG": 3, "MEI": 4, "ATA": 5, "TEC": 6}
            pos_id = pos_map.get(posicao.upper())
            if pos_id:
                atletas = [a for a in atletas if a.get("posicao_id") == pos_id]
        
        if preco_max:
            atletas = [a for a in atletas if a.get("preco_num", 100) <= preco_max]
        
        # Ordenar por média
        atletas.sort(key=lambda x: x.get("media_num", 0), reverse=True)
        
        # Limitar
        atletas = atletas[:limite]
        
        return [converter_atleta_para_response(a, clubes) for a in atletas]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar atletas: {e}", exc_info=True)

        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@app.get("/api/confrontos", response_model=List[MatchResponse])
def get_confrontos(rodada: Optional[int] = None):
    """Retorna análise de confrontos da rodada com previsão de placares"""
    try:
        status = api.get_status_mercado()
        rodada_req = rodada or (status.get("rodada_atual", 1) if status else 1)
        
        cached = _cache_get("confrontos", str(rodada_req))
        if cached is not None:
            return cached
        
        mercado = api.get_mercado()
        
        if not mercado:
            raise HTTPException(status_code=503, detail="API Cartola indisponível. Aguarde.")
        
        clubes = mercado.get("clubes", {})
        rodada_atual = status.get("rodada_atual", 1) if status else 1
        rodada = rodada or rodada_atual
        
        # Buscar partidas
        partidas_response = api.get_partidas(rodada)
        
        if isinstance(partidas_response, dict):
            partidas = partidas_response.get("partidas", [])
        elif isinstance(partidas_response, list):
            partidas = partidas_response
        else:
            partidas = []
        
        if not partidas:
            return []
        
        # Analisar confrontos
        confrontos_analyzer.analisar_rodada(partidas, clubes)
        
        # Gerar previsões de placar usando Poisson + Dixon-Coles V4
        match_analyzer.carregar_estatisticas_times(clubes, partidas)
        score_predictor = ScorePredictor()
        
        # Calcular dias de descanso via DataCollector
        descanso = {}
        try:
            from src.analysis.data_collector import DataCollector
            collector = DataCollector(api)
            descanso = collector.dias_descanso_rodada(rodada)
        except Exception:
            pass
        
        previsoes = score_predictor.prever_rodada(partidas, match_analyzer.estatisticas_times, descanso)
        
        # Criar mapa de previsões por time mandante
        previsoes_map = {}
        for prev in previsoes:
            previsoes_map[prev.mandante] = prev
        
        # Converter para response
        responses = []
        for partida in partidas:
            # Buscar análise do confronto
            partida_id = partida.get("partida_id", 0)
            
            # Adicionar rodada à partida (API Cartola não retorna esse campo)
            partida["rodada"] = rodada
            
            # Encontrar confronto analisado
            confronto_analise = None
            for c in confrontos_analyzer.confrontos:
                if c.partida_id == partida_id:
                    confronto_analise = {
                        "dificuldade_mandante": c.dificuldade_mandante,
                        "dificuldade_visitante": c.dificuldade_visitante,
                        "chance_sg_mandante": c.chance_sg_mandante,
                        "chance_sg_visitante": c.chance_sg_visitante,
                        "expectativa_gols_mandante": c.expectativa_gols_mandante,
                        "expectativa_gols_visitante": c.expectativa_gols_visitante,
                        "prob_vitoria_mandante": round(c.prob_vitoria_mandante * 100, 1),
                        "prob_empate": round(c.prob_empate * 100, 1),
                        "prob_vitoria_visitante": round(c.prob_vitoria_visitante * 100, 1),
                    }
                    break
            
            # Converter partida para response
            response = converter_partida_para_response(partida, clubes, confronto_analise)
            
            # Adicionar previsão de placar
            mandante_abrev = partida.get("clube_casa_abrev") or response.mandante.abrev
            if mandante_abrev in previsoes_map:
                prev = previsoes_map[mandante_abrev]
                response.placarProvavel = prev.placar_provavel
                response.probabilidadePlacar = prev.probabilidade_placar
                response.xgMandante = prev.xg_mandante
                response.xgVisitante = prev.xg_visitante
                response.over25 = prev.prob_over_2_5
                response.btts = prev.prob_btts
                response.confianca = prev.confianca
                if prev.top_placares:
                    response.topPlacares = [
                        {"placar": p[0], "probabilidade": round(p[1], 1)}
                        for p in prev.top_placares[:4]
                    ]
            
            responses.append(response)
        
        _cache_set("confrontos", responses, str(rodada_req))
        return responses
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao analisar confrontos: {e}", exc_info=True)

        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@app.get("/api/previsoes/placares")
def get_previsoes_placares(rodada: Optional[int] = None):
    """
    Retorna previsão de placares usando Distribuição de Poisson
    
    Metodologia científica baseada em:
    - Distribuição de Poisson (padrão casas de apostas)
    - Expected Goals (xG)
    - Força relativa dos times
    - Fator casa/fora
    
    Retorna:
    - Placar mais provável
    - Top 5 placares possíveis
    - Probabilidades de vitória/empate/derrota
    - Probabilidade de mais de 2.5 gols
    - Probabilidade de ambos marcarem
    """
    try:
        mercado = api.get_mercado()
        status = api.get_status_mercado()
        
        if not mercado:
            raise HTTPException(status_code=503, detail="API Cartola indisponível")
        
        clubes = mercado.get("clubes", {})
        rodada_atual = status.get("rodada_atual", 1) if status else 1
        rodada = rodada or rodada_atual
        
        # Buscar partidas
        partidas_response = api.get_partidas(rodada)
        
        if isinstance(partidas_response, dict):
            partidas = partidas_response.get("partidas", [])
        elif isinstance(partidas_response, list):
            partidas = partidas_response
        else:
            partidas = []
        
        if not partidas:
            return {"rodada": rodada, "previsoes": [], "erro": "Sem partidas"}
        
        # Carregar estatísticas dos times
        match_analyzer.carregar_estatisticas_times(clubes, partidas)
        
        # Prever placares com Dixon-Coles V4 + descanso
        score_predictor = ScorePredictor()
        
        descanso = {}
        try:
            from src.analysis.data_collector import DataCollector
            collector = DataCollector(api)
            descanso = collector.dias_descanso_rodada(rodada)
        except Exception:
            pass
        
        previsoes = score_predictor.prever_rodada(partidas, match_analyzer.estatisticas_times, descanso)
        
        # Converter para response
        resultado = {
            "rodada": rodada,
            "metodologia": "Poisson + Dixon-Coles V4 (τ=0.12, time decay, descanso)",
            "referencia": "Dixon & Coles (1997), Frontiers in Sports, PLOS ONE (2021-2023)",
            "previsoes": [
                {
                    "mandante": p.mandante,
                    "visitante": p.visitante,
                    "placarProvavel": p.placar_provavel,
                    "probabilidadePlacar": p.probabilidade_placar,
                    "xgMandante": p.xg_mandante,
                    "xgVisitante": p.xg_visitante,
                    "probVitoriaCasa": p.prob_vitoria_casa,
                    "probEmpate": p.prob_empate,
                    "probVitoriaFora": p.prob_vitoria_fora,
                    "topPlacares": [
                        {"placar": placar, "probabilidade": prob}
                        for placar, prob in p.top_placares
                    ],
                    "over25": p.prob_over_2_5,
                    "btts": p.prob_btts,
                    "confianca": p.confianca,
                    "fatores": p.fatores
                }
                for p in previsoes
            ]
        }
        
        return resultado
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Erro na previsão: {e}", exc_info=True)

        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@app.get("/api/confrontos/analise")
def get_confrontos_analise(rodada: Optional[int] = None):
    """Retorna análise completa de confrontos (melhores/piores times)"""
    mercado = api.get_mercado()
    status = api.get_status_mercado()
    
    if not mercado:
        raise HTTPException(status_code=503, detail="Mercado indisponível")
    
    clubes = mercado.get("clubes", {})
    rodada_atual = status.get("rodada_atual", 1) if status else 1
    rodada = rodada or rodada_atual
    
    partidas_response = api.get_partidas(rodada)
    
    if isinstance(partidas_response, dict):
        partidas = partidas_response.get("partidas", [])
    elif isinstance(partidas_response, list):
        partidas = partidas_response
    else:
        partidas = []
    
    if not partidas:
        return {"erro": "Partidas não disponíveis"}
    
    # Analisar
    confrontos_analyzer.analisar_rodada(partidas, clubes)
    
    # Montar resposta
    return {
        "rodada": rodada,
        "timesParaEscalar": [
            {
                "clubeId": r.clube_id,
                "nome": r.nome,
                "abrev": r.abreviacao,
                "adversario": r.adversario,
                "local": r.local,
                "dificuldade": r.dificuldade,
                "chanceSg": r.chance_sg,
                "expectativaGols": r.expectativa_gols,
                "scoreGeral": r.score_geral
            }
            for r in confrontos_analyzer.get_times_para_escalar(10)
        ],
        "timesParaEvitar": [
            {
                "clubeId": r.clube_id,
                "nome": r.nome,
                "abrev": r.abreviacao,
                "adversario": r.adversario,
                "local": r.local,
                "dificuldade": r.dificuldade,
                "scoreGeral": r.score_geral
            }
            for r in confrontos_analyzer.get_times_para_evitar(5)
        ],
        "melhoresParaSg": [
            {
                "clubeId": r.clube_id,
                "abrev": r.abreviacao,
                "adversario": r.adversario,
                "local": r.local,
                "chanceSg": r.chance_sg
            }
            for r in confrontos_analyzer.get_melhores_para_sg(5)
        ],
        "melhoresParaGols": [
            {
                "clubeId": r.clube_id,
                "abrev": r.abreviacao,
                "adversario": r.adversario,
                "local": r.local,
                "expectativaGols": r.expectativa_gols
            }
            for r in confrontos_analyzer.get_melhores_para_gols(5)
        ]
    }


@app.get("/api/escalacao/gerar")
@limiter.limit(RATE_LIMITS["heavy"])  # 30/min - endpoint pesado
def gerar_escalacao(
    request: Request,
    esquema: str = "4-4-2",
    cartoletas: float = Query(None, description="Orçamento disponível. Se omitido, usa do histórico.")
):
    """Gera times otimizados (valorização e pontuação) e auto-salva no histórico"""
    try:
        mercado = api.get_mercado()
        status = api.get_status_mercado()
        
        if not mercado:
            raise HTTPException(status_code=503, detail="API Cartola indisponível. Aguarde e tente novamente.")
        
        # Determinar orçamento
        orcamento_uso = 100.0
        
        # Se usuário não especificou, buscar do histórico
        if cartoletas is None:
            try:
                history_manager = HistoryManager()
                # Tenta pegar o patrimônio do time de valorização (geralmente onde focamos o ganho)
                patrimonio_atual = history_manager.get_cartoletas_atuais("valorizacao")
                if patrimonio_atual and patrimonio_atual > 0:
                    orcamento_uso = patrimonio_atual
            except Exception as e:
                print(f"Erro ao ler histórico: {e}")
                orcamento_uso = 100.0
        else:
            orcamento_uso = cartoletas
            
        atletas = mercado.get("atletas", [])
        clubes = mercado.get("clubes", {})
        rodada = status.get("rodada_atual", 1) if status else 1
        
        # Buscar partidas para análise de confrontos
        partidas_response = api.get_partidas(rodada)
        if isinstance(partidas_response, dict):
            partidas = partidas_response.get("partidas", [])
        elif isinstance(partidas_response, list):
            partidas = partidas_response
        else:
            partidas = []
        
        # Configurar confrontos no seletor
        team_selector.orcamento = orcamento_uso
        team_selector.rodada_atual = rodada  # v7: propagar rodada
        if partidas:
            team_selector.configurar_confrontos(partidas, clubes)
        
        # v7: Construir mapa de mando de campo e dificuldade por clube
        mando_por_clube = {}  # clube_id -> bool (True=mandante)
        dificuldade_por_clube = {}  # clube_id -> "facil"/"medio"/"dificil"
        
        if partidas:
            for p in partidas:
                casa_id = p.get("clube_casa_id")
                visit_id = p.get("clube_visitante_id")
                if casa_id:
                    mando_por_clube[casa_id] = True
                if visit_id:
                    mando_por_clube[visit_id] = False
            
            # Calcular dificuldade usando match_analyzer
            for clube_id_key in mando_por_clube:
                resumo = team_selector.match_analyzer.get_resumo_confronto(
                    clube_id_key, team_selector.confrontos_rodada
                ) if team_selector.confrontos_rodada else None
                
                if resumo and "erro" not in resumo:
                    dif = resumo.get("dificuldade", "MÉDIO")
                    if dif == "FÁCIL":
                        dificuldade_por_clube[clube_id_key] = "facil"
                    elif dif in ["DIFÍCIL", "MUITO DIFÍCIL"]:
                        dificuldade_por_clube[clube_id_key] = "dificil"
                    else:
                        dificuldade_por_clube[clube_id_key] = "medio"
                else:
                    dificuldade_por_clube[clube_id_key] = "medio"
        
        # Filtrar prováveis
        atletas = [a for a in atletas if a.get("status_id") == 7]
        
        # Analisar cada atleta (v7: com contexto real de mando e dificuldade)
        analisados = []
        for atleta in atletas:
            clube_id = atleta.get("clube_id")
            clube_info = clubes.get(str(clube_id), {})
            clube_abrev = clube_info.get("abreviacao", "???")
            
            pos_id = atleta.get("posicao_id", 4)
            pos_map = {1: "GOL", 2: "LAT", 3: "ZAG", 4: "MEI", 5: "ATA", 6: "TEC"}
            pos_abrev = pos_map.get(pos_id, "MEI")
            
            # v7: Determinar contexto real do jogo
            is_mandante = mando_por_clube.get(clube_id, True)
            dificuldade = dificuldade_por_clube.get(clube_id, "medio")
            
            analise = mpv_calc.analisar_jogador(
                atleta,
                clube_abrev=clube_abrev,
                posicao_abrev=pos_abrev,
                mandante=is_mandante,
                dificuldade_adversario=dificuldade,
                rodada_atual=rodada
            )
            
            # Adicionar pontuação da rodada atual (se houver)
            analise.pontos_rodada = atleta.get("pontos_num", 0) or 0
            
            analisados.append(analise)
        
        # v7: Gerar times com rodada_atual
        time_valor, time_pontos = team_selector.gerar_times_rodada(analisados, esquema, rodada_atual=rodada)
        
        def time_para_response(time: TimeEscalado, tipo: str) -> dict:
            if not time:
                return None
            
            def jogador_para_response(j):
                clube_info = clubes.get(str(j.clube_id), {})
                
                # Calcular valorização percentual
                preco_atual = j.preco
                variacao_absoluta = j.variacao  # Em C$
                preco_anterior = preco_atual - variacao_absoluta if preco_atual > 0 else 0
                valorizacao_pct = 0.0
                if preco_anterior > 0:
                    valorizacao_pct = round((variacao_absoluta / preco_anterior) * 100, 2)
                
                return {
                    "id": j.atleta_id,
                    "nome": j.nome,
                    "apelido": j.apelido,
                    "posicao": j.posicao_abrev,
                    "posicaoId": {"GOL": 1, "LAT": 2, "ZAG": 3, "MEI": 4, "ATA": 5, "TEC": 6}.get(j.posicao_abrev, 4),
                    "clubeId": j.clube_id,
                    "clubeAbrev": j.clube_abrev,
                    "clubeNome": clube_info.get("nome", ""),
                    "clubeEscudo": clube_info.get("escudos", {}).get("60x60"),
                    "preco": j.preco,
                    "media": j.media,
                    "pontuacao": j.pontos_rodada if hasattr(j, 'pontos_rodada') else 0,  # Pontuação da rodada atual
                    "jogos": j.jogos_num,
                    "status": "provavel",
                    "tendencia": valorizacao_pct,  # Agora é percentual
                    "valorizacao": valorizacao_pct,  # Mesmo valor
                    "potencial": j.mpv,
                    "confronto": time.analise_confrontos.get(j.clube_id)
                }
            
            return {
                "nome": f"Time {tipo.title()}",
                "tipo": tipo,
                "esquema": time.esquema,
                "rodada": rodada,
                "titulares": [jogador_para_response(j) for j in time.titulares],
                "reservas": [jogador_para_response(j) for j in time.reservas],
                "capitao": jogador_para_response(time.capitao) if time.capitao else None,
                "custoTotal": time.custo_total,
                "cartoletas": time.cartoletas_restantes,
                "pontuacaoEsperada": time.pontuacao_prevista,
                "analiseConfrontos": time.analise_confrontos
            }
        
        return {
            "rodada": rodada,
            "esquema": esquema,
            "cartoletas": cartoletas,
            "timeValorizacao": time_para_response(time_valor, "valorizacao"),
            "timePontuacao": time_para_response(time_pontos, "pontuacao"),
            "autoSalvo": _auto_salvar_historico(time_valor, time_pontos, rodada, orcamento_uso)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao gerar escalação: {e}", exc_info=True)

        raise HTTPException(status_code=500, detail="Erro interno do servidor")


def _auto_salvar_historico(time_valor, time_pontos, rodada: int, cartoletas: float) -> bool:
    """Salva automaticamente os times gerados no histórico"""
    try:
        hm = HistoryManager()
        if time_valor:
            hm.salvar_time_escalado(time_valor, rodada, cartoletas)
        if time_pontos:
            hm.salvar_time_escalado(time_pontos, rodada, cartoletas)
        return True
    except Exception as e:
        print(f"[auto-save] Erro ao salvar histórico: {e}")
        return False


@app.get("/api/dashboard", response_model=DashboardStatsResponse)
@limiter.limit(RATE_LIMITS["default"])  # 200/min
def get_dashboard(request: Request):
    """Retorna estatísticas para o dashboard"""
    try:
        cached = _cache_get("dashboard")
        if cached is not None:
            return cached
        
        mercado = api.get_mercado()
        status = api.get_status_mercado()
        
        if not mercado:
            raise HTTPException(status_code=503, detail="API Cartola temporariamente indisponível. Aguarde alguns segundos.")
        
        atletas = mercado.get("atletas", [])
        clubes = mercado.get("clubes", {})
        rodada = status.get("rodada_atual", 1) if status else 1
        
        # Pontuações parciais JÁ VÊM NO MERCADO durante a rodada!
        # O endpoint /atletas/pontuados retorna 204 durante jogos,
        # mas /atletas/mercado já tem pontos_num atualizado em tempo real
        pontuados = {}
        # Não precisa chamar endpoint separado - já está no mercado!
        
        # Pontuações parciais já estão em atletas (campo pontos_num)
        # Durante a rodada, a API atualiza automaticamente os pontos
        # Não precisa mesclar - já vem do mercado!
        
        # Contar status
        provaveis = len([a for a in atletas if a.get("status_id") == 7])
        duvidas = len([a for a in atletas if a.get("status_id") == 5])
        
        # Buscar confrontos
        partidas_response = api.get_partidas(rodada)
        if isinstance(partidas_response, dict):
            partidas = partidas_response.get("partidas", [])
        elif isinstance(partidas_response, list):
            partidas = partidas_response
        else:
            partidas = []
        
        confrontos = [converter_partida_para_response(p, clubes) for p in partidas[:5]]
        
        # Top jogadores
        atletas_provaveis = [a for a in atletas if a.get("status_id") == 7]
        
        # Calcular MPV para TODOS os prováveis (para usar em Top Valor e Top Pontos)
        mpv_calc = MPVCalculator()
        atletas_com_mpv = []
        for atleta in atletas_provaveis:
            try:
                mpv_score = mpv_calc.calcular_mpv(atleta)
                atletas_com_mpv.append({
                    **atleta,
                    "mpv_score": mpv_score
                })
            except Exception as e:
                atletas_com_mpv.append(atleta)
        
        # Atualizar a lista base para usar os atletas com MPV score
        atletas_provaveis = atletas_com_mpv
        
        # Top valorizadores (agora usa a lista já enriquecida)
        top_valor = sorted(atletas_provaveis, key=lambda x: x.get("mpv_score", x.get("variacao_num", 0)), reverse=True)[:5]
        
        # Top pontuadores: usar pontos_num se > 0 (rodada em andamento), senão média
        # Agora eles também terão o mpv_score!
        top_pontos_rodada = sorted(atletas_provaveis, key=lambda x: x.get("pontos_num", 0), reverse=True)[:10]
        top_pontos_rodada = [a for a in top_pontos_rodada if a.get("pontos_num", 0) > 0][:5]
        
        # Se não tem ninguém pontuando (mercado fechado, rodada não iniciou), usar média
        if not top_pontos_rodada:
            top_pontos = sorted(atletas_provaveis, key=lambda x: x.get("media_num", 0), reverse=True)[:5]
        else:
            top_pontos = top_pontos_rodada
        
        status_map = {1: "aberto", 2: "fechando", 4: "fechado"}
        
        # Calcular médias de preço do mercado
        precos = [a.get("preco_num", 0) for a in atletas_provaveis if a.get("preco_num", 0) > 0]
        preco_medio = sum(precos) / len(precos) if precos else 0
        
        # Calcular valorizados vs desvalorizados
        valorizados = len([a for a in atletas_provaveis if a.get("variacao_num", 0) > 0])
        desvalorizados = len([a for a in atletas_provaveis if a.get("variacao_num", 0) < 0])
        
        # Buscar patrimônio atual do histórico
        hm = HistoryManager()
        patrimonio_atual = hm.get_cartoletas_atuais("valorizacao")
        
        result = DashboardStatsResponse(
            mercado={
                "rodadaAtual": rodada,
                "status": status_map.get(status.get("status_mercado", 4), "fechado"),
                "fechamento": status.get("fechamento", {}).get("timestamp"),
                "totalAtletas": len(atletas),
                "provaveis": provaveis,
                "duvidas": duvidas,
                "precoMedio": round(preco_medio, 2),
                "valorizados": valorizados,
                "desvalorizados": desvalorizados
            },
            patrimonio=patrimonio_atual,
            topValorizadores=[converter_atleta_para_response(a, clubes) for a in top_valor],
            topPontuadores=[converter_atleta_para_response(a, clubes) for a in top_pontos],
            confrontos=confrontos
        )
        _cache_set("dashboard", result)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no dashboard: {e}", exc_info=True)

        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@app.post("/api/cache/limpar")
def limpar_cache():
    """
    Limpa o cache e força nova consulta à API do Cartola
    Use quando precisar de dados atualizados
    """
    try:
        api.limpar_cache()
        # Limpar caches de endpoints
        for key, val in _endpoint_caches.items():
            if isinstance(val, dict) and "data" in val:
                val["data"] = None
                val["timestamp"] = 0
            elif isinstance(val, dict):
                val.clear()
        return {
            "success": True, 
            "message": "Cache limpo! Próximas requisições buscarão dados atualizados da API"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ HISTÓRICO ============

@app.get("/api/historico/rodadas")
def get_historico_rodadas():
    """
    Lista todas as rodadas salvas no histórico
    """
    session = None
    try:
        session = history.get_session()
        
        from src.database.models import TimeHistorico
        
        # Buscar rodadas únicas
        rodadas = session.query(
            TimeHistorico.rodada_id
        ).distinct().order_by(TimeHistorico.rodada_id.desc()).all()
        
        result = []
        for (rodada_id,) in rodadas:
            # Contar times dessa rodada
            times = session.query(TimeHistorico).filter_by(rodada_id=rodada_id).all()
            
            result.append({
                "rodada": rodada_id,
                "times_salvos": len(times),
                "tipos": [t.tipo for t in times],
                "data_criacao": times[0].created_at.isoformat() if times else None
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Erro ao buscar histórico: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro interno do servidor")
    finally:
        if session:
            session.close()


@app.get("/api/historico/rodada/{rodada}")
def get_historico_rodada(rodada: int):
    """
    Retorna escalações salvas de uma rodada específica
    """
    session = None
    try:
        session = history.get_session()
        
        from src.database.models import TimeHistorico
        
        times = session.query(TimeHistorico).filter_by(
            rodada_id=rodada
        ).all()
        
        if not times:
            raise HTTPException(status_code=404, detail=f"Nenhuma escalação encontrada para rodada {rodada}")
        
        result = []
        for time in times:
            result.append({
                "tipo": time.tipo,
                "esquema": time.esquema,
                "custoTotal": time.custo_total,
                "cartoletas": time.cartoletas_inicial,
                "pontuacaoEsperada": time.pontuacao_prevista,
                "pontuacaoReal": time.pontuacao_real,
                "titulares": time.titulares,
                "reservas": time.reservas,
                "capitao_id": time.capitao_id,
                "criadoEm": time.created_at.isoformat(),
                "atualizadoEm": time.updated_at.isoformat() if time.updated_at else None
            })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar rodada: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro interno do servidor")
    finally:
        if session:
            session.close()


@app.get("/api/historico/status")
def get_historico_status():
    """
    Retorna estatísticas do histórico
    """
    session = None
    try:
        session = history.get_session()
        
        from src.database.models import TimeHistorico
        from sqlalchemy import func
        
        # Total de times salvos
        total = session.query(func.count(TimeHistorico.id)).scalar()
        
        # Rodadas salvas
        rodadas = session.query(
            func.count(func.distinct(TimeHistorico.rodada_id))
        ).scalar()
        
        # Última atualização
        ultimo = session.query(TimeHistorico).order_by(
            TimeHistorico.created_at.desc()
        ).first()
        
        return {
            "total_times_salvos": total,
            "total_rodadas": rodadas,
            "ultima_atualizacao": ultimo.created_at.isoformat() if ultimo else None,
            "banco_ativo": True
        }
        
    except Exception as e:
        logger.error(f"Erro ao buscar status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro interno do servidor")
    finally:
        if session:
            session.close()


@app.post("/api/historico/salvar")
@limiter.limit(RATE_LIMITS["default"])
def salvar_time_historico(request: Request, body: SaveTeamRequest):
    """
    Salva time manualmente no histórico.
    Chamado pelo botão Salvar no frontend.
    """
    try:
        mercado = api.get_mercado()
        if not mercado:
            raise HTTPException(status_code=503, detail="API Cartola indisponível")
        
        atletas_raw = mercado.get("atletas", [])
        clubes = mercado.get("clubes", {})
        
        # Mapear atletas por ID
        mapa_atletas = {a.get("atleta_id"): a for a in atletas_raw}
        
        # Construir titulares como AnaliseJogador simples
        from src.analysis.mpv_calculator import AnaliseJogador
        
        pos_map = {1: "GOL", 2: "LAT", 3: "ZAG", 4: "MEI", 5: "ATA", 6: "TEC"}
        titulares = []
        for aid in body.titulares_ids:
            at = mapa_atletas.get(aid)
            if at:
                pos_id = at.get("posicao_id", 4)
                clube_id = at.get("clube_id", 0)
                clube_info = clubes.get(str(clube_id), {})
                titulares.append(AnaliseJogador(
                    atleta_id=aid,
                    nome=at.get("nome", ""),
                    apelido=at.get("apelido", ""),
                    clube_id=clube_id,
                    clube_abrev=clube_info.get("abreviacao", "???"),
                    posicao_abrev=pos_map.get(pos_id, "MEI"),
                    preco=at.get("preco_num", 0),
                    media=at.get("media_num", 0),
                    mpv=0,
                    tendencia_valorizar=0,
                    pontuacao_esperada=body.pontuacaoEsperada or 0,
                    risco="medio",
                    variacao=at.get("variacao_num", 0),
                    jogos_num=at.get("jogos_num", 0),
                ))
        
        if not titulares:
            raise HTTPException(status_code=400, detail="Nenhum jogador válido encontrado")
        
        # Construir TimeEscalado
        capitao = next((t for t in titulares if t.atleta_id == body.capitao_id), titulares[0])
        custo = sum(t.preco for t in titulares)
        
        time_obj = TimeEscalado(
            tipo=body.tipo,
            esquema=body.esquema,
            titulares=titulares,
            reservas=[],
            capitao=capitao,
            custo_total=custo,
            cartoletas_restantes=body.cartoletas - custo,
            pontuacao_prevista=body.pontuacaoEsperada or 0,
            valorizacao_esperada=0,
            analise_confrontos=body.analiseConfrontos or {},
        )
        
        hm = HistoryManager()
        hm.salvar_time_escalado(time_obj, body.rodada, body.cartoletas)
        
        return {
            "success": True,
            "message": f"Time {body.tipo} salvo para rodada {body.rodada}",
            "rodada": body.rodada,
            "tipo": body.tipo,
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Erro ao salvar time: {e}", exc_info=True)

        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@app.get("/api/noticias/{clube_abrev}")
def get_noticias_time(clube_abrev: str):
    """
    Busca notícias e informações sobre desfalques de um time
    
    Fontes:
    - GE.globo.com (oficial)
    - API Cartola (status de jogadores)
    """
    try:
        noticias = web_scraper.buscar_noticias_time(clube_abrev.upper())
        resumo = web_scraper.gerar_resumo_desfalques(noticias)
        
        return {
            "clube": clube_abrev.upper(),
            "total_noticias": len(noticias),
            "lesionados": resumo["lesionados"],
            "suspensos": resumo["suspensos"],
            "duvidas": resumo["duvidas"],
            "vai_poupar": resumo["vai_poupar"],
            "noticias_destaque": resumo["noticias"][:5],
            "ultima_atualizacao": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erro ao buscar notícias: {e}", exc_info=True)

        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@app.get("/api/noticias/rodada/{rodada}")
def get_noticias_rodada(rodada: int):
    """
    Busca notícias de todos os times da rodada
    Útil para identificar desfalques e times que vão poupar
    """
    try:
        # Buscar partidas da rodada
        status = api.get_status_mercado()
        rodada_atual = status.get("rodada_atual", 1) if status else 1
        rodada = rodada or rodada_atual
        
        partidas_response = api.get_partidas(rodada)
        if isinstance(partidas_response, dict):
            partidas = partidas_response.get("partidas", [])
        else:
            partidas = partidas_response
        
        # Extrair clubes únicos
        clubes = set()
        for p in partidas:
            if p.get("clube_casa_id"):
                clubes.add(p["clube_casa_id"])
            if p.get("clube_visitante_id"):
                clubes.add(p["clube_visitante_id"])
        
        # Buscar clubes info
        mercado = api.get_mercado()
        clubes_info = mercado.get("clubes", {}) if mercado else {}
        
        clubes_abrev = []
        for clube_id in clubes:
            info = clubes_info.get(str(clube_id), {})
            abrev = info.get("abreviacao")
            if abrev:
                clubes_abrev.append(abrev)
        
        # Buscar notícias (limitado a 10 times por vez para não sobrecarregar)
        noticias_rodada = web_scraper.buscar_noticias_rodada(clubes_abrev[:10])
        
        resultado = {}
        for clube, noticias in noticias_rodada.items():
            resumo = web_scraper.gerar_resumo_desfalques(noticias)
            resultado[clube] = {
                "lesionados": resumo["lesionados"],
                "suspensos": resumo["suspensos"],
                "duvidas": resumo["duvidas"],
                "vai_poupar": resumo["vai_poupar"],
                "total_desfalques": len(resumo["lesionados"]) + len(resumo["suspensos"]),
            }
        
        return {
            "rodada": rodada,
            "times_analisados": len(resultado),
            "desfalques": resultado,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro ao buscar notícias da rodada: {e}", exc_info=True)

        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@app.post("/api/previsoes/customizado")
@limiter.limit(RATE_LIMITS["heavy"])  # 30/min - endpoint pesado
def prever_jogo_customizado(
    request: Request,
    mandante: str,
    visitante: str,
    forca_mandante: float = 50.0,
    forca_visitante: float = 50.0
):
    """
    Prevê qualquer jogo customizado usando Distribuição de Poisson
    
    Ideal para:
    - Jogos fora do Cartola FC
    - Copas estaduais
    - Jogos internacionais
    - Simulações
    
    Args:
        mandante: Nome do time da casa
        visitante: Nome do time visitante
        forca_mandante: Força do mandante (0-100)
        forca_visitante: Força do visitante (0-100)
    
    Returns:
        Previsão completa com placar, xG, probabilidades
    """
    try:
        from src.analysis.advanced_predictor import prever_jogo_customizado
        
        previsao = prever_jogo_customizado(
            mandante=mandante,
            visitante=visitante,
            forca_mandante=forca_mandante,
            forca_visitante=forca_visitante
        )
        
        return {
            "mandante": previsao.mandante,
            "visitante": previsao.visitante,
            "placarProvavel": previsao.placar_provavel,
            "probabilidadePlacar": previsao.probabilidade_placar,
            "xgMandante": previsao.xg_mandante,
            "xgVisitante": previsao.xg_visitante,
            "probVitoriaCasa": previsao.prob_vitoria_casa,
            "probEmpate": previsao.prob_empate,
            "probVitoriaFora": previsao.prob_vitoria_fora,
            "topPlacares": [
                {"placar": placar, "probabilidade": prob}
                for placar, prob in previsao.top_placares
            ],
            "over25": previsao.prob_over_2_5,
            "btts": previsao.prob_btts,
            "confianca": previsao.confianca,
            "metodologia": "Distribuição de Poisson + xG com recursos avançados",
            "recursos": {
                "historico_direto": "Suportado",
                "desfalques": "Suportado",
                "machine_learning": "Em preparação"
            }
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Erro na previsão: {e}", exc_info=True)

        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@app.get("/api/times/forca")
def get_forca_times(rodada: Optional[int] = None):
    """
    Retorna força calculada de todos os times
    """
    try:
        cached = _cache_get("forca_times")
        if cached is not None:
            return cached
        
        mercado = api.get_mercado()
        status = api.get_status_mercado()
        
        if not mercado:
            raise HTTPException(status_code=503, detail="API Cartola indisponível")
        
        clubes = mercado.get("clubes", {})
        rodada_atual = status.get("rodada_atual", 1) if status else 1
        rodada = rodada or rodada_atual
        
        # Buscar partidas para extrair posições
        partidas_response = api.get_partidas(rodada)
        
        if isinstance(partidas_response, dict):
            partidas = partidas_response.get("partidas", [])
        elif isinstance(partidas_response, list):
            partidas = partidas_response
        else:
            partidas = []
        
        # Calcular força dos times usando MatchAnalyzer
        match_analyzer.carregar_estatisticas_times(clubes, partidas)
        
        # Montar resposta
        times_forca = []
        for clube_id, stats in match_analyzer.estatisticas_times.items():
            clube_info = clubes.get(str(clube_id), {})
            
            times_forca.append({
                "id": clube_id,
                "nome": stats.nome,
                "abrev": stats.abreviacao,
                "posicao": stats.posicao or 0,
                "jogos": stats.jogos,
                "vitorias": stats.vitorias,
                "empates": stats.empates,
                "derrotas": stats.derrotas,
                "golsPro": stats.gols_pro,
                "golsContra": stats.gols_contra,
                "forcaCasa": round(stats.forca_geral, 1),  # Usar força geral para casa
                "forcaFora": round(stats.forca_geral * 0.85, 1),  # Reduzir 15% para fora
                "forcaGeral": round(stats.forca_geral, 1),
                "forma": stats.forma_sequencia,
                "escudo": clube_info.get("escudos", {}).get("60x60") if isinstance(clube_info.get("escudos"), dict) else None
            })
        
        # Ordenar por força geral
        times_forca.sort(key=lambda x: x["forcaGeral"], reverse=True)
        
        # Adicionar ranking
        for i, time in enumerate(times_forca, 1):
            time["ranking"] = i
        
        result = {
            "rodada": rodada,
            "times": times_forca,
            "metodologia": "80% ranking histórico + 20% classificação atual (início campeonato)",
            "peso_historico": 0.80 if rodada <= 5 else max(0.30, 0.80 - ((rodada - 5) * 0.05))
        }
        _cache_set("forca_times", result)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Erro ao calcular força: {e}", exc_info=True)

        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@app.get("/api/times/xg")
def get_xg_por_time(rodada: Optional[int] = None):
    """
    Retorna tabela de xG (Expected Goals) por time, estilo FootyStats.
    Inclui xG geral, casa, fora, xGA (contra) e próximos jogos com xG.
    """
    try:
        mercado = api.get_mercado()
        status = api.get_status_mercado()
        
        if not mercado:
            raise HTTPException(status_code=503, detail="API Cartola indisponível")
        
        clubes = mercado.get("clubes", {})
        rodada_atual = status.get("rodada_atual", 1) if status else 1
        rodada = rodada or rodada_atual
        
        # Carregar estatísticas
        partidas_response = api.get_partidas(rodada)
        if isinstance(partidas_response, dict):
            partidas = partidas_response.get("partidas", [])
        elif isinstance(partidas_response, list):
            partidas = partidas_response
        else:
            partidas = []
        
        match_analyzer.carregar_estatisticas_times(clubes, partidas)
        score_predictor_inst = ScorePredictor()
        
        # Calcular xG para cada jogo da rodada
        previsoes = score_predictor_inst.prever_rodada(partidas, match_analyzer.estatisticas_times)
        
        # Montar tabela xG por time
        times_xg = {}
        for clube_id, stats in match_analyzer.estatisticas_times.items():
            clube_info = clubes.get(str(clube_id), {})
            escudo = None
            if isinstance(clube_info.get("escudos"), dict):
                escudo = clube_info["escudos"].get("60x60")
            
            # Calcular xG base com forças relativas
            forca_ataque = stats.forca_geral / 50 if stats.forca_geral else 1.0
            forca_defesa_norm = max(0.5, min(1.5, (100 - stats.forca_geral) / 50 + 0.5))
            
            # V4: usar MEDIA_GOLS_POR_LIGA (1.25 per team) em vez de MEDIA_GOLS_MANDANTE (removido no V4)
            media_gols_base = 1.25  # brasileirão média ~2.50 / 2 times
            xg_base = media_gols_base * forca_ataque
            xga_base = media_gols_base * forca_defesa_norm
            
            times_xg[stats.abreviacao] = {
                "id": clube_id,
                "nome": stats.nome,
                "abrev": stats.abreviacao,
                "escudo": escudo,
                "posicao": stats.posicao or 0,
                "jogos": stats.jogos,
                "golsPro": stats.gols_pro,
                "golsContra": stats.gols_contra,
                "xgGeral": round(xg_base, 2),
                "xgCasa": round(xg_base * 1.15, 2),
                "xgFora": round(xg_base * 0.85, 2),
                "xgaGeral": round(xga_base, 2),
                "xgaCasa": round(xga_base * 0.85, 2),
                "xgaFora": round(xga_base * 1.15, 2),
                "forcaGeral": round(stats.forca_geral, 1),
            }
        
        # Próximos jogos com xG
        proximos_jogos = []
        for prev in previsoes:
            proximos_jogos.append({
                "mandante": prev.mandante,
                "visitante": prev.visitante,
                "xgMandante": round(prev.xg_mandante, 2),
                "xgVisitante": round(prev.xg_visitante, 2),
                "totalXg": round(prev.xg_mandante + prev.xg_visitante, 2),
                "placarProvavel": prev.placar_provavel,
                "over25": round(prev.prob_over_2_5 * 100, 1),
                "btts": round(prev.prob_btts * 100, 1),
            })
        
        # Ordenar times por xG geral
        ranking_xg = sorted(times_xg.values(), key=lambda x: x["xgGeral"], reverse=True)
        ranking_xga = sorted(times_xg.values(), key=lambda x: x["xgaGeral"])
        
        return {
            "rodada": rodada,
            "rankingXG": ranking_xg,
            "rankingXGA": ranking_xga,
            "proximosJogos": proximos_jogos,
            "metodologia": "xG calculado via modelo Poisson com forças ofensivas/defensivas relativas",
        }
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Erro ao calcular xG: {e}", exc_info=True)

        raise HTTPException(status_code=500, detail="Erro interno do servidor")


# ============ Brasileirão ============

# Sistema de cache in-memory genérico para endpoints pesados
import time as _time
import threading

_cache_lock = threading.Lock()

_endpoint_caches = {
    "classificacao": {"data": None, "timestamp": 0, "ttl": 600},   # 10 min
    "confrontos":    {"data": None, "timestamp": 0, "ttl": 300},   # 5 min
    "previsoes":     {"data": None, "timestamp": 0, "ttl": 300},   # 5 min
    "dashboard":     {"data": None, "timestamp": 0, "ttl": 300},   # 5 min
    "forca_times":   {"data": None, "timestamp": 0, "ttl": 600},   # 10 min
    "times_xg":      {"data": None, "timestamp": 0, "ttl": 600},   # 10 min
    "acuracia":      {"data": None, "timestamp": 0, "ttl": 3600},  # 1 hora
    "time_detail":   {},  # keyed by slug, each entry is {data, timestamp, ttl}
}


def _cache_get(name: str, key: str = "") -> Any:
    """Retorna dados cacheados ou None se expirado."""
    with _cache_lock:
        if key:
            entry = _endpoint_caches.get(name, {}).get(key)
        else:
            entry = _endpoint_caches.get(name)
        if entry and entry.get("data") is not None:
            if _time.time() - entry["timestamp"] < entry["ttl"]:
                return entry["data"]
        return None


def _cache_set(name: str, data: Any, key: str = ""):
    """Salva dados no cache."""
    with _cache_lock:
        if key:
            if name not in _endpoint_caches:
                _endpoint_caches[name] = {}
            _endpoint_caches[name][key] = {
                "data": data,
                "timestamp": _time.time(),
                "ttl": 900,  # 15 min para caches keyed
            }
        else:
            cache = _endpoint_caches[name]
            cache["data"] = data
            cache["timestamp"] = _time.time()


# Cache in-memory para classificação (TTL 10 min)
_classificacao_cache = _endpoint_caches["classificacao"]
_classificacao_disk = Path(__file__).parent / "data" / "cache" / "classificacao_response.json"
_confrontos_disk = Path(__file__).parent / "data" / "cache" / "confrontos_realizados.json"


def _load_confrontos_disk() -> tuple:
    """Carrega confrontos realizados do disco. Retorna (set, last_rodada)."""
    try:
        if _confrontos_disk.exists():
            data = json.loads(_confrontos_disk.read_text(encoding="utf-8"))
            confrontos = {tuple(c) for c in data.get("confrontos", [])}
            return confrontos, data.get("last_rodada", 0)
    except Exception:
        pass
    return set(), 0


def _save_confrontos_disk(confrontos: set, rodada: int):
    """Salva confrontos realizados em disco."""
    try:
        _confrontos_disk.parent.mkdir(parents=True, exist_ok=True)
        _confrontos_disk.write_text(json.dumps({
            "confrontos": [list(c) for c in confrontos],
            "last_rodada": rodada,
        }, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


@app.get("/api/brasileirao/classificacao")
def get_classificacao():
    """
    Retorna classificação do Brasileirão + simulação Monte Carlo.
    Combina dados reais da API Cartola com simulação de probabilidades.
    Cache de 10 minutos (memória) + disk cache para sobreviver restarts.
    """
    import time as _time

    # 1. Cache em memória (rápido)
    if (
        _classificacao_cache["data"] is not None
        and _time.time() - _classificacao_cache["timestamp"] < _classificacao_cache["ttl"]
    ):
        return _classificacao_cache["data"]

    # 2. Disk cache fallback (sobrevive a restarts — stale-while-revalidate)
    disk_stale = None
    try:
        if _classificacao_disk.exists():
            raw = json.loads(_classificacao_disk.read_text(encoding="utf-8"))
            ts = raw.pop("_cache_ts", 0)
            if _time.time() - ts < 900:  # 15 min: fresco o suficiente
                _classificacao_cache["data"] = raw
                _classificacao_cache["timestamp"] = _time.time()
                return raw
            disk_stale = raw  # manter como fallback
    except Exception:
        pass

    try:
        from src.analysis.monte_carlo import MonteCarloSimulator

        mercado = api.get_mercado()
        status = api.get_status_mercado()

        if not mercado:
            if disk_stale:
                return disk_stale
            raise HTTPException(status_code=503, detail="API Cartola indisponível")

        clubes = mercado.get("clubes", {})
        rodada_atual = status.get("rodada_atual", 1) if status else 1
        
        # Buscar partidas para construir a tabela
        partidas_response = api.get_partidas(rodada_atual)
        if isinstance(partidas_response, dict):
            partidas = partidas_response.get("partidas", [])
        elif isinstance(partidas_response, list):
            partidas = partidas_response
        else:
            partidas = []
        
        # Usar MatchAnalyzer para obter estatísticas
        match_analyzer.carregar_estatisticas_times(clubes, partidas)
        
        # Montar classificação atual
        classificacao = []
        forca_times = {}
        
        for clube_id, stats in match_analyzer.estatisticas_times.items():
            clube_info = clubes.get(str(clube_id), {})
            escudo = None
            if isinstance(clube_info.get("escudos"), dict):
                escudo = clube_info["escudos"].get("60x60")
            
            classificacao.append({
                "id": clube_id,
                "nome": stats.nome,
                "abrev": stats.abreviacao,
                "escudo": escudo,
                "posicao": stats.posicao or 0,
                "pontos": stats.vitorias * 3 + stats.empates,
                "jogos": stats.jogos,
                "vitorias": stats.vitorias,
                "empates": stats.empates,
                "derrotas": stats.derrotas,
                "gols_pro": stats.gols_pro,
                "gols_contra": stats.gols_contra,
                "saldo_gols": stats.gols_pro - stats.gols_contra,
                "aproveitamento": round((stats.vitorias * 3 + stats.empates) / max(stats.jogos * 3, 1) * 100, 1),
                "forma": stats.forma_sequencia,
            })
            forca_times[clube_id] = stats.forca_geral
        
        # Ordenar por pontos > vitórias > saldo > gols
        classificacao.sort(
            key=lambda x: (x["pontos"], x["vitorias"], x["saldo_gols"], x["gols_pro"]),
            reverse=True
        )
        
        # Atualizar posição
        for i, time in enumerate(classificacao, 1):
            time["posicao"] = i
        
        # Monte Carlo (500 simulações, com ScorePredictor para qualidade)
        simulacao = None
        pontos_necessarios_mc = None
        predictor = None
        try:
            predictor = ScorePredictor()
            mc = MonteCarloSimulator(score_predictor=predictor, n_simulacoes=300)

            # Cache de xG para evitar recalcular prever_confronto em cada simulação
            xg_cache = {}

            # Gerar jogos restantes com round-robin completo
            jogos_restantes = []
            time_ids = [t["id"] for t in classificacao]
            n_times = len(time_ids)

            # Coletar confrontos já realizados — disk cache + incremental
            confrontos_realizados, last_cached_rod = _load_confrontos_disk()

            # Partidas da rodada atual (já carregadas acima)
            for p in partidas:
                m_id = p.get("clube_casa_id")
                v_id = p.get("clube_visitante_id")
                if m_id and v_id:
                    confrontos_realizados.add((m_id, v_id))

            # Buscar APENAS rodadas que ainda não temos em cache
            for rod in range(max(1, last_cached_rod + 1), rodada_atual):
                try:
                    p_resp = api.get_partidas(rod)
                    if isinstance(p_resp, dict):
                        p_list = p_resp.get("partidas", [])
                    elif isinstance(p_resp, list):
                        p_list = p_resp
                    else:
                        p_list = []
                    for p in p_list:
                        m_id = p.get("clube_casa_id")
                        v_id = p.get("clube_visitante_id")
                        if m_id and v_id:
                            confrontos_realizados.add((m_id, v_id))
                except Exception:
                    pass

            # Salvar confrontos em disco para próximas requests
            _save_confrontos_disk(confrontos_realizados, rodada_atual)

            # Gerar jogos restantes (turno e returno completos)
            rodada_futura = rodada_atual + 1
            jogos_pendentes = []
            for i_t in range(n_times):
                for j_t in range(n_times):
                    if i_t == j_t:
                        continue
                    m = time_ids[i_t]
                    v = time_ids[j_t]
                    if (m, v) not in confrontos_realizados:
                        jogos_pendentes.append({"mandante_id": m, "visitante_id": v})

            # Distribuir em rodadas
            jogos_por_rodada = max(n_times // 2, 1)
            for idx, jogo in enumerate(jogos_pendentes):
                jogo["rodada"] = rodada_futura + (idx // jogos_por_rodada)
                jogos_restantes.append(jogo)
            
            if jogos_restantes:
                resultados, pontos_necessarios_mc = mc.simular_campeonato(
                    classificacao, jogos_restantes, forca_times, xg_cache=xg_cache
                )
                simulacao = [
                    {
                        "id": r.time_id,
                        "abrev": r.abrev,
                        "pontosMedio": r.pontos_medio,
                        "pontosMin": r.pontos_min,
                        "pontosMax": r.pontos_max,
                        "probTitulo": r.prob_titulo,
                        "probLibertadores": r.prob_libertadores,
                        "probSulamericana": r.prob_sulamericana,
                        "probRebaixamento": r.prob_rebaixamento,
                        "posicaoMedia": r.posicao_media,
                    }
                    for r in resultados
                ]
        except Exception as e:
            print(f"[Monte Carlo] Simulação falhou: {e}")
            import traceback
            traceback.print_exc()
        
        # Montar resposta com dados de confrontos para o frontend
        # Buscar próximos jogos da rodada atual
        proximos_jogos = []
        ultima_rodada_jogos = []
        try:
            predictor_pj = predictor if predictor else ScorePredictor()
            
            # Próximos jogos (rodada atual) — reusar partidas já carregadas
            p_list = partidas
            
            for p in p_list:
                m_id = p.get("clube_casa_id")
                v_id = p.get("clube_visitante_id")
                clube_m = clubes.get(str(m_id), {})
                clube_v = clubes.get(str(v_id), {})
                realizado = p.get("placar_oficial_mandante") is not None
                
                jogo_data = {
                    "mandante": clube_m.get("abreviacao", "?"),
                    "mandanteNome": clube_m.get("nome", ""),
                    "visitante": clube_v.get("abreviacao", "?"),
                    "visitanteNome": clube_v.get("nome", ""),
                    "dataHora": p.get("partida_data", ""),
                    "local": p.get("local", ""),
                    "realizado": realizado,
                    "placarMandante": p.get("placar_oficial_mandante"),
                    "placarVisitante": p.get("placar_oficial_visitante"),
                    "probVitoriaMandante": None,
                    "probEmpate": None,
                    "probVitoriaVisitante": None,
                }
                
                # Gerar probabilidades
                stats_m = match_analyzer.estatisticas_times.get(m_id)
                stats_v = match_analyzer.estatisticas_times.get(v_id)
                if stats_m and stats_v:
                    try:
                        prev = predictor_pj.prever_confronto(
                            mandante=jogo_data["mandante"],
                            visitante=jogo_data["visitante"],
                            mandante_id=m_id,
                            visitante_id=v_id,
                            forca_mandante=stats_m.forca_geral,
                            forca_visitante=stats_v.forca_geral,
                            posicao_mandante=stats_m.posicao or 10,
                            posicao_visitante=stats_v.posicao or 10,
                        )
                        jogo_data["probVitoriaMandante"] = prev.prob_vitoria_casa
                        jogo_data["probEmpate"] = prev.prob_empate
                        jogo_data["probVitoriaVisitante"] = prev.prob_vitoria_fora
                    except Exception as e:
                        print(f"[PJ] Erro previsao {jogo_data.get('mandante')} vs {jogo_data.get('visitante')}: {e}")
                
                if not realizado:
                    proximos_jogos.append(jogo_data)
                else:
                    ultima_rodada_jogos.append(jogo_data)
            
            # Se todos da rodada atual já foram realizados, pegar próxima rodada
            if not proximos_jogos and rodada_atual < 38:
                p_resp_next = api.get_partidas(rodada_atual + 1)
                if isinstance(p_resp_next, dict):
                    p_list_next = p_resp_next.get("partidas", [])
                elif isinstance(p_resp_next, list):
                    p_list_next = p_resp_next
                else:
                    p_list_next = []
                
                for p in p_list_next:
                    m_id = p.get("clube_casa_id")
                    v_id = p.get("clube_visitante_id")
                    clube_m = clubes.get(str(m_id), {})
                    clube_v = clubes.get(str(v_id), {})
                    
                    jogo_data = {
                        "mandante": clube_m.get("abreviacao", "?"),
                        "mandanteNome": clube_m.get("nome", ""),
                        "visitante": clube_v.get("abreviacao", "?"),
                        "visitanteNome": clube_v.get("nome", ""),
                        "dataHora": p.get("partida_data", ""),
                        "local": p.get("local", ""),
                        "realizado": False,
                        "placarMandante": None,
                        "placarVisitante": None,
                        "probVitoriaMandante": None,
                        "probEmpate": None,
                        "probVitoriaVisitante": None,
                    }
                    
                    stats_m = match_analyzer.estatisticas_times.get(m_id)
                    stats_v = match_analyzer.estatisticas_times.get(v_id)
                    if stats_m and stats_v:
                        try:
                            prev = predictor_pj.prever_confronto(
                                mandante=jogo_data["mandante"],
                                visitante=jogo_data["visitante"],
                                mandante_id=m_id,
                                visitante_id=v_id,
                                forca_mandante=stats_m.forca_geral,
                                forca_visitante=stats_v.forca_geral,
                                posicao_mandante=stats_m.posicao or 10,
                                posicao_visitante=stats_v.posicao or 10,
                            )
                            jogo_data["probVitoriaMandante"] = prev.prob_vitoria_casa
                            jogo_data["probEmpate"] = prev.prob_empate
                            jogo_data["probVitoriaVisitante"] = prev.prob_vitoria_fora
                        except Exception:
                            pass
                    
                    proximos_jogos.append(jogo_data)
            
            # Se não temos jogos da rodada atual realizados, buscar rodada anterior
            if not ultima_rodada_jogos and rodada_atual > 1:
                p_resp_prev = api.get_partidas(rodada_atual - 1)
                if isinstance(p_resp_prev, dict):
                    p_list_prev = p_resp_prev.get("partidas", [])
                elif isinstance(p_resp_prev, list):
                    p_list_prev = p_resp_prev
                else:
                    p_list_prev = []
                
                for p in p_list_prev:
                    m_id = p.get("clube_casa_id")
                    v_id = p.get("clube_visitante_id")
                    clube_m = clubes.get(str(m_id), {})
                    clube_v = clubes.get(str(v_id), {})
                    realizado = p.get("placar_oficial_mandante") is not None
                    
                    if realizado:
                        jogo_data = {
                            "mandante": clube_m.get("abreviacao", "?"),
                            "mandanteNome": clube_m.get("nome", ""),
                            "visitante": clube_v.get("abreviacao", "?"),
                            "visitanteNome": clube_v.get("nome", ""),
                            "dataHora": p.get("partida_data", ""),
                            "local": p.get("local", ""),
                            "realizado": True,
                            "placarMandante": p.get("placar_oficial_mandante"),
                            "placarVisitante": p.get("placar_oficial_visitante"),
                            "probVitoriaMandante": None,
                            "probEmpate": None,
                            "probVitoriaVisitante": None,
                        }
                        
                        stats_m = match_analyzer.estatisticas_times.get(m_id)
                        stats_v = match_analyzer.estatisticas_times.get(v_id)
                        if stats_m and stats_v:
                            try:
                                prev = predictor_pj.prever_confronto(
                                    mandante=jogo_data["mandante"],
                                    visitante=jogo_data["visitante"],
                                    mandante_id=m_id,
                                    visitante_id=v_id,
                                    forca_mandante=stats_m.forca_geral,
                                    forca_visitante=stats_v.forca_geral,
                                    posicao_mandante=stats_m.posicao or 10,
                                    posicao_visitante=stats_v.posicao or 10,
                                )
                                jogo_data["probVitoriaMandante"] = prev.prob_vitoria_casa
                                jogo_data["probEmpate"] = prev.prob_empate
                                jogo_data["probVitoriaVisitante"] = prev.prob_vitoria_fora
                            except Exception:
                                pass
                        
                        ultima_rodada_jogos.append(jogo_data)
        except Exception as e:
            print(f"[Classificação] Erro ao buscar jogos: {e}")
        
        # Serializar pontosNecessarios do Monte Carlo
        pontos_nec_response = []
        if pontos_necessarios_mc:
            for pn in pontos_necessarios_mc:
                pontos_nec_response.append({
                    "probabilidade": pn.probabilidade,
                    "titulo": pn.titulo,
                    "libertadores": pn.libertadores,
                    "sulamericana": pn.sulamericana,
                    "permanencia": pn.permanencia,
                })
        
        response = {
            "rodada": rodada_atual,
            "classificacao": classificacao,
            "simulacao": simulacao,
            "pontosNecessarios": pontos_nec_response,
            "totalTimes": len(classificacao),
            "proximosJogos": proximos_jogos,
            "jogosRealizados": ultima_rodada_jogos,
        }
        
        # Cachear resultado em memória
        _classificacao_cache["data"] = response
        _classificacao_cache["timestamp"] = _time.time()

        # Salvar em disco para sobreviver restarts
        try:
            _classificacao_disk.parent.mkdir(parents=True, exist_ok=True)
            disk_data = dict(response)
            disk_data["_cache_ts"] = _time.time()
            _classificacao_disk.write_text(
                json.dumps(disk_data, ensure_ascii=False, default=str),
                encoding="utf-8",
            )
        except Exception:
            pass

        return response

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Erro classificação: {e}", exc_info=True)

        # Fallback: retornar dados stale do disco
        if disk_stale:
            logger.warning("Retornando classificação stale do disco")
            return disk_stale

        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@app.get("/api/brasileirao/rodada/{rodada}")
def get_rodada_detalhada(rodada: int):
    """
    Retorna detalhes de uma rodada: partidas + previsões + resultados reais.
    Permite comparar previsão vs realidade para rodadas passadas.
    """
    try:
        mercado = api.get_mercado()
        status = api.get_status_mercado()
        
        if not mercado:
            raise HTTPException(status_code=503, detail="API Cartola indisponível")
        
        clubes = mercado.get("clubes", {})
        rodada_atual = status.get("rodada_atual", 1) if status else 1
        
        partidas_response = api.get_partidas(rodada)
        if isinstance(partidas_response, dict):
            partidas = partidas_response.get("partidas", [])
        elif isinstance(partidas_response, list):
            partidas = partidas_response
        else:
            partidas = []
        
        if not partidas:
            return {"rodada": rodada, "partidas": [], "previsoes": []}
        
        # Carregar estatísticas
        match_analyzer.carregar_estatisticas_times(clubes, partidas)
        predictor = ScorePredictor()
        
        jogos = []
        previsoes = []
        
        for p in partidas:
            mandante_id = p.get("clube_casa_id")
            visitante_id = p.get("clube_visitante_id")
            
            clube_m = clubes.get(str(mandante_id), {})
            clube_v = clubes.get(str(visitante_id), {})
            
            jogo = {
                "mandanteId": mandante_id,
                "mandante": clube_m.get("abreviacao", p.get("clube_casa_abrev", "?")),
                "mandanteNome": clube_m.get("nome", ""),
                "visitanteId": visitante_id,
                "visitante": clube_v.get("abreviacao", p.get("clube_visitante_abrev", "?")),
                "visitanteNome": clube_v.get("nome", ""),
                "placarMandante": p.get("placar_oficial_mandante"),
                "placarVisitante": p.get("placar_oficial_visitante"),
                "local": p.get("local", ""),
                "dataHora": p.get("partida_data", ""),
                "realizado": p.get("placar_oficial_mandante") is not None,
            }
            jogos.append(jogo)
            
            # Gerar previsão
            stats_m = match_analyzer.estatisticas_times.get(mandante_id)
            stats_v = match_analyzer.estatisticas_times.get(visitante_id)
            
            if stats_m and stats_v:
                try:
                    previsao = predictor.prever_confronto(
                        mandante=jogo["mandante"],
                        visitante=jogo["visitante"],
                        mandante_id=mandante_id,
                        visitante_id=visitante_id,
                        forca_mandante=stats_m.forca_geral,
                        forca_visitante=stats_v.forca_geral,
                        posicao_mandante=stats_m.posicao or 10,
                        posicao_visitante=stats_v.posicao or 10,
                    )
                    previsoes.append({
                        "mandante": jogo["mandante"],
                        "visitante": jogo["visitante"],
                        "placarPrevisto": previsao.placar_provavel,
                        "placarReal": f"{jogo['placarMandante']}x{jogo['placarVisitante']}" if jogo["realizado"] else None,
                        "acertou": (previsao.placar_provavel == f"{jogo['placarMandante']}x{jogo['placarVisitante']}") if jogo["realizado"] else None,
                        "xgMandante": previsao.xg_mandante,
                        "xgVisitante": previsao.xg_visitante,
                        "confianca": previsao.confianca,
                    })
                except Exception:
                    pass
        
        acuracia = None
        acertos = [p for p in previsoes if p.get("acertou") is True]
        realizados = [p for p in previsoes if p.get("acertou") is not None]
        if realizados:
            acuracia = round(len(acertos) / len(realizados) * 100, 1)
        
        return {
            "rodada": rodada,
            "rodadaAtual": rodada_atual,
            "partidas": jogos,
            "previsoes": previsoes,
            "acuracia": acuracia,
            "totalPartidas": len(jogos),
        }
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Erro rodada: {e}", exc_info=True)

        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@app.get("/api/brasileirao/acuracia")
def get_acuracia_geral():
    """
    Retorna acurácia do modelo de previsão ao longo de todas as rodadas.
    Compara previsões vs resultados reais para cada rodada concluída.
    """
    try:
        cached = _cache_get("acuracia")
        if cached is not None:
            return cached
        
        status = api.get_status_mercado()
        rodada_atual = status.get("rodada_atual", 1) if status else 1
        
        resumo_rodadas = []
        total_acertos = 0
        total_jogos = 0
        
        for rodada in range(1, rodada_atual):
            try:
                resultado = get_rodada_detalhada(rodada)
                if resultado and resultado.get("previsoes"):
                    realizados = [p for p in resultado["previsoes"] if p.get("acertou") is not None]
                    acertos = [p for p in realizados if p["acertou"]]
                    
                    if realizados:
                        resumo_rodadas.append({
                            "rodada": rodada,
                            "totalPartidas": len(realizados),
                            "acertos": len(acertos),
                            "acuracia": round(len(acertos) / len(realizados) * 100, 1),
                        })
                        total_acertos += len(acertos)
                        total_jogos += len(realizados)
            except Exception:
                continue
        
        result = {
            "rodadaAtual": rodada_atual,
            "totalRodadas": len(resumo_rodadas),
            "totalJogos": total_jogos,
            "totalAcertos": total_acertos,
            "acuraciaGeral": round(total_acertos / max(total_jogos, 1) * 100, 1),
            "rodadas": resumo_rodadas,
            "metodologia": "Poisson V3 + Frequências contextuais",
        }
        _cache_set("acuracia", result)
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro acurácia: {e}", exc_info=True)

        raise HTTPException(status_code=500, detail="Erro interno do servidor")


# ============ Página por Time ============

# Mapeamento slug→abreviação Cartola (Série A 2025)
TEAM_SLUGS = {
    "atletico-mg": "CAM", "athletico-pr": "CAP", "bahia": "BAH", "botafogo": "BOT",
    "ceara": "CEA", "corinthians": "COR", "cruzeiro": "CRU", "flamengo": "FLA",
    "fluminense": "FLU", "fortaleza": "FOR", "gremio": "GRE", "internacional": "INT",
    "juventude": "JUV", "mirassol": "MIR", "palmeiras": "PAL",
    "red-bull-bragantino": "RBB", "bragantino": "RBB",
    "santos": "SAN", "sao-paulo": "SAO", "sport": "SPO", "vasco": "VAS", "vitoria": "VIT",
}


@app.get("/api/brasileirao/time/{slug}")
def get_time_detalhado(slug: str):
    """
    Retorna dados completos de um time: posição, probabilidades Monte Carlo,
    forma, próximos jogos com previsão, e estatísticas gerais.
    """
    slug = slug.lower()
    abrev = TEAM_SLUGS.get(slug)
    if not abrev:
        raise HTTPException(status_code=404, detail=f"Time '{slug}' não encontrado")

    cached = _cache_get("time_detail", slug)
    if cached is not None:
        return cached

    try:
        from src.analysis.monte_carlo import MonteCarloSimulator

        mercado = api.get_mercado()
        status = api.get_status_mercado()
        if not mercado:
            raise HTTPException(status_code=503, detail="API Cartola indisponível")

        clubes = mercado.get("clubes", {})
        rodada_atual = status.get("rodada_atual", 1) if status else 1

        # Encontrar time_id
        time_id = None
        for cid, c in clubes.items():
            if c.get("abreviacao", "").upper() == abrev:
                time_id = int(cid)
                break
        if not time_id:
            raise HTTPException(status_code=404, detail=f"Time {abrev} não encontrado na API")

        # Carregar estatísticas
        partidas_response = api.get_partidas(rodada_atual)
        partidas = partidas_response.get("partidas", []) if isinstance(partidas_response, dict) else partidas_response or []
        match_analyzer.carregar_estatisticas_times(clubes, partidas)

        stats = match_analyzer.estatisticas_times.get(time_id)
        if not stats:
            raise HTTPException(status_code=404, detail="Estatísticas não disponíveis")

        # Classificação + forças
        classificacao = []
        forca_times = {}
        for cid, s in match_analyzer.estatisticas_times.items():
            classificacao.append({
                "id": cid, "nome": s.nome, "abrev": s.abreviacao,
                "pontos": s.vitorias * 3 + s.empates,
                "jogos": s.jogos, "vitorias": s.vitorias,
                "empates": s.empates, "derrotas": s.derrotas,
                "gols_pro": s.gols_pro, "gols_contra": s.gols_contra,
            })
            forca_times[cid] = s.forca_geral

        classificacao.sort(
            key=lambda x: (x["pontos"], x["vitorias"],
                           x["gols_pro"] - x["gols_contra"], x["gols_pro"]),
            reverse=True,
        )
        posicao = next((i + 1 for i, t in enumerate(classificacao) if t["id"] == time_id), 0)

        # Monte Carlo (harmonizado com /classificacao: mesmo preditor e n_sims)
        prob = {"titulo": 0, "libertadores": 0, "sulamericana": 0, "rebaixamento": 0, "posicaoMedia": 10}
        try:
            mc = MonteCarloSimulator(score_predictor=ScorePredictor(), n_simulacoes=500)
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
                    if r % 2 == 0: m, v = v, m
                    jogos_restantes.append({"mandante_id": m, "visitante_id": v, "rodada": r})
            if jogos_restantes:
                resultados, _ = mc.simular_campeonato(classificacao, jogos_restantes, forca_times, xg_cache={})
                for res in resultados:
                    if res.time_id == time_id:
                        prob = {
                            "titulo": res.prob_titulo,
                            "libertadores": res.prob_libertadores,
                            "sulamericana": res.prob_sulamericana,
                            "rebaixamento": res.prob_rebaixamento,
                            "posicaoMedia": res.posicao_media,
                        }
                        break
        except Exception:
            pass

        # Próximos jogos com previsão (com limite de tempo)
        sp = ScorePredictor()
        proximos = []
        max_tentativas = 3  # Limitar a 3 rodadas para evitar timeout
        tentativas_falhadas = 0
        
        for r in range(rodada_atual, min(rodada_atual + 5, 39)):
            if tentativas_falhadas >= 2:  # Se 2 rodadas falharem, desistir
                break
            try:
                pd = api.get_partidas(r)
                if not pd or not isinstance(pd, dict):  # API retornou None ou não-dict
                    tentativas_falhadas += 1
                    continue
                    
                ps = pd.get("partidas", [])
                jogo_encontrado = False
                for p in ps:
                    casa = p.get("clube_casa_id", 0)
                    fora = p.get("clube_visitante_id", 0)
                    if time_id in (casa, fora):
                        c_info, f_info = clubes.get(str(casa), {}), clubes.get(str(fora), {})
                        prev = sp.prever_confronto(
                            mandante=c_info.get("nome", "?"), visitante=f_info.get("nome", "?"),
                            mandante_id=casa, visitante_id=fora,
                            forca_mandante=forca_times.get(casa, 50),
                            forca_visitante=forca_times.get(fora, 50),
                            rodada=r,
                        )
                        eh_casa = casa == time_id
                        proximos.append({
                            "rodada": r,
                            "adversario": f_info.get("abreviacao", "?") if eh_casa else c_info.get("abreviacao", "?"),
                            "adversarioNome": f_info.get("nome", "?") if eh_casa else c_info.get("nome", "?"),
                            "local": "Casa" if eh_casa else "Fora",
                            "placarProvavel": prev.placar_provavel,
                            "probVitoria": round(prev.prob_vitoria_casa if eh_casa else prev.prob_vitoria_fora, 1),
                            "probEmpate": round(prev.prob_empate, 1),
                            "probDerrota": round(prev.prob_vitoria_fora if eh_casa else prev.prob_vitoria_casa, 1),
                            "xgTime": round(prev.xg_mandante if eh_casa else prev.xg_visitante, 2),
                            "xgAdversario": round(prev.xg_visitante if eh_casa else prev.xg_mandante, 2),
                        })
                        jogo_encontrado = True
                        break
                        
                if not jogo_encontrado:
                    tentativas_falhadas += 1
            except Exception:
                tentativas_falhadas += 1
                continue

        clube_info = clubes.get(str(time_id), {})
        escudo = None
        if isinstance(clube_info.get("escudos"), dict):
            escudo = clube_info["escudos"].get("60x60")

        result = {
            "slug": slug,
            "id": time_id,
            "nome": stats.nome,
            "abrev": stats.abreviacao,
            "escudo": escudo,
            "posicao": posicao,
            "pontos": stats.vitorias * 3 + stats.empates,
            "jogos": stats.jogos,
            "vitorias": stats.vitorias,
            "empates": stats.empates,
            "derrotas": stats.derrotas,
            "golsPro": stats.gols_pro,
            "golsContra": stats.gols_contra,
            "saldoGols": stats.gols_pro - stats.gols_contra,
            "aproveitamento": round((stats.vitorias * 3 + stats.empates) / max(stats.jogos * 3, 1) * 100, 1),
            "forma": getattr(stats, "forma_sequencia", ""),
            "forcaCasa": getattr(stats, "forca_casa", 50),
            "forcaFora": getattr(stats, "forca_fora", 50),
            "forcaGeral": stats.forca_geral,
            "probabilidades": prob,
            "proximosJogos": proximos,
            "rodadaAtual": rodada_atual,
        }
        _cache_set("time_detail", result, slug)
        return result

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Erro time: {e}", exc_info=True)

        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@app.get("/api/brasileirao/jogo/{partida_id}")
def get_jogo_detalhado(partida_id: int):
    """
    Retorna análise completa de um jogo: 1X2, Over/Under, placares, xG, forma.
    """
    try:
        status = api.get_status_mercado()
        mercado = api.get_mercado()
        if not mercado:
            raise HTTPException(status_code=503, detail="API Cartola indisponível")

        clubes = mercado.get("clubes", {})
        rodada_atual = status.get("rodada_atual", 1) if status else 1

        # Buscar a partida em rodadas próximas
        partida_encontrada = None
        rodada_partida = None
        for r in range(max(1, rodada_atual - 2), min(rodada_atual + 3, 39)):
            pd = api.get_partidas(r)
            ps = pd.get("partidas", []) if isinstance(pd, dict) else pd or []
            for p in ps:
                if p.get("partida_id") == partida_id:
                    partida_encontrada = p
                    rodada_partida = r
                    break
            if partida_encontrada:
                break

        if not partida_encontrada:
            raise HTTPException(status_code=404, detail="Partida não encontrada")

        casa_id = partida_encontrada.get("clube_casa_id", 0)
        fora_id = partida_encontrada.get("clube_visitante_id", 0)
        casa_info = clubes.get(str(casa_id), {})
        fora_info = clubes.get(str(fora_id), {})

        casa_nome = casa_info.get("nome", "Time A")
        fora_nome = fora_info.get("nome", "Time B")
        casa_abrev = casa_info.get("abreviacao", "???")
        fora_abrev = fora_info.get("abreviacao", "???")

        # Carregar estatísticas
        partidas_rodada = api.get_partidas(rodada_atual)
        partidas_list = partidas_rodada.get("partidas", []) if isinstance(partidas_rodada, dict) else partidas_rodada or []
        match_analyzer.carregar_estatisticas_times(clubes, partidas_list)

        forca_casa = match_analyzer.estatisticas_times.get(casa_id)
        forca_fora = match_analyzer.estatisticas_times.get(fora_id)

        # Previsão completa
        sp = ScorePredictor()
        prev = sp.prever_confronto(
            mandante=casa_nome, visitante=fora_nome,
            mandante_id=casa_id, visitante_id=fora_id,
            forca_mandante=forca_casa.forca_geral if forca_casa else 50,
            forca_visitante=forca_fora.forca_geral if forca_fora else 50,
            rodada=rodada_partida or rodada_atual,
        )

        # Escudos
        def get_escudo(info):
            if isinstance(info.get("escudo"), dict):
                return info["escudo"].get("60x60")
            return None

        # Forma dos times
        def get_forma(stats):
            if not stats:
                return {"forma": "", "jogos": 0, "vitorias": 0, "empates": 0, "derrotas": 0, "golsPro": 0, "golsContra": 0}
            return {
                "forma": getattr(stats, "forma_sequencia", ""),
                "jogos": stats.jogos,
                "vitorias": stats.vitorias,
                "empates": stats.empates,
                "derrotas": stats.derrotas,
                "golsPro": stats.gols_pro,
                "golsContra": stats.gols_contra,
                "forcaCasa": getattr(stats, "forca_casa", 50),
                "forcaFora": getattr(stats, "forca_fora", 50),
            }

        # Resultado real (se já jogou)
        resultado_real = None
        placar_casa = partida_encontrada.get("placar_oficial_mandante")
        placar_fora = partida_encontrada.get("placar_oficial_visitante")
        if placar_casa is not None and placar_fora is not None:
            resultado_real = {"casa": placar_casa, "fora": placar_fora}

        return {
            "partidaId": partida_id,
            "rodada": rodada_partida,
            "mandante": {
                "id": casa_id,
                "nome": casa_nome,
                "abrev": casa_abrev,
                "escudo": get_escudo(casa_info),
                "stats": get_forma(forca_casa),
            },
            "visitante": {
                "id": fora_id,
                "nome": fora_nome,
                "abrev": fora_abrev,
                "escudo": get_escudo(fora_info),
                "stats": get_forma(forca_fora),
            },
            "previsao": {
                "placarProvavel": prev.placar_provavel,
                "probVitoriaCasa": round(prev.prob_vitoria_casa, 1),
                "probEmpate": round(prev.prob_empate, 1),
                "probVitoriaFora": round(prev.prob_vitoria_fora, 1),
                "xgCasa": round(prev.xg_mandante, 2),
                "xgFora": round(prev.xg_visitante, 2),
                "over15": round(prev.prob_over_1_5, 1),
                "over25": round(prev.prob_over_2_5, 1),
                "over35": round(prev.prob_over_3_5, 1),
                "btts": round(prev.prob_btts, 1),
                "topPlacares": [{"placar": p, "prob": round(pr, 1)} for p, pr in prev.top_placares[:5]],
                "confianca": round(prev.confianca, 1),
                "contexto": prev.contexto,
                "modo": prev.modo_previsao,
            },
            "resultadoReal": resultado_real,
            "local": partida_encontrada.get("local", ""),
            "data": partida_encontrada.get("partida_data", ""),
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Erro jogo: {e}", exc_info=True)

        raise HTTPException(status_code=500, detail="Erro interno do servidor")


# ============ Scouts ============

@app.get("/api/scouts/destaques")
def get_scouts_destaques(rodada: Optional[int] = None, limite: int = Query(default=15, le=50)):
    """
    Retorna jogadores destaque da rodada baseado em scouts.
    Inclui maiores pontuadores, artilheiros e assistentes.
    Fallback: usa cache JSON salvo pelo scheduler quando API ao vivo não disponível.
    """
    try:
        pontuados = api.get_atletas_pontuados()
        mercado = api.get_mercado()
        
        if not pontuados or not pontuados.get("atletas"):
            # Fallback: carregar do cache JSON (salvo pelo scheduler)
            import json
            from pathlib import Path
            
            cache_dir = Path("data")
            target_rodada = rodada
            if not target_rodada:
                status = api.get_status_mercado()
                target_rodada = status.get("rodada_atual", 1) if status else 1
            
            cache_file = cache_dir / f"scouts_rodada_{target_rodada}.json"
            # Tentar rodada atual, se não houver tentar a anterior
            if not cache_file.exists() and target_rodada > 1:
                cache_file = cache_dir / f"scouts_rodada_{target_rodada - 1}.json"
            
            if cache_file.exists():
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                return {
                    "rodada": cached.get("rodada"),
                    "destaques": cached.get("destaques", [])[:limite],
                    "artilheiros": cached.get("artilheiros", [])[:10],
                    "assistentes": cached.get("assistentes", [])[:10],
                    "totalJogadores": cached.get("totalJogadores", 0),
                    "fonte": "cache",
                }
            
            return {"rodada": rodada, "destaques": [], "artilheiros": [], "assistentes": []}
        
        clubes = mercado.get("clubes", {}) if mercado else {}
        atletas_dict = pontuados.get("atletas", {})
        
        # Montar lista ordenada por pontuação
        destaques = []
        artilheiros = []
        assistentes = []
        
        for atleta_id, dados in atletas_dict.items():
            scouts = dados.get("scout", {})
            pontos = dados.get("pontuacao", 0)
            clube_id = dados.get("clube_id", 0)
            clube_info = clubes.get(str(clube_id), {})
            
            jogador = {
                "id": int(atleta_id),
                "apelido": dados.get("apelido", ""),
                "clubeAbrev": clube_info.get("abreviacao", "?"),
                "clubeNome": clube_info.get("nome", ""),
                "pontuacao": round(pontos, 2),
                "scouts": {k: v for k, v in scouts.items() if v and v > 0},
                "gols": scouts.get("G", 0) or 0,
                "assistencias": scouts.get("A", 0) or 0,
                "saldoGols": scouts.get("SG", 0) or 0,
                "finalizacoesTrave": scouts.get("FT", 0) or 0,
                "desarmes": scouts.get("DS", 0) or 0,
            }
            
            destaques.append(jogador)
            if jogador["gols"] > 0:
                artilheiros.append(jogador)
            if jogador["assistencias"] > 0:
                assistentes.append(jogador)
        
        destaques.sort(key=lambda x: x["pontuacao"], reverse=True)
        artilheiros.sort(key=lambda x: x["gols"], reverse=True)
        assistentes.sort(key=lambda x: x["assistencias"], reverse=True)
        
        return {
            "rodada": rodada,
            "destaques": destaques[:limite],
            "artilheiros": artilheiros[:10],
            "assistentes": assistentes[:10],
            "totalJogadores": len(destaques),
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro scouts destaques: {e}", exc_info=True)

        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@app.get("/api/scouts/jogador/{atleta_id}")
def get_scout_jogador(atleta_id: int):
    """
    Retorna scouts detalhados de um jogador específico.
    Inclui dados do mercado + scouts da última rodada.
    """
    try:
        mercado = api.get_mercado()
        pontuados = api.get_atletas_pontuados()
        
        if not mercado:
            raise HTTPException(status_code=503, detail="API Cartola indisponível")
        
        atletas = mercado.get("atletas", [])
        clubes = mercado.get("clubes", {})
        
        # Encontrar o atleta
        atleta = None
        for a in atletas:
            if a.get("atleta_id") == atleta_id:
                atleta = a
                break
        
        if not atleta:
            raise HTTPException(status_code=404, detail="Jogador não encontrado")
        
        clube_id = atleta.get("clube_id", 0)
        clube_info = clubes.get(str(clube_id), {})
        
        pos_map = {1: "GOL", 2: "LAT", 3: "ZAG", 4: "MEI", 5: "ATA", 6: "TEC"}
        
        # Scouts da última rodada (se disponível)
        scouts_rodada = {}
        pontuacao_rodada = None
        if pontuados:
            atleta_pont = pontuados.get("atletas", {}).get(str(atleta_id))
            if atleta_pont:
                scouts_rodada = atleta_pont.get("scout", {})
                pontuacao_rodada = atleta_pont.get("pontuacao")
        
        return {
            "id": atleta_id,
            "nome": atleta.get("nome", ""),
            "apelido": atleta.get("apelido", ""),
            "foto": atleta.get("foto", ""),
            "posicao": pos_map.get(atleta.get("posicao_id", 0), "?"),
            "posicaoId": atleta.get("posicao_id", 0),
            "clubeId": clube_id,
            "clubeAbrev": clube_info.get("abreviacao", "?"),
            "clubeNome": clube_info.get("nome", ""),
            "preco": atleta.get("preco_num", 0),
            "media": atleta.get("media_num", 0),
            "pontosTotais": atleta.get("pontos_num", 0),
            "jogos": atleta.get("jogos_num", 0),
            "variacao": atleta.get("variacao_num", 0),
            "minimo": atleta.get("minimo_para_valorizar", 0),
            "statusId": atleta.get("status_id", 0),
            "scoutsRodada": {k: v for k, v in scouts_rodada.items() if v},
            "pontuacaoRodada": pontuacao_rodada,
            "scoutsAcumulados": atleta.get("scout", {}),
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro scout jogador: {e}", exc_info=True)

        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@app.get("/api/scouts/desfalques")
def get_desfalques_geral():
    """
    Retorna desfalques consolidados (lesionados, suspensos, dúvidas) de todos os clubes.
    Filtro por status_id: 3=Suspenso, 5=Contundido, 2=Dúvida.
    """
    try:
        mercado = api.get_mercado()
        
        if not mercado:
            raise HTTPException(status_code=503, detail="API Cartola indisponível")
        
        atletas = mercado.get("atletas", [])
        clubes = mercado.get("clubes", {})
        
        # Agrupar desfalques por clube
        desfalques_por_clube = {}
        
        for atleta in atletas:
            status_id = atleta.get("status_id", 0)
            if status_id not in (2, 3, 5):  # Dúvida, Suspenso, Contundido
                continue
            
            clube_id = atleta.get("clube_id", 0)
            if clube_id not in desfalques_por_clube:
                clube_info = clubes.get(str(clube_id), {})
                desfalques_por_clube[clube_id] = {
                    "clubeId": clube_id,
                    "clubeNome": clube_info.get("nome", ""),
                    "clubeAbrev": clube_info.get("abreviacao", "?"),
                    "lesionados": [],
                    "suspensos": [],
                    "duvidas": [],
                }
            
            apelido = atleta.get("apelido", atleta.get("nome", "?"))
            if status_id == 5:
                desfalques_por_clube[clube_id]["lesionados"].append(apelido)
            elif status_id == 3:
                desfalques_por_clube[clube_id]["suspensos"].append(apelido)
            elif status_id == 2:
                desfalques_por_clube[clube_id]["duvidas"].append(apelido)
        
        # Montar resposta
        clubes_lista = list(desfalques_por_clube.values())
        for c in clubes_lista:
            c["totalDesfalques"] = len(c["lesionados"]) + len(c["suspensos"]) + len(c["duvidas"])
        
        clubes_lista.sort(key=lambda x: x["totalDesfalques"], reverse=True)
        
        total_les = sum(len(c["lesionados"]) for c in clubes_lista)
        total_sus = sum(len(c["suspensos"]) for c in clubes_lista)
        total_duv = sum(len(c["duvidas"]) for c in clubes_lista)
        
        return {
            "totalClubes": len(clubes_lista),
            "clubes": clubes_lista,
            "resumo": {
                "totalLesionados": total_les,
                "totalSuspensos": total_sus,
                "totalDuvidas": total_duv,
                "totalGeral": total_les + total_sus + total_duv,
            },
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro desfalques: {e}", exc_info=True)

        raise HTTPException(status_code=500, detail="Erro interno do servidor")


# ============ OG Images Dinâmicas ============

def _generate_og_svg(title: str, subtitle: str, accent_color: str = "#22c55e") -> str:
    """Gera SVG 1200x630 para OG image."""
    # Escapar caracteres XML
    import html as _html
    title = _html.escape(title)
    subtitle = _html.escape(subtitle)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#1e293b"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="630" fill="url(#bg)"/>
  <rect x="0" y="0" width="1200" height="6" fill="{accent_color}"/>
  <text x="80" y="260" font-family="system-ui,sans-serif" font-size="52" font-weight="700" fill="#f8fafc">{title}</text>
  <text x="80" y="330" font-family="system-ui,sans-serif" font-size="28" fill="#94a3b8">{subtitle}</text>
  <text x="80" y="540" font-family="system-ui,sans-serif" font-size="36" font-weight="700" fill="{accent_color}">ScoutDados</text>
  <text x="80" y="580" font-family="system-ui,sans-serif" font-size="20" fill="#64748b">Brasileirão 2026 • Análises &amp; Estatísticas</text>
</svg>'''


@app.get("/api/og-image/jogo/{partida_id}")
def og_image_jogo(partida_id: int):
    """OG image SVG dinâmica para página de jogo."""
    try:
        status = api.get_status_mercado()
        mercado = api.get_mercado()
        if not mercado:
            raise HTTPException(status_code=503, detail="Sem dados")
        clubes = {c["id"]: c for c in mercado.get("clubes", {}).values()} if isinstance(mercado.get("clubes"), dict) else {}
        partidas = mercado.get("partidas", {})
        partida = partidas.get(str(partida_id))
        if not partida:
            raise HTTPException(status_code=404, detail="Partida não encontrada")
        mandante = clubes.get(partida.get("clube_casa_id"), {})
        visitante = clubes.get(partida.get("clube_visitante_id"), {})
        nome_m = mandante.get("nome", "Time A")
        nome_v = visitante.get("nome", "Time B")
        rodada = status.get("rodada_atual", "?")
        svg = _generate_og_svg(
            f"{nome_m}  vs  {nome_v}",
            f"Rodada {rodada} • Previsão de placares e probabilidades",
        )
    except HTTPException:
        raise
    except Exception:
        svg = _generate_og_svg("Análise de Jogo", "Brasileirão 2026 • ScoutDados")
    return FastAPIResponse(content=svg, media_type="image/svg+xml",
                           headers={"Cache-Control": "public, max-age=3600"})


@app.get("/api/og-image/time/{slug}")
def og_image_time(slug: str):
    """OG image SVG dinâmica para página de time."""
    from src.utils.team_mapping import SERIE_A_TIMES
    info = SERIE_A_TIMES.get(slug)
    nome = info["nome"] if info else slug.replace("-", " ").title()
    svg = _generate_og_svg(
        nome,
        "Estatísticas completas • Brasileirão 2026",
    )
    return FastAPIResponse(content=svg, media_type="image/svg+xml",
                           headers={"Cache-Control": "public, max-age=3600"})


# ============ Health, Sitemap, Métricas ============

@app.get("/health")
def health_check():
    """Health check para UptimeRobot/monitoramento."""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "cache_backend": cache.backend_name,
        "version": "3.0.0"
    }


@app.get("/api/admin/metrics")
def admin_metrics():
    """Métricas internas agregadas (últimas 24h)."""
    data = metrics.get_metrics()
    data["cache_backend"] = cache.backend_name
    data["circuit_breakers"] = {
        name: cb.get_status() for name, cb in circuit_breakers.items()
    }
    return data


@app.get("/sitemap.xml", response_class=FastAPIResponse)
def sitemap_xml():
    """Serve o sitemap completo gerado por generate_sitemap.py (scheduler).
    Fallback: gera um sitemap mínimo se o arquivo não existir."""
    from pathlib import Path as _P
    sitemap_file = _P(__file__).parent / "sitemap.xml"
    if sitemap_file.exists():
        xml = sitemap_file.read_text(encoding="utf-8")
    else:
        # Fallback mínimo — não deveria acontecer em prod
        base = "https://scoutdados.com.br"
        today = datetime.now().strftime("%Y-%m-%d")
        pages = ["/", "/brasileirao", "/confrontos", "/dashboard",
                 "/escalacao", "/mercado", "/scouts", "/blog"]
        urls_xml = "\n".join(
            f'  <url><loc>{base}{p}</loc><lastmod>{today}</lastmod></url>'
            for p in pages
        )
        xml = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls_xml}\n</urlset>'
    return FastAPIResponse(content=xml, media_type="application/xml")


# ============ Blog API (Posts Automáticos) ============

@app.get("/api/blog/posts")
def get_blog_posts():
    """
    Lista todos os posts de blog — estáticos + gerados automaticamente.
    Posts automáticos de análise de rodada vêm de data/blog_posts/.
    """
    try:
        from src.analysis.blog_generator import listar_posts_gerados
        auto_posts = listar_posts_gerados()
        return {"posts": auto_posts, "total": len(auto_posts)}
    except Exception as e:
        return {"posts": [], "total": 0, "error": str(e)}


@app.get("/api/blog/post/{slug}")
def get_blog_post(slug: str):
    """Retorna um post automático completo pelo slug."""
    try:
        from src.analysis.blog_generator import get_post_by_slug
        post = get_post_by_slug(slug)
        if not post:
            raise HTTPException(status_code=404, detail="Post não encontrado")
        return post
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar post: {e}", exc_info=True)

        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@app.post("/api/blog/gerar/{rodada}")
def gerar_blog_post(rodada: int, request: Request):
    """Gera manualmente um post de análise para uma rodada específica.
    Requer header X-Blog-Key para autenticação."""
    blog_key = os.environ.get("BLOG_API_KEY", "scoutdados-blog-2026")
    request_key = request.headers.get("X-Blog-Key", "")
    if request_key != blog_key:
        raise HTTPException(status_code=403, detail="Acesso negado. Header X-Blog-Key inválido.")
    try:
        from src.analysis.blog_generator import gerar_post_rodada
        post = gerar_post_rodada(rodada, api)
        if not post:
            raise HTTPException(status_code=404, detail="Sem dados para gerar post desta rodada")
        return {"status": "ok", "slug": post["slug"], "title": post["title"]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao gerar post: {e}", exc_info=True)

        raise HTTPException(status_code=500, detail="Erro interno do servidor")


# ============ Match Pages (Páginas Progressivas de Jogos) ============

@app.get("/api/jogos")
def list_match_pages(limit: int = 50):
    """Lista todas as páginas de jogos (pré-jogo e pós-jogo)."""
    try:
        from src.analysis.match_page_manager import MatchPageManager
        pm = MatchPageManager()
        pages = pm.listar_paginas(limit=limit)
        stats = pm.stats()
        return {"pages": pages, "stats": stats}
    except Exception as e:
        return {"pages": [], "stats": {}, "error": str(e)}


@app.get("/api/jogos/{slug}")
def get_match_page(slug: str):
    """Retorna página completa de um jogo pelo slug."""
    try:
        from src.analysis.match_page_manager import MatchPageManager
        pm = MatchPageManager()
        page = pm.get_pagina(slug)
        if not page:
            raise HTTPException(status_code=404, detail="Página de jogo não encontrada")
        return page
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar página: {e}", exc_info=True)

        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@app.post("/api/jogos/discover")
def discover_match_pages(days: int = 30):
    """Descobre jogos futuros e cria páginas base."""
    try:
        from src.analysis.match_page_manager import MatchPageManager
        pm = MatchPageManager()
        result = pm.discover_and_create(max_days_ahead=days)
        return {"status": "ok", **result}
    except Exception as e:
        logger.error(f"Erro na descoberta: {e}", exc_info=True)

        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@app.post("/api/jogos/update")
def update_match_pages():
    """Atualiza páginas de jogos nas janelas T-72h/T-48h/pós-jogo."""
    try:
        from src.analysis.match_page_manager import MatchPageManager
        pm = MatchPageManager()
        result = pm.update_upcoming()
        return {"status": "ok", **result}
    except Exception as e:
        logger.error(f"Erro na atualização: {e}", exc_info=True)

        raise HTTPException(status_code=500, detail="Erro interno do servidor")


# ============ Executar ============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
