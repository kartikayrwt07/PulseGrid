import { GraduationCap, ShieldCheck } from "lucide-react";
import { useAuth } from "../../lib/auth";
import { HERO_PERSONAS, cn } from "../../lib/utils";

export function RoleSwitcher({ onRoleChanged }: { onRoleChanged?: (role: "faculty" | "student") => void }) {
  const { role, studentId, switching, switchRole } = useAuth();

  const handleFaculty = async () => {
    await switchRole("faculty");
    onRoleChanged?.("faculty");
  };

  const handleStudent = async (id: number) => {
    await switchRole("student", id);
    onRoleChanged?.("student");
  };

  return (
    <div className="flex flex-wrap items-center gap-2">
      <div className="inline-flex rounded-lg border border-slate-700 bg-slate-900 p-0.5">
        <button
          type="button"
          data-testid="role-faculty"
          disabled={switching}
          onClick={() => void handleFaculty()}
          className={cn(
            "inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition disabled:opacity-50",
            role === "faculty"
              ? "bg-emerald-500/20 text-emerald-300 shadow-sm"
              : "text-slate-400 hover:text-slate-200",
          )}
        >
          <ShieldCheck className="h-3.5 w-3.5" />
          Faculty
        </button>
        <button
          type="button"
          data-testid="role-student"
          disabled={switching}
          onClick={() => void handleStudent(studentId ?? 1)}
          className={cn(
            "inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition disabled:opacity-50",
            role === "student"
              ? "bg-sky-500/20 text-sky-300 shadow-sm"
              : "text-slate-400 hover:text-slate-200",
          )}
        >
          <GraduationCap className="h-3.5 w-3.5" />
          Student
        </button>
      </div>

      {role === "student" ? (
        <select
          aria-label="Select Student Persona"
          disabled={switching}
          value={studentId ?? 1}
          onChange={(e) => void handleStudent(Number(e.target.value))}
          className="rounded-lg border border-slate-700 bg-slate-900 px-2.5 py-1.5 text-xs text-slate-200 focus:border-sky-500 focus:outline-none disabled:opacity-50"
        >
          {HERO_PERSONAS.map((p) => (
            <option key={p.id} value={p.id}>
              {p.rollNo} — {p.name} ({p.tag})
            </option>
          ))}
        </select>
      ) : null}
    </div>
  );
}
