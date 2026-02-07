import { Info } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

export function ColorLegend() {
  return (
    <Alert className="bg-muted/30 border-muted">
      <Info className="h-4 w-4" />
      <AlertDescription>
        <h3 className="text-sm font-semibold mb-3">
          Legenda das Faixas de Classificação
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-primary/20 border-2 border-primary flex-shrink-0" />
            <span><strong className="text-primary">G-4:</strong> Libertadores (fase de grupos)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-info/20 border-2 border-info flex-shrink-0" />
            <span><strong className="text-info">G-6:</strong> Libertadores (pré-eliminatórias)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-warning/20 border-2 border-warning flex-shrink-0" />
            <span><strong className="text-warning">G-12:</strong> Sul-Americana</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-destructive/20 border-2 border-destructive flex-shrink-0" />
            <span><strong className="text-destructive">Z-4:</strong> Rebaixamento (Série B)</span>
          </div>
        </div>
        <p className="text-xs text-muted-foreground mt-3">
          💡 <strong>Dica:</strong> Clique no nome de qualquer time para ver análise detalhada, probabilidades e próximos jogos
        </p>
      </AlertDescription>
    </Alert>
  );
}
