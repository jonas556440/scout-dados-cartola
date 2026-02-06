// Tipos para Cartola FC 2026

export type Position = 'GOL' | 'ZAG' | 'LAT' | 'MEI' | 'ATA' | 'TEC';

export interface Player {
  id: number;
  nome: string;
  apelido: string;
  posicao: Position;
  posicaoId: number;
  clubeId: number;
  clubeAbrev: string;
  clubeNome: string;
  clubeEscudo?: string;
  preco: number;
  media: number;
  pontuacao: number;
  jogos: number;
  status: 'provavel' | 'duvida' | 'suspenso' | 'contundido' | 'nulo';
  scouts?: Scouts;
  tendencia?: number;
  potencial?: number;
  valorizacao?: number;
  mpv_score?: number; // Score de valorização calculado pelo MPVCalculator
  xG?: number;
  xA?: number;
}

export interface Scouts {
  // Positivos
  G?: number;   // Gol
  A?: number;   // Assistência
  SG?: number;  // Saldo de gols
  DS?: number;  // Desarme
  FS?: number;  // Falta sofrida
  FF?: number;  // Finalização para fora
  FD?: number;  // Finalização defendida
  FT?: number;  // Finalização na trave
  DD?: number;  // Defesa difícil
  DP?: number;  // Defesa de pênalti
  GS?: number;  // Gol sofrido
  PS?: number;  // Pênalti sofrido
  PC?: number;  // Pênalti cometido
  FC?: number;  // Falta cometida
  // Negativos
  CA?: number;  // Cartão amarelo
  CV?: number;  // Cartão vermelho
  GC?: number;  // Gol contra
  PP?: number;  // Pênalti perdido
  I?: number;   // Impedimento
}

export interface Team {
  id?: number;
  nome: string;
  tipo: 'valorizacao' | 'pontuacao';
  esquema: string;
  rodada: number;
  titulares: Player[];
  reservas: Player[];
  capitao?: Player;
  custoTotal: number;
  cartoletas: number;
  pontuacaoEsperada?: number;
  pontuacaoReal?: number;
}

export interface Club {
  id: number;
  nome: string;
  abrev: string;
  escudo?: string;
  posicao?: number;
  pontos?: number;
  jogos?: number;
  vitorias?: number;
  empates?: number;
  derrotas?: number;
  golsPro?: number;
  golsContra?: number;
  forcaCasa?: number;
  forcaFora?: number;
}

export interface Match {
  id: number;
  rodada: number;
  mandanteId: number;
  mandante: Club;
  visitanteId: number;
  visitante: Club;
  local: string;
  data?: string;
  hora?: string;
  aproveitamentoMandante?: number;
  aproveitamentoVisitante?: number;
  probabilidadeMandante?: number;
  probabilidadeEmpate?: number;
  probabilidadeVisitante?: number;
  
  // Previsão de placar (Distribuição de Poisson)
  placarProvavel?: string;
  probabilidadePlacar?: number;
  xgMandante?: number;
  xgVisitante?: number;
  over25?: number;
  btts?: number;
}

export interface RoundStatus {
  rodadaAtual: number;
  status: 'aberto' | 'fechado' | 'em_andamento';
  fechamento?: string;
  partidas: Match[];
}

export interface Patrimony {
  rodada: number;
  cartoletas: number;
  valorTime: number;
  pontuacaoTotal: number;
  variacao: number;
  data: string;
}

export interface TeamHistory {
  id: number;
  rodada: number;
  tipo: 'valorizacao' | 'pontuacao';
  esquema: string;
  custoTotal: number;
  cartoletas: number;
  pontuacaoObtida?: number;
  valorizacaoObtida?: number;
  titulares: Player[];
  reservas: Player[];
  capitao: Player;
  dataCriacao: string;
}

export interface DashboardStats {
  mercado: {
    rodadaAtual: number;
    status: string;
    fechamento?: string;
    totalAtletas: number;
    provaveis: number;
    duvidas: number;
    precoMedio?: number;
    valorizados?: number;
    desvalorizados?: number;
  };
  patrimonio?: number;
  topValorizadores: Player[];
  topPontuadores: Player[];
  confrontos: Match[];
}

