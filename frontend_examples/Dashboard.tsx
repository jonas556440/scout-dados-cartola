/**
 * Exemplo de Dashboard.tsx modificado para usar a API real
 * Este arquivo mostra como substituir os mockData por chamadas à API
 * 
 * COMO USAR:
 * 1. Clone o frontend: git clone https://github.com/jonas556440/cartola-ai-pro frontend
 * 2. Copie src/config/api.ts para o frontend
 * 3. Copie src/hooks/useCartolaApi.ts para o frontend
 * 4. Substitua o Dashboard.tsx original por este
 */

import { motion } from "framer-motion";
import { TrendingUp, Users, Zap, Trophy, Loader2, AlertCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";

// Componentes do cartola
import { PlayerCard } from "@/components/cartola/PlayerCard";
import { FormationDisplay } from "@/components/cartola/FormationDisplay";
import { MatchCard } from "@/components/cartola/MatchCard";
import { StatCard } from "@/components/cartola/StatCard";

// Hook da API real (substituindo mockData)
import { useDashboard, useEscalacao, useConfrontos } from "@/hooks/useCartolaApi";

// ============ Loading Skeleton ============

function DashboardSkeleton() {
    return (
        <div className="container mx-auto p-6 space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {[1, 2, 3, 4].map((i) => (
                    <Skeleton key={i} className="h-32 rounded-lg" />
                ))}
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Skeleton className="h-96 rounded-lg" />
                <Skeleton className="h-96 rounded-lg" />
            </div>
        </div>
    );
}

// ============ Error State ============

function DashboardError({ error }: { error: Error }) {
    return (
        <div className="container mx-auto p-6">
            <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                    Erro ao carregar dados: {error.message}
                    <br />
                    Verifique se o backend está rodando em http://localhost:8000
                </AlertDescription>
            </Alert>
        </div>
    );
}

// ============ Dashboard Component ============

