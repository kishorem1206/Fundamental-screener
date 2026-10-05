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
  quality: number | null;
  business_quality: number | null;
  fundamental: number | null;
  quantitative: number | null;
  relative_strength: number | null;
  technical: number | null;
  valuation: number | null;
}

type Part = { score: number | null; weight?: number; reason?: string; note?: string; source?: string; basis?: string; [k: string]: unknown };

export interface FrameworkStockDetail extends FrameworkScoreRow {
  detail: {
    quality?: { score: number | null; band: string | null; formula?: string; capped?: string; governance_red_flag?: string };
    business_quality?: { score: number | null; coverage: number; components: Record<string, Part>; not_measured: string[]; source: string | null; years_on_record: number };
    fundamental?: { score: number | null; coverage: number; components: Record<string, Part>; double_in: Record<string, unknown>; long_run_growth: Part | null };
    trend?: { trend: string; reason?: string; signals: { signal: string; reading: string; vote: number }[] };
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
  { key: "quantitative", label: "Quantitative", question: "Are the numbers getting better or worse?", pending: "phase 6" },
  { key: "relative_strength", label: "Rel. strength", question: "Is it beating the market and its sector?", pending: "phase 6" },
  { key: "technical", label: "Technical", question: "Is price behaviour confirming it?", pending: "phase 7" },
  { key: "valuation", label: "Valuation", question: "Is the price reasonable?", pending: "phase 7" },
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
  const [sort, setSort] = useState<ScoreKey | "market_cap">("quality");
  const [open, setOpen] = useState<string | null>(null);
  const [order, setOrder] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(0);

  useEffect(() => { setPage(0); }, [q, sector, trend, sort, order]);

  useEffect(() => {
    const params: Record<string, string> = { sort, order, limit: String(PAGE), offset: String(page * PAGE) };
    if (q.trim()) params.q = q.trim();
    if (sector) params.sector = sector;
    if (trend) params.trend = trend;
    const t = setTimeout(() => {
      api.getFrameworkScores(params).then((r) => { setData(r); setError(""); })
        .catch((e: unknown) => setError(e instanceof Error ? e.message : "Could not load scores"));
    }, 200);
    return () => clearTimeout(t);
  }, [q, sector, trend, sort, order, page]);

  const sortBy = (key: ScoreKey | "market_cap") => {
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
                    {SCORES.map((s) => (
                      <td key={s.key} className="py-2 px-2 text-right tabular-nums font-semibold"
                          style={{ color: scoreColor(r[s.key]) }}>
                        {r[s.key] === null ? "—" : r[s.key]!.toFixed(1)}
                        {s.key === "quality" && r.business_quality !== null && (
                          <div className="text-[10px] font-normal" style={{ color: "var(--text-dim)" }}
                               title="Business Quality, 30% of Quality">business {r.business_quality.toFixed(0)}</div>
                        )}
                      </td>
                    ))}
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
                    <tr><td colSpan={SCORES.length + 4} className="p-0"><StockDetail symbol={r.symbol} onAnalyse={() => onAnalyse?.(r.stock_id)} /></td></tr>
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
};
const HIDDEN = new Set(["score", "weight", "source", "governance_flags"]);

function facts(part: Part): string {
  if (part.score === null && part.reason) return part.reason;
  return Object.entries(part)
    .filter(([k, v]) => !HIDDEN.has(k) && v !== null && v !== undefined && typeof v !== "object")
    .map(([k, v]) => `${k.replace(/_/g, " ")}: ${typeof v === "number" ? Number(v.toFixed(2)) : v}`)
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

function StockDetail({ symbol, onAnalyse }: { symbol: string; onAnalyse: () => void }) {
  const [d, setD] = useState<FrameworkStockDetail | null>(null);
  const [err, setErr] = useState("");
  useEffect(() => {
    api.getFrameworkStock(symbol).then(setD).catch((e: unknown) => setErr(e instanceof Error ? e.message : "Could not load"));
  }, [symbol]);
  if (err) return <div className="p-4 text-xs" style={{ color: "var(--accent-red)" }}>{err}</div>;
  if (!d) return <div className="p-4 text-xs" style={{ color: "var(--text-dim)" }}>Loading…</div>;
  const { quality, business_quality: bq, fundamental: f, trend } = d.detail;
  return (
    <div className="p-4 space-y-4" style={{ background: "var(--glass)" }}>
      <div className="text-xs" style={{ color: "var(--text-secondary)" }}>
        <b style={{ color: "var(--text-primary)" }}>Quality {quality?.score?.toFixed(1) ?? "—"}</b>
        {quality?.band ? ` (${quality.band.toLowerCase().replace("_", " ")})` : ""} = {quality?.formula ?? "—"}.
        {quality?.capped && <span style={{ color: "var(--accent-red)" }}> {quality.capped}.</span>}
        {trend && <> Business trend: <b>{trend.trend.toLowerCase().replace("_", " ")}</b>{trend.reason ? ` — ${trend.reason}` : ""}.</>}
        <button onClick={onAnalyse} className="ml-3 underline" style={{ color: "var(--accent-gold-bright)" }}>Run full analysis</button>
      </div>
      <div className="grid gap-5 lg:grid-cols-2">
        {f && <PartsTable title="Fundamental" total={f.score} parts={f.components} />}
        {bq && <PartsTable title="Business quality" total={bq.score} parts={bq.components} />}
      </div>
      <div className="text-[11px] space-y-1" style={{ color: "var(--text-dim)" }}>
        {f?.double_in && <div>Doubling: {facts(f.double_in as Part)} · rates {JSON.stringify((f.double_in as Record<string, unknown>).growth_pct_per_year)}</div>}
        {bq && <div>Business quality from {bq.source ?? "no Screener history"} ({bq.years_on_record} years). Not measured: {bq.not_measured.join(", ")}.</div>}
      </div>
    </div>
  );
}
