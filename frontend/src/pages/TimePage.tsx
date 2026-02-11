import { useParams, Link } from "react-router-dom";
import { MainLayout } from "@/components/layout/MainLayout";
import { SEO } from "@/components/SEO";
import { useTimeDetalhado } from "@/hooks/useCartolaApi";
import { motion } from "framer-motion";
import {
  Shield,
  TrendingUp,
  TrendingDown,
  Trophy,
  AlertCircle,
  Loader2,
  Calendar,
  Target,
  ArrowLeft,
  Swords,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { Progress } from "@/components/ui/progress";
import { Disclaimer } from "@/components/Disclaimer";

const TimePage = () => {
  const { slug } = useParams<{ slug: string }>();
  const { data: time, isLoading, error } = useTimeDetalhado(slug || "");

  if (error) {
    return (
      <MainLayout>
        <SEO
          title="Time não encontrado"
          description="Página de time não encontrada."
          path={`/brasileirao/time/${slug}`}
        />
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Time não encontrado. Verifique o endereço ou{" "}
            <Link to="/brasileirao" className="underline font-semibold">
              volte à classificação
            </Link>.
          </AlertDescription>
        </Alert>
      </MainLayout>
    );
  }

  if (isLoading || !time) {
    return (
      <MainLayout>
        <div className="space-y-6">
          <div className="flex items-center gap-2">
            <Loader2 className="h-6 w-6 animate-spin" />
            <span>Carregando dados do time...</span>
          </div>
          <Skeleton className="h-48 rounded-lg" />
          <Skeleton className="h-64 rounded-lg" />
        </div>
      </MainLayout>
    );
  }

  const zonaClass =
    time.posicao <= 4
      ? "text-primary"
      : time.posicao <= 6
      ? "text-info"
      : time.posicao <= 12
      ? "text-warning"
      : time.posicao >= 17
      ? "text-destructive"
      : "text-muted-foreground";

  return (
    <MainLayout>
      <SEO
        title={`${time.nome} - Brasileirão 2026`}
        description={`Estatísticas completas do ${time.nome} no Brasileirão 2026. ${time.posicao}º lugar com ${time.pontos} pontos. Simulação Monte Carlo, próximos jogos e probabilidades.`}
        path={`/brasileirao/time/${slug}`}
        image={`/api/og-image/time/${slug}`}
      />

      {/* Voltar */}
      <Link
        to="/brasileirao"
        className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-4 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" /> Voltar à classificação
      </Link>

      {/* Header do time */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card p-6 mb-6"
      >
        <div className="flex items-center gap-4 mb-4">
          {time.escudo && (
            <img src={time.escudo} alt={time.abrev} className="w-16 h-16" loading="lazy" />
          )}
          <div>
            <h1 className="font-display text-3xl md:text-4xl font-bold">
              {time.nome}
            </h1>
            <div className="flex items-center gap-3 mt-1">
              <span className={cn("text-2xl font-bold", zonaClass)}>
                {time.posicao}º lugar
              </span>
              <span className="text-muted-foreground">•</span>
              <span className="text-lg font-semibold">
                {time.pontos} pontos
              </span>
              <span className="text-muted-foreground">•</span>
              <span className="text-sm text-muted-foreground">
                {time.jogos} jogos
              </span>
            </div>
          </div>
        </div>

        {/* Estatísticas rápidas */}
        <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-7 gap-3">
          {[
            { label: "V", value: time.vitorias, color: "text-success" },
            { label: "E", value: time.empates, color: "text-warning" },
            { label: "D", value: time.derrotas, color: "text-destructive" },
            { label: "GP", value: time.golsPro, color: "" },
            { label: "GC", value: time.golsContra, color: "" },
            {
              label: "SG",
              value: time.saldoGols > 0 ? `+${time.saldoGols}` : time.saldoGols,
              color: time.saldoGols > 0 ? "text-success" : time.saldoGols < 0 ? "text-destructive" : "",
            },
            { label: "Aprov.", value: `${time.aproveitamento}%`, color: "" },
          ].map((stat) => (
            <div key={stat.label} className="text-center p-2 bg-muted/30 rounded-lg">
              <div className="text-xs text-muted-foreground uppercase tracking-wider">
                {stat.label}
              </div>
              <div className={cn("text-xl font-bold", stat.color)}>
                {stat.value}
              </div>
            </div>
          ))}
        </div>

        {/* Forma */}
        {time.forma && time.forma.length > 0 && (
          <div className="mt-4">
            <span className="text-sm text-muted-foreground mr-2">Forma:</span>
            <div className="inline-flex gap-1">
              {time.forma.split("").slice(-5).map((r, i) => (
                <span
                  key={i}
                  className={cn(
                    "w-7 h-7 rounded-sm flex items-center justify-center text-xs font-bold text-white",
                    r === "V"
                      ? "bg-success"
                      : r === "E"
                      ? "bg-warning"
                      : r === "D"
                      ? "bg-destructive"
                      : "bg-muted"
                  )}
                >
                  {r}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Força */}
        <div className="grid grid-cols-3 gap-4 mt-4">
          {[
            { label: "Casa", value: time.forcaCasa },
            { label: "Fora", value: time.forcaFora },
            { label: "Geral", value: time.forcaGeral },
          ].map((f) => (
            <div key={f.label} className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-muted-foreground">{f.label}</span>
                <span className="font-semibold">{(f.value * 100).toFixed(0)}%</span>
              </div>
              <Progress value={f.value * 100} className="h-2" />
            </div>
          ))}
        </div>
      </motion.div>

      <div className="grid md:grid-cols-2 gap-6 mb-6">
        {/* Probabilidades Monte Carlo */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
          className="glass-card p-6"
        >
          <h2 className="font-display text-xl font-bold mb-4 flex items-center gap-2">
            <Trophy className="w-5 h-5 text-primary" />
            Simulação Monte Carlo
          </h2>
          <p className="text-xs text-muted-foreground mb-4">
            1.000 simulações do restante do campeonato
          </p>

          <div className="space-y-4">
            {[
              {
                label: "Título",
                value: time.probabilidades.titulo,
                color: "bg-primary",
                icon: <Trophy className="w-4 h-4" />,
              },
              {
                label: "Libertadores (G4)",
                value: time.probabilidades.libertadores,
                color: "bg-primary",
                icon: <TrendingUp className="w-4 h-4" />,
              },
              {
                label: "Sul-Americana (G6)",
                value: time.probabilidades.sulamericana,
                color: "bg-info",
                icon: <Shield className="w-4 h-4" />,
              },
              {
                label: "Rebaixamento",
                value: time.probabilidades.rebaixamento,
                color: "bg-destructive",
                icon: <TrendingDown className="w-4 h-4" />,
              },
            ].map((prob) => (
              <div key={prob.label} className="space-y-1">
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    {prob.icon}
                    <span>{prob.label}</span>
                  </div>
                  <span className="font-bold">{prob.value.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-muted rounded-full h-3">
                  <div
                    className={cn("h-3 rounded-full transition-all", prob.color)}
                    style={{ width: `${Math.min(prob.value, 100)}%` }}
                  />
                </div>
              </div>
            ))}

            <div className="pt-2 border-t text-sm text-muted-foreground">
              Posição média prevista:{" "}
              <span className="font-bold text-foreground">
                {time.probabilidades.posicaoMedia.toFixed(1)}º
              </span>
            </div>
          </div>
        </motion.div>

        {/* Próximos jogos */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="glass-card p-6"
        >
          <h2 className="font-display text-xl font-bold mb-4 flex items-center gap-2">
            <Calendar className="w-5 h-5 text-primary" />
            Próximos Jogos
          </h2>

          <div className="space-y-3">
            {time.proximosJogos.map((jogo, idx) => (
              <div
                key={idx}
                className="block p-3 bg-muted/30 rounded-lg"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-muted-foreground">
                    Rodada {jogo.rodada} •{" "}
                    <span
                      className={cn(
                        "font-semibold",
                        jogo.local === "Casa" ? "text-success" : "text-info"
                      )}
                    >
                      {jogo.local === "Casa" ? "🏠 Casa" : "✈️ Fora"}
                    </span>
                  </span>
                  <Swords className="w-3 h-3 text-muted-foreground" />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <span className="font-semibold">
                      vs {jogo.adversarioNome}
                    </span>
                    <span className="text-xs text-muted-foreground ml-2">
                      ({jogo.adversario})
                    </span>
                  </div>
                  <div className="text-right">
                    <div className="font-bold text-sm">{jogo.placarProvavel}</div>
                    <div className="text-[10px] text-muted-foreground">
                      xG {jogo.xgTime.toFixed(1)} × {jogo.xgAdversario.toFixed(1)}
                    </div>
                  </div>
                </div>
                <div className="flex gap-1 mt-2">
                  <div
                    className="h-1.5 rounded-full bg-success"
                    style={{ width: `${jogo.probVitoria}%` }}
                    title={`Vitória: ${jogo.probVitoria.toFixed(1)}%`}
                  />
                  <div
                    className="h-1.5 rounded-full bg-warning"
                    style={{ width: `${jogo.probEmpate}%` }}
                    title={`Empate: ${jogo.probEmpate.toFixed(1)}%`}
                  />
                  <div
                    className="h-1.5 rounded-full bg-destructive"
                    style={{ width: `${jogo.probDerrota}%` }}
                    title={`Derrota: ${jogo.probDerrota.toFixed(1)}%`}
                  />
                </div>
              </div>
            ))}

            {time.proximosJogos.length === 0 && (
              <p className="text-sm text-muted-foreground text-center py-4">
                Nenhum jogo futuro encontrado.
              </p>
            )}
          </div>
        </motion.div>
      </div>

      <Disclaimer />
    </MainLayout>
  );
};

export default TimePage;
