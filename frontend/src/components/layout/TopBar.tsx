import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../../api/client";
import { RoleSwitcher } from "../ui/RoleSwitcher";

interface TopBarProps {
  onRoleChanged: (role: "faculty" | "student") => void;
}

export function TopBar({ onRoleChanged }: TopBarProps) {
  const healthQuery = useQuery({
    queryKey: ["health"],
    queryFn: ({ signal }) => apiClient.getHealth(signal),
    staleTime: 60_000,
  });

  const healthy = healthQuery.data?.status === "ok" && healthQuery.data?.model_loaded;

  return (
    <header className="no-print flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 bg-slate-950/90 px-4 py-3 sm:px-6">
      <div className="flex items-center gap-3">
        <span
          className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[11px] font-medium ${
            healthy
              ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-300"
              : "border-amber-500/40 bg-amber-500/10 text-amber-300"
          }`}
        >
          <span
            className={`h-1.5 w-1.5 rounded-full ${healthy ? "bg-emerald-400" : "bg-amber-400"}`}
          />
          {healthQuery.data
            ? `Week ${healthQuery.data.active_week ?? 9} / ${healthQuery.data.total_weeks ?? 14} · ${healthQuery.data.dataset_count} Students`
            : "Connecting..."}
        </span>
      </div>

      <RoleSwitcher onRoleChanged={onRoleChanged} />
    </header>
  );
}
