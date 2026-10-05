import { useState, useCallback, useEffect, useRef } from "react";
import type { MACDResult, MACDScanResult, MACDChartBar, MACDChartData, MarketCapCategory } from "../types";
import { scanMACD, getMACDChart } from "../api";

// ─── Constants ────────────────────────────────────────────────────────────────

const UNIVERSES = [
  { id: "NIFTY_50",           label: "Nifty 50",     count: 50 },
  { id: "NIFTY_500",          label: "Nifty 500",    count: 500 },
  { id: "NIFTY_TOTAL_MARKET", label: "Total Market", count: "750+" },
];

const SOURCES = ["Close", "Open", "High", "Low", "HL2", "HLC3", "OHLC4"] as const;
const MA_TYPES = ["EMA", "SMA"] as const;
const TIMEFRAMES = ["1H", "4H", "1D", "1W"] as const;

const MCAP_BADGE: Record<MarketCapCategory, string> = {
  LARGE_CAP: "bg-blue-900/60 text-blue-300 border border-blue-800/50",
  MID_CAP:   "bg-purple-900/60 text-purple-300 border border-purple-800/50",
  SMALL_CAP: "bg-yellow-900/60 text-yellow-300 border border-yellow-800/50",
  MICRO_CAP: "bg-gray-800 text-gray-400 border border-gray-700",
};
const MCAP_LABEL: Record<MarketCapCategory, string> = {
  LARGE_CAP: "Large", MID_CAP: "Mid", SMALL_CAP: "Small", MICRO_CAP: "Micro",
};

// Histogram state display config
const HIST_STATE_CFG = {
  STRONG_BULLISH: { label: "Strong Bullish",   badge: "bg-green-900/60 text-green-300 border border-green-700",   dot: "bg-green-400" },
  BULLISH_FADING: { label: "Bullish Fading",   badge: "bg-teal-900/60 text-teal-300 border border-teal-700",     dot: "bg-teal-400"  },
  STRONG_BEARISH: { label: "Strong Bearish",   badge: "bg-red-900/60 text-red-300 border border-red-700",         dot: "bg-red-400"   },
  BEARISH_FADING: { label: "Bearish Fading",   badge: "bg-orange-900/60 text-orange-300 border border-orange-700", dot: "bg-orange-400" },
  NEUTRAL:        { label: "Neutral",           badge: "bg-gray-800 text-gray-400 border border-gray-700",         dot: "bg-gray-500"  },
};

// Full MACD state → display
function macdStateLabel(s: string): string {
  const map: Record<string, string> = {
    STRONG_BULLISH:                "Strong Bullish",
    BULLISH_FADING:                "Bullish Fading",
    STRONG_BEARISH:                "Strong Bearish",
    BEARISH_FADING:                "Bearish Fading",
    NEUTRAL:                       "Neutral",
    BULLISH_CROSSOVER_ABOVE_ZERO:  "↑ Cross Above 0",
    BULLISH_CROSSOVER_BELOW_ZERO:  "↑ Cross Below 0",
    BEARISH_CROSSOVER_ABOVE_ZERO:  "↓ Cross Above 0",
    BEARISH_CROSSOVER_BELOW_ZERO:  "↓ Cross Below 0",
  };
  return map[s] ?? s;
}

function macdStateBadge(s: string): string {
  if (s.startsWith("STRONG_BULLISH") || s.includes("BULLISH_CROSSOVER"))
    return "bg-green-900/60 text-green-300 border border-green-700";
  if (s === "BULLISH_FADING")
    return "bg-teal-900/60 text-teal-300 border border-teal-700";
  if (s.startsWith("STRONG_BEARISH") || s.includes("BEARISH_CROSSOVER"))
    return "bg-red-900/60 text-red-300 border border-red-700";
  if (s === "BEARISH_FADING")
    return "bg-orange-900/60 text-orange-300 border border-orange-700";
  return "bg-gray-800 text-gray-400 border border-gray-700";
}

// Histogram bar colors for SVG chart
function histBarColor(state: string): string {
  if (state === "STRONG_BULLISH") return "#26a69a";
  if (state === "BULLISH_FADING") return "#80cbc4";
  if (state === "STRONG_BEARISH") return "#ef5350";
  if (state === "BEARISH_FADING") return "#ef9a9a";
  return "#6b7280";
}

// ─── localStorage persistence ─────────────────────────────────────────────────

const LS_KEY = "macd_page_settings_v1";

