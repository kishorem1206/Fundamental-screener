import { useState } from "react";
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import { axisTick, gridStroke, chartTooltipStyle, ChartEmptyState } from "./ChartCard";
import type { PricePoint } from "../../types";

function fmtDate(d: string, window: "1y" | "5y") {
  const dt = new Date(d);
  if (Number.isNaN(dt.getTime())) return d;
  return window === "1y"
    ? dt.toLocaleDateString("en-IN", { month: "short", day: "2-digit" })
    : dt.toLocaleDateString("en-IN", { month: "short", year: "2-digit" });
}

export default function PriceHistoryChart({ oneYear, fiveYear }: { oneYear: PricePoint[]; fiveYear: PricePoint[] }) {
  const [window, setWindow] = useState<"1y" | "5y">("1y");
  const points = window === "1y" ? oneYear : fiveYear;

  if (oneYear.length < 2 && fiveYear.length < 2) return null;

  const rows = points.map((p) => ({ date: fmtDate(p.date, window), close: p.close }));
  const changePct = points.length >= 2 ? ((points[points.length - 1].close - points[0].close) / points[0].close) * 100 : null;

  return (
    <div className="card-rich p-5">
      <div className="flex items-center justify-between mb-3">
        <div>
          <p className="eyebrow">Price History</p>
          {changePct !== null && (
            <p className="text-xs mt-0.5" style={{ color: changePct >= 0 ? "#4fb3a0" : "#d9694f" }}>
              {changePct >= 0 ? "+" : ""}{changePct.toFixed(1)}% over {window === "1y" ? "1 year" : "5 years"}
            </p>
          )}
        </div>
        <div style={{ display: "flex", gap: 6 }}>
          {(["1y", "5y"] as const).map((w) => (
            <button key={w} onClick={() => setWindow(w)}
              disabled={(w === "1y" ? oneYear : fiveYear).length < 2}
              style={{
                padding: "4px 12px", borderRadius: 6, fontSize: 12, fontWeight: 600,
                border: "1px solid",
                borderColor: window === w ? "var(--accent)" : "var(--border-subtle)",
                background: window === w ? "rgba(201,162,39,0.12)" : "transparent",
                color: window === w ? "var(--accent)" : "var(--text-secondary)",
                cursor: "pointer", opacity: (w === "1y" ? oneYear : fiveYear).length < 2 ? 0.4 : 1,
              }}>
              {w.toUpperCase()}
            </button>
          ))}
        </div>
      </div>
      {points.length < 2 ? (
        <ChartEmptyState message="No price history available" />
      ) : (
        <ResponsiveContainer width="100%" height={240}>
          <AreaChart data={rows} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="priceFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#c9a227" stopOpacity={0.25} />
                <stop offset="100%" stopColor="#c9a227" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} vertical={false} />
            <XAxis dataKey="date" tick={axisTick} axisLine={false} tickLine={false} minTickGap={40} />
            <YAxis tick={axisTick} axisLine={false} tickLine={false} width={52} domain={["auto", "auto"]} tickFormatter={(v) => `₹${v}`} />
            <Tooltip {...chartTooltipStyle} formatter={(v: number) => [`₹${v.toFixed(2)}`, "Close"]} />
            <Area type="monotone" dataKey="close" stroke="#c9a227" strokeWidth={2} fill="url(#priceFill)" isAnimationActive={false} />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
