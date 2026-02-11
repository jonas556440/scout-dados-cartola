import { Sidebar } from "./Sidebar";
import { cn } from "@/lib/utils";

interface MainLayoutProps {
  children: React.ReactNode;
  className?: string;
}

export function MainLayout({ children, className }: MainLayoutProps) {
  return (
    <div className="min-h-screen">
      {/* WCAG 2.4.1 — Skip to main content */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary focus:text-primary-foreground focus:rounded-md"
      >
        Pular para conteúdo principal
      </a>
      <Sidebar />
      <main
        id="main-content"
        className={cn(
          "md:ml-64 min-h-screen p-4 md:p-8",
          className
        )}
      >
        {children}
      </main>
    </div>
  );
}
