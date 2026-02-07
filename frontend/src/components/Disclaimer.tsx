import { AlertTriangle } from "lucide-react";

interface DisclaimerProps {
  compact?: boolean;
}

export function Disclaimer({ compact = false }: DisclaimerProps) {
  if (compact) {
    return (
      <div className="text-[10px] text-muted-foreground/60 text-center py-2 border-t border-border mt-4">
        <AlertTriangle className="inline w-3 h-3 mr-1" />
        Projeções estatísticas (Poisson/Monte Carlo) com fins informativos. Não representa garantia de resultado.
      </div>
    );
  }

  return (
    <div className="glass-card p-4 mt-6 border border-warning/20 bg-warning/5">
      <div className="flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-warning shrink-0 mt-0.5" />
        <p className="text-xs text-muted-foreground leading-relaxed">
          <strong>Aviso:</strong> As projeções apresentadas são resultado de modelos estatísticos
          (Poisson, Monte Carlo) com fins informativos e educacionais. Não representam garantia
          de resultado e não devem ser utilizadas para fins de apostas. O ScoutDados não é e não
          promove casa de apostas.
        </p>
      </div>
    </div>
  );
}