export interface FormationPosition {
  posicao: Position;
  quantidade: number;
  x: number;
  y: number;
}

export interface Formation {
  nome: string;
  esquema: string;
  posicoes: FormationPosition[];
}

export const FORMATIONS: Record<string, Formation> = {
  '4-4-2': {
    nome: '4-4-2',
    esquema: '4-4-2',
    posicoes: [
      // Goleiro - bem no fundo
      { posicao: 'GOL', quantidade: 1, x: 50, y: 88 },
      // Defesa - linha bem separada (y: 70-72)
      { posicao: 'LAT', quantidade: 1, x: 8, y: 70 },    // Lateral esquerdo na ponta
      { posicao: 'ZAG', quantidade: 1, x: 32, y: 72 },   // Zagueiro esquerdo
      { posicao: 'ZAG', quantidade: 1, x: 68, y: 72 },   // Zagueiro direito
      { posicao: 'LAT', quantidade: 1, x: 92, y: 70 },   // Lateral direito na ponta
      // Meio-campo - linha separada (y: 45-50)
      { posicao: 'MEI', quantidade: 1, x: 10, y: 48 },   // Meia esquerdo
      { posicao: 'MEI', quantidade: 1, x: 35, y: 50 },   // Volante esquerdo
      { posicao: 'MEI', quantidade: 1, x: 65, y: 50 },   // Volante direito
      { posicao: 'MEI', quantidade: 1, x: 90, y: 48 },   // Meia direito
      // Ataque - dupla na frente (y: 22-25)
      { posicao: 'ATA', quantidade: 1, x: 35, y: 25 },   // Atacante esquerdo
      { posicao: 'ATA', quantidade: 1, x: 65, y: 25 },   // Atacante direito
      // Técnico - área técnica
      { posicao: 'TEC', quantidade: 1, x: 92, y: 92 },
    ],
  },
  '3-5-2': {
    nome: '3-5-2',
    esquema: '3-5-2',
    posicoes: [
      // Goleiro
      { posicao: 'GOL', quantidade: 1, x: 50, y: 88 },
      // Defesa (3 zagueiros bem espaçados)
      { posicao: 'ZAG', quantidade: 1, x: 22, y: 72 },
      { posicao: 'ZAG', quantidade: 1, x: 50, y: 74 },
      { posicao: 'ZAG', quantidade: 1, x: 78, y: 72 },
      // Meio-campo (5: alas bem nas pontas)
      { posicao: 'LAT', quantidade: 1, x: 5, y: 50 },    // Ala esquerdo ponta
      { posicao: 'MEI', quantidade: 1, x: 28, y: 48 },   // Volante esquerdo
      { posicao: 'MEI', quantidade: 1, x: 50, y: 45 },   // Meia central
      { posicao: 'MEI', quantidade: 1, x: 72, y: 48 },   // Volante direito
      { posicao: 'LAT', quantidade: 1, x: 95, y: 50 },   // Ala direito ponta
      // Ataque (dupla)
      { posicao: 'ATA', quantidade: 1, x: 35, y: 22 },
      { posicao: 'ATA', quantidade: 1, x: 65, y: 22 },
      // Técnico
      { posicao: 'TEC', quantidade: 1, x: 92, y: 92 },
    ],
  },
  '4-3-3': {
    nome: '4-3-3',
    esquema: '4-3-3',
    posicoes: [
      // Goleiro
      { posicao: 'GOL', quantidade: 1, x: 50, y: 88 },
      // Defesa (laterais bem nas pontas)
      { posicao: 'LAT', quantidade: 1, x: 8, y: 70 },
      { posicao: 'ZAG', quantidade: 1, x: 32, y: 72 },
      { posicao: 'ZAG', quantidade: 1, x: 68, y: 72 },
      { posicao: 'LAT', quantidade: 1, x: 92, y: 70 },
      // Meio-campo (triângulo)
      { posicao: 'MEI', quantidade: 1, x: 30, y: 50 },   // Volante esquerdo
      { posicao: 'MEI', quantidade: 1, x: 50, y: 42 },   // Meia central avançado
      { posicao: 'MEI', quantidade: 1, x: 70, y: 50 },   // Volante direito
      // Ataque (trio bem aberto)
      { posicao: 'ATA', quantidade: 1, x: 15, y: 20 },   // Ponta esquerda
      { posicao: 'ATA', quantidade: 1, x: 50, y: 15 },   // Centroavante
      { posicao: 'ATA', quantidade: 1, x: 85, y: 20 },   // Ponta direita
      // Técnico
      { posicao: 'TEC', quantidade: 1, x: 92, y: 92 },
    ],
  },
  '4-5-1': {
    nome: '4-5-1',
    esquema: '4-5-1',
    posicoes: [
      // Goleiro
      { posicao: 'GOL', quantidade: 1, x: 50, y: 88 },
      // Defesa
      { posicao: 'LAT', quantidade: 1, x: 8, y: 70 },
      { posicao: 'ZAG', quantidade: 1, x: 32, y: 72 },
      { posicao: 'ZAG', quantidade: 1, x: 68, y: 72 },
      { posicao: 'LAT', quantidade: 1, x: 92, y: 70 },
      // Meio-campo (5 bem distribuídos)
      { posicao: 'MEI', quantidade: 1, x: 10, y: 48 },
      { posicao: 'MEI', quantidade: 1, x: 30, y: 52 },
      { posicao: 'MEI', quantidade: 1, x: 50, y: 42 },   // Meia central avançado
      { posicao: 'MEI', quantidade: 1, x: 70, y: 52 },
      { posicao: 'MEI', quantidade: 1, x: 90, y: 48 },
      // Ataque (1 centroavante)
      { posicao: 'ATA', quantidade: 1, x: 50, y: 18 },
      // Técnico
      { posicao: 'TEC', quantidade: 1, x: 92, y: 92 },
    ],
  },
  '3-4-3': {
    nome: '3-4-3',
    esquema: '3-4-3',
    posicoes: [
      // Goleiro
      { posicao: 'GOL', quantidade: 1, x: 50, y: 88 },
      // Defesa (3 zagueiros)
      { posicao: 'ZAG', quantidade: 1, x: 22, y: 72 },
      { posicao: 'ZAG', quantidade: 1, x: 50, y: 74 },
      { posicao: 'ZAG', quantidade: 1, x: 78, y: 72 },
      // Meio-campo (4 com alas bem abertos)
      { posicao: 'LAT', quantidade: 1, x: 8, y: 50 },    // Ala esquerdo
      { posicao: 'MEI', quantidade: 1, x: 35, y: 48 },
      { posicao: 'MEI', quantidade: 1, x: 65, y: 48 },
      { posicao: 'LAT', quantidade: 1, x: 92, y: 50 },   // Ala direito
      // Ataque (trio bem aberto)
      { posicao: 'ATA', quantidade: 1, x: 18, y: 20 },
      { posicao: 'ATA', quantidade: 1, x: 50, y: 15 },
      { posicao: 'ATA', quantidade: 1, x: 82, y: 20 },
      // Técnico
      { posicao: 'TEC', quantidade: 1, x: 92, y: 92 },
    ],
  },
};

export const POSITION_COLORS: Record<Position, string> = {
  GOL: 'pos-gol',
  ZAG: 'pos-zag',
  LAT: 'pos-lat',
  MEI: 'pos-mei',
  ATA: 'pos-ata',
  TEC: 'pos-tec',
};

export const POSITION_NAMES: Record<Position, string> = {
  GOL: 'Goleiro',
  ZAG: 'Zagueiro',
  LAT: 'Lateral',
  MEI: 'Meia',
  ATA: 'Atacante',
  TEC: 'Técnico',
};
