import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, RotateCcw, SlidersHorizontal } from "lucide-react";
import { WaterfallChart } from "../../components/charts/WaterfallChart";
import { RiskTierBadge } from "../../components/ui/Badge";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { DashboardSkeleton } from "../../components/ui/Skeleton";
import { Spinner } from "../../components/ui/Spinner";
import { useSimulate } from "../../hooks/useSimulate";
import { useStudentAnalytics } from "../../hooks/useStudentAnalytics";
import { useAuth } from "../../lib/auth";
import { formatPct } from "../../lib/utils";

export function RecoveryPage() {
  const { studentId } = useAuth();
  const effectiveId = studentId ?? 1;
  const analytics = useStudentAnalytics(effectiveId);

  const baselineMins = useMemo(() => {
    const f = analytics.data?.baseline_features ?? {};
    return {
      att: Math.min(100, Math.max(0, Math.round(f.att_mean ?? 75))),
      assign: Math.min(100, Math.max(0, Math.round(f.assign_mean ?? 75))),
      internal: Math.min(100, Math.max(0, Math.round(f.internal_mean ?? 75))),
    };
  }, [analytics.data?.student_id]);

  const [attSlider, setAttSlider] = useState(85);
  const [assignSlider, setAssignSlider] = useState(85);
  const [internalSlider, setInternalSlider] = useState(75);
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    setAttSlider(baselineMins.att);
    setAssignSlider(baselineMins.assign);
    setInternalSlider(baselineMins.internal);
    setDirty(false);
  }, [effectiveId, baselineMins]);

  const weeksRemaining = Math.max(
    1,
    (analytics.data?.total_weeks ?? 14) - (analytics.data?.active_week ?? 9),
  );

  const simRequest = useMemo(() => {
    if (!analytics.data || !dirty) return null;
    return {
      student_id: effectiveId,
      attendance_pct: attSlider,
      assignment_score: assignSlider,
      internal_score: internalSlider,
      weeks_remaining: weeksRemaining,
    };
  }, [analytics.data, dirty, effectiveId, attSlider, assignSlider, internalSlider, weeksRemaining]);

  const sim = useSimulate(simRequest, 150);

  if (analytics.isLoading) return <DashboardSkeleton />;
  if (analytics.isError) {
    return (
      <ErrorBanner
        title="Unable to load recovery planner"
        message={analytics.error instanceof Error ? analytics.error.message : "Request failed"}
        onRetry={() => void analytics.refetch()}
      />
    );
  }

  const data = analytics.data;
  if (!data) {
    return (
      <EmptyState
        title="No recovery data available"
        description="Switch to a valid student persona to simulate counterfactual recovery trajectories."
      />
    );
  }

  const activeTier = sim.data?.simulated_tier ?? data.risk_tier;
  const activeScore = sim.data?.simulated_projected_score ?? data.projected_final_score;
  const activeShap = sim.data?.shap_values ?? data.shap_values;
  const activeGroupedShap = sim.data?.grouped_shap ?? data.grouped_shap;
  const scoreDelta = sim.data?.score_delta ?? 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-slate-100">
            Recovery Planner &amp; What-If Simulator
          </h1>
          <p className="mt-0.5 text-xs text-slate-400">
            {data.name} ({data.roll_no}) · Minimum-effort feasible recovery solver + live SHAP feedback
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {sim.data?.historical_cusum_triggered ? (
            <span
              className={`rounded-full border px-2.5 py-0.5 text-[11px] font-medium ${
                sim.data.projected_cusum_active
                  ? "border-rose-500/40 bg-rose-500/15 text-rose-300"
                  : "border-emerald-500/40 bg-emerald-500/15 text-emerald-300"
              }`}
            >
              {sim.data.projected_cusum_active
                ? `CUSUM Shift (Wk ${data.cusum_week ?? "?"} -> Active)`
                : `CUSUM Wk ${data.cusum_week ?? "?"} -> Stabilizing`}
            </span>
          ) : null}
          <RiskTierBadge tier={activeTier} />
          <span className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-1 font-mono text-sm font-bold text-emerald-300">
            {formatPct(activeScore)}
            {dirty && scoreDelta !== 0 ? (
              <span className="ml-1.5 text-xs text-sky-300">
                ({scoreDelta >= 0 ? "+" : ""}
                {scoreDelta.toFixed(1)})
              </span>
            ) : null}
          </span>
        </div>
      </div>

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <SlidersHorizontal className="h-4 w-4 text-sky-400" />
              <h2 className="text-sm font-semibold text-slate-200">
                What-If Remaining {weeksRemaining}-Week Targets
              </h2>
            </div>
            <button
              type="button"
              onClick={() => {
                setAttSlider(baselineMins.att);
                setAssignSlider(baselineMins.assign);
                setInternalSlider(baselineMins.internal);
                setDirty(false);
              }}
              className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-slate-200"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              Reset
            </button>
          </div>

          <p className="mt-1 text-[11px] text-slate-400">
            Sliders are clamped between your current baseline and 100% (requests debounce automatically).
          </p>

          <div className="mt-4 space-y-4">
            <SliderControl
              label="Future Weekly Attendance %"
              value={attSlider}
              min={baselineMins.att}
              onChange={(v) => {
                setAttSlider(v);
                setDirty(true);
              }}
            />
            <SliderControl
              label="Future Assignment Score %"
              value={assignSlider}
              min={baselineMins.assign}
              onChange={(v) => {
                setAssignSlider(v);
                setDirty(true);
              }}
            />
            <SliderControl
              label="Future Closed-Book Internal Score %"
              value={internalSlider}
              min={baselineMins.internal}
              onChange={(v) => {
                setInternalSlider(v);
                setDirty(true);
              }}
            />
          </div>

          <div className="mt-4 min-h-[24px]">
            {sim.isLoading ? <Spinner label="Recomputing risk & SHAP attributions..." /> : null}
            {sim.error ? <ErrorBanner message={sim.error} /> : null}
          </div>

          <div className="mt-4 border-t border-slate-800 pt-4">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Recommended Solver Checklist
            </h3>
            <p className="mt-1 text-xs text-slate-300">{data.recovery_plan.summary}</p>
            <ul className="mt-3 space-y-2">
              {data.recovery_plan.recovery_steps.map((step, idx) => (
                <li
                  key={`${step.feature}-${idx}`}
                  className="flex items-start justify-between gap-2 rounded-lg border border-slate-800 bg-slate-950/60 p-2.5 text-xs"
                >
                  <div>
                    <p className="inline-flex items-center gap-1.5 font-semibold text-emerald-300">
                      <CheckCircle2 className="h-3.5 w-3.5" />
                      {step.label}
                    </p>
                    <p className="mt-0.5 text-[11px] text-slate-400">{step.action}</p>
                  </div>
                  <span className="shrink-0 font-mono text-slate-200">
                    {formatPct(step.current_pct, 0)} → {formatPct(step.target_pct, 0)}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <h2 className="text-sm font-semibold text-slate-200">
            {dirty ? "Simulated SHAP Feature Impact" : "Baseline SHAP Feature Impact"}
          </h2>
          <p className="mb-3 text-[11px] text-slate-400">
            Updates live as you test attendance and internal study targets.
          </p>
          <WaterfallChart entries={activeShap} groupedEntries={activeGroupedShap} />
        </div>
      </section>
    </div>
  );
}

function SliderControl({
  label,
  value,
  min,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  onChange: (val: number) => void;
}) {
  return (
    <label className="block">
      <div className="flex items-center justify-between text-xs">
        <span className="font-medium text-slate-300">{label}</span>
        <span className="font-mono font-semibold text-sky-300">
          {value}% <span className="text-[11px] text-slate-500">(min {min}%)</span>
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={100}
        step={1}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="mt-1.5 h-2 w-full cursor-pointer accent-emerald-400"
      />
    </label>
  );
}
