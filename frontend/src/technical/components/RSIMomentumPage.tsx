import { useState, useCallback, useEffect } from "react";
import type { RSIMomentumResult, RSIMomentumSignal, RSIMomentumStock, MarketCapCategory, StockMatch } from "../types";
import { scanRSIMomentum, runScreenWithRSIMomentum } from "../api";

// ─── localStorage persistence ─────────────────────────────────────────────────

const MOM_LS_KEY = "rsi_momentum_page_settings_v1";

interface MomSettings {
  universe: string; lookback: number; rsiLow: number; rsiHigh: number;
  threshold: number; freshnessFilter: string; selectedSignals: string[];
  bbOn: boolean; bbMode: string; bbTf: string;
  macdOn: boolean; macdMode: string; macdTf: string;
  volOn: boolean; volRatio: number; volTf: string;
  requireRsiRising: boolean;
}

const MOM_DEFAULTS: MomSettings = {
  universe: "NIFTY_500", lookback: 20, rsiLow: 0, rsiHigh: 100, threshold: 60,
  freshnessFilter: "any", selectedSignals: ["FRESH_BREAKOUT", "APPROACHING"],
  bbOn: false, bbMode: "near_upper", bbTf: "1D",
  macdOn: false, macdMode: "bullish", macdTf: "1D",
  volOn: false, volRatio: 100, volTf: "1D",
  requireRsiRising: false,
};

function loadMomSettings(): MomSettings {
  try {
    const raw = localStorage.getItem(MOM_LS_KEY);
    if (raw) return { ...MOM_DEFAULTS, ...JSON.parse(raw) as Partial<MomSettings> };
  } catch { /* ignore */ }
  return { ...MOM_DEFAULTS };
}

function saveMomSettings(s: MomSettings) {
  try { localStorage.setItem(MOM_LS_KEY, JSON.stringify(s)); } catch { /* ignore */ }
}

// ─── Constants ────────────────────────────────────────────────────────────────

const UNIVERSES = [
  { id: "NIFTY_50",           label: "Nifty 50",    count: 50 },
  { id: "NIFTY_500",          label: "Nifty 500",   count: 500 },
  { id: "NIFTY_TOTAL_MARKET", label: "Total Market", count: "750+" },
];

const SIGNAL_CONFIG: Record<RSIMomentumSignal, { label: string; dot: string; badge: string; desc: string }> = {
  FRESH_BREAKOUT: {
    label: "Fresh Breakout", dot: "bg-green-400",
    badge: "bg-green-900/60 text-green-300 border border-green-700",
    desc: "RSI just crossed above threshold for first time in the lookback window",
  },
  APPROACHING_AGAIN: {
    label: "Approaching Again", dot: "bg-cyan-400",
    badge: "bg-cyan-900/60 text-cyan-300 border border-cyan-700",
    desc: "Was above threshold in lookback, pulled back — second-chance entry",
  },
  APPROACHING: {
    label: "Approaching", dot: "bg-blue-400",
    badge: "bg-blue-900/60 text-blue-300 border border-blue-700",
    desc: "RSI within 5 pts below threshold, rising, no prior crossing",
  },
  ALREADY_STRONG: {
    label: "Already Strong", dot: "bg-yellow-400",
    badge: "bg-yellow-900/60 text-yellow-300 border border-yellow-700",
    desc: "RSI above threshold — momentum already playing out",
  },
  EXTENDED: {
    label: "Extended", dot: "bg-red-400",
    badge: "bg-red-900/60 text-red-300 border border-red-700",
    desc: "RSI ≥ 70 — extended, risk of reversal",
  },
  NEUTRAL: {
    label: "Neutral", dot: "bg-gray-500",
    badge: "bg-gray-800 text-gray-400 border border-gray-700",
    desc: "RSI below approaching zone or falling",
  },
};

const ALL_SIGNALS: RSIMomentumSignal[] = [
  "FRESH_BREAKOUT", "APPROACHING_AGAIN", "APPROACHING", "ALREADY_STRONG", "EXTENDED", "NEUTRAL",
];

const SIGNAL_RANK_MAP: Record<RSIMomentumSignal, number> = {
  FRESH_BREAKOUT: 5.0, APPROACHING_AGAIN: 4.5, APPROACHING: 4.0,
  ALREADY_STRONG: 3.0, EXTENDED: 2.0, NEUTRAL: 1.0,
};

const MCAP_BADGE: Record<MarketCapCategory, string> = {
  LARGE_CAP:  "bg-blue-900/50 text-blue-300 border border-blue-800",
  MID_CAP:    "bg-purple-900/50 text-purple-300 border border-purple-800",
  SMALL_CAP:  "bg-yellow-900/50 text-yellow-300 border border-yellow-800",
  MICRO_CAP:  "bg-gray-800 text-gray-400 border border-gray-700",
};

const MCAP_LABEL: Record<MarketCapCategory, string> = {
  LARGE_CAP: "Large", MID_CAP: "Mid", SMALL_CAP: "Small", MICRO_CAP: "Micro",
};

const TF_OPTIONS = ["1H", "4H", "1D", "1W", "1M"] as const;

const BB_MODES = {
  near_upper:  { label: "Near Upper  (≥0.88)", op: "gte", value: 0.88 },
  touch_upper: { label: "Touch Upper (≥0.95)", op: "gte", value: 0.95 },
  above_upper: { label: "Above Upper (>1.0)",  op: "gt",  value: 1.0  },
  near_lower:  { label: "Near Lower  (≤0.15)", op: "lte", value: 0.15 },
  at_lower:    { label: "At/Below Lower (≤0)", op: "lte", value: 0.0  },
} as const;

