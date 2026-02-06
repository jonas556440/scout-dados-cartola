import { cn } from "@/lib/utils";
import { motion } from "framer-motion";
import { LucideIcon } from "lucide-react";

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: LucideIcon;
  trend?: number;
  variant?: 'default' | 'primary' | 'secondary' | 'success' | 'warning';
  className?: string;
}

const variantStyles = {
  default: "text-foreground",
  primary: "text-primary",
  secondary: "text-secondary",
  success: "text-success",
  warning: "text-warning",
};

const iconBgStyles = {
  default: "bg-muted",
  primary: "bg-primary/20",
  secondary: "bg-secondary/20",
  success: "bg-success/20",
  warning: "bg-warning/20",
};

export function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  variant = 'default',
  className,
}: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn("stat-card", className)}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm text-muted-foreground mb-1">{title}</p>
          <div className="flex items-baseline gap-2">
            <span className={cn("text-2xl font-display font-bold", variantStyles[variant])}>
              {value}
            </span>
            {trend !== undefined && (
              <span className={cn(
                "text-xs font-medium",
                trend >= 0 ? "text-success" : "text-destructive"
              )}>
                {trend >= 0 ? '+' : ''}{trend}%
              </span>
            )}
          </div>
          {subtitle && (
            <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>
          )}
        </div>
        
        {Icon && (
          <div className={cn(
            "p-2 rounded-lg",
            iconBgStyles[variant]
          )}>
            <Icon className={cn("w-5 h-5", variantStyles[variant])} />
          </div>
        )}
      </div>
    </motion.div>
  );
}
