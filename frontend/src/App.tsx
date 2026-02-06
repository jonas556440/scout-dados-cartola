import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import LandingPage from "./pages/LandingPage";
import Dashboard from "./pages/Dashboard";
import Escalacao from "./pages/Escalacao";
import Confrontos from "./pages/Confrontos";
import Mercado from "./pages/Mercado";
import Historico from "./pages/Historico";
import Estatisticas from "./pages/Estatisticas";
import Sobre from "./pages/Sobre";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <ErrorBoundary>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/escalacao" element={<Escalacao />} />
            <Route path="/confrontos" element={<Confrontos />} />
            <Route path="/mercado" element={<Mercado />} />
            <Route path="/historico" element={<Historico />} />
            <Route path="/estatisticas" element={<Estatisticas />} />
            <Route path="/sobre" element={<Sobre />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </ErrorBoundary>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
