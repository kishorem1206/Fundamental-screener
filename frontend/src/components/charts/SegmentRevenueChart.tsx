import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Legend,
} from "recharts";
import { axisTick, gridStroke, ChartEmptyState } from "./ChartCard";
import type { BusinessSegmentItem } from "../../types";

const PALETTE = ["#c9a227", "#4fb3a0", "#e0793c", "#e8c766", "#7fb8ff", "#d9694f", "#4fb3a0", "#e0793c"];

function fyLabel(isoDate: string): string {
  const year = isoDate.slice(0, 4);
  return `FY${year.slice(2)}`;
}

export default function SegmentRevenueChart({ segments }: { segments: BusinessSegmentItem[] }) {
  if (segments.length === 0) return <ChartEmptyState message="No segment-level revenue data available" />;

  const segmentNames = Array.from(new Set(segments.map((s) => s.segment_name)));
  const years = Array.from(new Set(segments.map((s) => s.fiscal_year))).sort();

  const data = years.map((fy) => {
    const row: Record<string, string | number> = { fy: fyLabel(fy) };
    for (const name of segmentNames) {
      const match = segments.find((s) => s.fiscal_year === fy && s.segment_name === name);
      if (match) row[name] = match.revenue / 1e7; // plain INR -> Cr
    }
    return row;
  });

  const colorFor = (name: string) => PALETTE[segmentNames.indexOf(name) % PALETTE.length];

  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} vertical={false} />
        <XAxis dataKey="fy" tick={axisTick} axisLine={false} tickLine={false} />
        <YAxis tick={axisTick} axisLine={false} tickLine={false}
               tickFormatter={(v) => v >= 1000 ? `₹${(v / 1000).toFixed(0)}kCr` : `₹${v.toFixed(0)}Cr`} width={56} />
        <Tooltip
          contentStyle={{
            background: "var(--bg-card)", border: "1px solid var(--border-subtle)",
            borderRadius: 10, color: "var(--text-primary)", fontSize: 12,
          }}
          formatter={(v: number) => `₹${v.toFixed(0)} Cr`}
        />
        <Legend wrapperStyle={{ fontSize: 11, color: "var(--text-dim)" }} />
        {segmentNames.map((name) => (
          <Bar key={name} dataKey={name} stackId="segments" fill={colorFor(name)} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
