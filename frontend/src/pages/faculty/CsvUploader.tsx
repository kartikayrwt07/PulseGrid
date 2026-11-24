import { useState, type DragEvent } from "react";
import { useQueryClient } from "@tanstack/react-query";
import {
  ArrowRight,
  CheckCircle2,
  Download,
  FileSpreadsheet,
  RotateCcw,
  UploadCloud,
} from "lucide-react";
import { apiClient, type UploadResult } from "../../api/client";
import { UploadPreviewPanel } from "../../components/faculty/UploadPreviewPanel";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { Spinner } from "../../components/ui/Spinner";

const SAMPLE_UPLOAD_CSV = [
  "roll_no,student_name,subject_code,week,attended_sessions,total_sessions,assignment_score,internal_score",
  "STU-001,Aarav Kulkarni,MA101,9,2,3,62.0,57.0",
  "STU-002,Meera Nair,CS201,9,3,3,94.0,36.0",
  "STU-003,Rohan Deshmukh,CS301L,9,2,2,81.0,78.0",
  "STU-901,Kavya Verma,MA101,9,3,3,88.0,85.0",
  "STU-901,Kavya Verma,CS201,9,3,3,86.0,83.0",
].join("\n");

interface CsvUploaderProps {
  onNavigateDashboard?: () => void;
}

export function CsvUploader({ onNavigateDashboard }: CsvUploaderProps) {
  const queryClient = useQueryClient();
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [committing, setCommitting] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [confirmReset, setConfirmReset] = useState(false);
  const [resetMsg, setResetMsg] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<UploadResult | null>(null);

  const invalidateCohortQueries = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] }),
      queryClient.invalidateQueries({ queryKey: ["students"] }),
      queryClient.invalidateQueries({ queryKey: ["student-analytics"] }),
      queryClient.invalidateQueries({ queryKey: ["recovery-plan"] }),
      queryClient.invalidateQueries({ queryKey: ["interventions"] }),
      queryClient.invalidateQueries({ queryKey: ["health"] }),
    ]);
  };

  const handleFile = async (file: File | undefined) => {
    if (!file || uploading || committing) return;
    setUploading(true);
    setError(null);
    setResetMsg(null);
    setSelectedFile(file);
    try {
      setResult(await apiClient.uploadAcademicFile(file, false));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setUploading(false);
    }
  };

  const handleCommit = async () => {
    if (!selectedFile || committing) return;
    setCommitting(true);
    setError(null);
    try {
      setResult(await apiClient.uploadAcademicFile(selectedFile, true));
      await invalidateCohortQueries();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Commit failed.");
    } finally {
      setCommitting(false);
    }
  };

  const handleResetDemo = async () => {
    if (resetting) return;
    setResetting(true);
    setError(null);
    try {
      const res = await apiClient.resetDemoCohort();
      setConfirmReset(false);
      setSelectedFile(null);
      setResult(null);
      setResetMsg(
        `Demo cohort restored (${res.students_seeded} students, ${res.snapshots_recomputed} snapshots).`,
      );
      await invalidateCohortQueries();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Demo cohort reset failed.");
    } finally {
      setResetting(false);
    }
  };

  const downloadSampleCsv = () => {
    const blob = new Blob([SAMPLE_UPLOAD_CSV], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "pulsegrid_sample_upload.csv";
    link.click();
    URL.revokeObjectURL(url);
  };

  const onDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragging(false);
    void handleFile(e.dataTransfer.files?.[0]);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-100">
            CSV / Excel Data Ingestion &amp; Auto-Mapper
          </h1>
          <p className="mt-0.5 text-xs text-slate-400">
            Preview fuzzy column mapping first, then commit atomically to recompute cohort risk
            snapshots.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={downloadSampleCsv}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-800"
          >
            <Download className="h-3.5 w-3.5 text-sky-400" />
            Download Sample Upload CSV
          </button>
          <button
            type="button"
            onClick={() => setConfirmReset((v) => !v)}
            disabled={resetting}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-900/80 px-3 py-1.5 text-xs font-medium text-slate-300 hover:border-amber-500/40 hover:text-amber-200"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            Reset to Demo Cohort
          </button>
        </div>
      </div>

      {confirmReset ? (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-amber-500/40 bg-amber-950/30 p-3.5 text-xs">
          <span className="text-amber-200">
            Confirm restoring the deterministic 240-student cohort and 4 pinned hero personas?
          </span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setConfirmReset(false)}
              className="rounded-md border border-slate-700 px-2.5 py-1 text-slate-300 hover:bg-slate-800"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={() => void handleResetDemo()}
              disabled={resetting}
              className="rounded-md bg-amber-500 px-3 py-1 font-semibold text-slate-950 hover:bg-amber-400"
            >
              {resetting ? "Restoring..." : "Confirm Reset"}
            </button>
          </div>
        </div>
      ) : null}

      {resetMsg ? (
        <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-emerald-500/40 bg-emerald-950/30 p-3.5 text-xs text-emerald-200">
          <span className="inline-flex items-center gap-1.5 font-medium">
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            {resetMsg}
          </span>
          {onNavigateDashboard ? (
            <button
              type="button"
              onClick={onNavigateDashboard}
              className="inline-flex items-center gap-1 rounded-md bg-emerald-500 px-2.5 py-1 font-semibold text-slate-950 hover:bg-emerald-400"
            >
              View Updated Dashboard <ArrowRight className="h-3.5 w-3.5" />
            </button>
          ) : null}
        </div>
      ) : null}

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={`flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-7 text-center transition ${
          dragging
            ? "border-emerald-400 bg-emerald-950/20"
            : "border-slate-700 bg-slate-900/50 hover:border-slate-600"
        }`}
      >
        <UploadCloud className="h-9 w-9 text-emerald-400" />
        <p className="mt-2.5 text-sm font-semibold text-slate-200">
          Drag &amp; drop CSV or XLSX sheet here
        </p>
        <p className="mt-1 text-xs text-slate-400">
          Supports messy columns like <span className="font-mono">Take-Home Assn (%)</span> or{" "}
          <span className="font-mono">Midterm Internal Marks</span> (max 5 MB).
        </p>
        <label className="mt-3.5 inline-flex cursor-pointer items-center gap-2 rounded-lg bg-emerald-500 px-4 py-2 text-xs font-semibold text-slate-950 hover:bg-emerald-400">
          <FileSpreadsheet className="h-4 w-4" />
          <span>{uploading ? "Analyzing File..." : "Choose File"}</span>
          <input
            type="file"
            accept=".csv,.xlsx,.xls"
            disabled={uploading || committing}
            onChange={(e) => {
              void handleFile(e.target.files?.[0]);
              e.target.value = "";
            }}
            className="hidden"
          />
        </label>
        {uploading ? (
          <div className="mt-3">
            <Spinner label="Running fuzzy header matching and health scan..." />
          </div>
        ) : null}
      </div>

      {error ? <ErrorBanner title="Upload Validation Failed" message={error} /> : null}

      {!result ? (
        <EmptyState
          title="No file previewed yet"
          description="Download the sample CSV or drop data/messy_sample.xlsx above to preview and commit records."
        />
      ) : (
        <UploadPreviewPanel
          result={result}
          committing={committing}
          canCommit={Boolean(selectedFile) && (result.missing_required ?? []).length === 0}
          onCommit={() => void handleCommit()}
          onNavigateDashboard={onNavigateDashboard}
        />
      )}
    </div>
  );
}
