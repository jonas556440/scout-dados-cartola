import { MainLayout } from "@/components/layout/MainLayout";
import { useClassificacao, useAcuracia } from "@/hooks/useCartolaApi";
import { motion } from "framer-motion";
import { Trophy, TrendingUp, TrendingDown, AlertCircle, Loader2, Target, Shield, Calendar, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { useMemo } from "react";
import { Link } from "react-router-dom";
import { SEO } from "@/components/SEO";
import { Disclaimer } from "@/components/Disclaimer";
import { ColorLegend } from "@/components/ui/color-legend";
import { TermTooltip } from "@/components/ui/term-tooltip";
import { HelpSection } from "@/components/ui/help-section";
import { IconWithTooltip } from "@/components/ui/icon-with-tooltip";
import { getTeamSlug } from "@/lib/teams";

const Brasileirao = () => {
  const { data: classificacaoData, isLoading, error } = useClassificacao();
  const { data: acuraciaData, isLoading: isLoadingAcuracia } = useAcuracia();

  const classificacao = useMemo(() => {
    return classificacaoData?.classificacao || [];
  }, [classificacaoData]);

  const simulacaoMap = useMemo(() => {
    if (!classificacaoData?.simulacao) return new Map();
    const map = new Map<number, typeof classificacaoData.simulacao[0]>();
    for (const s of classificacaoData.simulacao) {
      map.set(s.id, s);
    }
    return map;
  }, [classificacaoData]);

  const proximosJogos = classificacaoData?.proximosJogos || [];
  const jogosRealizados = classificacaoData?.jogosRealizados || [];

  if (error) {
    return (
      <MainLayout>
        <SEO title="Brasileirão 2026" description="Classificação do Brasileirão 2026 com simulação Monte Carlo." path="/brasileirao" />
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
        <SEO title="Brasileirão 2026" description="Classificação do Brasileirão 2026 com simulação Monte Carlo." path="/brasileirao" />
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
        title="Brasileirão 2026 - Classificação e Probabilidades"
        description="Classificação do Brasileirão 2026 com probabilidades de título, Libertadores, Sul-Americana e rebaixamento. Previsões para os próximos jogos."
        path="/brasileirao"
      />
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6"
      >
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 hero-gradient rounded-lg">
            <Trophy className="w-6 h-6 text-primary-foreground" />
          </div>
          <div>
            <h1 className="font-display text-2xl md:text-4xl font-bold">
              Campeonato Brasileiro 2026 - Série A
            </h1>
            <div className="flex items-center gap-3">
              <p className="text-muted-foreground text-sm">
                Rodada {classificacaoData?.rodada || '?'} • Classificação e Probabilidades
              </p>
              <span className="text-xs px-2 py-1 rounded-full bg-success/20 text-success font-semibold">
                ✅ Atualizado
              </span>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Legenda de cores */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="mb-4"
      >
        <ColorLegend />
      </motion.div>

      <Tabs defaultValue="classificacao" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="classificacao">
            <IconWithTooltip icon={<Shield className="w-4 h-4 mr-2" />} tooltip="Classificação com probabilidades" side="bottom" />
            Classificação
          </TabsTrigger>
          <TabsTrigger value="pontos-necessarios">
            <IconWithTooltip icon={<TrendingUp className="w-4 h-4 mr-2" />} tooltip="Pontos necessários para objetivos" side="bottom" />
            Pontos Necessários
          </TabsTrigger>
          <TabsTrigger value="acuracia">
            <IconWithTooltip icon={<Target className="w-4 h-4 mr-2" />} tooltip="Precisão das previsões por rodada" side="bottom" />
            Acurácia
          </TabsTrigger>
        </TabsList>

        {/* ===== CLASSIFICAÇÃO UNIFICADA COM PROBABILIDADES ===== */}
        <TabsContent value="classificacao">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-card p-4 md:p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-display text-lg md:text-xl font-bold">
                Classificação e Probabilidades
              </h2>
              {classificacaoData?.simulacao && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <span className="text-xs px-3 py-1 rounded-full bg-primary/20 text-primary font-semibold cursor-help">
                      500 simulações • <TermTooltip term="monte-carlo">Monte Carlo</TermTooltip>
                    </span>
                  </TooltipTrigger>
                  <TooltipContent className="max-w-xs">
                    <p className="text-sm">Probabilidades calculadas via 500 simulações Monte Carlo com modelo Poisson calibrado.</p>
                  </TooltipContent>
                </Tooltip>
              )}
            </div>

            <div className="overflow-x-auto">
              <table className="stats-table w-full">
                <thead>
                  <tr>
                    <th className="text-left text-xs">Pos</th>
                    <th className="text-left text-xs">Time</th>
                    <th className="text-center text-xs" title="Pontos">Pts</th>
                    <th className="text-center text-xs" title="Jogos">J</th>
                    <th className="text-center text-xs hidden md:table-cell" title="Vitórias">V</th>
                    <th className="text-center text-xs hidden md:table-cell" title="Empates">E</th>
                    <th className="text-center text-xs hidden md:table-cell" title="Derrotas">D</th>
                    <th className="text-center text-xs hidden lg:table-cell" title="Gols Pró">GP</th>
                    <th className="text-center text-xs hidden lg:table-cell" title="Gols Contra">GC</th>
                    <th className="text-center text-xs hidden md:table-cell">
                      <TermTooltip term="sg">SG</TermTooltip>
                    </th>
                    <th className="text-center text-xs hidden lg:table-cell">
                      <TermTooltip term="forma">Forma</TermTooltip>
                    </th>
                    {/* Separador visual - Probabilidades */}
                    <th className="text-center text-xs border-l border-border/50 px-1">
                      <span className="flex items-center justify-center gap-0.5">
                        <Trophy className="w-3 h-3 text-primary" />
                        <span className="hidden sm:inline">Título</span>
                        <span className="sm:hidden">Tít</span>
                      </span>
                    </th>
                    <th className="text-center text-xs px-1">
                      <span className="flex items-center justify-center gap-0.5">
                        <TrendingUp className="w-3 h-3 text-info" />
                        <span className="hidden sm:inline">Libertadores</span>
                        <span className="sm:hidden">Lib</span>
                      </span>
                    </th>
                    <th className="text-center text-xs px-1">
                      <span className="hidden sm:inline">Sul-Americana</span>
                      <span className="sm:hidden">Sula</span>
                    </th>
                    <th className="text-center text-xs px-1">
                      <span className="flex items-center justify-center gap-0.5">
                        <TrendingDown className="w-3 h-3 text-destructive" />
                        <span className="hidden sm:inline">Rebaixamento</span>
                        <span className="sm:hidden">Z4</span>
                      </span>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {classificacao.map((time, index) => {
                    const sim = simulacaoMap.get(time.id);
                    return (
                      <motion.tr
                        key={time.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.02 }}
                        className={cn(
                          "hover:bg-accent/50 transition-colors",
                          index < 4 && "border-l-2 border-l-primary",
                          index >= 4 && index < 6 && "border-l-2 border-l-info",
                          index >= 6 && index < 12 && "border-l-2 border-l-warning",
                          index >= 16 && "border-l-2 border-l-destructive"
                        )}
                      >
                        <td>
                          <span className={cn(
                            "w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold",
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
                          <Link
                            to={`/brasileirao/time/${getTeamSlug(time.abrev)}`}
                            className="flex items-center gap-2 group"
                          >
                            {time.escudo && (
                              <img src={time.escudo} alt={time.abrev} className="w-5 h-5" />
                            )}
                            <span className="font-semibold text-xs md:text-sm text-primary group-hover:text-primary/80 underline decoration-dotted decoration-1 underline-offset-2 transition-colors">
                              {time.nome || time.abrev}
                            </span>
                          </Link>
                        </td>
                        <td className="text-center font-bold text-sm md:text-base">{time.pontos}</td>
                        <td className="text-center text-xs md:text-sm">{time.jogos}</td>
                        <td className="text-center text-success text-xs hidden md:table-cell">{time.vitorias}</td>
                        <td className="text-center text-warning text-xs hidden md:table-cell">{time.empates}</td>
                        <td className="text-center text-destructive text-xs hidden md:table-cell">{time.derrotas}</td>
                        <td className="text-center text-xs hidden lg:table-cell">{time.gols_pro}</td>
                        <td className="text-center text-xs hidden lg:table-cell">{time.gols_contra}</td>
                        <td className="text-center text-xs font-semibold hidden md:table-cell">
                          <span className={cn(
                            time.saldo_gols > 0 ? "text-success" :
                            time.saldo_gols < 0 ? "text-destructive" :
                            "text-muted-foreground"
                          )}>
                            {time.saldo_gols > 0 ? `+${time.saldo_gols}` : time.saldo_gols}
                          </span>
                        </td>
                        <td className="text-center hidden lg:table-cell">
                          <div className="flex gap-0.5 justify-center">
                            {(time.forma || "").split("").slice(-5).map((r, i) => (
                              <span key={i} className={cn(
                                "w-4 h-4 rounded-sm flex items-center justify-center text-[9px] font-bold text-white",
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

                        {/* Colunas de probabilidade */}
                        <td className="text-center border-l border-border/50">
                          {sim && sim.probTitulo > 0 ? (
                            <span className={cn(
                              "px-1.5 py-0.5 rounded text-[10px] md:text-xs font-bold",
                              sim.probTitulo > 20 ? "bg-primary/20 text-primary" :
                              sim.probTitulo > 5 ? "bg-primary/10 text-primary/70" :
                              "text-muted-foreground"
                            )}>
                              {sim.probTitulo.toFixed(1)}%
                            </span>
                          ) : (
                            <span className="text-muted-foreground text-[10px]">
                              {sim ? (sim.probTitulo < 0.1 ? "~0%" : "-") : "-"}
                            </span>
                          )}
                        </td>
                        <td className="text-center">
                          {sim ? (
                            <span className={cn(
                              "text-[10px] md:text-xs font-semibold",
                              sim.probLibertadores > 50 ? "text-success" :
                              sim.probLibertadores > 20 ? "text-info" :
                              "text-muted-foreground"
                            )}>
                              {sim.probLibertadores.toFixed(1)}%
                            </span>
                          ) : <span className="text-muted-foreground text-[10px]">-</span>}
                        </td>
                        <td className="text-center">
                          {sim ? (
                            <span className="text-[10px] md:text-xs text-warning font-semibold">
                              {sim.probSulamericana > 0 ? `${sim.probSulamericana.toFixed(1)}%` : '-'}
                            </span>
                          ) : <span className="text-muted-foreground text-[10px]">-</span>}
                        </td>
                        <td className="text-center">
                          {sim && sim.probRebaixamento > 0 ? (
                            <span className={cn(
                              "px-1.5 py-0.5 rounded text-[10px] md:text-xs font-bold",
                              sim.probRebaixamento > 30 ? "bg-destructive/20 text-destructive" :
                              sim.probRebaixamento > 10 ? "bg-destructive/10 text-destructive/70" :
                              "text-muted-foreground"
                            )}>
                              {sim.probRebaixamento.toFixed(1)}%
                            </span>
                          ) : (
                            <span className="text-muted-foreground text-[10px]">
                              {sim ? (sim.probRebaixamento < 0.1 ? "~0%" : "-") : "-"}
                            </span>
                          )}
                        </td>
                      </motion.tr>
                    );
                  })}
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
            <p className="text-xs text-muted-foreground mt-2">
              A coluna "Libertadores" refere-se à chance de terminar nas 6 primeiras colocações.
              "Sul-Americana" à probabilidade de terminar entre o 7º e 12º lugares.
            </p>
          </motion.div>

          {/* ===== PRÓXIMOS JOGOS ===== */}
          {proximosJogos.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15 }}
              className="glass-card p-4 md:p-6 mt-6"
            >
              <div className="flex items-center gap-2 mb-4">
                <Calendar className="w-5 h-5 text-primary" />
                <h2 className="font-display text-lg md:text-xl font-bold">
                  Probabilidades para os próximos jogos
                </h2>
              </div>

              <div className="overflow-x-auto">
                <table className="stats-table w-full">
                  <thead>
                    <tr>
                      <th className="text-left text-xs">Data</th>
                      <th className="text-left text-xs">Mandante</th>
                      <th className="text-left text-xs">Visitante</th>
                      <th className="text-center text-xs">
                        <span className="text-success">Vitória do<br className="hidden sm:inline" /> mandante</span>
                      </th>
                      <th className="text-center text-xs">
                        <span className="text-warning">Empate</span>
                      </th>
                      <th className="text-center text-xs">
                        <span className="text-info">Vitória do<br className="hidden sm:inline" /> visitante</span>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {proximosJogos.map((jogo, index) => {
                      const dataFormatada = jogo.dataHora
                        ? new Date(jogo.dataHora).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' })
                        : '-';
                      return (
                        <motion.tr
                          key={`prox-${jogo.mandante}-${jogo.visitante}`}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: index * 0.03 }}
                          className="hover:bg-accent/50 transition-colors"
                        >
                          <td className="text-xs text-muted-foreground whitespace-nowrap">{dataFormatada}</td>
                          <td className="font-semibold text-xs md:text-sm">{jogo.mandanteNome || jogo.mandante}</td>
                          <td className="text-xs md:text-sm">{jogo.visitanteNome || jogo.visitante}</td>
                          <td className="text-center">
                            <span className={cn(
                              "text-xs md:text-sm font-bold",
                              jogo.probVitoriaMandante && jogo.probVitoriaMandante > 50 ? "text-success" : "text-muted-foreground"
                            )}>
                              {jogo.probVitoriaMandante != null ? `${jogo.probVitoriaMandante.toFixed(1)}%` : '-'}
                            </span>
                          </td>
                          <td className="text-center">
                            <span className="text-xs md:text-sm font-bold text-warning">
                              {jogo.probEmpate != null ? `${jogo.probEmpate.toFixed(1)}%` : '-'}
                            </span>
                          </td>
                          <td className="text-center">
                            <span className={cn(
                              "text-xs md:text-sm font-bold",
                              jogo.probVitoriaVisitante && jogo.probVitoriaVisitante > 50 ? "text-info" : "text-muted-foreground"
                            )}>
                              {jogo.probVitoriaVisitante != null ? `${jogo.probVitoriaVisitante.toFixed(1)}%` : '-'}
                            </span>
                          </td>
                        </motion.tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </motion.div>
          )}

          {/* ===== JOGOS REALIZADOS ===== */}
          {jogosRealizados.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="glass-card p-4 md:p-6 mt-6"
            >
              <div className="flex items-center gap-2 mb-4">
                <CheckCircle2 className="w-5 h-5 text-success" />
                <h2 className="font-display text-lg md:text-xl font-bold">
                  Jogos realizados
                </h2>
              </div>

              <div className="overflow-x-auto">
                <table className="stats-table w-full">
                  <thead>
                    <tr>
                      <th className="text-left text-xs">Data</th>
                      <th className="text-left text-xs">Mandante</th>
                      <th className="text-center text-xs"></th>
                      <th className="text-left text-xs">Visitante</th>
                      <th className="text-center text-xs">
                        <span className="text-success">Vitória do<br className="hidden sm:inline" /> mandante</span>
                      </th>
                      <th className="text-center text-xs">
                        <span className="text-warning">Empate</span>
                      </th>
                      <th className="text-center text-xs">
                        <span className="text-info">Vitória do<br className="hidden sm:inline" /> visitante</span>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {jogosRealizados.map((jogo, index) => {
                      const dataFormatada = jogo.dataHora
                        ? new Date(jogo.dataHora).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' })
                        : '-';

                      // Determinar resultado
                      const golsM = jogo.placarMandante ?? 0;
                      const golsV = jogo.placarVisitante ?? 0;
                      let resultadoReal: 'mandante' | 'empate' | 'visitante' = 'empate';
                      if (golsM > golsV) resultadoReal = 'mandante';
                      else if (golsV > golsM) resultadoReal = 'visitante';

                      return (
                        <motion.tr
                          key={`real-${jogo.mandante}-${jogo.visitante}`}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: index * 0.03 }}
                          className="hover:bg-accent/50 transition-colors"
                        >
                          <td className="text-xs text-muted-foreground whitespace-nowrap">{dataFormatada}</td>
                          <td className="font-semibold text-xs md:text-sm">{jogo.mandanteNome || jogo.mandante}</td>
                          <td className="text-center">
                            <span className="text-sm font-bold px-2 py-1 rounded bg-muted">
                              {jogo.placarMandante}x{jogo.placarVisitante}
                            </span>
                          </td>
                          <td className="text-xs md:text-sm">{jogo.visitanteNome || jogo.visitante}</td>
                          <td className="text-center">
                            <span className={cn(
                              "text-xs font-semibold",
                              resultadoReal === 'mandante' ? "text-success font-bold" : "text-muted-foreground"
                            )}>
                              {jogo.probVitoriaMandante != null ? `${jogo.probVitoriaMandante.toFixed(1)}%` : '-'}
                            </span>
                          </td>
                          <td className="text-center">
                            <span className={cn(
                              "text-xs font-semibold",
                              resultadoReal === 'empate' ? "text-warning font-bold" : "text-muted-foreground"
                            )}>
                              {jogo.probEmpate != null ? `${jogo.probEmpate.toFixed(1)}%` : '-'}
                            </span>
                          </td>
                          <td className="text-center">
                            <span className={cn(
                              "text-xs font-semibold",
                              resultadoReal === 'visitante' ? "text-info font-bold" : "text-muted-foreground"
                            )}>
                              {jogo.probVitoriaVisitante != null ? `${jogo.probVitoriaVisitante.toFixed(1)}%` : '-'}
                            </span>
                          </td>
                        </motion.tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </motion.div>
          )}
        </TabsContent>

        {/* ===== PONTOS NECESSÁRIOS ===== */}
        <TabsContent value="pontos-necessarios">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-card p-4 md:p-6"
          >
            <div className="flex items-center gap-2 mb-4">
              <TrendingUp className="w-5 h-5 text-primary" />
              <h2 className="font-display text-lg md:text-xl font-bold">
                Pontos Necessários para Objetivos
              </h2>
            </div>
            <p className="text-sm text-muted-foreground mb-4">
              Quantos pontos um time precisa somar até o final do campeonato para atingir cada objetivo, 
              com base em 500 simulações Monte Carlo. Leia: "Com X% de probabilidade, um time com Y pontos 
              atingiria o objetivo".
            </p>

            {classificacaoData?.pontosNecessarios && classificacaoData.pontosNecessarios.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border/50">
                      <th className="text-left py-3 px-3 font-semibold">Probabilidade</th>
                      <th className="text-center py-3 px-3 font-semibold">
                        <span className="inline-flex items-center gap-1">
                          <Trophy className="w-3.5 h-3.5 text-yellow-500" />
                          Título
                        </span>
                      </th>
                      <th className="text-center py-3 px-3 font-semibold">
                        <span className="inline-flex items-center gap-1">
                          <TrendingUp className="w-3.5 h-3.5 text-blue-500" />
                          Libertadores
                        </span>
                      </th>
                      <th className="text-center py-3 px-3 font-semibold">
                        <span className="inline-flex items-center gap-1">
                          <Shield className="w-3.5 h-3.5 text-orange-500" />
                          Sul-Americana
                        </span>
                      </th>
                      <th className="text-center py-3 px-3 font-semibold">
                        <span className="inline-flex items-center gap-1">
                          <TrendingDown className="w-3.5 h-3.5 text-green-500" />
                          Permanência
                        </span>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {classificacaoData.pontosNecessarios.map((pn, idx) => (
                      <motion.tr
                        key={pn.probabilidade}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: idx * 0.05 }}
                        className={cn(
                          "border-b border-border/20 hover:bg-muted/30 transition-colors",
                          pn.probabilidade >= 90 && "bg-primary/5"
                        )}
                      >
                        <td className="py-3 px-3">
                          <span className={cn(
                            "font-bold text-sm",
                            pn.probabilidade >= 95 ? "text-green-500" :
                            pn.probabilidade >= 80 ? "text-blue-500" :
                            "text-muted-foreground"
                          )}>
                            {pn.probabilidade}%
                          </span>
                        </td>
                        <td className="text-center py-3 px-3">
                          <span className="font-mono font-bold text-yellow-500">
                            {pn.titulo > 0 ? `${pn.titulo} pts` : "–"}
                          </span>
                        </td>
                        <td className="text-center py-3 px-3">
                          <span className="font-mono font-bold text-blue-500">
                            {pn.libertadores > 0 ? `${pn.libertadores} pts` : "–"}
                          </span>
                        </td>
                        <td className="text-center py-3 px-3">
                          <span className="font-mono font-bold text-orange-500">
                            {pn.sulamericana > 0 ? `${pn.sulamericana} pts` : "–"}
                          </span>
                        </td>
                        <td className="text-center py-3 px-3">
                          <span className="font-mono font-bold text-green-500">
                            {pn.permanencia > 0 ? `${pn.permanencia} pts` : "–"}
                          </span>
                        </td>
                      </motion.tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-12 text-muted-foreground">
                <TrendingUp className="w-12 h-12 mx-auto mb-4 opacity-30" />
                <p>Dados de pontos necessários não disponíveis</p>
                <p className="text-xs mt-1">Aguarde a conclusão da simulação Monte Carlo</p>
              </div>
            )}

            <div className="mt-4 text-xs text-muted-foreground">
              <p>
                <strong>Como ler:</strong> Na linha "90%", o valor na coluna "Libertadores" indica que, em 90% das simulações,
                um time com essa pontuação ou mais terminou no G-4. Quanto maior a probabilidade exigida, mais pontos são necessários.
              </p>
            </div>
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

      {/* Seção de ajuda */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="mt-8"
      >
        <HelpSection
          title="❓ Como interpretar os dados"
          items={[
            {
              term: "Faixas de Classificação",
              definition: "G-4 (1º a 4º): Vaga direta na fase de grupos da Libertadores. G-6 (5º e 6º): Vaga nas pré-eliminatórias da Libertadores. G-12 (7º a 12º): Vaga na Sul-Americana. Z-4 (17º a 20º): Rebaixamento para a Série B."
            },
            {
              term: "Simulação Monte Carlo",
              definition: "Algoritmo que simula o restante do campeonato 500 vezes com variações aleatórias realistas baseadas no modelo Poisson calibrado. As probabilidades mostradas são a porcentagem de cenários em que cada time conquistou o título, vaga na Libertadores, Sul-Americana ou foi rebaixado."
            },
            {
              term: "Probabilidades para próximos jogos",
              definition: "Previsões calculadas com modelo Poisson V4 + Dixon-Coles, considerando força ofensiva/defensiva, mando de campo e forma recente dos times."
            },
            {
              term: "Forma Recente",
              definition: "Mostra os últimos 5 jogos do time: V (Vitória), E (Empate), D (Derrota). Times com muitos 'V' estão em boa fase; muitos 'D' indicam má fase."
            },
            {
              term: "Clique nos times",
              definition: "Clique no nome de qualquer time para ver análise detalhada com probabilidades individuais, próximos 5 jogos com previsões, forma recente e estatísticas completas."
            }
          ]}
        />
      </motion.div>

      {/* Disclaimer */}
      <Disclaimer />
    </MainLayout>
  );
};

export default Brasileirao;
