import { MainLayout } from "@/components/layout/MainLayout";
import { MatchCard } from "@/components/cartola/MatchCard";
import { Disclaimer } from "@/components/Disclaimer";
import { useConfrontos, useForcaTimes, usePrevisaoPlacares, useNoticiasRodada, usePrevisaoCustomizada } from "@/hooks/useCartolaApi";
import { motion } from "framer-motion";
import { Swords, Calendar, MapPin, TrendingUp, Shield, Loader2, AlertCircle, Target, Award, Gamepad2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { useMemo, useState } from "react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { SEO } from "@/components/SEO";

const Confrontos = () => {
  const { data: confrontos, isLoading, error } = useConfrontos();
  const { data: forcaTimesData, isLoading: isLoadingForca } = useForcaTimes();
  const { data: previsoesData, isLoading: isLoadingPrevisoes } = usePrevisaoPlacares();
  const { data: noticiasData, isLoading: isLoadingNoticias } = useNoticiasRodada();
  const previsaoCustomizada = usePrevisaoCustomizada();

  // Simulador state
  const [simMandante, setSimMandante] = useState<string>("");
  const [simVisitante, setSimVisitante] = useState<string>("");
  const [simForcaMandante, setSimForcaMandante] = useState<number>(50);
  const [simForcaVisitante, setSimForcaVisitante] = useState<number>(50);

  // Usar dados do endpoint de força dos times
  const clubesStats = useMemo(() => {
    if (!forcaTimesData || !forcaTimesData.times) return [];
    return forcaTimesData.times;
  }, [forcaTimesData]);

  // Lista de times para o Simulador
  const timesDisponiveis = useMemo(() => {
    if (!clubesStats.length) return [];
    return clubesStats.map(t => ({ abrev: t.abrev, nome: t.nome || t.abrev, forcaGeral: t.forcaGeral }))
      .sort((a, b) => a.nome.localeCompare(b.nome));
  }, [clubesStats]);

  // Auto-preencher força ao selecionar time
  const handleMandanteChange = (abrev: string) => {
    setSimMandante(abrev);
    const time = timesDisponiveis.find(t => t.abrev === abrev);
    if (time) setSimForcaMandante(Math.round(time.forcaGeral));
  };
  const handleVisitanteChange = (abrev: string) => {
    setSimVisitante(abrev);
    const time = timesDisponiveis.find(t => t.abrev === abrev);
    if (time) setSimForcaVisitante(Math.round(time.forcaGeral));
  };

  const handleSimular = () => {
    if (!simMandante || !simVisitante || simMandante === simVisitante) return;
    previsaoCustomizada.mutate({
      mandante: simMandante,
      visitante: simVisitante,
      forcaMandante: simForcaMandante,
      forcaVisitante: simForcaVisitante,
    });
  };

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
      <SEO
        title="Confrontos"
        description="Análise de confrontos da rodada com previsão de placares (Poisson + xG), desfalques e simulador de jogos."
        path="/confrontos"
      />
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

      {/* Previsão de Placares */}
      {previsoesData && previsoesData.previsoes && previsoesData.previsoes.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card p-6 mb-8"
        >
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <Target className="w-5 h-5 text-primary" />
              <h2 className="font-display text-xl font-bold">Previsão de Placares</h2>
            </div>
            <span className="text-xs px-3 py-1 rounded-full bg-primary/20 text-primary font-semibold">
              Distribuição de Poisson + xG
            </span>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {previsoesData.previsoes.map((previsao, index) => (
              <motion.div
                key={`${previsao.mandanteId}-${previsao.visitanteId}`}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.05 }}
                className="glass-card p-4 hover:shadow-lg transition-all"
              >
                {/* Jogo */}
                <div className="flex items-center justify-between mb-4">
                  <div className="flex-1 text-right">
                    <div className="font-semibold text-sm">{previsao.mandante}</div>
                    <div className="text-xs text-muted-foreground">Casa</div>
                  </div>
                  
                  <div className="px-4 py-2 mx-3 rounded-lg bg-primary/10 border border-primary/20">
                    <div className="text-lg font-bold text-center text-primary">
                      {previsao.placarProvavel}
                    </div>
                    <div className="text-[10px] text-center text-muted-foreground">
                      {previsao.probabilidadePlacar.toFixed(1)}%
                    </div>
                  </div>
                  
                  <div className="flex-1">
                    <div className="font-semibold text-sm">{previsao.visitante}</div>
                    <div className="text-xs text-muted-foreground">Fora</div>
                  </div>
                </div>

                {/* xG */}
                <div className="flex items-center justify-between mb-3 text-xs">
                  <span className="text-muted-foreground">xG: <strong>{previsao.xgMandante.toFixed(2)}</strong></span>
                  <span className="text-muted-foreground">xG: <strong>{previsao.xgVisitante.toFixed(2)}</strong></span>
                </div>

                {/* Probabilidades 1x2 */}
                <div className="grid grid-cols-3 gap-2 mb-3">
                  <div className="text-center p-2 rounded bg-success/10 border border-success/20">
                    <div className="text-xs text-muted-foreground">Casa</div>
                    <div className="font-bold text-success">{previsao.probVitoriaCasa.toFixed(1)}%</div>
                  </div>
                  <div className="text-center p-2 rounded bg-warning/10 border border-warning/20">
                    <div className="text-xs text-muted-foreground">Empate</div>
                    <div className="font-bold text-warning">{previsao.probEmpate.toFixed(1)}%</div>
                  </div>
                  <div className="text-center p-2 rounded bg-info/10 border border-info/20">
                    <div className="text-xs text-muted-foreground">Fora</div>
                    <div className="font-bold text-info">{previsao.probVitoriaFora.toFixed(1)}%</div>
                  </div>
                </div>

                {/* Over/Under e BTTS */}
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="flex items-center justify-between p-2 rounded bg-muted/50">
                    <span className="text-muted-foreground">+2.5 gols</span>
                    <span className="font-bold">{previsao.over25.toFixed(1)}%</span>
                  </div>
                  <div className="flex items-center justify-between p-2 rounded bg-muted/50">
                    <span className="text-muted-foreground">Ambos marcam</span>
                    <span className="font-bold">{previsao.btts.toFixed(1)}%</span>
                  </div>
                </div>

                {/* Top placar alternativo */}
                {previsao.topPlacares && previsao.topPlacares.length > 1 && (
                  <div className="mt-3 pt-3 border-t border-border">
                    <div className="text-[10px] text-muted-foreground mb-1">Placares alternativos:</div>
                    <div className="flex gap-2 flex-wrap">
                      {previsao.topPlacares.slice(1, 4).map((placar, i) => (
                        <span key={i} className="text-xs px-2 py-1 rounded bg-muted text-muted-foreground">
                          {placar.placar} <span className="font-bold">({placar.probabilidade.toFixed(1)}%)</span>
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Confiança */}
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-[10px] text-muted-foreground">Confiança do modelo:</span>
                  <div className="flex items-center gap-2">
                    <div className="w-20 h-1.5 bg-muted rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-primary rounded-full"
                        style={{ width: `${previsao.confianca}%` }}
                      />
                    </div>
                    <span className="text-xs font-bold text-primary">{previsao.confianca.toFixed(0)}%</span>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Simulador de Jogos */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card p-6 mb-8"
      >
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <Gamepad2 className="w-5 h-5 text-primary" />
            <h2 className="font-display text-xl font-bold">Simulador de Jogos</h2>
          </div>
          <span className="text-xs px-3 py-1 rounded-full bg-primary/20 text-primary font-semibold">
            AdvancedScorePredictor
          </span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Mandante */}
          <div className="space-y-4">
            <Label className="text-sm font-semibold">Mandante (Casa)</Label>
            <Select value={simMandante} onValueChange={handleMandanteChange}>
              <SelectTrigger>
                <SelectValue placeholder="Selecione o time mandante" />
              </SelectTrigger>
              <SelectContent>
                {timesDisponiveis
                  .filter(t => t.abrev !== simVisitante)
                  .map(t => (
                    <SelectItem key={t.abrev} value={t.abrev}>
                      {t.nome} ({t.abrev})
                    </SelectItem>
                  ))}
              </SelectContent>
            </Select>
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-muted-foreground">Força</span>
                <span className="text-sm font-bold text-primary">{simForcaMandante}</span>
              </div>
              <Slider
                value={[simForcaMandante]}
                onValueChange={(v) => setSimForcaMandante(v[0])}
                min={0}
                max={100}
                step={1}
              />
            </div>
          </div>

          {/* Visitante */}
          <div className="space-y-4">
            <Label className="text-sm font-semibold">Visitante (Fora)</Label>
            <Select value={simVisitante} onValueChange={handleVisitanteChange}>
              <SelectTrigger>
                <SelectValue placeholder="Selecione o time visitante" />
              </SelectTrigger>
              <SelectContent>
                {timesDisponiveis
                  .filter(t => t.abrev !== simMandante)
                  .map(t => (
                    <SelectItem key={t.abrev} value={t.abrev}>
                      {t.nome} ({t.abrev})
                    </SelectItem>
                  ))}
              </SelectContent>
            </Select>
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-muted-foreground">Força</span>
                <span className="text-sm font-bold text-primary">{simForcaVisitante}</span>
              </div>
              <Slider
                value={[simForcaVisitante]}
                onValueChange={(v) => setSimForcaVisitante(v[0])}
                min={0}
                max={100}
                step={1}
              />
            </div>
          </div>
        </div>

        <Button
          className="w-full"
          disabled={!simMandante || !simVisitante || simMandante === simVisitante || previsaoCustomizada.isPending}
          onClick={handleSimular}
        >
          {previsaoCustomizada.isPending ? (
            <><Loader2 className="w-4 h-4 animate-spin mr-2" /> Simulando...</>
          ) : (
            <><Swords className="w-4 h-4 mr-2" /> Simular Confronto</>
          )}
        </Button>

        {/* Resultado da simulação */}
        {previsaoCustomizada.data && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-6 p-4 rounded-lg bg-card border border-border"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex-1 text-right">
                <div className="font-semibold">{previsaoCustomizada.data.mandante}</div>
                <div className="text-xs text-muted-foreground">Casa</div>
              </div>
              <div className="px-6 py-3 mx-4 rounded-lg bg-primary/10 border border-primary/20">
                <div className="text-2xl font-bold text-center text-primary">
                  {previsaoCustomizada.data.placarProvavel}
                </div>
                <div className="text-xs text-center text-muted-foreground">
                  {previsaoCustomizada.data.probabilidadePlacar.toFixed(1)}%
                </div>
              </div>
              <div className="flex-1">
                <div className="font-semibold">{previsaoCustomizada.data.visitante}</div>
                <div className="text-xs text-muted-foreground">Fora</div>
              </div>
            </div>

            <div className="flex items-center justify-between mb-3 text-xs">
              <span className="text-muted-foreground">xG: <strong>{previsaoCustomizada.data.xgMandante.toFixed(2)}</strong></span>
              <span className="text-muted-foreground">xG: <strong>{previsaoCustomizada.data.xgVisitante.toFixed(2)}</strong></span>
            </div>

            <div className="grid grid-cols-3 gap-2 mb-3">
              <div className="text-center p-2 rounded bg-success/10 border border-success/20">
                <div className="text-xs text-muted-foreground">Casa</div>
                <div className="font-bold text-success">{previsaoCustomizada.data.probVitoriaCasa.toFixed(1)}%</div>
              </div>
              <div className="text-center p-2 rounded bg-warning/10 border border-warning/20">
                <div className="text-xs text-muted-foreground">Empate</div>
                <div className="font-bold text-warning">{previsaoCustomizada.data.probEmpate.toFixed(1)}%</div>
              </div>
              <div className="text-center p-2 rounded bg-info/10 border border-info/20">
                <div className="text-xs text-muted-foreground">Fora</div>
                <div className="font-bold text-info">{previsaoCustomizada.data.probVitoriaFora.toFixed(1)}%</div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="flex items-center justify-between p-2 rounded bg-muted/50">
                <span className="text-muted-foreground">+2.5 gols</span>
                <span className="font-bold">{previsaoCustomizada.data.over25.toFixed(1)}%</span>
              </div>
              <div className="flex items-center justify-between p-2 rounded bg-muted/50">
                <span className="text-muted-foreground">Ambos marcam</span>
                <span className="font-bold">{previsaoCustomizada.data.btts.toFixed(1)}%</span>
              </div>
            </div>

            {previsaoCustomizada.data.topPlacares && previsaoCustomizada.data.topPlacares.length > 1 && (
              <div className="mt-3 pt-3 border-t border-border">
                <div className="text-[10px] text-muted-foreground mb-1">Placares alternativos:</div>
                <div className="flex gap-2 flex-wrap">
                  {previsaoCustomizada.data.topPlacares.slice(1, 5).map((placar, i) => (
                    <span key={i} className="text-xs px-2 py-1 rounded bg-muted text-muted-foreground">
                      {placar.placar} <span className="font-bold">({placar.probabilidade.toFixed(1)}%)</span>
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="mt-3 flex items-center justify-between">
              <span className="text-[10px] text-muted-foreground">
                {previsaoCustomizada.data.metodologia}
              </span>
              <div className="flex items-center gap-2">
                <div className="w-20 h-1.5 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary rounded-full"
                    style={{ width: `${previsaoCustomizada.data.confianca}%` }}
                  />
                </div>
                <span className="text-xs font-bold text-primary">{previsaoCustomizada.data.confianca.toFixed(0)}%</span>
              </div>
            </div>
          </motion.div>
        )}

        {previsaoCustomizada.isError && (
          <Alert variant="destructive" className="mt-4">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>Erro ao simular confronto. Tente novamente.</AlertDescription>
          </Alert>
        )}
      </motion.div>

      {/* Desfalques da Rodada */}
      {noticiasData && noticiasData.clubes && noticiasData.clubes.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card p-6 mb-8"
        >
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-warning" />
              <h2 className="font-display text-xl font-bold">Desfalques Confirmados</h2>
            </div>
            <div className="flex gap-2 text-xs">
              <span className="px-2 py-1 rounded bg-destructive/20 text-destructive">
                {noticiasData.resumo.total_lesionados} Lesionados
              </span>
              <span className="px-2 py-1 rounded bg-warning/20 text-warning">
                {noticiasData.resumo.total_suspensos} Suspensos
              </span>
              <span className="px-2 py-1 rounded bg-info/20 text-info">
                {noticiasData.resumo.total_duvidas} Dúvidas
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {noticiasData.clubes
              .filter(clube => clube.total_desfalques > 0)
              .map((clube, index) => (
                <motion.div
                  key={clube.clube_id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="glass-card p-4"
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="font-semibold">{clube.clube_abrev}</div>
                    <span className="text-xs px-2 py-1 rounded bg-destructive/20 text-destructive font-bold">
                      {clube.total_desfalques} desfalques
                    </span>
                  </div>

                  {clube.lesionados.length > 0 && (
                    <div className="mb-2">
                      <div className="text-xs text-muted-foreground mb-1">🔴 Lesionados:</div>
                      <div className="flex flex-wrap gap-1">
                        {clube.lesionados.map((jogador, i) => (
                          <span key={i} className="text-xs px-2 py-0.5 rounded bg-destructive/10 text-destructive">
                            {jogador}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {clube.suspensos.length > 0 && (
                    <div className="mb-2">
                      <div className="text-xs text-muted-foreground mb-1">🟡 Suspensos:</div>
                      <div className="flex flex-wrap gap-1">
                        {clube.suspensos.map((jogador, i) => (
                          <span key={i} className="text-xs px-2 py-0.5 rounded bg-warning/10 text-warning">
                            {jogador}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {clube.duvidas.length > 0 && (
                    <div className="mb-2">
                      <div className="text-xs text-muted-foreground mb-1">💭 Dúvidas:</div>
                      <div className="flex flex-wrap gap-1">
                        {clube.duvidas.map((jogador, i) => (
                          <span key={i} className="text-xs px-2 py-0.5 rounded bg-info/10 text-info">
                            {jogador}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </motion.div>
              ))}
          </div>
        </motion.div>
      )}

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

      {/* Disclaimer */}
      <Disclaimer />
    </MainLayout>
  );
};

export default Confrontos;