const MACD_MODES = {
  bullish:    { label: "Bullish   (Hist > 0)",  field: "histogram",         op: "gt", value: 0   },
  bearish:    { label: "Bearish   (Hist < 0)",  field: "histogram",         op: "lt", value: 0   },
  cross_bull: { label: "Bull Crossover",         field: "bullish_crossover", op: "eq", value: 1.0 },
  cross_bear: { label: "Bear Crossover",         field: "bearish_crossover", op: "eq", value: 1.0 },
} as const;

// ─── Types ────────────────────────────────────────────────────────────────────

type FreshnessFilter = "any" | "fresh" | "was_above";
type BBMode   = keyof typeof BB_MODES;
type MacdMode = keyof typeof MACD_MODES;

type ExtraData = {
  bb_pct_b?:   number | null;
  macd_hist?:  number | null;
  macd_sig?:   string;
  vol_ratio?:  number | null;
};

// ─── Small reusable components ────────────────────────────────────────────────

function TimeframeSelect({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <select
      value={value}
      onChange={e => onChange(e.target.value)}
      className="text-[10px] bg-gray-900 border border-gray-700 rounded px-1 py-0.5 text-gray-400 focus:outline-none"
    >
      {TF_OPTIONS.map(tf => <option key={tf} value={tf}>{tf}</option>)}
    </select>
  );
}

function CheckToggle({ label, checked, onChange, color = "#93BBFF" }: {
  label: string; checked: boolean; onChange: (v: boolean) => void; color?: string;
}) {
  return (
    <button
      onClick={() => onChange(!checked)}
      className="w-full flex items-center gap-2 text-xs text-left py-1"
    >
      <span
        className="w-3.5 h-3.5 rounded border flex items-center justify-center text-[8px] shrink-0"
        style={{
          background:  checked ? "rgba(59,130,246,0.25)" : "transparent",
          borderColor: checked ? "#3B82F6" : "#374151",
          color: "#93BBFF",
        }}
      >{checked ? "✓" : ""}</span>
      <span style={{ color: checked ? color : "#6B7280" }} className="font-medium">{label}</span>
    </button>
  );
}

