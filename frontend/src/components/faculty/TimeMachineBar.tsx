import { AlertTriangle, Pause, Play, Sparkles, Zap } from "lucide-react";
import type { Schemas } from "../../api/client";

export type ScoringEngineMode = "pulsegrid" | "naive";

interface TimeMachineBarProps {
  data: Schemas["TimeMachineResponse"];
  selectedWeek: number;
  onSelectWeek: (wk: number) => void;
  playing: boolean;
  onTogglePlay: () => void;
  engine: ScoringEngineMode;
  onSelectEngine: (mode: ScoringEngineMode) => void;
}

export function TimeMachineBar({
  data,
  selectedWeek,
  onSelectWeek,
  playing,
  onTogglePlay,
  engine,
  onSelectEngine,
}: TimeMachineBarProps) {
  const active = engine === "pulsegrid" ? data.pulsegrid : data.naive_static;

  return (
    <div className="space-y-3 rounded-xl border border-slate-800 bg-slate-900/80 p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={onTogglePlay}
            aria-label={playing ? "Pause Week Replay" : "Play Week 4 to 9 Replay"}
            className="inline-flex items-center gap-1.5 rounded-lg border border-emerald-500/40 bg-emerald-500/15 px-3 py-1.5 text-xs font-semibold text-emerald-300 hover:bg-emerald-500/25"
          >
            {playing ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
            {playing ? "Pause" : "Replay"}
          </button>

          <div
            role="group"
            aria-label="Week Time Machine Scrubber"
            className="inline-flex flex-wrap items-center gap-1 rounded-lg border border-slate-800 bg-slate-950/70 p-1"
          >
            {data.available_weeks.map((wk) => (
              <button
                key={wk}
                type="button"
                onClick={() => onSelectWeek(wk)}
                className={`rounded-md px-2.5 py-1 text-xs font-semibold transition ${
                  wk === selectedWeek
                    ? "bg-emerald-500 text-slate-950"
                    : "text-slate-400 hover:bg-slate-800 hover:text-slate-100"
                }`}
              >
                Wk {wk}
              </button>
            ))}
          </div>
        </div>

        <div
          role="group"
          aria-label="Scoring Engine Toggle"
          className="inline-flex rounded-lg border border-slate-700 bg-slate-950/80 p-1 text-xs"
        >
          <button
            type="button"
            onClick={() => onSelectEngine("pulsegrid")}
            className={`rounded-md px-3 py-1 font-semibold transition ${
              engine === "pulsegrid"
                ? "bg-sky-500/25 text-sky-300"
                : "text-slate-400 hover:text-slate-100"
            }`}
          >
            PulseGrid (Cohort-Calibrated)
          </button>
          <button
            type="button"
            onClick={() => onSelectEngine("naive")}
            className={`rounded-md px-3 py-1 font-semibold transition ${
              engine === "naive"
                ? "bg-rose-500/25 text-rose-300"
                : "text-slate-400 hover:text-slate-100"
            }`}
          >
            Naive Static (&lt;60%)
          </button>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2 text-xs">
        <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/40 bg-emerald-500/10 px-3 py-1 font-medium text-emerald-300">
          <Sparkles className="h-3.5 w-3.5" />
          {data.delta_callout}
        </span>

        {data.shock_banner ? (
          <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-500/40 bg-amber-500/15 px-3 py-1 font-medium text-amber-200">
            <AlertTriangle className="h-3.5 w-3.5 text-amber-400" />
            {data.shock_banner.message}
          </span>
        ) : null}

        <span className="ml-auto inline-flex items-center gap-1.5 rounded-md border border-slate-800 bg-slate-950/60 px-2.5 py-1 font-mono text-[11px] text-slate-300">
          <Zap className="h-3 w-3 text-sky-400" />
          Wk {selectedWeek} Flagged: {active.flagged_count} · On-Track False Alarms:{" "}
          <span className={active.false_alarms_on_track > 0 ? "text-rose-300" : "text-emerald-300"}>
            {active.false_alarms_on_track}
          </span>
          {" · "}Aarav Detected: {active.aarav_detected ? "YES" : "NO"}
        </span>
      </div>
    </div>
  );
}