interface MACDSettings {
  universe: string;
  source: string;
  fast: number;
  slow: number;
  signalPeriod: number;
  oscMa: string;
  sigMa: string;
  timeframe: string;
  histFilters: string[];
  crossFilters: string[];
  crossBars: number;
  crossoverLookback: number;
}

const DEFAULTS: MACDSettings = {
  universe: "NIFTY_500",
  source: "Close",
  fast: 12,
  slow: 26,
  signalPeriod: 9,
  oscMa: "EMA",
  sigMa: "EMA",
  timeframe: "1D",
  histFilters: [],
  crossFilters: [],
  crossBars: 5,
  crossoverLookback: 20,
};

function loadSettings(): MACDSettings {
  try {
    const raw = localStorage.getItem(LS_KEY);
    if (raw) return { ...DEFAULTS, ...JSON.parse(raw) as Partial<MACDSettings> };
  } catch { /* ignore */ }
  return { ...DEFAULTS };
}

function saveSettings(s: MACDSettings) {
  try { localStorage.setItem(LS_KEY, JSON.stringify(s)); } catch { /* ignore */ }
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function CheckToggle({ label, checked, onChange, color = "#93BBFF" }: {
  label: string; checked: boolean; onChange: (v: boolean) => void; color?: string;
}) {
  return (
    <button onClick={() => onChange(!checked)} className="w-full flex items-center gap-2 text-xs text-left py-1">
      <span
        className="w-3.5 h-3.5 rounded border flex items-center justify-center text-[8px] shrink-0"
        style={{ background: checked ? "rgba(59,130,246,0.25)" : "transparent", borderColor: checked ? "#3B82F6" : "#374151", color: "#93BBFF" }}
      >{checked ? "✓" : ""}</span>
      <span style={{ color: checked ? color : "#6B7280" }} className="font-medium">{label}</span>
    </button>
  );
}

function NumInput({ label, value, min, max, onChange }: {
  label: string; value: number; min: number; max: number; onChange: (v: number) => void;
}) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-[11px] text-gray-500">{label}</span>
      <input
        type="number" min={min} max={max} value={value}
        onChange={e => {
          const v = parseInt(e.target.value, 10);
          if (!isNaN(v) && v >= min && v <= max) onChange(v);
        }}
        className="w-16 bg-gray-900 border border-gray-700 rounded px-2 py-1 text-xs text-gray-200 text-right tabular-nums focus:border-blue-600 focus:outline-none"
      />
    </div>
  );
}

function SelectInput({ label, value, options, onChange }: {
  label: string; value: string; options: readonly string[]; onChange: (v: string) => void;
}) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-[11px] text-gray-500">{label}</span>
      <select
        value={value} onChange={e => onChange(e.target.value)}
        className="bg-gray-900 border border-gray-700 rounded px-2 py-1 text-xs text-gray-200 focus:border-blue-600 focus:outline-none"
      >
        {options.map(o => <option key={o} value={o}>{o}</option>)}
      </select>
    </div>
  );
}

// ─── MACD Chart (SVG) ─────────────────────────────────────────────────────────

