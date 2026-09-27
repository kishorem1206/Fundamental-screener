import { useState } from "react";
import {
  ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, ZAxis, Tooltip, CartesianGrid, Cell, Customized,
} from "recharts";
import { axisTick, gridStroke, ChartEmptyState } from "./ChartCard";
import type { PeerEntry } from "../../types";

// Short display name for on-chart labels — full name still shows in the
// hover tooltip. Strips the common corporate suffixes so labels stay
// compact next to each dot rather than overlapping.
function shortName(name: string): string {
  return name.replace(/\s+(Ltd\.?|Limited|Inc\.?|Corporation|Corp\.?)$/i, "").trim();
}

// ── Label collision avoidance (2026-09-23 fix — peer labels were stacking
// on top of each other whenever several peers clustered close together,
// e.g. several IT-services peers all sitting near 10-15% revenue CAGR /
// 10-20x P/E). Recharts has no built-in label-collision handling for
// scatter charts, so this runs a small greedy pairwise-separation pass in
// PIXEL space (via the chart's own computed point coordinates, read through
// the officially-supported `Customized` component — NOT a DOM hack) after
// every render, covering peers AND the subject star point together so they
// never overlap each other either. General-purpose: works for any cluster
// size/shape, not tuned to one chart's data. ──────────────────────────────

interface LabelBox {
  key: string;
  anchorX: number; anchorY: number; // the dot/bubble's real pixel center — labels never drift arbitrarily far from this
  cx: number; cy: number;           // label block's current center (mutated during resolution)
  initialCx: number; initialCy: number;
  width: number; height: number;
  name: string; valueText: string;
}

// Rough monospace-independent width estimate for a proportional sans-serif
// font — accurate enough for collision math, not for pixel-perfect layout.
function estimateTextWidth(text: string, fontSize: number, bold: boolean): number {
  return text.length * fontSize * (bold ? 0.62 : 0.54);
}

const LABEL_BLOCK_HEIGHT = 18;
const LABEL_PADDING = 3;
const MAX_ITERATIONS = 80;

function resolveLabelOverlaps(boxes: LabelBox[]): void {
  for (let iter = 0; iter < MAX_ITERATIONS; iter++) {
    let moved = false;
    for (let i = 0; i < boxes.length; i++) {
      for (let j = i + 1; j < boxes.length; j++) {
        const a = boxes[i];
        const b = boxes[j];
        const ax1 = a.cx - a.width / 2 - LABEL_PADDING;
        const ax2 = a.cx + a.width / 2 + LABEL_PADDING;
        const ay1 = a.cy - a.height / 2 - LABEL_PADDING;
        const ay2 = a.cy + a.height / 2 + LABEL_PADDING;
        const bx1 = b.cx - b.width / 2 - LABEL_PADDING;
        const bx2 = b.cx + b.width / 2 + LABEL_PADDING;
        const by1 = b.cy - b.height / 2 - LABEL_PADDING;
        const by2 = b.cy + b.height / 2 + LABEL_PADDING;
        const overlapX = Math.min(ax2, bx2) - Math.max(ax1, bx1);
        const overlapY = Math.min(ay2, by2) - Math.max(ay1, by1);
        if (overlapX > 0 && overlapY > 0) {
          moved = true;
          // Push apart along whichever axis has the smaller overlap — the
          // cheaper separation, so labels don't travel further than needed.
          if (overlapX < overlapY) {
            const shift = overlapX / 2 + 0.5;
            if (a.cx <= b.cx) { a.cx -= shift; b.cx += shift; } else { a.cx += shift; b.cx -= shift; }
          } else {
            const shift = overlapY / 2 + 0.5;
            if (a.cy <= b.cy) { a.cy -= shift; b.cy += shift; } else { a.cy += shift; b.cy -= shift; }
          }
        }
      }
    }
    if (!moved) break;
  }
}

