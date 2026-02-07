import { MainLayout } from "@/components/layout/MainLayout";
import { useClassificacao, useAcuracia } from "@/hooks/useCartolaApi";
import { motion } from "framer-motion";
import { Trophy, TrendingUp, TrendingDown, AlertCircle, Loader2, Target, BarChart3, Shield } from "lucide-react";
import { cn } from "@/lib/utils";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useMemo } from "react";
import { SEO } from "@/components/SEO";
import { Disclaimer } from "@/components/Disclaimer";

const Brasileirao = () => {
  const { data: classificacaoData, isLoading, error } = useClassificacao();
  const { data: acuraciaData, isLoading: isLoadingAcuracia } = useAcuracia();

  const classificacao = useMemo(() => {
    return classificacaoData?.classificacao || [];
  }, [classificacaoData]);

  const simulacao = useMemo(() => {
    if (!classificacaoData?.simulacao) return new Map();
    const map = new Map<number, typeof classificacaoData.simulacao[0]>();
    for (const s of classificacaoData.simulacao) {
      map.set(s.id, s);
    }
    return map;
  }, [classificacaoData]);

  if (error) {
    return (
      <MainLayout>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Erro ao carregar dados do Brasileirão. Verifique se o backend está rodando.
          </AlertDescription>
        </Alert>
      </MainLayout>
    );
  }

  if (isLoading) {
    return (
      <MainLayout>
        <div className="space-y-6">
          <div className="flex items-center gap-2">
            <Loader2 className="h-6 w-6 animate-spin" />
            <span>Carregando classificação...</span>
          </div>
          <Skeleton className="h-96 rounded-lg" />
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <SEO
        title="Brasileirão 2026"
        description="Classificação do Brasileirão 2026 com simulação Monte Carlo. Probabilidades de título, Libertadores e rebaixamento."
        path="/brasileirao"
      />
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 hero-gradient rounded-lg">
            <Trophy className="w-6 h-6 text-primary-foreground" />
          </div>
          <div>
            <h1 className="font-display text-3xl md:text-4xl font-bold">
              Brasileirão 2026
            </h1>
            <div className="flex items-center gap-3">
              <p className="text-muted-foreground">
                Rodada {classificacaoData?.rodada || '?'} • Classificação + Simulação Monte Carlo
              </p>
              <span className="text-xs px-2 py-1 rounded-full bg-success/20 text-success font-semibold">
                🔴 AO VIVO
              </span>
            </div>
          </div>
        </div>
      </motion.div>

      <Tabs defaultValue="classificacao" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="classificacao">
            <Shield className="w-4 h-4 mr-2" /> Classificação
          </TabsTrigger>
          <TabsTrigger value="simulacao">
            <BarChart3 className="w-4 h-4 mr-2" /> Monte Carlo
          </TabsTrigger>
          <TabsTrigger value="acuracia">
            <Target className="w-4 h-4 mr-2" /> Acurácia
          </TabsTrigger>
        </TabsList>

        {/* ===== CLASSIFICAÇÃO ===== */}
        <TabsContent value="classificacao">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-card p-6"
          >
            <div className="overflow-x-auto">
              <table className="stats-table w-full">
                <thead>
                  <tr>
                    <th className="text-left">#</th>
                    <th className="text-left">Time</th>
                    <th className="text-center">P</th>
                    <th className="text-center">J</th>
                    <th className="text-center">V</th>
                    <th className="text-center">E</th>
                    <th className="text-center">D</th>
                    <th className="text-center">GP</th>
                    <th className="text-center">GC</th>
                    <th className="text-center">SG</th>
                    <th className="text-center">%</th>
                    <th className="text-center">Forma</th>
                  </tr>
                </thead>
                <tbody>
                  {classificacao.map((time, index) => (
                    <motion.tr
                      key={time.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.03 }}
                      className={cn(
                        index < 4 && "border-l-2 border-l-primary",
                        index >= 4 && index < 6 && "border-l-2 border-l-info",
                        index >= 6 && index < 12 && "border-l-2 border-l-warning",
                        index >= 16 && "border-l-2 border-l-destructive"
                      )}
                    >
                      <td>
                        <span className={cn(
                          "w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold",
                          index < 4 ? "bg-primary/20 text-primary" :
                          index < 6 ? "bg-info/20 text-info" :
                          index < 12 ? "bg-warning/20 text-warning" :
                          index >= 16 ? "bg-destructive/20 text-destructive" :
                          "bg-muted text-muted-foreground"
                        )}>
                          {time.posicao}
                        </span>
                      </td>
                      <td>
                        <div className="flex items-center gap-2">
                          {time.escudo && (
                            <img src={time.escudo} alt={time.abrev} className="w-6 h-6" />
                          )}
                          <div>
                            <div className="font-semibold text-sm">{time.nome || time.abrev}</div>
                            <div className="text-xs text-muted-foreground">{time.abrev}</div>
                          </div>
                        </div>
                      </td>
                      <td className="text-center font-bold text-lg">{time.pontos}</td>
                      <td className="text-center">{time.jogos}</td>
                      <td className="text-center text-success">{time.vitorias}</td>
                      <td className="text-center text-warning">{time.empates}</td>
                      <td className="text-center text-destructive">{time.derrotas}</td>
                      <td className="text-center">{time.gols_pro}</td>
                      <td className="text-center">{time.gols_contra}</td>
                      <td className="text-center font-semibold">
                        <span className={cn(
                          time.saldo_gols > 0 ? "text-success" :
                          time.saldo_gols < 0 ? "text-destructive" :
                          "text-muted-foreground"
                        )}>
                          {time.saldo_gols > 0 ? `+${time.saldo_gols}` : time.saldo_gols}
                        </span>
                      </td>
                      <td className="text-center text-sm">{time.aproveitamento}%</td>
                      <td className="text-center">
                        <div className="flex gap-0.5 justify-center">
                          {(time.forma || "").split("").slice(-5).map((r, i) => (
                            <span key={i} className={cn(
                              "w-5 h-5 rounded-sm flex items-center justify-center text-[10px] font-bold text-white",
                              r === "V" ? "bg-success" :
                              r === "E" ? "bg-warning" :
                              r === "D" ? "bg-destructive" :
                              "bg-muted"
                            )}>
                              {r}
                            </span>
                          ))}
                        </div>
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Legenda */}
            <div className="flex flex-wrap gap-4 mt-4 text-xs text-muted-foreground">
              <div className="flex items-center gap-1">
                <span className="w-3 h-3 rounded-full bg-primary" /> Libertadores (G4)
              </div>
              <div className="flex items-center gap-1">
                <span className="w-3 h-3 rounded-full bg-info" /> Pré-Libertadores
              </div>
              <div className="flex items-center gap-1">
                <span className="w-3 h-3 rounded-full bg-warning" /> Sul-Americana
              </div>
              <div className="flex items-center gap-1">
                <span className="w-3 h-3 rounded-full bg-destructive" /> Rebaixamento (Z4)
              </div>
            </div>
          </motion.div>
        </TabsContent>

        {/* ===== MONTE CARLO ===== */}
        <TabsContent value="simulacao">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-card p-6"
          >
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-primary" />
                <h2 className="font-display text-xl font-bold">Simulação Monte Carlo</h2>
              </div>
              <span className="text-xs px-3 py-1 rounded-full bg-primary/20 text-primary font-semibold">
                200 simulações • Poisson V3
              </span>
            </div>

            {classificacaoData?.simulacao ? (
              <div className="overflow-x-auto">
                <table className="stats-table w-full">
                  <thead>
                    <tr>
                      <th className="text-left">Time</th>
                      <th className="text-center">Pos. Média</th>
                      <th className="text-center">Pts Médio</th>
                      <th className="text-center">
                        <span className="flex items-center justify-center gap-1">
                          <Trophy className="w-3 h-3" /> Título
                        </span>
                      </th>
                      <th className="text-center">
                        <span className="flex items-center justify-center gap-1">
                          <TrendingUp className="w-3 h-3" /> G4
                        </span>
                      </th>
                      <th className="text-center">Sula</th>
                      <th className="text-center">
                        <span className="flex items-center justify-center gap-1">
                          <TrendingDown className="w-3 h-3" /> Z4
                        </span>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {classificacaoData.simulacao.map((sim, index) => (
                      <motion.tr
                        key={sim.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.03 }}
                      >
                        <td className="font-semibold">{sim.abrev}</td>
                        <td className="text-center">{sim.posicaoMedia.toFixed(1)}º</td>
                        <td className="text-center font-semibold">{sim.pontosMedio}</td>
                        <td className="text-center">
                          {sim.probTitulo > 0 ? (
                            <span className={cn(
                              "px-2 py-0.5 rounded text-xs font-bold",
                              sim.probTitulo > 20 ? "bg-primary/20 text-primary" :
                              sim.probTitulo > 5 ? "bg-primary/10 text-primary/60" :
                              "text-muted-foreground"
                            )}>
                              {sim.probTitulo.toFixed(1)}%
                            </span>
                          ) : (
                            <span className="text-muted-foreground text-xs">-</span>
                          )}
                        </td>
                        <td className="text-center">
                          <span className={cn(
                            "text-xs font-semibold",
                            sim.probLibertadores > 50 ? "text-success" :
                            sim.probLibertadores > 20 ? "text-info" :
                            "text-muted-foreground"
                          )}>
                            {sim.probLibertadores.toFixed(1)}%
                          </span>
                        </td>
                        <td className="text-center">
                          <span className="text-xs text-warning font-semibold">
                            {sim.probSulamericana > 0 ? `${sim.probSulamericana.toFixed(1)}%` : '-'}
                          </span>
                        </td>
                        <td className="text-center">
                          {sim.probRebaixamento > 0 ? (
                            <span className={cn(
                              "px-2 py-0.5 rounded text-xs font-bold",
                              sim.probRebaixamento > 30 ? "bg-destructive/20 text-destructive" :
                              sim.probRebaixamento > 10 ? "bg-destructive/10 text-destructive/70" :
                              "text-muted-foreground"
                            )}>
                              {sim.probRebaixamento.toFixed(1)}%
                            </span>
                          ) : (
                            <span className="text-muted-foreground text-xs">-</span>
                          )}
                        </td>
                      </motion.tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-12 text-muted-foreground">
                <BarChart3 className="w-12 h-12 mx-auto mb-4 opacity-30" />
                <p>Simulação Monte Carlo não disponível</p>
                <p className="text-xs mt-1">Aguarde mais rodadas para dados suficientes</p>
              </div>
            )}
          </motion.div>
        </TabsContent>

        {/* ===== ACURÁCIA ===== */}
        <TabsContent value="acuracia">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            {/* Card principal */}
            <div className="glass-card p-6">
              <div className="flex items-center gap-2 mb-6">
                <Target className="w-5 h-5 text-primary" />
                <h2 className="font-display text-xl font-bold">Acurácia do Modelo</h2>
              </div>

              {isLoadingAcuracia ? (
                <div className="flex items-center gap-2 justify-center py-8">
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Calculando acurácia...</span>
                </div>
              ) : acuraciaData ? (
                <>
                  {/* Stats cards */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    <div className="glass-card p-4 text-center">
                      <div className="text-3xl font-bold text-primary">
                        {acuraciaData.acuraciaGeral.toFixed(1)}%
                      </div>
                      <div className="text-xs text-muted-foreground">Acurácia Geral</div>
                    </div>
                    <div className="glass-card p-4 text-center">
                      <div className="text-3xl font-bold">{acuraciaData.totalAcertos}</div>
                      <div className="text-xs text-muted-foreground">Acertos</div>
                    </div>
                    <div className="glass-card p-4 text-center">
                      <div className="text-3xl font-bold">{acuraciaData.totalJogos}</div>
                      <div className="text-xs text-muted-foreground">Jogos Analisados</div>
                    </div>
                    <div className="glass-card p-4 text-center">
                      <div className="text-3xl font-bold">{acuraciaData.totalRodadas}</div>
                      <div className="text-xs text-muted-foreground">Rodadas</div>
                    </div>
                  </div>

                  {/* Tabela por rodada */}
                  {acuraciaData.rodadas.length > 0 && (
                    <div className="overflow-x-auto">
                      <table className="stats-table w-full">
                        <thead>
                          <tr>
                            <th className="text-center">Rodada</th>
                            <th className="text-center">Partidas</th>
                            <th className="text-center">Acertos</th>
                            <th className="text-center">Acurácia</th>
                          </tr>
                        </thead>
                        <tbody>
                          {acuraciaData.rodadas.map((r, index) => (
                            <motion.tr
                              key={r.rodada}
                              initial={{ opacity: 0 }}
                              animate={{ opacity: 1 }}
                              transition={{ delay: index * 0.05 }}
                            >
                              <td className="text-center font-semibold">R{r.rodada}</td>
                              <td className="text-center">{r.totalPartidas}</td>
                              <td className="text-center font-bold text-success">{r.acertos}</td>
                              <td className="text-center">
                                <div className="flex items-center justify-center gap-2">
                                  <div className="w-16 h-2 bg-muted rounded-full overflow-hidden">
                                    <div
                                      className={cn(
                                        "h-full rounded-full",
                                        r.acuracia >= 30 ? "bg-success" :
                                        r.acuracia >= 15 ? "bg-warning" :
                                        "bg-destructive"
                                      )}
                                      style={{ width: `${Math.min(r.acuracia, 100)}%` }}
                                    />
                                  </div>
                                  <span className="text-xs font-bold">{r.acuracia.toFixed(1)}%</span>
                                </div>
                              </td>
                            </motion.tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}

                  <div className="mt-4 text-xs text-muted-foreground text-center">
                    Metodologia: {acuraciaData.metodologia}
                  </div>
                </>
              ) : (
                <div className="text-center py-12 text-muted-foreground">
                  <Target className="w-12 h-12 mx-auto mb-4 opacity-30" />
                  <p>Dados de acurácia não disponíveis</p>
                  <p className="text-xs mt-1">Aguarde rodadas concluídas para comparação</p>
                </div>
              )}
            </div>
          </motion.div>
        </TabsContent>
      </Tabs>

      {/* Disclaimer */}
      <Disclaimer />
    </MainLayout>
  );
};

export default Brasileirao;
