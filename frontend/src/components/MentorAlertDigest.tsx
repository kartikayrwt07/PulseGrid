import { useState } from "react";
import { Check, Copy } from "lucide-react";
import type { StudentAnalytics } from "../api/client";
import { ARCHETYPE_LABELS } from "../lib/utils";

export function buildMentorAlertText(data: StudentAnalytics): string {
  const urgentSubjects = data.ponr.filter(
    (p) =>
      p.eligibility_status === "WINDOW_CLOSING" ||
      p.eligibility_status === "UNRECOVERABLE_WITHOUT_WAIVER",
  );
  const topDrivers = data.shap_values
    .slice(0, 3)
    .map((s) => `${s.label} (${s.shap_value >= 0 ? "+" : ""}${s.shap_value.toFixed(2)})`)
    .join(", ");
  const steps = data.recovery_plan.recovery_steps
    .map((st, idx) => `  ${idx + 1}. ${st.action}`)
    .join("\n");

  const lines = [
    `[PULSEGRID MENTOR ALERT] ${data.name} (${data.roll_no})`,
    `Risk Tier: ${data.risk_tier} (${data.risk_score.toFixed(1)}/100) | Projected Score: ${data.projected_final_score.toFixed(1)}% -> Target: ${data.recovery_plan.projected_score_after.toFixed(1)}%`,
    `Primary Archetype: ${ARCHETYPE_LABELS[data.archetype] ?? data.archetype}`,
    `CUSUM Shift: ${data.cusum_triggered ? `Detected at Week ${data.cusum_week}` : "None"} | Assign-IA Divergence: ${data.divergence_index.toFixed(2)} sigma`,
    urgentSubjects.length > 0
      ? `Urgent PONR: ${urgentSubjects.map((s) => `${s.subject_code} (${s.current_pct.toFixed(1)}%, need ${s.min_future_needed}/${s.remaining_sessions}, budget=${s.bunk_budget})`).join("; ")}`
      : `Tightest PONR Window: ${data.ponr_days_left} days left`,
    `Top Risk Drivers (SHAP): ${topDrivers || "Balanced"}`,
    `Recommended Action Plan:`,
    steps || "  - Continue routine progress monitoring.",
  ];
  return lines.join("\n");
}

export function MentorAlertDigest({ data }: { data: StudentAnalytics }) {
  const [copied, setCopied] = useState(false);
  const digestText = buildMentorAlertText(data);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(digestText);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 print-sheet">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-sm font-semibold text-slate-200">Mentor Alert Digest</h2>
          <p className="text-[11px] text-slate-400">
            Ready-to-paste summary for advisor Slack, email, or LMS notes.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void handleCopy()}
          className="no-print inline-flex items-center gap-1.5 rounded-lg border border-emerald-500/40 bg-emerald-500/15 px-3 py-1.5 text-xs font-semibold text-emerald-300 transition hover:bg-emerald-500/25"
        >
          {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
          {copied ? "Copied!" : "Copy Mentor Alert"}
        </button>
      </div>
      <pre className="mt-3 overflow-x-auto whitespace-pre-wrap rounded-lg border border-slate-800 bg-slate-950/80 p-3 font-mono text-[11px] leading-relaxed text-slate-300">
        {digestText}
      </pre>
    </div>
  );
}
