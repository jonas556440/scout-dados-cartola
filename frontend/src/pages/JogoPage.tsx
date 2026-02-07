import { useParams, Link } from "react-router-dom";
import { MainLayout } from "@/components/layout/MainLayout";
import { SEO } from "@/components/SEO";
import { useJogoDetalhado } from "@/hooks/useCartolaApi";
import { motion } from "framer-motion";
import {
  Swords,
  AlertCircle,
  Loader2,
  ArrowLeft,
  Target,
  BarChart3,
  CheckCircle2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { Disclaimer } from "@/components/Disclaimer";

const JogoPage = () => {
  const { id } = useParams<{ id: string }>();
  const { data: jogo, isLoading, error } = useJogoDetalhado(id || "");

  if (error) {
    return (
      <MainLayout>
        <SEO
          title="Jogo não encontrado"
          description="Página de jogo não encontrada."
          path={`/brasileirao/jogo/${id}`}
        />
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Jogo não encontrado. Verifique o endereço ou{" "}
            <Link to="/brasileirao" className="underline font-semibold">
              volte à classificação
            </Link>.
          </AlertDescription>
        </Alert>
      </MainLayout>
    );
  }

  if (isLoading || !jogo) {
    return (
      <MainLayout>
        <div className="space-y-6">
          <div className="flex items-center gap-2">
            <Loader2 className="h-6 w-6 animate-spin" />
            <span>Carregando análise do jogo...</span>
          </div>
          <Skeleton className="h-48 rounded-lg" />
          <Skeleton className="h-64 rounded-lg" />
        </div>
      </MainLayout>
    );
  }

  const { mandante, visitante, previsao, resultadoReal } = jogo;

  return (
    <MainLayout>
      <SEO
        title={`${mandante.nome} x ${visitante.nome} - Rodada ${jogo.rodada}`}
        description={`Análise completa de ${mandante.nome} x ${visitante.nome} pelo Brasileirão 2026. Previsão: ${previsao.placarProvavel}. Probabilidades 1X2, Over/Under, BTTS e placares mais prováveis.`}
        path={`/brasileirao/jogo/${id}`}
      />

      {/* Voltar */}
      <Link
        to="/brasileirao"
        className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-4 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" /> Voltar à classificação
      </Link>

      {/* Header do jogo */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card p-6 mb-6"
      >
        <div className="text-center mb-4">
          <span className="text-xs text-muted-foreground uppercase tracking-wider">
            Brasileirão 2026 • Rodada {jogo.rodada}
          </span>
          {jogo.local && (
            <p className="text-xs text-muted-foreground mt-1">{jogo.local}</p>
          )}
        </div>

        {/* Placar / Previsão */}
        <div className="flex items-center justify-center gap-6 md:gap-12 mb-6">
          {/* Mandante */}
          <Link
            to={`/brasileirao/time/${slugFromAbrev(mandante.abrev)}`}
            className="flex flex-col items-center gap-2 hover:opacity-80 transition-opacity"
          >
            {mandante.escudo && (
              <img src={mandante.escudo} alt={mandante.abrev} className="w-16 h-16 md:w-20 md:h-20" />
            )}
            <span className="font-display font-bold text-sm md:text-base text-center">
              {mandante.nome}
            </span>
          </Link>

          {/* Placar central */}
          <div className="text-center">
            {resultadoReal ? (
              <>
                <div className="text-4xl md:text-5xl font-display font-black">
                  {resultadoReal.casa}{" "}
                  <span className="text-muted-foreground">×</span>{" "}
                  {resultadoReal.fora}
                </div>
                <div className="flex items-center gap-1 justify-center mt-1">
                  <CheckCircle2 className="w-3 h-3 text-success" />
                  <span className="text-xs text-success font-semibold">RESULTADO FINAL</span>
                </div>
                <div className="text-xs text-muted-foreground mt-1">
                  Previsão era: {previsao.placarProvavel}
                </div>
              </>
            ) : (
              <>
                <div className="text-3xl md:text-4xl font-display font-black text-primary">
                  {previsao.placarProvavel}
                </div>
                <div className="text-xs text-muted-foreground mt-1">Placar previsto</div>
                <div className="text-xs text-muted-foreground">
                  {previsao.modo} • Confiança {previsao.confianca}%
                </div>
              </>
            )}
          </div>

          {/* Visitante */}
          <Link
            to={`/brasileirao/time/${slugFromAbrev(visitante.abrev)}`}
            className="flex flex-col items-center gap-2 hover:opacity-80 transition-opacity"
          >
            {visitante.escudo && (
              <img src={visitante.escudo} alt={visitante.abrev} className="w-16 h-16 md:w-20 md:h-20" />
            )}
            <span className="font-display font-bold text-sm md:text-base text-center">
              {visitante.nome}
            </span>
          </Link>
        </div>

        {/* Forma dos times */}
        <div className="flex justify-between items-center">
          <FormaDisplay forma={mandante.stats.forma} label={mandante.abrev} />
          <FormaDisplay forma={visitante.stats.forma} label={visitante.abrev} reverse />
        </div>
      </motion.div>

      {/* Cards de análise */}
      <div className="grid md:grid-cols-2 gap-6 mb-6">
        {/* 1X2 + Over/Under */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
          className="glass-card p-6"
        >
          <h2 className="font-display text-xl font-bold mb-4 flex items-center gap-2">
            <Target className="w-5 h-5 text-primary" />
            Probabilidades
          </h2>

          {/* 1X2 */}
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-muted-foreground mb-3">Resultado (1X2)</h3>
            <div className="grid grid-cols-3 gap-2">
              <ProbCard
                label={mandante.abrev}
                value={previsao.probVitoriaCasa}
                color="bg-success"
              />
              <ProbCard label="Empate" value={previsao.probEmpate} color="bg-warning" />
              <ProbCard
                label={visitante.abrev}
                value={previsao.probVitoriaFora}
                color="bg-info"
              />
            </div>
          </div>

          {/* Over/Under */}
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-muted-foreground mb-3">Over/Under</h3>
            <div className="space-y-2">
              {[
                { label: "Over 1.5", value: previsao.over15 },
                { label: "Over 2.5", value: previsao.over25 },
                { label: "Over 3.5", value: previsao.over35 },
              ].map((ou) => (
                <div key={ou.label} className="flex items-center justify-between">
                  <span className="text-sm">{ou.label}</span>
                  <div className="flex items-center gap-2">
                    <div className="w-24 bg-muted rounded-full h-2">
                      <div
                        className="h-2 rounded-full bg-primary"
                        style={{ width: `${ou.value}%` }}
                      />
                    </div>
                    <span className="text-sm font-bold w-12 text-right">
                      {ou.value.toFixed(0)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* BTTS */}
          <div>
            <h3 className="text-sm font-semibold text-muted-foreground mb-2">
              Ambos Marcam (BTTS)
            </h3>
            <div className="flex items-center gap-3">
              <div className="flex-1 bg-muted rounded-full h-3">
                <div
                  className="h-3 rounded-full bg-primary"
                  style={{ width: `${previsao.btts}%` }}
                />
              </div>
              <span className="font-bold">{previsao.btts.toFixed(0)}%</span>
            </div>
          </div>
        </motion.div>

        {/* xG + Top placares */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="glass-card p-6"
        >
          <h2 className="font-display text-xl font-bold mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-primary" />
            Gols Esperados & Placares
          </h2>

          {/* xG */}
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-muted-foreground mb-3">
              Expected Goals (xG)
            </h3>
            <div className="flex items-center justify-between p-4 bg-muted/30 rounded-lg">
              <div className="text-center">
                <div className="text-2xl font-bold text-success">
                  {previsao.xgCasa.toFixed(2)}
                </div>
                <div className="text-xs text-muted-foreground">{mandante.abrev}</div>
              </div>
              <Swords className="w-5 h-5 text-muted-foreground" />
              <div className="text-center">
                <div className="text-2xl font-bold text-info">
                  {previsao.xgFora.toFixed(2)}
                </div>
                <div className="text-xs text-muted-foreground">{visitante.abrev}</div>
              </div>
            </div>
          </div>

          {/* Top placares */}
          <div>
            <h3 className="text-sm font-semibold text-muted-foreground mb-3">
              Placares Mais Prováveis
            </h3>
            <div className="space-y-2">
              {previsao.topPlacares.map((p, i) => (
                <div
                  key={p.placar}
                  className="flex items-center justify-between p-2 rounded-lg bg-muted/20"
                >
                  <div className="flex items-center gap-2">
                    <span
                      className={cn(
                        "w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold",
                        i === 0
                          ? "bg-primary/20 text-primary"
                          : "bg-muted text-muted-foreground"
                      )}
                    >
                      {i + 1}
                    </span>
                    <span className="font-mono font-bold text-lg">{p.placar}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-20 bg-muted rounded-full h-2">
                      <div
                        className="h-2 rounded-full bg-primary"
                        style={{ width: `${Math.min(p.prob * 4, 100)}%` }}
                      />
                    </div>
                    <span className="font-semibold text-sm w-14 text-right">
                      {p.prob.toFixed(1)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Stats dos times */}
          {mandante.stats && visitante.stats && (
            <div className="mt-6 pt-4 border-t">
              <h3 className="text-sm font-semibold text-muted-foreground mb-3">
                Comparação no Campeonato
              </h3>
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-xs text-muted-foreground">
                    <th className="text-left">{mandante.abrev}</th>
                    <th className="text-center">Stat</th>
                    <th className="text-right">{visitante.abrev}</th>
                  </tr>
                </thead>
                <tbody className="space-y-1">
                  {[
                    { label: "Gols Marcados", m: mandante.stats.golsPro, v: visitante.stats.golsPro },
                    { label: "Gols Sofridos", m: mandante.stats.golsContra, v: visitante.stats.golsContra, inverted: true },
                  ].map((stat) => (
                    <tr key={stat.label}>
                      <td
                        className={cn(
                          "text-left font-semibold",
                          !stat.inverted
                            ? stat.m > stat.v
                              ? "text-success"
                              : stat.m < stat.v
                              ? "text-destructive"
                              : ""
                            : stat.m < stat.v
                            ? "text-success"
                            : stat.m > stat.v
                            ? "text-destructive"
                            : ""
                        )}
                      >
                        {stat.m}
                      </td>
                      <td className="text-center text-muted-foreground text-xs">
                        {stat.label}
                      </td>
                      <td
                        className={cn(
                          "text-right font-semibold",
                          !stat.inverted
                            ? stat.v > stat.m
                              ? "text-success"
                              : stat.v < stat.m
                              ? "text-destructive"
                              : ""
                            : stat.v < stat.m
                            ? "text-success"
                            : stat.v > stat.m
                            ? "text-destructive"
                            : ""
                        )}
                      >
                        {stat.v}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </motion.div>
      </div>

      <Disclaimer />
    </MainLayout>
  );
};

// ===== Componentes auxiliares =====

function ProbCard({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  return (
    <div className="text-center p-3 bg-muted/30 rounded-lg">
      <div className={cn("text-2xl font-bold")}>{value.toFixed(0)}%</div>
      <div
        className={cn("w-full h-1.5 rounded-full mt-2", "bg-muted")}
      >
        <div className={cn("h-1.5 rounded-full", color)} style={{ width: `${value}%` }} />
      </div>
      <div className="text-xs text-muted-foreground mt-1">{label}</div>
    </div>
  );
}

function FormaDisplay({
  forma,
  label,
  reverse,
}: {
  forma?: string;
  label: string;
  reverse?: boolean;
}) {
  if (!forma || forma.length === 0) return null;
  return (
    <div className={cn("flex items-center gap-2", reverse && "flex-row-reverse")}>
      <span className="text-xs text-muted-foreground">{label}</span>
      <div className="flex gap-0.5">
        {forma.split("").slice(-5).map((r, i) => (
          <span
            key={i}
            className={cn(
              "w-5 h-5 rounded-sm flex items-center justify-center text-[10px] font-bold text-white",
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
  );
}

// Mapeamento abreviação → slug
const ABREV_TO_SLUG: Record<string, string> = {
  CAM: "atletico-mg",
  CAP: "athletico-pr",
  BAH: "bahia",
  BOT: "botafogo",
  COR: "corinthians",
  CRU: "cruzeiro",
  CUI: "cuiaba",
  FLA: "flamengo",
  FLU: "fluminense",
  FOR: "fortaleza",
  GRE: "gremio",
  INT: "internacional",
  JUV: "juventude",
  MIR: "mirassol",
  PAL: "palmeiras",
  SAN: "santos",
  SAO: "sao-paulo",
  SPO: "sport",
  VAS: "vasco",
  VIT: "vitoria",
  RBB: "red-bull-bragantino",
  CHA: "chapecoense",
  CFC: "coritiba",
  REM: "remo",
};

function slugFromAbrev(abrev: string): string {
  return ABREV_TO_SLUG[abrev] || abrev.toLowerCase();
}

export default JogoPage;
