import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from "recharts";
import { ChartEmptyState } from "./ChartCard";

export interface DonutSlice {
  name: string;
  value: number;
  color: string;
}

interface Props {
  data: DonutSlice[];
  formatter?: (v: number) => string;
  height?: number;
}

export default function DonutChart({ data, formatter, height = 160 }: Props) {
  const slices = data.filter((d) => d.value > 0);
  if (slices.length === 0) return <ChartEmptyState />;
  const total = slices.reduce((s, d) => s + d.value, 0);
  const fmt = formatter || ((v: number) => String(v));

  return (
    <div>
      <ResponsiveContainer width="100%" height={height}>
        <PieChart>
          <Pie data={slices} cx="50%" cy="50%" innerRadius="58%" outerRadius="88%"
               paddingAngle={2} dataKey="value" strokeWidth={0}>
            {slices.map((s) => <Cell key={s.name} fill={s.color} />)}
          </Pie>
          <Tooltip
            contentStyle={{
              background: "var(--bg-card)", border: "1px solid var(--border-subtle)",
              borderRadius: 10, color: "var(--text-primary)", fontSize: 12,
            }}
            formatter={(v: number, name: string) => [fmt(v), name]}
          />
        </PieChart>
      </ResponsiveContainer>
      <div className="mt-2 space-y-2">
        {slices.map((s) => (
          <div key={s.name} className="flex items-center gap-2.5 text-xs">
            <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: s.color }} />
            <span className="flex-1" style={{ color: "var(--text-secondary)" }}>{s.name}</span>
            <span className="font-semibold tabular-nums" style={{ color: "var(--text-primary)" }}>
              {total > 0 ? Math.round((s.value / total) * 100) : 0}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
