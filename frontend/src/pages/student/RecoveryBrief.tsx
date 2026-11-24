import { ArrowLeft, Printer } from "lucide-react";
import { MentorAlertDigest } from "../../components/MentorAlertDigest";
import { TrajectoryChart } from "../../components/charts/TrajectoryChart";
import { ArchetypeBadge, PONRBadge, RiskTierBadge } from "../../components/ui/Badge";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { DashboardSkeleton } from "../../components/ui/Skeleton";
import { useResolvedStudentId } from "../../hooks/useResolvedStudentId";
import { useStudentAnalytics } from "../../hooks/useStudentAnalytics";
import { useAuth } from "../../lib/auth";
import { formatPct, formatPonrMargin } from "../../lib/utils";

interface RecoveryBriefProps {
  studentRef?: number | string;
  onBack?: () => void;
}

export function RecoveryBrief({ studentRef, onBack }: RecoveryBriefProps) {
  const { studentId } = useAuth();
  const resolved = useResolvedStudentId(studentRef);
  const targetId = studentRef !== undefined ? resolved.studentId : (studentId ?? 1);
  const analytics = useStudentAnalytics(targetId);

  if (resolved.isResolving || analytics.isLoading) return <DashboardSkeleton />;
  if (analytics.isError) {
    return (
      <ErrorBanner
        title="Unable to load recovery brief"
        message={analytics.error instanceof Error ? analytics.error.message : "Request failed"}
        onRetry={() => void analytics.refetch()}
      />
    );
  }

  const data = analytics.data;
  if (!data) {
    return (
      <EmptyState
        title="No recovery brief available"
        description="Select a student profile to generate the printable recovery brief."
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="no-print flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          {onBack ? (
            <button
              type="button"
              onClick={onBack}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-800"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              Back
            </button>
          ) : null}
          <div>
            <h1 className="text-xl font-bold text-slate-100">Printable Recovery Brief</h1>
            <p className="text-xs text-slate-400">
              Clean 1-page action brief optimized for PDF export and advisor handoff.
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => window.print()}
          className="inline-flex items-center gap-2 rounded-lg bg-sky-500 px-4 py-2 text-xs font-semibold text-slate-950 transition hover:bg-sky-400"
        >
          <Printer className="h-4 w-4" />
          Print / Save PDF
        </button>
      </div>

      <article className="space-y-5 rounded-xl border border-slate-800 bg-slate-900/70 p-6 print-sheet">
        <header className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-800 pb-4">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-wider text-emerald-400">
              PulseGrid Academic Recovery Brief · Week {data.active_week ?? 9} /{" "}
              {data.total_weeks ?? 14}
            </p>
            <h2 className="mt-1 text-2xl font-bold text-slate-100">
              {data.name} ({data.roll_no})
            </h2>
            <p className="text-xs text-slate-400">
              {data.program} · Year {data.year}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <RiskTierBadge tier={data.risk_tier} />
            <ArchetypeBadge archetype={data.archetype} />
          </div>
        </header>

        <section className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <BriefStat label="Risk Score" value={`${data.risk_score.toFixed(1)} / 100`} />
          <BriefStat label="Current Projection" value={formatPct(data.projected_final_score)} />
          <BriefStat
            label="Post-Recovery Target"
            value={formatPct(data.recovery_plan.projected_score_after)}
          />
          <BriefStat
            label="CUSUM Change-Point"
            value={data.cusum_triggered ? `Week ${data.cusum_week}` : "None"}
          />
        </section>

        <section>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
            Weekly Trajectory &amp; Cohort Benchmark (Printable SVG)
          </h3>
          <TrajectoryChart
            data={data.weekly_trajectory}
            cusumTriggered={data.cusum_triggered}
            cusumWeek={data.cusum_week}
            lightMode
          />
        </section>

        <section>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
            Prescribed Counterfactual Action Plan
          </h3>
          <p className="mb-3 text-xs text-slate-300">{data.recovery_plan.summary}</p>
          <ul className="space-y-2">
            {data.recovery_plan.recovery_steps.map((step, i) => (
              <li
                key={`${step.feature}-${i}`}
                className="flex items-center justify-between gap-3 rounded-lg border border-slate-800 bg-slate-950/60 p-3 text-xs"
              >
                <div>
                  <p className="font-semibold text-slate-100">{step.label}</p>
                  <p className="text-slate-400">{step.action}</p>
                </div>
                <span className="font-mono font-semibold text-emerald-300">
                  {formatPct(step.current_pct, 0)} → {formatPct(step.target_pct, 0)}
                </span>
              </li>
            ))}
          </ul>
        </section>

        <section>
          <div className="mb-2 flex flex-wrap items-baseline justify-between gap-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Subject Attendance &amp; Internal Eligibility Standing
            </h3>
            <span className="text-[11px] text-slate-400">
              Policy: 75% per-subject attendance &amp; 40% per-subject minimum internal assessment
            </span>
          </div>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            {data.ponr.map((subj) => (
              <div
                key={subj.subject_id}
                className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-950/50 px-3 py-2 text-xs"
              >
                <div>
                  <span className="font-semibold text-slate-200">{subj.subject_code}</span>{" "}
                  <span className="text-slate-400">({formatPct(subj.current_pct)})</span>
                  <p className="text-[11px] text-slate-400">
                    Need {subj.min_future_needed}/{subj.remaining_sessions} ·{" "}
                    {formatPonrMargin(
                      subj.bunk_budget_sessions ?? subj.bunk_budget,
                      subj.sessions_per_week,
                    )}
                  </p>
                </div>
                <PONRBadge status={subj.eligibility_status} />
              </div>
            ))}
          </div>
        </section>
      </article>

      <MentorAlertDigest data={data} />
    </div>
  );
}

function BriefStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3">
      <p className="text-[11px] text-slate-400">{label}</p>
      <p className="mt-1 font-mono text-base font-bold text-slate-100">{value}</p>
    </div>
  );
}
