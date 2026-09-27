import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid
} from "recharts";

type SeriesInput = Record<string, number | null> | Array<{ year?: string | number; value: number }>;

function toPoints(data: SeriesInput): Array<{ label: string; value: number }> {
  if (Array.isArray(data)) {
    return data
      .filter((d) => d.value !== null && d.value !== undefined)
      .map((d, i) => ({ label: d.year ? String(d.year) : `Y${i + 1}`, value: d.value }));
  }
  return Object.entries(data)
    .filter(([, v]) => v !== null && v !== undefined)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([year, value]) => ({ label: year, value: value! }));
}

interface Props {
  data: SeriesInput;
  color?: string;
  formatter?: (v: number) => string;
  height?: number;
}

export default function TrendChart({ data, color = "#c9a227", formatter, height = 140 }: Props) {
  const points = toPoints(data);

  if (points.length === 0) {
    return (
      <div className="flex items-center justify-center text-xs"
           style={{ height, color: "var(--text-dim)" }}>
        No data
      </div>
    );
  }

  const gradId = `grad-${color.replace("#", "")}`;

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={points} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={color} stopOpacity={0.25} />
            <stop offset="95%" stopColor={color} stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
        <XAxis dataKey="label" tick={{ fill: "var(--text-dim)", fontSize: 11 }}
               axisLine={false} tickLine={false} />
        <YAxis tick={{ fill: "var(--text-dim)", fontSize: 11 }} axisLine={false}
               tickLine={false} width={52} tickFormatter={formatter || ((v) => String(v))} />
        <Tooltip
          contentStyle={{
            background: "var(--bg-card)", border: "1px solid var(--border-subtle)",
            borderRadius: 8, color: "var(--text-primary)", fontSize: 12,
          }}
          formatter={(v: number) => [formatter ? formatter(v) : v, ""]}
        />
        <Area type="monotone" dataKey="value" stroke={color} strokeWidth={2}
              fill={`url(#${gradId})`}
              dot={{ r: 3, fill: color, strokeWidth: 0 }}
              activeDot={{ r: 5, fill: color }} />
      </AreaChart>
    </ResponsiveContainer>
  );
}
