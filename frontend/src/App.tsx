import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { HelmetProvider } from "react-helmet-async";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { CookieBanner } from "@/components/CookieBanner";
import LandingPage from "./pages/LandingPage";
import Dashboard from "./pages/Dashboard";
import Escalacao from "./pages/Escalacao";
import Confrontos from "./pages/Confrontos";
import Mercado from "./pages/Mercado";
import Historico from "./pages/Historico";
import Estatisticas from "./pages/Estatisticas";
import Sobre from "./pages/Sobre";
import Privacidade from "./pages/Privacidade";
import Termos from "./pages/Termos";
import Brasileirao from "./pages/Brasileirao";
import Scouts from "./pages/Scouts";
import Blog from "./pages/Blog";
import BlogPost from "./pages/BlogPost";
import TimePage from "./pages/TimePage";
import JogoPage from "./pages/JogoPage";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 2,
      retryDelay: 1000,
      staleTime: 1000 * 60 * 5, // 5 min default
    },
  },
});

const App = () => (
  <HelmetProvider>
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
            <Route path="/brasileirao" element={<Brasileirao />} />
            <Route path="/brasileirao/time/:slug" element={<TimePage />} />
            <Route path="/brasileirao/jogo/:id" element={<JogoPage />} />
            <Route path="/scouts" element={<Scouts />} />
            <Route path="/blog" element={<Blog />} />
            <Route path="/blog/:slug" element={<BlogPost />} />
            <Route path="/sobre" element={<Sobre />} />
            <Route path="/privacidade" element={<Privacidade />} />
            <Route path="/termos" element={<Termos />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
          <CookieBanner />
        </BrowserRouter>
      </ErrorBoundary>
    </TooltipProvider>
  </QueryClientProvider>
  </HelmetProvider>
);

export default App;
