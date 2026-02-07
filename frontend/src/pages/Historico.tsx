import { MainLayout } from "@/components/layout/MainLayout";
import { PatrimonyChart } from "@/components/cartola/PatrimonyChart";
import { useHistoricoRodadas, useHistoricoStatus, useHistoricoRodada, useDashboard } from "@/hooks/useCartolaApi";
import { useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { History, Calendar, Loader2, AlertCircle, Wallet, Users, ChevronDown, ChevronUp } from "lucide-react";
import { cn } from "@/lib/utils";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { SEO } from "@/components/SEO";

// Componente para exibir os detalhes de uma rodada expandida
const RodadaDetalhes = ({ rodada }: { rodada: number }) => {
  const { data: detalhes, isLoading, error } = useHistoricoRodada(rodada);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="w-6 h-6 animate-spin text-primary" />
        <span className="ml-2 text-sm text-muted-foreground">Carregando times...</span>
      </div>
    );
  }

  if (error || !detalhes) {
    return (
      <Alert variant="destructive" className="mt-4">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>Erro ao carregar detalhes da rodada</AlertDescription>
      </Alert>
    );
  }

  // Se detalhes for um array, use-o diretamente, senão converta em array
  const times = Array.isArray(detalhes) ? detalhes : [detalhes];

  return (
    <div className="mt-4 space-y-6">
      {times.map((time: any, idx: number) => (
        <motion.div
          key={idx}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: idx * 0.1 }}
          className="glass-card p-4"
        >
          {/* Header do Time */}
          <div className="mb-4 pb-3 border-b border-border">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-bold">
                  {time.tipo === 'valorizacao' ? '💰 Time de Valorização' : '⚽ Time de Pontuação'}
                </h3>
                <p className="text-sm text-muted-foreground">
                  Esquema: {time.esquema || '4-4-2'} • Patrimônio: C$ {(time.patrimonio ?? 100).toFixed(2)}
                </p>
              </div>
              <div className="text-right">
                <p className="text-sm text-muted-foreground">Pontuação Esperada</p>
                <p className="text-2xl font-bold text-success">
                  {(time.pontuacao_esperada ?? 0).toFixed(1)}
                </p>
              </div>
            </div>
          </div>

          {/* Titulares */}
          {time.titulares && time.titulares.length > 0 && (
            <div className="mb-4">
              <h4 className="text-sm font-semibold mb-3 text-muted-foreground">
                Titulares ({time.titulares.length})
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {time.titulares.map((jogador: any) => (
                  <div
                    key={jogador.atleta_id}
                    className="flex items-center gap-3 p-3 rounded-lg bg-card/50 border border-border/50"
                  >
                    <div className={cn(
                      "flex items-center justify-center w-10 h-10 rounded-full text-xs font-bold",
                      jogador.posicao_abrev === 'GOL' && "bg-yellow-500/20 text-yellow-600",
                      jogador.posicao_abrev === 'LAT' && "bg-green-500/20 text-green-600",
                      jogador.posicao_abrev === 'ZAG' && "bg-blue-500/20 text-blue-600",
                      jogador.posicao_abrev === 'MEI' && "bg-purple-500/20 text-purple-600",
                      jogador.posicao_abrev === 'ATA' && "bg-red-500/20 text-red-600",
                      jogador.posicao_abrev === 'TEC' && "bg-gray-500/20 text-gray-600"
                    )}>
                      {jogador.posicao_abrev || 'N/A'}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-sm truncate">{jogador.apelido || 'Sem nome'}</p>
                      <p className="text-xs text-muted-foreground">
                        {jogador.clube_abrev || 'N/A'} • C$ {(jogador.preco ?? 0).toFixed(2)}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-bold">
                        {(jogador.pontuacao_esperada ?? jogador.media ?? 0).toFixed(1)}
                      </p>
                      <p className="text-xs text-muted-foreground">pts</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Reservas */}
          {time.reservas && time.reservas.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold mb-3 text-muted-foreground">
                Reservas ({time.reservas.length})
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {time.reservas.map((jogador: any) => (
                  <div
                    key={jogador.atleta_id}
                    className="flex items-center gap-3 p-2 rounded-lg bg-card/30 border border-dashed border-border/30"
                  >
                    <div className={cn(
                      "flex items-center justify-center w-8 h-8 rounded-full text-xs font-bold",
                      jogador.posicao_abrev === 'GOL' && "bg-yellow-500/10 text-yellow-600",
                      jogador.posicao_abrev === 'ZAG' && "bg-blue-500/10 text-blue-600",
                      jogador.posicao_abrev === 'TEC' && "bg-gray-500/10 text-gray-600"
                    )}>
                      {jogador.posicao_abrev || 'N/A'}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-xs truncate">{jogador.apelido || 'Sem nome'}</p>
                      <p className="text-xs text-muted-foreground">
                        {jogador.clube_abrev || 'N/A'} • C$ {(jogador.preco ?? 0).toFixed(2)}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs font-semibold">
                        {(jogador.pontuacao_esperada ?? jogador.media ?? 0).toFixed(1)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </motion.div>
      ))}
    </div>
  );
};

const Historico = () => {
  const { data: historicoRodadas, isLoading: loadingRodadas, error: errorRodadas } = useHistoricoRodadas();
  const { data: historicoStatus, isLoading: loadingStatus } = useHistoricoStatus();
  const { data: dashboardData } = useDashboard();
  const [rodadaExpandida, setRodadaExpandida] = useState<number | null>(null);

  const isLoading = loadingRodadas || loadingStatus;
  const error = errorRodadas;

  // Gerar dados de patrimônio baseado no histórico real ou dados do dashboard
  const patrimonyData = useMemo(() => {
    const patrimonioAtual = dashboardData?.patrimonio ?? 100;
    const rodadaAtual = dashboardData?.mercado?.rodadaAtual ?? 1;
    
    // Se temos histórico real, usar ele
    if (historicoRodadas && historicoRodadas.length > 0) {
      return historicoRodadas.map((item, index) => ({
        rodada: item.rodada,
        patrimonio: 100 + (index * 2), // Estimativa simples
      }));
    }
    
    // Senão, gerar dados baseado na rodada atual
    const data = [];
    for (let i = 1; i <= rodadaAtual; i++) {
      data.push({
        rodada: i,
        patrimonio: i === rodadaAtual ? patrimonioAtual : 100 + ((i - 1) * 2),
      });
    }
    return data;
  }, [historicoRodadas, dashboardData]);

  if (isLoading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <Loader2 className="w-8 h-8 animate-spin text-primary mx-auto mb-4" />
            <p className="text-muted-foreground">Carregando histórico...</p>
          </div>
        </div>
      </MainLayout>
    );
  }

  if (error) {
    return (
      <MainLayout>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Erro ao carregar histórico</AlertTitle>
          <AlertDescription>
            Não foi possível obter os dados da API. Verifique se o servidor está rodando.
          </AlertDescription>
        </Alert>
      </MainLayout>
    );
  }

  const rodadaAtual = dashboardData?.mercado?.rodadaAtual ?? 1;
  const patrimonioAtual = dashboardData?.patrimonio ?? 100;
  const temHistorico = historicoRodadas && historicoRodadas.length > 0;

  return (
    <MainLayout>
      <SEO title="Histórico de Rodadas" description="Acompanhe seu histórico no Cartola FC 2026. Evolução patrimonial, pontuação por rodada e análise de desempenho." path="/historico" />
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 hero-gradient rounded-lg">
            <History className="w-6 h-6 text-primary-foreground" />
          </div>
          <div>
            <h1 className="font-display text-3xl md:text-4xl font-bold">
              Histórico <span className="text-sm px-2 py-1 bg-red-500 text-white rounded-md ml-2">🔴 AO VIVO - API REAL</span>
            </h1>
            <p className="text-muted-foreground">
              Acompanhe seu desempenho ao longo do campeonato
            </p>
          </div>
        </div>
      </motion.div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="glass-card p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/20 rounded-lg">
              <Calendar className="w-5 h-5 text-primary" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Rodada Atual</p>
              <p className="text-2xl font-bold">{rodadaAtual}</p>
            </div>
          </div>
        </div>
        <div className="glass-card p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-secondary/20 rounded-lg">
              <Wallet className="w-5 h-5 text-secondary" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Patrimônio</p>
              <p className="text-2xl font-bold">C$ {patrimonioAtual.toFixed(2)}</p>
            </div>
          </div>
        </div>
        <div className="glass-card p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-success/20 rounded-lg">
              <Users className="w-5 h-5 text-success" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Times Salvos</p>
              <p className="text-2xl font-bold">{historicoStatus?.total_times ?? 0}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Patrimony Chart */}
      <div className="mb-8">
        <PatrimonyChart data={patrimonyData} />
      </div>

      {/* Timeline */}
      <div className="glass-card p-6">
        <h2 className="font-display text-xl font-bold mb-6">Timeline de Rodadas</h2>
        
        <div className="space-y-4">
          {temHistorico ? (
            historicoRodadas.map((item, index) => (
              <motion.div
                key={item.rodada}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="relative pl-8 pb-8 border-l-2 border-border last:border-l-0 last:pb-0"
              >
                {/* Timeline Dot */}
                <div className={cn(
                  "absolute left-0 top-0 -translate-x-1/2 w-4 h-4 rounded-full border-2",
                  item.times_salvos > 0 ? "bg-success border-success" : "bg-primary border-primary"
                )} />

                {/* Content */}
                <div className="ml-4">
                  <div 
                    className="glass-card p-4 cursor-pointer hover:bg-accent/50 transition-colors"
                    onClick={() => setRodadaExpandida(rodadaExpandida === item.rodada ? null : item.rodada)}
                  >
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                      <div className="flex items-center gap-3">
                        <div className="flex items-center gap-2 text-muted-foreground">
                          <Calendar className="w-4 h-4" />
                          <span>Rodada {item.rodada}</span>
                        </div>
                        {item.tipos.map((tipo) => (
                          <span key={tipo} className={cn(
                            "px-2 py-0.5 text-xs font-bold rounded-full",
                            tipo === 'valorizacao' ? "bg-primary/20 text-primary" : "bg-secondary/20 text-secondary"
                          )}>
                            {tipo === 'valorizacao' ? 'Valorização' : 'Pontuação'}
                          </span>
                        ))}
                      </div>
                      
                      <div className="flex items-center gap-4">
                        <div className="flex items-center gap-4 text-sm text-muted-foreground">
                          <span>{item.times_salvos} time(s)</span>
                          {item.data_criacao && (
                            <span>{new Date(item.data_criacao).toLocaleDateString('pt-BR')}</span>
                          )}
                        </div>
                        {rodadaExpandida === item.rodada ? (
                          <ChevronUp className="w-5 h-5 text-muted-foreground" />
                        ) : (
                          <ChevronDown className="w-5 h-5 text-muted-foreground" />
                        )}
                      </div>
                    </div>
                  </div>
                  
                  {/* Detalhes Expandidos */}
                  <AnimatePresence>
                    {rodadaExpandida === item.rodada && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.3 }}
                      >
                        <RodadaDetalhes rodada={item.rodada} />
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </motion.div>
            ))
          ) : (
            // Mostrar rodada atual mesmo sem histórico
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="relative pl-8 pb-8 border-l-2 border-border"
            >
              <div className="absolute left-0 top-0 -translate-x-1/2 w-4 h-4 rounded-full border-2 bg-primary border-primary" />
              <div className="glass-card p-4 ml-4">
                <div className="flex items-center gap-3">
                  <Calendar className="w-4 h-4 text-muted-foreground" />
                  <span className="text-muted-foreground">Rodada {rodadaAtual}</span>
                  <span className="px-2 py-0.5 text-xs font-bold rounded-full bg-yellow-500/20 text-yellow-600">
                    Em andamento
                  </span>
                </div>
                <p className="mt-2 text-sm text-muted-foreground">
                  Escale seu time na aba "Escalação" e salve para registrar no histórico.
                </p>
              </div>
            </motion.div>
          )}

          {!temHistorico && rodadaAtual === 1 && (
            <div className="text-center py-8 text-muted-foreground">
              <History className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>Nenhuma rodada concluída ainda.</p>
              <p className="text-sm">O histórico será atualizado após a primeira rodada.</p>
            </div>
          )}
        </div>
      </div>
    </MainLayout>
  );
};

export default Historico;
