import {
  ARCHETYPE_LABELS,
  ARCHETYPE_STYLES,
  PONR_STATUS_STYLES,
  TIER_STYLES,
  cn,
} from "../../lib/utils";

export function RiskTierBadge({ tier }: { tier: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold tracking-wide",
        TIER_STYLES[tier] ?? "bg-slate-800 text-slate-300 border-slate-700",
      )}
    >
      {tier.replace("_", " ")}
    </span>
  );
}

export function ArchetypeBadge({ archetype }: { archetype: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium",
        ARCHETYPE_STYLES[archetype] ?? "bg-slate-800 text-slate-300 border-slate-700",
      )}
    >
      {ARCHETYPE_LABELS[archetype] ?? archetype}
    </span>
  );
}

export function PONRBadge({ status }: { status: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border px-2 py-0.5 text-[11px] font-semibold",
        PONR_STATUS_STYLES[status] ?? "bg-slate-800 text-slate-300 border-slate-700",
      )}
    >
      {status.replace(/_/g, " ")}
    </span>
  );
}
