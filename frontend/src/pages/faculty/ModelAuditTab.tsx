import {
  Bar,
  BarChart,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { DashboardSkeleton } from "../../components/ui/Skeleton";
import { useModelAudit } from "../../hooks/useModelAudit";

export function ModelAuditTab() {
  const auditQuery = useModelAudit();
  if (auditQuery.isLoading) return <DashboardSkeleton />;
  if (auditQuery.isError) {
    return (
      <ErrorBanner
        title="Could not load model audit metrics"
        message={auditQuery.error instanceof Error ? auditQuery.error.message : "Request failed"}
        onRetry={() => void auditQuery.refetch()}
      />
    );
  }
  const audit = auditQuery.data;
  if (!audit) {
    return (
      <EmptyState
        title="Model audit unavailable"
        description="Run backend/ml/train_and_evaluate.py to generate holdout evaluation metrics."
      />
    );
  }

  const topFeatures = audit.feature_importances.slice(0, 10);
  const cmMax = Math.max(1, ...audit.confusion_matrix.flat());
  const calibData = (audit.calibration_curve ?? []).map((b) => ({
    predPct: Math.round(b.bin_mean_pred * 1000) / 10,
    obsPct: Math.round(b.bin_true_freq * 1000) / 10,
    count: b.bin_count,
  }));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold tracking-tight text-slate-100">
          Leakage-Free Model Evaluation &amp; Audit
        </h1>
        <p className="mt-0.5 text-xs text-slate-400">
          5-Fold Stratified CV + holdout evaluation (Features: Weeks {audit.feature_window_weeks} →{" "}
          Targets: Weeks {audit.target_window_weeks} · n={audit.holdout_size} unseen holdout)
        </p>
      </div>

      <section className="grid grid-cols-2 gap-3 lg:grid-cols-6">
        <MetricCard label="Selected Model" value={audit.selected_model} />
        <MetricCard
          label="Holdout At-Risk Recall"
          value={`${(audit.at_risk_recall * 100).toFixed(1)}%`}
          accent="text-emerald-300"
        />
        <MetricCard label="Macro F1" value={audit.macro_f1.toFixed(3)} />
        <MetricCard label="ROC AUC (OvR)" value={audit.roc_auc.toFixed(3)} accent="text-sky-300" />
        <MetricCard label="Regressor MAE" value={`${audit.mae.toFixed(2)} pts`} />
        <MetricCard
          label="Brier Score"
          value={(audit.brier_score ?? 0).toFixed(4)}
          accent="text-emerald-300"
        />
      </section>

      <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/60 p-4">
        <h2 className="mb-3 text-sm font-semibold text-slate-200">
          3-Classifier 5-Fold CV &amp; Holdout Comparison
        </h2>
        <table className="w-full text-left text-xs">
          <thead className="border-b border-slate-800 text-[11px] uppercase text-slate-400">
            <tr>
              <th className="py-2 pr-3">Model</th>
              <th className="py-2 pr-3">5-Fold CV Recall</th>
              <th className="py-2 pr-3">5-Fold CV Macro F1</th>
              <th className="py-2 pr-3">5-Fold CV AUC</th>
              <th className="py-2 pr-3">Holdout Recall</th>
              <th className="py-2">Holdout AUC</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/70">
            {audit.model_comparison.map((row) => (
              <tr
                key={row.model_name}
                className={row.model_name === audit.selected_model ? "bg-emerald-950/20" : ""}
              >
                <td className="py-2 pr-3 font-medium text-slate-100">
                  {row.model_name}
                  {row.model_name === audit.selected_model ? (
                    <span className="ml-2 rounded bg-emerald-500/20 px-1.5 py-0.5 text-[10px] text-emerald-300">
                      ACTIVE
                    </span>
                  ) : null}
                </td>
                <td className="py-2 pr-3 font-mono text-emerald-300">
                  {((row.cv_at_risk_recall_mean ?? 0) * 100).toFixed(1)}% ±{" "}
                  {((row.cv_at_risk_recall_std ?? 0) * 100).toFixed(1)}%
                </td>
                <td className="py-2 pr-3 font-mono">
                  {(row.cv_macro_f1_mean ?? 0).toFixed(3)} ± {(row.cv_macro_f1_std ?? 0).toFixed(3)}
                </td>
                <td className="py-2 pr-3 font-mono text-sky-300">
                  {(row.cv_roc_auc_mean ?? 0).toFixed(3)}
                </td>
                <td className="py-2 pr-3 font-mono">{(row.at_risk_recall * 100).toFixed(1)}%</td>
                <td className="py-2 font-mono">{row.roc_auc.toFixed(3)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <div className="mb-2 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-slate-200">
                Probability Calibration Reliability Curve
              </h2>
              <p className="text-[11px] text-slate-400">
                Out-of-fold P(At-Risk or Critical) across 5 quantile bins vs ideal diagonal.
              </p>
            </div>
            <span className="rounded-md border border-emerald-500/40 bg-emerald-500/15 px-2 py-0.5 font-mono text-[11px] text-emerald-300">
              Brier {(audit.brier_score ?? 0).toFixed(4)}
            </span>
          </div>
          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={calibData} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis
                  type="number"
                  dataKey="predPct"
                  domain={[0, 100]}
                  stroke="#94a3b8"
                  fontSize={11}
                  tickFormatter={(v: number) => `${v}%`}
                />
                <YAxis
                  type="number"
                  domain={[0, 100]}
                  stroke="#94a3b8"
                  fontSize={11}
                  tickFormatter={(v: number) => `${v}%`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#0f172a",
                    borderColor: "#334155",
                    borderRadius: "0.5rem",
                    fontSize: "12px",
                  }}
                  formatter={(v, _, item) => [
                    `${Number(v).toFixed(1)}% (n=${item?.payload?.count ?? 0})`,
                    "Observed Rate",
                  ]}
                  labelFormatter={(l) => `Predicted Risk Prob: ${Number(l).toFixed(1)}%`}
                />
                <ReferenceLine
                  segment={[{ x: 0, y: 0 }, { x: 100, y: 100 }]}
                  stroke="#64748b"
                  strokeDasharray="4 4"
                />
                <Line
                  type="monotone"
                  dataKey="obsPct"
                  stroke="#38bdf8"
                  strokeWidth={2.5}
                  dot={{ r: 4, fill: "#38bdf8" }}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          <h3 className="mb-2 mt-4 text-xs font-semibold uppercase tracking-wider text-slate-400">
            Holdout Confusion Matrix (Rows = Actual, Cols = Predicted)
          </h3>
          <table className="w-full text-center text-xs">
            <thead>
              <tr className="text-[10px] text-slate-400">
                <th className="p-1 text-left">Actual \ Pred</th>
                {audit.class_labels.map((lbl) => (
                  <th key={lbl} className="p-1 font-mono">
                    {lbl}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {audit.confusion_matrix.map((row, rIdx) => (
                <tr key={audit.class_labels[rIdx] ?? rIdx}>
                  <td className="p-1 text-left font-mono text-[10px] text-slate-300">
                    {audit.class_labels[rIdx]}
                  </td>
                  {row.map((val, cIdx) => {
                    const alpha = Math.max(0.08, (val / cmMax) * 0.75);
                    return (
                      <td
                        key={cIdx}
                        style={{
                          backgroundColor:
                            rIdx === cIdx
                              ? `rgba(16, 185, 129, ${alpha})`
                              : `rgba(244, 63, 94, ${val > 0 ? alpha : 0.05})`,
                        }}
                        className="border border-slate-900 p-2 font-mono font-semibold text-slate-100"
                      >
                        {val}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <h2 className="mb-1 text-sm font-semibold text-slate-200">
            Top Global Feature Importances (Zero Leakage)
          </h2>
          <p className="mb-3 text-[11px] text-slate-400">
            Derived strictly from Weeks 1–8 observational indicators — no exam scores or demographics.
          </p>
          <div className="h-96 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={topFeatures}
                layout="vertical"
                margin={{ top: 4, right: 16, left: 16, bottom: 4 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
                <XAxis
                  type="number"
                  stroke="#94a3b8"
                  fontSize={11}
                  tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`}
                />
                <YAxis type="category" dataKey="label" width={165} stroke="#cbd5e1" fontSize={11} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#0f172a",
                    borderColor: "#334155",
                    borderRadius: "0.5rem",
                    fontSize: "12px",
                  }}
                  formatter={(v) => [`${(Number(v) * 100).toFixed(2)}%`, "Importance"]}
                />
                <Bar dataKey="importance" fill="#38bdf8" radius={[4, 4, 4, 4]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </section>
    </div>
  );
}

function MetricCard({
  label,
  value,
  accent = "text-slate-100",
}: {
  label: string;
  value: string;
  accent?: string;
}) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-3.5">
      <p className="text-[11px] text-slate-400">{label}</p>
      <p className={`mt-1 truncate text-base font-bold ${accent}`}>{value}</p>
    </div>
  );
}
