import { cn } from "@/lib/utils";
import type { Player, Team } from "@/types/cartola";
import { FORMATIONS, POSITION_COLORS } from "@/types/cartola";
import { PositionBadge } from "./PositionBadge";
import { motion } from "framer-motion";
import { Star, Users, Wallet, Target, TrendingUp, Zap } from "lucide-react";

interface FormationDisplayProps {
  team: Team;
  onPlayerClick?: (player: Player) => void;
  className?: string;
}

export function FormationDisplay({ team, onPlayerClick, className }: FormationDisplayProps) {
  // Verificar se o time está definido e tem dados
  if (!team || !team.titulares || team.titulares.length === 0) {
    return (
      <div className={cn("glass-card p-8 text-center", className)}>
        <p className="text-muted-foreground">Nenhum time disponível</p>
      </div>
    );
  }

  const formation = FORMATIONS[team.esquema] || FORMATIONS['4-4-2'];
  const isVal = team.tipo === 'valorizacao';
  
  // Mapear jogadores para posições
  const getPlayerForPosition = (positionIndex: number) => {
    const positionType = formation.posicoes[positionIndex].posicao;
    const playersOfPosition = team.titulares.filter(p => p.posicao === positionType);
    
    // Encontrar qual jogador dessa posição usar
    let count = 0;
    for (let i = 0; i <= positionIndex; i++) {
      if (formation.posicoes[i].posicao === positionType) {
        count++;
      }
    }
    
    return playersOfPosition[count - 1];
  };

  return (
    <div className={cn(
      "glass-card overflow-hidden transition-all",
      isVal ? "team-card-valorizacao" : "team-card-pontuacao",
      className
    )}>
      {/* Header com cor distinta */}
      <div className={cn(
        "flex items-center justify-between p-4 border-b",
        isVal
          ? "bg-green-500/5 border-green-500/20"
          : "bg-blue-500/5 border-blue-500/20"
      )}>
        <div className="flex items-center gap-3">
          <div className={cn(
            "p-2 rounded-lg",
            isVal
              ? "bg-gradient-to-br from-green-500 to-emerald-600"
              : "bg-gradient-to-br from-blue-500 to-indigo-600"
          )}>
            {isVal
              ? <TrendingUp className="w-5 h-5 text-white" />
              : <Zap className="w-5 h-5 text-white" />
            }
          </div>
          <div>
            <h3 className={cn(
              "font-display text-lg font-bold",
              isVal ? "text-green-400" : "text-blue-400"
            )}>
              {team.nome || (isVal ? 'Time Valorização' : 'Time Pontuação')}
            </h3>
            <div className="flex items-center gap-2 mt-0.5">
              <span className={cn(
                "px-2 py-0.5 text-[10px] font-bold rounded-full uppercase tracking-wider",
                isVal
                  ? "bg-green-500/20 text-green-400 border border-green-500/30"
                  : "bg-blue-500/20 text-blue-400 border border-blue-500/30"
              )}>
                {isVal ? '💰 Valorização' : '⚡ Pontuação'}
              </span>
              <span className="text-sm text-muted-foreground">{team.esquema}</span>
            </div>
          </div>
        </div>
        <div className="text-right">
          <div className={cn(
            "flex items-center gap-1 text-lg font-bold",
            isVal ? "text-green-400" : "text-blue-400"
          )}>
            <Wallet className="w-4 h-4" />
            C${(team.custoTotal ?? 0).toFixed(0)}
          </div>
          <div className="text-xs text-muted-foreground">
            Sobra: C${(team.cartoletas ?? 100 - (team.custoTotal ?? 0)).toFixed(0)}
          </div>
        </div>
      </div>

      {/* Campo */}
      <div className={cn(
        "relative aspect-[3/4] overflow-hidden",
        isVal
          ? "bg-gradient-to-b from-green-900/40 to-green-800/40"
          : "bg-gradient-to-b from-blue-900/30 to-slate-900/40"
      )}>
        {/* Linhas do campo */}
        <div className={cn(
          "absolute inset-2 sm:inset-4 border-2 rounded-lg",
          isVal ? "border-white/20" : "border-white/15"
        )}>
          {/* Linha do meio */}
          <div className={cn("absolute top-1/2 left-0 right-0 h-0.5", isVal ? "bg-white/20" : "bg-white/15")} />
          {/* Círculo central */}
          <div className={cn("absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-20 h-20 border-2 rounded-full", isVal ? "border-white/20" : "border-white/15")} />
          {/* Área do gol */}
          <div className={cn("absolute bottom-0 left-1/2 -translate-x-1/2 w-32 h-12 border-2 border-b-0", isVal ? "border-white/20" : "border-white/15")} />
          {/* Grande área */}
          <div className={cn("absolute bottom-0 left-1/2 -translate-x-1/2 w-48 h-24 border-2 border-b-0", isVal ? "border-white/20" : "border-white/15")} />
        </div>

        {/* Jogadores */}
        {formation.posicoes.map((pos, index) => {
          const player = getPlayerForPosition(index);
          if (!player) return null;
          
          const isCaptain = team.capitao?.id === player.id;
          
          return (
            <motion.div
              key={`${pos.posicao}-${index}`}
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: index * 0.05 }}
              onClick={() => onPlayerClick?.(player)}
              className="absolute cursor-pointer group"
              style={{
                left: `${pos.x}%`,
                top: `${pos.y}%`,
                transform: 'translate(-50%, -50%)',
              }}
            >
              <div className={cn(
                "relative flex flex-col items-center transition-transform group-hover:scale-110",
              )}>
                {/* Círculo do jogador com escudo dentro - tamanho reduzido */}
                <div className={cn(
                  "w-8 h-8 sm:w-10 sm:h-10 rounded-full flex items-center justify-center font-bold text-xs shadow-lg transition-all relative overflow-hidden",
                  POSITION_COLORS[pos.posicao],
                  isCaptain && "ring-2 ring-secondary ring-offset-1 ring-offset-green-900"
                )}>
                  {/* Escudo do time dentro da bolinha */}
                  {player.clubeEscudo ? (
                    <img 
                      src={player.clubeEscudo} 
                      alt={player.clubeAbrev} 
                      className="w-5 h-5 sm:w-6 sm:h-6 object-contain"
                      loading="lazy"
                    />
                  ) : (
                    <span>{player.apelido.substring(0, 2).toUpperCase()}</span>
                  )}
                </div>
                
                {/* Capitão */}
                {isCaptain && (
                  <div className="absolute -top-1 -right-1 w-4 h-4 bg-secondary rounded-full flex items-center justify-center shadow-md">
                    <Star className="w-2.5 h-2.5 text-secondary-foreground fill-current" />
                  </div>
                )}
                
                {/* Nome e preço - compacto */}
                <div className="mt-0.5 text-center max-w-[60px] sm:max-w-none">
                  <div className="text-[9px] sm:text-[10px] font-semibold text-white drop-shadow-lg whitespace-nowrap leading-tight overflow-hidden text-ellipsis">
                    {player.apelido.length > 7 ? player.apelido.substring(0, 7) + '.' : player.apelido}
                  </div>
                  <div className={cn(
                    "text-[8px] sm:text-[9px] font-bold leading-tight",
                    isVal ? "text-green-400" : "text-blue-400"
                  )}>
                    C${(player.preco ?? 0).toFixed(1)}
                  </div>
                  {/* Pontuação/Valorização atual - hidden on very small screens */}
                  {player.pontuacao !== undefined && player.pontuacao > 0 && (
                    <div className="hidden sm:block text-[9px] text-secondary font-bold leading-tight bg-secondary/20 px-1 rounded mt-0.5">
                      {(player.pontuacao ?? 0).toFixed(1)} pts
                    </div>
                  )}
                  {player.valorizacao !== undefined && player.valorizacao !== 0 && (
                    <div className={cn(
                      "hidden sm:block text-[9px] font-bold leading-tight px-1 rounded mt-0.5",
                      player.valorizacao > 0 
                        ? "text-green-400 bg-green-400/20" 
                        : "text-red-400 bg-red-400/20"
                    )}>
                      {player.valorizacao > 0 ? '+' : ''}{(player.valorizacao ?? 0).toFixed(1)}%
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Legenda Explicativa */}
      <div className="flex justify-center flex-wrap gap-x-4 gap-y-1 py-1.5 bg-background/40 backdrop-blur-sm border-t border-border/20 text-[10px] text-muted-foreground">
        <div className="flex items-center gap-1">
          <span className={cn("font-bold", isVal ? "text-green-400" : "text-blue-400")}>C$</span>
          <span>Preço</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="font-bold text-secondary">pts</span>
          <span>Última</span>
        </div>
        <div className="flex items-center gap-1">
          <span className={cn("font-bold", isVal ? "text-green-400" : "text-blue-400")}>%</span>
          <span>Valoriz.</span>
        </div>
      </div>

      {/* Reservas */}
      <div className="p-4 border-t border-border/50 bg-muted/20">
        <div className="flex items-center gap-2 mb-3">
          <Users className="w-4 h-4 text-muted-foreground" />
          <span className="text-sm font-semibold text-muted-foreground">Banco de Reservas</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {team.reservas.map((player) => (
            <div
              key={player.id}
              onClick={() => onPlayerClick?.(player)}
              className="flex items-center gap-2 px-2 py-1 bg-muted/50 rounded-lg cursor-pointer hover:bg-muted transition-colors"
            >
              <PositionBadge position={player.posicao} size="sm" />
              <span className="text-xs font-medium">{player.apelido}</span>
              <span className={cn("text-xs font-bold", isVal ? "text-green-400" : "text-blue-400")}>C${(player.preco ?? 0).toFixed(1)}</span>
              {/* Pontuação atual - NOVO */}
              {player.pontuacao !== undefined && player.pontuacao > 0 && (
                <span className="text-xs text-secondary font-bold bg-secondary/20 px-1 rounded">
                  {(player.pontuacao ?? 0).toFixed(1)}pts
                </span>
              )}
              {/* Valorização atual - NOVO */}
              {player.valorizacao !== undefined && player.valorizacao !== 0 && (
                <span className={cn(
                  "text-xs font-bold px-1 rounded",
                  player.valorizacao > 0 
                    ? "text-green-400 bg-green-400/20" 
                    : "text-red-400 bg-red-400/20"
                )}>
                  {player.valorizacao > 0 ? '+' : ''}{(player.valorizacao ?? 0).toFixed(1)}%
                </span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Stats */}
      <div className={cn(
        "grid grid-cols-3 divide-x divide-border/50 border-t",
        isVal ? "border-green-500/20" : "border-blue-500/20"
      )}>
        <div className="p-3 text-center">
          <div className={cn("text-lg font-bold", isVal ? "text-green-400" : "text-blue-400")}>C${(team.custoTotal ?? 0).toFixed(0)}</div>
          <div className="text-xs text-muted-foreground">Custo Total</div>
        </div>
        <div className="p-3 text-center">
          <div className="text-lg font-bold text-secondary">C${(team.cartoletas ?? 100 - (team.custoTotal ?? 0)).toFixed(0)}</div>
          <div className="text-xs text-muted-foreground">Em Caixa</div>
        </div>
        <div className="p-3 text-center">
          <div className="flex items-center justify-center gap-1 text-lg font-bold">
            <Target className="w-4 h-4 text-info" />
            {team.pontuacaoEsperada || '-'}
          </div>
          <div className="text-xs text-muted-foreground">Pts Esperados</div>
        </div>
      </div>
    </div>
  );
}
