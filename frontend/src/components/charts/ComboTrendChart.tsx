import {
  ResponsiveContainer, ComposedChart, Bar, Line, XAxis, YAxis, Tooltip, CartesianGrid,
} from "recharts";
import { axisTick, gridStroke, chartTooltipStyle, ChartEmptyState } from "./ChartCard";

type SeriesInput = Record<string, number | null>;

interface Props {
  barData: SeriesInput;
  lineData: SeriesInput;
  barLabel: string;
  lineLabel: string;
  barColor?: string;
  lineColor?: string;
  barFormatter?: (v: number) => string;
  lineFormatter?: (v: number) => string;
  height?: number;
  // Optional second line, sharing the same right-hand axis as the first —
  // for percentage pairs like OPM %/NPM % this is the common case, so a
  // second axis would be redundant.
  lineData2?: SeriesInput;
  line2Label?: string;
  line2Color?: string;
}

export default function ComboTrendChart({
  barData, lineData, barLabel, lineLabel,
  barColor = "#c9a227", lineColor = "#e0793c",
  barFormatter, lineFormatter, height = 240,
  lineData2, line2Label, line2Color = "#4fb3a0",
}: Props) {
  const years = Array.from(
    new Set([...Object.keys(barData || {}), ...Object.keys(lineData || {}), ...Object.keys(lineData2 || {})])
  ).sort();

  const points = years
    .map((y) => ({ year: y, bar: barData?.[y], line: lineData?.[y], line2: lineData2?.[y] }))
    .filter((p) => p.bar !== null && p.bar !== undefined);

  if (points.length === 0) return <ChartEmptyState />;

  const bf = barFormatter || ((v: number) => String(v));
  const lf = lineFormatter || ((v: number) => String(v));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={points} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} vertical={false} />
        <XAxis dataKey="year" tick={axisTick} axisLine={false} tickLine={false} />
        <YAxis yAxisId="bar" tick={axisTick} axisLine={false} tickLine={false} tickFormatter={bf} width={56} />
        <YAxis yAxisId="line" orientation="right" tick={axisTick} axisLine={false} tickLine={false} tickFormatter={lf} width={56} />
        <Tooltip
          {...chartTooltipStyle}
          formatter={(v: number, name: string) =>
            [name === barLabel ? bf(v) : lf(v), name]
          }
        />
        <Bar yAxisId="bar" dataKey="bar" name={barLabel} fill={barColor} radius={[4, 4, 0, 0]} maxBarSize={34} />
        <Line yAxisId="line" dataKey="line" name={lineLabel} stroke={lineColor} strokeWidth={2}
              dot={{ r: 3, fill: lineColor, strokeWidth: 0 }} activeDot={{ r: 5 }} connectNulls />
        {lineData2 && (
          <Line yAxisId="line" dataKey="line2" name={line2Label} stroke={line2Color} strokeWidth={2}
                dot={{ r: 3, fill: line2Color, strokeWidth: 0 }} activeDot={{ r: 5 }} connectNulls />
        )}
      </ComposedChart>
    </ResponsiveContainer>
  );
}
