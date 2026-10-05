import { useState, useCallback, useEffect } from "react";
import type { DivergenceScanResult, DivergenceHit, DivergenceType, MarketCapCategory } from "../types";
import { scanRSIDivergence } from "../api";

// ─── localStorage persistence ─────────────────────────────────────────────────

export const RSI_DIV_LS_KEY = "rsi_div_page_settings_v1";

export interface RsiDivSettings {
  universe: string; timeframe: string;
  pivotLeft: number; pivotRight: number;
  maxRecencyBars: number; minBarsBetween: number; maxBarsBetween: number;
  minRsiChange: number; minPriceChgPct: number;
  maxPivotRsi: number | null; minPivotRsi: number | null;
  requireRsiRising: boolean; divTypes: DivergenceType[];
}

const RSI_DIV_DEFAULTS: RsiDivSettings = {
  universe: "NIFTY_500", timeframe: "1D",
  pivotLeft: 3, pivotRight: 3, maxRecencyBars: 10,
  minBarsBetween: 5, maxBarsBetween: 50,
  minRsiChange: 1.0, minPriceChgPct: 0.1,
  maxPivotRsi: 40, minPivotRsi: null,
  requireRsiRising: false, divTypes: ["REGULAR_BULLISH"],
};

export function loadRsiDivSettings(): RsiDivSettings {
  try {
    const raw = localStorage.getItem(RSI_DIV_LS_KEY);
    if (raw) return { ...RSI_DIV_DEFAULTS, ...JSON.parse(raw) as Partial<RsiDivSettings> };
  } catch { /* ignore */ }
  return { ...RSI_DIV_DEFAULTS };
}

function saveRsiDivSettings(s: RsiDivSettings) {
  try { localStorage.setItem(RSI_DIV_LS_KEY, JSON.stringify(s)); } catch { /* ignore */ }
}

// ─── Constants ────────────────────────────────────────────────────────────────

const UNIVERSES = [
  { id: "NIFTY_50",           label: "Nifty 50",     count: 50 },
  { id: "NIFTY_500",          label: "Nifty 500",    count: 500 },
  { id: "NIFTY_TOTAL_MARKET", label: "Total Market", count: "750+" },
];

const DIV_TYPE_CONFIG: Record<DivergenceType, { label: string; short: string; color: string; desc: string }> = {
  REGULAR_BULLISH: {
    label: "Regular Bullish",
    short: "Bull Div",
    color: "#4ade80",
    desc: "Price LL · RSI HL → reversal signal",
  },
  REGULAR_BEARISH: {
    label: "Regular Bearish",
    short: "Bear Div",
    color: "#f87171",
    desc: "Price HH · RSI LH → reversal signal",
  },
  HIDDEN_BULLISH: {
    label: "Hidden Bullish",
    short: "Hidden Bull",
    color: "#93BBFF",
    desc: "Price HL · RSI LL → trend continuation",
  },
  HIDDEN_BEARISH: {
    label: "Hidden Bearish",
    short: "Hidden Bear",
    color: "#fb923c",
    desc: "Price LH · RSI HH → trend continuation",
  },
};

const MCAP_LABEL: Record<MarketCapCategory, string> = {
  LARGE_CAP: "Large", MID_CAP: "Mid", SMALL_CAP: "Small", MICRO_CAP: "Micro",
};

const ALL_DIV_TYPES: DivergenceType[] = [
  "REGULAR_BULLISH", "REGULAR_BEARISH", "HIDDEN_BULLISH", "HIDDEN_BEARISH",
];

// ─── Small components ─────────────────────────────────────────────────────────

function MiniSlider({
  label, value, min, max, step, unit = "", onChange, hint,
}: {
  label: string; value: number; min: number; max: number;
  step: number; unit?: string; onChange: (v: number) => void; hint?: string;
}) {
  const pct = `${((value - min) / (max - min)) * 100}%`;
  return (
    <div>
      <div className="flex items-baseline justify-between mb-2">
        <span className="text-xs font-semibold uppercase tracking-widest text-gray-500">{label}</span>
        <span className="text-base font-bold tabular-nums" style={{ color: "#93BBFF" }}>{value}{unit}</span>
      </div>
      <input
        type="range" min={min} max={max} step={step} value={value}
        onChange={e => onChange(Number(e.target.value))}
        className="range-slider" style={{ "--pct": pct } as React.CSSProperties}
      />
      {hint && <p className="text-[10px] mt-1" style={{ color: "#2D3748" }}>{hint}</p>}
    </div>
  );
}

