import { AlertTriangle, ArrowRight, CheckCircle2 } from "lucide-react";
import type { UploadResult } from "../../api/client";

interface UploadPreviewPanelProps {
  result: UploadResult;
  committing: boolean;
  canCommit: boolean;
  onCommit: () => void;
  onNavigateDashboard?: () => void;
}

export function UploadPreviewPanel({
  result,
  committing,
  canCommit,
  onCommit,
  onNavigateDashboard,
}: UploadPreviewPanelProps) {
  return (
    <div className="space-y-5">
      {result.committed ? (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-emerald-500/40 bg-emerald-950/35 p-4 text-xs text-emerald-200">
          <div>
            <p className="inline-flex items-center gap-1.5 text-sm font-semibold text-emerald-300">
              <CheckCircle2 className="h-4 w-4" /> Commit Succeeded &amp; Snapshots Updated
            </p>
            <p className="mt-1 text-slate-300">
              Upserted {result.students_upserted} student(s), {result.records_upserted} record(s),
              recomputed {result.snapshots_recomputed} snapshot(s).
            </p>
          </div>
          {onNavigateDashboard ? (
            <button
              type="button"
              onClick={onNavigateDashboard}
              className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-500 px-3.5 py-2 font-semibold text-slate-950 hover:bg-emerald-400"
            >
              View Updated Dashboard <ArrowRight className="h-4 w-4" />
            </button>
          ) : null}
        </div>
      ) : (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-sky-500/30 bg-sky-950/20 p-3.5 text-xs">
          <span className="text-slate-300">
            Preview ready ({result.valid_row_count} valid rows). Review mappings below, then commit
            to update live predictions.
          </span>
          <button
            type="button"
            disabled={committing || !canCommit}
            onClick={onCommit}
            className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-500 px-4 py-2 font-semibold text-slate-950 hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <CheckCircle2 className="h-4 w-4" />
            {committing ? "Committing..." : "Commit & Recompute Snapshots"}
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <InfoBox label="Filename" value={result.filename} />
        <InfoBox label="Total Rows Parsed" value={String(result.row_count)} />
        <InfoBox
          label="Mapped Headers"
          value={`${result.column_mappings.filter((c) => c.canonical_column).length} / ${result.column_mappings.length}`}
        />
      </div>

      {(result.warnings ?? []).length > 0 ? (
        <div className="rounded-xl border border-amber-500/40 bg-amber-950/25 p-4 text-xs text-amber-200">
          <p className="inline-flex items-center gap-1.5 font-semibold text-amber-300">
            <AlertTriangle className="h-4 w-4" />
            Data Health Warnings
          </p>
          <ul className="mt-1.5 list-disc pl-5">
            {(result.warnings ?? []).map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        </div>
      ) : null}

      <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
        <h2 className="mb-3 text-sm font-semibold text-slate-200">
          Canonical Column Mapping Preview
        </h2>
        <table className="w-full text-left text-xs">
          <thead className="border-b border-slate-800 text-[11px] uppercase text-slate-400">
            <tr>
              <th className="py-2 pr-3">Uploaded Header</th>
              <th className="py-2 pr-3">Matched Canonical Field</th>
              <th className="py-2 pr-3">Confidence</th>
              <th className="py-2">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/70">
            {result.column_mappings.map((m) => (
              <tr key={m.source_column}>
                <td className="py-2 pr-3 font-medium text-slate-200">{m.source_column}</td>
                <td className="py-2 pr-3 font-mono text-sky-300">{m.canonical_column ?? "—"}</td>
                <td className="py-2 pr-3 font-mono">{Math.round(m.confidence * 100)}%</td>
                <td className="py-2">
                  {m.canonical_column ? (
                    <span className="text-emerald-300">Mapped</span>
                  ) : (
                    <span className="text-slate-500">Unmapped</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {result.preview_rows.length > 0 ? (
        <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <h2 className="mb-3 text-sm font-semibold text-slate-200">
            Normalized Data Preview (First {result.preview_rows.length} Rows)
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-slate-800 text-[11px] text-slate-400">
                <tr>
                  {Object.keys(result.preview_rows[0]).map((col) => (
                    <th key={col} className="py-2 pr-3 font-mono">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/70">
                {result.preview_rows.map((row, idx) => (
                  <tr key={idx}>
                    {Object.keys(result.preview_rows[0]).map((col) => (
                      <td key={col} className="py-1.5 pr-3 text-slate-300">
                        {String(row[col] ?? "—")}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}
    </div>
  );
}

function InfoBox({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-3.5">
      <p className="text-[11px] text-slate-400">{label}</p>
      <p className="mt-1 truncate text-sm font-bold text-slate-100">{value}</p>
    </div>
  );
}
