/**
 * Hook personalizado para usar a API do Cartola FC
 * Substitui os mockData por chamadas reais ao backend
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { cartolaApi } from '@/config/api';
import type { Player, Team, Match, DashboardStats } from '@/types/cartola';

// ============ Dashboard ============

export function useDashboard() {
    return useQuery({
        queryKey: ['dashboard'],
        queryFn: () => cartolaApi.getDashboard() as Promise<DashboardStats>,
        staleTime: 1000 * 60 * 5, // 5 minutos
        refetchInterval: 1000 * 60 * 5, // Atualizar a cada 5 min
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
        staleTime: 1000 * 60, // 1 minuto
        refetchInterval: 1000 * 60, // Atualizar a cada minuto
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
    });
}

// ============ Confrontos ============

export function useConfrontos(rodada?: number) {
    return useQuery({
        queryKey: ['confrontos', rodada],
        queryFn: () => cartolaApi.getConfrontos(rodada) as Promise<Match[]>,
        staleTime: 1000 * 60 * 10, // 10 minutos
    });
}

interface ConfrontosAnalise {
    rodada: number;
    timesParaEscalar: Array<{
        clubeId: number;
        nome: string;
        abrev: string;
        adversario: string;
        local: string;
        dificuldade: string;
        chanceSg: number;
        expectativaGols: number;
        scoreGeral: number;
    }>;
    timesParaEvitar: Array<{
        clubeId: number;
        abrev: string;
        adversario: string;
        dificuldade: string;
    }>;
    melhoresParaSg: Array<{
        clubeId: number;
        abrev: string;
        adversario: string;
        chanceSg: number;
    }>;
    melhoresParaGols: Array<{
        clubeId: number;
        abrev: string;
        adversario: string;
        expectativaGols: number;
    }>;
}

export function useConfrontosAnalise(rodada?: number) {
    return useQuery({
        queryKey: ['confrontos-analise', rodada],
        queryFn: () => cartolaApi.getConfrontosAnalise(rodada) as Promise<ConfrontosAnalise>,
        staleTime: 1000 * 60 * 10, // 10 minutos
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
        enabled: true, // Sempre buscar quando mudar esquema/cartoletas
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
        },
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
