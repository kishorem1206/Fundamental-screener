import { useState, useCallback } from "react";
import type { Universe, DivergenceScanResult, MACDScanResult } from "./types";
import { fetchUniverses, scanRSIDivergence, scanMACD } from "./api";
import { loadRsiDivSettings } from "./components/RSIDivergencePage";
import ChatPanel from "./components/ChatPanel";
import { RSIMomentumPage } from "./components/RSIMomentumPage";
import { RSIDivergencePage } from "./components/RSIDivergencePage";
import { MACDPage } from "./components/MACDPage";
import { TVScreenerPage } from "./components/TVScreenerPage";
import { useEffect } from "react";
import "./technical.css";

const UNIVERSE_LABELS: Record<string, string> = {
  NIFTY_50: "Nifty 50",
  NIFTY_500: "Nifty 500",
  NIFTY_TOTAL_MARKET: "Total Market",
};

const MACD_LS_KEY = "macd_page_settings_v1";

function loadMacdUniverse(): string {
  try {
    const raw = localStorage.getItem(MACD_LS_KEY);
    if (raw) return (JSON.parse(raw) as { universe?: string }).universe ?? "NIFTY_500";
  } catch { /* ignore */ }
  return "NIFTY_500";
}

type Tab = "screen" | "momentum" | "divergence" | "macd" | "tv" | "chat";

// ─── Combined row type ────────────────────────────────────────────────────────

interface CombinedRow {
  symbol:             string;
  exchange:           string;
  company_name:       string;
  sector:             string;
  market_cap_category: string;
  // RSI Divergence fields (if matched)
  divType?:           string;
  divP2Date?:         string;
  divP2Rsi?:          number;
  divBars?:           number;
  divStrength?:       number;
  // MACD fields (if matched)
  macdState?:         string;
  macdCross?:         string;
  macdCrossLoc?:      string;
  macdHistogram?:     number;
  // match flags
  hasDiv:  boolean;
  hasMacd: boolean;
}

const DIV_TYPE_LABELS: Record<string, string> = {
  REGULAR_BULLISH: "Reg. Bullish",
  REGULAR_BEARISH: "Reg. Bearish",
  HIDDEN_BULLISH:  "Hidden Bull",
  HIDDEN_BEARISH:  "Hidden Bear",
};

const MCAP_BADGE: Record<string, string> = {
  LARGE_CAP: "bg-blue-900/50 text-blue-300 border-blue-800",
  MID_CAP:   "bg-purple-900/50 text-purple-300 border-purple-800",
  SMALL_CAP: "bg-yellow-900/50 text-yellow-300 border-yellow-800",
  MICRO_CAP: "bg-gray-800 text-gray-400 border-gray-700",
};
const MCAP_LABEL: Record<string, string> = {
  LARGE_CAP: "Large", MID_CAP: "Mid", SMALL_CAP: "Small", MICRO_CAP: "Micro",
};

function histColor(v: number | undefined): string {
  if (v === undefined) return "text-gray-500";
  return v > 0 ? "text-emerald-400" : "text-red-400";
}

