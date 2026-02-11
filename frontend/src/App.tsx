import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { toast } from "sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { HelmetProvider } from "react-helmet-async";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { CookieBanner } from "@/components/CookieBanner";
import { lazy, Suspense } from "react";
import { Loader2 } from "lucide-react";

// Eager load: landing page (first paint)
import LandingPage from "./pages/LandingPage";

// Lazy load: all other pages
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Escalacao = lazy(() => import("./pages/Escalacao"));
const Confrontos = lazy(() => import("./pages/Confrontos"));
const Mercado = lazy(() => import("./pages/Mercado"));
const Historico = lazy(() => import("./pages/Historico"));
const Estatisticas = lazy(() => import("./pages/Estatisticas"));
const Sobre = lazy(() => import("./pages/Sobre"));
const Privacidade = lazy(() => import("./pages/Privacidade"));
const Termos = lazy(() => import("./pages/Termos"));
const Brasileirao = lazy(() => import("./pages/Brasileirao"));
const Scouts = lazy(() => import("./pages/Scouts"));
const Blog = lazy(() => import("./pages/Blog"));
const BlogPost = lazy(() => import("./pages/BlogPost"));
const TimePage = lazy(() => import("./pages/TimePage"));
const JogoPage = lazy(() => import("./pages/JogoPage"));
const NotFound = lazy(() => import("./pages/NotFound"));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 2,
      retryDelay: 1000,
      staleTime: 1000 * 60 * 5, // 5 min default
    },
    mutations: {
      onError: (error: Error) => {
        toast.error(error.message || "Ocorreu um erro. Tente novamente.");
      },
    },
  },
});

const PageLoader = () => (
  <div className="flex items-center justify-center min-h-screen bg-background">
    <Loader2 className="h-8 w-8 animate-spin text-primary" />
  </div>
);

const App = () => (
  <HelmetProvider>
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <ErrorBoundary>
        <BrowserRouter>
          <Suspense fallback={<PageLoader />}>
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
          </Suspense>
          <CookieBanner />
        </BrowserRouter>
      </ErrorBoundary>
    </TooltipProvider>
  </QueryClientProvider>
  </HelmetProvider>
);

export default App;
