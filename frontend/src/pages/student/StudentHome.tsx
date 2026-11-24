import { AlertTriangle, ArrowRight, CheckCircle2, Flame } from "lucide-react";
import { TrajectoryChart } from "../../components/charts/TrajectoryChart";
import { ArchetypeBadge, PONRBadge, RiskTierBadge } from "../../components/ui/Badge";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { DashboardSkeleton } from "../../components/ui/Skeleton";
import { useStudentAnalytics } from "../../hooks/useStudentAnalytics";
import { useAuth } from "../../lib/auth";
import { formatPct, formatPonrMargin } from "../../lib/utils";

interface StudentHomeProps {
  onOpenRecovery: () => void;
}

export function StudentHome({ onOpenRecovery }: StudentHomeProps) {
  const { studentId } = useAuth();
  const analytics = useStudentAnalytics(studentId ?? 1);

  if (analytics.isLoading) return <DashboardSkeleton />;
  if (analytics.isError) {
    return (
      <ErrorBanner
        title="Could not load your academic dashboard"
        message={analytics.error instanceof Error ? analytics.error.message : "Failed to fetch"}
        onRetry={() => void analytics.refetch()}
      />
    );
  }

  const data = analytics.data;
  if (!data) {
    return (
      <EmptyState
        title="No student profile found"
        description="Switch persona in the top bar or ask your coordinator to sync your records."
      />
    );
  }

  const urgentPonr = data.ponr.filter(
    (p) =>
      p.eligibility_status === "WINDOW_CLOSING" ||
      p.eligibility_status === "UNRECOVERABLE_WITHOUT_WAIVER",
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-xl font-bold text-slate-100">Welcome back, {data.name}</h1>
            <RiskTierBadge tier={data.risk_tier} />
            <ArchetypeBadge archetype={data.archetype} />
          </div>
          <p className="mt-0.5 text-xs text-slate-400">
            {data.roll_no} · Projected Final Score:{" "}
            <span className="font-semibold text-slate-200">
              {formatPct(data.projected_final_score)}
            </span>{" "}
            · Target after recovery:{" "}
            <span className="font-semibold text-emerald-300">
              {formatPct(data.recovery_plan.projected_score_after)}
            </span>
          </p>
        </div>

        <button
          type="button"
          onClick={onOpenRecovery}
          className="inline-flex items-center gap-2 rounded-lg bg-emerald-500 px-4 py-2 text-xs font-semibold text-slate-950 transition hover:bg-emerald-400"
        >
          Open What-If Recovery Simulator
          <ArrowRight className="h-4 w-4" />
        </button>
      </div>

      {urgentPonr.length > 0 ? (
        <div
          role="status"
          className="rounded-xl border border-amber-500/50 bg-amber-950/30 p-4 text-amber-100"
        >
          <div className="flex items-start gap-3">
            <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-400" />
            <div>
              <p className="text-sm font-semibold">
                Attendance Point-of-No-Return Alert ({urgentPonr[0].eligibility_status.replace(/_/g, " ")})
              </p>
              <p className="mt-1 text-xs text-amber-200/90">
                {urgentPonr
                  .map((s) => {
                    const sessions = s.bunk_budget_sessions ?? s.bunk_budget;
                    return `${s.subject_code} (${s.subject_name}): ${s.current_pct.toFixed(1)}% now — must attend ${s.min_future_needed} of ${s.remaining_sessions} remaining sessions (${formatPonrMargin(sessions, s.sessions_per_week)}; bunk budget: ${sessions}).`;
                  })
                  .join(" ")}
              </p>
            </div>
          </div>
        </div>
      ) : data.cusum_triggered ? (
        <div className="rounded-xl border border-rose-500/40 bg-rose-950/25 p-4 text-rose-100">
          <div className="flex items-start gap-3">
            <Flame className="mt-0.5 h-5 w-5 shrink-0 text-rose-400" />
            <div>
              <p className="text-sm font-semibold">
                Early Momentum Shift Detected at Week {data.cusum_week}
              </p>
              <p className="mt-1 text-xs text-rose-200/80">
                Your performance stepped down relative to your own Weeks 1–4 baseline. Review the
                Recovery &amp; What-If simulator to map a fast bounce-back.
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="rounded-xl border border-emerald-500/30 bg-emerald-950/20 p-4 text-emerald-100">
          <div className="flex items-start gap-3">
            <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-emerald-400" />
            <div>
              <p className="text-sm font-semibold">All Subjects Currently Clear of Immediate PONR</p>
              <p className="mt-1 text-xs text-emerald-200/80">
                {data.recovery_plan.summary}
              </p>
            </div>
          </div>
        </div>
      )}

      <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
        <h2 className="text-sm font-semibold text-slate-200">
          Your Semester Trajectory &amp; Cohort Benchmark
        </h2>
        <p className="mb-3 text-[11px] text-slate-400">
          Compares your raw composite against cohort-calibrated Z-scores (hard exams do not inflate risk).
        </p>
        <TrajectoryChart
          data={data.weekly_trajectory}
          cusumTriggered={data.cusum_triggered}
          cusumWeek={data.cusum_week}
        />
      </section>

      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {data.ponr.map((subj) => (
          <div
            key={subj.subject_id}
            className="rounded-xl border border-slate-800 bg-slate-900/70 p-4"
          >
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="text-xs font-mono text-slate-400">
                  {subj.subject_code} · {subj.subject_type}
                </p>
                <h3 className="text-sm font-semibold text-slate-100">{subj.subject_name}</h3>
              </div>
              <PONRBadge status={subj.eligibility_status} />
            </div>

            <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
              <div>
                <p className="text-[11px] text-slate-400">Attendance (≥75%)</p>
                <p className="font-mono font-semibold text-slate-100">
                  {formatPct(subj.current_pct)}
                </p>
              </div>
              <div>
                <p className="text-[11px] text-slate-400">PONR Margin</p>
                <p className="font-mono text-[11px] font-semibold text-slate-100">
                  {formatPonrMargin(subj.bunk_budget_sessions ?? subj.bunk_budget, subj.sessions_per_week)}
                </p>
              </div>
              <div>
                <p
                  className="text-[11px] text-slate-400"
                  title="40% per-subject minimum internal assessment required"
                >
                  Internal (≥40%)
                </p>
                <p className="font-mono font-semibold text-slate-100">
                  {formatPct(subj.internal_standing.average_pct * 100)}
                </p>
              </div>
            </div>
          </div>
        ))}
      </section>
    </div>
  );
}
