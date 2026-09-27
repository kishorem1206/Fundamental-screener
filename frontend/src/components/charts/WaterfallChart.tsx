import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Cell, LabelList,
} from "recharts";
import { axisTick, gridStroke, ChartEmptyState } from "./ChartCard";

export interface WaterfallStep {
  label: string;
  value: number;
}

interface Props {
  steps: WaterfallStep[];
  formatter?: (v: number) => string;
}

const TOTAL_COLOR = "#c9a227";
const UP_COLOR = "#4fb3a0";
const DOWN_COLOR = "#e0793c";

// Standard bridge-chart construction: each declared `step` is a running total
// (e.g. Revenue, EBITDA, PAT); a connecting delta bar is synthesized between
// each pair showing the drop/rise from one total to the next.
//
// Real bug found 2026-09-15: the original version stacked a transparent
// "base" Bar under a colored "value" Bar (same stackId) to make the delta
// segment float — that never actually offset anything, so every delta bar
// rendered from zero exactly like the total bars, making the chart
// unreadable as a bridge (a company with a large expense base showed its
// "-> EBITDA" delta as a bar nearly as tall as Revenue itself, sitting on
// the baseline, rather than a short segment floating between EBITDA and
// Revenue's actual levels). Recharts supports range bars natively — a
// dataKey resolving to a [min, max] tuple draws a bar spanning exactly that
// range — which is what floating a delta segment actually requires.
function buildBars(steps: WaterfallStep[]) {
  const bars: { name: string; range: [number, number]; display: number; kind: "total" | "up" | "down" }[] = [];
  for (let i = 0; i < steps.length; i++) {
    const step = steps[i];
    bars.push({ name: step.label, range: [0, step.value], display: step.value, kind: "total" });
    if (i < steps.length - 1) {
      const next = steps[i + 1];
      const delta = next.value - step.value;
      const lo = Math.min(step.value, next.value);
      const hi = Math.max(step.value, next.value);
      bars.push({
        name: `→ ${next.label}`,
        range: [lo, hi],
        display: delta,
        kind: delta >= 0 ? "up" : "down",
      });
    }
  }
  return bars;
}

export default function WaterfallChart({ steps, formatter }: Props) {
  const valid = steps.filter((s) => s.value !== null && s.value !== undefined && !Number.isNaN(s.value));
  if (valid.length < 2) return <ChartEmptyState message="Not enough data for a P&L bridge" />;

  const bars = buildBars(valid);
  const fmt = formatter || ((v: number) => String(v));

  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={bars} margin={{ top: 16, right: 8, left: 0, bottom: 0 }} barGap={2}>
        <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} vertical={false} />
        <XAxis dataKey="name" tick={axisTick} axisLine={false} tickLine={false} interval={0} />
        <YAxis tick={axisTick} axisLine={false} tickLine={false} tickFormatter={fmt} width={56} />
        <Tooltip
          contentStyle={{
            background: "var(--bg-card)", border: "1px solid var(--border-subtle)",
            borderRadius: 10, color: "var(--text-primary)", fontSize: 12,
          }}
          formatter={(_v: number, _n: string, entry) => {
            const p = entry?.payload as (typeof bars)[number];
            return [fmt(p.display), p.kind === "total" ? "Total" : p.kind === "up" ? "Increase" : "Decrease"];
          }}
        />
        <Bar dataKey="range" radius={[4, 4, 4, 4]}>
          {bars.map((b, i) => (
            <Cell key={i} fill={b.kind === "total" ? TOTAL_COLOR : b.kind === "up" ? UP_COLOR : DOWN_COLOR} />
          ))}
          <LabelList
            dataKey="display"
            position="top"
            formatter={(v: number) => fmt(v)}
            style={{ fill: "var(--text-secondary)", fontSize: 10 }}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
