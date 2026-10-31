// Weekly candles with the stage periods behind them, on one time axis over three
// panes: price, volume, relative strength. Hand-drawn SVG: recharts has no candle
// mark, and the stage bands and markers need the same x scale.
import { useEffect, useMemo, useRef, useState } from "react";
import { STAGE_COLOR } from "./StageScreener";

export interface StageWeek { week: string; open: number; high: number; low: number; close: number; volume: number; sma30: number | null; sma10: number | null; rs: number | null;
  stage: number | null; sub_stage: string | null; confidence: number | null; event: string | null; provisional: boolean }

const UP = "#17805c", DOWN = "#a8342c", INK = "#55554f", GRID = "#eeeeea";
const PRICE_H = 340, VOLUME_H = 70, RS_H = 110, GAP = 18, AXIS = 22, RIGHT = 58, LEFT = 6;
const WINDOWS = [{ label: "1Y", weeks: 52 }, { label: "2Y", weeks: 104 }, { label: "All", weeks: 0 }];

function ticks(low: number, high: number, n: number) {
  const step = (high - low) / n, mag = 10 ** Math.floor(Math.log10(step)), s = [1, 2, 2.5, 5, 10].find((m) => m * mag >= step)! * mag;
  const out = [];
  for (let v = Math.ceil(low / s) * s; v <= high; v += s) out.push(v);
  return out;
}

function path(points: (number | null)[], x: (i: number) => number, y: (v: number) => number) {
  let d = "", open = false;
  points.forEach((p, i) => {
    if (p === null) { open = false; return; }
    d += `${open ? "L" : "M"}${x(i).toFixed(1)} ${y(p).toFixed(1)}`;
    open = true;
  });
  return d;
}

