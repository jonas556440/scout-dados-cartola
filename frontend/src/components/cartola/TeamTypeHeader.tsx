import { cn } from "@/lib/utils";
import { TrendingUp, Zap } from "lucide-react";

interface TeamTypeHeaderProps {
  tipo: 'valorizacao' | 'pontuacao';
  className?: string;
}

export function TeamTypeHeader({ tipo, className }: TeamTypeHeaderProps) {
  const isVal = tipo === 'valorizacao';

  return (
    <div className={cn("rounded-xl p-4 mb-4 border transition-all", className,
      isVal
        ? "bg-green-500/5 border-green-500/20 hover:border-green-500/40"
        : "bg-blue-500/5 border-blue-500/20 hover:border-blue-500/40"
    )}>
      <div className="flex items-center gap-3">
        <div className={cn(
          "p-2.5 rounded-xl shadow-lg",
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
            {isVal ? '💰 Time Valorização' : '⚡ Time Pontuação'}
          </h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            {isVal
              ? 'Jogadores baratos (C$3-6) com potencial de subir de preço'
              : 'Jogadores com maior chance de pontuar bem na rodada'
            }
          </p>
        </div>
      </div>
    </div>
  );
}
