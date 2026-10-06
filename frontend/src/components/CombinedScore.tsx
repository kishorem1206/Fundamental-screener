import { Fragment, useEffect, useState } from "react";
import { ArrowDown, ArrowUp, ChevronDown, ChevronRight } from "lucide-react";
import { api } from "../api";

// Combined Score — the framework's scores side by side, never blended into one
// number (Important md files/stock_quality_portfolio_replacement_agent_framework.md,
// section 1). A score column fills in when the phase that builds it lands.

type ScoreKey = "quality" | "fundamental" | "quantitative" | "relative_strength" | "technical" | "valuation";

export interface FrameworkScoreRow {
  stock_id: string;
  symbol: string;
  company_name: string;
  sector: string | null;
  market_cap: number | null;
  as_of: string;
  basis: "QUICK" | "FULL";
  latest_fy: string | null;
  trend: string | null;
  classification: string | null;
  action: string | null;
  quality: number | null;
  business_quality: number | null;
  fundamental: number | null;
  quantitative: number | null;
  relative_strength: number | null;
  technical: number | null;
  valuation: number | null;
  valuation_view: string | null;
  quality_change_6m: number | null;
  quality_change_12m: number | null;
  quality_direction: string | null;
  sector_rank?: { rank: number; of: number; top_pct: number; label: string; sector: string } | null;
}

type Part = { score: number | null; weight?: number; reason?: string; note?: string; source?: string; basis?: string; [k: string]: unknown };

type Alt = { symbol: string; company_name: string; classification: string; action: string; quality: number | null;
  fundamental: number | null; relative_strength: number | null; technical: number | null; valuation: number | null; valuation_view: string | null };

const CLASS_COLOR: Record<string, string> = {
  "Core Quality": "#4fb3a0", "Investable": "#7fb8ff", "Improving / Watch": "#e8c766", "Recovery Candidate": "#e8c766",
  "Tactical Only": "#e0793c", "Replacement Candidate": "#d9694f", "Avoid": "#d9694f",
};

export interface FrameworkStockDetail extends FrameworkScoreRow {
  best_alternative?: Alt | null;
  replacement?: { existing: string; candidate: string; differences: Record<string, number | null>; why_better: string[];
    valuation: { existing: string | null; candidate: string | null };
    risk: { existing: Record<string, number | null>; candidate: Record<string, number | null> } } | null;
  detail: {
    quality?: { score: number | null; band: string | null; formula?: string; capped?: string; governance_red_flag?: string };
    business_quality?: { score: number | null; coverage: number; components: Record<string, Part>; not_measured: string[]; source: string | null; years_on_record: number };
    fundamental?: { score: number | null; coverage: number; components: Record<string, Part>; double_in: Record<string, unknown>; long_run_growth: Part | null };
    trend?: { trend: string; reason?: string; signals: { signal: string; reading: string; vote: number }[] };
    decision?: { classification: string | null; action: string | null; size: string | null; matrix: string | null; why: string[];
      gates: { core: boolean; preferred: boolean; recovery: boolean; tactical: boolean; red_flags: string[] };
      interpretation: { strong: string[]; weak: string[]; improving: string[]; deteriorating: string[]; performance: string | null; why: string[] | null } };
    momentum?: { direction: string; current?: number;
      "6m"?: { quality: number | null; change: number | null; method: string; as_of?: string; reason?: string };
      "12m"?: { quality: number | null; change: number | null; method: string; as_of?: string; reason?: string } };
    technical?: { score: number | null; reason?: string; components: Record<string, Part>; as_of?: string };
    valuation?: { score: number | null; view: string | null; reason?: string; interpretation?: string; components: Record<string, Part>;
      pe: number | null; market_cap_cr: number; market_cap_source: string; ttm_profit_cr: number | null; ttm_note?: string | null; as_of?: string };
    quantitative?: { score: number | null; coverage: number; components: Record<string, Part>; not_measured: string[]; as_of: string | null };
    relative_strength?: { score: number | null; reason?: string; components: Record<string, Part>; as_of?: string;
      why_holding_up?: { sector_weak_over: string[]; stock_ahead_of_sector_over: string[]; reasons: string[] } };
  };
}

