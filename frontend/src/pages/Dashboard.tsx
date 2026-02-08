import { MainLayout } from "@/components/layout/MainLayout";
import { StatCard } from "@/components/cartola/StatCard";
import { MatchCard } from "@/components/cartola/MatchCard";
import { PlayerCard } from "@/components/cartola/PlayerCard";
import { FormationDisplay } from "@/components/cartola/FormationDisplay";
import { useDashboard, useEscalacao } from "@/hooks/useCartolaApi";
import { motion } from "framer-motion";
import { 
  Users, 
  Wallet, 
  TrendingUp, 
  Clock,
  ChevronRight,
  Zap,
  Loader2,
  AlertCircle,
  Info,
} from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { SEO } from "@/components/SEO";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { TermTooltip } from "@/components/ui/term-tooltip";

const Dashboard = () => {
  // Usar dados da API real (com dataUpdatedAt para cache info)
  const { 
    data: dashboardData, 
    isLoading: loadingDashboard, 
    error: errorDashboard,
    dataUpdatedAt 
  } = useDashboard();
  
  // Pegar orçamento do dashboard ou usar padrão 100
  const orcamento = dashboardData?.patrimonio ?? 100;

  // Formatar tempo desde última atualização
  const getTempoAtualizacao = () => {
    if (!dataUpdatedAt) return null;
    const diff = Date.now() - dataUpdatedAt;
    const minutos = Math.floor(diff / 60000);
    if (minutos < 1) return 'Agora mesmo';
    return `Há ${minutos} min`;
  };
  
  const { data: escalacaoData, isLoading: loadingEscalacao } = useEscalacao('4-4-2', orcamento);
  
  // Extrair dados do dashboard
  const mercado = dashboardData?.mercado;
  const topValorizadores = dashboardData?.topValorizadores || [];
  const topPontuadores = dashboardData?.topPontuadores || [];
  const confrontos = dashboardData?.confrontos || [];

  // Calcular tempo até fechamento
  const calcularTempoFechamento = () => {
    if (!mercado?.fechamento) return 'N/A';
    
    // Se for timestamp Unix (número), converter para Date
    let fechamento: Date;
    if (typeof mercado.fechamento === 'number') {
      // Timestamp Unix em segundos
      fechamento = new Date(mercado.fechamento * 1000);
    } else {
      fechamento = new Date(mercado.fechamento);
    }
    
    const agora = new Date();
    const diff = fechamento.getTime() - agora.getTime();
    
    if (diff <= 0) return 'Fechado';
    
    const horas = Math.floor(diff / (1000 * 60 * 60));
    const minutos = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    
    return `${horas}h ${minutos}m`;
  };

  // Error state
  if (errorDashboard) {
    return (
      <MainLayout>
        <SEO title="Dashboard" description="Painel do Cartola FC 2026: mercado, escalação otimizada, confrontos e destaques da rodada." path="/dashboard" />
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Erro ao carregar dados do dashboard. Verifique se o backend está rodando.
          </AlertDescription>
        </Alert>
      </MainLayout>
    );
  }

  // Aguardar dados mínimos necessários
  if (!dashboardData || !mercado) {
    return (
      <MainLayout>
        <SEO title="Dashboard" description="Painel do Cartola FC 2026: mercado, escalação otimizada, confrontos e destaques da rodada." path="/dashboard" />
        <div className="flex flex-col items-center justify-center h-96 gap-4">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <span>Carregando dados do Cartola FC...</span>
        </div>
      </MainLayout>
    );
  }

  // Loading state das escalações - já tratado acima

  return (
    <MainLayout>
      <SEO
        title="Dashboard"
        description="Painel do Cartola FC 2026: mercado, escalação otimizada, confrontos e destaques da rodada."
        path="/dashboard"
      />
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="font-display text-3xl md:text-4xl font-bold">
              Dashboard
            </h1>
            <div className="flex items-center gap-3 mt-1">
              <p className="text-muted-foreground">
                Rodada {mercado.rodadaAtual} • Brasileirão 2026
              </p>
              {dashboardData && (
                <div className="flex flex-wrap gap-2">
                  <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 font-medium flex items-center gap-1 border border-emerald-500/20">
                    <span className="relative flex h-2 w-2">
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                    </span>
                    Dados atualizados
                  </span>
                  
                  {dataUpdatedAt && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-500 font-medium flex items-center gap-1 border border-blue-500/20" title={`Atualizado em: ${new Date(dataUpdatedAt).toLocaleTimeString()}`}>
                      <Zap className="w-3 h-3" />
                      {getTempoAtualizacao()}
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <div className={`flex items-center gap-2 px-4 py-2 rounded-lg ${
              mercado.status === 'aberto' ? 'bg-success/20 text-success' : 'bg-destructive/20 text-destructive'
            }`}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <div className="flex items-center gap-2 cursor-help">
                    <Clock className="w-4 h-4" />
                    <span className="font-semibold">
                      {mercado.status === 'aberto' ? `Fecha em ${calcularTempoFechamento()}` : 'Mercado Fechado'}
                    </span>
                  </div>
                </TooltipTrigger>
                <TooltipContent className="max-w-xs">
                  <p className="text-sm">O mercado fecha antes do início da rodada. Faça sua escalação antes deste horário!</p>
                </TooltipContent>
              </Tooltip>
            </div>
            
            <Link to="/escalacao">
              <Button className="hero-gradient text-primary-foreground gap-2">
                <Users className="w-4 h-4" />
                Escalar Time
              </Button>
            </Link>
          </div>
        </div>
      </motion.div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard
          title="Preço Médio"
          value={`C$${mercado.precoMedio?.toFixed(1) || '0.0'}`}
          subtitle="Média do mercado"
          icon={Wallet}
          variant="primary"
        />
        <StatCard
          title="Valorizados"
          value={mercado.valorizados || 0}
          subtitle="Jogadores em alta"
          icon={TrendingUp}
          variant="success"
        />
        <StatCard
          title="Atletas Prováveis"
          value={mercado.provaveis}
          subtitle={`de ${mercado.totalAtletas} atletas`}
          icon={Users}
          variant="secondary"
        />
        <StatCard
          title="Atletas Dúvida"
          value={mercado.duvidas}
          subtitle="Atenção na escalação"
          icon={AlertCircle}
          variant="warning"
        />
      </div>

      {/* Explicação das Estratégias */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="mb-6"
      >
        <div className="glass-card p-4 border-info/20">
          <div className="flex items-start gap-3">
            <Info className="w-5 h-5 text-info mt-0.5 shrink-0" />
            <div>
              <h3 className="font-display text-sm font-bold text-info mb-1">Como funcionam as sugestões?</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Geramos <strong className="text-green-400">dois tipos de time</strong> para cada rodada: 
                o <strong className="text-green-400">💰 Time Valorização</strong> foca em jogadores baratos (C$3-6) que vão subir de preço — ideal para aumentar seu patrimônio. 
                O <strong className="text-blue-400">⚡ Time Pontuação</strong> seleciona jogadores com maior chance de pontuar bem — ideal para subir no ranking.
              </p>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Times Sugeridos */}
        <div className="lg:col-span-2 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="font-display text-xl font-bold">Times Sugeridos</h2>
            <Link to="/escalacao" className="flex items-center gap-1 text-sm text-primary hover:underline">
              Ver detalhes <ChevronRight className="w-4 h-4" />
            </Link>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {loadingEscalacao ? (
              <>
                <Skeleton className="h-96 rounded-lg" />
                <Skeleton className="h-96 rounded-lg" />
              </>
            ) : escalacaoData ? (
              <>
                <FormationDisplay team={escalacaoData.timeValorizacao} />
                <FormationDisplay team={escalacaoData.timePontuacao} />
              </>
            ) : (
              <div className="col-span-2 text-center text-muted-foreground">
                Nenhuma escalação disponível
              </div>
            )}
          </div>
        </div>

        {/* Confrontos */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-display text-xl font-bold">Confrontos</h2>
            <Link to="/confrontos" className="flex items-center gap-1 text-sm text-primary hover:underline">
              Ver todos <ChevronRight className="w-4 h-4" />
            </Link>
          </div>
          
          <div className="space-y-4">
            {confrontos.slice(0, 2).map((match) => (
              <MatchCard key={match.id} match={match} />
            ))}
          </div>
        </div>
      </div>

      {/* Top Players */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Valorizadores */}
        <div className="glass-card p-6 team-card-valorizacao">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2.5 rounded-xl bg-gradient-to-br from-green-500 to-emerald-600 shadow-lg">
              <TrendingUp className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="font-display text-lg font-bold text-green-400">💰 Top Valorizadores</h3>
              <p className="text-xs text-muted-foreground">Maior potencial de subir de preço</p>
            </div>
          </div>
          
          <div className="space-y-3">
            {topValorizadores.map((player, index) => (
              <PlayerCard 
                key={player.id} 
                player={player} 
                compact 
                className={index === 0 ? "border-green-500/50" : ""}
              />
            ))}
          </div>
        </div>

        {/* Top Pontuadores */}
        <div className="glass-card p-6 team-card-pontuacao">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2.5 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 shadow-lg">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="font-display text-lg font-bold text-blue-400">⚡ Top Pontuadores</h3>
              <p className="text-xs text-muted-foreground">Maior chance de pontuar na rodada</p>
            </div>
          </div>
          
          <div className="space-y-3">
            {topPontuadores.map((player, index) => (
              <PlayerCard 
                key={player.id} 
                player={player} 
                compact 
                isCaptain={index === 0}
              />
            ))}
          </div>
        </div>
      </div>
    </MainLayout>
  );
};

export default Dashboard;