// Loosely-typed on purpose: recharts doesn't export a precise TS shape for
// what it injects into a `Customized` render prop (it spreads the chart's
// internal `state`, confirmed via source — `formattedGraphicalItems` is a
// real, stable field, just not part of the public API surface/typings).
// Every access below is defensively guarded so a shape change in a future
// recharts version degrades to "no labels drawn" rather than a crash.
function PeerLabelsOverlay(props: Record<string, unknown>) {
  const items = props.formattedGraphicalItems as
    | Array<{ props?: { points?: Array<Record<string, unknown>> } }>
    | undefined;
  if (!Array.isArray(items)) return null;

  const boxes: LabelBox[] = [];
  items.forEach((graphicalItem, itemIdx) => {
    const points = graphicalItem?.props?.points;
    if (!Array.isArray(points)) return;
    points.forEach((point, pointIdx) => {
      const cx = point.cx;
      const cy = point.cy;
      const label = point.label;
      if (typeof cx !== "number" || typeof cy !== "number" || !Number.isFinite(cx) || !Number.isFinite(cy)) return;
      if (typeof label !== "string" || !label) return;
      const [name, valueText] = label.split("|");
      if (!name) return;
      const radius = typeof point.height === "number" ? point.height / 2 : 6;
      const initialCy = cy - Math.max(radius, 6) - (LABEL_BLOCK_HEIGHT / 2 + 4);
      const width = Math.max(
        estimateTextWidth(name, 10, true),
        estimateTextWidth(valueText ?? "", 9, false),
      ) + 4;
      boxes.push({
        key: `${itemIdx}-${pointIdx}`,
        anchorX: cx, anchorY: cy,
        cx, cy: initialCy,
        initialCx: cx, initialCy,
        width, height: LABEL_BLOCK_HEIGHT,
        name, valueText: valueText ?? "",
      });
    });
  });

  if (boxes.length === 0) return null;
  resolveLabelOverlaps(boxes);

  return (
    <g>
      {boxes.map((b) => {
        const displaced = Math.hypot(b.cx - b.initialCx, b.cy - b.initialCy) > 6;
        return (
          <g key={b.key}>
            {displaced && (
              <line
                x1={b.anchorX} y1={b.anchorY} x2={b.cx} y2={b.cy}
                stroke="var(--text-dim)" strokeWidth={0.75} strokeDasharray="2 2" opacity={0.55}
              />
            )}
            <text x={b.cx} y={b.cy - 3} textAnchor="middle" fontSize={10} fontWeight={600} fill="var(--text-secondary)">
              {b.name}
            </text>
            <text x={b.cx} y={b.cy + 8} textAnchor="middle" fontSize={9} fill="var(--text-dim)">
              {b.valueText}
            </text>
          </g>
        );
      })}
    </g>
  );
}

interface SubjectPoint {
  company_name: string;
  market_cap?: number | null;
  revenue_cagr_3y?: number | null;
  roce?: number | null;
  pe_ratio?: number | null;
}

interface Props {
  peers: PeerEntry[];
  subject: SubjectPoint | null;
  // Fixes the Y-axis metric and hides the interactive toggle buttons —
  // for a static, printed context (the editorial report) where a
  // clickable toggle can't do anything and would just render as a dead
  // control. The live dashboard's own usage never passes this, so its
  // interactive ROCE/P-E toggle is unchanged. `height` lets a caller ask
  // for a bigger chart than the dashboard's default 280px (added for the
  // same editorial-report use — "much bigger size to be clear").
  fixedMetric?: "roce" | "pe_ratio";
  height?: number;
}

const Y_OPTIONS = [
  { key: "roce" as const, label: "ROCE %" },
  { key: "pe_ratio" as const, label: "P/E" },
];

