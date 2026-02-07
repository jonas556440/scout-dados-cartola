/**
 * Configuração da API do Cartola FC 2026
 */

// Usar URL vazia para usar o proxy do Vite (mesma origem)
// Se VITE_API_URL estiver definido, usar ela (para produção)
export const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export const API_ENDPOINTS = {
    status: '/api/status',
    atletas: '/api/mercado/atletas',
    confrontos: '/api/confrontos',
    confrontosAnalise: '/api/confrontos/analise',
    gerarEscalacao: '/api/escalacao/gerar',
    dashboard: '/api/dashboard',
    forcaTimes: '/api/times/forca',
    historicoRodadas: '/api/historico/rodadas',
    historicoRodada: '/api/historico/rodada',
    historicoStatus: '/api/historico/status',
    historicoSalvar: '/api/historico/salvar',
    // Endpoints órfãos - Fase 1
    previsaoPlacares: '/api/previsoes/placares',
    previsaoCustomizado: '/api/previsoes/customizado',
    noticiasTime: '/api/noticias',
    noticiasRodada: '/api/noticias/rodada',
    // Brasileirão - Fase 2
    brasileiraoClassificacao: '/api/brasileirao/classificacao',
    brasileiraoRodada: '/api/brasileirao/rodada',
    brasileiraoAcuracia: '/api/brasileirao/acuracia',
    // Scouts - Fase 2
    scoutsDestaques: '/api/scouts/destaques',
    scoutsJogador: '/api/scouts/jogador',
    scoutsDesfalques: '/api/scouts/desfalques',
    // Blog automático
    blogPosts: '/api/blog/posts',
    blogPost: '/api/blog/post',
    // xG por time
    timesXG: '/api/times/xg',
    // Páginas por time e jogo
    brasileiraoTime: '/api/brasileirao/time',
    brasileiraoJogo: '/api/brasileirao/jogo',
} as const;

export async function apiRequest<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const response = await fetch(url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options?.headers,
        },
    });
    
    if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
}

