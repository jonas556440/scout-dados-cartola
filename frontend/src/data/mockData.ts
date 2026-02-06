/**
 * ATENÇÃO: Este arquivo contém apenas fallbacks vazios!
 * Todas as páginas devem usar os hooks da API real:
 * - useDashboard()
 * - useEscalacao()
 * - useConfrontos()
 * - useAtletas()
 * 
 * Os dados mock foram REMOVIDOS - use a API!
 */

export const mockDashboardStats = {
  mercado: {
    rodadaAtual: 1,
    status: 'aberto' as const,
    fechamento: Date.now() + 3600000,
    totalAtletas: 0,
    provaveis: 0,
    duvidas: 0,
  },
  patrimonio: {
    cartoletas: 100,
    valorTime: 0,
    pontuacaoTotal: 0,
    variacao: 0,
  },
  topValorizadores: [],
  topPontuadores: [],
  confrontos: [],
};

export const mockTeamValorizacao = {
  nome: "Use a API - useEscalacao()",
  tipo: 'valorizacao' as const,
  esquema: '4-4-2',
  rodada: 1,
  titulares: [],
  reservas: [],
  capitao: null,
  custoTotal: 0,
  cartoletas: 100,
};

export const mockTeamPontuacao = {
  nome: "Use a API - useEscalacao()",
  tipo: 'pontuacao' as const,
  esquema: '4-4-2',
  rodada: 1,
  titulares: [],
  reservas: [],
  capitao: null,
  custoTotal: 0,
  cartoletas: 100,
};

export const mockPatrimony = [];

export const mockPlayers = [];

export const mockClubs = [];

export const mockMatches = [];