function MACDChart({ data }: { data: MACDChartData }) {
  const bars = data.bars;
  if (bars.length < 2) return <div className="text-gray-600 text-xs p-4">Not enough data</div>;

  const W = 700, H = 200, PAD = { top: 10, bottom: 10, left: 8, right: 8 };
  const plotW = W - PAD.left - PAD.right;
  const plotH = H - PAD.top - PAD.bottom;

  const hists  = bars.map(b => b.histogram);
  const macds  = bars.map(b => b.macd);
  const sigs   = bars.map(b => b.signal);
  const all    = [...hists, ...macds, ...sigs];
  const yMin   = Math.min(...all) * 1.1;
  const yMax   = Math.max(...all) * 1.1;
  const yRange = yMax - yMin || 1;

  const n = bars.length;
  const barW = plotW / n;

  const toY = (v: number) => PAD.top + ((yMax - v) / yRange) * plotH;
  const toX = (i: number) => PAD.left + (i + 0.5) * barW;
  const zeroY = toY(0);

  // Polyline points
  const macdPts   = bars.map((b, i) => `${toX(i)},${toY(b.macd)}`).join(" ");
  const signalPts = bars.map((b, i) => `${toX(i)},${toY(b.signal)}`).join(" ");

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ background: "#0d1117", borderRadius: 6 }}>
      {/* Zero line */}
      <line x1={PAD.left} y1={zeroY} x2={W - PAD.right} y2={zeroY} stroke="#374151" strokeWidth={1} strokeDasharray="4 2" />

      {/* Histogram bars */}
      {bars.map((b, i) => {
        const x = PAD.left + i * barW + barW * 0.1;
        const bw = barW * 0.8;
        const y1 = b.histogram >= 0 ? toY(b.histogram) : zeroY;
        const y2 = b.histogram >= 0 ? zeroY : toY(b.histogram);
        return (
          <rect key={i} x={x} y={y1} width={bw} height={Math.max(y2 - y1, 1)}
            fill={histBarColor(b.histogram_state)} opacity={0.85} />
        );
      })}

      {/* MACD line */}
      <polyline points={macdPts} fill="none" stroke="#3B82F6" strokeWidth={1.5} />
      {/* Signal line */}
      <polyline points={signalPts} fill="none" stroke="#F97316" strokeWidth={1.5} />

      {/* Legend */}
      <rect x={PAD.left} y={PAD.top} width={8} height={8} fill="#3B82F6" />
      <text x={PAD.left + 11} y={PAD.top + 7} fill="#93BBFF" fontSize={9}>MACD</text>
      <rect x={PAD.left + 50} y={PAD.top} width={8} height={8} fill="#F97316" />
      <text x={PAD.left + 61} y={PAD.top + 7} fill="#FDBA74" fontSize={9}>Signal</text>
    </svg>
  );
}

// ─── Results Table ────────────────────────────────────────────────────────────

type SortCol = "symbol" | "company_name" | "market_cap_category" | "close_price"
  | "macd" | "signal_line" | "histogram" | "macd_state" | "last_crossover_bars_ago";

const MCAP_ORDER: Record<MarketCapCategory, number> = { LARGE_CAP: 4, MID_CAP: 3, SMALL_CAP: 2, MICRO_CAP: 1 };

