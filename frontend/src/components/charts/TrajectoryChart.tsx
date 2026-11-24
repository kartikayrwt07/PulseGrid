import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Schemas } from "../../api/client";
import { EmptyState } from "../ui/EmptyState";

interface TrajectoryChartProps {
  data: Schemas["WeeklyTrajectoryPoint"][];
  cusumTriggered: boolean;
  cusumWeek?: number | null;
  lightMode?: boolean;
}

export function TrajectoryChart({
  data,
  cusumTriggered,
  cusumWeek,
  lightMode = false,
}: TrajectoryChartProps) {
  if (!data || data.length === 0) {
    return (
      <EmptyState
        title="No weekly trajectory data"
        description="Weekly attendance and assessment points will appear once records are ingested."
      />
    );
  }

  const gridStroke = lightMode ? "#cbd5e1" : "#1e293b";
  const axisStroke = lightMode ? "#334155" : "#94a3b8";
  const zAxisStroke = lightMode ? "#0369a1" : "#38bdf8";
  const cusumLabel = lightMode ? "#be123c" : "#fda4af";

  const chartNode = (
    <LineChart
      width={lightMode ? 680 : undefined}
      height={lightMode ? 210 : undefined}
      data={data}
      margin={{ top: 14, right: 16, left: 0, bottom: 4 }}
    >
      <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
      <XAxis
        dataKey="week"
        tickFormatter={(w: number) => `Wk ${w}`}
        stroke={axisStroke}
        fontSize={11}
      />
      <YAxis
        yAxisId="left"
        domain={[0, 100]}
        stroke={axisStroke}
        fontSize={11}
        tickFormatter={(v: number) => `${v}%`}
      />
      <YAxis
        yAxisId="right"
        orientation="right"
        domain={[-3, 3]}
        stroke={zAxisStroke}
        fontSize={11}
        tickFormatter={(v: number) => `${v.toFixed(1)}σ`}
      />
      <Tooltip
        contentStyle={{
          backgroundColor: lightMode ? "#ffffff" : "#0f172a",
          borderColor: lightMode ? "#cbd5e1" : "#334155",
          borderRadius: "0.5rem",
          fontSize: "12px",
        }}
        labelFormatter={(w) => `Week ${w}`}
      />
      <Legend wrapperStyle={{ fontSize: "11px" }} />
      <ReferenceLine
        yAxisId="left"
        y={75}
        stroke="#d97706"
        strokeDasharray="3 3"
        label={{ value: "75% Min", fill: "#d97706", fontSize: 10, position: "insideTopLeft" }}
      />
      {cusumTriggered && cusumWeek ? (
        <ReferenceLine
          yAxisId="left"
          x={cusumWeek}
          stroke="#e11d48"
          strokeWidth={2}
          strokeDasharray="4 4"
          label={{
            value: `CUSUM Wk ${cusumWeek}`,
            fill: cusumLabel,
            fontSize: 11,
            position: "top",
          }}
        />
      ) : null}
      <Line
        yAxisId="left"
        type="monotone"
        dataKey="composite"
        name="Raw Composite (%)"
        stroke={lightMode ? "#059669" : "#10b981"}
        strokeWidth={2.5}
        dot={{ r: 3 }}
        isAnimationActive={!lightMode}
      />
      <Line
        yAxisId="left"
        type="monotone"
        dataKey="attendance_pct"
        name="Attendance (%)"
        stroke={lightMode ? "#7c3aed" : "#a78bfa"}
        strokeWidth={1.75}
        dot={false}
        isAnimationActive={!lightMode}
      />
      <Line
        yAxisId="left"
        type="monotone"
        dataKey="internal_score"
        name="Internal Score (%)"
        stroke={lightMode ? "#ea580c" : "#fb923c"}
        strokeWidth={1.75}
        dot={false}
        isAnimationActive={!lightMode}
      />
      <Line
        yAxisId="right"
        type="monotone"
        dataKey="z_composite"
        name="Cohort Z-Score (σ)"
        stroke={zAxisStroke}
        strokeWidth={2}
        strokeDasharray="5 3"
        dot={{ r: 2.5 }}
        isAnimationActive={!lightMode}
      />
    </LineChart>
  );

  if (lightMode) {
    return (
      <div className="print-chart overflow-x-auto rounded-lg border border-slate-200 bg-white p-2 text-slate-900">
        {chartNode}
      </div>
    );
  }

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        {chartNode}
      </ResponsiveContainer>
    </div>
  );
}
