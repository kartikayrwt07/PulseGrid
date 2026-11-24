import { Inbox } from "lucide-react";
import type { ReactNode } from "react";

interface EmptyStateProps {
  title: string;
  description: string;
  action?: ReactNode;
}

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-800 bg-slate-900/50 px-6 py-12 text-center">
      <Inbox className="h-9 w-9 text-slate-500" />
      <h3 className="mt-3 text-sm font-semibold text-slate-200">{title}</h3>
      <p className="mt-1 max-w-md text-xs text-slate-400">{description}</p>
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}
