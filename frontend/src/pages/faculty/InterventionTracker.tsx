import { useState, type FormEvent } from "react";
import { ArrowUpRight, ClipboardPlus, TrendingUp } from "lucide-react";
import { RiskTierBadge } from "../../components/ui/Badge";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { DashboardSkeleton } from "../../components/ui/Skeleton";
import { useCreateIntervention, useInterventions } from "../../hooks/useInterventions";
import { useStudents } from "../../hooks/useStudents";

interface InterventionTrackerProps {
  onSelectStudent: (id: number) => void;
}

export function InterventionTracker({ onSelectStudent }: InterventionTrackerProps) {
  const listQuery = useInterventions();
  const studentsQuery = useStudents({ limit: 240, sort_by: "name" });
  const createMut = useCreateIntervention();

  const [studentId, setStudentId] = useState(1);
  const [week, setWeek] = useState(9);
  const [ivType, setIvType] = useState("Remedial Mentoring");
  const [notes, setNotes] = useState("");
  const [outcome, setOutcome] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (createMut.isPending || notes.trim().length < 3) return;
    createMut.mutate(
      {
        student_id: studentId,
        week,
        intervention_type: ivType,
        notes: notes.trim(),
        outcome: outcome.trim() || null,
      },
      {
        onSuccess: () => {
          setNotes("");
          setOutcome("");
        },
      },
    );
  };

  if (listQuery.isLoading) return <DashboardSkeleton />;
  if (listQuery.isError) {
    return (
      <ErrorBanner
        title="Could not load intervention log"
        message={listQuery.error instanceof Error ? listQuery.error.message : "Request failed"}
        onRetry={() => void listQuery.refetch()}
      />
    );
  }

  const items = listQuery.data?.items ?? [];
  const improvedCount = items.filter((i) => i.risk_improved).length;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-100">
            Intervention Log &amp; Before/After Lift Tracker
          </h1>
          <p className="mt-0.5 text-xs text-slate-400">
            Captures baseline risk tier on creation and measures post-mentoring trajectory lift.
          </p>
        </div>
        <div className="inline-flex items-center gap-2 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 text-xs font-semibold text-emerald-300">
          <TrendingUp className="h-4 w-4" />
          {improvedCount} of {items.length} interventions improved tier
        </div>
      </div>

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <form
          onSubmit={handleSubmit}
          className="space-y-3 rounded-xl border border-slate-800 bg-slate-900/60 p-4"
        >
          <div className="flex items-center gap-2">
            <ClipboardPlus className="h-4 w-4 text-emerald-400" />
            <h2 className="text-sm font-semibold text-slate-200">Log Faculty Intervention</h2>
          </div>

          <label className="block text-xs">
            <span className="text-slate-400">Student</span>
            <select
              value={studentId}
              onChange={(e) => setStudentId(Number(e.target.value))}
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-2.5 py-1.5 text-xs text-slate-100"
            >
              {(studentsQuery.data?.items ?? []).map((s) => (
                <option key={s.id} value={s.id}>
                  {s.roll_no} — {s.name} ({s.risk_tier})
                </option>
              ))}
            </select>
          </label>

          <div className="grid grid-cols-2 gap-2">
            <label className="block text-xs">
              <span className="text-slate-400">Week</span>
              <input
                type="number"
                min={1}
                max={20}
                value={week}
                onChange={(e) => setWeek(Number(e.target.value))}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-2.5 py-1.5 text-xs text-slate-100"
              />
            </label>
            <label className="block text-xs">
              <span className="text-slate-400">Type</span>
              <select
                value={ivType}
                onChange={(e) => setIvType(e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-2.5 py-1.5 text-xs text-slate-100"
              >
                <option>Remedial Mentoring</option>
                <option>Attendance Contract</option>
                <option>Peer Tutoring</option>
                <option>Parent / Advisor Escalation</option>
              </select>
            </label>
          </div>

          <label className="block text-xs">
            <span className="text-slate-400">Action Notes</span>
            <textarea
              required
              minLength={3}
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Document support plan, target sessions, or drills..."
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 p-2 text-xs text-slate-100"
            />
          </label>

          <label className="block text-xs">
            <span className="text-slate-400">Initial Outcome / Follow-up</span>
            <input
              type="text"
              value={outcome}
              onChange={(e) => setOutcome(e.target.value)}
              placeholder="Optional expected milestone..."
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-2.5 py-1.5 text-xs text-slate-100"
            />
          </label>

          {createMut.isError ? (
            <ErrorBanner
              message={
                createMut.error instanceof Error
                  ? createMut.error.message
                  : "Failed to save intervention."
              }
            />
          ) : null}

          <button
            type="submit"
            disabled={createMut.isPending || notes.trim().length < 3}
            className="w-full rounded-lg bg-emerald-500 py-2 text-xs font-semibold text-slate-950 transition hover:bg-emerald-400 disabled:opacity-50"
          >
            {createMut.isPending ? "Saving..." : "Record Intervention"}
          </button>
        </form>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 lg:col-span-2">
          <h2 className="mb-3 text-sm font-semibold text-slate-200">
            Recorded Interventions ({items.length})
          </h2>
          {!items.length ? (
            <EmptyState
              title="No interventions recorded"
              description="Use the form on the left to log mentoring actions and track tier improvement."
            />
          ) : (
            <div className="space-y-3">
              {items.map((iv) => (
                <div
                  key={iv.id}
                  className="rounded-lg border border-slate-800 bg-slate-950/70 p-3 text-xs"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <button
                      type="button"
                      onClick={() => onSelectStudent(iv.student_id)}
                      className="inline-flex items-center gap-1 font-semibold text-slate-100 hover:text-emerald-300"
                    >
                      {iv.student_roll_no} · {iv.student_name}
                      <ArrowUpRight className="h-3.5 w-3.5" />
                    </button>
                    <div className="flex items-center gap-2">
                      <span className="text-[11px] text-slate-400">Wk {iv.week}</span>
                      {iv.pre_risk_tier ? <RiskTierBadge tier={iv.pre_risk_tier} /> : null}
                      <span className="text-slate-500">→</span>
                      <RiskTierBadge tier={iv.current_risk_tier} />
                      {iv.risk_improved ? (
                        <span className="rounded-full border border-emerald-500/40 bg-emerald-500/20 px-2 py-0.5 text-[10px] font-bold text-emerald-300">
                          LIFT IMPROVED
                        </span>
                      ) : null}
                    </div>
                  </div>
                  <p className="mt-1.5 font-medium text-sky-300">{iv.intervention_type}</p>
                  <p className="mt-0.5 text-slate-300">{iv.notes}</p>
                  {iv.outcome ? <p className="mt-1 text-[11px] text-emerald-300/90">{iv.outcome}</p> : null}
                </div>
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
