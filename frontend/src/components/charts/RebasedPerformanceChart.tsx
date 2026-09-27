import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, Legend } from "recharts";
import { axisTick, gridStroke, chartTooltipStyle, ChartEmptyState } from "./ChartCard";
import type { PeerPerformanceSeries } from "../../types";

const COLORS = ["#c9a227", "#4fb3a0", "#e0793c", "#d9694f", "#e8c766", "#a9b3c9"];

function fmtDate(d: string) {
  const dt = new Date(d);
  return Number.isNaN(dt.getTime()) ? d : dt.toLocaleDateString("en-IN", { month: "short", day: "2-digit" });
}

export default function RebasedPerformanceChart({ series }: { series: PeerPerformanceSeries[] }) {
  if (series.length < 2) return <ChartEmptyState message="Not enough peer price history for a comparison" />;

  // Merge every series onto one row-per-date grid (Recharts needs one
  // array of objects, one key per line) — series share the same fetch
  // window so their point counts line up 1:1 by index.
  const pointCount = Math.min(...series.map((s) => s.points.length));
  const rows = Array.from({ length: pointCount }, (_, i) => {
    const row: Record<string, string | number> = { date: fmtDate(series[0].points[i].date) };
    for (const s of series) row[s.name] = s.points[i].value;
    return row;
  });

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={rows} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} vertical={false} />
        <XAxis dataKey="date" tick={axisTick} axisLine={false} tickLine={false} />
        <YAxis tick={axisTick} axisLine={false} tickLine={false} width={44} tickFormatter={(v) => `${v}`} />
        <Tooltip {...chartTooltipStyle} formatter={(v: number) => v.toFixed(1)} />
        <Legend wrapperStyle={{ fontSize: 11 }} />
        {series.map((s, i) => (
          <Line
            key={s.name} type="monotone" dataKey={s.name}
            stroke={COLORS[i % COLORS.length]} strokeWidth={s.is_subject ? 2.5 : 1.5}
            dot={false} isAnimationActive={false}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