function DualRangeSlider({
  label, low, high, min, max, step = 1, hint, onChange,
}: {
  label: string; low: number; high: number; min: number; max: number;
  step?: number; hint?: string; onChange: (lo: number, hi: number) => void;
}) {
  const lowPct  = ((low  - min) / (max - min)) * 100;
  const highPct = ((high - min) / (max - min)) * 100;
  const highZ   = highPct - lowPct < 10 ? 5 : 2;
  return (
    <div>
      <div className="flex items-baseline justify-between mb-2">
        <span className="text-xs font-semibold uppercase tracking-widest text-gray-500">{label}</span>
        <span className="text-base font-bold tabular-nums" style={{ color: "#93BBFF" }}>{low}–{high}d</span>
      </div>
      <div style={{ position: "relative", height: "20px", display: "flex", alignItems: "center" }}>
        <div style={{ position: "absolute", left: 0, right: 0, height: "3px", background: "rgba(255,255,255,0.09)", borderRadius: "2px" }} />
        <div style={{ position: "absolute", left: `${lowPct}%`, right: `${100 - highPct}%`, height: "3px", background: "var(--accent-blue, #3B82F6)", borderRadius: "2px" }} />
        <input type="range" min={min} max={max} step={step} value={low}
          onChange={e => onChange(Math.min(Number(e.target.value), high - step), high)}
          className="dual-range" style={{ zIndex: 2 }} />
        <input type="range" min={min} max={max} step={step} value={high}
          onChange={e => onChange(low, Math.max(Number(e.target.value), low + step))}
          className="dual-range" style={{ zIndex: highZ }} />
      </div>
      <div className="flex justify-between mt-1.5">
        {[5, 15, 25, 35, 50].map(n => (
          <span key={n} className="text-[10px] tabular-nums" style={{ color: "#2D3748" }}>{n}</span>
        ))}
      </div>
      {hint && <p className="text-[10px] mt-1" style={{ color: "#2D3748" }}>{hint}</p>}
    </div>
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

// ─── Sorting ──────────────────────────────────────────────────────────────────

type SortKey = "divergence_age" | "strength_score" | "rsi_change" | "price_chg_pct" |
               "bars_between" | "pivot2_rsi" | "rsi_today" | "symbol";

function scoreColor(s: number): string {
  if (s >= 7) return "#4ade80";
  if (s >= 5) return "#facc15";
  if (s >= 3) return "#93BBFF";
  return "#6B7280";
}

function pctColor(v: number): string {
  return v < 0 ? "#f87171" : "#4ade80";
}

// ─── Divergence Table ─────────────────────────────────────────────────────────

function DivergenceTable({ hits }: { hits: DivergenceHit[] }) {
  const [sortKey, setSortKey] = useState<SortKey>("divergence_age");
  const [sortAsc, setSortAsc] = useState(true);

  function handleSort(key: SortKey) {
    if (sortKey === key) setSortAsc(a => !a);
    else { setSortKey(key); setSortAsc(key === "divergence_age"); }
  }

  const sorted = [...hits].sort((a, b) => {
    const m = sortAsc ? 1 : -1;
    if (sortKey === "symbol") return m * a.symbol.localeCompare(b.symbol);
    if (sortKey === "rsi_today") {
      const av = a.rsi_today ?? -999;
      const bv = b.rsi_today ?? -999;
      return m * (av - bv);
    }
    const av = a[sortKey] as number;
    const bv = b[sortKey] as number;
    return m * (av - bv);
  });

  function Th({ k, label, right = false }: { k: SortKey; label: string; right?: boolean }) {
    const active = sortKey === k;
    return (
      <th
        onClick={() => handleSort(k)}
        className={`py-2 px-3 text-[10px] font-semibold uppercase tracking-widest cursor-pointer select-none ${right ? "text-right" : "text-left"}`}
        style={{ color: active ? "#93BBFF" : "#374151" }}
      >
        {label}{active ? (sortAsc ? " ↑" : " ↓") : ""}
      </th>
    );
  }

  if (hits.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 gap-2">
        <p className="text-gray-500 text-sm">No divergences found</p>
        <p className="text-gray-700 text-xs">Try increasing the recency window or relaxing filter parameters</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs border-collapse">
        <thead>
          <tr className="border-b border-gray-800">
            <Th k="symbol"         label="Symbol" />
            <th className="py-2 px-3 text-[10px] font-semibold uppercase tracking-widest text-left text-gray-600">Type</th>
            <Th k="divergence_age" label="Days Since" right />
            <th className="py-2 px-3 text-[10px] font-semibold uppercase tracking-widest text-right text-gray-600">P1 Date</th>
            <th className="py-2 px-3 text-[10px] font-semibold uppercase tracking-widest text-right text-gray-600">P2 Date</th>
            <th className="py-2 px-3 text-[10px] font-semibold uppercase tracking-widest text-right text-gray-600">P1 Price</th>
            <th className="py-2 px-3 text-[10px] font-semibold uppercase tracking-widest text-right text-gray-600">P2 Price</th>
            <Th k="pivot2_rsi"     label="P1 RSI"  right />
            <Th k="pivot2_rsi"     label="P2 RSI"  right />
            <Th k="price_chg_pct"  label="Price Δ%"  right />
            <Th k="rsi_change"     label="RSI Δ"     right />
            <Th k="bars_between"   label="Bars"      right />
            <Th k="rsi_today"      label="RSI Now"   right />
            <Th k="strength_score" label="Score"     right />
          </tr>
        </thead>
        <tbody>
          {sorted.map((h, i) => {
            const cfg = DIV_TYPE_CONFIG[h.div_type];
            return (
              <tr
                key={`${h.symbol}-${h.pivot2_date}-${i}`}
                className="border-b border-gray-900 hover:bg-gray-900/60 transition-colors"
              >
                {/* Symbol + company */}
                <td className="py-2.5 px-3">
                  <div className="font-semibold text-white">{h.symbol}</div>
                  <div className="text-gray-600 truncate max-w-[120px]">{h.company_name}</div>
                  <span className="text-[9px] px-1 py-0.5 rounded mt-0.5 inline-block"
                    style={{ background: "rgba(255,255,255,0.04)", color: "#4B5563" }}>
                    {MCAP_LABEL[h.market_cap_category]}
                  </span>
                </td>
                {/* Type badge */}
                <td className="py-2.5 px-3">
                  <span className="text-[10px] font-medium px-1.5 py-0.5 rounded"
                    style={{ color: cfg.color, background: `${cfg.color}18`, border: `1px solid ${cfg.color}30` }}>
                    {cfg.short}
                  </span>
                </td>
                {/* Days since pivot2 */}
                <td className="py-2.5 px-3 text-right tabular-nums">
                  <span style={{ color: h.divergence_age <= 3 ? "#4ade80" : h.divergence_age <= 7 ? "#facc15" : "#93BBFF" }}>
                    {h.divergence_age}d
                  </span>
                </td>
                {/* Dates */}
                <td className="py-2.5 px-3 text-right tabular-nums text-gray-500">{h.pivot1_date}</td>
                <td className="py-2.5 px-3 text-right tabular-nums" style={{ color: "#93BBFF" }}>{h.pivot2_date}</td>
                {/* Prices */}
                <td className="py-2.5 px-3 text-right tabular-nums text-gray-400">
                  ₹{h.pivot1_price.toLocaleString("en-IN", { maximumFractionDigits: 2 })}
                </td>
                <td className="py-2.5 px-3 text-right tabular-nums text-gray-300">
                  ₹{h.pivot2_price.toLocaleString("en-IN", { maximumFractionDigits: 2 })}
                </td>
                {/* RSI values */}
                <td className="py-2.5 px-3 text-right tabular-nums text-gray-500">{h.pivot1_rsi.toFixed(1)}</td>
                <td className="py-2.5 px-3 text-right tabular-nums font-medium" style={{ color: "#93BBFF" }}>
                  {h.pivot2_rsi.toFixed(1)}
                </td>
                {/* Price change % */}
                <td className="py-2.5 px-3 text-right tabular-nums font-medium" style={{ color: pctColor(h.price_chg_pct) }}>
                  {h.price_chg_pct > 0 ? "+" : ""}{h.price_chg_pct.toFixed(2)}%
                </td>
                {/* RSI change */}
                <td className="py-2.5 px-3 text-right tabular-nums font-medium" style={{ color: "#4ade80" }}>
                  +{h.rsi_change.toFixed(2)}
                </td>
                {/* Bars between */}
                <td className="py-2.5 px-3 text-right tabular-nums text-gray-500">{h.bars_between}</td>
                {/* RSI today vs prev */}
                <td className="py-2.5 px-3 text-right tabular-nums">
                  {h.rsi_today != null ? (
                    <span style={{ color: h.rsi_today > (h.rsi_prev ?? 0) ? "#4ade80" : "#f87171" }}>
                      {h.rsi_today.toFixed(1)}
                      <span className="ml-0.5 text-[9px]">{h.rsi_today > (h.rsi_prev ?? 0) ? "↑" : "↓"}</span>
                    </span>
                  ) : <span className="text-gray-700">—</span>}
                </td>
                {/* Strength score */}
                <td className="py-2.5 px-3 text-right tabular-nums font-bold" style={{ color: scoreColor(h.strength_score) }}>
                  {h.strength_score.toFixed(1)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export function RSIDivergencePage() {
  const _init = loadRsiDivSettings();
  const [universe,         setUniverse]         = useState(_init.universe);
  const [timeframe,        setTimeframe]         = useState(_init.timeframe);
  const [pivotLeft,        setPivotLeft]         = useState(_init.pivotLeft);
  const [pivotRight,       setPivotRight]        = useState(_init.pivotRight);
  const [maxRecencyBars,   setMaxRecencyBars]    = useState(_init.maxRecencyBars);
  const [minBarsBetween,   setMinBarsBetween]    = useState(_init.minBarsBetween);
  const [maxBarsBetween,   setMaxBarsBetween]    = useState(_init.maxBarsBetween);
  const [minRsiChange,     setMinRsiChange]      = useState(_init.minRsiChange);
  const [minPriceChgPct,   setMinPriceChgPct]   = useState(_init.minPriceChgPct);
  const [maxPivotRsi,      setMaxPivotRsi]       = useState<number | null>(_init.maxPivotRsi);
  const [minPivotRsi,      setMinPivotRsi]       = useState<number | null>(_init.minPivotRsi);
  const [requireRsiRising, setRequireRsiRising]  = useState(_init.requireRsiRising);
  const [selectedTypes,    setSelectedTypes]     = useState<Set<DivergenceType>>(
    new Set(_init.divTypes)
  );

  const [result,   setResult]   = useState<DivergenceScanResult | null>(null);
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState<string | null>(null);

  // Persist settings on every change so tab-switching doesn't reset them
  useEffect(() => {
    saveRsiDivSettings({
      universe, timeframe, pivotLeft, pivotRight, maxRecencyBars,
      minBarsBetween, maxBarsBetween, minRsiChange, minPriceChgPct,
      maxPivotRsi, minPivotRsi, requireRsiRising, divTypes: [...selectedTypes],
    });
  }, [universe, timeframe, pivotLeft, pivotRight, maxRecencyBars,
      minBarsBetween, maxBarsBetween, minRsiChange, minPriceChgPct,
      maxPivotRsi, minPivotRsi, requireRsiRising, selectedTypes]);

  function toggleType(t: DivergenceType) {
    setSelectedTypes(prev => {
      const next = new Set(prev);
      if (next.has(t)) { if (next.size > 1) next.delete(t); }
      else next.add(t);
      return next;
    });
  }

  const handleScan = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await scanRSIDivergence({
        universe,
        timeframe,
        pivot_left:          pivotLeft,
        pivot_right:         pivotRight,
        max_recency_bars:    maxRecencyBars,
        min_bars_between:    minBarsBetween,
        max_bars_between:    maxBarsBetween,
        min_rsi_change:      minRsiChange,
        min_price_chg_pct:   minPriceChgPct,
        max_pivot_rsi:       maxPivotRsi ?? undefined,
        min_pivot_rsi:       minPivotRsi ?? undefined,
        require_rsi_rising:  requireRsiRising,
        div_types:           [...selectedTypes],
        limit: 200,
      });
      setResult(res);
    } catch (e) {
      setError((e as Error).message);
      setResult(null);
    } finally {
      setLoading(false);
    }
  }, [universe, timeframe, pivotLeft, pivotRight, maxRecencyBars, minBarsBetween, maxBarsBetween, minRsiChange, minPriceChgPct, maxPivotRsi, minPivotRsi, requireRsiRising, selectedTypes]);

  return (
    <div className="flex flex-1 min-h-0">

      {/* ── Sidebar ───────────────────────────────────────────────────────── */}
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

          {/* Timeframe */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-widest text-gray-500 mb-2">Timeframe</label>
            <div className="grid grid-cols-4 gap-1">
              {(["1H", "4H", "1D", "1W"] as const).map(tf => (
                <button
                  key={tf}
                  onClick={() => setTimeframe(tf)}
                  className={`rounded py-1.5 text-xs font-semibold transition-colors ${
                    timeframe === tf
                      ? "bg-blue-600/30 text-blue-300 border border-blue-600/50"
                      : "text-gray-500 border border-gray-800 hover:text-gray-300 hover:border-gray-600"
                  }`}
                >{tf}</button>
              ))}
            </div>
            {(timeframe === "1H" || timeframe === "4H") && (
              <p className="mt-1.5 text-[10px] text-yellow-700">
                Intraday bars — more noise, shorter divergence windows recommended
              </p>
            )}
          </div>

          <div className="border-t border-gray-800" />

          {/* Divergence type */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-widest text-gray-500 mb-2">Pattern</label>
            <div className="space-y-1.5">
              {ALL_DIV_TYPES.map(t => {
                const cfg = DIV_TYPE_CONFIG[t];
                const active = selectedTypes.has(t);
                return (
                  <button key={t} onClick={() => toggleType(t)}
                    className={`w-full flex items-center gap-2 rounded-md px-2.5 py-2 text-xs transition-colors ${
                      active ? "bg-gray-800" : "text-gray-600 hover:text-gray-400"
                    }`}>
                    <span className="w-2 h-2 rounded-full shrink-0" style={{ background: active ? cfg.color : "#374151" }} />
                    <div className="text-left">
                      <div style={{ color: active ? "#E2E8F0" : "#6B7280" }}>{cfg.label}</div>
                      <div className="text-[9px]" style={{ color: active ? "#4B5680" : "#1F2937" }}>{cfg.desc}</div>
                    </div>
                    {active && <span className="ml-auto text-gray-600">✓</span>}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="border-t border-gray-800" />

          {/* Pivot detection */}
          <div className="space-y-4">
            <label className="block text-xs font-semibold uppercase tracking-widest text-gray-500">Pivot Detection</label>
            <MiniSlider
              label="Pivot Left"  value={pivotLeft}  min={1} max={8} step={1}
              onChange={setPivotLeft}
              hint="Bars to left that must be higher"
            />
            <MiniSlider
              label="Pivot Right" value={pivotRight} min={1} max={8} step={1}
              onChange={setPivotRight}
              hint="Bars to right that must be higher"
            />
          </div>

          <div className="border-t border-gray-800" />

          {/* Recency & spacing */}
          <div className="space-y-4">
            <label className="block text-xs font-semibold uppercase tracking-widest text-gray-500">Filters</label>
            <MiniSlider
              label="Max Days Since P2" value={maxRecencyBars} min={1} max={20} step={1} unit="d"
              onChange={setMaxRecencyBars}
              hint="Second pivot must be this recent"
            />
            <DualRangeSlider
              label="Bars Between P1 & P2"
              low={minBarsBetween} high={maxBarsBetween}
              min={5} max={50} step={1}
              hint="Trading days separating the two pivots"
              onChange={(lo, hi) => { setMinBarsBetween(lo); setMaxBarsBetween(hi); }}
            />
            <MiniSlider
              label="Min RSI Change" value={minRsiChange} min={0} max={15} step={0.5}
              onChange={setMinRsiChange}
              hint="RSI improvement threshold"
            />
            <MiniSlider
              label="Min Price Drop %" value={minPriceChgPct} min={0} max={5} step={0.1}
              onChange={setMinPriceChgPct}
              hint="Price must drop at least this much"
            />
          </div>

          <div className="border-t border-gray-800" />

          {/* RSI level gates */}
          <div className="space-y-4">
            <label className="block text-xs font-semibold uppercase tracking-widest text-gray-500">RSI Level Gate</label>

            {/* Bullish max RSI toggle + slider */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <button
                  onClick={() => setMaxPivotRsi(v => v === null ? 40 : null)}
                  className="flex items-center gap-2 text-xs"
                >
                  <span
                    className="w-3 h-3 rounded border flex items-center justify-center text-[8px]"
                    style={{
                      background: maxPivotRsi !== null ? "rgba(59,130,246,0.25)" : "transparent",
                      borderColor: maxPivotRsi !== null ? "#3B82F6" : "#374151",
                      color: "#93BBFF",
                    }}
                  >{maxPivotRsi !== null ? "✓" : ""}</span>
                  <span style={{ color: maxPivotRsi !== null ? "#4ade80" : "#6B7280" }} className="font-medium">
                    Bullish: P1 & P2 RSI &lt; {maxPivotRsi ?? "—"}
                  </span>
                </button>
              </div>
              {maxPivotRsi !== null && (
                <MiniSlider
                  label="" value={maxPivotRsi} min={20} max={60} step={1}
                  onChange={setMaxPivotRsi}
                  hint="Both pivots must have RSI below this (oversold zone)"
                />
              )}
            </div>

            {/* Bearish min RSI toggle + slider */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <button
                  onClick={() => setMinPivotRsi(v => v === null ? 60 : null)}
                  className="flex items-center gap-2 text-xs"
                >
                  <span
                    className="w-3 h-3 rounded border flex items-center justify-center text-[8px]"
                    style={{
                      background: minPivotRsi !== null ? "rgba(59,130,246,0.25)" : "transparent",
                      borderColor: minPivotRsi !== null ? "#3B82F6" : "#374151",
                      color: "#93BBFF",
                    }}
                  >{minPivotRsi !== null ? "✓" : ""}</span>
                  <span style={{ color: minPivotRsi !== null ? "#f87171" : "#6B7280" }} className="font-medium">
                    Bearish: P1 & P2 RSI &gt; {minPivotRsi ?? "—"}
                  </span>
                </button>
              </div>
              {minPivotRsi !== null && (
                <MiniSlider
                  label="" value={minPivotRsi} min={40} max={85} step={1}
                  onChange={setMinPivotRsi}
                  hint="Both pivots must have RSI above this (overbought zone)"
                />
              )}
            </div>
          </div>

          <div className="border-t border-gray-800" />

          {/* RSI Momentum filter */}
          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-widest text-gray-500">Today's RSI</label>
            <CheckToggle
              label="RSI rising today (today > yesterday)"
              checked={requireRsiRising}
              onChange={setRequireRsiRising}
              color="#4ade80"
            />
            <p className="text-[10px]" style={{ color: "#2D3748" }}>
              Only show stocks where RSI is currently ticking up
            </p>
          </div>

          {/* Scan */}
          <button
            onClick={() => void handleScan()}
            disabled={loading}
            className="w-full rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed px-4 py-2.5 text-sm font-semibold text-white transition-colors"
          >
            {loading ? "Scanning…" : "Scan for Divergence"}
          </button>

          {result && !loading && (
            <p className="text-xs text-gray-600 text-center">
              {result.total_matched} found · {result.stocks_screened} scanned
              {" "}· {result.execution_time_ms.toFixed(0)}ms · {timeframe}
            </p>
          )}
        </div>
      </aside>

      {/* ── Main content ──────────────────────────────────────────────────── */}
      <main className="flex-1 overflow-y-auto p-5 space-y-4">

        {/* Legend */}
        <div className="flex flex-wrap gap-3 text-[10px]" style={{ color: "#374151" }}>
          <span>P1 = first (older) pivot · P2 = second (recent) pivot</span>
          <span className="text-gray-700">·</span>
          <span>Bull Div: P1 price &gt; P2 price · P1 RSI &lt; P2 RSI</span>
          <span className="text-gray-700">·</span>
          <span>Score 0–10: higher = stronger divergence</span>
        </div>

        {!result && !loading && !error && (
          <div className="flex flex-col items-center justify-center py-16 gap-3">
            <div className="text-5xl opacity-10">📉</div>
            <p className="text-gray-500 text-sm">Select a universe and click Scan</p>
            <p className="text-gray-700 text-xs">
              Detects price swing lows where RSI makes a higher low (bullish divergence)
            </p>
            <p className="text-gray-700 text-xs">Second pivot must be within {maxRecencyBars} trading days</p>
          </div>
        )}

        {loading && (
          <div className="flex flex-col items-center justify-center py-16 gap-3">
            <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-gray-500 text-sm">Scanning for divergences…</p>
            <p className="text-gray-700 text-xs">Fetches 2 years of daily data · results cached 4h</p>
          </div>
        )}

        {error && !loading && (
          <div className="rounded-lg border border-red-800 bg-red-950/50 px-4 py-3 text-sm text-red-300">
            <span className="font-medium">Error: </span>{error}
          </div>
        )}

        {result && !loading && (
          <>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <h2 className="text-sm font-semibold text-gray-300">
                  {result.total_matched} Recent Divergence{result.total_matched !== 1 ? "s" : ""}
                </h2>
                <span className="text-xs text-gray-700">
                  in {result.universe} · pivot {pivotLeft}/{pivotRight} · P2 within {maxRecencyBars}d
                </span>
              </div>
              <button
                onClick={() => {
                  const rows = result.divergences.map(h => ({
                    symbol: h.symbol, exchange: h.exchange,
                    company: h.company_name, sector: h.sector,
                    cap: h.market_cap_category,
                    div_type: h.div_type, status: h.status,
                    pivot1_date: h.pivot1_date, pivot2_date: h.pivot2_date,
                    pivot1_price: h.pivot1_price, pivot2_price: h.pivot2_price,
                    pivot1_rsi: h.pivot1_rsi, pivot2_rsi: h.pivot2_rsi,
                    price_chg_pct: h.price_chg_pct, rsi_change: h.rsi_change,
                    bars_between: h.bars_between, divergence_age: h.divergence_age,
                    strength_score: h.strength_score,
                  }));
                  const date = new Date().toISOString().slice(0, 10);
                  const keys = Object.keys(rows[0]);
                  const csv = [
                    keys.join(","),
                    ...rows.map(r => keys.map(k => {
                      const v = String((r as Record<string, unknown>)[k] ?? "");
                      return v.includes(",") ? `"${v}"` : v;
                    }).join(",")),
                  ].join("\n");
                  const a = document.createElement("a");
                  a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
                  a.download = `rsi_divergence_${result.universe}_${date}.csv`;
                  a.click();
                }}
                className="flex items-center gap-1 px-2.5 py-1 rounded border border-gray-700 text-xs text-gray-400 hover:border-gray-500 hover:text-gray-200 transition-colors"
              >
                ↓ CSV
              </button>
            </div>
            <DivergenceTable hits={result.divergences} />
          </>
        )}
      </main>
    </div>
  );
}
