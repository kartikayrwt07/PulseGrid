import {
  Activity,
  BarChart3,
  ClipboardCheck,
  Compass,
  FileSpreadsheet,
  FileText,
  LayoutDashboard,
  ScatterChart as ScatterIcon,
  SlidersHorizontal,
  UserCheck,
} from "lucide-react";
import { useAuth } from "../../lib/auth";
import { cn } from "../../lib/utils";

export type AppRoute =
  | { page: "faculty-dashboard" }
  | { page: "faculty-triage" }
  | { page: "faculty-upload" }
  | { page: "faculty-interventions" }
  | { page: "faculty-audit" }
  | { page: "faculty-student"; studentRef: number | string }
  | { page: "faculty-brief"; studentRef: number | string }
  | { page: "student-home" }
  | { page: "student-recovery" }
  | { page: "student-brief" };

interface SidebarProps {
  route: AppRoute;
  onNavigate: (next: AppRoute) => void;
}

export function Sidebar({ route, onNavigate }: SidebarProps) {
  const { role } = useAuth();

  const facultyItems = [
    {
      label: "Cohort Triage",
      icon: LayoutDashboard,
      active: route.page === "faculty-dashboard",
      onClick: () => onNavigate({ page: "faculty-dashboard" }),
    },
    {
      label: "Triage Matrix",
      icon: ScatterIcon,
      active: route.page === "faculty-triage",
      onClick: () => onNavigate({ page: "faculty-triage" }),
    },
    {
      label: "Student Drilldown",
      icon: UserCheck,
      active: route.page === "faculty-student",
      onClick: () =>
        onNavigate({
          page: "faculty-student",
          studentRef: route.page === "faculty-student" ? route.studentRef : 1,
        }),
    },
    {
      label: "Interventions",
      icon: ClipboardCheck,
      active: route.page === "faculty-interventions",
      onClick: () => onNavigate({ page: "faculty-interventions" }),
    },
    {
      label: "CSV / XLSX Upload",
      icon: FileSpreadsheet,
      active: route.page === "faculty-upload",
      onClick: () => onNavigate({ page: "faculty-upload" }),
    },
    {
      label: "Model Audit",
      icon: BarChart3,
      active: route.page === "faculty-audit",
      onClick: () => onNavigate({ page: "faculty-audit" }),
    },
  ];

  const studentItems = [
    {
      label: "My Academic Pulse",
      icon: Compass,
      active: route.page === "student-home",
      onClick: () => onNavigate({ page: "student-home" }),
    },
    {
      label: "Recovery & What-If",
      icon: SlidersHorizontal,
      active: route.page === "student-recovery",
      onClick: () => onNavigate({ page: "student-recovery" }),
    },
    {
      label: "Recovery Brief",
      icon: FileText,
      active: route.page === "student-brief",
      onClick: () => onNavigate({ page: "student-brief" }),
    },
  ];

  const items = role === "faculty" ? facultyItems : studentItems;

  return (
    <aside className="no-print flex w-full shrink-0 flex-col border-b border-slate-800 bg-slate-900/70 p-4 md:w-60 md:border-b-0 md:border-r">
      <div className="flex items-center gap-2.5 px-2 pb-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/20 text-emerald-400">
          <Activity className="h-5 w-5" />
        </div>
        <div>
          <span className="text-base font-bold tracking-tight text-slate-100">PulseGrid</span>
          <p className="text-[10px] uppercase tracking-wider text-slate-400">
            Early-Warning Engine
          </p>
        </div>
      </div>

      <nav className="flex flex-wrap gap-1.5 md:flex-col">
        {items.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.label}
              type="button"
              onClick={item.onClick}
              className={cn(
                "flex items-center gap-2.5 rounded-lg px-3 py-2 text-xs font-medium transition",
                item.active
                  ? "bg-slate-800 text-emerald-300 shadow-sm"
                  : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200",
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="mt-auto hidden rounded-lg border border-slate-800 bg-slate-950/60 p-3 text-[11px] text-slate-400 md:block">
        <p className="font-semibold text-slate-300">Policy Calibration</p>
        <p className="mt-1">75% Per-Subject Att · 40% Per-Subject IA Min · 14-Wk Sem</p>
      </div>
    </aside>
  );
}