export default function TechnicalScreener() {
  const [tab, setTab] = useState<Tab>("screen");
  const [universes, setUniverses] = useState<Universe[]>([]);
  const [selectedUniverse, setSelectedUniverse] = useState("NIFTY_500");

  // Toggle state
  const [useDiv,  setUseDiv]  = useState(false);
  const [useMacd, setUseMacd] = useState(false);

  // Scan state
  const [rows,    setRows]    = useState<CombinedRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);
  const [meta,    setMeta]    = useState<{ divTotal: number; macdTotal: number; ms: number } | null>(null);

  useEffect(() => {
    fetchUniverses().then(setUniverses).catch(() => {});
  }, []);

  const handleRun = useCallback(async () => {
    if (!useDiv && !useMacd) return;
    setLoading(true);
    setError(null);
    setRows([]);
    setMeta(null);

    const t0 = performance.now();

    try {
      const [divRes, macdRes] = await Promise.all([
        useDiv
          ? ((): Promise<DivergenceScanResult> => {
              const s = loadRsiDivSettings();
              return scanRSIDivergence({
                universe:           selectedUniverse,
                timeframe:          s.timeframe,
                pivot_left:         s.pivotLeft,
                pivot_right:        s.pivotRight,
                max_recency_bars:   s.maxRecencyBars,
                min_bars_between:   s.minBarsBetween,
                max_bars_between:   s.maxBarsBetween,
                min_rsi_change:     s.minRsiChange,
                min_price_chg_pct:  s.minPriceChgPct,
                max_pivot_rsi:      s.maxPivotRsi ?? undefined,
                min_pivot_rsi:      s.minPivotRsi ?? undefined,
                require_rsi_rising: s.requireRsiRising,
                div_types:          s.divTypes,
                limit: 500,
              });
            })()
          : Promise.resolve(null),

        useMacd
          ? ((): Promise<MACDScanResult> => {
              // localStorage stores camelCase keys (matching MACDSettings interface)
              let ms: {
                source?: string; fast?: number; slow?: number;
                signalPeriod?: number; oscMa?: string; sigMa?: string;
                timeframe?: string; histFilters?: string[];
                crossFilters?: string[]; crossoverLookback?: number;
              } = {};
              try {
                const raw = localStorage.getItem(MACD_LS_KEY);
                if (raw) ms = JSON.parse(raw) as typeof ms;
              } catch { /* ignore */ }
              return scanMACD({
                universe:           selectedUniverse,
                source:             ms.source,
                fast:               ms.fast,
                slow:               ms.slow,
                signal_period:      ms.signalPeriod,
                osc_ma_type:        ms.oscMa,
                sig_ma_type:        ms.sigMa,
                timeframe:          ms.timeframe,
                hist_filters:       ms.histFilters,
                cross_filters:      ms.crossFilters,
                crossover_lookback: ms.crossoverLookback,
                limit: 500,
              });
            })()
          : Promise.resolve(null),
      ]);

      // Build combined rows — keyed by symbol, union of both scans
      const map = new Map<string, CombinedRow>();

      if (divRes) {
        for (const d of divRes.divergences) {
          map.set(d.symbol, {
            symbol:              d.symbol,
            exchange:            d.exchange,
            company_name:        d.company_name,
            sector:              d.sector,
            market_cap_category: d.market_cap_category,
            divType:     d.div_type,
            divP2Date:   d.pivot2_date,
            divP2Rsi:    d.pivot2_rsi,
            divBars:     d.bars_between,
            divStrength: d.strength_score,
            hasDiv: true, hasMacd: false,
          });
        }
      }

      if (macdRes) {
        for (const m of macdRes.results) {
          const existing = map.get(m.symbol);
          if (existing) {
            existing.hasMacd     = true;
            existing.macdState   = m.macd_state;
            existing.macdCross   = m.last_crossover_type ?? undefined;
            existing.macdCrossLoc= m.crossover_location ?? undefined;
            existing.macdHistogram = m.histogram;
          } else {
            map.set(m.symbol, {
              symbol:              m.symbol,
              exchange:            m.exchange,
              company_name:        m.company_name,
              sector:              m.sector,
              market_cap_category: m.market_cap_category,
              macdState:    m.macd_state,
              macdCross:    m.last_crossover_type ?? undefined,
              macdCrossLoc: m.crossover_location ?? undefined,
              macdHistogram: m.histogram,
              hasDiv: false, hasMacd: true,
            });
          }
        }
      }

      // Sort: both first, div-only second, macd-only third
      const sorted = [...map.values()].sort((a, b) => {
        const sa = (a.hasDiv ? 2 : 0) + (a.hasMacd ? 1 : 0);
        const sb = (b.hasDiv ? 2 : 0) + (b.hasMacd ? 1 : 0);
        return sb - sa;
      });

      setRows(sorted);
      setMeta({
        divTotal:  divRes?.total_matched  ?? 0,
        macdTotal: macdRes?.total_matched ?? 0,
        ms: Math.round(performance.now() - t0),
      });
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [selectedUniverse, useDiv, useMacd]);

  const bothCount = rows.filter((r) => r.hasDiv && r.hasMacd).length;

  function downloadCsv() {
    if (!rows.length) return;
    const headers = [
      "Symbol", "Exchange", "Company", "Sector", "Cap",
      ...(useDiv  ? ["DIV Match", "Pattern", "P2 Date", "P2 RSI", "Bars Between", "Strength"] : []),
      ...(useMacd ? ["MACD Match", "MACD State", "Cross", "Histogram"] : []),
    ];
    const escape = (v: unknown) => {
      const s = String(v ?? "");
      return s.includes(",") || s.includes('"') || s.includes("\n") ? `"${s.replace(/"/g, '""')}"` : s;
    };
    const csvRows = rows.map(r => [
      r.symbol, r.exchange, r.company_name, r.sector, r.market_cap_category,
      ...(useDiv  ? [r.hasDiv ? "Yes" : "No", r.divType ?? "", r.divP2Date ?? "", r.divP2Rsi ?? "", r.divBars ?? "", r.divStrength ?? ""] : []),
      ...(useMacd ? [r.hasMacd ? "Yes" : "No", r.macdState ?? "", r.macdCross ?? "", r.macdHistogram ?? ""] : []),
    ].map(escape).join(","));
    const csv = [headers.join(","), ...csvRows].join("\n");
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    a.download = `screen_${selectedUniverse}_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
  }

  return (
    <div className="technical-root overflow-hidden flex flex-col" style={{ height: "calc(100vh - 65px)" }}>
      {/* Header */}
      <header
        className="px-5 py-3 flex items-center justify-between shrink-0"
        style={{ borderBottom: "1px solid var(--border-subtle)", background: "rgba(10,16,32,0.85)", backdropFilter: "blur(12px)" }}
      >
        <div className="flex items-center gap-3">
          <h1 className="text-sm font-semibold tracking-tight" style={{ color: "var(--text-primary)" }}>
            Technical Screener
          </h1>
          <span className="text-xs font-mono" style={{ color: "var(--text-dim)" }}>India · NSE/BSE</span>
        </div>
        <div
          className="flex items-center gap-1 rounded-xl p-1"
          style={{ background: "rgba(255,255,255,0.04)", border: "1px solid var(--border-subtle)" }}
        >
          {(["screen", "momentum", "divergence", "macd", "tv", "chat"] as const).map((t) => {
            const labels: Record<Tab, string> = { screen: "Screen", momentum: "RSI Momentum", divergence: "RSI Divergence", macd: "MACD", tv: "TradingView", chat: "AI Chat" };
            const isActive = tab === t;
            return (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 ${isActive ? "tab-active" : ""}`}
                style={isActive ? {} : { color: "var(--text-muted)" }}
                onMouseEnter={(e) => { if (!isActive) (e.currentTarget as HTMLButtonElement).style.color = "var(--text-primary)"; }}
                onMouseLeave={(e) => { if (!isActive) (e.currentTarget as HTMLButtonElement).style.color = "var(--text-muted)"; }}
              >
                {labels[t]}
              </button>
            );
          })}
        </div>
        <span className="w-24" />
      </header>

      {/* Body */}
      <div className="flex flex-1 min-h-0">
        {tab === "screen" ? (
          <>
            {/* Sidebar */}
            <aside className="w-56 shrink-0 border-r border-gray-800 flex flex-col overflow-y-auto">
              <div className="p-4 space-y-5">
                {/* Universe */}
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-widest text-gray-500 mb-2">
                    Universe
                  </label>
                  <div className="space-y-1">
                    {(universes.length > 0
                      ? universes
                      : Object.entries(UNIVERSE_LABELS).map(([id, name]) => ({ id, name, description: "", stockCount: 0 }))
                    ).map((u) => (
                      <button
                        key={u.id}
                        onClick={() => setSelectedUniverse(u.id)}
                        className={`w-full text-left rounded-md px-3 py-2 text-xs transition-colors ${
                          selectedUniverse === u.id
                            ? "bg-blue-600/20 text-blue-300 border border-blue-700/50"
                            : "text-gray-400 hover:bg-gray-800 hover:text-gray-200 border border-transparent"
                        }`}
                      >
                        <div className="font-medium">{UNIVERSE_LABELS[u.id] ?? u.name}</div>
                        {u.stockCount > 0 && <div className="text-gray-600 mt-0.5">{u.stockCount} stocks</div>}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="border-t border-gray-800" />

                {/* Scan toggles */}
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-widest text-gray-500 mb-3">
                    Include Scanners
                  </label>
                  <div className="space-y-2">
                    {/* RSI Divergence toggle */}
                    <button
                      onClick={() => setUseDiv((v) => !v)}
                      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg border text-xs font-medium transition-all ${
                        useDiv
                          ? "bg-emerald-900/30 border-emerald-700/50 text-emerald-300"
                          : "border-gray-800 text-gray-500 hover:border-gray-700 hover:text-gray-400"
                      }`}
                    >
                      <span className={`w-4 h-4 rounded flex items-center justify-center border flex-shrink-0 ${useDiv ? "bg-emerald-500 border-emerald-400" : "border-gray-700"}`}>
                        {useDiv && <span className="text-white text-xs leading-none">✓</span>}
                      </span>
                      <span>RSI Divergence</span>
                    </button>

                    {/* MACD toggle */}
                    <button
                      onClick={() => setUseMacd((v) => !v)}
                      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg border text-xs font-medium transition-all ${
                        useMacd
                          ? "bg-blue-900/30 border-blue-700/50 text-blue-300"
                          : "border-gray-800 text-gray-500 hover:border-gray-700 hover:text-gray-400"
                      }`}
                    >
                      <span className={`w-4 h-4 rounded flex items-center justify-center border flex-shrink-0 ${useMacd ? "bg-blue-500 border-blue-400" : "border-gray-700"}`}>
                        {useMacd && <span className="text-white text-xs leading-none">✓</span>}
                      </span>
                      <span>MACD</span>
                    </button>
                  </div>

                  {(useDiv || useMacd) && (
                    <p className="mt-2 text-xs text-gray-600">
                      Uses your saved settings from each page.
                    </p>
                  )}
                </div>

                {/* Run */}
                <button
                  onClick={() => void handleRun()}
                  disabled={loading || (!useDiv && !useMacd)}
                  className="w-full rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed px-4 py-2.5 text-sm font-semibold text-white transition-colors"
                >
                  {loading ? "Scanning…" : "Run Screen"}
                </button>

                {!useDiv && !useMacd && (
                  <p className="text-xs text-gray-700 text-center">Enable at least one scanner</p>
                )}
              </div>
            </aside>

            {/* Main content */}
            <main className="flex-1 overflow-y-auto p-5">
              {/* Empty state */}
              {!loading && !error && rows.length === 0 && (
                <div className="flex flex-col items-center justify-center h-full text-center gap-3">
                  <div className="text-4xl opacity-20">📊</div>
                  <p className="text-gray-500 text-sm">Toggle the scanners you want, then run</p>
                  <p className="text-gray-700 text-xs">Settings are taken from the RSI Divergence and MACD pages</p>
                </div>
              )}

              {/* Loading */}
              {loading && (
                <div className="flex flex-col items-center justify-center h-full gap-3">
                  <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                  <p className="text-gray-500 text-sm">Running{useDiv && useMacd ? " both scanners" : useDiv ? " RSI Divergence" : " MACD"} on {selectedUniverse.replace(/_/g, " ")}…</p>
                  <p className="text-gray-700 text-xs">First run may take 30–60 s · results cached for 4 h</p>
                </div>
              )}

              {/* Error */}
              {error && !loading && (
                <div className="rounded-lg border border-red-800 bg-red-950/50 px-4 py-3 text-sm text-red-300 max-w-xl">
                  <span className="font-medium">Error: </span>{error}
                </div>
              )}

              {/* Results */}
              {!loading && rows.length > 0 && (
                <div className="flex flex-col gap-3">
                  {/* Stats bar */}
                  <div className="flex items-center gap-4 text-xs text-gray-500 flex-wrap">
                    <span>
                      <span className="text-gray-200 font-medium">{rows.length}</span> stocks
                      {useDiv && useMacd && bothCount > 0 && (
                        <span className="ml-2 text-yellow-400 font-semibold">· {bothCount} match both ✦</span>
                      )}
                    </span>
                    {useDiv  && <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-400 inline-block" /><span className="text-emerald-400">{meta?.divTotal ?? 0} RSI div</span></span>}
                    {useMacd && <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-blue-400 inline-block" /><span className="text-blue-400">{meta?.macdTotal ?? 0} MACD</span></span>}
                    <span className="ml-auto flex items-center gap-3 text-gray-600">
                      <span>{meta?.ms ?? 0} ms · {selectedUniverse.replace(/_/g, " ")}</span>
                      <button
                        onClick={downloadCsv}
                        className="flex items-center gap-1 px-2 py-1 rounded border border-gray-700 text-gray-400 hover:border-gray-500 hover:text-gray-200 transition-colors"
                      >
                        ↓ CSV
                      </button>
                    </span>
                  </div>

                  {/* Table */}
                  <div className="overflow-x-auto rounded-lg border border-gray-800">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b border-gray-800 bg-gray-900/60 text-gray-500 uppercase tracking-wider">
                          <th className="py-2.5 px-3 text-left w-8">#</th>
                          <th className="py-2.5 px-3 text-left">Symbol</th>
                          <th className="py-2.5 px-3 text-left">Company</th>
                          <th className="py-2.5 px-3 text-left">Cap</th>
                          <th className="py-2.5 px-3 text-left">Sector</th>
                          {useDiv && <>
                            <th className="py-2.5 px-3 text-left">Pattern</th>
                            <th className="py-2.5 px-3 text-right">P2 Date</th>
                            <th className="py-2.5 px-3 text-right">P2 RSI</th>
                            <th className="py-2.5 px-3 text-right">Bars</th>
                            <th className="py-2.5 px-3 text-right">Strength</th>
                          </>}
                          {useMacd && <>
                            <th className="py-2.5 px-3 text-left">MACD State</th>
                            <th className="py-2.5 px-3 text-left">Cross</th>
                            <th className="py-2.5 px-3 text-right">Histogram</th>
                          </>}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-800/50">
                        {rows.map((row, i) => {
                          const rowBg = row.hasDiv && row.hasMacd
                            ? "bg-yellow-950/20 hover:bg-yellow-950/30"
                            : "hover:bg-gray-800/30";
                          return (
                            <tr key={`${row.exchange}:${row.symbol}`} className={`transition-colors ${rowBg}`}>
                              <td className="py-2.5 px-3 text-gray-600 tabular-nums">{i + 1}</td>
                              <td className="py-2.5 px-3">
                                <div className="flex items-center gap-1.5 flex-wrap">
                                  <span className="font-mono font-semibold text-gray-100 tracking-wide">{row.symbol}</span>
                                  {row.hasDiv  && <span className="rounded px-1 py-0.5 font-medium bg-emerald-900/60 text-emerald-300 border border-emerald-800/50">DIV</span>}
                                  {row.hasMacd && <span className="rounded px-1 py-0.5 font-medium bg-blue-900/60 text-blue-300 border border-blue-800/50">MACD</span>}
                                </div>
                              </td>
                              <td className="py-2.5 px-3 text-gray-400 max-w-44 truncate" title={row.company_name}>{row.company_name}</td>
                              <td className="py-2.5 px-3">
                                <span className={`inline-flex items-center rounded px-1.5 py-0.5 border ${MCAP_BADGE[row.market_cap_category] ?? "bg-gray-800 text-gray-400 border-gray-700"}`}>
                                  {MCAP_LABEL[row.market_cap_category] ?? row.market_cap_category}
                                </span>
                              </td>
                              <td className="py-2.5 px-3 text-gray-500 max-w-36 truncate" title={row.sector}>{row.sector}</td>
                              {useDiv && <>
                                <td className="py-2.5 px-3 text-gray-400">{row.divType ? (DIV_TYPE_LABELS[row.divType] ?? row.divType) : <span className="text-gray-700">—</span>}</td>
                                <td className="py-2.5 px-3 text-right tabular-nums text-gray-300">{row.divP2Date ?? <span className="text-gray-700">—</span>}</td>
                                <td className="py-2.5 px-3 text-right tabular-nums text-green-400">{row.divP2Rsi?.toFixed(1) ?? <span className="text-gray-700">—</span>}</td>
                                <td className="py-2.5 px-3 text-right tabular-nums text-gray-400">{row.divBars ?? <span className="text-gray-700">—</span>}</td>
                                <td className="py-2.5 px-3 text-right tabular-nums text-gray-300">{row.divStrength?.toFixed(1) ?? <span className="text-gray-700">—</span>}</td>
                              </>}
                              {useMacd && <>
                                <td className="py-2.5 px-3 text-gray-400">{row.macdState ?? <span className="text-gray-700">—</span>}</td>
                                <td className="py-2.5 px-3 text-gray-400">
                                  {row.macdCross
                                    ? <span>{row.macdCross.startsWith("BULLISH") ? "↑" : "↓"} {row.macdCrossLoc?.replace("_", " ").toLowerCase()}</span>
                                    : <span className="text-gray-700">—</span>}
                                </td>
                                <td className={`py-2.5 px-3 text-right tabular-nums ${histColor(row.macdHistogram)}`}>
                                  {row.macdHistogram !== undefined ? row.macdHistogram.toFixed(2) : <span className="text-gray-700">—</span>}
                                </td>
                              </>}
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </main>
          </>
        ) : tab === "momentum" ? (
          <RSIMomentumPage />
        ) : tab === "divergence" ? (
          <RSIDivergencePage />
        ) : tab === "macd" ? (
          <MACDPage />
        ) : tab === "tv" ? (
          <TVScreenerPage />
        ) : (
          <div className="flex-1 min-h-0">
            <ChatPanel />
          </div>
        )}
      </div>
    </div>
  );
}