function FilterOpt<T extends string>({
  value, current, onChange, label,
}: { value: T; current: T; onChange: (v: T) => void; label: string }) {
  const active = value === current;
  return (
    <button
      onClick={() => onChange(value)}
      className="w-full flex items-center gap-1.5 text-left text-[11px] py-0.5 px-1 rounded"
      style={{ color: active ? "#93BBFF" : "#4B5563" }}
    >
      <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${active ? "bg-blue-400" : "bg-gray-700"}`} />
      {label}
    </button>
  );
}

function ExtraFilterBlock({
  label, enabled, onToggle, tf, onTf, children,
}: {
  label: string; enabled: boolean; onToggle: () => void;
  tf: string; onTf: (v: string) => void; children: React.ReactNode;
}) {
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <button
          onClick={onToggle}
          className="flex items-center gap-2 text-xs py-0.5"
        >
          <span
            className={`w-3 h-3 rounded border flex items-center justify-center text-[8px]`}
            style={{
              background: enabled ? "rgba(59,130,246,0.25)" : "transparent",
              borderColor: enabled ? "#3B82F6" : "#374151",
              color: "#93BBFF",
            }}
          >
            {enabled ? "✓" : ""}
          </span>
          <span style={{ color: enabled ? "#E2E8F0" : "#6B7280" }} className="font-medium">{label}</span>
        </button>
        <TimeframeSelect value={tf} onChange={onTf} />
      </div>
      {enabled && (
        <div className="ml-5 space-y-0">
          {children}
        </div>
      )}
    </div>
  );
}

// ─── Dual-handle RSI range slider ────────────────────────────────────────────

function DualRangeSlider({ low, high, min, max, onChange }: {
  low: number; high: number; min: number; max: number;
  onChange: (low: number, high: number) => void;
}) {
  const lowPct  = ((low  - min) / (max - min)) * 100;
  const highPct = ((high - min) / (max - min)) * 100;
  const highZ = highPct - lowPct < 8 ? 5 : 2;

  return (
    <div>
      <div className="flex items-baseline justify-between mb-3">
        <label className="text-xs font-semibold uppercase tracking-widest text-gray-500">RSI Display Filter</label>
        <span className="text-sm font-bold tabular-nums leading-none" style={{ color: "#93BBFF" }}>{low} – {high}</span>
      </div>
      <div style={{ position: "relative", height: "20px", display: "flex", alignItems: "center" }}>
        <div style={{ position: "absolute", left: 0, right: 0, height: "3px", background: "rgba(255,255,255,0.09)", borderRadius: "2px" }} />
        <div style={{ position: "absolute", left: `${lowPct}%`, right: `${100 - highPct}%`, height: "3px", background: "var(--accent-blue)", borderRadius: "2px" }} />
        <input type="range" min={min} max={max} step={1} value={low}
          onChange={e => onChange(Math.min(Number(e.target.value), high - 1), high)}
          className="dual-range" style={{ zIndex: 2 }} />
        <input type="range" min={min} max={max} step={1} value={high}
          onChange={e => onChange(low, Math.max(Number(e.target.value), low + 1))}
          className="dual-range" style={{ zIndex: highZ }} />
      </div>
      <div className="flex justify-between mt-2">
        {[0, 25, 50, 75, 100].map(n => (
          <span key={n} className="text-[10px] tabular-nums" style={{ color: "#2D3748" }}>{n}</span>
        ))}
      </div>
    </div>
  );
}

function RangeSlider({ label, value, min, max, step, unit = "", onChange, hint }: {
  label: string; value: number; min: number; max: number; step: number;
  unit?: string; onChange: (v: number) => void; hint?: string;
}) {
  const pct = `${((value - min) / (max - min)) * 100}%`;
  const scaleLabels = Array.from({ length: 6 }, (_, i) => Math.round(min + (i / 5) * (max - min)));
  return (
    <div>
      <div className="flex items-baseline justify-between mb-3">
        <label className="text-xs font-semibold uppercase tracking-widest text-gray-500">{label}</label>
        <span className="text-xl font-bold tabular-nums leading-none" style={{ color: "#93BBFF" }}>{value}{unit}</span>
      </div>
      <input type="range" min={min} max={max} step={step} value={value}
        onChange={e => onChange(Number(e.target.value))}
        className="range-slider" style={{ "--pct": pct } as React.CSSProperties} />
      <div className="flex justify-between mt-1.5">
        {scaleLabels.map(n => (
          <span key={n} className="text-[10px] tabular-nums" style={{ color: "#2D3748" }}>{n}</span>
        ))}
      </div>
      {hint && <p className="text-xs mt-2" style={{ color: "#1E293B" }}>{hint}</p>}
    </div>
  );
}

function FreshnessToggle({ value, onChange, threshold, lookback }: {
  value: FreshnessFilter; onChange: (v: FreshnessFilter) => void;
  threshold: number; lookback: number;
}) {
  const opts: { id: FreshnessFilter; label: string; desc: string; color: string }[] = [
    { id: "any",       label: "Either",     desc: "No filter on prior crossings", color: "#94A3B8" },
    { id: "fresh",     label: "Fresh only", desc: `RSI NOT above ${threshold} in last ${lookback}d`, color: "#4ade80" },
    { id: "was_above", label: "Was above",  desc: `RSI WAS above ${threshold} within ${lookback}d`, color: "#facc15" },
  ];
  return (
    <div>
      <label className="block text-xs font-semibold uppercase tracking-widest text-gray-500 mb-2">Prior Crossings</label>
      <div className="space-y-1">
        {opts.map(({ id, label, desc, color }) => {
          const active = value === id;
          return (
            <button key={id} onClick={() => onChange(id)}
              className="w-full text-left px-3 py-2 rounded-lg text-xs transition-colors border"
              style={{ background: active ? "rgba(79,124,255,0.1)" : "transparent", borderColor: active ? "rgba(79,124,255,0.35)" : "transparent" }}>
              <div className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: active ? color : "#374151" }} />
                <span style={{ color: active ? "#E2E8F0" : "#6B7280" }} className="font-medium">{label}</span>
              </div>
              <p className="mt-0.5 ml-3.5 text-[10px]" style={{ color: active ? "#4B5680" : "#374151" }}>{desc}</p>
            </button>
          );
        })}
      </div>
    </div>
  );
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function fmt(n: number | null, decimals = 1): string {
  if (n === null) return "—";
  return n.toFixed(decimals);
}

function rsiColor(v: number): string {
  if (v >= 70) return "text-red-400 font-semibold";
  if (v >= 60) return "text-orange-300";
  if (v >= 55) return "text-blue-300";
  return "text-gray-400";
}

function changeColor(v: number): string {
  if (v > 0) return "text-green-400";
  if (v < 0) return "text-red-400";
  return "text-gray-500";
}

function trendIcon(t: string): string { return t === "RISING" ? "↑" : t === "FALLING" ? "↓" : "→"; }
function trendColor(t: string): string { return t === "RISING" ? "text-green-400" : t === "FALLING" ? "text-red-400" : "text-gray-500"; }
function daysSinceLabel(n: number | null): string { return n === null ? "Never" : `${n}d ago`; }

function bbColor(pctB: number): string {
  if (pctB >= 0.95) return "#FB923C"; // orange — at/above upper
  if (pctB >= 0.88) return "#FCD34D"; // yellow — near upper
  if (pctB > 0.5)   return "#93BBFF"; // blue — above middle
  if (pctB < 0.15)  return "#F87171"; // red — near lower
  return "#6B7280";
}

function macdColor(hist: number): string {
  if (hist > 0) return "text-green-400";
  if (hist < 0) return "text-red-400";
  return "text-gray-500";
}

// Map screens response → RSIMomentumStock[]
function rsiTrendStr(v: unknown): "RISING" | "FLAT" | "FALLING" {
  const n = Number(v);
  if (n === 1.0) return "RISING";
  if (n === -1.0) return "FALLING";
  return "FLAT";
}

function mapScreensToMomentum(stocks: StockMatch[]): RSIMomentumStock[] {
  return stocks.flatMap(s => {
    const rm = s.indicators["rsi_momentum_1D"] ?? {};
    if (rm.rsi_today === undefined) return [];
    return [{
      id: s.id,
      symbol: s.symbol,
      exchange: s.exchange,
      company_name: s.company_name,
      sector: s.sector,
      macro_sector: s.macro_sector,
      market_cap_category: s.market_cap_category,
      rsi_today:          Number(rm.rsi_today ?? 0),
      rsi_prev:           Number(rm.rsi_prev ?? 0),
      rsi_change:         Number(rm.rsi_change ?? 0),
      distance_to_60:     Number(rm.distance_to_60 ?? 0),
      rsi_trend:          rsiTrendStr(rm.rsi_trend),
      above_60_in_20d:    Boolean(rm.above_60_in_20d),
      days_since_above_60: rm.days_since_above_60 != null ? Number(rm.days_since_above_60) : null,
      signal:             ((rm.signal as unknown) as RSIMomentumSignal) ?? "NEUTRAL",
      signal_rank:        Number(rm.signal_rank ?? 1.0),
    }];
  });
}

function extractExtras(
  stocks: StockMatch[],
  bbTf: string | null,
  macdTf: string | null,
  volTf: string | null,
): Record<string, ExtraData> {
  const out: Record<string, ExtraData> = {};
  for (const s of stocks) {
    const entry: ExtraData = {};
    if (bbTf) {
      const bb = s.indicators[`bollinger_${bbTf.toUpperCase()}`] ?? {};
      entry.bb_pct_b = bb.percent_b != null ? Number(bb.percent_b) : null;
    }
    if (macdTf) {
      const macd = s.indicators[`macd_${macdTf.toUpperCase()}`] ?? {};
      entry.macd_hist = macd.histogram != null ? Number(macd.histogram) : null;
      entry.macd_sig  = String(macd.signal ?? "");
    }
    if (volTf) {
      const vol = s.indicators[`volume_strength_${volTf.toUpperCase()}`] ?? {};
      entry.vol_ratio = vol.volume_ratio != null ? Number(vol.volume_ratio) : null;
    }
    out[s.id] = entry;
  }
  return out;
}

// ─── Table ────────────────────────────────────────────────────────────────────

type SortCol =
  | "symbol" | "company_name" | "market_cap_category" | "signal_rank"
  | "rsi_today" | "rsi_prev" | "rsi_change" | "distance_to_60"
  | "rsi_trend" | "above_60_in_20d" | "days_since_above_60"
  | "bb_pct_b" | "macd_hist" | "vol_ratio";

const MCAP_ORDER: Record<string, number> = { LARGE_CAP: 4, MID_CAP: 3, SMALL_CAP: 2, MICRO_CAP: 1 };
const TREND_ORDER: Record<string, number> = { RISING: 3, FLAT: 2, FALLING: 1 };

function RSIMomentumTable({
  stocks, threshold, lookback,
  extras, showBB, showMACD, showVol,
}: {
  stocks: RSIMomentumStock[];
  threshold: number;
  lookback: number;
  extras: Record<string, ExtraData> | null;
  showBB: boolean;
  showMACD: boolean;
  showVol: boolean;
}) {
  const [sortCol, setSortCol] = useState<SortCol>("signal_rank");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  function toggleSort(col: SortCol) {
    if (sortCol === col) {
      setSortDir(d => d === "asc" ? "desc" : "asc");
    } else {
      setSortCol(col);
      setSortDir(["signal_rank","rsi_today","rsi_prev","above_60_in_20d","market_cap_category"].includes(col) ? "desc" : "asc");
    }
  }

  const sorted = [...stocks].sort((a, b) => {
    let av: number, bv: number;
    switch (sortCol) {
      case "symbol":       return sortDir === "asc" ? a.symbol.localeCompare(b.symbol) : b.symbol.localeCompare(a.symbol);
      case "company_name": return sortDir === "asc" ? a.company_name.localeCompare(b.company_name) : b.company_name.localeCompare(a.company_name);
      case "market_cap_category": av = MCAP_ORDER[a.market_cap_category] ?? 0; bv = MCAP_ORDER[b.market_cap_category] ?? 0; break;
      case "signal_rank":     av = a.signal_rank;                  bv = b.signal_rank;                  break;
      case "rsi_today":       av = a.rsi_today;                    bv = b.rsi_today;                    break;
      case "rsi_prev":        av = a.rsi_prev;                     bv = b.rsi_prev;                     break;
      case "rsi_change":      av = a.rsi_change;                   bv = b.rsi_change;                   break;
      case "distance_to_60":  av = a.distance_to_60;               bv = b.distance_to_60;               break;
      case "rsi_trend":       av = TREND_ORDER[a.rsi_trend] ?? 0; bv = TREND_ORDER[b.rsi_trend] ?? 0; break;
      case "above_60_in_20d": av = a.above_60_in_20d ? 1 : 0;     bv = b.above_60_in_20d ? 1 : 0;     break;
      case "days_since_above_60": av = a.days_since_above_60 ?? 9999; bv = b.days_since_above_60 ?? 9999; break;
      case "bb_pct_b":    av = extras?.[a.id]?.bb_pct_b   ?? -999; bv = extras?.[b.id]?.bb_pct_b   ?? -999; break;
      case "macd_hist":   av = extras?.[a.id]?.macd_hist  ?? -999; bv = extras?.[b.id]?.macd_hist  ?? -999; break;
      case "vol_ratio":   av = extras?.[a.id]?.vol_ratio  ?? -999; bv = extras?.[b.id]?.vol_ratio  ?? -999; break;
      default: return 0;
    }
    return sortDir === "asc" ? av - bv : bv - av;
  });

  const SortIcon = ({ col }: { col: SortCol }) =>
    sortCol !== col ? <span className="opacity-20">↕</span>
      : sortDir === "asc" ? <span className="text-blue-400">↑</span>
      : <span className="text-blue-400">↓</span>;

  const mkTh = (align: "left"|"right"|"center", label: string, col: SortCol) => (
    <th
      className={`text-${align} py-1.5 px-2 text-[11px] font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-300 select-none whitespace-nowrap`}
      onClick={() => toggleSort(col)}
    >
      {label} <SortIcon col={col} />
    </th>
  );

  return (
    <div
      className="overflow-x-auto rounded-lg border border-gray-800 [&::-webkit-scrollbar]:h-1.5 [&::-webkit-scrollbar-track]:bg-gray-900 [&::-webkit-scrollbar-thumb]:bg-gray-700 [&::-webkit-scrollbar-thumb]:rounded-full"
      style={{ scrollbarWidth: "thin", scrollbarColor: "#374151 #111827" }}
    >
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-gray-800 bg-gray-900/60">
            <th className="text-left py-1.5 px-2 text-[11px] font-medium text-gray-500 uppercase tracking-wider w-6">#</th>
            {mkTh("left",   "Symbol",           "symbol")}
            {mkTh("left",   "Company",          "company_name")}
            {mkTh("left",   "Cap",              "market_cap_category")}
            {mkTh("left",   "Signal",           "signal_rank")}
            {mkTh("right",  "RSI",              "rsi_today")}
            {mkTh("right",  "Prev",             "rsi_prev")}
            {mkTh("right",  "Chg",              "rsi_change")}
            {mkTh("right",  `Dist ${threshold}`,"distance_to_60")}
            {mkTh("center", "Trend",            "rsi_trend")}
            {mkTh("center", `>${threshold}/${lookback}D`, "above_60_in_20d")}
            {mkTh("right",  "Days Since",       "days_since_above_60")}
            {showBB   && mkTh("right", "BB %B", "bb_pct_b")}
            {showMACD && mkTh("right", "MACD",  "macd_hist")}
            {showVol  && mkTh("right", "Vol%",  "vol_ratio")}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-800/50">
          {sorted.length === 0 && (
            <tr>
              <td colSpan={13 + (showBB ? 1 : 0) + (showMACD ? 1 : 0) + (showVol ? 1 : 0)}
                className="py-10 text-center text-gray-600 text-sm">
                No stocks matched the selected filters
              </td>
            </tr>
          )}
          {sorted.map((s, i) => {
            const cfg = SIGNAL_CONFIG[s.signal];
            const ex  = extras?.[s.id];
            return (
              <tr key={s.id} className="hover:bg-gray-800/30 transition-colors">
                <td className="py-1.5 px-2 text-gray-600 tabular-nums">{i + 1}</td>
                <td className="py-1.5 px-2">
                  <span className="font-mono font-semibold text-gray-100 tracking-wide">{s.symbol}</span>
                </td>
                <td className="py-1.5 px-2 text-gray-400 max-w-28 truncate" title={s.company_name}>{s.company_name}</td>
                <td className="py-1.5 px-2">
                  <span className={`inline-flex items-center rounded px-1 py-0.5 ${MCAP_BADGE[s.market_cap_category] ?? "bg-gray-800 text-gray-400"}`}>
                    {MCAP_LABEL[s.market_cap_category] ?? s.market_cap_category}
                  </span>
                </td>
                <td className="py-1.5 px-2">
                  <span className={`inline-flex items-center gap-1 rounded px-1.5 py-0.5 font-medium ${cfg.badge}`}>
                    <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${cfg.dot}`} />
                    {cfg.label}
                  </span>
                </td>
                <td className={`py-1.5 px-2 text-right tabular-nums ${rsiColor(s.rsi_today)}`}>{fmt(s.rsi_today)}</td>
                <td className="py-1.5 px-2 text-right tabular-nums text-gray-500">{fmt(s.rsi_prev)}</td>
                <td className={`py-1.5 px-2 text-right tabular-nums ${changeColor(s.rsi_change)}`}>
                  {s.rsi_change > 0 ? "+" : ""}{fmt(s.rsi_change)}
                </td>
                <td className={`py-1.5 px-2 text-right tabular-nums ${s.distance_to_60 < 0 ? "text-orange-400" : s.distance_to_60 < 2 ? "text-blue-300 font-semibold" : "text-gray-400"}`}>
                  {s.distance_to_60 < 0 ? "+" + fmt(Math.abs(s.distance_to_60)) : fmt(s.distance_to_60)}{s.distance_to_60 < 0 ? " ↑" : ""}
                </td>
                <td className={`py-1.5 px-2 text-center font-medium ${trendColor(s.rsi_trend)}`}>
                  <span title={s.rsi_trend}>{trendIcon(s.rsi_trend)}</span>
                </td>
                <td className="py-1.5 px-2 text-center">
                  {s.above_60_in_20d ? <span className="text-yellow-500">Yes</span> : <span className="text-green-500">No</span>}
                </td>
                <td className="py-1.5 px-2 text-right tabular-nums text-gray-500">{daysSinceLabel(s.days_since_above_60)}</td>

                {/* Extra indicator columns */}
                {showBB && (
                  <td className="py-1.5 px-2 text-right tabular-nums">
                    {ex?.bb_pct_b != null
                      ? <span style={{ color: bbColor(ex.bb_pct_b) }}>{ex.bb_pct_b.toFixed(3)}</span>
                      : <span className="text-gray-700">—</span>}
                  </td>
                )}
                {showMACD && (
                  <td className={`py-1.5 px-2 text-right tabular-nums ${ex?.macd_hist != null ? macdColor(ex.macd_hist) : "text-gray-700"}`}>
                    {ex?.macd_hist != null
                      ? `${ex.macd_hist > 0 ? "+" : ""}${ex.macd_hist.toFixed(3)}`
                      : "—"}
                  </td>
                )}
                {showVol && (
                  <td className="py-1.5 px-2 text-right tabular-nums">
                    {ex?.vol_ratio != null
                      ? <span style={{ color: ex.vol_ratio > 150 ? "#4ade80" : ex.vol_ratio > 100 ? "#93BBFF" : "#6B7280" }}>
                          {Math.round(ex.vol_ratio)}%
                        </span>
                      : <span className="text-gray-700">—</span>}
                  </td>
                )}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export function RSIMomentumPage() {
  // Core RSI Momentum filter state
  const _init = loadMomSettings();
  const [universe,        setUniverse]        = useState(_init.universe);
  const [lookback,        setLookback]        = useState(_init.lookback);
  const [rsiLow,          setRsiLow]          = useState(_init.rsiLow);
  const [rsiHigh,         setRsiHigh]         = useState(_init.rsiHigh);
  const [threshold,       setThreshold]       = useState(_init.threshold);
  const [freshnessFilter, setFreshnessFilter] = useState<FreshnessFilter>(_init.freshnessFilter as FreshnessFilter);
  const [selectedSignals, setSelectedSignals] = useState<Set<RSIMomentumSignal>>(
    new Set(_init.selectedSignals as RSIMomentumSignal[])
  );

  // Extra indicator filter state
  const [bbOn,    setBbOn]    = useState(_init.bbOn);
  const [bbMode,  setBbMode]  = useState<BBMode>(_init.bbMode as BBMode);
  const [bbTf,    setBbTf]    = useState(_init.bbTf);

  const [macdOn,   setMacdOn]   = useState(_init.macdOn);
  const [macdMode, setMacdMode] = useState<MacdMode>(_init.macdMode as MacdMode);
  const [macdTf,   setMacdTf]   = useState(_init.macdTf);

  const [volOn,    setVolOn]    = useState(_init.volOn);
  const [volRatio, setVolRatio] = useState(_init.volRatio);
  const [volTf,    setVolTf]    = useState(_init.volTf);

  // Results
  const [result,          setResult]          = useState<RSIMomentumResult | null>(null);
  const [extraIndicators, setExtraIndicators] = useState<Record<string, ExtraData> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);

  const [requireRsiRising, setRequireRsiRising] = useState(_init.requireRsiRising);

  // Persist settings on every change
  useEffect(() => {
    saveMomSettings({
      universe, lookback, rsiLow, rsiHigh, threshold,
      freshnessFilter, selectedSignals: [...selectedSignals],
      bbOn, bbMode, bbTf, macdOn, macdMode, macdTf,
      volOn, volRatio, volTf, requireRsiRising,
    });
  }, [universe, lookback, rsiLow, rsiHigh, threshold, freshnessFilter, selectedSignals,
      bbOn, bbMode, bbTf, macdOn, macdMode, macdTf, volOn, volRatio, volTf, requireRsiRising]);

  const hasExtras = bbOn || macdOn || volOn;

  function toggleSignal(sig: RSIMomentumSignal) {
    setSelectedSignals(prev => {
      const next = new Set(prev);
      if (next.has(sig)) { if (next.size > 1) next.delete(sig); }
      else next.add(sig);
      return next;
    });
  }

  function selectAll() { setSelectedSignals(new Set(ALL_SIGNALS)); }

  const handleScan = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Always use combined screen path so BB/MACD/Vol are always fetched for display
      const signalRanks = [...selectedSignals].map(s => SIGNAL_RANK_MAP[s]);
      const res = await runScreenWithRSIMomentum({
        universe,
        signalRanks,
        bbCond:     bbOn   ? { ...BB_MODES[bbMode],     tf: bbTf   } : undefined,
        macdCond:   macdOn ? { ...MACD_MODES[macdMode], tf: macdTf } : undefined,
        volCond:    volOn  ? { ratio: volRatio, tf: volTf }          : undefined,
        displayTfs: { bb: bbTf, macd: macdTf, vol: volTf },
        limit: 100,
      });

      const mappedStocks = mapScreensToMomentum(res.stocks);
      setResult({
        executed_at:       res.executed_at,
        universe:          res.universe,
        total_matched:     res.total_matched,
        stocks_screened:   res.stocks_screened,
        execution_time_ms: res.execution_time_ms,
        stocks:            mappedStocks,
      });
      setExtraIndicators(extractExtras(res.stocks, bbTf, macdTf, volTf));
    } catch (e) {
      setError((e as Error).message);
      setResult(null);
      setExtraIndicators(null);
    } finally {
      setLoading(false);
    }
  }, [universe, lookback, threshold, selectedSignals, bbOn, bbMode, bbTf, macdOn, macdMode, macdTf, volOn, volRatio, volTf]);

  // Client-side filters applied on top of scan results
  const displayedStocks = result
    ? result.stocks.filter(s => {
        if (s.rsi_today < rsiLow || s.rsi_today > rsiHigh) return false;
        if (requireRsiRising && s.rsi_change <= 0) return false;
        if (freshnessFilter === "fresh")     return !s.above_60_in_20d;
        if (freshnessFilter === "was_above") return s.above_60_in_20d && s.rsi_today < threshold;
        return true;
      })
    : [];

  return (
    <div className="flex flex-1 min-h-0">

      {/* ── Sidebar ──────────────────────────────────────────────────────── */}
      <aside className="w-64 shrink-0 border-r border-gray-800 overflow-y-auto">
        <div className="p-4 space-y-5">

          {/* Universe */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-widest text-gray-500 mb-2">Universe</label>
            <div className="space-y-1">
              {UNIVERSES.map(u => (
                <button key={u.id} onClick={() => setUniverse(u.id)}
                  className={`w-full text-left rounded-md px-3 py-2 text-xs transition-colors ${
                    universe === u.id
                      ? "bg-blue-600/20 text-blue-300 border border-blue-700/50"
                      : "text-gray-400 hover:bg-gray-800 hover:text-gray-200 border border-transparent"
                  }`}>
                  <div className="font-medium">{u.label}</div>
                  <div className="text-gray-600 text-xs mt-0.5">{u.count} stocks</div>
                </button>
              ))}
            </div>
          </div>

          <div className="border-t border-gray-800" />

          {/* Threshold */}
          <RangeSlider
            label="Threshold" value={threshold} min={40} max={80} step={1}
            onChange={setThreshold}
            hint={`Breakout target · Approaching zone: ${threshold - 5}–${threshold}`}
          />

          {/* RSI Display Filter */}
          <div>
            <DualRangeSlider
              low={rsiLow} high={rsiHigh} min={0} max={100}
              onChange={(lo, hi) => { setRsiLow(lo); setRsiHigh(hi); }}
            />
            <p className="text-[10px] mt-1" style={{ color: "#4B5680" }}>
              Show only stocks with RSI in this range
            </p>
          </div>

          {/* Lookback */}
          <RangeSlider
            label="Lookback (Days)" value={lookback} min={5} max={60} step={1} unit="d"
            onChange={setLookback}
            hint={`"Fresh" = RSI not above ${threshold} in last ${lookback} days`}
          />

          <div className="border-t border-gray-800" />

          {/* Prior crossings */}
          <FreshnessToggle
            value={freshnessFilter} onChange={setFreshnessFilter}
            threshold={threshold} lookback={lookback}
          />

          <div className="border-t border-gray-800" />

          {/* Signal filter */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-semibold uppercase tracking-widest text-gray-500">Show Signals</label>
              <button onClick={selectAll} className="text-xs text-gray-600 hover:text-gray-400">All</button>
            </div>
            <div className="space-y-1.5">
              {ALL_SIGNALS.map(sig => {
                const cfg = SIGNAL_CONFIG[sig];
                const active = selectedSignals.has(sig);
                return (
                  <button key={sig} onClick={() => toggleSignal(sig)}
                    className={`w-full flex items-center gap-2 rounded-md px-2.5 py-2 text-xs transition-colors ${
                      active ? "bg-gray-800 text-gray-200" : "text-gray-600 hover:text-gray-400"
                    }`}>
                    <span className={`w-2 h-2 rounded-full shrink-0 ${active ? cfg.dot : "bg-gray-700"}`} />
                    <span className="text-left">{cfg.label}</span>
                    {active && <span className="ml-auto text-gray-600">✓</span>}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="border-t border-gray-800" />

          {/* ── Extra Filters ────────────────────────────────────────────── */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <label className="text-xs font-semibold uppercase tracking-widest text-gray-500">Extra Filters</label>
              {hasExtras && (
                <span className="text-[10px] text-blue-500 bg-blue-950/50 border border-blue-900/40 rounded px-1.5 py-0.5">
                  combined scan
                </span>
              )}
            </div>

            <div className="space-y-3">
              {/* Bollinger Band */}
              <ExtraFilterBlock
                label="Bollinger Band" enabled={bbOn} onToggle={() => setBbOn(v => !v)}
                tf={bbTf} onTf={setBbTf}
              >
                {(Object.keys(BB_MODES) as BBMode[]).map(k => (
                  <FilterOpt key={k} value={k} current={bbMode} onChange={setBbMode}
                    label={BB_MODES[k].label} />
                ))}
              </ExtraFilterBlock>

              {/* MACD */}
              <ExtraFilterBlock
                label="MACD" enabled={macdOn} onToggle={() => setMacdOn(v => !v)}
                tf={macdTf} onTf={setMacdTf}
              >
                {(Object.keys(MACD_MODES) as MacdMode[]).map(k => (
                  <FilterOpt key={k} value={k} current={macdMode} onChange={setMacdMode}
                    label={MACD_MODES[k].label} />
                ))}
              </ExtraFilterBlock>

              {/* Volume */}
              <ExtraFilterBlock
                label="Volume" enabled={volOn} onToggle={() => setVolOn(v => !v)}
                tf={volTf} onTf={setVolTf}
              >
                <div className="pt-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] text-gray-600">Vol / 30d avg</span>
                    <span className="text-[11px] font-bold tabular-nums" style={{ color: "#93BBFF" }}>{">"}{volRatio}%</span>
                  </div>
                  <input
                    type="range" min={50} max={500} step={10} value={volRatio}
                    onChange={e => setVolRatio(Number(e.target.value))}
                    className="range-slider w-full"
                    style={{ "--pct": `${((volRatio - 50) / 450) * 100}%` } as React.CSSProperties}
                  />
                  <div className="flex justify-between mt-1">
                    {[50,100,200,350,500].map(n => (
                      <span key={n} className="text-[9px] tabular-nums" style={{ color: "#2D3748" }}>{n}</span>
                    ))}
                  </div>
                </div>
              </ExtraFilterBlock>
            </div>

            {hasExtras && (
              <p className="text-[10px] mt-2" style={{ color: "#374151" }}>
                Extra filters use screen endpoint · RSI lookback/threshold use defaults (50d, 60)
              </p>
            )}
          </div>

          <div className="border-t border-gray-800" />

          {/* Today's RSI */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-widest text-gray-500 mb-2">Today's RSI</label>
            <CheckToggle
              label="RSI rising today"
              checked={requireRsiRising}
              onChange={setRequireRsiRising}
            />
            <p className="text-[10px] mt-1" style={{ color: "#4B5680" }}>
              Only show stocks where RSI {">"} yesterday
            </p>
          </div>

          {/* Scan button */}
          <button
            onClick={() => void handleScan()}
            disabled={loading}
            className="w-full rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed px-4 py-2.5 text-sm font-semibold text-white transition-colors"
          >
            {loading ? "Scanning…" : "Run Scan"}
          </button>

        </div>
      </aside>

      {/* ── Main content ─────────────────────────────────────────────────── */}
      <main className="flex-1 min-w-0 overflow-y-auto p-5 space-y-4">

        {!result && !loading && (
          <div className="space-y-4">
            <div className="flex flex-col items-center justify-center py-12 gap-3">
              <div className="text-4xl opacity-20">📈</div>
              <p className="text-gray-500 text-sm">Detect stocks approaching or breaking out above RSI {rsiHigh}</p>
              <p className="text-gray-700 text-xs">Select universe and signals, then run the scan</p>
            </div>
            <div className="grid grid-cols-2 gap-3 max-w-2xl mx-auto">
              {ALL_SIGNALS.slice(0, 4).map(sig => {
                const cfg = SIGNAL_CONFIG[sig];
                return (
                  <div key={sig} className="rounded-lg border border-gray-800 bg-gray-900/40 p-3 space-y-1">
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${cfg.dot}`} />
                      <span className="text-xs font-semibold text-gray-200">{cfg.label}</span>
                    </div>
                    <p className="text-xs text-gray-500">{cfg.desc}</p>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {loading && (
          <div className="flex flex-col items-center justify-center py-20 gap-3">
            <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-gray-500 text-sm">
              {hasExtras ? "Running combined indicator scan…" : "Scanning RSI momentum across universe…"}
            </p>
            <p className="text-gray-700 text-xs">First run may take 30–90s · results cached for 4h</p>
          </div>
        )}

        {error && !loading && (
          <div className="rounded-lg border border-red-800 bg-red-950/50 px-4 py-3 text-sm text-red-300 max-w-xl">
            <span className="font-medium">Error: </span>{error}
          </div>
        )}

        {result && !loading && (
          <>
            {/* Signal summary chips */}
            <div className="flex flex-wrap gap-2 items-center">
              {ALL_SIGNALS.map(sig => {
                const count = displayedStocks.filter(s => s.signal === sig).length;
                if (count === 0) return null;
                const cfg = SIGNAL_CONFIG[sig];
                return (
                  <span key={sig} className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium ${cfg.badge}`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
                    {cfg.label}: {count}
                  </span>
                );
              })}
              {freshnessFilter !== "any" && (
                <span className="inline-flex items-center rounded-full px-3 py-1 text-xs font-medium bg-gray-800 text-blue-400 border border-blue-900">
                  {freshnessFilter === "fresh" ? `Fresh only (not above ${rsiHigh} in ${lookback}d)` : `Was above ${rsiHigh} in ${lookback}d`}
                </span>
              )}
              {bbOn   && <span className="inline-flex items-center rounded-full px-3 py-1 text-xs font-medium bg-yellow-900/30 text-yellow-400 border border-yellow-800/40">BB: {BB_MODES[bbMode].label} [{bbTf}]</span>}
              {macdOn && <span className="inline-flex items-center rounded-full px-3 py-1 text-xs font-medium bg-green-900/30 text-green-400 border border-green-800/40">MACD: {MACD_MODES[macdMode].label} [{macdTf}]</span>}
              {volOn  && <span className="inline-flex items-center rounded-full px-3 py-1 text-xs font-medium bg-blue-900/30 text-blue-400 border border-blue-800/40">Vol {">"}{volRatio}% [{volTf}]</span>}
            </div>

            {/* Stats + CSV bar */}
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>
                <span className="text-gray-200 font-medium">{result.total_matched}</span> fetched ·{" "}
                <span className="text-gray-200 font-medium">{displayedStocks.length}</span> shown ·{" "}
                {result.execution_time_ms.toFixed(0)}ms
              </span>
              <button
                onClick={() => {
                  const rows = displayedStocks.map(s => {
                    const ex = extraIndicators?.[s.id];
                    return {
                      symbol: s.symbol, exchange: s.exchange,
                      company: s.company_name, sector: s.sector,
                      cap: s.market_cap_category,
                      signal: s.signal, rsi_today: s.rsi_today,
                      rsi_prev: s.rsi_prev, rsi_change: s.rsi_change,
                      rsi_trend: s.rsi_trend,
                      distance_to_threshold: s.distance_to_60,
                      above_threshold_in_lookback: s.above_60_in_20d,
                      days_since_above_threshold: s.days_since_above_60 ?? "",
                      signal_rank: s.signal_rank,
                      ...(extraIndicators ? {
                        bb_pct_b:  ex?.bb_pct_b  ?? "",
                        macd_hist: ex?.macd_hist ?? "",
                        vol_ratio: ex?.vol_ratio ?? "",
                      } : {}),
                    };
                  });
                  if (!rows.length) return;
                  const keys = Object.keys(rows[0]);
                  const escape = (v: unknown) => {
                    const s = String(v ?? "");
                    return s.includes(",") || s.includes('"') ? `"${s.replace(/"/g, '""')}"` : s;
                  };
                  const csv = [keys.join(","), ...rows.map(r => keys.map(k => escape((r as Record<string,unknown>)[k])).join(","))].join("\n");
                  const a = document.createElement("a");
                  a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
                  a.download = `rsi_momentum_${universe}_${new Date().toISOString().slice(0,10)}.csv`;
                  a.click();
                }}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded border border-gray-700 text-gray-300 hover:border-blue-600 hover:text-blue-300 hover:bg-blue-950/30 transition-colors font-medium"
              >
                ↓ CSV
              </button>
            </div>
            <RSIMomentumTable
              stocks={displayedStocks}
              threshold={rsiHigh}
              lookback={lookback}
              extras={extraIndicators}
              showBB={extraIndicators !== null}
              showMACD={extraIndicators !== null}
              showVol={extraIndicators !== null}
            />
          </>
        )}
      </main>
    </div>
  );
}
