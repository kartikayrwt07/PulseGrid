import {
  CartesianGrid,
  Legend,
  ReferenceDot,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { TimeMachineBar } from "../../components/faculty/TimeMachineBar";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { DashboardSkeleton } from "../../components/ui/Skeleton";
import { useDashboardSummary } from "../../hooks/useDashboardSummary";
import { useTimeMachineState } from "../../hooks/useTimeMachineState";

interface TriageMatrixProps {
  onSelectStudent: (id: number) => void;
}

interface PlotDot {
  id: number;
  roll_no: string;
  name: string;
  tier: string;
  archetype: string;
  xRisk: number;
  yScore: number;
  cusumTriggered: boolean;
  isHeroAarav: boolean;
}

const TIER_COLORS: Record<string, string> = {
  CRITICAL: "#f43f5e",
  AT_RISK: "#f59e0b",
  WATCH: "#38bdf8",
  SAFE: "#10b981",
};

export function TriageMatrix({ onSelectStudent }: TriageMatrixProps) {
  const summary = useDashboardSummary();
  const tm = useTimeMachineState();

  if (summary.isLoading && tm.query.isLoading) return <DashboardSkeleton />;
  if (summary.isError && tm.query.isError) {
    return (
      <ErrorBanner
        title="Could not load triage matrix"
        message={summary.error instanceof Error ? summary.error.message : "Request failed"}
        onRetry={() => void summary.refetch()}
      />
    );
  }

  const tmData = tm.query.data;
  const dots: PlotDot[] = tmData
    ? tmData.points.map((pt) => ({
        id: pt.student_id,
        roll_no: pt.roll_no,
        name: pt.name,
        tier: tm.engine === "pulsegrid" ? pt.risk_tier : pt.naive_tier,
        archetype: pt.archetype,
        xRisk: tm.engine === "pulsegrid" ? pt.risk_score : pt.naive_risk_score,
        yScore: pt.projected_score,
        cusumTriggered: pt.cusum_triggered,
        isHeroAarav: pt.is_hero_aarav,
      }))
    : (summary.data?.triage_points ?? []).map((pt) => ({
        id: pt.id,
        roll_no: pt.roll_no,
        name: pt.name,
        tier: pt.risk_tier,
        archetype: pt.archetype,
        xRisk: pt.risk_score,
        yScore: pt.projected_score_after,
        cusumTriggered: false,
        isHeroAarav: pt.roll_no === "STU-001",
      }));

  if (!dots.length) {
    return (
      <EmptyState
        title="No triage coordinates available"
        description="Cohort snapshots must be populated before plotting urgency vs rescueability."
      />
    );
  }

  const byTier = (tier: string) => dots.filter((d) => d.tier === tier);
  const aaravDot = dots.find((d) => d.isHeroAarav);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold tracking-tight text-slate-100">
          2×2 Faculty Triage Matrix ({dots.length} Students · Week {tm.selectedWeek})
        </h1>
        <p className="mt-0.5 text-xs text-slate-400">
          Urgency (Risk Score) vs. Projected Standing. Scrub weeks or switch scoring engines; white
          beacon ring tracks STU-001 Aarav Kulkarni.
        </p>
      </div>

      {tmData ? (
        <TimeMachineBar
          data={tmData}
          selectedWeek={tm.selectedWeek}
          onSelectWeek={tm.selectWeek}
          playing={tm.playing}
          onTogglePlay={tm.togglePlay}
          engine={tm.engine}
          onSelectEngine={tm.setEngine}
        />
      ) : null}

      <section className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <QuadrantCard
          title="Top-Right: High Rescue ROI"
          count={dots.filter((p) => p.xRisk >= 50 && p.yScore >= 65).length}
          desc="Urgent but recoverable with targeted attendance/IA plan"
          tone="border-amber-500/30 text-amber-300"
        />
        <QuadrantCard
          title="Bottom-Right: Escalation Zone"
          count={dots.filter((p) => p.xRisk >= 50 && p.yScore < 65).length}
          desc="High risk requiring intensive mentoring or dean waiver"
          tone="border-rose-500/30 text-rose-300"
        />
        <QuadrantCard
          title="Top-Left: Safe / Monitor"
          count={dots.filter((p) => p.xRisk < 50 && p.yScore >= 65).length}
          desc="Stable cohort performance; light automated watch"
          tone="border-emerald-500/30 text-emerald-300"
        />
        <QuadrantCard
          title="Bottom-Left: Borderline"
          count={dots.filter((p) => p.xRisk < 50 && p.yScore < 65).length}
          desc="Low immediate risk but weak score ceiling"
          tone="border-sky-500/30 text-sky-300"
        />
      </section>

      <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
        <div className="h-[430px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 16, right: 20, bottom: 16, left: 4 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis
                type="number"
                dataKey="xRisk"
                name="Urgency (Risk Score)"
                domain={[0, 100]}
                stroke="#94a3b8"
                fontSize={12}
                label={{
                  value: "Urgency (Risk Score 0 → 100)",
                  position: "insideBottom",
                  offset: -8,
                  fill: "#94a3b8",
                  fontSize: 11,
                }}
              />
              <YAxis
                type="number"
                dataKey="yScore"
                name="Projected Score"
                domain={[30, 100]}
                stroke="#94a3b8"
                fontSize={12}
                tickFormatter={(v: number) => `${v}%`}
              />
              <ReferenceLine x={50} stroke="#475569" strokeDasharray="4 4" />
              <ReferenceLine y={65} stroke="#475569" strokeDasharray="4 4" />
              <Tooltip
                cursor={{ strokeDasharray: "3 3" }}
                content={({ active, payload }) => {
                  if (!active || !payload?.length) return null;
                  const pt = payload[0].payload as PlotDot;
                  return (
                    <div className="rounded-lg border border-slate-700 bg-slate-950 p-2.5 text-xs shadow-lg">
                      <p className="font-bold text-slate-100">
                        {pt.name} ({pt.roll_no})
                      </p>
                      <p className="text-slate-400">
                        {pt.archetype} · {pt.tier}
                        {pt.cusumTriggered ? " · CUSUM Active" : ""}
                      </p>
                      <p className="mt-1 text-slate-200">
                        Risk: <span className="font-mono">{pt.xRisk.toFixed(1)}</span> · Projected:{" "}
                        <span className="font-mono text-emerald-300">{pt.yScore.toFixed(1)}%</span>
                      </p>
                    </div>
                  );
                }}
              />
              <Legend verticalAlign="top" height={32} wrapperStyle={{ fontSize: "12px" }} />
              {(["CRITICAL", "AT_RISK", "WATCH", "SAFE"] as const).map((tier) => (
                <Scatter
                  key={tier}
                  name={tier}
                  data={byTier(tier)}
                  fill={TIER_COLORS[tier]}
                  cursor="pointer"
                  onClick={(entry) => {
                    const pt = entry as unknown as PlotDot;
                    if (pt?.id) onSelectStudent(pt.id);
                  }}
                />
              ))}
              {aaravDot ? (
                <ReferenceDot
                  x={aaravDot.xRisk}
                  y={aaravDot.yScore}
                  r={10}
                  fill="none"
                  stroke="#ffffff"
                  strokeWidth={2.5}
                  label={{
                    value: "STU-001 Aarav",
                    fill: "#f8fafc",
                    fontSize: 11,
                    position: "top",
                  }}
                />
              ) : null}
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </section>
    </div>
  );
}

function QuadrantCard({
  title,
  count,
  desc,
  tone,
}: {
  title: string;
  count: number;
  desc: string;
  tone: string;
}) {
  return (
    <div className={`rounded-xl border bg-slate-900/70 p-3.5 ${tone}`}>
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold">{title}</p>
        <span className="font-mono text-lg font-bold">{count}</span>
      </div>
      <p className="mt-1 text-[11px] text-slate-400">{desc}</p>
    </div>
  );
}
