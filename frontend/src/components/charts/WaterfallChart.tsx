import { useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Schemas } from "../../api/client";
import { EmptyState } from "../ui/EmptyState";

interface WaterfallChartProps {
  entries: Schemas["SHAPEntry"][];
  groupedEntries?: Schemas["SHAPEntry"][];
}

export function WaterfallChart({ entries, groupedEntries }: WaterfallChartProps) {
  const hasGrouped = Boolean(groupedEntries && groupedEntries.length > 0);
  const [mode, setMode] = useState<"grouped" | "raw">("grouped");
  const activeMode = hasGrouped ? mode : "raw";
  const activeSource = activeMode === "grouped" && groupedEntries ? groupedEntries : entries;

  if (!activeSource || activeSource.length === 0) {
    return (
      <EmptyState
        title="No SHAP attribution entries"
        description="Feature attributions will appear once model inference runs for this student."
      />
    );
  }

  const sorted = [...activeSource].sort(
    (a, b) => Math.abs(b.shap_value) - Math.abs(a.shap_value),
  );
  const chartHeight = activeMode === "grouped" ? 270 : Math.max(270, sorted.length * 24);

  return (
    <div className="space-y-2.5">
      {hasGrouped ? (
        <div className="inline-flex rounded-lg border border-slate-700 bg-slate-950/70 p-0.5 text-[11px]">
          <button
            type="button"
            onClick={() => setMode("grouped")}
            className={`rounded-md px-2.5 py-1 font-medium transition ${
              activeMode === "grouped"
                ? "bg-sky-500/20 text-sky-300"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Grouped Factors
          </button>
          <button
            type="button"
            onClick={() => setMode("raw")}
            className={`rounded-md px-2.5 py-1 font-medium transition ${
              activeMode === "raw"
                ? "bg-sky-500/20 text-sky-300"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Raw 20 Features
          </button>
        </div>
      ) : null}

      <div className="h-72 w-full overflow-y-auto pr-1">
        <div style={{ height: chartHeight }} className="w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={sorted}
              layout="vertical"
              margin={{ top: 8, right: 20, left: 16, bottom: 8 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
              <XAxis
                type="number"
                stroke="#94a3b8"
                fontSize={11}
                tickFormatter={(v: number) => `${v > 0 ? "+" : ""}${v.toFixed(2)}`}
              />
              <YAxis
                type="category"
                dataKey="label"
                width={175}
                stroke="#cbd5e1"
                fontSize={11}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#0f172a",
                  borderColor: "#334155",
                  borderRadius: "0.5rem",
                  fontSize: "12px",
                }}
                formatter={(value) => {
                  const num = Number(value);
                  return [
                    `${num >= 0 ? "+" : ""}${num.toFixed(3)} (${num >= 0 ? "Increases Risk" : "Protective"})`,
                    "SHAP Impact",
                  ];
                }}
              />
              <ReferenceLine x={0} stroke="#64748b" />
              <Bar dataKey="shap_value" radius={[4, 4, 4, 4]}>
                {sorted.map((entry) => (
                  <Cell
                    key={entry.feature}
                    fill={entry.shap_value >= 0 ? "#f43f5e" : "#10b981"}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
