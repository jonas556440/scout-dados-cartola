import { cn } from "@/lib/utils";
import type { Player } from "@/types/cartola";
import { PositionBadge } from "./PositionBadge";
import { TrendingUp, TrendingDown, Star, Zap } from "lucide-react";
import { motion } from "framer-motion";

interface PlayerCardProps {
  player: Player;
  isCaptain?: boolean;
  isSelected?: boolean;
  showStats?: boolean;
  onClick?: () => void;
  className?: string;
  compact?: boolean;
}

export function PlayerCard({
  player,
  isCaptain = false,
  isSelected = false,
  showStats = true,
  onClick,
  className,
  compact = false,
}: PlayerCardProps) {
  const tendenciaPositiva = (player.tendencia || 0) > 0;

  if (compact) {
    return (
      <motion.div
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={onClick}
        className={cn(
          "player-card p-3 flex items-center gap-3",
          isSelected && "border-primary glow-green",
          isCaptain && "border-secondary glow-gold",
          onClick && "cursor-pointer",
          className
        )}
      >
        <PositionBadge position={player.posicao} size="sm" />
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1">
            <span className="font-semibold text-sm truncate">{player.apelido}</span>
            {isCaptain && <Star className="w-3 h-3 text-secondary fill-secondary" />}
          </div>
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            {player.clubeEscudo && (
              <img 
                src={player.clubeEscudo} 
                alt={player.clubeAbrev} 
                className="w-5 h-5 object-contain"
              />
            )}
            <span>{player.clubeAbrev}</span>
          </div>
        </div>

        <div className="text-right space-y-0.5">
          <div className="text-sm font-bold text-primary">C${(player.preco ?? 0).toFixed(1)}</div>
          
          {/* Mostrar pontos ou média (Sempre mostrar algo para debug visual) */}
          <div className={cn(
            "flex items-center justify-end gap-1 text-xs font-bold",
            (player.pontuacao && player.pontuacao > 0) ? "text-success" : "text-primary/70"
          )}>
            <Zap className="w-3 h-3" />
            {(player.pontuacao && player.pontuacao > 0) 
              ? player.pontuacao.toFixed(1)
              : (player.media ? player.media.toFixed(1) : '0.0')
            }
            <span className="text-[10px] font-normal lowercase opacity-80">
              {(player.pontuacao && player.pontuacao > 0) ? 'pts' : 'méd'}
            </span>
          </div>
          
          {/* Mostrar variação se tiver */}
          {player.valorizacao !== undefined && player.valorizacao !== 0 && (
            <div className={cn(
              "flex items-center justify-end gap-1 text-xs font-medium",
              player.valorizacao > 0 ? "text-success" : "text-destructive"
            )}>
              {player.mpv_score !== undefined && player.valorizacao > 0 && (
                 <span className="bg-yellow-100 text-yellow-800 text-[9px] px-1 py-0 rounded border border-yellow-200 mr-1" title="MPV Score: Alta probabilidade">
                   🎯 MPV
                 </span>
              )}
              {player.valorizacao > 0 ? (
                <TrendingUp className="w-3 h-3" />
              ) : (
                <TrendingDown className="w-3 h-3" />
              )}
              {player.valorizacao > 0 ? '+' : ''}{player.valorizacao.toFixed(1)}%
            </div>
          )}
          
          {/* Se não tiver pontos nem valorização, mostrar potencial */}
          {!player.pontuacao && !player.valorizacao && player.potencial && (
            <div className="flex items-center justify-end gap-1 text-xs text-muted-foreground">
              <Zap className="w-3 h-3 text-secondary" />
              {player.potencial}
            </div>
          )}
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      whileHover={{ y: -4, scale: 1.01 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={cn(
        "player-card",
        isSelected && "border-primary glow-green",
        isCaptain && "border-secondary glow-gold",
        onClick && "cursor-pointer",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between p-4 pb-2">
        <div className="flex items-center gap-2">
          <PositionBadge position={player.posicao} />
          {isCaptain && (
            <span className="flex items-center gap-1 px-2 py-0.5 bg-secondary/20 text-secondary text-xs font-bold rounded-full">
              <Star className="w-3 h-3 fill-current" />
              CAP
            </span>
          )}
        </div>
        <div className="text-right">
          <div className="text-lg font-bold text-primary">C${(player.preco ?? 0).toFixed(1)}</div>
          {player.tendencia !== undefined && (
            <div className={cn(
              "flex items-center gap-1 text-xs font-medium",
              tendenciaPositiva ? "text-success" : "text-destructive"
            )}>
              {tendenciaPositiva ? (
                <TrendingUp className="w-3 h-3" />
              ) : (
                <TrendingDown className="w-3 h-3" />
              )}
              {tendenciaPositiva ? '+' : ''}{player.tendencia}%
            </div>
          )}
        </div>
      </div>

      {/* Player Info */}
      <div className="px-4 pb-2">
        <h3 className="font-display text-xl font-bold truncate">{player.apelido}</h3>
        <p className="text-sm text-muted-foreground">{player.clubeNome}</p>
      </div>

      {/* Stats */}
      {showStats && (
        <div className="grid grid-cols-3 gap-2 p-4 pt-2 border-t border-border/50">
          <div className="text-center">
            <div className={cn(
              "text-lg font-bold",
              player.pontuacao && player.pontuacao > 0 ? "text-success" : ""
            )}>
              {player.pontuacao !== undefined && player.pontuacao > 0 
                ? player.pontuacao.toFixed(1) 
                : (player.media ?? 0).toFixed(1)}
            </div>
            <div className="text-xs text-muted-foreground">
              {player.pontuacao !== undefined && player.pontuacao > 0 ? "Pontos" : "Média"}
            </div>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold">{player.jogos}</div>
            <div className="text-xs text-muted-foreground">Jogos</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold flex items-center justify-center gap-1">
              <Zap className="w-4 h-4 text-secondary" />
              {player.potencial || '-'}
            </div>
            <div className="text-xs text-muted-foreground">Potencial</div>
          </div>
        </div>
      )}

      {/* Status */}
      <div className={cn(
        "h-1",
        player.status === 'provavel' && "bg-success",
        player.status === 'duvida' && "bg-warning",
        player.status === 'suspenso' && "bg-destructive",
        player.status === 'contundido' && "bg-destructive",
        player.status === 'nulo' && "bg-muted",
      )} />
    </motion.div>
  );
}
