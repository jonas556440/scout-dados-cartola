import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

type TermType = 'xg' | 'mpv' | 'monte-carlo' | '1x2' | 'over-under' | 'sg' | 'forma' | 'aproveitamento' | 'forca' | 'npxg';

const TERM_DEFINITIONS: Record<TermType, string> = {
  'xg': 'Expected Goals (xG): Métrica que estima a qualidade das chances criadas, baseada em dados estatísticos de milhares de jogos. Quanto maior o xG, melhores as chances.',
  'mpv': 'Maior Pontuação Valorizada (MPV): Jogadores que mais pontuam considerando o custo-benefício. Fórmula: pontos médios ÷ preço.',
  'monte-carlo': 'Simulação Monte Carlo: Algoritmo que simula o campeonato 1000 vezes com variações aleatórias realistas para calcular probabilidades precisas de título, Libertadores, Sulamericana e rebaixamento.',
  '1x2': 'Aposta 1X2: Probabilidade de vitória do mandante (1), empate (X) ou vitória do visitante (2). Formato tradicional de aposta esportiva.',
  'over-under': 'Over/Under: Probabilidade de o jogo ter mais (Over) ou menos (Under) que determinado número de gols. Ex: Over 2.5 = mais de 2.5 gols no jogo.',
  'sg': 'Saldo de Gols: Diferença entre gols marcados e gols sofridos. Critério de desempate no Brasileirão.',
  'forma': 'Forma Recente: Sequência dos últimos 5 jogos (V = Vitória, E = Empate, D = Derrota). Indica o momento atual do time.',
  'aproveitamento': 'Aproveitamento: Percentual de pontos conquistados em relação ao total possível. Fórmula: (pontos ÷ (jogos × 3)) × 100%.',
  'forca': 'Força do Time: Métrica de 0 a 100 calculada com base em desempenho, gols, defesa e histórico recente. Usada para prever confrontos.',
  'npxg': 'Non-Penalty xG (NPxG): Expected Goals excluindo pênaltis. Mostra a qualidade das chances criadas no jogo corrido, sem distorção dos pênaltis.'
};

interface TermTooltipProps {
  term: TermType;
  children: React.ReactNode;
  className?: string;
}

export function TermTooltip({ term, children, className }: TermTooltipProps) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span className={`border-b border-dotted border-muted-foreground/50 cursor-help ${className || ''}`}>
          {children}
        </span>
      </TooltipTrigger>
      <TooltipContent className="max-w-xs md:max-w-sm">
        <p className="text-sm leading-relaxed">{TERM_DEFINITIONS[term]}</p>
      </TooltipContent>
    </Tooltip>
  );
}

// Export para uso em outros componentes que precisam das definições
export { TERM_DEFINITIONS };
export type { TermType };
