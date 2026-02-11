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
  topPlacares?: TopPlacar[];
  confianca?: number;
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
      { posicao: 'LAT', quantidade: 1, x: 15, y: 70 },   // Lateral esquerdo na ponta
      { posicao: 'ZAG', quantidade: 1, x: 35, y: 72 },   // Zagueiro esquerdo
      { posicao: 'ZAG', quantidade: 1, x: 65, y: 72 },   // Zagueiro direito
      { posicao: 'LAT', quantidade: 1, x: 85, y: 70 },   // Lateral direito na ponta
      // Meio-campo - linha separada (y: 45-50)
      { posicao: 'MEI', quantidade: 1, x: 15, y: 48 },   // Meia esquerdo
      { posicao: 'MEI', quantidade: 1, x: 38, y: 50 },   // Volante esquerdo
      { posicao: 'MEI', quantidade: 1, x: 62, y: 50 },   // Volante direito
      { posicao: 'MEI', quantidade: 1, x: 85, y: 48 },   // Meia direito
      // Ataque - dupla na frente (y: 22-25)
      { posicao: 'ATA', quantidade: 1, x: 38, y: 25 },   // Atacante esquerdo
      { posicao: 'ATA', quantidade: 1, x: 62, y: 25 },   // Atacante direito
      // Técnico - área técnica
      { posicao: 'TEC', quantidade: 1, x: 85, y: 92 },
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
      { posicao: 'LAT', quantidade: 1, x: 15, y: 50 },   // Ala esquerdo ponta
      { posicao: 'MEI', quantidade: 1, x: 30, y: 48 },   // Volante esquerdo
      { posicao: 'MEI', quantidade: 1, x: 50, y: 45 },   // Meia central
      { posicao: 'MEI', quantidade: 1, x: 70, y: 48 },   // Volante direito
      { posicao: 'LAT', quantidade: 1, x: 85, y: 50 },   // Ala direito ponta
      // Ataque (dupla)
      { posicao: 'ATA', quantidade: 1, x: 38, y: 22 },
      { posicao: 'ATA', quantidade: 1, x: 62, y: 22 },
      // Técnico
      { posicao: 'TEC', quantidade: 1, x: 85, y: 92 },
    ],
  },
  '4-3-3': {
    nome: '4-3-3',
    esquema: '4-3-3',
    posicoes: [
      // Goleiro
      { posicao: 'GOL', quantidade: 1, x: 50, y: 88 },
      // Defesa (laterais bem nas pontas)
      { posicao: 'LAT', quantidade: 1, x: 15, y: 70 },
      { posicao: 'ZAG', quantidade: 1, x: 35, y: 72 },
      { posicao: 'ZAG', quantidade: 1, x: 65, y: 72 },
      { posicao: 'LAT', quantidade: 1, x: 85, y: 70 },
      // Meio-campo (triângulo)
      { posicao: 'MEI', quantidade: 1, x: 30, y: 50 },   // Volante esquerdo
      { posicao: 'MEI', quantidade: 1, x: 50, y: 42 },   // Meia central avançado
      { posicao: 'MEI', quantidade: 1, x: 70, y: 50 },   // Volante direito
      // Ataque (trio bem aberto)
      { posicao: 'ATA', quantidade: 1, x: 18, y: 20 },   // Ponta esquerda
      { posicao: 'ATA', quantidade: 1, x: 50, y: 15 },   // Centroavante
      { posicao: 'ATA', quantidade: 1, x: 82, y: 20 },   // Ponta direita
      // Técnico
      { posicao: 'TEC', quantidade: 1, x: 85, y: 92 },
    ],
  },
  '4-5-1': {
    nome: '4-5-1',
    esquema: '4-5-1',
    posicoes: [
      // Goleiro
      { posicao: 'GOL', quantidade: 1, x: 50, y: 88 },
      // Defesa
      { posicao: 'LAT', quantidade: 1, x: 15, y: 70 },
      { posicao: 'ZAG', quantidade: 1, x: 35, y: 72 },
      { posicao: 'ZAG', quantidade: 1, x: 65, y: 72 },
      { posicao: 'LAT', quantidade: 1, x: 85, y: 70 },
      // Meio-campo (5 bem distribuídos)
      { posicao: 'MEI', quantidade: 1, x: 15, y: 48 },
      { posicao: 'MEI', quantidade: 1, x: 32, y: 52 },
      { posicao: 'MEI', quantidade: 1, x: 50, y: 42 },   // Meia central avançado
      { posicao: 'MEI', quantidade: 1, x: 68, y: 52 },
      { posicao: 'MEI', quantidade: 1, x: 85, y: 48 },
      // Ataque (1 centroavante)
      { posicao: 'ATA', quantidade: 1, x: 50, y: 18 },
      // Técnico
      { posicao: 'TEC', quantidade: 1, x: 85, y: 92 },
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
      { posicao: 'LAT', quantidade: 1, x: 15, y: 50 },   // Ala esquerdo
      { posicao: 'MEI', quantidade: 1, x: 38, y: 48 },
      { posicao: 'MEI', quantidade: 1, x: 62, y: 48 },
      { posicao: 'LAT', quantidade: 1, x: 85, y: 50 },   // Ala direito
      // Ataque (trio bem aberto)
      { posicao: 'ATA', quantidade: 1, x: 18, y: 20 },
      { posicao: 'ATA', quantidade: 1, x: 50, y: 15 },
      { posicao: 'ATA', quantidade: 1, x: 82, y: 20 },
      // Técnico
      { posicao: 'TEC', quantidade: 1, x: 85, y: 92 },
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

// ========================================
// TIPOS PARA ENDPOINTS ÓRFÃOS (FASE 1)
// ========================================

// /api/previsoes/placares
export interface TopPlacar {
  placar: string;
  probabilidade: number;
}

export interface PrevisaoJogo {
  mandante: string;
  mandanteId: number;
  visitante: string;
  visitanteId: number;
  placarProvavel: string;
  probabilidadePlacar: number;
  xgMandante: number;
  xgVisitante: number;
  probVitoriaCasa: number;
  probEmpate: number;
  probVitoriaFora: number;
  topPlacares: TopPlacar[];
  over15: number;
  over25: number;
  over35: number;
  btts: number;
  confianca: number;
  local?: string;
  data?: string;
}

export interface PrevisaoRodadaResponse {
  rodada: number;
  previsoes: PrevisaoJogo[];
  erro?: string;
  total?: number;
}

// /api/previsoes/customizado (POST)
export interface PrevisaoCustomizadaRequest {
  mandante: string;
  visitante: string;
  forcaMandante?: number; // 0-100
  forcaVisitante?: number; // 0-100
}

export interface PrevisaoCustomizadaResponse {
  mandante: string;
  visitante: string;
  placarProvavel: string;
  probabilidadePlacar: number;
  xgMandante: number;
  xgVisitante: number;
  probVitoriaCasa: number;
  probEmpate: number;
  probVitoriaFora: number;
  topPlacares: TopPlacar[];
  over25: number;
  btts: number;
  confianca: number;
  metodologia: string;
  recursos: {
    historico_direto: string;
    desfalques: string;
    machine_learning: string;
  };
}

// /api/confrontos/analise
export interface TimeConfronto {
  clubeId: number;
  nome: string;
  abrev: string;
  adversario: string;
  local: 'casa' | 'fora';
  dificuldade: number; // 0-100
  chanceSg: number; // 0-100
  expectativaGols: number;
  scoreGeral: number; // 0-100
}

export interface ConfrontosAnaliseResponse {
  rodada: number;
  timesParaEscalar: TimeConfronto[];
  timesParaEvitar: TimeConfronto[];
}

// /api/noticias/{clube_abrev}
export interface NoticiaDestaque {
  titulo: string;
  url?: string;
  tipo: 'lesao' | 'suspensao' | 'duvida' | 'poupado' | 'recuperado';
  jogadores?: string[];
}

export interface NoticiasTimeResponse {
  clube: string;
  total_noticias: number;
  lesionados: string[];
  suspensos: string[];
  duvidas: string[];
  vai_poupar: string[];
  noticias_destaque: NoticiaDestaque[];
  ultima_atualizacao: string;
}

// /api/noticias/rodada/{rodada}
export interface DesfalqueClube {
  clube_id: number;
  clube_nome: string;
  clube_abrev: string;
  lesionados: string[];
  suspensos: string[];
  duvidas: string[];
  vai_poupar: string[];
  total_desfalques: number;
}

export interface NoticiasRodadaResponse {
  rodada: number;
  total_clubes: number;
  clubes: DesfalqueClube[];
  resumo: {
    total_lesionados: number;
    total_suspensos: number;
    total_duvidas: number;
    total_poupados: number;
  };
}

// /api/times/forca
export interface ForcaTime {
  id: number;
  nome: string;
  abrev: string;
  posicao: number;
  jogos: number;
  vitorias: number;
  empates: number;
  derrotas: number;
  golsPro: number;
  golsContra: number;
  saldoGols: number;
  pontosGanhos: number;
  aproveitamento: number;
  forcaCasa: number; // 0-100
  forcaFora: number; // 0-100
  forcaGeral: number; // 0-100
  forcaAtaque: number; // 0-100
  forcaDefesa: number; // 0-100
  mediaGolsPro: number;
  mediaGolsContra: number;
  formaRecente: string; // ex: "VVEVD"
}

export interface ForcaTimesResponse {
  rodada: number;
  times: ForcaTime[];
  metodologia: string;
}

// ============ Brasileirão ============

export interface ClassificacaoTime {
  id: number;
  nome: string;
  abrev: string;
  escudo?: string;
  posicao: number;
  pontos: number;
  jogos: number;
  vitorias: number;
  empates: number;
  derrotas: number;
  gols_pro: number;
  gols_contra: number;
  saldo_gols: number;
  aproveitamento: number;
  forma: string;
}

export interface SimulacaoTime {
  id: number;
  abrev: string;
  pontosMedio: number;
  pontosMin?: number;
  pontosMax?: number;
  probTitulo: number;
  probLibertadores: number;
  probSulamericana: number;
  probRebaixamento: number;
  posicaoMedia: number;
}

export interface PontosNecessarios {
  probabilidade: number;
  titulo: number;
  libertadores: number;
  sulamericana: number;
  permanencia: number;
}

export interface JogoProbabilidade {
  mandante: string;
  mandanteNome: string;
  visitante: string;
  visitanteNome: string;
  dataHora: string;
  local: string;
  realizado: boolean;
  placarMandante: number | null;
  placarVisitante: number | null;
  probVitoriaMandante: number | null;
  probEmpate: number | null;
  probVitoriaVisitante: number | null;
}

export interface ClassificacaoResponse {
  rodada: number;
  classificacao: ClassificacaoTime[];
  simulacao: SimulacaoTime[] | null;
  totalTimes: number;
  pontosNecessarios?: PontosNecessarios[];
  proximosJogos?: JogoProbabilidade[];
  jogosRealizados?: JogoProbabilidade[];
}

export interface PartidaRodada {
  mandanteId: number;
  mandante: string;
  mandanteNome: string;
  visitanteId: number;
  visitante: string;
  visitanteNome: string;
  placarMandante: number | null;
  placarVisitante: number | null;
  local: string;
  dataHora: string;
  realizado: boolean;
}

export interface PrevisaoRodadaDetalhe {
  mandante: string;
  visitante: string;
  placarPrevisto: string;
  placarReal: string | null;
  acertou: boolean | null;
  xgMandante: number;
  xgVisitante: number;
  confianca: number;
}

export interface RodadaDetalhadaResponse {
  rodada: number;
  rodadaAtual: number;
  partidas: PartidaRodada[];
  previsoes: PrevisaoRodadaDetalhe[];
  acuracia: number | null;
  totalPartidas: number;
}

export interface AcuraciaRodada {
  rodada: number;
  totalPartidas: number;
  acertos: number;
  acuracia: number;
}

export interface AcuraciaResponse {
  rodadaAtual: number;
  totalRodadas: number;
  totalJogos: number;
  totalAcertos: number;
  acuraciaGeral: number;
  rodadas: AcuraciaRodada[];
  metodologia: string;
}

// ============ Scouts ============

export interface ScoutJogador {
  id: number;
  apelido: string;
  clubeAbrev: string;
  clubeNome: string;
  pontuacao: number;
  scouts: Record<string, number>;
  gols: number;
  assistencias: number;
  saldoGols: number;
  finalizacoesTrave: number;
  desarmes: number;
}

export interface ScoutsDestaquesResponse {
  rodada: number | null;
  destaques: ScoutJogador[];
  artilheiros: ScoutJogador[];
  assistentes: ScoutJogador[];
  totalJogadores: number;
}

export interface ScoutDetalhadoResponse {
  id: number;
  nome: string;
  apelido: string;
  foto: string;
  posicao: string;
  posicaoId: number;
  clubeId: number;
  clubeAbrev: string;
  clubeNome: string;
  preco: number;
  media: number;
  pontosTotais: number;
  jogos: number;
  variacao: number;
  minimo: number;
  statusId: number;
  scoutsRodada: Record<string, number>;
  pontuacaoRodada: number | null;
  scoutsAcumulados: Record<string, number>;
}

export interface DesfalqueClubeFull {
  clubeId: number;
  clubeNome: string;
  clubeAbrev: string;
  lesionados: string[];
  suspensos: string[];
  duvidas: string[];
  totalDesfalques: number;
}

export interface DesfalquesResponse {
  totalClubes: number;
  clubes: DesfalqueClubeFull[];
  resumo: {
    totalLesionados: number;
    totalSuspensos: number;
    totalDuvidas: number;
    totalGeral: number;
  };
}
