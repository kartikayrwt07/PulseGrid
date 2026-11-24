import { useState } from "react";
import { ArrowLeft, CheckCircle2, ClipboardPlus, FileText, Sparkles } from "lucide-react";
import { MentorAlertDigest } from "../../components/MentorAlertDigest";
import { InterventionDrawer } from "../../components/faculty/InterventionDrawer";
import { TrajectoryChart } from "../../components/charts/TrajectoryChart";
import { WaterfallChart } from "../../components/charts/WaterfallChart";
import { ArchetypeBadge, PONRBadge, RiskTierBadge } from "../../components/ui/Badge";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { DashboardSkeleton } from "../../components/ui/Skeleton";
import { useInterventions } from "../../hooks/useInterventions";
import { useResolvedStudentId } from "../../hooks/useResolvedStudentId";
import { useStudentAnalytics } from "../../hooks/useStudentAnalytics";
import { HERO_PERSONAS, formatPct, formatPonrMargin } from "../../lib/utils";

interface StudentDetailProps {
  studentRef: number | string;
  onBack: () => void;
  onSelectStudent: (id: number) => void;
  onOpenBrief?: () => void;
}

export function StudentDetail({
  studentRef,
  onBack,
  onSelectStudent,
  onOpenBrief,
}: StudentDetailProps) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [toastMsg, setToastMsg] = useState<string | null>(null);
  const resolved = useResolvedStudentId(studentRef);
  const analytics = useStudentAnalytics(resolved.studentId);
  const ivQuery = useInterventions(resolved.studentId ?? undefined);

  if (resolved.isResolving || analytics.isLoading) return <DashboardSkeleton />;
  if (resolved.resolveError || analytics.isError) {
    const err = resolved.resolveError ?? analytics.error;
    return (
      <ErrorBanner
        title="Could not load student analytics"
        message={err instanceof Error ? err.message : "Failed to fetch analytics"}
        onRetry={() => void analytics.refetch()}
      />
    );
  }

  const data = analytics.data;
  if (!data) {
    return (
      <EmptyState
        title="Student not found"
        description="Select a student from the support queue to inspect full risk and recovery telemetry."
      />
    );
  }

  const latestIvWeek = ivQuery.data?.items?.[0]?.week ?? null;

  return (
    <div className="space-y-6">
      {toastMsg ? (
        <div className="flex items-center justify-between rounded-xl border border-emerald-500/40 bg-emerald-950/35 px-4 py-2.5 text-xs text-emerald-200">
          <span className="inline-flex items-center gap-1.5 font-medium">
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            {toastMsg}
          </span>
          <button
            type="button"
            onClick={() => setToastMsg(null)}
            className="text-slate-400 hover:text-slate-100"
          >
            Dismiss
          </button>
        </div>
      ) : null}

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onBack}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-800"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Queue
          </button>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-xl font-bold text-slate-100">{data.name}</h1>
              <span className="text-xs font-mono text-slate-400">{data.roll_no}</span>
              <RiskTierBadge tier={data.risk_tier} />
              <ArchetypeBadge archetype={data.primary_archetype ?? data.archetype} />
              {(data.secondary_flags ?? []).map((flag) => (
                <span
                  key={flag}
                  className="inline-flex items-center rounded-md border border-slate-600/70 bg-slate-900/70 px-2 py-0.5 text-[11px] font-medium text-slate-300"
                >
                  +{flag.replace(/_/g, " ").toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase())}
                </span>
              ))}
              {latestIvWeek ? (
                <span className="inline-flex items-center rounded-md border border-emerald-500/40 bg-emerald-500/15 px-2 py-0.5 text-[11px] font-semibold text-emerald-300">
                  Intervened (Week {latestIvWeek})
                </span>
              ) : null}
            </div>
            <p className="mt-0.5 text-xs text-slate-400">
              {data.program} · Year {data.year} · Risk Score {data.risk_score.toFixed(1)}/100
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-1.5">
          <button
            type="button"
            onClick={() => setDrawerOpen(true)}
            className="inline-flex items-center gap-1.5 rounded-md bg-emerald-500 px-2.5 py-1 text-[11px] font-semibold text-slate-950 hover:bg-emerald-400"
          >
            <ClipboardPlus className="h-3.5 w-3.5" />
            Log Intervention
          </button>
          {onOpenBrief ? (
            <button
              type="button"
              onClick={onOpenBrief}
              className="inline-flex items-center gap-1.5 rounded-md border border-sky-500/40 bg-sky-500/15 px-2.5 py-1 text-[11px] font-medium text-sky-300 hover:bg-sky-500/25"
            >
              <FileText className="h-3.5 w-3.5" />
              Print Brief
            </button>
          ) : null}
          {HERO_PERSONAS.map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => onSelectStudent(p.id)}
              className={`rounded-md border px-2.5 py-1 text-[11px] font-medium transition ${
                p.id === data.student_id
                  ? "border-emerald-500/50 bg-emerald-500/15 text-emerald-300"
                  : "border-slate-800 bg-slate-900 text-slate-400 hover:text-slate-200"
              }`}
            >
              {p.name.split(" ")[0]}
            </button>
          ))}
        </div>
      </div>

      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatBox
          label="Projected Final Score"
          value={formatPct(data.projected_final_score)}
          note={`Recoverable to ${formatPct(data.recovery_plan.projected_score_after)}`}
        />
        <StatBox
          label="CUSUM Change-Point"
          value={data.cusum_triggered ? `Week ${data.cusum_week}` : "No Shift"}
          note={`Baseline ${data.cusum.baseline_mean.toFixed(2)}σ`}
        />
        <StatBox
          label="Assign–Internal Divergence"
          value={`${data.divergence_index >= 0 ? "+" : ""}${data.divergence_index.toFixed(2)}σ`}
          note={data.divergence_index > 1.5 ? "Flagged Comfort Trap (>1.5σ)" : "Within normal spread"}
        />
        <StatBox
          label="Tightest PONR Window"
          value={data.ponr_days_left <= 0 ? "Urgent (≤0d)" : `${data.ponr_days_left} days left`}
          note="75% per-subject attendance rule"
        />
      </section>

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <h2 className="text-sm font-semibold text-slate-200">
            Weekly Trajectory &amp; Cohort Z-Score
          </h2>
          <p className="mb-3 text-[11px] text-slate-400">
            Dual-axis raw % vs cohort-calibrated σ; red marker shows CUSUM trigger week.
          </p>
          <TrajectoryChart
            data={data.weekly_trajectory}
            cusumTriggered={data.cusum_triggered}
            cusumWeek={data.cusum_week}
          />
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <h2 className="text-sm font-semibold text-slate-200">
            SHAP Root-Cause Attribution
          </h2>
          <p className="mb-3 text-[11px] text-slate-400">
            Red bars push risk higher; green bars protect performance.
          </p>
          <WaterfallChart entries={data.shap_values} groupedEntries={data.grouped_shap} />
        </div>
      </section>

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 lg:col-span-2">
          <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
            <h2 className="text-sm font-semibold text-slate-200">
              Per-Subject PONR &amp; Attendance Standing
            </h2>
            <span className="text-[11px] text-slate-400">
              75% per-subject attendance · 40% per-subject minimum internal assessment
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-slate-800 text-[11px] uppercase text-slate-400">
                <tr>
                  <th className="py-2 pr-3">Subject</th>
                  <th className="py-2 pr-3">Type</th>
                  <th className="py-2 pr-3">Att %</th>
                  <th className="py-2 pr-3">PONR Margin</th>
                  <th className="py-2 pr-3">Need / Left</th>
                  <th className="py-2 pr-3">Internal Avg</th>
                  <th className="py-2">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/70">
                {data.ponr.map((subj) => {
                  const marginSessions = subj.bunk_budget_sessions ?? subj.bunk_budget;
                  return (
                    <tr key={subj.subject_id}>
                      <td className="py-2 pr-3 font-medium text-slate-200">
                        {subj.subject_code} · {subj.subject_name}
                      </td>
                      <td className="py-2 pr-3 text-slate-400">{subj.subject_type}</td>
                      <td className="py-2 pr-3 font-mono">{formatPct(subj.current_pct)}</td>
                      <td className="py-2 pr-3 font-mono text-[11px] text-slate-200">
                        {formatPonrMargin(marginSessions, subj.sessions_per_week)}
                      </td>
                      <td className="py-2 pr-3 font-mono">
                        {subj.min_future_needed} / {subj.remaining_sessions}
                      </td>
                      <td className="py-2 pr-3 font-mono">
                        {formatPct(subj.internal_standing.average_pct * 100)}
                      </td>
                      <td className="py-2">
                        <PONRBadge status={subj.eligibility_status} />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-emerald-400" />
            <h2 className="text-sm font-semibold text-slate-200">Counterfactual Recovery Plan</h2>
          </div>
          <p className="mt-2 text-xs text-slate-300">{data.recovery_plan.summary}</p>
          <ul className="mt-4 space-y-2.5">
            {data.recovery_plan.recovery_steps.map((step, i) => (
              <li
                key={`${step.feature}-${step.subject}-${i}`}
                className="rounded-lg border border-slate-800 bg-slate-950/70 p-2.5 text-xs"
              >
                <div className="flex items-center justify-between font-semibold text-emerald-300">
                  <span className="inline-flex items-center gap-1.5">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    {step.label}
                  </span>
                  <span className="font-mono">
                    {formatPct(step.current_pct, 0)} → {formatPct(step.target_pct, 0)}
                  </span>
                </div>
                <p className="mt-1 text-[11px] text-slate-400">{step.action}</p>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <MentorAlertDigest data={data} />

      <InterventionDrawer
        open={drawerOpen}
        studentId={data.student_id}
        studentName={data.name}
        rollNo={data.roll_no}
        activeWeek={data.active_week ?? 9}
        onClose={() => setDrawerOpen(false)}
        onSuccess={(wk) => setToastMsg(`Intervention saved for ${data.name} (Week ${wk}).`)}
      />
    </div>
  );
}

function StatBox({ label, value, note }: { label: string; value: string; note: string }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
      <p className="text-xs text-slate-400">{label}</p>
      <p className="mt-1 text-xl font-bold text-slate-100">{value}</p>
      <p className="mt-1 text-[11px] text-slate-400">{note}</p>
    </div>
  );
}
