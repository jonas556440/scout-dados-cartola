/**
 * Hook personalizado para usar a API do Cartola FC
 * Substitui os mockData por chamadas reais ao backend
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { cartolaApi } from '@/config/api';
import { cacheUtils } from '@/lib/persistor';
import type { 
    Player, 
    Team, 
    Match, 
    DashboardStats,
    PrevisaoRodadaResponse,
    PrevisaoCustomizadaRequest,
    PrevisaoCustomizadaResponse,
    NoticiasTimeResponse,
    NoticiasRodadaResponse,
    ConfrontosAnaliseResponse,
    ForcaTimesResponse,
    ForcaTime,
    ClassificacaoResponse,
    RodadaDetalhadaResponse,
    AcuraciaResponse,
    ScoutsDestaquesResponse,
    ScoutDetalhadoResponse,
    DesfalquesResponse,
} from '@/types/cartola';

// ============ Dashboard ============

export function useDashboard() {
    return useQuery({
        queryKey: ['dashboard'],
        queryFn: () => cartolaApi.getDashboard() as Promise<DashboardStats>,
        staleTime: 1000 * 60 * 5, // 5 minutos
        gcTime: 24 * 60 * 60 * 1000, // 24h para cache persist
        retry: 2,
        retryDelay: 1000,
        initialData: () => {
            try {
                return cacheUtils.dashboard.restoreData();
            } catch {
                return undefined;
            }
        },
    });
}

// ============ Status do Mercado ============

interface MercadoStatus {
    rodadaAtual: number;
    status: 'aberto' | 'fechado' | 'em_andamento';
    fechamento?: string;
}

export function useStatus() {
    return useQuery({
        queryKey: ['status'],
        queryFn: () => cartolaApi.getStatus() as Promise<MercadoStatus>,
        staleTime: 1000 * 60, // 1 minuto (status muda rápido)
        gcTime: 24 * 60 * 60 * 1000, // 24h para cache persist
        retry: 2,
        retryDelay: 1000,
        initialData: () => {
            try {
                return cacheUtils.status.restoreData();
            } catch {
                return undefined;
            }
        },
    });
}

// ============ Atletas ============

interface UseAtletasParams {
    posicao?: string;
    precoMax?: number;
    limite?: number;
}

export function useAtletas(params?: UseAtletasParams) {
    return useQuery({
        queryKey: ['atletas', params],
        queryFn: () => cartolaApi.getAtletas(params) as Promise<Player[]>,
        staleTime: 1000 * 60 * 5, // 5 minutos
        gcTime: 24 * 60 * 60 * 1000, // 24h para cache persist
        retry: 2,
        retryDelay: 1000,
        initialData: () => {
            try {
                return cacheUtils.mercado.restoreData();
            } catch {
                return undefined;
            }
        },
    });
}

// ============ Confrontos ============

export function useConfrontos(rodada?: number) {
    return useQuery({
        queryKey: ['confrontos', rodada],
        queryFn: () => cartolaApi.getConfrontos(rodada) as Promise<Match[]>,
        staleTime: 1000 * 60 * 10, // 10 minutos
        gcTime: 24 * 60 * 60 * 1000, // 24h para cache persist
        retry: 2,
        retryDelay: 1000,
        initialData: () => {
            try {
                return cacheUtils.confrontos.restoreData();
            } catch {
                return undefined;
            }
        },
    });
}

// ============ Confrontos Análise ============

export function useConfrontosAnalise(rodada?: number) {
    return useQuery({
        queryKey: ['confrontos-analise', rodada],
        queryFn: () => cartolaApi.getConfrontosAnalise(rodada) as Promise<ConfrontosAnaliseResponse>,
        staleTime: 1000 * 60 * 10, // 10 minutos
        gcTime: 24 * 60 * 60 * 1000, // 24h para cache persist
        retry: 2,
        retryDelay: 1000,
        initialData: () => {
            try {
                return cacheUtils.confrontos.restoreData();
            } catch {
                return undefined;
            }
        },
    });
}

// ============ Força dos Times ============

// ============ Força dos Times ============

export function useForcaTimes(rodada?: number) {
    return useQuery({
        queryKey: ['forca-times', rodada],
        queryFn: () => cartolaApi.getForcaTimes(rodada) as Promise<ForcaTimesResponse>,
        staleTime: 1000 * 60 * 30, // 30 minutos (muda pouco)
        gcTime: 24 * 60 * 60 * 1000, // 24h para cache persist
        retry: 2,
        retryDelay: 1000,
        initialData: () => {
            try {
                return cacheUtils.confrontos.restoreData();
            } catch {
                return undefined;
            }
        },
    });
}

// ============ Escalação ============

interface EscalacaoResponse {
    rodada: number;
    esquema: string;
    cartoletas: number;
    timeValorizacao: Team | null;
    timePontuacao: Team | null;
}

export function useEscalacao(esquema: string = '4-4-2', cartoletas: number = 100) {
    return useQuery({
        queryKey: ['escalacao', esquema, cartoletas],
        queryFn: () => cartolaApi.gerarEscalacao(esquema, cartoletas) as Promise<EscalacaoResponse>,
        staleTime: 1000 * 60 * 5, // 5 minutos
        gcTime: 24 * 60 * 60 * 1000, // 24h para cache persist
        retry: 2,
        retryDelay: 1000,
        enabled: true, // Sempre buscar quando mudar esquema/cartoletas
        initialData: () => {
            try {
                return cacheUtils.escalacao.restoreData();
            } catch {
                return undefined;
            }
        },
    });
}

// Hook com mutation para gerar sob demanda
export function useGerarEscalacao() {
    const queryClient = useQueryClient();
    
    return useMutation({
        mutationFn: ({ esquema, cartoletas }: { esquema: string; cartoletas: number }) =>
            cartolaApi.gerarEscalacao(esquema, cartoletas) as Promise<EscalacaoResponse>,
        onSuccess: (data, variables) => {
            // Atualizar cache
            queryClient.setQueryData(['escalacao', variables.esquema, variables.cartoletas], data);
            // Persistir em localStorage
            try {
                cacheUtils.escalacao.persistData(data);
            } catch {
                // Ignorar erros de localStorage
            }
        },
    });
}

// ============ Provider de dados ============

// ============ Histórico ============

interface HistoricoRodada {
    rodada: number;
    times_salvos: number;
    tipos: string[];
    data_criacao: string | null;
}

interface HistoricoStatus {
    total_rodadas: number;
    ultima_rodada: number;
    total_times: number;
    patrimonio_atual: number;
}

export function useHistoricoRodadas() {
    return useQuery({
        queryKey: ['historico-rodadas'],
        queryFn: () => cartolaApi.getHistoricoRodadas() as Promise<HistoricoRodada[]>,
        staleTime: 1000 * 60 * 10, // 10 minutos
        retry: 2,
        retryDelay: 1000,
    });
}

export function useHistoricoRodada(rodada: number) {
    return useQuery({
        queryKey: ['historico-rodada', rodada],
        queryFn: () => cartolaApi.getHistoricoRodada(rodada),
        staleTime: 1000 * 60 * 10,
        enabled: rodada > 0,
        retry: 2,
        retryDelay: 1000,
    });
}

export function useHistoricoStatus() {
    return useQuery({
        queryKey: ['historico-status'],
        queryFn: () => cartolaApi.getHistoricoStatus() as Promise<HistoricoStatus>,
        staleTime: 1000 * 60 * 5,
        retry: 2,
        retryDelay: 1000,
    });
}

// ============ Salvar Time ============

export function useSalvarTime() {
    const queryClient = useQueryClient();
    
    return useMutation({
        mutationFn: (data: {
            tipo: string;
            rodada: number;
            titulares_ids: number[];
            capitao_id: number;
            esquema?: string;
            cartoletas: number;
            pontuacaoEsperada?: number;
        }) => cartolaApi.salvarTime(data),
        onSuccess: () => {
            // Invalidar cache do histórico para refletir o novo time
            queryClient.invalidateQueries({ queryKey: ['historico-rodadas'] });
            queryClient.invalidateQueries({ queryKey: ['historico-status'] });
        },
    });
}

// ============ ENDPOINTS ÓRFÃOS - CONECTADOS (FASE 1) ============

// /api/previsoes/placares - Previsão de placares da rodada
export function usePrevisaoPlacares(rodada?: number) {
    return useQuery({
        queryKey: ['previsao-placares', rodada],
        queryFn: () => cartolaApi.getPrevisaoPlacares(rodada) as Promise<PrevisaoRodadaResponse>,
        staleTime: 1000 * 60 * 30, // 30 minutos (previsões mudam pouco)
        gcTime: 24 * 60 * 60 * 1000, // 24h para cache persist
        retry: 2,
        retryDelay: 1000,
    });
}

// /api/previsoes/customizado - Previsão de jogo customizado (mutation)
export function usePrevisaoCustomizada() {
    return useMutation({
        mutationFn: (request: PrevisaoCustomizadaRequest) => 
            cartolaApi.postPrevisaoCustomizada(request) as Promise<PrevisaoCustomizadaResponse>,
    });
}

// /api/noticias/{clube_abrev} - Notícias e desfalques de um time
export function useNoticiasTime(clubeAbrev: string) {
    return useQuery({
        queryKey: ['noticias-time', clubeAbrev],
        queryFn: () => cartolaApi.getNoticiasTime(clubeAbrev) as Promise<NoticiasTimeResponse>,
        staleTime: 1000 * 60 * 15, // 15 minutos (notícias mudam relativamente rápido)
        gcTime: 24 * 60 * 60 * 1000, // 24h para cache persist
        retry: 2,
        retryDelay: 1000,
        enabled: !!clubeAbrev, // Só buscar se tiver clube
    });
}

// /api/noticias/rodada/{rodada} - Desfalques consolidados da rodada
export function useNoticiasRodada(rodada?: number) {
    return useQuery({
        queryKey: ['noticias-rodada', rodada],
        queryFn: () => cartolaApi.getNoticiasRodada(rodada) as Promise<NoticiasRodadaResponse>,
        staleTime: 1000 * 60 * 20, // 20 minutos
        gcTime: 24 * 60 * 60 * 1000, // 24h para cache persist
        retry: 2,
        retryDelay: 1000,
    });
}

// ============ Brasileirão ============

export function useClassificacao() {
    return useQuery({
        queryKey: ['brasileirao-classificacao'],
        queryFn: () => cartolaApi.getClassificacao() as Promise<ClassificacaoResponse>,
        staleTime: 1000 * 60 * 10,
        gcTime: 24 * 60 * 60 * 1000,
        retry: 2,
        retryDelay: 1000,
    });
}

export function useRodadaDetalhada(rodada: number) {
    return useQuery({
        queryKey: ['brasileirao-rodada', rodada],
        queryFn: () => cartolaApi.getRodadaDetalhada(rodada) as Promise<RodadaDetalhadaResponse>,
        staleTime: 1000 * 60 * 10,
        gcTime: 24 * 60 * 60 * 1000,
        retry: 2,
        enabled: rodada > 0,
    });
}

export function useAcuracia() {
    return useQuery({
        queryKey: ['brasileirao-acuracia'],
        queryFn: () => cartolaApi.getAcuracia() as Promise<AcuraciaResponse>,
        staleTime: 1000 * 60 * 30,
        gcTime: 24 * 60 * 60 * 1000,
        retry: 2,
    });
}

// ============ Scouts ============

export function useScoutsDestaques(rodada?: number) {
    return useQuery({
        queryKey: ['scouts-destaques', rodada],
        queryFn: () => cartolaApi.getScoutsDestaques(rodada) as Promise<ScoutsDestaquesResponse>,
        staleTime: 1000 * 60 * 10,
        gcTime: 24 * 60 * 60 * 1000,
        retry: 2,
    });
}

export function useScoutJogador(atletaId: number) {
    return useQuery({
        queryKey: ['scout-jogador', atletaId],
        queryFn: () => cartolaApi.getScoutJogador(atletaId) as Promise<ScoutDetalhadoResponse>,
        staleTime: 1000 * 60 * 10,
        gcTime: 24 * 60 * 60 * 1000,
        retry: 2,
        enabled: atletaId > 0,
    });
}

export function useDesfalques() {
    return useQuery({
        queryKey: ['scouts-desfalques'],
        queryFn: () => cartolaApi.getDesfalques() as Promise<DesfalquesResponse>,
        staleTime: 1000 * 60 * 15,
        gcTime: 24 * 60 * 60 * 1000,
        retry: 2,
    });
}

// ============ Provider de dados ============

// Hook combinado para páginas que precisam de múltiplos dados
export function useCartolaData() {
    const status = useStatus();
    const dashboard = useDashboard();
    
    return {
        status: status.data,
        dashboard: dashboard.data,
        isLoading: status.isLoading || dashboard.isLoading,
        isError: status.isError || dashboard.isError,
        error: status.error || dashboard.error,
        refetch: () => {
            status.refetch();
            dashboard.refetch();
        },
    };
}

// ============ Utils ============

// Converter posição para ID
export const posicaoToId: Record<string, number> = {
    'GOL': 1,
    'LAT': 2,
    'ZAG': 3,
    'MEI': 4,
    'ATA': 5,
    'TEC': 6,
};

// Converter ID para posição
export const idToPosicao: Record<number, string> = {
    1: 'GOL',
    2: 'LAT',
    3: 'ZAG',
    4: 'MEI',
    5: 'ATA',
    6: 'TEC',
};

// Cores por posição
export const posicaoCores: Record<string, string> = {
    'GOL': 'bg-yellow-500',
    'LAT': 'bg-green-500',
    'ZAG': 'bg-blue-500',
    'MEI': 'bg-purple-500',
    'ATA': 'bg-red-500',
    'TEC': 'bg-gray-500',
};

// Formatar preço
export function formatarPreco(valor: number): string {
    return `C$ ${valor.toFixed(2).replace('.', ',')}`;
}

// Formatar porcentagem
export function formatarPorcentagem(valor: number): string {
    return `${valor.toFixed(1).replace('.', ',')}%`;
}
