import { Sidebar } from "./Sidebar";
import { cn } from "@/lib/utils";

interface MainLayoutProps {
  children: React.ReactNode;
  className?: string;
}

export function MainLayout({ children, className }: MainLayoutProps) {
  return (
    <div className="min-h-screen">
      <Sidebar />
      <main className={cn(
        "md:ml-64 min-h-screen p-4 md:p-8",
        className
      )}>
        {children}
      </main>
    </div>
  );
}
