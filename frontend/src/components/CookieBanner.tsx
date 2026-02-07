import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { X, Cookie } from "lucide-react";
import { Button } from "@/components/ui/button";

const CONSENT_KEY = "scoutdados-consent";

type ConsentState = "pending" | "accepted" | "declined";

export function CookieBanner() {
  const [consent, setConsent] = useState<ConsentState>("accepted"); // default hide

  useEffect(() => {
    const stored = localStorage.getItem(CONSENT_KEY);
    if (!stored) {
      setConsent("pending");
    } else {
      setConsent(stored as ConsentState);
    }
  }, []);

  const handleAccept = () => {
    localStorage.setItem(CONSENT_KEY, "accepted");
    setConsent("accepted");
    // Habilitar GA se existir
    if (typeof window !== "undefined" && (window as any).gtag) {
      (window as any).gtag("consent", "update", {
        analytics_storage: "granted",
        ad_storage: "granted",
      });
    }
  };

  const handleDecline = () => {
    localStorage.setItem(CONSENT_KEY, "declined");
    setConsent("declined");
    if (typeof window !== "undefined" && (window as any).gtag) {
      (window as any).gtag("consent", "update", {
        analytics_storage: "denied",
        ad_storage: "denied",
      });
    }
  };

  if (consent !== "pending") return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-[100] p-4 animate-in slide-in-from-bottom-4 duration-500">
      <div className="max-w-4xl mx-auto glass-card border border-border p-4 md:p-6 shadow-2xl">
        <div className="flex items-start gap-4">
          <Cookie className="w-6 h-6 text-primary shrink-0 mt-0.5" />
          <div className="flex-1">
            <h3 className="font-semibold text-sm mb-1">Cookies e Privacidade</h3>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Usamos cookies do Google Analytics e AdSense para melhorar sua experiência
              e exibir conteúdo relevante. Seus dados são tratados conforme a LGPD.{" "}
              <Link to="/privacidade" className="text-primary hover:underline">
                Política de Privacidade
              </Link>
            </p>
          </div>
          <button onClick={handleDecline} className="text-muted-foreground hover:text-foreground">
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="flex items-center gap-3 mt-4 justify-end">
          <Button variant="outline" size="sm" onClick={handleDecline}>
            Recusar
          </Button>
          <Button size="sm" onClick={handleAccept} className="hero-gradient text-primary-foreground">
            Aceitar Cookies
          </Button>
        </div>
      </div>
    </div>
  );
}
