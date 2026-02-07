import { cn } from "@/lib/utils";
import { Link, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import {
  LayoutDashboard,
  Users,
  Trophy,
  TrendingUp,
  History,
  Swords,
  BarChart3,
  Menu,
  X,
  Shield,
  FileText,
  Star,
  Newspaper,
} from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { useDashboard } from "@/hooks/useCartolaApi";

const navSections = [
  {
    header: "Brasileirão",
    emoji: "🏆",
    items: [
      { icon: Trophy, label: 'Classificação', href: '/brasileirao' },
      { icon: Swords, label: 'Confrontos', href: '/confrontos' },
    ],
  },
  {
    header: "Cartola FC",
    emoji: "⚽",
    items: [
      { icon: LayoutDashboard, label: 'Dashboard', href: '/dashboard' },
      { icon: Users, label: 'Escalação', href: '/escalacao' },
      { icon: TrendingUp, label: 'Mercado', href: '/mercado' },
      { icon: Star, label: 'Scouts', href: '/scouts' },
      { icon: History, label: 'Histórico', href: '/historico' },
    ],
  },
  {
    header: "Análises",
    emoji: "📊",
    items: [
      { icon: BarChart3, label: 'Estatísticas', href: '/estatisticas' },
      { icon: Newspaper, label: 'Blog', href: '/blog' },
    ],
  },
];

export function Sidebar() {
  const location = useLocation();
  const [isOpen, setIsOpen] = useState(false);
  const { data: dashboardData } = useDashboard();

  const rodada = dashboardData?.mercado?.rodadaAtual || 1;
  const statusMercado = dashboardData?.mercado?.status === 'aberto' ? 'Mercado Aberto' : 'Mercado Fechado';
  const patrimonio = dashboardData?.patrimonio ?? 100.0;

  // Rotas do Cartola FC (onde faz sentido mostrar rodada/patrimônio)
  const cartolaRoutes = ['/', '/escalacao', '/mercado', '/historico'];
  const isCartolaRoute = cartolaRoutes.includes(location.pathname);

  return (
    <>
      {/* Mobile Toggle */}
      <Button
        variant="ghost"
        size="icon"
        className="fixed top-4 left-4 z-50 md:hidden"
        onClick={() => setIsOpen(!isOpen)}
      >
        {isOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
      </Button>

      {/* Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-background/80 backdrop-blur-sm z-40 md:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed left-0 top-0 h-screen w-64 bg-sidebar border-r border-sidebar-border z-50 transition-transform duration-300",
          "md:translate-x-0",
          isOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        )}
      >
        {/* Logo */}
        <div className="flex items-center gap-3 p-6 border-b border-sidebar-border">
          <div className="w-10 h-10 rounded-xl hero-gradient flex items-center justify-center">
            <span className="text-lg font-bold text-primary-foreground">S</span>
          </div>
          <div>
            <h1 className="font-display text-lg font-bold">ScoutDados</h1>
            <p className="text-xs text-muted-foreground">Estatísticas & Cartola</p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="p-4 space-y-1 overflow-y-auto" style={{ maxHeight: 'calc(100vh - 240px)' }}>
          {navSections.map((section) => (
            <div key={section.header}>
              <div className="text-xs uppercase text-muted-foreground tracking-wider mt-4 mb-2 px-3 flex items-center gap-1.5">
                <span>{section.emoji}</span>
                <span>{section.header}</span>
              </div>
              {section.items.map((item) => {
                const isActive = location.pathname === item.href;
                
                return (
                  <Link
                    key={item.href}
                    to={item.href}
                    onClick={() => setIsOpen(false)}
                    className={cn(
                      "flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200",
                      "hover:bg-sidebar-accent",
                      isActive && "bg-sidebar-accent text-sidebar-primary"
                    )}
                  >
                    {isActive && (
                      <motion.div
                        layoutId="activeNav"
                        className="absolute left-0 w-1 h-8 bg-sidebar-primary rounded-r-full"
                      />
                    )}
                    <item.icon className={cn(
                      "w-5 h-5 transition-colors",
                      isActive ? "text-sidebar-primary" : "text-sidebar-foreground/60"
                    )} />
                    <span className={cn(
                      "font-medium transition-colors",
                      isActive ? "text-sidebar-foreground" : "text-sidebar-foreground/60"
                    )}>
                      {item.label}
                    </span>
                  </Link>
                );
              })}
            </div>
          ))}
        </nav>

        {/* Bottom Section */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-sidebar-border">
          {/* Legal Links */}
          <div className="flex items-center gap-3 mb-3 px-2">
            <Link to="/privacidade" onClick={() => setIsOpen(false)} className="text-[10px] text-sidebar-foreground/40 hover:text-sidebar-foreground/80 transition-colors flex items-center gap-1">
              <Shield className="w-3 h-3" />Privacidade
            </Link>
            <Link to="/termos" onClick={() => setIsOpen(false)} className="text-[10px] text-sidebar-foreground/40 hover:text-sidebar-foreground/80 transition-colors flex items-center gap-1">
              <FileText className="w-3 h-3" />Termos
            </Link>
          </div>
          
          {/* Rodada/Patrimônio: só em rotas do Cartola FC */}
          {isCartolaRoute && (
            <div className="glass-card p-4">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
                  <TrendingUp className="w-4 h-4 text-primary" />
                </div>
                <div>
                  <div className="text-sm font-semibold">Rodada {rodada}</div>
                  <div className="text-xs text-muted-foreground">{statusMercado}</div>
                </div>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Patrimônio</span>
                <span className="font-bold text-primary">C${patrimonio.toFixed(1)}</span>
              </div>
            </div>
          )}
        </div>
      </aside>
    </>
  );
}
