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
};
