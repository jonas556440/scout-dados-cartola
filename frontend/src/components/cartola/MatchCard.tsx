import { cn } from "@/lib/utils";
import type { Match } from "@/types/cartola";
import { motion } from "framer-motion";
import { MapPin, Calendar, ArrowRight, TrendingUp, Home, Plane, Activity } from "lucide-react";

interface MatchCardProps {
  match: Match;
  className?: string;
  showProbabilities?: boolean;
}

export function MatchCard({ match, className, showProbabilities = true }: MatchCardProps) {
  const mandanteFavorito = (match.probabilidadeMandante || 0) > (match.probabilidadeVisitante || 0);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn("glass-card overflow-hidden", className)}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-muted/30 border-b border-border/50">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Calendar className="w-3 h-3" />
          <span>{match.data} • {match.hora}</span>
        </div>
        <div className="flex items-center gap-1 text-xs text-muted-foreground">
          <MapPin className="w-3 h-3" />
          <span>{match.local}</span>
        </div>
      </div>

      {/* Teams */}
      <div className="p-4">
        <div className="flex items-center justify-between gap-4">
          {/* Mandante */}
          <div className={cn(
            "flex-1 text-center p-3 rounded-lg transition-all",
            mandanteFavorito ? "bg-primary/10 border border-primary/30" : "bg-muted/30"
          )}>
            <div className="flex items-center justify-center gap-1 text-xs text-muted-foreground mb-1">
              <Home className="w-3 h-3" />
              <span>Casa</span>
            </div>
            <div className="font-display text-xl font-bold">{match.mandante.abrev}</div>
            <div className="text-sm text-muted-foreground">{match.mandante.nome}</div>
            {match.aproveitamentoMandante && (
              <div className="flex items-center justify-center gap-1 mt-2 text-xs">
                <TrendingUp className="w-3 h-3 text-primary" />
                <span className="text-primary font-semibold">{match.aproveitamentoMandante}%</span>
              </div>
            )}
          </div>

          {/* VS / Placar Previsto */}
          <div className="flex flex-col items-center gap-1">
            {match.placarProvavel ? (
              <>
                <span className="text-xs text-muted-foreground">Previsão</span>
                <div className="text-2xl font-bold text-primary">{match.placarProvavel}</div>
                <span className="text-[10px] text-muted-foreground">{match.probabilidadePlacar?.toFixed(1)}%</span>
              </>
            ) : (
              <>
                <span className="text-xs text-muted-foreground">VS</span>
                <ArrowRight className="w-4 h-4 text-muted-foreground" />
              </>
            )}
          </div>

          {/* Visitante */}
          <div className={cn(
            "flex-1 text-center p-3 rounded-lg transition-all",
            !mandanteFavorito ? "bg-primary/10 border border-primary/30" : "bg-muted/30"
          )}>
            <div className="flex items-center justify-center gap-1 text-xs text-muted-foreground mb-1">
              <Plane className="w-3 h-3" />
              <span>Fora</span>
            </div>
            <div className="font-display text-xl font-bold">{match.visitante.abrev}</div>
            <div className="text-sm text-muted-foreground">{match.visitante.nome}</div>
            {match.aproveitamentoVisitante && (
              <div className="flex items-center justify-center gap-1 mt-2 text-xs">
                <TrendingUp className="w-3 h-3 text-primary" />
                <span className="text-primary font-semibold">{match.aproveitamentoVisitante}%</span>
              </div>
            )}
          </div>
        </div>

        {/* Expected Goals */}
        {match.xgMandante && match.xgVisitante && (
          <div className="mt-3 flex items-center justify-center gap-4 text-sm">
            <div className="flex items-center gap-1">
              <span className="text-muted-foreground text-xs">xG:</span>
              <span className="font-bold text-primary">{match.xgMandante}</span>
            </div>
            <span className="text-muted-foreground">vs</span>
            <div className="flex items-center gap-1">
              <span className="font-bold text-secondary">{match.xgVisitante}</span>
            </div>
          </div>
        )}

        {/* Mercado de Gols */}
        {match.over25 && match.btts && (
          <div className="mt-2 flex items-center justify-center gap-4 text-xs">
            <div className="px-2 py-1 rounded bg-muted/50">
              <span className="text-muted-foreground">+2.5 gols:</span>
              <span className="ml-1 font-semibold">{match.over25?.toFixed(0)}%</span>
            </div>
            <div className="px-2 py-1 rounded bg-muted/50">
              <span className="text-muted-foreground">Ambos marcam:</span>
              <span className="ml-1 font-semibold">{match.btts?.toFixed(0)}%</span>
            </div>
          </div>
        )}

        {/* Probabilidades */}
        {showProbabilities && match.probabilidadeMandante && (
          <div className="mt-4 pt-4 border-t border-border/50">
            <div className="text-xs text-muted-foreground text-center mb-2">Probabilidades</div>
            <div className="flex items-center h-6 rounded-full overflow-hidden bg-muted/30">
              <div
                className="h-full bg-primary flex items-center justify-center text-xs font-bold text-primary-foreground"
                style={{ width: `${match.probabilidadeMandante}%` }}
              >
                {match.probabilidadeMandante?.toFixed(1)}%
              </div>
              <div
                className="h-full bg-muted-foreground/50 flex items-center justify-center text-xs font-bold"
                style={{ width: `${match.probabilidadeEmpate}%` }}
              >
                {match.probabilidadeEmpate?.toFixed(1)}%
              </div>
              <div
                className="h-full bg-secondary flex items-center justify-center text-xs font-bold text-secondary-foreground"
                style={{ width: `${match.probabilidadeVisitante}%` }}
              >
                {match.probabilidadeVisitante?.toFixed(1)}%
              </div>
            </div>
            <div className="flex justify-between text-xs text-muted-foreground mt-1">
              <span>Mandante</span>
              <span>Empate</span>
              <span>Visitante</span>
            </div>
          </div>
        )}

        {/* Placares Alternativos + Confiança */}
        {match.topPlacares && match.topPlacares.length > 1 && (
          <div className="mt-3 pt-3 border-t border-border/50">
            <div className="flex items-center justify-between">
              <div className="flex gap-1.5 flex-wrap">
                {match.topPlacares.slice(1, 4).map((p, i) => (
                  <span key={i} className="text-[10px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground">
                    {p.placar} <span className="font-semibold">({p.probabilidade.toFixed(1)}%)</span>
                  </span>
                ))}
              </div>
              {match.confianca != null && (
                <div className="flex items-center gap-1.5 ml-2 shrink-0">
                  <Activity className="w-3 h-3 text-muted-foreground" />
                  <div className="w-12 h-1.5 bg-muted rounded-full overflow-hidden">
                    <div className="h-full bg-primary rounded-full" style={{ width: `${match.confianca}%` }} />
                  </div>
                  <span className="text-[10px] font-bold text-primary">{match.confianca.toFixed(0)}%</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
}