export default function PeerScatterChart({ peers, subject, fixedMetric, height = 280 }: Props) {
  const [yKeyState, setYKey] = useState<"roce" | "pe_ratio">("roce");
  const yKey = fixedMetric ?? yKeyState;

  const yUnit = yKey === "roce" ? "%" : "x";

  const toPoint = (p: SubjectPoint | PeerEntry) => {
    const yVal = p[yKey] ?? null;
    return {
      name: p.company_name,
      x: p.revenue_cagr_3y ?? null,
      y: yVal,
      z: p.market_cap ? p.market_cap / 1e9 : 4,
      // Unit baked in here (not passed separately to the label renderer)
      // since the collision-avoidance overlay below reads labels off the
      // chart's own computed points, not a per-point React prop.
      label: yVal !== null ? `${shortName(p.company_name)}|${yVal.toFixed(1)}${yUnit}` : shortName(p.company_name),
    };
  };

  const peerPoints = peers.map(toPoint).filter((p) => p.x !== null && p.y !== null);
  const subjectPoint = subject ? toPoint(subject) : null;
  const hasSubject = subjectPoint && subjectPoint.x !== null && subjectPoint.y !== null;

  return (
    <div>
      {!fixedMetric && (
        <div className="flex items-center justify-end gap-1 mb-2">
          {Y_OPTIONS.map((o) => (
            <button
              key={o.key}
              onClick={() => setYKey(o.key)}
              className="px-2.5 py-1 rounded-md text-[11px] font-semibold transition-colors"
              style={{
                background: yKey === o.key ? "rgba(201,162,39,0.16)" : "transparent",
                color: yKey === o.key ? "#e8c766" : "var(--text-dim)",
                border: `1px solid ${yKey === o.key ? "rgba(201,162,39,0.35)" : "var(--border-subtle)"}`,
              }}
            >
              {o.label}
            </button>
          ))}
        </div>
      )}
      {peerPoints.length === 0 && !hasSubject ? (
        <ChartEmptyState message="No comparable peer metrics available" />
      ) : (
        <ResponsiveContainer width="100%" height={height}>
          <ScatterChart margin={{ top: 24, right: 16, left: 0, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
            <XAxis type="number" dataKey="x" name="Revenue CAGR 3Y" unit="%"
                   tick={axisTick} axisLine={false} tickLine={false}
                   label={{ value: "Revenue CAGR 3Y (%)", position: "insideBottom", offset: -2, fill: "var(--text-dim)", fontSize: 10 }} />
            <YAxis type="number" dataKey="y" name={Y_OPTIONS.find((o) => o.key === yKey)!.label}
                   tick={axisTick} axisLine={false} tickLine={false} width={48} />
            <ZAxis type="number" dataKey="z" range={[40, 400]} name="Market Cap" unit="B" />
            <Tooltip
              cursor={{ strokeDasharray: "3 3", stroke: "var(--border-subtle)" }}
              contentStyle={{
                background: "var(--bg-card)", border: "1px solid var(--border-subtle)",
                borderRadius: 10, color: "var(--text-primary)", fontSize: 12,
              }}
              formatter={(value: number, name: string) => [
                name === "Market Cap" ? `₹${value.toFixed(1)}B` : `${value.toFixed(1)}${name.includes("CAGR") ? "%" : ""}`,
                name,
              ]}
              labelFormatter={() => ""}
              content={({ active, payload }) => {
                if (!active || !payload?.length) return null;
                const p = payload[0].payload as { name: string; x: number; y: number; z: number };
                return (
                  <div style={{
                    background: "var(--bg-card)", border: "1px solid var(--border-subtle)",
                    borderRadius: 10, padding: "8px 10px", fontSize: 12,
                  }}>
                    <p style={{ fontWeight: 600, color: "var(--text-primary)", marginBottom: 4 }}>{p.name}</p>
                    <p style={{ color: "var(--text-secondary)" }}>Rev CAGR 3Y: {p.x.toFixed(1)}%</p>
                    <p style={{ color: "var(--text-secondary)" }}>{Y_OPTIONS.find((o) => o.key === yKey)!.label}: {p.y.toFixed(1)}</p>
                    <p style={{ color: "var(--text-dim)" }}>Mkt Cap: ₹{p.z.toFixed(1)}B</p>
                  </div>
                );
              }}
            />
            <Scatter data={peerPoints} fill="#c9a227" fillOpacity={0.55} isAnimationActive={false}>
              {peerPoints.map((_, i) => <Cell key={i} fill="#c9a227" fillOpacity={0.55} />)}
            </Scatter>
            {hasSubject && (
              <Scatter data={[subjectPoint]} fill="#e0793c" shape="star" isAnimationActive={false}>
                <Cell fill="#e0793c" />
              </Scatter>
            )}
            <Customized component={PeerLabelsOverlay} />
          </ScatterChart>
        </ResponsiveContainer>
      )}
      <p className="text-[11px] mt-1" style={{ color: "var(--text-dim)" }}>
        Bubble size = market cap · <span style={{ color: "#e0793c" }}>★</span> = subject company
      </p>
    </div>
  );
}