export const cartolaApi = {
    getStatus: () => apiRequest(API_ENDPOINTS.status),
    
    getAtletas: (params?: { posicao?: string; precoMax?: number; limite?: number }) => {
        const searchParams = new URLSearchParams();
        if (params?.posicao) searchParams.set('posicao', params.posicao);
        if (params?.precoMax) searchParams.set('preco_max', params.precoMax.toString());
        if (params?.limite) searchParams.set('limite', params.limite.toString());
        
        const query = searchParams.toString();
        return apiRequest(`${API_ENDPOINTS.atletas}${query ? `?${query}` : ''}`);
    },
    
    getConfrontos: (rodada?: number) => {
        const query = rodada ? `?rodada=${rodada}` : '';
        return apiRequest(`${API_ENDPOINTS.confrontos}${query}`);
    },
    
    getConfrontosAnalise: (rodada?: number) => {
        const query = rodada ? `?rodada=${rodada}` : '';
        return apiRequest(`${API_ENDPOINTS.confrontosAnalise}${query}`);
    },
    
    gerarEscalacao: (esquema: string = '4-4-2', cartoletas: number = 100) => {
        return apiRequest(`${API_ENDPOINTS.gerarEscalacao}?esquema=${esquema}&cartoletas=${cartoletas}`);
    },
    
    getDashboard: () => apiRequest(API_ENDPOINTS.dashboard),
    
    getForcaTimes: (rodada?: number) => {
        const query = rodada ? `?rodada=${rodada}` : '';
        return apiRequest(`${API_ENDPOINTS.forcaTimes}${query}`);
    },
    
    getHistoricoRodadas: () => apiRequest(API_ENDPOINTS.historicoRodadas),
    
    getHistoricoRodada: (rodada: number) => 
        apiRequest(`${API_ENDPOINTS.historicoRodada}/${rodada}`),
    
    getHistoricoStatus: () => apiRequest(API_ENDPOINTS.historicoStatus),
    
    salvarTime: (data: {
        tipo: string;
        rodada: number;
        titulares_ids: number[];
        capitao_id: number;
        esquema?: string;
        cartoletas: number;
        pontuacaoEsperada?: number;
    }) => apiRequest(API_ENDPOINTS.historicoSalvar, {
        method: 'POST',
        body: JSON.stringify(data),
    }),
    
    // ========== ENDPOINTS ÓRFÃOS - CONECTADOS (FASE 1) ==========
    
    // GET /api/previsoes/placares - Previsão de placares da rodada
    getPrevisaoPlacares: (rodada?: number) => {
        const query = rodada ? `?rodada=${rodada}` : '';
        return apiRequest(`${API_ENDPOINTS.previsaoPlacares}${query}`);
    },
    
    // POST /api/previsoes/customizado - Previsão de jogo customizado
    // Backend usa query params, não body JSON
    postPrevisaoCustomizada: (data: {
        mandante: string;
        visitante: string;
        forcaMandante?: number;
        forcaVisitante?: number;
    }) => {
        const params = new URLSearchParams({
            mandante: data.mandante,
            visitante: data.visitante,
            forca_mandante: String(data.forcaMandante || 50),
            forca_visitante: String(data.forcaVisitante || 50),
        });
        return apiRequest(`${API_ENDPOINTS.previsaoCustomizado}?${params}`, {
            method: 'POST',
        });
    },
    
    // GET /api/noticias/{clube_abrev} - Notícias e desfalques de um time
    getNoticiasTime: (clubeAbrev: string) => 
        apiRequest(`${API_ENDPOINTS.noticiasTime}/${clubeAbrev.toUpperCase()}`),
    
    // GET /api/noticias/rodada/{rodada} - Desfalques consolidados da rodada
    getNoticiasRodada: (rodada?: number) => {
        const query = rodada ? `/${rodada}` : '';
        return apiRequest(`${API_ENDPOINTS.noticiasRodada}${query}`);
    },

    // ========== BRASILEIRÃO (FASE 2) ==========

    getClassificacao: () => apiRequest(API_ENDPOINTS.brasileiraoClassificacao),

    getRodadaDetalhada: (rodada: number) =>
        apiRequest(`${API_ENDPOINTS.brasileiraoRodada}/${rodada}`),

    getAcuracia: () => apiRequest(API_ENDPOINTS.brasileiraoAcuracia),

    // ========== SCOUTS (FASE 2) ==========

    getScoutsDestaques: (rodada?: number, limite?: number) => {
        const params = new URLSearchParams();
        if (rodada) params.set('rodada', rodada.toString());
        if (limite) params.set('limite', limite.toString());
        const query = params.toString();
        return apiRequest(`${API_ENDPOINTS.scoutsDestaques}${query ? `?${query}` : ''}`);
    },

    getScoutJogador: (atletaId: number) =>
        apiRequest(`${API_ENDPOINTS.scoutsJogador}/${atletaId}`),

    getDesfalques: () => apiRequest(API_ENDPOINTS.scoutsDesfalques),

    // ========== BLOG AUTOMÁTICO ==========

    getBlogPosts: () => apiRequest(API_ENDPOINTS.blogPosts),

    getBlogPost: (slug: string) =>
        apiRequest(`${API_ENDPOINTS.blogPost}/${slug}`),

    // ========== xG POR TIME ==========

    getTimesXG: (rodada?: number) => {
        const query = rodada ? `?rodada=${rodada}` : '';
        return apiRequest(`${API_ENDPOINTS.timesXG}${query}`);
    },

    // ========== PÁGINAS POR TIME / JOGO ==========

    getTimeDetalhado: (slug: string) =>
        apiRequest(`${API_ENDPOINTS.brasileiraoTime}/${slug}`),

    getJogoDetalhado: (partidaId: number) =>
        apiRequest(`${API_ENDPOINTS.brasileiraoJogo}/${partidaId}`),
};
