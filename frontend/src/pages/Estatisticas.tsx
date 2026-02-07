import { MainLayout } from "@/components/layout/MainLayout";
import { useAtletas, useForcaTimes, useTimesXG } from "@/hooks/useCartolaApi";
import { motion } from "framer-motion";
import { useMemo } from "react";
import { Loader2, AlertCircle } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  BarChart3, 
  TrendingUp, 
  Target, 
  Users,
  Shield,
  Zap,
} from "lucide-react";
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from "recharts";
import type { Position } from "@/types/cartola";
import { POSITION_NAMES } from "@/types/cartola";
import { SEO } from "@/components/SEO";
import { Disclaimer } from "@/components/Disclaimer";

const Estatisticas = () => {
  const { data: atletas, isLoading, error } = useAtletas({ limite: 500 });
  const { data: forcaTimesData, isLoading: isLoadingForca } = useForcaTimes();
  const { data: xgData, isLoading: isLoadingXG } = useTimesXG();

  // Dados por posição
  const dadosPorPosicao = useMemo(() => {
    if (!atletas) return [];
    return (['GOL', 'ZAG', 'LAT', 'MEI', 'ATA'] as Position[]).map(pos => {
      const jogadores = atletas.filter(p => p.posicao === pos);
      return {
        posicao: pos,
        nome: POSITION_NAMES[pos],
        quantidade: jogadores.length,
        mediaPreco: jogadores.reduce((acc, p) => acc + p.preco, 0) / jogadores.length || 0,
      mediaPotencial: jogadores.reduce((acc, p) => acc + (p.potencial || 0), 0) / jogadores.length || 0,
    };
  });
  }, [atletas]);

  // Dados para radar chart
  const radarData = useMemo(() => {
    if (!dadosPorPosicao.length) return [];
    return dadosPorPosicao.map(d => ({
      posicao: d.posicao,
      potencial: d.mediaPotencial,
      preco: d.mediaPreco,
    }));
  }, [dadosPorPosicao]);

  // Cores para pie chart
  const COLORS = ['hsl(200, 80%, 55%)', 'hsl(280, 70%, 55%)', 'hsl(320, 70%, 55%)', 'hsl(45, 93%, 58%)', 'hsl(0, 70%, 55%)'];

  // Top times por força (usando API real)
  const topTimes = useMemo(() => {
    if (!forcaTimesData || !forcaTimesData.times) return [];
    
    return forcaTimesData.times
      .slice(0, 10) // Top 10 times
      .map(time => ({
        nome: time.abrev,
        forcaCasa: time.forcaCasa,
        forcaFora: time.forcaFora,
        posicao: time.posicao,
        jogos: time.jogos,
        vitorias: time.vitorias,
        empates: time.empates,
        derrotas: time.derrotas,
      }));
  }, [forcaTimesData]);

  if (isLoading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-96">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      </MainLayout>
    );
  }

  if (error) {
    return (
      <MainLayout>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Erro ao carregar estatísticas</AlertTitle>
          <AlertDescription>
            Não foi possível obter os dados da API. Verifique se o servidor está rodando.
          </AlertDescription>
        </Alert>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <SEO title="Estatísticas" description="Estatísticas completas do mercado Cartola FC e xG do Brasileirão 2026." path="/estatisticas" />
      
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 hero-gradient rounded-lg">
            <BarChart3 className="w-6 h-6 text-primary-foreground" />
          </div>
          <div>
            <h1 className="font-display text-3xl md:text-4xl font-bold">
              Estatísticas
            </h1>
            <p className="text-muted-foreground">
              Análise detalhada do mercado, times e xG
            </p>
          </div>
        </div>
      </motion.div>

      <Tabs defaultValue="visao-geral" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3 max-w-md">
          <TabsTrigger value="visao-geral">Visão Geral</TabsTrigger>
          <TabsTrigger value="xg">xG (Expected Goals)</TabsTrigger>
          <TabsTrigger value="forca">Força dos Times</TabsTrigger>
        </TabsList>

        {/* ====== TAB: VISÃO GERAL ====== */}
        <TabsContent value="visao-geral" className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Jogadores por Posição */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="chart-container"
        >
          <div className="flex items-center gap-2 mb-4">
            <Users className="w-5 h-5 text-primary" />
            <h3 className="font-display text-lg font-bold">Jogadores por Posição</h3>
          </div>
          
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={dadosPorPosicao}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  fill="#8884d8"
                  paddingAngle={5}
                  dataKey="quantidade"
                  label={({ posicao, quantidade }) => `${posicao}: ${quantidade}`}
                >
                  {dadosPorPosicao.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(220, 18%, 12%)',
                    border: '1px solid hsl(220, 14%, 18%)',
                    borderRadius: '8px',
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Média de Potencial por Posição */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="chart-container"
        >
          <div className="flex items-center gap-2 mb-4">
            <Zap className="w-5 h-5 text-secondary" />
            <h3 className="font-display text-lg font-bold">Potencial por Posição</h3>
          </div>
          
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
                <PolarGrid stroke="hsl(220, 14%, 18%)" />
                <PolarAngleAxis dataKey="posicao" tick={{ fill: 'hsl(215, 20%, 55%)', fontSize: 12 }} />
                <PolarRadiusAxis 
                  angle={30} 
                  domain={[0, 100]} 
                  tick={{ fill: 'hsl(215, 20%, 55%)', fontSize: 10 }}
                />
                <Radar
                  name="Potencial"
                  dataKey="potencial"
                  stroke="hsl(142, 76%, 45%)"
                  fill="hsl(142, 76%, 45%)"
                  fillOpacity={0.3}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(220, 18%, 12%)',
                    border: '1px solid hsl(220, 14%, 18%)',
                    borderRadius: '8px',
                  }}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Preço Médio por Posição */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="chart-container"
        >
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-5 h-5 text-primary" />
            <h3 className="font-display text-lg font-bold">Preço Médio por Posição</h3>
          </div>
          
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={dadosPorPosicao}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 14%, 18%)" />
                <XAxis dataKey="posicao" stroke="hsl(215, 20%, 55%)" fontSize={12} />
                <YAxis stroke="hsl(215, 20%, 55%)" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(220, 18%, 12%)',
                    border: '1px solid hsl(220, 14%, 18%)',
                    borderRadius: '8px',
                  }}
                  formatter={(value: number) => [`C$${value.toFixed(1)}`, 'Preço Médio']}
                />
                <Bar dataKey="mediaPreco" fill="hsl(142, 76%, 45%)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Força dos Times */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="chart-container"
        >
          <div className="flex items-center gap-2 mb-4">
            <Shield className="w-5 h-5 text-primary" />
            <h3 className="font-display text-lg font-bold">Força dos Times (Top 5)</h3>
          </div>
          
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={topTimes} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(220, 14%, 18%)" />
                <XAxis type="number" stroke="hsl(215, 20%, 55%)" fontSize={12} domain={[0, 100]} />
                <YAxis dataKey="nome" type="category" stroke="hsl(215, 20%, 55%)" fontSize={12} width={50} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(220, 18%, 12%)',
                    border: '1px solid hsl(220, 14%, 18%)',
                    borderRadius: '8px',
                  }}
                />
                <Bar dataKey="forcaCasa" fill="hsl(142, 76%, 45%)" name="Casa" radius={[0, 4, 4, 0]} />
                <Bar dataKey="forcaFora" fill="hsl(45, 93%, 58%)" name="Fora" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          
          <div className="flex items-center justify-center gap-6 mt-4">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-primary" />
              <span className="text-sm text-muted-foreground">Casa</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-secondary" />
              <span className="text-sm text-muted-foreground">Fora</span>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Tabela Completa de Força dos Times */}
      </TabsContent>

      {/* ====== TAB: xG (EXPECTED GOALS) ====== */}
      <TabsContent value="xg" className="space-y-6">
        {isLoadingXG ? (
          <div className="space-y-2">
            {[...Array(10)].map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        ) : xgData ? (
          <>
            {/* Próximos Jogos com xG */}
            {xgData.proximosJogos.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="chart-container"
              >
                <div className="flex items-center gap-2 mb-4">
                  <Target className="w-5 h-5 text-primary" />
                  <h2 className="font-display text-xl font-bold">xG: Próximos Jogos da Rodada</h2>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-border">
                        <th className="text-left p-3 text-sm font-medium text-muted-foreground">Jogo</th>
                        <th className="text-center p-3 text-sm font-medium text-muted-foreground">xG Casa</th>
                        <th className="text-center p-3 text-sm font-medium text-muted-foreground">xG Fora</th>
                        <th className="text-center p-3 text-sm font-medium text-muted-foreground">Total</th>
                        <th className="text-center p-3 text-sm font-medium text-muted-foreground">Placar</th>
                        <th className="text-center p-3 text-sm font-medium text-muted-foreground">Over 2.5</th>
                        <th className="text-center p-3 text-sm font-medium text-muted-foreground">BTTS</th>
                      </tr>
                    </thead>
                    <tbody>
                      {xgData.proximosJogos.map((jogo, i) => (
                        <tr key={i} className="border-b border-border/50 hover:bg-accent/50 transition-colors">
                          <td className="p-3 font-medium">{jogo.mandante} x {jogo.visitante}</td>
                          <td className="p-3 text-center">
                            <span className="inline-flex items-center justify-center px-2.5 py-1 rounded-md bg-primary/20 text-primary font-semibold text-sm">
                              {jogo.xgMandante.toFixed(2)}
                            </span>
                          </td>
                          <td className="p-3 text-center">
                            <span className="inline-flex items-center justify-center px-2.5 py-1 rounded-md bg-blue-500/20 text-blue-400 font-semibold text-sm">
                              {jogo.xgVisitante.toFixed(2)}
                            </span>
                          </td>
                          <td className="p-3 text-center font-semibold">{jogo.totalXg.toFixed(2)}</td>
                          <td className="p-3 text-center font-bold text-primary">{jogo.placarProvavel}</td>
                          <td className="p-3 text-center">
                            <span className={`text-sm font-medium ${jogo.over25 > 50 ? 'text-green-400' : 'text-red-400'}`}>
                              {jogo.over25}%
                            </span>
                          </td>
                          <td className="p-3 text-center">
                            <span className={`text-sm font-medium ${jogo.btts > 50 ? 'text-green-400' : 'text-red-400'}`}>
                              {jogo.btts}%
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </motion.div>
            )}

            {/* Ranking xG por Time */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="chart-container"
            >
              <div className="flex items-center gap-2 mb-4">
                <Zap className="w-5 h-5 text-primary" />
                <h2 className="font-display text-xl font-bold">xG por Time — Geral / Casa / Fora</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="text-left p-3 text-sm font-medium text-muted-foreground">#</th>
                      <th className="text-left p-3 text-sm font-medium text-muted-foreground">Time</th>
                      <th className="text-center p-3 text-sm font-medium text-muted-foreground">xG Geral</th>
                      <th className="text-center p-3 text-sm font-medium text-muted-foreground">xG Casa</th>
                      <th className="text-center p-3 text-sm font-medium text-muted-foreground">xG Fora</th>
                      <th className="text-center p-3 text-sm font-medium text-muted-foreground">xGA Geral</th>
                      <th className="text-center p-3 text-sm font-medium text-muted-foreground">GP</th>
                      <th className="text-center p-3 text-sm font-medium text-muted-foreground">GC</th>
                      <th className="text-center p-3 text-sm font-medium text-muted-foreground">Força</th>
                    </tr>
                  </thead>
                  <tbody>
                    {xgData.rankingXG.map((time, index) => (
                      <tr key={time.id} className="border-b border-border/50 hover:bg-accent/50 transition-colors">
                        <td className="p-3 text-sm text-muted-foreground">{index + 1}</td>
                        <td className="p-3">
                          <div className="flex items-center gap-2">
                            <div className="w-7 h-7 rounded-full bg-accent flex items-center justify-center">
                              <span className="text-[10px] font-bold">{time.abrev}</span>
                            </div>
                            <span className="font-medium text-sm">{time.abrev}</span>
                          </div>
                        </td>
                        <td className="p-3 text-center">
                          <span className="inline-flex items-center justify-center px-2 py-1 rounded-md bg-green-500/20 text-green-400 font-bold text-sm">
                            {time.xgGeral.toFixed(2)}
                          </span>
                        </td>
                        <td className="p-3 text-center text-sm">{time.xgCasa.toFixed(2)}</td>
                        <td className="p-3 text-center text-sm">{time.xgFora.toFixed(2)}</td>
                        <td className="p-3 text-center">
                          <span className="inline-flex items-center justify-center px-2 py-1 rounded-md bg-red-500/20 text-red-400 font-bold text-sm">
                            {time.xgaGeral.toFixed(2)}
                          </span>
                        </td>
                        <td className="p-3 text-center text-sm">{time.golsPro}</td>
                        <td className="p-3 text-center text-sm">{time.golsContra}</td>
                        <td className="p-3 text-center text-sm">{time.forcaGeral.toFixed(0)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="text-xs text-muted-foreground mt-4">
                {xgData.metodologia}
              </p>
            </motion.div>
          </>
        ) : (
          <div className="text-center py-8 text-muted-foreground">
            Sem dados de xG disponíveis
          </div>
        )}
      </TabsContent>

      {/* ====== TAB: FORÇA DOS TIMES ====== */}
      <TabsContent value="forca" className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="chart-container mb-8"
      >
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-primary" />
            <h2 className="font-display text-xl font-bold">Força dos Times</h2>
          </div>
          {forcaTimesData && (
            <span className="text-xs text-muted-foreground">
              {forcaTimesData.metodologia}
            </span>
          )}
        </div>

        {isLoadingForca ? (
          <div className="space-y-2">
            {[...Array(20)].map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        ) : forcaTimesData && forcaTimesData.times ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left p-3 text-sm font-medium text-muted-foreground"></th>
                  <th className="text-left p-3 text-sm font-medium text-muted-foreground">Time</th>
                  <th className="text-center p-3 text-sm font-medium text-muted-foreground">Pos</th>
                  <th className="text-center p-3 text-sm font-medium text-muted-foreground">J</th>
                  <th className="text-center p-3 text-sm font-medium text-muted-foreground">V</th>
                  <th className="text-center p-3 text-sm font-medium text-muted-foreground">E</th>
                  <th className="text-center p-3 text-sm font-medium text-muted-foreground">D</th>
                  <th className="text-center p-3 text-sm font-medium text-muted-foreground">Força Casa</th>
                  <th className="text-center p-3 text-sm font-medium text-muted-foreground">Força Fora</th>
                </tr>
              </thead>
              <tbody>
                {forcaTimesData.times.map((time, index) => (
                  <tr 
                    key={time.id} 
                    className="border-b border-border/50 hover:bg-accent/50 transition-colors"
                  >
                    <td className="p-3 text-sm font-medium text-muted-foreground">
                      {index + 1}
                    </td>
                    <td className="p-3">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-full bg-accent flex items-center justify-center">
                          <span className="text-xs font-bold">{time.abrev}</span>
                        </div>
                        <span className="font-medium">{time.abrev}</span>
                      </div>
                    </td>
                    <td className="p-3 text-center text-sm">{time.posicao}º</td>
                    <td className="p-3 text-center text-sm">{time.jogos}</td>
                    <td className="p-3 text-center text-sm">{time.vitorias}</td>
                    <td className="p-3 text-center text-sm">{time.empates}</td>
                    <td className="p-3 text-center text-sm">{time.derrotas}</td>
                    <td className="p-3 text-center">
                      <span className="inline-flex items-center justify-center px-2 py-1 rounded-md bg-primary/20 text-primary font-semibold">
                        {(time.forcaCasa ?? 0).toFixed(0)}
                      </span>
                    </td>
                    <td className="p-3 text-center">
                      <span className="inline-flex items-center justify-center px-2 py-1 rounded-md bg-secondary/20 text-secondary font-semibold">
                        {(time.forcaFora ?? 0).toFixed(0)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8 text-muted-foreground">
            Sem dados disponíveis
          </div>
        )}
      </motion.div>
      </TabsContent>

      </Tabs>

      <Disclaimer />
    </MainLayout>
  );
};

export default Estatisticas;