export interface FrameworkScoresResponse {
  total: number;
  scores: FrameworkScoreRow[];
  sectors: string[];
}

const SCORES: { key: ScoreKey; label: string; question: string; pending?: string }[] = [
  { key: "quality", label: "Quality", question: "Is this a good business? 70% Fundamental + 30% Business Quality. 50 is the gate, 65+ preferred." },
  { key: "fundamental", label: "Fundamental", question: "Are the financial numbers strong?" },
  { key: "quantitative", label: "Quantitative", question: "Are the measurable numbers getting better or worse? Changes in growth, margins, returns and debt, plus price volatility and drawdown." },
  { key: "relative_strength", label: "Rel. strength", question: "Is it beating the Nifty 50, its sector and same-sector stocks, and holding up when the market falls?" },
  { key: "technical", label: "Technical", question: "Is price behaviour confirming strength or reversal? Trend structure, moving averages, RSI, MACD, volume, breakout, base, divergence." },
  { key: "valuation", label: "Valuation", question: "Is the price reasonable? Higher is cheaper: P/E against its own history and its industry, PEG, EV/EBITDA, free-cash-flow yield, deep-report value." },
];

const TRENDS: Record<string, { label: string; color: string }> = {
  IMPROVING: { label: "Improving", color: "#4fb3a0" },
  STABLE: { label: "Stable", color: "#a9b3c9" },
  CYCLICAL: { label: "Cyclical", color: "#e8c766" },
  DECLINING: { label: "Declining", color: "#d9694f" },
  INSUFFICIENT_DATA: { label: "Not enough data", color: "#6f7c96" },
};

// The framework's own bands (section 2): 65+ strong, 50 the practical gate, below 40 weak.
const scoreColor = (v: number | null) =>
  v === null ? "var(--text-dim)" : v >= 65 ? "#4fb3a0" : v >= 50 ? "#c9a227" : v >= 40 ? "#e0793c" : "#d9694f";

const PAGE = 50;

interface Props {
  onAnalyse?: (stockId: string) => void;
}

