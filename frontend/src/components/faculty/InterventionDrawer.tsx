import { useEffect, useState, type FormEvent } from "react";
import { ClipboardPlus, X } from "lucide-react";
import { useCreateIntervention } from "../../hooks/useInterventions";
import { ErrorBanner } from "../ui/ErrorBanner";

interface InterventionDrawerProps {
  open: boolean;
  studentId: number;
  studentName: string;
  rollNo: string;
  activeWeek: number;
  onClose: () => void;
  onSuccess: (loggedWeek: number) => void;
}

export function InterventionDrawer({
  open,
  studentId,
  studentName,
  rollNo,
  activeWeek,
  onClose,
  onSuccess,
}: InterventionDrawerProps) {
  const createMut = useCreateIntervention();
  const [week, setWeek] = useState(activeWeek);
  const [ivType, setIvType] = useState("Remedial Mentoring");
  const [notes, setNotes] = useState("");
  const [outcome, setOutcome] = useState("");

  useEffect(() => {
    if (open) {
      setWeek(activeWeek);
    }
  }, [open, activeWeek, studentId]);

  if (!open) return null;

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
          onSuccess(week);
          onClose();
        },
      },
    );
  };

  return (
    <div
      className="fixed inset-0 z-50 flex justify-end bg-slate-950/70 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-label="Log Faculty Intervention Drawer"
    >
      <div className="flex h-full w-full max-w-md flex-col border-l border-slate-800 bg-slate-900 p-5 shadow-2xl">
        <div className="flex items-start justify-between border-b border-slate-800 pb-4">
          <div>
            <p className="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-100">
              <ClipboardPlus className="h-4 w-4 text-emerald-400" />
              Log Faculty Intervention
            </p>
            <p className="mt-0.5 text-xs text-slate-400">
              {studentName} ({rollNo}) · Active Week {activeWeek}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close intervention drawer"
            className="rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-slate-100"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-4 flex flex-1 flex-col space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <label className="block text-xs">
              <span className="text-slate-400">Intervention Week</span>
              <input
                type="number"
                min={1}
                max={20}
                value={week}
                onChange={(e) => setWeek(Number(e.target.value))}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-2.5 py-2 text-xs text-slate-100"
              />
            </label>
            <label className="block text-xs">
              <span className="text-slate-400">Type</span>
              <select
                value={ivType}
                onChange={(e) => setIvType(e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-2.5 py-2 text-xs text-slate-100"
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
              rows={4}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Document assigned recovery plan, lab catch-up, or concept drills..."
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 p-2.5 text-xs text-slate-100"
            />
          </label>

          <label className="block text-xs">
            <span className="text-slate-400">Expected / Initial Outcome</span>
            <input
              type="text"
              value={outcome}
              onChange={(e) => setOutcome(e.target.value)}
              placeholder="e.g. Scheduled weekly check-in"
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-2.5 py-2 text-xs text-slate-100"
            />
          </label>

          {createMut.isError ? (
            <ErrorBanner
              message={
                createMut.error instanceof Error
                  ? createMut.error.message
                  : "Failed to log intervention."
              }
            />
          ) : null}

          <div className="mt-auto flex items-center justify-end gap-2 border-t border-slate-800 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-slate-700 px-3.5 py-2 text-xs font-medium text-slate-300 hover:bg-slate-800"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createMut.isPending || notes.trim().length < 3}
              className="rounded-lg bg-emerald-500 px-4 py-2 text-xs font-semibold text-slate-950 hover:bg-emerald-400 disabled:opacity-50"
            >
              {createMut.isPending ? "Saving..." : "Save Intervention"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