function MACDTable({
  results,
  onSelect,
  selectedId,
}: {
  results: MACDResult[];
  onSelect: (r: MACDResult) => void;
  selectedId: string | null;
}) {
  const [sortCol, setSortCol] = useState<SortCol>("histogram");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  function toggleSort(col: SortCol) {
    if (sortCol === col) {
      setSortDir(d => d === "asc" ? "desc" : "asc");
    } else {
      setSortCol(col);
      setSortDir("desc");
    }
  }

  const sorted = [...results].sort((a, b) => {
    let av: number, bv: number;
    switch (sortCol) {
      case "symbol":       return sortDir === "asc" ? a.symbol.localeCompare(b.symbol) : b.symbol.localeCompare(a.symbol);
      case "company_name": return sortDir === "asc" ? a.company_name.localeCompare(b.company_name) : b.company_name.localeCompare(a.company_name);
      case "market_cap_category": av = MCAP_ORDER[a.market_cap_category] ?? 0; bv = MCAP_ORDER[b.market_cap_category] ?? 0; break;
      case "close_price":  av = a.close_price;  bv = b.close_price;  break;
      case "macd":         av = a.macd;          bv = b.macd;          break;
      case "signal_line":  av = a.signal_line;   bv = b.signal_line;   break;
      case "histogram":    av = a.histogram;     bv = b.histogram;     break;
      case "last_crossover_bars_ago": av = a.last_crossover_bars_ago ?? 999; bv = b.last_crossover_bars_ago ?? 999; break;
      default: return 0;
    }
    return sortDir === "asc" ? av - bv : bv - av;
  });

  const SortIcon = ({ col }: { col: SortCol }) =>
    sortCol !== col ? <span className="opacity-20">↕</span>
      : sortDir === "asc" ? <span className="text-blue-400">↑</span>
      : <span className="text-blue-400">↓</span>;

  const mkTh = (align: "left" | "right" | "center", label: string, col: SortCol) => (
    <th
      className={`text-${align} py-1.5 px-2 text-[11px] font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-300 select-none whitespace-nowrap`}
      onClick={() => toggleSort(col)}
    >{label} <SortIcon col={col} /></th>
  );

  return (
    <div
      className="overflow-x-auto rounded-lg border border-gray-800 [&::-webkit-scrollbar]:h-1.5 [&::-webkit-scrollbar-track]:bg-gray-900 [&::-webkit-scrollbar-thumb]:bg-gray-700 [&::-webkit-scrollbar-thumb]:rounded-full"
      style={{ scrollbarWidth: "thin", scrollbarColor: "#374151 #111827" }}
    >
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-gray-800 bg-gray-900/60">
            <th className="py-1.5 px-2 text-[11px] font-medium text-gray-500 w-6">#</th>
            {mkTh("left",   "Symbol",    "symbol")}
            {mkTh("left",   "Company",   "company_name")}
            {mkTh("left",   "Cap",       "market_cap_category")}
            {mkTh("right",  "Price",     "close_price")}
            {mkTh("right",  "MACD",      "macd")}
            {mkTh("right",  "Signal",    "signal_line")}
            {mkTh("right",  "Hist",      "histogram")}
            <th className="py-1.5 px-2 text-[11px] font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Dir</th>
            <th className="py-1.5 px-2 text-[11px] font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Zero</th>
            {mkTh("left",   "Status",    "macd_state")}
            <th className="py-1.5 px-2 text-[11px] font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">Cross</th>
            {mkTh("right",  "Bars Ago",  "last_crossover_bars_ago")}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-800/50">
          {sorted.length === 0 && (
            <tr><td colSpan={13} className="py-10 text-center text-gray-600">No stocks matched the filters</td></tr>
          )}
          {sorted.map((r, i) => {
            const isSelected = r.id === selectedId;
            const hCfg = HIST_STATE_CFG[r.histogram_state as keyof typeof HIST_STATE_CFG] ?? HIST_STATE_CFG.NEUTRAL;
            return (
              <tr
                key={r.id}
                onClick={() => onSelect(r)}
                className={`cursor-pointer transition-colors ${isSelected ? "bg-blue-950/40 border-l-2 border-blue-500" : "hover:bg-gray-800/30"}`}
              >
                <td className="py-1.5 px-2 text-gray-600 tabular-nums">{i + 1}</td>
                <td className="py-1.5 px-2">
                  <span className="font-mono font-semibold text-gray-100 tracking-wide">{r.symbol}</span>
                </td>
                <td className="py-1.5 px-2 text-gray-400 max-w-28 truncate" title={r.company_name}>{r.company_name}</td>
                <td className="py-1.5 px-2">
                  <span className={`inline-flex items-center rounded px-1 py-0.5 ${MCAP_BADGE[r.market_cap_category] ?? "bg-gray-800 text-gray-400"}`}>
                    {MCAP_LABEL[r.market_cap_category] ?? r.market_cap_category}
                  </span>
                </td>
                <td className="py-1.5 px-2 text-right tabular-nums text-gray-300">{r.close_price.toFixed(2)}</td>
                <td className={`py-1.5 px-2 text-right tabular-nums ${r.macd >= 0 ? "text-green-400" : "text-red-400"}`}>
                  {r.macd > 0 ? "+" : ""}{r.macd.toFixed(3)}
                </td>
                <td className={`py-1.5 px-2 text-right tabular-nums ${r.signal_line >= 0 ? "text-teal-400" : "text-orange-400"}`}>
                  {r.signal_line > 0 ? "+" : ""}{r.signal_line.toFixed(3)}
                </td>
                <td className="py-1.5 px-2 text-right tabular-nums font-semibold"
                  style={{ color: r.histogram > 0 ? "#4ade80" : r.histogram < 0 ? "#f87171" : "#6b7280" }}>
                  {r.histogram > 0 ? "+" : ""}{r.histogram.toFixed(3)}
                </td>
                <td className="py-1.5 px-2 text-center">
                  {r.histogram_direction === "INCREASING" ? <span className="text-green-400">↑</span>
                    : r.histogram_direction === "DECREASING" ? <span className="text-red-400">↓</span>
                    : <span className="text-gray-600">→</span>}
                </td>
                <td className="py-1.5 px-2 text-center text-[10px]"
                  style={{ color: r.zero_line_status === "ABOVE" ? "#4ade80" : r.zero_line_status === "BELOW" ? "#f87171" : "#6b7280" }}>
                  {r.zero_line_status === "ABOVE" ? "▲" : r.zero_line_status === "BELOW" ? "▼" : "—"}
                </td>
                <td className="py-1.5 px-2">
                  <span className={`inline-flex items-center gap-1 rounded px-1.5 py-0.5 font-medium ${macdStateBadge(r.macd_state)}`}>
                    <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${hCfg.dot}`} />
                    {macdStateLabel(r.macd_state)}
                  </span>
                </td>
                <td className="py-1.5 px-2 text-[10px] tabular-nums whitespace-nowrap">
                  {r.last_crossover_type ? (
                    <span style={{ color: r.last_crossover_type.startsWith("BULLISH") ? "#4ade80" : "#f87171" }}>
                      {r.last_crossover_type.startsWith("BULLISH") ? "↑" : "↓"}{" "}
                      {r.last_crossover_type.includes("BELOW") ? "< 0" : "> 0"}
                    </span>
                  ) : <span className="text-gray-700">—</span>}
                </td>
                <td className="py-1.5 px-2 text-right tabular-nums text-gray-500">
                  {r.last_crossover_bars_ago != null ? `${r.last_crossover_bars_ago}d` : "—"}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ─── Summary Cards ────────────────────────────────────────────────────────────

function SummaryCards({ results }: { results: MACDResult[] }) {
  const cards = [
    {
      label: "Strong Bullish",
      count: results.filter(r => r.macd_state === "STRONG_BULLISH").length,
      color: "#4ade80", bg: "rgba(74,222,128,0.08)",
    },
    {
      label: "Bullish Fading",
      count: results.filter(r => r.macd_state === "BULLISH_FADING").length,
      color: "#2dd4bf", bg: "rgba(45,212,191,0.08)",
    },
    {
      label: "Bull Cross",
      count: results.filter(r => r.last_crossover_type?.startsWith("BULLISH") && (r.last_crossover_bars_ago ?? 999) <= 5).length,
      color: "#86efac", bg: "rgba(134,239,172,0.08)",
    },
    {
      label: "Strong Bearish",
      count: results.filter(r => r.macd_state === "STRONG_BEARISH").length,
      color: "#f87171", bg: "rgba(248,113,113,0.08)",
    },
    {
      label: "Bearish Fading",
      count: results.filter(r => r.macd_state === "BEARISH_FADING").length,
      color: "#fb923c", bg: "rgba(251,146,60,0.08)",
    },
    {
      label: "Bear Cross",
      count: results.filter(r => r.last_crossover_type?.startsWith("BEARISH") && (r.last_crossover_bars_ago ?? 999) <= 5).length,
      color: "#fca5a5", bg: "rgba(252,165,165,0.08)",
    },
  ];

  return (
    <div className="grid grid-cols-6 gap-3">
      {cards.map(c => (
        <div key={c.label} className="rounded-lg border border-gray-800 p-3 text-center"
          style={{ background: c.bg }}>
          <div className="text-2xl font-bold tabular-nums" style={{ color: c.color }}>{c.count}</div>
          <div className="text-[10px] mt-0.5 font-medium" style={{ color: c.color + "bb" }}>{c.label}</div>
        </div>
      ))}
    </div>
  );
}

// ─── Quick Presets ────────────────────────────────────────────────────────────

type Preset = {
  label: string;
  histFilters: string[];
  crossFilters: string[];
  color: string;
};

const PRESETS: Preset[] = [
  { label: "Strong Bullish",      histFilters: ["STRONG_BULLISH"],              crossFilters: [], color: "#4ade80" },
  { label: "Bullish Fading",      histFilters: ["BULLISH_FADING"],              crossFilters: [], color: "#2dd4bf" },
  { label: "↑ Cross Below 0",     histFilters: [],                              crossFilters: ["BULLISH_BELOW_ZERO"], color: "#86efac" },
  { label: "↑ Cross Above 0",     histFilters: [],                              crossFilters: ["BULLISH_ABOVE_ZERO"], color: "#6ee7b7" },
  { label: "Bearish Fading",      histFilters: ["BEARISH_FADING"],              crossFilters: [], color: "#fb923c" },
  { label: "Strong Bearish",      histFilters: ["STRONG_BEARISH"],              crossFilters: [], color: "#f87171" },
  { label: "↓ Cross Above 0",     histFilters: [],                              crossFilters: ["BEARISH_ABOVE_ZERO"], color: "#fca5a5" },
  { label: "↓ Cross Below 0",     histFilters: [],                              crossFilters: ["BEARISH_BELOW_ZERO"], color: "#fda4af" },
];

// ─── Main Page ────────────────────────────────────────────────────────────────

export function MACDPage() {
  const init = loadSettings();

  const [universe,     setUniverse]     = useState(init.universe);
  const [source,       setSource]       = useState(init.source);
  const [fast,         setFast]         = useState(init.fast);
  const [slow,         setSlow]         = useState(init.slow);
  const [signalPeriod, setSignalPeriod] = useState(init.signalPeriod);
  const [oscMa,        setOscMa]        = useState(init.oscMa);
  const [sigMa,        setSigMa]        = useState(init.sigMa);
  const [timeframe,    setTimeframe]    = useState(init.timeframe);
  const [histFilters,  setHistFilters]  = useState<string[]>(init.histFilters);
  const [crossFilters,       setCrossFilters]       = useState<string[]>(init.crossFilters);
  const [crossBars,          setCrossBars]          = useState(init.crossBars);
  const [crossoverLookback,  setCrossoverLookback]  = useState(init.crossoverLookback);

  const [scanResult,  setScanResult]  = useState<MACDScanResult | null>(null);
  const [loading,     setLoading]     = useState(false);
  const [error,       setError]       = useState<string | null>(null);

  const [selectedRow, setSelectedRow] = useState<MACDResult | null>(null);
  const [chartData,   setChartData]   = useState<MACDChartData | null>(null);
  const [chartLoading, setChartLoading] = useState(false);

  // Persist settings on change
  useEffect(() => {
    saveSettings({ universe, source, fast, slow, signalPeriod, oscMa, sigMa, timeframe, histFilters, crossFilters, crossBars, crossoverLookback });
  }, [universe, source, fast, slow, signalPeriod, oscMa, sigMa, timeframe, histFilters, crossFilters, crossBars, crossoverLookback]);

  const handleScan = useCallback(async () => {
    setLoading(true);
    setError(null);
    setSelectedRow(null);
    setChartData(null);
    try {
      const res = await scanMACD({
        universe,
        source,
        fast,
        slow,
        signal_period: signalPeriod,
        osc_ma_type: oscMa,
        sig_ma_type: sigMa,
        timeframe,
        hist_filters: histFilters,
        cross_filters: crossFilters,
        cross_bars: crossoverLookback,
        crossover_lookback: crossoverLookback,
        limit: 500,
      });
      setScanResult(res);
    } catch (e) {
      setError((e as Error).message);
      setScanResult(null);
    } finally {
      setLoading(false);
    }
  }, [universe, source, fast, slow, signalPeriod, oscMa, sigMa, timeframe, histFilters, crossFilters, crossBars, crossoverLookback]);

  async function handleSelectRow(r: MACDResult) {
    setSelectedRow(r);
    setChartLoading(true);
    setChartData(null);
    try {
      const data = await getMACDChart({
        exchange: r.exchange,
        symbol: r.symbol,
        source,
        fast,
        slow,
        signal_period: signalPeriod,
        osc_ma_type: oscMa,
        sig_ma_type: sigMa,
        timeframe,
        num_bars: 80,
      });
      setChartData(data);
    } catch { /* chart optional */ }
    finally { setChartLoading(false); }
  }

  function applyPreset(p: Preset) {
    setHistFilters(p.histFilters);
    setCrossFilters(p.crossFilters);
  }

  function resetDefaults() {
    setSource(DEFAULTS.source);
    setFast(DEFAULTS.fast);
    setSlow(DEFAULTS.slow);
    setSignalPeriod(DEFAULTS.signalPeriod);
    setOscMa(DEFAULTS.oscMa);
    setSigMa(DEFAULTS.sigMa);
    setTimeframe(DEFAULTS.timeframe);
    setHistFilters([]);
    setCrossFilters([]);
    setCrossBars(DEFAULTS.crossBars);
    setCrossoverLookback(DEFAULTS.crossoverLookback);
  }

  function toggleHist(f: string) {
    setHistFilters(prev => prev.includes(f) ? prev.filter(x => x !== f) : [...prev, f]);
  }
  function toggleCross(f: string) {
    setCrossFilters(prev => {
      if (prev.includes(f)) return prev.filter(x => x !== f);
      // Selecting a specific sub-type removes the generic, and vice versa
      let next = [...prev, f];
      if (f === "BULLISH") next = next.filter(x => !x.startsWith("BULLISH_"));
      if (f === "BEARISH") next = next.filter(x => !x.startsWith("BEARISH_"));
      if (f.startsWith("BULLISH_")) next = next.filter(x => x !== "BULLISH");
      if (f.startsWith("BEARISH_")) next = next.filter(x => x !== "BEARISH");
      return next;
    });
  }

  const results = scanResult?.results ?? [];

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

          {/* MACD Settings */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <label className="text-xs font-semibold uppercase tracking-widest text-gray-500">MACD Settings</label>
              <button onClick={resetDefaults} className="text-[10px] text-gray-600 hover:text-gray-400">Reset</button>
            </div>
            <div className="space-y-2">
              <SelectInput label="Source"      value={source}       options={SOURCES}    onChange={setSource} />
              <NumInput    label="Fast"         value={fast}         min={2}   max={50}   onChange={setFast} />
              <NumInput    label="Slow"         value={slow}         min={3}   max={200}  onChange={setSlow} />
              <NumInput    label="Signal"       value={signalPeriod} min={1}   max={50}   onChange={setSignalPeriod} />
              <SelectInput label="Oscillator"  value={oscMa}        options={MA_TYPES}   onChange={setOscMa} />
              <SelectInput label="Signal MA"   value={sigMa}        options={MA_TYPES}   onChange={setSigMa} />
              <SelectInput label="Timeframe"   value={timeframe}    options={TIMEFRAMES} onChange={setTimeframe} />
            </div>
          </div>

          <div className="border-t border-gray-800" />

          {/* Quick Presets */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-widest text-gray-500 mb-2">Quick Presets</label>
            <div className="grid grid-cols-2 gap-1">
              {PRESETS.map(p => (
                <button key={p.label} onClick={() => applyPreset(p)}
                  className="rounded px-2 py-1.5 text-[10px] font-medium border border-gray-800 hover:border-gray-600 text-left transition-colors"
                  style={{ color: p.color }}>
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          <div className="border-t border-gray-800" />

          {/* Histogram Filter */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-widest text-gray-500 mb-2">Histogram Filter</label>
            <div className="space-y-0.5">
              <CheckToggle label="Strong Bullish"   checked={histFilters.includes("STRONG_BULLISH")} onChange={() => toggleHist("STRONG_BULLISH")} color="#4ade80" />
              <CheckToggle label="Bullish Fading"   checked={histFilters.includes("BULLISH_FADING")} onChange={() => toggleHist("BULLISH_FADING")} color="#2dd4bf" />
              <CheckToggle label="Strong Bearish"   checked={histFilters.includes("STRONG_BEARISH")} onChange={() => toggleHist("STRONG_BEARISH")} color="#f87171" />
              <CheckToggle label="Bearish Fading"   checked={histFilters.includes("BEARISH_FADING")} onChange={() => toggleHist("BEARISH_FADING")} color="#fb923c" />
              <CheckToggle label="Positive Histogram" checked={histFilters.includes("POSITIVE")}     onChange={() => toggleHist("POSITIVE")}       color="#86efac" />
              <CheckToggle label="Negative Histogram" checked={histFilters.includes("NEGATIVE")}     onChange={() => toggleHist("NEGATIVE")}       color="#fca5a5" />
            </div>
          </div>

          <div className="border-t border-gray-800" />

          {/* Crossover Filter */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-widest text-gray-500 mb-2">Crossover Filter</label>

            {/* Crossover detection window — always visible */}
            <div className="mb-3 rounded-md bg-gray-900/60 border border-gray-800 p-2.5 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] text-gray-400 font-medium">Detect crossovers within</span>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="number" min={1} max={50} value={crossoverLookback}
                  onChange={e => setCrossoverLookback(Math.max(1, Math.min(50, parseInt(e.target.value, 10) || 20)))}
                  className="w-14 bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs text-blue-300 font-semibold text-right tabular-nums focus:border-blue-500 focus:outline-none"
                />
                <span className="text-[11px] text-gray-500">bars back</span>
              </div>
              <p className="text-[10px] text-gray-600 leading-tight">
                Lower = more recent crossovers only. Set to 1 to catch only today's cross.
              </p>
            </div>

            <div className="space-y-0.5">
              <CheckToggle label="Bullish Crossover"   checked={crossFilters.includes("BULLISH")}          onChange={() => toggleCross("BULLISH")}          color="#4ade80" />
              <CheckToggle label="Bearish Crossover"   checked={crossFilters.includes("BEARISH")}          onChange={() => toggleCross("BEARISH")}          color="#f87171" />
              <CheckToggle label="↑ Cross Below Zero"  checked={crossFilters.includes("BULLISH_BELOW_ZERO")} onChange={() => toggleCross("BULLISH_BELOW_ZERO")} color="#86efac" />
              <CheckToggle label="↑ Cross Above Zero"  checked={crossFilters.includes("BULLISH_ABOVE_ZERO")} onChange={() => toggleCross("BULLISH_ABOVE_ZERO")} color="#6ee7b7" />
              <CheckToggle label="↓ Cross Above Zero"  checked={crossFilters.includes("BEARISH_ABOVE_ZERO")} onChange={() => toggleCross("BEARISH_ABOVE_ZERO")} color="#fca5a5" />
              <CheckToggle label="↓ Cross Below Zero"  checked={crossFilters.includes("BEARISH_BELOW_ZERO")} onChange={() => toggleCross("BEARISH_BELOW_ZERO")} color="#fda4af" />
            </div>
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

      {/* ── Main content ──────────────────────────────────────────────────── */}
      <main className="flex-1 min-w-0 overflow-y-auto p-5 space-y-4">

        {!scanResult && !loading && (
          <div className="flex flex-col items-center justify-center py-20 gap-3">
            <div className="text-4xl opacity-20">📊</div>
            <p className="text-gray-500 text-sm">Configure MACD settings, apply filters, then run the scan</p>
            <p className="text-gray-700 text-xs">
              Supports EMA/SMA · 7 source types · 4 histogram states · crossover detection with zero-line context
            </p>
          </div>
        )}

        {loading && (
          <div className="flex flex-col items-center justify-center py-20 gap-3">
            <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-gray-500 text-sm">Computing MACD for all stocks…</p>
            <p className="text-gray-700 text-xs">First run may take 30–60s · cached 4h</p>
          </div>
        )}

        {error && !loading && (
          <div className="rounded-lg border border-red-800 bg-red-950/50 px-4 py-3 text-sm text-red-300">
            <span className="font-medium">Error: </span>{error}
          </div>
        )}

        {scanResult && !loading && (
          <>
            {/* Stats bar */}
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>
                <span className="text-gray-300 font-medium">{scanResult.total_matched}</span> matched ·{" "}
                {scanResult.stocks_screened} screened · {scanResult.execution_time_ms.toFixed(0)}ms ·{" "}
                {timeframe} · {oscMa}/{sigMa} {fast}/{slow}/{signalPeriod}
              </span>
            </div>

            {/* Summary cards */}
            <SummaryCards results={results} />

            {/* Chart panel (shown when a stock is selected) */}
            {selectedRow && (
              <div className="rounded-lg border border-gray-800 p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="font-mono font-bold text-gray-100">{selectedRow.symbol}</span>
                    <span className="text-gray-500 text-xs ml-2">{selectedRow.company_name}</span>
                    <span className={`ml-3 text-xs inline-flex items-center gap-1 rounded px-1.5 py-0.5 font-medium ${macdStateBadge(selectedRow.macd_state)}`}>
                      {macdStateLabel(selectedRow.macd_state)}
                    </span>
                  </div>
                  <button onClick={() => { setSelectedRow(null); setChartData(null); }}
                    className="text-gray-600 hover:text-gray-300 text-lg leading-none">×</button>
                </div>
                <div className="flex gap-6 text-xs">
                  <span>MACD <span className={selectedRow.macd >= 0 ? "text-green-400" : "text-red-400"}>{selectedRow.macd > 0 ? "+" : ""}{selectedRow.macd.toFixed(4)}</span></span>
                  <span>Signal <span className={selectedRow.signal_line >= 0 ? "text-teal-400" : "text-orange-400"}>{selectedRow.signal_line > 0 ? "+" : ""}{selectedRow.signal_line.toFixed(4)}</span></span>
                  <span>Hist <span style={{ color: selectedRow.histogram > 0 ? "#4ade80" : "#f87171" }}>{selectedRow.histogram > 0 ? "+" : ""}{selectedRow.histogram.toFixed(4)}</span></span>
                  <span className="text-gray-500">Zero: <span style={{ color: selectedRow.zero_line_status === "ABOVE" ? "#4ade80" : "#f87171" }}>{selectedRow.zero_line_status}</span></span>
                </div>
                {chartLoading && <div className="text-gray-600 text-xs py-4 text-center animate-pulse">Loading chart…</div>}
                {chartData && <MACDChart data={chartData} />}
                {!chartLoading && !chartData && <div className="text-gray-700 text-xs py-2">Chart unavailable</div>}
              </div>
            )}

            {/* Results table */}
            {results.length > 0 ? (
              <MACDTable results={results} onSelect={handleSelectRow} selectedId={selectedRow?.id ?? null} />
            ) : (
              <div className="py-10 text-center text-gray-600 text-sm">No stocks matched the selected filters</div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
