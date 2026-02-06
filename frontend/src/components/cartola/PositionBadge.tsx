import { cn } from "@/lib/utils";
import type { Position } from "@/types/cartola";
import { POSITION_COLORS } from "@/types/cartola";

interface PositionBadgeProps {
  position: Position;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

const sizeClasses = {
  sm: 'px-1.5 py-0.5 text-[10px]',
  md: 'px-2 py-1 text-xs',
  lg: 'px-3 py-1.5 text-sm',
};

export function PositionBadge({ position, className, size = 'md' }: PositionBadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center justify-center font-bold rounded-md',
        POSITION_COLORS[position],
        sizeClasses[size],
        className
      )}
    >
      {position}
    </span>
  );
}
