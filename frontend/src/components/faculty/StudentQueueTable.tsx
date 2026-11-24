import { ArrowRight } from "lucide-react";
import type { Schemas } from "../../api/client";
import { ARCHETYPE_LABELS, formatPct } from "../../lib/utils";
import { ArchetypeBadge, RiskTierBadge } from "../ui/Badge";

interface StudentQueueTableProps {
  items: Schemas["StudentSummary"][];
  onSelectStudent: (id: number) => void;
}

export function StudentQueueTable({ items, onSelectStudent }: StudentQueueTableProps) {
  return (
    <div className="mt-3 overflow-x-auto">
      <table className="w-full text-left text-xs">
        <thead className="border-b border-slate-800 text-[11px] uppercase tracking-wider text-slate-400">
          <tr>
            <th className="py-2.5 pr-3">Student</th>
            <th className="py-2.5 pr-3">Risk Tier</th>
            <th className="py-2.5 pr-3">Archetype</th>
            <th className="py-2.5 pr-3">CUSUM</th>
            <th className="py-2.5 pr-3">PONR Window</th>
            <th className="py-2.5 pr-3">Projected → Rescue</th>
            <th className="py-2.5 text-right">Action</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/70">
          {items.map((stu) => (
            <tr
              key={stu.id}
              onClick={() => onSelectStudent(stu.id)}
              className="cursor-pointer transition hover:bg-slate-800/40"
            >
              <td className="py-2.5 pr-3">
                <div className="font-semibold text-slate-100">{stu.name}</div>
                <div className="text-[11px] text-slate-400">
                  {stu.roll_no}
                  {stu.is_hero_persona ? " · Hero Case" : ""}
                </div>
              </td>
              <td className="py-2.5 pr-3">
                <RiskTierBadge tier={stu.risk_tier} />
              </td>
              <td className="py-2.5 pr-3">
                <div className="flex flex-wrap items-center gap-1">
                  <ArchetypeBadge archetype={stu.primary_archetype ?? stu.archetype} />
                  {stu.secondary_flags && stu.secondary_flags.length > 0 ? (
                    <span
                      title={stu.secondary_flags.map((f) => ARCHETYPE_LABELS[f] ?? f).join(", ")}
                      className="inline-flex items-center rounded border border-slate-700 bg-slate-800/80 px-1.5 py-0.5 text-[10px] font-medium text-slate-300"
                    >
                      +{stu.secondary_flags.length}
                    </span>
                  ) : null}
                </div>
              </td>
              <td className="py-2.5 pr-3">
                {stu.cusum_triggered ? (
                  <span className="font-medium text-rose-300">
                    Wk {stu.cusum_week ?? "?"}
                  </span>
                ) : (
                  <span className="text-slate-500">—</span>
                )}
              </td>
              <td className="py-2.5 pr-3">
                <span
                  className={
                    stu.ponr_days_left <= 4 ? "font-semibold text-rose-300" : "text-slate-300"
                  }
                >
                  {stu.ponr_days_left <= 0 ? "Urgent (≤0d)" : `${stu.ponr_days_left}d left`}
                </span>
              </td>
              <td className="py-2.5 pr-3 font-mono text-slate-200">
                {formatPct(stu.projected_final_score)} →{" "}
                <span className="text-emerald-300">{formatPct(stu.projected_score_after)}</span>
              </td>
              <td className="py-2.5 text-right">
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    onSelectStudent(stu.id);
                  }}
                  className="inline-flex items-center gap-1 rounded-md border border-slate-700 bg-slate-800 px-2.5 py-1 text-[11px] font-medium text-slate-200 hover:border-emerald-500/50 hover:text-emerald-300"
                >
                  Inspect <ArrowRight className="h-3 w-3" />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
