"""
API REST para Cartola FC 2026
Endpoints para integrar com o frontend React

Framework: FastAPI
Formato: JSON compatível com src/types/cartola.ts do frontend
"""
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import sys
from pathlib import Path

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

# Segurança
from src.utils.rate_limiter import limiter, setup_rate_limiting, RATE_LIMITS
from src.utils.security_headers import SecurityHeadersMiddleware
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
    "https://scoutfutebol.com.br",
    "https://www.scoutfutebol.com.br",
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
    allow_headers=["*"],
    max_age=3600,  # Cache preflight por 1 hora
)

# Security Headers (X-Frame-Options, X-Content-Type-Options, etc)
app.add_middleware(SecurityHeadersMiddleware)

# Rate Limiting (proteção contra DDoS/abuso)
setup_rate_limiting(app)

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
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


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
        raise HTTPException(status_code=500, detail=f"Erro ao buscar atletas: {str(e)}")


@app.get("/api/confrontos", response_model=List[MatchResponse])
def get_confrontos(rodada: Optional[int] = None):
    """Retorna análise de confrontos da rodada com previsão de placares"""
    try:
        mercado = api.get_mercado()
        status = api.get_status_mercado()
        
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
        
        # Gerar previsões de placar usando Poisson
        match_analyzer.carregar_estatisticas_times(clubes, partidas)
        score_predictor = ScorePredictor()
        previsoes = score_predictor.prever_rodada(partidas, match_analyzer.estatisticas_times)
        
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
            
            responses.append(response)
        
        return responses
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao analisar confrontos: {str(e)}")


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
    - Over/Under 2.5 gols
    - BTTS (Ambos marcam)
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
        
        # Prever placares
        score_predictor = ScorePredictor()
        previsoes = score_predictor.prever_rodada(partidas, match_analyzer.estatisticas_times)
        
        # Converter para response
        resultado = {
            "rodada": rodada,
            "metodologia": "Distribuição de Poisson + Expected Goals (xG)",
            "referencia": "Frontiers in Sports, PLOS ONE (2021-2023)",
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
        raise HTTPException(status_code=500, detail=f"Erro na previsão: {str(e)}")


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
    """Gera times otimizados (valorização e pontuação)"""
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
            "timePontuacao": time_para_response(time_pontos, "pontuacao")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar escalação: {str(e)}")


@app.get("/api/dashboard", response_model=DashboardStatsResponse)
@limiter.limit(RATE_LIMITS["default"])  # 200/min
def get_dashboard(request: Request):
    """Retorna estatísticas para o dashboard"""
    try:
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
        
        return DashboardStatsResponse(
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no dashboard: {str(e)}")


@app.post("/api/cache/limpar")
def limpar_cache():
    """
    Limpa o cache e força nova consulta à API do Cartola
    Use quando precisar de dados atualizados
    """
    try:
        api.limpar_cache()
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
        
        session.close()
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar histórico: {str(e)}")


@app.get("/api/historico/rodada/{rodada}")
def get_historico_rodada(rodada: int):
    """
    Retorna escalações salvas de uma rodada específica
    """
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
        
        session.close()
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar rodada: {str(e)}")


@app.get("/api/historico/status")
def get_historico_status():
    """
    Retorna estatísticas do histórico
    """
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
        
        session.close()
        
        return {
            "total_times_salvos": total,
            "total_rodadas": rodadas,
            "ultima_atualizacao": ultimo.created_at.isoformat() if ultimo else None,
            "banco_ativo": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar status: {str(e)}")


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
        raise HTTPException(status_code=500, detail=f"Erro ao buscar notícias: {str(e)}")


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
        raise HTTPException(status_code=500, detail=f"Erro ao buscar notícias da rodada: {str(e)}")


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
        raise HTTPException(status_code=500, detail=f"Erro na previsão: {str(e)}")


@app.get("/api/times/forca")
def get_forca_times(rodada: Optional[int] = None):
    """
    Retorna força calculada de todos os times
    
    Usa sistema ponderado:
    - 80% ranking histórico (início do campeonato)
    - 20% posição atual na tabela
    - Ajuste conforme avançam as rodadas
    
    Retorna lista ordenada por força geral
    """
    try:
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
                "escudo": clube_info.get("escudo", {}).get("60x60") if isinstance(clube_info.get("escudo"), dict) else None
            })
        
        # Ordenar por força geral
        times_forca.sort(key=lambda x: x["forcaGeral"], reverse=True)
        
        # Adicionar ranking
        for i, time in enumerate(times_forca, 1):
            time["ranking"] = i
        
        return {
            "rodada": rodada,
            "times": times_forca,
            "metodologia": "80% ranking histórico + 20% classificação atual (início campeonato)",
            "peso_historico": 0.80 if rodada <= 5 else max(0.30, 0.80 - ((rodada - 5) * 0.05))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao calcular força: {str(e)}")


# ============ Executar ============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
