export function cn(...classes: Array<string | false | null | undefined>): string {
  return classes.filter(Boolean).join(" ");
}

export function formatPct(value: number | null | undefined, digits = 1): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return `${value.toFixed(digits)}%`;
}

export function formatPonrMargin(bunkBudgetSessions: number, sessionsPerWeek: number): string {
  if (bunkBudgetSessions < 0) return "Waiver Required";
  if (bunkBudgetSessions === 0) return "0 missable sessions — attend all";
  const approxDays = Math.round((bunkBudgetSessions * 7) / Math.max(1, sessionsPerWeek));
  const unit = bunkBudgetSessions === 1 ? "session" : "sessions";
  return `${bunkBudgetSessions} missable ${unit} (~${approxDays}d margin)`;
}

export const TIER_STYLES: Record<string, string> = {
  CRITICAL: "bg-rose-500/15 text-rose-300 border-rose-500/40",
  AT_RISK: "bg-amber-500/15 text-amber-300 border-amber-500/40",
  WATCH: "bg-sky-500/15 text-sky-300 border-sky-500/40",
  SAFE: "bg-emerald-500/15 text-emerald-300 border-emerald-500/40",
};

export const ARCHETYPE_LABELS: Record<string, string> = {
  DETENTION_CLIFF: "Detention Cliff",
  PASSIVE_COPIER_CONCEPT_GAP: "Passive Copier Gap",
  SILENT_SLIPPER: "Silent Slipper",
  BROAD_DISENGAGEMENT: "Broad Disengagement",
  CONCEPTUAL_STRUGGLER: "Conceptual Struggler",
  ON_TRACK: "On Track",
};

export const ARCHETYPE_STYLES: Record<string, string> = {
  DETENTION_CLIFF: "bg-rose-500/15 text-rose-300 border-rose-500/30",
  PASSIVE_COPIER_CONCEPT_GAP: "bg-fuchsia-500/15 text-fuchsia-300 border-fuchsia-500/30",
  SILENT_SLIPPER: "bg-orange-500/15 text-orange-300 border-orange-500/30",
  BROAD_DISENGAGEMENT: "bg-red-500/15 text-red-300 border-red-500/30",
  CONCEPTUAL_STRUGGLER: "bg-yellow-500/15 text-yellow-300 border-yellow-500/30",
  ON_TRACK: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
};

export const PONR_STATUS_STYLES: Record<string, string> = {
  UNRECOVERABLE_WITHOUT_WAIVER: "bg-rose-500/20 text-rose-200 border-rose-500/50",
  WINDOW_CLOSING: "bg-amber-500/20 text-amber-200 border-amber-500/50",
  WATCH: "bg-sky-500/15 text-sky-300 border-sky-500/40",
  SAFE: "bg-emerald-500/15 text-emerald-300 border-emerald-500/40",
};

export const HERO_PERSONAS = [
  { id: 1, rollNo: "STU-001", name: "Aarav Kulkarni", tag: "Silent Slipper (CUSUM Wk 7)" },
  { id: 2, rollNo: "STU-002", name: "Meera Nair", tag: "Passive Copier Gap" },
  { id: 3, rollNo: "STU-003", name: "Rohan Deshmukh", tag: "Detention Cliff (CN Lab)" },
  { id: 4, rollNo: "STU-004", name: "Priya Sharma", tag: "Recovered After Intervention" },
] as const;
