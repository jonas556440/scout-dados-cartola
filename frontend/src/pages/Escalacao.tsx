import { MainLayout } from "@/components/layout/MainLayout";
import { FormationDisplay } from "@/components/cartola/FormationDisplay";
import { PlayerCard } from "@/components/cartola/PlayerCard";
import { useEscalacao, useAtletas, useDashboard, useGerarEscalacao, useSalvarTime } from "@/hooks/useCartolaApi";
import { motion } from "framer-motion";
import { useState } from "react";
import { Loader2, AlertCircle, Check } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { useToast } from "@/hooks/use-toast";
import { 
  Users, 
  RefreshCw, 
  Save, 
  Search,
  Star,
  TrendingUp,
  Zap,
} from "lucide-react";
import type { Player, Position } from "@/types/cartola";
import { cn } from "@/lib/utils";
import { SEO } from "@/components/SEO";

const POSITIONS: Position[] = ['GOL', 'ZAG', 'LAT', 'MEI', 'ATA', 'TEC'];
const FORMATIONS = ['4-4-2', '3-5-2', '4-3-3', '4-5-1', '3-4-3'];

const Escalacao = () => {
  const [tipoTime, setTipoTime] = useState<'valorizacao' | 'pontuacao'>('valorizacao');
  const [esquema, setEsquema] = useState('4-4-2');
  const [filtroPos, setFiltroPos] = useState<Position | 'TODOS'>('TODOS');
  const [busca, setBusca] = useState('');
  const [selectedPlayer, setSelectedPlayer] = useState<Player | null>(null);
  const [timeSalvo, setTimeSalvo] = useState(false);
  const { toast } = useToast();

  // Obter orçamento atual
  const { data: dashboardData } = useDashboard();
  const orcamento = dashboardData?.patrimonio ?? 100;

  const { data: escalacaoData, isLoading: loadingEscalacao, refetch } = useEscalacao(esquema, orcamento);
  const { data: atletas, isLoading: loadingAtletas } = useAtletas();
  const gerarEscalacao = useGerarEscalacao();
  const salvarTimeMutation = useSalvarTime();

  const teamData = tipoTime === 'valorizacao' ? escalacaoData?.timeValorizacao : escalacaoData?.timePontuacao;

  const isVal = tipoTime === 'valorizacao';

  // Função para regenerar time
  const handleRegenerar = async () => {
    try {
      await gerarEscalacao.mutateAsync({ esquema, cartoletas: orcamento });
      toast({
        title: "Time regenerado!",
        description: `Nova escalação ${esquema} gerada com sucesso.`,
      });
      setTimeSalvo(false);
    } catch (error) {
      toast({
        title: "Erro ao regenerar",
        description: "Não foi possível gerar nova escalação. Tente novamente.",
        variant: "destructive",
      });
    }
  };

  // Função para salvar time (backend + localStorage)
  const handleSalvar = async () => {
    if (!teamData) return;
    
    // Salvar no localStorage como backup
    const timeSalvar = {
      tipo: tipoTime,
      esquema,
      jogadores: teamData.titulares,
      capitao: teamData.capitao,
      dataSalvo: new Date().toISOString(),
    };
    localStorage.setItem(`cartola_time_${tipoTime}`, JSON.stringify(timeSalvar));
    
    // Salvar no backend
    try {
      await salvarTimeMutation.mutateAsync({
        tipo: tipoTime,
        rodada: escalacaoData?.rodada || 1,
        titulares_ids: teamData.titulares.map((j: any) => j.id),
        capitao_id: teamData.capitao?.id || teamData.titulares[0]?.id,
        esquema,
        cartoletas: orcamento,
        pontuacaoEsperada: teamData.pontuacaoEsperada || teamData.pontuacaoPrevista || 0,
      });
      setTimeSalvo(true);
      toast({
        title: "Time salvo!",
        description: `Time ${isVal ? 'Valorização' : 'Pontuação'} salvo no histórico.`,
      });
    } catch {
      // Se falhar no backend, pelo menos salvou no localStorage
      setTimeSalvo(true);
      toast({
        title: "Salvo localmente",
        description: "Time salvo localmente. Sincronização com servidor pendente.",
        variant: "destructive",
      });
    }
  };

  // Filtrar jogadores
  const jogadoresFiltrados = (atletas || []).filter(player => {
    const matchPos = filtroPos === 'TODOS' || player.posicao === filtroPos;
    const matchBusca = player.apelido.toLowerCase().includes(busca.toLowerCase()) ||
                       player.clubeAbrev.toLowerCase().includes(busca.toLowerCase());
    return matchPos && matchBusca;
  }).sort((a, b) => (b.potencial || 0) - (a.potencial || 0));

  // Verificar se está carregando ou se não há dados
  if (loadingEscalacao) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-[60vh]">
          <div className="text-center">
            <RefreshCw className="w-12 h-12 animate-spin mx-auto mb-4 text-primary" />
            <p className="text-lg text-muted-foreground">Gerando escalação...</p>
          </div>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <SEO title="Escalação Inteligente" description="Monte sua escalação ideal para o Cartola FC 2026. Otimização por valorização ou pontuação com análise estatística." path="/escalacao" />
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="font-display text-3xl md:text-4xl font-bold">
              Escalação
            </h1>
            <p className="text-muted-foreground mt-1">
              Monte seu time ideal para a rodada
            </p>
          </div>
          
          <div className="flex items-center gap-3">
            <Select value={esquema} onValueChange={setEsquema}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="Esquema" />
              </SelectTrigger>
              <SelectContent>
                {FORMATIONS.map(f => (
                  <SelectItem key={f} value={f}>{f}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            <Button 
              variant="outline" 
              className="gap-2"
              onClick={handleRegenerar}
              disabled={gerarEscalacao.isPending}
            >
              <RefreshCw className={cn("w-4 h-4", gerarEscalacao.isPending && "animate-spin")} />
              {gerarEscalacao.isPending ? 'Gerando...' : 'Regenerar'}
            </Button>
            
            <Button 
              className={cn(
                "gap-2 text-white",
                isVal ? "valorizacao-gradient" : "pontuacao-gradient"
              )}
              onClick={handleSalvar}
              disabled={!teamData || timeSalvo}
            >
              {timeSalvo ? <Check className="w-4 h-4" /> : <Save className="w-4 h-4" />}
              {timeSalvo ? 'Salvo!' : 'Salvar'}
            </Button>
          </div>
        </div>
      </motion.div>

      {/* Strategy Selector - Cards visuais */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
        <button
          onClick={() => { setTipoTime('valorizacao'); setTimeSalvo(false); }}
          className={cn(
            "rounded-xl p-4 text-left transition-all border-2",
            tipoTime === 'valorizacao'
              ? "bg-green-500/10 border-green-500/50 shadow-lg shadow-green-500/10"
              : "bg-card/50 border-border/50 hover:border-green-500/30 opacity-60 hover:opacity-100"
          )}
        >
          <div className="flex items-center gap-3">
            <div className={cn(
              "p-2.5 rounded-xl transition-all",
              tipoTime === 'valorizacao'
                ? "bg-gradient-to-br from-green-500 to-emerald-600 shadow-lg"
                : "bg-green-500/20"
            )}>
              <TrendingUp className={cn("w-5 h-5", tipoTime === 'valorizacao' ? "text-white" : "text-green-400")} />
            </div>
            <div>
              <h3 className={cn(
                "font-display font-bold text-base",
                tipoTime === 'valorizacao' ? "text-green-400" : "text-muted-foreground"
              )}>
                💰 Time Valorização
              </h3>
              <p className="text-xs text-muted-foreground mt-0.5">
                Jogadores baratos (C$3-6) que vão subir de preço
              </p>
            </div>
          </div>
        </button>

        <button
          onClick={() => { setTipoTime('pontuacao'); setTimeSalvo(false); }}
          className={cn(
            "rounded-xl p-4 text-left transition-all border-2",
            tipoTime === 'pontuacao'
              ? "bg-blue-500/10 border-blue-500/50 shadow-lg shadow-blue-500/10"
              : "bg-card/50 border-border/50 hover:border-blue-500/30 opacity-60 hover:opacity-100"
          )}
        >
          <div className="flex items-center gap-3">
            <div className={cn(
              "p-2.5 rounded-xl transition-all",
              tipoTime === 'pontuacao'
                ? "bg-gradient-to-br from-blue-500 to-indigo-600 shadow-lg"
                : "bg-blue-500/20"
            )}>
              <Zap className={cn("w-5 h-5", tipoTime === 'pontuacao' ? "text-white" : "text-blue-400")} />
            </div>
            <div>
              <h3 className={cn(
                "font-display font-bold text-base",
                tipoTime === 'pontuacao' ? "text-blue-400" : "text-muted-foreground"
              )}>
                ⚡ Time Pontuação
              </h3>
              <p className="text-xs text-muted-foreground mt-0.5">
                Jogadores com maior chance de pontuar na rodada
              </p>
            </div>
          </div>
        </button>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Time */}
        <div className="lg:col-span-2">
          <FormationDisplay 
            team={{...teamData, esquema}} 
            onPlayerClick={setSelectedPlayer}
          />
        </div>

        {/* Player Selection */}
        <div className="glass-card p-4 h-fit max-h-[800px] overflow-hidden flex flex-col">
          <div className="flex items-center gap-2 mb-4">
            <Users className="w-5 h-5 text-primary" />
            <h3 className="font-display text-lg font-bold">Mercado</h3>
          </div>

          {/* Search & Filter */}
          <div className="space-y-3 mb-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Buscar jogador..."
                value={busca}
                onChange={(e) => setBusca(e.target.value)}
                className="pl-9"
              />
            </div>
            
            <div className="flex flex-wrap gap-2">
              <Button
                size="sm"
                variant={filtroPos === 'TODOS' ? 'default' : 'outline'}
                onClick={() => setFiltroPos('TODOS')}
                className="text-xs"
              >
                Todos
              </Button>
              {POSITIONS.map(pos => (
                <Button
                  key={pos}
                  size="sm"
                  variant={filtroPos === pos ? 'default' : 'outline'}
                  onClick={() => setFiltroPos(pos)}
                  className="text-xs px-2"
                >
                  {pos}
                </Button>
              ))}
            </div>
          </div>

          {/* Players List */}
          <div className="flex-1 overflow-y-auto space-y-2 pr-2">
            {jogadoresFiltrados.map((player) => {
              const isInTeam = teamData.titulares.some(p => p.id === player.id) ||
                               teamData.reservas.some(p => p.id === player.id);
              const isCaptain = teamData.capitao?.id === player.id;
              
              return (
                <PlayerCard
                  key={player.id}
                  player={player}
                  compact
                  isSelected={isInTeam}
                  isCaptain={isCaptain}
                  onClick={() => setSelectedPlayer(player)}
                />
              );
            })}
          </div>
        </div>
      </div>

      {/* Player Detail Modal */}
      {selectedPlayer && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={() => setSelectedPlayer(null)}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="glass-card max-w-md w-full"
            onClick={(e) => e.stopPropagation()}
          >
            <PlayerCard player={selectedPlayer} showStats />
            <div className="p-4 border-t border-border/50 flex gap-2">
              <Button 
                variant="outline" 
                className="flex-1"
                onClick={() => setSelectedPlayer(null)}
              >
                Fechar
              </Button>
              <Button className="flex-1 gap-2 hero-gradient text-primary-foreground">
                <Star className="w-4 h-4" />
                Capitão
              </Button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </MainLayout>
  );
};

export default Escalacao;