export default function CombinedScore({ onAnalyse }: Props) {
  const [data, setData] = useState<FrameworkScoresResponse | null>(null);
  const [error, setError] = useState("");
  const [q, setQ] = useState("");
  const [sector, setSector] = useState("");
  const [trend, setTrend] = useState("");
  const [sort, setSort] = useState<ScoreKey | "market_cap" | "quality_change_12m">("quality");
  const [direction, setDirection] = useState("");
  const [cls, setCls] = useState("");
  const [open, setOpen] = useState<string | null>(null);
  const [order, setOrder] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(0);

  useEffect(() => { setPage(0); }, [q, sector, trend, direction, cls, sort, order]);

  useEffect(() => {
    const params: Record<string, string> = { sort, order, limit: String(PAGE), offset: String(page * PAGE) };
    if (q.trim()) params.q = q.trim();
    if (sector) params.sector = sector;
    if (trend) params.trend = trend;
    if (direction) params.direction = direction;
    if (cls) params.classification = cls;
    const t = setTimeout(() => {
      api.getFrameworkScores(params).then((r) => { setData(r); setError(""); })
        .catch((e: unknown) => setError(e instanceof Error ? e.message : "Could not load scores"));
    }, 200);
    return () => clearTimeout(t);
  }, [q, sector, trend, direction, cls, sort, order, page]);

  const sortBy = (key: ScoreKey | "market_cap" | "quality_change_12m") => {
    if (sort === key) setOrder(order === "desc" ? "asc" : "desc");
    else { setSort(key); setOrder("desc"); }
  };
  const Arrow = order === "desc" ? ArrowDown : ArrowUp;
  const inputStyle = { background: "var(--bg-input)", border: "1px solid var(--border-subtle)", color: "var(--text-primary)" };

  return (
    <div className="space-y-6 fade-in">
      <div className="card-rich p-6">
        <p className="eyebrow">Combined score</p>
        <h1 className="text-xl font-semibold mb-1" style={{ color: "var(--text-primary)" }}>
          Six scores, side by side
        </h1>
        <p className="text-sm max-w-3xl" style={{ color: "var(--text-secondary)" }}>
          Each score answers its own question and they are never averaged: a strong chart cannot repair weak
          fundamentals, and a cheap price cannot repair a weak business. Quality is the first gate: 50 to invest,
          65 and above preferred. Open a row to see every input and where it came from; the remaining columns fill
          in as they are built.
        </p>
      </div>

      <div className="card-rich p-4">
        <div className="flex flex-wrap items-center gap-3 mb-4">
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Filter by name or symbol"
                 className="rounded-lg px-3 py-2 text-sm w-64" style={inputStyle} />
          <select value={sector} onChange={(e) => setSector(e.target.value)} className="rounded-lg px-3 py-2 text-sm" style={inputStyle}>
            <option value="">All sectors</option>
            {(data?.sectors ?? []).map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
          <select value={trend} onChange={(e) => setTrend(e.target.value)} className="rounded-lg px-3 py-2 text-sm" style={inputStyle}>
            <option value="">Any trend</option>
            {Object.entries(TRENDS).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
          </select>
          <select value={cls} onChange={(e) => setCls(e.target.value)} className="rounded-lg px-3 py-2 text-sm" style={inputStyle}>
            <option value="">Any classification</option>
            {Object.keys(CLASS_COLOR).map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
          <select value={direction} onChange={(e) => setDirection(e.target.value)} className="rounded-lg px-3 py-2 text-sm" style={inputStyle}>
            <option value="">Any quality momentum</option>
            <option value="IMPROVING">Quality improving</option>
            <option value="STABLE">Quality stable</option>
            <option value="DECLINING">Quality declining</option>
          </select>
          <span className="text-xs ml-auto" style={{ color: "var(--text-dim)" }}>
            {data ? `${data.total.toLocaleString("en-IN")} stocks` : "Loading…"}
          </span>
        </div>

        {error && <div className="text-sm mb-3" style={{ color: "var(--accent-red)" }}>{error}</div>}

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr style={{ color: "var(--text-dim)", borderBottom: "1px solid var(--border-subtle)" }}>
                <th className="text-left py-2 px-2 text-xs font-medium">Stock</th>
                <th className="text-left py-2 px-2 text-xs font-medium" title="Classification and action from the framework's gates and decision matrix">Decision</th>
                {SCORES.map((s) => (
                  <th key={s.key} className="text-right py-2 px-2 text-xs font-medium" title={s.question}>
                    {s.pending ? (
                      <span title={`${s.question} Built in ${s.pending}.`}>{s.label}</span>
                    ) : (
                      <button onClick={() => sortBy(s.key)} className="inline-flex items-center gap-1"
                              style={{ color: sort === s.key ? "var(--accent-gold-bright)" : "inherit" }}>
                        {s.label}{sort === s.key && <Arrow className="h-3 w-3" />}
                      </button>
                    )}
                  </th>
                ))}
                <th className="text-right py-2 px-2 text-xs font-medium" title="Quality now against 12 months ago (6 months in brackets)">
                  <button onClick={() => sortBy("quality_change_12m")} className="inline-flex items-center gap-1"
                          style={{ color: sort === "quality_change_12m" ? "var(--accent-gold-bright)" : "inherit" }}>
                    Quality momentum{sort === "quality_change_12m" && <Arrow className="h-3 w-3" />}
                  </button>
                </th>
                <th className="text-left py-2 px-2 text-xs font-medium" title="Rank of Quality within the stock's sector">Sector rank</th>
                <th className="text-left py-2 px-2 text-xs font-medium">Business trend</th>
                <th className="text-right py-2 px-2 text-xs font-medium">
                  <button onClick={() => sortBy("market_cap")} className="inline-flex items-center gap-1"
                          style={{ color: sort === "market_cap" ? "var(--accent-gold-bright)" : "inherit" }}>
                    Mkt cap (₹ cr){sort === "market_cap" && <Arrow className="h-3 w-3" />}
                  </button>
                </th>
                <th className="text-right py-2 px-2 text-xs font-medium">Basis</th>
              </tr>
            </thead>
            <tbody>
              {(data?.scores ?? []).map((r) => {
                const t = r.trend ? TRENDS[r.trend] : null;
                const isOpen = open === r.symbol;
                return (
                  <Fragment key={r.stock_id}>
                  <tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                    <td className="py-2 px-2">
                      <button onClick={() => setOpen(isOpen ? null : r.symbol)} className="text-left flex items-start gap-1.5"
                              title="Show the inputs behind these scores">
                        {isOpen ? <ChevronDown className="h-3.5 w-3.5 mt-1" /> : <ChevronRight className="h-3.5 w-3.5 mt-1" />}
                        <span>
                        <div className="font-medium" style={{ color: "var(--text-primary)" }}>{r.symbol}</div>
                        <div className="text-xs truncate max-w-56" style={{ color: "var(--text-dim)" }}>
                          {r.company_name} · {r.sector ?? "—"}
                        </div>
                        </span>
                      </button>
                    </td>
                    <td className="py-2 px-2 text-xs">
                      <div style={{ color: r.classification ? CLASS_COLOR[r.classification] : "var(--text-dim)" }}>{r.classification ?? "—"}</div>
                      <div style={{ color: "var(--text-dim)" }}>{r.action ?? ""}</div>
                    </td>
                    {SCORES.map((s) => (
                      <td key={s.key} className="py-2 px-2 text-right tabular-nums font-semibold"
                          style={{ color: scoreColor(r[s.key]) }}>
                        {r[s.key] === null ? "—" : r[s.key]!.toFixed(1)}
                        {s.key === "valuation" && r.valuation_view && (
                          <div className="text-[10px] font-normal" style={{ color: "var(--text-dim)" }}>{r.valuation_view.toLowerCase()}</div>
                        )}
                        {s.key === "quality" && r.business_quality !== null && (
                          <div className="text-[10px] font-normal" style={{ color: "var(--text-dim)" }}
                               title="Business Quality, 30% of Quality">business {r.business_quality.toFixed(0)}</div>
                        )}
                      </td>
                    ))}
                    <td className="py-2 px-2 text-right text-xs tabular-nums"
                        style={{ color: r.quality_direction === "IMPROVING" ? "#4fb3a0" : r.quality_direction === "DECLINING" ? "#d9694f" : "var(--text-secondary)" }}>
                      {r.quality_change_12m === null ? "—" : `${r.quality_change_12m > 0 ? "+" : ""}${r.quality_change_12m.toFixed(1)}`}
                      {r.quality_change_6m !== null && <span style={{ color: "var(--text-dim)" }}> ({r.quality_change_6m > 0 ? "+" : ""}{r.quality_change_6m.toFixed(1)})</span>}
                    </td>
                    <td className="py-2 px-2 text-xs" style={{ color: "var(--text-secondary)" }}>
                      {r.sector_rank ? <>#{r.sector_rank.rank}/{r.sector_rank.of} <span style={{ color: "var(--text-dim)" }}>{r.sector_rank.label}</span></> : "—"}
                    </td>
                    <td className="py-2 px-2 text-xs" style={{ color: t?.color ?? "var(--text-dim)" }}>{t?.label ?? "—"}</td>
                    <td className="py-2 px-2 text-right tabular-nums" style={{ color: "var(--text-secondary)" }}>
                      {r.market_cap === null ? "—" : Math.round(r.market_cap / 1e7).toLocaleString("en-IN")}
                    </td>
                    <td className="py-2 px-2 text-right text-xs" style={{ color: "var(--text-dim)" }}
                        title={`${r.basis === "FULL" ? "From a full analysis" : "From the quick (Yahoo) analysis"} · ${r.latest_fy ?? ""} · scored ${r.as_of}`}>
                      {r.basis === "FULL" ? "Full" : "Quick"}
                    </td>
                  </tr>
                  {isOpen && (
                    <tr><td colSpan={SCORES.length + 7} className="p-0"><StockDetail symbol={r.symbol} onAnalyse={onAnalyse ? () => onAnalyse(r.stock_id) : undefined} /></td></tr>
                  )}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        </div>

        {data && data.total > PAGE && (
          <div className="flex items-center justify-end gap-3 mt-4 text-xs" style={{ color: "var(--text-dim)" }}>
            <button disabled={page === 0} onClick={() => setPage(page - 1)} className="px-3 py-1.5 rounded-lg"
                    style={{ border: "1px solid var(--border-subtle)", opacity: page === 0 ? 0.4 : 1 }}>Previous</button>
            <span>{page * PAGE + 1}–{Math.min((page + 1) * PAGE, data.total)} of {data.total.toLocaleString("en-IN")}</span>
            <button disabled={(page + 1) * PAGE >= data.total} onClick={() => setPage(page + 1)} className="px-3 py-1.5 rounded-lg"
                    style={{ border: "1px solid var(--border-subtle)", opacity: (page + 1) * PAGE >= data.total ? 0.4 : 1 }}>Next</button>
          </div>
        )}
      </div>
    </div>
  );
}

const LABELS: Record<string, string> = {
  growth: "Growth", profitability: "Profitability", cash_flow: "Cash flow", balance_sheet: "Balance sheet",
  efficiency: "Efficiency (add-on)", earnings_consistency: "Earnings consistency", working_capital_trend: "Working-capital trend",
  share_dilution: "Share dilution", dividend_sustainability: "Dividend sustainability",
  durability: "Durability of returns", margin_resilience: "Margin resilience", predictability: "Predictability",
  capital_allocation: "Capital allocation", promoter_behaviour: "Promoter behaviour", management_credibility: "Management credibility",
  growth_acceleration: "Growth acceleration", margin_change: "Margin change", return_change: "Return change",
  debt_change: "Debt change", volatility: "Volatility", drawdown: "Drawdown", risk_adjusted_return: "Risk-adjusted return",
  vs_market: "vs Nifty 50", vs_sector: "vs sector", sector_percentile: "Sector percentile", resilience: "Resilience in market falls",
  drawdown_vs_market: "Drawdown vs market", near_52_week_high: "Near 52-week high",
  trend_structure: "Trend structure", moving_averages: "Moving averages", rsi: "RSI (14)", macd: "MACD", volume: "Volume confirmation",
  breakout: "Breakout / breakdown", base: "Base / contraction", reversal: "Reversal structure",
  pe_vs_history: "P/E vs own history", pe_vs_sector: "P/E vs industry", pb_vs_history: "P/B vs own history",
  pb_vs_sector: "P/B vs industry", peg: "PEG", ev_ebitda: "EV/EBITDA", fcf_yield: "Free-cash-flow yield", deep_report: "Deep report value",
};

function flat(v: unknown): string {
  if (v && typeof v === "object" && !Array.isArray(v)) {
    return Object.entries(v as Record<string, unknown>).map(([k, x]) => `${k} ${typeof x === "number" ? Number(x.toFixed(2)) : x}`).join(", ");
  }
  return Array.isArray(v) ? v.join(", ") : String(v);
}
const HIDDEN = new Set(["score", "weight", "source", "governance_flags", "note"]);

function facts(part: Part): string {
  if (part.score === null && part.reason) return part.reason;
  return Object.entries(part)
    .filter(([k, v]) => !HIDDEN.has(k) && v !== null && v !== undefined)
    .map(([k, v]) => `${k.replace(/_/g, " ")}: ${typeof v === "number" ? Number(v.toFixed(2)) : flat(v)}`)
    .join(" · ");
}

function PartsTable({ title, total, parts }: { title: string; total: number | null; parts: Record<string, Part> }) {
  return (
    <div>
      <div className="text-xs font-semibold mb-1.5" style={{ color: "var(--text-primary)" }}>
        {title} <span style={{ color: scoreColor(total) }}>{total === null ? "—" : total.toFixed(1)}</span>
      </div>
      <table className="w-full text-xs">
        <tbody>
          {Object.entries(parts).map(([name, part]) => (
            <tr key={name} style={{ borderTop: "1px solid var(--border-subtle)" }}>
              <td className="py-1 pr-2 whitespace-nowrap" style={{ color: "var(--text-secondary)" }}>{LABELS[name] ?? name}</td>
              <td className="py-1 pr-2 text-right tabular-nums" style={{ color: "var(--text-dim)" }}>
                {part.weight !== undefined ? `${Math.round(part.weight * 100)}%` : ""}
              </td>
              <td className="py-1 pr-2 text-right tabular-nums font-semibold" style={{ color: scoreColor(part.score) }}>
                {part.score === null ? "—" : part.score.toFixed(1)}
              </td>
              <td className="py-1" style={{ color: "var(--text-dim)" }}>{part.note ? `${part.note}. ` : ""}{facts(part)}{part.source || part.basis ? ` (${part.source ?? part.basis})` : ""}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function StockDetail({ symbol, onAnalyse }: { symbol: string; onAnalyse?: () => void }) {
  const [d, setD] = useState<FrameworkStockDetail | null>(null);
  const [err, setErr] = useState("");
  useEffect(() => {
    api.getFrameworkStock(symbol).then(setD).catch((e: unknown) => setErr(e instanceof Error ? e.message : "Could not load"));
  }, [symbol]);
  const [why, setWhy] = useState<{ summary: string; major_risks?: string[]; what_would_change_it?: string | null; author: string } | null>(null);
  const [asking, setAsking] = useState(false);
  const [live, setLive] = useState<{ last_price: number | null; change_pct: number | null; as_of: string | null } | null>(null);
  useEffect(() => { api.nseQuote(symbol).then(setLive).catch(() => setLive(null)); }, [symbol]);
  if (err) return <div className="p-4 text-xs" style={{ color: "var(--accent-red)" }}>{err}</div>;
  if (!d) return <div className="p-4 text-xs" style={{ color: "var(--text-dim)" }}>Loading…</div>;
  const { quality, business_quality: bq, fundamental: f, trend, quantitative: qn, relative_strength: rs, technical: tc, valuation: vl, momentum: mo, decision: dc } = d.detail;
  const horizon = (h?: { quality: number | null; change: number | null; method: string; as_of?: string; reason?: string }, label = "") =>
    !h ? null : h.quality === null ? `${label}: ${h.reason ?? "not available"}` :
      `${label} ${h.quality.toFixed(1)} (${h.change! > 0 ? "+" : ""}${h.change!.toFixed(1)} since, ${h.method}${h.as_of ? ` at ${h.as_of}` : ""})`;
  return (
    <div className="p-4 space-y-4" style={{ background: "var(--glass)" }}>
      <div className="text-xs" style={{ color: "var(--text-secondary)" }}>
        <b style={{ color: "var(--text-primary)" }}>Quality {quality?.score?.toFixed(1) ?? "—"}</b>
        {quality?.band ? ` (${quality.band.toLowerCase().replace("_", " ")})` : ""} = {quality?.formula ?? "—"}.
        {quality?.capped && <span style={{ color: "var(--accent-red)" }}> {quality.capped}.</span>}
        {trend && <> Business trend: <b>{trend.trend.toLowerCase().replace("_", " ")}</b>{trend.reason ? ` — ${trend.reason}` : ""}.</>}
        {live?.last_price != null && (
          <span className="ml-1" title={`NSE live quote${live.as_of ? `, ${live.as_of}` : ""}`}> Price <b style={{ color: "var(--text-primary)" }}>₹{live.last_price.toLocaleString("en-IN")}</b>
            {live.change_pct != null && <span style={{ color: live.change_pct >= 0 ? "#4fb3a0" : "#d9694f" }}> {live.change_pct >= 0 ? "+" : ""}{live.change_pct.toFixed(2)}%</span>}
            <span style={{ color: "var(--text-dim)" }}> (NSE{live.as_of ? `, ${live.as_of.slice(11, 16)}` : ""})</span>.</span>
        )}
        {onAnalyse && <button onClick={onAnalyse} className="ml-3 underline" style={{ color: "var(--accent-gold-bright)" }}>Run full analysis</button>}
        <a href={`/api/framework/${encodeURIComponent(symbol)}/integrated-report.pdf`} target="_blank" rel="noreferrer"
           className="ml-3 underline" style={{ color: "var(--accent-gold-bright)" }}
           title="One PDF: this framework section, the editorial report (if a full analysis exists) and the deep report (if built). Takes up to a minute.">
          Integrated report (PDF)</a>
      </div>
      {dc?.classification && (
        <div className="rounded-lg p-3 text-xs space-y-1.5" style={{ border: `1px solid ${CLASS_COLOR[dc.classification]}`, color: "var(--text-secondary)" }}>
          <div className="text-sm" style={{ color: "var(--text-primary)" }}>
            <b style={{ color: CLASS_COLOR[dc.classification] }}>{dc.classification}</b> · {dc.action}
            {dc.size && dc.size !== "None" && <> · position size: {dc.size.toLowerCase()}</>}
            {dc.matrix && <span style={{ color: "var(--text-dim)" }}> — {dc.matrix}</span>}
          </div>
          <div>{dc.why.join(". ")}.</div>
          {dc.gates.red_flags.length > 0 && <div style={{ color: "var(--accent-red)" }}>Red flags: {dc.gates.red_flags.join("; ")}</div>}
          <div>
            {dc.interpretation.strong.length > 0 && <>Strong: {dc.interpretation.strong.join(", ")}. </>}
            {dc.interpretation.weak.length > 0 && <>Weak: {dc.interpretation.weak.join(", ")}. </>}
            {dc.interpretation.improving.length > 0 && <>Improving: {dc.interpretation.improving.join(", ")}. </>}
            {dc.interpretation.deteriorating.length > 0 && <>Deteriorating: {dc.interpretation.deteriorating.join(", ")}. </>}
            {dc.interpretation.performance && <>The stock is {dc.interpretation.performance}. </>}
          </div>
          {d.best_alternative && (
            <div>Best same-sector alternative now: <b style={{ color: "var(--text-primary)" }}>{d.best_alternative.symbol}</b> ({d.best_alternative.classification},{" "}
              {d.best_alternative.action.toLowerCase()}, Quality {d.best_alternative.quality?.toFixed(1) ?? "—"}).</div>
          )}
          {d.replacement && (
            <div>Replacement view: {d.replacement.candidate} is better on {d.replacement.why_better.join(", ")} (
              {Object.entries(d.replacement.differences).filter(([, v]) => v !== null).map(([k, v]) => `${k.replace(/_/g, " ")} ${v! > 0 ? "+" : ""}${v}`).join(", ")};
              valuation {d.replacement.valuation.existing?.toLowerCase() ?? "—"} → {d.replacement.valuation.candidate?.toLowerCase() ?? "—"}).</div>
          )}
          <div className="pt-1">
            {why ? (
              <div className="space-y-1">
                <div style={{ color: "var(--text-primary)" }}>{why.summary}</div>
                {why.major_risks && why.major_risks.length > 0 && <div>Major risks: {why.major_risks.join("; ")}.</div>}
                {why.what_would_change_it && <div>What would change it: {why.what_would_change_it}</div>}
                <div style={{ color: "var(--text-dim)" }}>Written by {why.author === "gpt-oss" ? "gpt-oss from the numbers above, checked against the decision" : "the rules (model unavailable or its answer disagreed with the decision)"}.</div>
              </div>
            ) : (
              <button disabled={asking} onClick={() => { setAsking(true); api.explainFramework(d.symbol).then(setWhy).finally(() => setAsking(false)); }}
                      className="underline" style={{ color: "var(--accent-gold-bright)" }}>{asking ? "Writing the explanation…" : "Explain this decision"}</button>
            )}
          </div>
        </div>
      )}
      {(mo || d.sector_rank) && (
        <div className="text-xs" style={{ color: "var(--text-secondary)" }}>
          {mo && <><b style={{ color: "var(--text-primary)" }}>Quality momentum: {mo.direction.toLowerCase().replace("_", " ")}</b>.{" "}
            {[horizon(mo["6m"], "6 months ago"), horizon(mo["12m"], "12 months ago")].filter(Boolean).join("; ")}.{" "}</>}
          {d.sector_rank && <>Quality ranks #{d.sector_rank.rank} of {d.sector_rank.of} in {d.sector_rank.sector} ({d.sector_rank.label}).</>}
        </div>
      )}
      <div className="grid gap-5 lg:grid-cols-2">
        {f && <PartsTable title="Fundamental" total={f.score} parts={f.components} />}
        {bq && <PartsTable title="Business quality" total={bq.score} parts={bq.components} />}
        {qn && <PartsTable title="Quantitative" total={qn.score} parts={qn.components} />}
        {rs && <PartsTable title={`Relative strength${rs.as_of ? ` (prices to ${rs.as_of})` : ""}`} total={rs.score} parts={rs.components} />}
        {tc && <PartsTable title="Technical" total={tc.score} parts={tc.components} />}
        {vl && <PartsTable title={`Valuation${vl.view ? ` — ${vl.view.toLowerCase()}` : ""}`} total={vl.score} parts={vl.components} />}
      </div>
      {rs?.why_holding_up && (
        <div className="text-xs rounded-lg p-3" style={{ border: "1px solid var(--border-subtle)", color: "var(--text-secondary)" }}>
          <b style={{ color: "var(--text-primary)" }}>Holding up while its sector is weak</b> (sector down over {rs.why_holding_up.sector_weak_over.join(" and ")},
          stock 10%+ ahead over {rs.why_holding_up.stock_ahead_of_sector_over.join(" and ")}). Why, from the business data: {rs.why_holding_up.reasons.join("; ")}.
        </div>
      )}
      {vl && (
        <div className="text-xs" style={{ color: "var(--text-secondary)" }}>
          {vl.interpretation && <><b style={{ color: "var(--text-primary)" }}>Quality and price together:</b> {vl.interpretation}. </>}
          {vl.market_cap_cr !== undefined && <>Market cap ₹{Math.round(vl.market_cap_cr).toLocaleString("en-IN")} cr ({vl.market_cap_source}),
          trailing profit {vl.ttm_profit_cr === null ? "—" : `₹${Math.round(vl.ttm_profit_cr).toLocaleString("en-IN")} cr`}
          {vl.pe ? `, P/E ${vl.pe}` : ""}. </>}{vl.ttm_note ?? ""}{vl.reason ?? ""}
        </div>
      )}
      <div className="text-[11px] space-y-1" style={{ color: "var(--text-dim)" }}>
        {f?.double_in && <div>Doubling: {facts(f.double_in as Part)} · rates {JSON.stringify((f.double_in as Record<string, unknown>).growth_pct_per_year)}</div>}
        {bq && <div>Business quality from {bq.source ?? "no Screener history"} ({bq.years_on_record} years). Not measured: {bq.not_measured.join(", ")}.</div>}
      </div>
    </div>
  );
}
