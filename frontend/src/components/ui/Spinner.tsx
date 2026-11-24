import { Loader2 } from "lucide-react";
import { cn } from "../../lib/utils";

export function Spinner({ className, label }: { className?: string; label?: string }) {
  return (
    <div className={cn("inline-flex items-center gap-2 text-slate-300", className)}>
      <Loader2 className="h-4 w-4 animate-spin text-emerald-400" />
      {label ? <span className="text-xs font-medium">{label}</span> : null}
    </div>
  );
}
