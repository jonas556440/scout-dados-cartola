import { cn } from "@/lib/utils";
import type { Patrimony } from "@/types/cartola";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from "recharts";
import { motion } from "framer-motion";
import { TrendingUp, Wallet, Target } from "lucide-react";

interface PatrimonyChartProps {
  data: Patrimony[];
  className?: string;
}

export function PatrimonyChart({ data, className }: PatrimonyChartProps) {
  const chartData = data.map(p => ({
    rodada: `R${p.rodada}`,
    cartoletas: p.cartoletas,
    pontuacao: p.pontuacaoTotal,
    variacao: p.variacao,
  }));

  // Se só tem 1 rodada, adicionar ponto inicial para visualização
  if (chartData.length === 1) {
    chartData.unshift({
      rodada: 'Início',
      cartoletas: 100,
      pontuacao: 0,
      variacao: 0,
    });
  }

  const ultimoPatrimonio = data[data.length - 1];
  const primeiroPatrimonio = data[0];
  const variacaoTotal = (ultimoPatrimonio && typeof ultimoPatrimonio.cartoletas === 'number')
    ? ((ultimoPatrimonio.cartoletas - 100) / 100 * 100).toFixed(1)
    : '0.0';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn("chart-container", className)}
    >
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="font-display text-lg font-bold">Evolução do Patrimônio</h3>
          <p className="text-sm text-muted-foreground">Acompanhe seu progresso ao longo das rodadas</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-primary" />
            <span className="text-xs text-muted-foreground">Cartoletas</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-secondary" />
            <span className="text-xs text-muted-foreground">Pontuação</span>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="flex items-center gap-3 p-3 bg-muted/30 rounded-lg">
          <div className="p-2 bg-primary/20 rounded-lg">
            <Wallet className="w-4 h-4 text-primary" />
          </div>
          <div>
            <div className="text-lg font-bold text-primary">
              C${(ultimoPatrimonio?.cartoletas ?? 100).toFixed(1)}
            </div>
            <div className="text-xs text-muted-foreground">Patrimônio Atual</div>
          </div>
        </div>
        
        <div className="flex items-center gap-3 p-3 bg-muted/30 rounded-lg">
          <div className="p-2 bg-secondary/20 rounded-lg">
            <Target className="w-4 h-4 text-secondary" />
          </div>
          <div>
            <div className="text-lg font-bold text-secondary">
              {(ultimoPatrimonio?.pontuacaoTotal ?? 0).toFixed(1)}
            </div>
            <div className="text-xs text-muted-foreground">Pontuação Total</div>
          </div>
        </div>
        
        <div className="flex items-center gap-3 p-3 bg-muted/30 rounded-lg">
          <div className="p-2 bg-success/20 rounded-lg">
            <TrendingUp className="w-4 h-4 text-success" />
          </div>
          <div>
            <div className={cn(
              "text-lg font-bold",
              Number(variacaoTotal) >= 0 ? "text-success" : "text-destructive"
            )}>
              {Number(variacaoTotal) >= 0 ? '+' : ''}{variacaoTotal}%
            </div>
            <div className="text-xs text-muted-foreground">Variação Total</div>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="colorCartoletas" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="hsl(142, 76%, 45%)" stopOpacity={0.3} />
                <stop offset="95%" stopColor="hsl(142, 76%, 45%)" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorPontuacao" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="hsl(45, 93%, 58%)" stopOpacity={0.3} />
                <stop offset="95%" stopColor="hsl(45, 93%, 58%)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 14%, 18%)" />
            <XAxis 
              dataKey="rodada" 
              stroke="hsl(215, 20%, 55%)" 
              fontSize={12}
              tickLine={false}
            />
            <YAxis 
              stroke="hsl(215, 20%, 55%)" 
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'hsl(220, 18%, 12%)',
                border: '1px solid hsl(220, 14%, 18%)',
                borderRadius: '8px',
                boxShadow: '0 4px 24px -4px hsl(0 0% 0% / 0.4)',
              }}
              labelStyle={{ color: 'hsl(210, 40%, 98%)' }}
            />
            <Area
              type="monotone"
              dataKey="cartoletas"
              stroke="hsl(142, 76%, 45%)"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorCartoletas)"
              name="Cartoletas"
            />
            <Area
              type="monotone"
              dataKey="pontuacao"
              stroke="hsl(45, 93%, 58%)"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorPontuacao)"
              name="Pontuação"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}
