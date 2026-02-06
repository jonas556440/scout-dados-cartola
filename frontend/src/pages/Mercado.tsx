import { MainLayout } from "@/components/layout/MainLayout";
import { PlayerCard } from "@/components/cartola/PlayerCard";
import { PositionBadge } from "@/components/cartola/PositionBadge";
import { useAtletas } from "@/hooks/useCartolaApi";
import { motion } from "framer-motion";
import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { 
  Search, 
  TrendingUp, 
  TrendingDown,
  Filter,
  ArrowUpDown,
  Zap,
  DollarSign,
  Loader2,
  AlertCircle,
} from "lucide-react";
import type { Player, Position } from "@/types/cartola";
import { cn } from "@/lib/utils";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

const POSITIONS: Position[] = ['GOL', 'ZAG', 'LAT', 'MEI', 'ATA', 'TEC'];

type SortField = 'preco' | 'media' | 'potencial' | 'tendencia';
type SortOrder = 'asc' | 'desc';

const Mercado = () => {
  const [busca, setBusca] = useState('');
  const [filtroPos, setFiltroPos] = useState<Position | 'TODOS'>('TODOS');
  const [sortField, setSortField] = useState<SortField>('potencial');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [precoMin, setPrecoMin] = useState('');
  const [precoMax, setPrecoMax] = useState('');

  // Filtrar e ordenar jogadores
  const { data: atletas, isLoading, error } = useAtletas({ limite: 500 });

  const jogadoresFiltrados = (atletas || [])
    .filter(player => {
      const matchPos = filtroPos === 'TODOS' || player.posicao === filtroPos;
      const matchBusca = player.apelido.toLowerCase().includes(busca.toLowerCase()) ||
                         player.clubeAbrev.toLowerCase().includes(busca.toLowerCase()) ||
                         player.clubeNome.toLowerCase().includes(busca.toLowerCase());
      const matchPrecoMin = !precoMin || player.preco >= parseFloat(precoMin);
      const matchPrecoMax = !precoMax || player.preco <= parseFloat(precoMax);
      return matchPos && matchBusca && matchPrecoMin && matchPrecoMax && player.status === 'provavel';
    })
    .sort((a, b) => {
      let aVal = a[sortField] || 0;
      let bVal = b[sortField] || 0;
      return sortOrder === 'desc' ? bVal - aVal : aVal - bVal;
    });

  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  return (
    <MainLayout>
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="font-display text-3xl md:text-4xl font-bold">
          Mercado
        </h1>
        <p className="text-muted-foreground mt-1">
          {jogadoresFiltrados.length} atletas disponíveis
        </p>
      </motion.div>

      {/* Filters */}
      <div className="glass-card p-4 mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Buscar jogador ou time..."
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
              className="pl-9"
            />
          </div>

          {/* Position Filter */}
          <div className="flex flex-wrap gap-2">
            <Button
              size="sm"
              variant={filtroPos === 'TODOS' ? 'default' : 'outline'}
              onClick={() => setFiltroPos('TODOS')}
            >
              Todos
            </Button>
            {POSITIONS.map(pos => (
              <Button
                key={pos}
                size="sm"
                variant={filtroPos === pos ? 'default' : 'outline'}
                onClick={() => setFiltroPos(pos)}
              >
                {pos}
              </Button>
            ))}
          </div>

          {/* Price Filter */}
          <div className="flex items-center gap-2">
            <DollarSign className="w-4 h-4 text-muted-foreground" />
            <Input
              type="number"
              placeholder="Min"
              value={precoMin}
              onChange={(e) => setPrecoMin(e.target.value)}
              className="w-20"
            />
            <span className="text-muted-foreground">-</span>
            <Input
              type="number"
              placeholder="Max"
              value={precoMax}
              onChange={(e) => setPrecoMax(e.target.value)}
              className="w-20"
            />
          </div>
        </div>

        {/* Sort Options */}
        <div className="flex gap-2 mt-4 pt-4 border-t border-border/50">
          <span className="text-sm text-muted-foreground">Ordenar por:</span>
          {[
            { field: 'potencial' as SortField, label: 'Potencial', icon: Zap },
            { field: 'preco' as SortField, label: 'Preço', icon: DollarSign },
            { field: 'media' as SortField, label: 'Média', icon: TrendingUp },
            { field: 'tendencia' as SortField, label: 'Tendência', icon: TrendingUp },
          ].map(({ field, label, icon: Icon }) => (
            <Button
              key={field}
              size="sm"
              variant={sortField === field ? 'default' : 'ghost'}
              onClick={() => toggleSort(field)}
              className="gap-1"
            >
              <Icon className="w-3 h-3" />
              {label}
              {sortField === field && (
                sortOrder === 'desc' ? <TrendingDown className="w-3 h-3" /> : <TrendingUp className="w-3 h-3" />
              )}
            </Button>
          ))}
        </div>
      </div>

      {/* Players Table */}
      <div className="glass-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="stats-table">
            <thead>
              <tr>
                <th>Jogador</th>
                <th className="text-center">Pos</th>
                <th className="text-center">Time</th>
                <th className="text-center">Preço</th>
                <th className="text-center">Média</th>
                <th className="text-center">Potencial</th>
                <th className="text-center">Tendência</th>
                <th className="text-center">Status</th>
              </tr>
            </thead>
            <tbody>
              {jogadoresFiltrados.map((player, index) => (
                <motion.tr
                  key={player.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.02 }}
                  className="hover:bg-muted/30 cursor-pointer"
                >
                  <td>
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center font-bold text-sm">
                        {player.apelido.substring(0, 2).toUpperCase()}
                      </div>
                      <div>
                        <div className="font-semibold">{player.apelido}</div>
                        <div className="text-xs text-muted-foreground">{player.nome}</div>
                      </div>
                    </div>
                  </td>
                  <td className="text-center">
                    <PositionBadge position={player.posicao} size="sm" />
                  </td>
                  <td className="text-center">
                    <div className="flex items-center justify-center gap-2">
                      {player.clubeEscudo ? (
                        <img 
                          src={player.clubeEscudo} 
                          alt={player.clubeAbrev} 
                          className="w-8 h-8 object-contain"
                          onError={(e) => {
                            (e.target as HTMLImageElement).style.display = 'none';
                          }}
                        />
                      ) : null}
                      <span className="font-semibold">{player.clubeAbrev}</span>
                    </div>
                  </td>
                  <td className="text-center">
                    <span className="font-bold text-primary">C${(player.preco ?? 0).toFixed(1)}</span>
                  </td>
                  <td className="text-center">
                    <div className="flex flex-col items-center">
                      <span className="font-bold">
                        {player.pontuacao !== undefined && player.pontuacao > 0 
                          ? player.pontuacao.toFixed(1) 
                          : (player.media ?? 0).toFixed(1)}
                      </span>
                      {player.pontuacao !== undefined && player.pontuacao > 0 && (
                        <span className="text-[10px] text-success font-bold">Última</span>
                      )}
                    </div>
                  </td>
                  <td className="text-center">
                    <div className="flex items-center justify-center gap-1">
                      <Zap className="w-3 h-3 text-secondary" />
                      <span className="font-semibold">{player.potencial || '-'}</span>
                    </div>
                  </td>
                  <td className="text-center">
                    <span className={cn(
                      "flex items-center justify-center gap-1 font-medium",
                      (player.tendencia || 0) > 0 ? "text-success" : "text-destructive"
                    )}>
                      {(player.tendencia || 0) > 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                      {(player.tendencia || 0) > 0 ? '+' : ''}{player.tendencia || 0}%
                    </span>
                  </td>
                  <td className="text-center">
                    <span className={cn(
                      "px-2 py-1 rounded-full text-xs font-semibold",
                      player.status === 'provavel' && "bg-success/20 text-success",
                      player.status === 'duvida' && "bg-warning/20 text-warning",
                      player.status === 'suspenso' && "bg-destructive/20 text-destructive",
                    )}>
                      {player.status === 'provavel' ? 'Provável' : 
                       player.status === 'duvida' ? 'Dúvida' : 'Suspenso'}
                    </span>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </MainLayout>
  );
};

export default Mercado;
