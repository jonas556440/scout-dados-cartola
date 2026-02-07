import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

interface IconWithTooltipProps {
  icon: React.ReactNode;
  tooltip: string;
  className?: string;
  side?: "top" | "right" | "bottom" | "left";
}

export function IconWithTooltip({ 
  icon, 
  tooltip, 
  className,
  side = "top" 
}: IconWithTooltipProps) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div className={cn("inline-flex cursor-help", className)} aria-label={tooltip}>
          {icon}
        </div>
      </TooltipTrigger>
      <TooltipContent side={side}>
        <p className="text-sm">{tooltip}</p>
      </TooltipContent>
    </Tooltip>
  );
}
