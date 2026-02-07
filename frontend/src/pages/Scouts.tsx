import { MainLayout } from "@/components/layout/MainLayout";
import { useScoutsDestaques, useDesfalques } from "@/hooks/useCartolaApi";
import { motion } from "framer-motion";
import { Star, AlertCircle, Loader2, Zap, Target, ShieldAlert, Medal } from "lucide-react";
import { cn } from "@/lib/utils";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { SEO } from "@/components/SEO";
import { Disclaimer } from "@/components/Disclaimer";

// Mapa de scouts para labels amigáveis
const SCOUT_LABELS: Record<string, string> = {
  G: "Gol", A: "Assistência", FT: "Finalização Trave", FD: "Finalização Defendida",
  FF: "Finalização Fora", FS: "Falta Sofrida", PE: "Passe Errado", I: "Impedimento",
  RB: "Roubada", FC: "Falta Cometida", GC: "Gol Contra", CA: "Cartão Amarelo",
  CV: "Cartão Vermelho", SG: "Sem Gol Sofrido", DD: "Defesa Difícil", DP: "Defesa Pênalti",
  GS: "Gol Sofrido", DS: "Desarme", PP: "Pênalti Perdido", PC: "Pênalti Cometido",
};

// Scouts positivos (verde) e negativos (vermelho)
const SCOUTS_POSITIVOS = new Set(["G", "A", "FT", "FD", "FS", "RB", "SG", "DD", "DP", "DS"]);
const SCOUTS_NEGATIVOS = new Set(["PE", "GC", "CA", "CV", "GS", "PP", "PC", "FC", "I", "FF"]);

