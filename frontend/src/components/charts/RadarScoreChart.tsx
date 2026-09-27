import {
  ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Tooltip,
} from "recharts";
import { chartTooltipStyle, ChartEmptyState } from "./ChartCard";
import type { Scores } from "../../types";

const CATEGORIES: { key: keyof Scores; label: string }[] = [
  { key: "growth", label: "Growth" },
  { key: "profitability", label: "Profitability" },
  { key: "cash_flow", label: "Cash Flow" },
  { key: "balance_sheet", label: "Balance Sheet" },
  { key: "efficiency", label: "Efficiency" },
  { key: "valuation", label: "Valuation" },
];

export default function RadarScoreChart({ scores }: { scores: Scores | null }) {
  if (!scores) return <ChartEmptyState message="No score breakdown available" />;

  const data = CATEGORIES.map(({ key, label }) => ({
    category: label,
    score: (scores[key] as number | null) ?? 0,
    hasValue: scores[key] !== null && scores[key] !== undefined,
  }));

  if (data.every((d) => !d.hasValue)) return <ChartEmptyState message="No score breakdown available" />;

  return (
    <ResponsiveContainer width="100%" height={420}>
      <RadarChart data={data} outerRadius="78%">
        <PolarGrid stroke="rgba(255,255,255,0.08)" />
        <PolarAngleAxis dataKey="category" tick={{ fill: "var(--text-secondary)", fontSize: 13.5 }} />
        <PolarRadiusAxis domain={[0, 100]} tick={{ fill: "var(--text-dim)", fontSize: 10 }} axisLine={false} tickCount={5} />
        <Radar
          dataKey="score"
          stroke="#c9a227"
          strokeWidth={2.5}
          fill="#c9a227"
          fillOpacity={0.22}
          dot={{ r: 4, fill: "#c9a227", strokeWidth: 0 }}
        />
        <Tooltip
          {...chartTooltipStyle}
          formatter={(v: number) => [v.toFixed(1), "Score"]}
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}