export default function Dashboard() {
    // Buscar dados da API real
    const { data: dashboard, isLoading: loadingDashboard, error: errorDashboard } = useDashboard();
    const { data: escalacao, isLoading: loadingEscalacao } = useEscalacao('4-4-2', 100);
    const { data: confrontos, isLoading: loadingConfrontos } = useConfrontos();

    // Estados de loading
    if (loadingDashboard || loadingEscalacao) {
        return <DashboardSkeleton />;
    }

    // Estados de erro
    if (errorDashboard) {
        return <DashboardError error={errorDashboard as Error} />;
    }

    // Dados do dashboard
    const stats = dashboard?.mercado;
    const topValorizadores = dashboard?.topValorizadores || [];
    const topPontuadores = dashboard?.topPontuadores || [];
    const patrimonio = dashboard?.patrimonio;

    // Times gerados
    const timeValorizacao = escalacao?.timeValorizacao;
    const timePontuacao = escalacao?.timePontuacao;

    // Animações
    const containerVariants = {
        hidden: { opacity: 0 },
        visible: {
            opacity: 1,
            transition: { staggerChildren: 0.1 }
        }
    };

    const itemVariants = {
        hidden: { y: 20, opacity: 0 },
        visible: {
            y: 0,
            opacity: 1,
            transition: { type: "spring", stiffness: 100 }
        }
    };

    return (
        <motion.div
            className="container mx-auto p-6 space-y-6"
            variants={containerVariants}
            initial="hidden"
            animate="visible"
        >
            {/* Header */}
            <motion.div variants={itemVariants}>
                <h1 className="text-3xl font-bold text-foreground">
                    Dashboard
                </h1>
                <p className="text-muted-foreground">
                    Rodada {stats?.rodadaAtual} • Mercado {stats?.status === 'aberto' ? '🟢 Aberto' : '🔴 Fechado'}
                </p>
            </motion.div>

            {/* Stats Cards */}
            <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard
                    title="Rodada Atual"
                    value={stats?.rodadaAtual || 0}
                    icon={Trophy}
                    trend="neutral"
                />
                <StatCard
                    title="Atletas Prováveis"
                    value={stats?.provaveis || 0}
                    icon={Users}
                    trend="up"
                    description={`${stats?.duvidas || 0} dúvidas`}
                />
                <StatCard
                    title="Patrimônio"
                    value={`C$ ${patrimonio?.cartoletas?.toFixed(2) || '100.00'}`}
                    icon={TrendingUp}
                    trend={patrimonio?.variacao >= 0 ? 'up' : 'down'}
                    description={`${patrimonio?.variacao >= 0 ? '+' : ''}${patrimonio?.variacao?.toFixed(2) || '0.00'}`}
                />
                <StatCard
                    title="Pontuação Total"
                    value={patrimonio?.pontuacaoTotal?.toFixed(1) || '0.0'}
                    icon={Zap}
                    trend="neutral"
                />
            </motion.div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Time Valorização */}
                <motion.div variants={itemVariants}>
                    <Card className="h-full">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <TrendingUp className="h-5 w-5 text-green-500" />
                                Time Valorização
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            {timeValorizacao ? (
                                <FormationDisplay
                                    team={timeValorizacao}
                                    showDetails
                                />
                            ) : (
                                <p className="text-muted-foreground text-center py-8">
                                    {loadingEscalacao ? (
                                        <Loader2 className="h-6 w-6 animate-spin mx-auto" />
                                    ) : (
                                        'Nenhum time gerado'
                                    )}
                                </p>
                            )}
                        </CardContent>
                    </Card>
                </motion.div>

                {/* Time Pontuação */}
                <motion.div variants={itemVariants}>
                    <Card className="h-full">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Zap className="h-5 w-5 text-yellow-500" />
                                Time Pontuação
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            {timePontuacao ? (
                                <FormationDisplay
                                    team={timePontuacao}
                                    showDetails
                                />
                            ) : (
                                <p className="text-muted-foreground text-center py-8">
                                    {loadingEscalacao ? (
                                        <Loader2 className="h-6 w-6 animate-spin mx-auto" />
                                    ) : (
                                        'Nenhum time gerado'
                                    )}
                                </p>
                            )}
                        </CardContent>
                    </Card>
                </motion.div>
            </div>

            {/* Confrontos */}
            <motion.div variants={itemVariants}>
                <Card>
                    <CardHeader>
                        <CardTitle>Próximos Confrontos</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {loadingConfrontos ? (
                                [1, 2, 3].map((i) => (
                                    <Skeleton key={i} className="h-24 rounded-lg" />
                                ))
                            ) : confrontos?.length ? (
                                confrontos.slice(0, 6).map((match) => (
                                    <MatchCard key={match.id} match={match} />
                                ))
                            ) : (
                                <p className="text-muted-foreground col-span-3 text-center py-4">
                                    Nenhum confronto disponível
                                </p>
                            )}
                        </div>
                    </CardContent>
                </Card>
            </motion.div>

            {/* Top Jogadores */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Top Valorizadores */}
                <motion.div variants={itemVariants}>
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <TrendingUp className="h-5 w-5 text-green-500" />
                                Top Valorizadores
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-2">
                            {topValorizadores.map((player, index) => (
                                <PlayerCard
                                    key={player.id}
                                    player={player}
                                    rank={index + 1}
                                    showTrend
                                    compact
                                />
                            ))}
                        </CardContent>
                    </Card>
                </motion.div>

                {/* Top Pontuadores */}
                <motion.div variants={itemVariants}>
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Zap className="h-5 w-5 text-yellow-500" />
                                Top Pontuadores
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-2">
                            {topPontuadores.map((player, index) => (
                                <PlayerCard
                                    key={player.id}
                                    player={player}
                                    rank={index + 1}
                                    showMedia
                                    compact
                                />
                            ))}
                        </CardContent>
                    </Card>
                </motion.div>
            </div>
        </motion.div>
    );
}
