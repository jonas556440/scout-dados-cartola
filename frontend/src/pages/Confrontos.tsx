import { MainLayout } from "@/components/layout/MainLayout";
import { MatchCard } from "@/components/cartola/MatchCard";
import { useConfrontos, useForcaTimes } from "@/hooks/useCartolaApi";
import { motion } from "framer-motion";
import { Swords, Calendar, MapPin, TrendingUp, Shield, Loader2, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { useMemo } from "react";

const Confrontos = () => {
  const { data: confrontos, isLoading, error } = useConfrontos();
  const { data: forcaTimesData, isLoading: isLoadingForca } = useForcaTimes();

  // Usar dados do endpoint de força dos times
  const clubesStats = useMemo(() => {
    if (!forcaTimesData || !forcaTimesData.times) return [];
    return forcaTimesData.times;
  }, [forcaTimesData]);

  // Error state
  if (error) {
    return (
      <MainLayout>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Erro ao carregar confrontos. Verifique se o backend está rodando.
          </AlertDescription>
        </Alert>
      </MainLayout>
    );
  }

  // Loading state
  if (isLoading) {
    return (
      <MainLayout>
        <div className="space-y-6">
          <div className="flex items-center gap-2">
            <Loader2 className="h-6 w-6 animate-spin" />
            <span>Carregando confrontos...</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <Skeleton key={i} className="h-48 rounded-lg" />
            ))}
          </div>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 hero-gradient rounded-lg">
            <Swords className="w-6 h-6 text-primary-foreground" />
          </div>
          <div>
            <h1 className="font-display text-3xl md:text-4xl font-bold">
              Confrontos
            </h1>
            <div className="flex items-center gap-3">
              <p className="text-muted-foreground">
                Rodada {confrontos?.[0]?.rodada || '?'} • Análise de partidas
              </p>
              {confrontos && (
                <span className="text-xs px-2 py-1 rounded-full bg-success/20 text-success font-semibold">
                  🔴 AO VIVO - API REAL
                </span>
              )}
            </div>
          </div>
        </div>
      </motion.div>

      {/* Matches Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 mb-8">
        {confrontos && confrontos.map((match, index) => (
          <motion.div
            key={match.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <MatchCard match={match} />
          </motion.div>
        ))}
      </div>

      {/* Análise de Times */}
      <div className="glass-card p-6">
        <div className="flex items-center gap-2 mb-6">
          <Shield className="w-5 h-5 text-primary" />
          <h2 className="font-display text-xl font-bold">Força dos Times</h2>
        </div>

        <div className="overflow-x-auto">
          <table className="stats-table">
            <thead>
              <tr>
                <th>Time</th>
                <th className="text-center">Pos</th>
                <th className="text-center">J</th>
                <th className="text-center">V</th>
                <th className="text-center">E</th>
                <th className="text-center">D</th>
                <th className="text-center">Força Casa</th>
                <th className="text-center">Força Fora</th>
              </tr>
            </thead>
            <tbody>
              {isLoadingForca ? (
                Array.from({ length: 20 }).map((_, index) => (
                  <tr key={index}>
                    <td colSpan={8}>
                      <Skeleton className="h-12 w-full" />
                    </td>
                  </tr>
                ))
              ) : clubesStats.length > 0 ? (
                clubesStats.map((club, index) => (
                  <motion.tr
                    key={club.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                  >
                    <td>
                      <div className="flex items-center gap-3">
                        <span className={cn(
                          "w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold",
                          index < 4 ? "bg-primary/20 text-primary" : 
                          index < 6 ? "bg-info/20 text-info" :
                          index >= 16 ? "bg-destructive/20 text-destructive" :
                          "bg-muted text-muted-foreground"
                        )}>
                          {index + 1}
                        </span>
                        <div>
                          <div className="font-semibold">{club.nome || club.abrev}</div>
                          <div className="text-xs text-muted-foreground">{club.abrev}</div>
                        </div>
                      </div>
                    </td>
                    <td className="text-center font-bold">{club.posicao}º</td>
                    <td className="text-center">{club.jogos}</td>
                    <td className="text-center text-success">{club.vitorias}</td>
                    <td className="text-center text-warning">{club.empates}</td>
                    <td className="text-center text-destructive">{club.derrotas}</td>
                    <td className="text-center">
                      <div className="flex items-center justify-center gap-2">
                        <div className="w-16 h-2 bg-muted rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-primary rounded-full"
                            style={{ width: `${club.forcaCasa}%` }}
                          />
                        </div>
                        <span className="text-xs font-semibold text-primary">{Math.round(club.forcaCasa)}</span>
                      </div>
                    </td>
                    <td className="text-center">
                      <div className="flex items-center justify-center gap-2">
                        <div className="w-16 h-2 bg-muted rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-secondary rounded-full"
                            style={{ width: `${club.forcaFora}%` }}
                          />
                        </div>
                        <span className="text-xs font-semibold text-secondary">{Math.round(club.forcaFora)}</span>
                      </div>
                    </td>
                  </motion.tr>
                ))
              ) : (
                <tr>
                  <td colSpan={8} className="text-center py-8 text-muted-foreground">
                    Nenhum dado disponível
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </MainLayout>
  );
};

export default Confrontos;