export default function StageChart({ weeks, resistance, support }: { weeks: StageWeek[]; resistance: number | null; support: number | null }) {
  const box = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(900);
  const [span, setSpan] = useState(0);
  const [hover, setHover] = useState<number | null>(null);
  useEffect(() => {
    if (!box.current) return;
    const watch = new ResizeObserver(([e]) => setWidth(e.contentRect.width));
    watch.observe(box.current);
    return () => watch.disconnect();
  }, []);

  const rows = useMemo(() => (span ? weeks.slice(-span) : weeks), [weeks, span]);
  const plot = Math.max(width - LEFT - RIGHT, 200);
  const slot = plot / rows.length, body = Math.max(Math.min(slot * 0.62, 9), 1.5);
  const x = (i: number) => LEFT + slot * (i + 0.5);
  const lows = rows.map((r) => r.low), highs = rows.map((r) => r.high);
  const levels = [resistance, support].filter((v): v is number => v !== null);
  const low = Math.min(...lows, ...levels) * 0.97, high = Math.max(...highs, ...levels) * 1.03;
  const top = 16;
  const y = (v: number) => top + (1 - (v - low) / (high - low)) * (PRICE_H - top);
  const volumeTop = PRICE_H + GAP, maxVolume = Math.max(...rows.map((r) => r.volume), 1);
  const rsTop = volumeTop + VOLUME_H + GAP;
  const rsValues = rows.flatMap((r) => (r.rs === null ? [] : [r.rs]));
  const rsMax = Math.max(...rsValues.map(Math.abs), 5) * 1.1;
  const yRs = (v: number) => rsTop + (1 - (v + rsMax) / (2 * rsMax)) * RS_H;
  const height = rsTop + RS_H + AXIS;

  const bands: { stage: number; from: number; to: number }[] = [];
  rows.forEach((r, i) => {
    if (r.stage === null) return;
    const last = bands[bands.length - 1];
    if (last && last.stage === r.stage && last.to === i - 1) last.to = i;
    else bands.push({ stage: r.stage, from: i, to: i });
  });
  const months: { i: number; label: string }[] = [];
  rows.forEach((r, i) => {
    const d = new Date(r.week), prev = i ? new Date(rows[i - 1].week) : null;
    if (prev && d.getMonth() !== prev.getMonth() && d.getMonth() % (rows.length > 80 ? 6 : 3) === 0) months.push({ i, label: d.toLocaleDateString("en-IN", { month: "short", year: "2-digit" }) });
  });
  const h = hover !== null ? rows[hover] : null;
  const move = (clientX: number) => {
    const rect = box.current!.getBoundingClientRect();
    setHover(Math.min(rows.length - 1, Math.max(0, Math.floor((clientX - rect.left - LEFT) / slot))));
  };

  return (
    <div>
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mb-2 text-[11px]" style={{ color: INK }}>
        {[1, 2, 3, 4].map((s) => <span key={s} className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm" style={{ background: STAGE_COLOR[s] }} />Stage {s}</span>)}
        <span className="flex items-center gap-1"><span className="w-4 h-0.5" style={{ background: "#1f1f1c" }} />30-week</span>
        <span className="flex items-center gap-1"><span className="w-4 h-0.5" style={{ background: "#3b78c9" }} />10-week</span>
        <span>▲ breakout · ▲ dark on volume · ▼ breakdown</span>
        <span className="flex-1" />
        {WINDOWS.map((w) => <button key={w.label} className="stage-pill" style={{ padding: "2px 10px" }} aria-pressed={span === w.weeks} onClick={() => { setSpan(w.weeks); setHover(null); }}>{w.label}</button>)}
      </div>
      <div ref={box} className="relative" style={{ touchAction: "pan-y" }} onPointerMove={(e) => move(e.clientX)} onPointerLeave={() => setHover(null)}>
        <svg width={width} height={height} role="img" aria-label="Weekly price with stage periods, volume and relative strength">
          {bands.map((b, i) => {
            const bx = LEFT + slot * b.from, w = slot * (b.to - b.from + 1);
            return (
              <g key={i}>
                <rect x={bx} y={top} width={w} height={PRICE_H - top} fill={STAGE_COLOR[b.stage]} opacity={0.09} />
                <rect x={bx + 1} y={0} width={Math.max(w - 2, 1)} height={7} fill={STAGE_COLOR[b.stage]} rx={2} />
                {w > 22 && <text x={bx + w / 2} y={top + 3} textAnchor="middle" fontSize={10} fill={INK} dominantBaseline="hanging">S{b.stage}</text>}
              </g>
            );
          })}
          {ticks(low, high, 5).map((v) => (
            <g key={v}><line x1={LEFT} x2={LEFT + plot} y1={y(v)} y2={y(v)} stroke={GRID} /><text x={LEFT + plot + 6} y={y(v) + 3} fontSize={10} fill={INK}>{v.toLocaleString("en-IN")}</text></g>
          ))}
          {resistance !== null && <g><line x1={LEFT} x2={LEFT + plot} y1={y(resistance)} y2={y(resistance)} stroke={DOWN} strokeDasharray="4 4" /><text x={LEFT + 4} y={y(resistance) - 4} fontSize={10} fill={INK}>Resistance {resistance.toLocaleString("en-IN")}</text></g>}
          {support !== null && <g><line x1={LEFT} x2={LEFT + plot} y1={y(support)} y2={y(support)} stroke={UP} strokeDasharray="4 4" /><text x={LEFT + 4} y={y(support) + 12} fontSize={10} fill={INK}>Support {support.toLocaleString("en-IN")}</text></g>}
          {rows.map((r, i) => {
            const up = r.close >= r.open, color = up ? UP : DOWN, yo = y(r.open), yc = y(r.close);
            return (
              <g key={r.week} opacity={r.provisional ? 0.55 : 1}>
                <line x1={x(i)} x2={x(i)} y1={y(r.high)} y2={y(r.low)} stroke={color} />
                <rect x={x(i) - body / 2} y={Math.min(yo, yc)} width={body} height={Math.max(Math.abs(yc - yo), 1)} fill={color} />
                <rect x={x(i) - body / 2} y={volumeTop + VOLUME_H * (1 - r.volume / maxVolume)} width={body} height={Math.max(VOLUME_H * (r.volume / maxVolume), 1)} fill={color} opacity={0.55} />
                {r.event === "breakdown" && <text x={x(i)} y={y(r.high) - 5} textAnchor="middle" fontSize={11} fill={DOWN}>▼</text>}
                {r.event?.startsWith("breakout") && <text x={x(i)} y={y(r.low) + 13} textAnchor="middle" fontSize={11} fill={r.event === "breakout_volume" ? "#1f1f1c" : "#9a9a92"}>▲</text>}
              </g>
            );
          })}
          <path d={path(rows.map((r) => r.sma30), x, y)} fill="none" stroke="#1f1f1c" strokeWidth={2} />
          <path d={path(rows.map((r) => r.sma10), x, y)} fill="none" stroke="#3b78c9" strokeWidth={1.5} />
          <text x={LEFT} y={volumeTop - 5} fontSize={10} fill={INK}>Volume</text>
          <text x={LEFT} y={rsTop - 5} fontSize={10} fill={INK}>Relative strength against the Nifty 500 (0 = its own 52-week average)</text>
          <line x1={LEFT} x2={LEFT + plot} y1={yRs(0)} y2={yRs(0)} stroke="#b9b8b1" />
          <text x={LEFT + plot + 6} y={yRs(0) + 3} fontSize={10} fill={INK}>0</text>
          <text x={LEFT + plot + 6} y={yRs(rsMax * 0.8) + 3} fontSize={10} fill={INK}>+{(rsMax * 0.8).toFixed(0)}</text>
          <text x={LEFT + plot + 6} y={yRs(-rsMax * 0.8) + 3} fontSize={10} fill={INK}>−{(rsMax * 0.8).toFixed(0)}</text>
          <path d={path(rows.map((r) => r.rs), x, yRs)} fill="none" stroke="#3b78c9" strokeWidth={2} />
          {months.map((m) => <text key={m.i} x={x(m.i)} y={height - 6} textAnchor="middle" fontSize={10} fill={INK}>{m.label}</text>)}
          {hover !== null && <line x1={x(hover)} x2={x(hover)} y1={0} y2={height - AXIS} stroke="#1f1f1c" strokeDasharray="2 3" />}
        </svg>
        {h && (
          <div className="absolute top-3 text-[11px] rounded-lg px-3 py-2 pointer-events-none tabular-nums"
               style={{ [x(hover!) > width / 2 ? "left" : "right"]: RIGHT + 8, background: "#ffffff", border: "1px solid #e6e5e0", boxShadow: "0 4px 14px rgba(0,0,0,0.08)", color: "#1f1f1c" } as React.CSSProperties}>
            <div className="font-semibold mb-0.5">Week to {h.week}{h.provisional ? " (open)" : ""}</div>
            <div>{h.stage ? `Stage ${h.stage}${h.sub_stage ? ` · ${h.sub_stage}` : ""}, confidence ${h.confidence?.toFixed(0) ?? "—"}` : "Unclassified"}</div>
            <div>O {h.open} · H {h.high} · L {h.low} · C {h.close}</div>
            <div>30W {h.sma30 ?? "—"} · 10W {h.sma10 ?? "—"} · RS {h.rs ?? "—"}</div>
            <div>Volume {h.volume.toLocaleString("en-IN")}</div>
            {h.event && <div>{h.event === "breakdown" ? "Breakdown" : h.event === "breakout_volume" ? "Breakout on volume" : "Breakout"}</div>}
          </div>
        )}
      </div>
    </div>
  );
}
