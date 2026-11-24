import { useState } from "react";
import { AlertCircle, Flame, Search, ShieldAlert, Users } from "lucide-react";
import { StudentQueueTable } from "../../components/faculty/StudentQueueTable";
import { TimeMachineBar } from "../../components/faculty/TimeMachineBar";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { DashboardSkeleton, Skeleton } from "../../components/ui/Skeleton";
import { useDashboardSummary } from "../../hooks/useDashboardSummary";
import { useStudents } from "../../hooks/useStudents";
import { useTimeMachineState } from "../../hooks/useTimeMachineState";
import { formatPct } from "../../lib/utils";

interface FacultyDashboardProps {
  onSelectStudent: (studentId: number) => void;
}

export function FacultyDashboard({ onSelectStudent }: FacultyDashboardProps) {
  const [riskTier, setRiskTier] = useState<"SAFE" | "WATCH" | "AT_RISK" | "CRITICAL" | "">("");
  const [archetype, setArchetype] = useState("");
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState<"urgency" | "ponr" | "name">("urgency");

  const summary = useDashboardSummary();
  const tm = useTimeMachineState();
  const students = useStudents({
    risk_tier: riskTier || undefined,
    archetype: archetype || undefined,
    search: search.trim() || undefined,
    sort_by: sortBy,
    limit: 80,
  });

  if (summary.isLoading) return <DashboardSkeleton />;
  if (summary.isError) {
    return (
      <ErrorBanner
        title="Could not load cohort summary"
        message={summary.error instanceof Error ? summary.error.message : "Request failed"}
        onRetry={() => void summary.refetch()}
      />
    );
  }

  const kpi = summary.data;
  if (!kpi) {
    return (
      <EmptyState
        title="No cohort data available"
        description="Seed or upload student academic records to populate the early-warning queue."
      />
    );
  }

  const tmData = tm.query.data;
  const activeEngineMetrics = tmData
    ? tm.engine === "pulsegrid"
      ? tmData.pulsegrid
      : tmData.naive_static
    : null;
  const isLiveSnapshot =
    !activeEngineMetrics ||
    (tm.engine === "pulsegrid" && tm.selectedWeek === (kpi.active_week ?? kpi.current_week));
  const atRiskCriticalTotal = isLiveSnapshot
    ? kpi.at_risk_count + kpi.critical_count
    : activeEngineMetrics.flagged_count;
  const criticalSub = isLiveSnapshot
    ? `${kpi.critical_count} Critical · ${kpi.at_risk_count} At-Risk`
    : `${activeEngineMetrics.critical_count} Critical · ${activeEngineMetrics.at_risk_count} At-Risk (Wk ${tm.selectedWeek})`;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold tracking-tight text-slate-100">
          Cohort Early-Warning Triage
        </h1>
        <p className="mt-0.5 text-xs text-slate-400">
          Week {kpi.active_week ?? kpi.current_week} of {kpi.total_weeks} · Cohort-calibrated
          Z-scores, CUSUM shifts &amp; PONR deadlines
        </p>
      </div>

      {tmData ? (
        <TimeMachineBar
          data={tmData}
          selectedWeek={tm.selectedWeek}
          onSelectWeek={tm.selectWeek}
          playing={tm.playing}
          onTogglePlay={tm.togglePlay}
          engine={tm.engine}
          onSelectEngine={tm.setEngine}
        />
      ) : null}

      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          label="Total Cohort"
          value={String(kpi.total_students)}
          sub={`Avg projected: ${formatPct(kpi.avg_projected_score)}`}
          icon={Users}
          accent="text-slate-200"
        />
        <KpiCard
          label={tm.engine === "naive" ? "Naive Static Flagged" : "At-Risk & Critical"}
          value={String(atRiskCriticalTotal)}
          sub={criticalSub}
          icon={ShieldAlert}
          accent="text-rose-400"
        />
        <KpiCard
          label={activeEngineMetrics ? `False Alarms (Wk ${tm.selectedWeek})` : "CUSUM Silent Slippers"}
          value={String(
            activeEngineMetrics ? activeEngineMetrics.false_alarms_on_track : kpi.cusum_alerts_count,
          )}
          sub={
            activeEngineMetrics
              ? `Avoided vs Naive: ${tmData?.false_alarms_prevented ?? 0}`
              : "Baseline deviation change-points"
          }
          icon={Flame}
          accent={
            activeEngineMetrics && activeEngineMetrics.false_alarms_on_track > 0
              ? "text-rose-400"
              : "text-amber-400"
          }
        />
        <KpiCard
          label="Root-Cause Traps"
          value={String(kpi.detention_cliff_count + kpi.passive_copier_count)}
          sub={`${kpi.detention_cliff_count} Detention · ${kpi.passive_copier_count} Passive Copier`}
          icon={AlertCircle}
          accent="text-sky-400"
        />
      </section>

      <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
          <div className="relative min-w-[220px] flex-1">
            <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search student name or roll (e.g. Aarav, STU-002)..."
              className="w-full rounded-lg border border-slate-700 bg-slate-950 py-1.5 pl-9 pr-3 text-xs text-slate-100 placeholder:text-slate-500 focus:border-emerald-500 focus:outline-none"
            />
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <select
              aria-label="Filter by Risk Tier"
              value={riskTier}
              onChange={(e) => setRiskTier(e.target.value as typeof riskTier)}
              className="rounded-lg border border-slate-700 bg-slate-950 px-2.5 py-1.5 text-xs text-slate-200"
            >
              <option value="">All Tiers</option>
              <option value="CRITICAL">CRITICAL</option>
              <option value="AT_RISK">AT RISK</option>
              <option value="WATCH">WATCH</option>
              <option value="SAFE">SAFE</option>
            </select>

            <select
              aria-label="Filter by Archetype"
              value={archetype}
              onChange={(e) => setArchetype(e.target.value)}
              className="rounded-lg border border-slate-700 bg-slate-950 px-2.5 py-1.5 text-xs text-slate-200"
            >
              <option value="">All Archetypes</option>
              {kpi.archetype_distribution.map((a) => (
                <option key={a.label} value={a.label}>
                  {a.label} ({a.count})
                </option>
              ))}
            </select>

            <select
              aria-label="Sort Students"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
              className="rounded-lg border border-slate-700 bg-slate-950 px-2.5 py-1.5 text-xs text-slate-200"
            >
              <option value="urgency">Sort: Highest Risk</option>
              <option value="ponr">Sort: Earliest PONR</option>
              <option value="name">Sort: Name</option>
            </select>
          </div>
        </div>

        {students.isLoading ? (
          <div className="mt-4 space-y-2">
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        ) : students.isError ? (
          <div className="mt-4">
            <ErrorBanner
              message={
                students.error instanceof Error ? students.error.message : "Failed to load students"
              }
              onRetry={() => void students.refetch()}
            />
          </div>
        ) : !students.data?.items.length ? (
          <div className="mt-4">
            <EmptyState
              title="No students match your filters"
              description="Try clearing the search term or resetting the risk tier and archetype filters."
              action={
                <button
                  type="button"
                  onClick={() => {
                    setSearch("");
                    setRiskTier("");
                    setArchetype("");
                  }}
                  className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs text-slate-200 hover:bg-slate-700"
                >
                  Reset Filters
                </button>
              }
            />
          </div>
        ) : (
          <StudentQueueTable items={students.data.items} onSelectStudent={onSelectStudent} />
        )}
      </section>
    </div>
  );
}

function KpiCard({
  label,
  value,
  sub,
  icon: Icon,
  accent,
}: {
  label: string;
  value: string;
  sub: string;
  icon: typeof Users;
  accent: string;
}) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-slate-400">{label}</span>
        <Icon className={`h-4 w-4 ${accent}`} />
      </div>
      <div className={`mt-2 text-2xl font-bold tracking-tight ${accent}`}>{value}</div>
      <p className="mt-1 text-[11px] text-slate-400">{sub}</p>
    </div>
  );
}