const Scouts = () => {
  const { data: destaquesData, isLoading, error } = useScoutsDestaques();
  const { data: desfalquesData, isLoading: isLoadingDesfalques } = useDesfalques();

  if (error) {
    return (
      <MainLayout>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Erro ao carregar scouts. Verifique se o backend está rodando.
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
            <span>Carregando scouts...</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <Skeleton key={i} className="h-32 rounded-lg" />
            ))}
          </div>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <SEO
        title="Scouts & Destaques"
        description="Scouts detalhados, artilheiros, assistentes e desfalques da rodada do Cartola FC 2026."
        path="/scouts"
      />
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 hero-gradient rounded-lg">
            <Star className="w-6 h-6 text-primary-foreground" />
          </div>
          <div>
            <h1 className="font-display text-3xl md:text-4xl font-bold">
              Scouts & Destaques
            </h1>
            <p className="text-muted-foreground">
              Maiores pontuadores, artilheiros, assistentes e desfalques
            </p>
          </div>
        </div>
      </motion.div>

      <Tabs defaultValue="destaques" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="destaques">
            <Zap className="w-4 h-4 mr-2" /> Destaques
          </TabsTrigger>
          <TabsTrigger value="artilheiros">
            <Medal className="w-4 h-4 mr-2" /> Gols & Assists
          </TabsTrigger>
          <TabsTrigger value="desfalques">
            <ShieldAlert className="w-4 h-4 mr-2" /> Desfalques
          </TabsTrigger>
        </TabsList>

        {/* ===== DESTAQUES ===== */}
        <TabsContent value="destaques">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4"
          >
            {destaquesData?.destaques && destaquesData.destaques.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {destaquesData.destaques.map((jogador, index) => (
                  <motion.div
                    key={jogador.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="glass-card p-4 hover:shadow-lg transition-all"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        {index < 3 && (
                          <span className={cn(
                            "w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white",
                            index === 0 ? "bg-yellow-500" :
                            index === 1 ? "bg-gray-400" :
                            "bg-amber-700"
                          )}>
                            {index + 1}
                          </span>
                        )}
                        <div>
                          <div className="font-semibold text-sm">{jogador.apelido}</div>
                          <div className="text-xs text-muted-foreground">{jogador.clubeAbrev}</div>
                        </div>
                      </div>
                      <div className={cn(
                        "text-xl font-bold",
                        jogador.pontuacao >= 10 ? "text-success" :
                        jogador.pontuacao >= 5 ? "text-primary" :
                        jogador.pontuacao >= 0 ? "text-muted-foreground" :
                        "text-destructive"
                      )}>
                        {jogador.pontuacao.toFixed(1)}
                      </div>
                    </div>

                    {/* Scouts */}
                    <div className="flex flex-wrap gap-1">
                      {Object.entries(jogador.scouts).map(([key, value]) => (
                        <Badge
                          key={key}
                          variant={SCOUTS_POSITIVOS.has(key) ? "default" : "destructive"}
                          className="text-[10px] px-1.5 py-0"
                        >
                          {SCOUT_LABELS[key] || key}: {value}
                        </Badge>
                      ))}
                    </div>
                  </motion.div>
                ))}
              </div>
            ) : (
              <div className="glass-card p-12 text-center text-muted-foreground">
                <Star className="w-12 h-12 mx-auto mb-4 opacity-30" />
                <p>Nenhum scout disponível</p>
                <p className="text-xs mt-1">Os scouts são atualizados após cada rodada</p>
              </div>
            )}
          </motion.div>
        </TabsContent>

        {/* ===== ARTILHEIROS & ASSISTENTES ===== */}
        <TabsContent value="artilheiros">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="grid grid-cols-1 lg:grid-cols-2 gap-6"
          >
            {/* Artilheiros */}
            <div className="glass-card p-6">
              <div className="flex items-center gap-2 mb-4">
                <Target className="w-5 h-5 text-success" />
                <h3 className="font-display text-lg font-bold">Artilheiros da Rodada</h3>
              </div>
              {destaquesData?.artilheiros && destaquesData.artilheiros.length > 0 ? (
                <div className="space-y-3">
                  {destaquesData.artilheiros.map((jogador, index) => (
                    <div key={jogador.id} className="flex items-center justify-between p-2 rounded bg-muted/30">
                      <div className="flex items-center gap-2">
                        <span className="w-6 h-6 rounded-full bg-success/20 text-success flex items-center justify-center text-xs font-bold">
                          {index + 1}
                        </span>
                        <div>
                          <div className="font-semibold text-sm">{jogador.apelido}</div>
                          <div className="text-xs text-muted-foreground">{jogador.clubeAbrev}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-lg font-bold text-success">⚽ {jogador.gols}</span>
                        <span className="text-xs text-muted-foreground">({jogador.pontuacao.toFixed(1)} pts)</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center py-6 text-muted-foreground text-sm">Nenhum gol registrado</p>
              )}
            </div>

            {/* Assistentes */}
            <div className="glass-card p-6">
              <div className="flex items-center gap-2 mb-4">
                <Zap className="w-5 h-5 text-info" />
                <h3 className="font-display text-lg font-bold">Assistências da Rodada</h3>
              </div>
              {destaquesData?.assistentes && destaquesData.assistentes.length > 0 ? (
                <div className="space-y-3">
                  {destaquesData.assistentes.map((jogador, index) => (
                    <div key={jogador.id} className="flex items-center justify-between p-2 rounded bg-muted/30">
                      <div className="flex items-center gap-2">
                        <span className="w-6 h-6 rounded-full bg-info/20 text-info flex items-center justify-center text-xs font-bold">
                          {index + 1}
                        </span>
                        <div>
                          <div className="font-semibold text-sm">{jogador.apelido}</div>
                          <div className="text-xs text-muted-foreground">{jogador.clubeAbrev}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-lg font-bold text-info">🎯 {jogador.assistencias}</span>
                        <span className="text-xs text-muted-foreground">({jogador.pontuacao.toFixed(1)} pts)</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center py-6 text-muted-foreground text-sm">Nenhuma assistência registrada</p>
              )}
            </div>
          </motion.div>
        </TabsContent>

        {/* ===== DESFALQUES ===== */}
        <TabsContent value="desfalques">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            {/* Resumo */}
            {desfalquesData && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="glass-card p-4 text-center">
                  <div className="text-3xl font-bold text-destructive">{desfalquesData.resumo.totalGeral}</div>
                  <div className="text-xs text-muted-foreground">Total Desfalques</div>
                </div>
                <div className="glass-card p-4 text-center">
                  <div className="text-3xl font-bold text-destructive">{desfalquesData.resumo.totalLesionados}</div>
                  <div className="text-xs text-muted-foreground">Lesionados</div>
                </div>
                <div className="glass-card p-4 text-center">
                  <div className="text-3xl font-bold text-warning">{desfalquesData.resumo.totalSuspensos}</div>
                  <div className="text-xs text-muted-foreground">Suspensos</div>
                </div>
                <div className="glass-card p-4 text-center">
                  <div className="text-3xl font-bold text-info">{desfalquesData.resumo.totalDuvidas}</div>
                  <div className="text-xs text-muted-foreground">Dúvidas</div>
                </div>
              </div>
            )}

            {/* Cards por clube */}
            {isLoadingDesfalques ? (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {[1, 2, 3].map((i) => <Skeleton key={i} className="h-32 rounded-lg" />)}
              </div>
            ) : desfalquesData?.clubes && desfalquesData.clubes.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {desfalquesData.clubes.map((clube, index) => (
                  <motion.div
                    key={clube.clubeId}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="glass-card p-4"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="font-semibold">{clube.clubeNome || clube.clubeAbrev}</div>
                      <span className="text-xs px-2 py-1 rounded bg-destructive/20 text-destructive font-bold">
                        {clube.totalDesfalques} desfalques
                      </span>
                    </div>

                    {clube.lesionados.length > 0 && (
                      <div className="mb-2">
                        <div className="text-xs text-destructive mb-1 font-semibold">🔴 Lesionados ({clube.lesionados.length})</div>
                        <div className="flex flex-wrap gap-1">
                          {clube.lesionados.map((j, i) => (
                            <Badge key={i} variant="destructive" className="text-xs">{j}</Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {clube.suspensos.length > 0 && (
                      <div className="mb-2">
                        <div className="text-xs text-warning mb-1 font-semibold">🟡 Suspensos ({clube.suspensos.length})</div>
                        <div className="flex flex-wrap gap-1">
                          {clube.suspensos.map((j, i) => (
                            <Badge key={i} variant="outline" className="text-xs border-warning text-warning">{j}</Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {clube.duvidas.length > 0 && (
                      <div className="mb-2">
                        <div className="text-xs text-info mb-1 font-semibold">💭 Dúvidas ({clube.duvidas.length})</div>
                        <div className="flex flex-wrap gap-1">
                          {clube.duvidas.map((j, i) => (
                            <Badge key={i} variant="outline" className="text-xs border-info text-info">{j}</Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </motion.div>
                ))}
              </div>
            ) : (
              <div className="glass-card p-12 text-center text-muted-foreground">
                <ShieldAlert className="w-12 h-12 mx-auto mb-4 opacity-30" />
                <p>Nenhum desfalque registrado</p>
              </div>
            )}
          </motion.div>
        </TabsContent>
      </Tabs>

      {/* Disclaimer */}
      <Disclaimer compact />
    </MainLayout>
  );
};

export default Scouts;
