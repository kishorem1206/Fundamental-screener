import { useEffect, useState } from "react";
import { ArrowDown, ArrowUp } from "lucide-react";
import { api } from "../api";
import type { CompanyScoreRow, QuickGrowthKey, ScoreKey } from "../types";

type DisplayKey = ScoreKey | QuickGrowthKey;

const BASE_SCORES: { key: DisplayKey; label: string }[] = [
  { key: "growth", label: "Growth" },
  { key: "profitability", label: "Profitability" },
  { key: "cash_flow", label: "Cash Flow" },
  { key: "balance_sheet", label: "Balance Sheet" },
  { key: "efficiency", label: "Efficiency" },
  { key: "valuation", label: "Valuation" },
  { key: "overall", label: "Overall" },
];
// Quick Screener only — the two components blended into `growth` (see
// types.ts's QuickGrowthKey doc comment). Inserted right after "Growth" so
// the blend and its two ingredients sit together.
const QUICK_GROWTH_SPLIT: { key: DisplayKey; label: string }[] = [
  { key: "growth_annual", label: "Growth (Annual)" },
  { key: "growth_quarterly", label: "Growth (Quarterly)" },
];

type Range = [number, number];
const FULL: Range = [0, 100];
const emptyRanges = (scores: { key: DisplayKey }[]): Record<DisplayKey, Range> =>
  Object.fromEntries(scores.map((s) => [s.key, [...FULL]])) as Record<DisplayKey, Range>;
const isActive = (r: Range) => r[0] > FULL[0] || r[1] < FULL[1];

function RangeSlider({ value, onChange }: { value: Range; onChange: (v: Range) => void }) {
  const [lo, hi] = value;
  return (
    <div className="dual-range">
      <div className="dual-range-track" />
      <div className="dual-range-fill" style={{ left: `${lo}%`, right: `${100 - hi}%` }} />
      <input type="range" min={0} max={100} step={1} value={lo} aria-label="minimum"
             style={{ zIndex: lo > 90 ? 2 : 1 }}
             onChange={(e) => onChange([Math.min(Number(e.target.value), hi), hi])} />
      <input type="range" min={0} max={100} step={1} value={hi} aria-label="maximum"
             onChange={(e) => onChange([lo, Math.max(Number(e.target.value), lo)])} />
    </div>
  );
}

const scoreColor = (v: number | null) =>
  v === null ? "var(--text-dim)" : v >= 70 ? "#4fb3a0" : v >= 50 ? "#c9a227" : "#d9694f";

const fmtDate = (iso: string | null) =>
  iso ? new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" }) : "—";

interface Props {
  // "full": scores from completed full analyses (row opens the analysis).
  // "quick": Yahoo-only quick scores, a separate table (row offers "Full analysis").
  source: "full" | "quick";
  onViewAnalysis?: (analysisId: string) => void;
  onAnalyse?: (stockId: string) => void;
}

const COPY = {
  full: {
    eyebrow: "Score Screener",
    title: "Filter analysed companies by score",
    hint: "Drag the handles on any score (0–100) — filters combine. Scores refresh each time a company is re-analysed.",
  },
  quick: {
    eyebrow: "Quick Screener",
    title: "Screen every stock on quick scores",
    hint: "Drag the handles on any score (0–100) — filters combine. Yahoo-only estimates; shortlist here, then run a full analysis.",
  },
} as const;

export default function ScoreScreener({ source, onViewAnalysis, onAnalyse }: Props) {
  // Quick Screener adds the two growth components right after "Growth";
  // the full Score Screener (fa_company_scores has no equivalent columns
  // yet) sticks to the base six-plus-overall set.
  const SCORES: { key: DisplayKey; label: string }[] = source === "quick"
    ? [BASE_SCORES[0], ...QUICK_GROWTH_SPLIT, ...BASE_SCORES.slice(1)]
    : BASE_SCORES;

  const [ranges, setRanges] = useState<Record<DisplayKey, Range>>(() => emptyRanges(SCORES));
  const [sortBy, setSortBy] = useState<DisplayKey | "scored_at">("overall");
  const [order, setOrder] = useState<"asc" | "desc">("desc");
  const [search, setSearch] = useState("");
  const [sector, setSector] = useState("");
  const [sectors, setSectors] = useState<string[]>([]);
  const [rows, setRows] = useState<CompanyScoreRow[]>([]);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getSectors().then((r) => setSectors(r.sectors)).catch(() => setSectors([]));
  }, []);

  // Reset filters when switching source (full <-> quick) — the two have
  // different filterable key sets (growth_annual/growth_quarterly are
  // Quick Screener only), so a stale range object from the other source
  // would carry keys the new source's SCORES list doesn't render.
  useEffect(() => {
    setRanges(emptyRanges(SCORES));
    setSortBy("overall");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [source]);

  useEffect(() => {
    const params: Record<string, string> = { sort_by: sortBy, order, limit: "100" };
    if (search.trim()) params.q = search.trim();
    if (sector) params.sector = sector;
    for (const { key } of SCORES) {
      if (ranges[key][0] > FULL[0]) params[`min_${key}`] = String(ranges[key][0]);
      if (ranges[key][1] < FULL[1]) params[`max_${key}`] = String(ranges[key][1]);
    }
    const t = setTimeout(() => {
      (source === "quick" ? api.getQuickScores(params) : api.getCompanyScores(params))
        .then((r) => { setRows(r.results); setTotal(r.total); setError(""); })
        .catch((e: unknown) => setError(e instanceof Error ? e.message : "Failed to load scores"));
    }, 300);
    return () => clearTimeout(t);
  }, [ranges, sortBy, order, search, sector, source]);

  const anyFilter = SCORES.some(({ key }) => isActive(ranges[key])) || search !== "" || sector !== "";
  const clickSort = (key: DisplayKey | "scored_at") => {
    if (sortBy === key) setOrder((o) => (o === "desc" ? "asc" : "desc"));
    else { setSortBy(key); setOrder("desc"); }
  };
  const SortIcon = order === "desc" ? ArrowDown : ArrowUp;

  return (
    <div className="card-rich p-6">
      <div className="flex items-start justify-between gap-4 flex-wrap mb-4">
        <div>
          <p className="eyebrow">{COPY[source].eyebrow}</p>
          <h2 className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
            {COPY[source].title}
          </h2>
          <p className="text-xs mt-1" style={{ color: "var(--text-dim)" }}>{COPY[source].hint}</p>
        </div>
        {anyFilter && (
          <button className="text-xs px-3 py-1.5 rounded-md" onClick={() => { setRanges(emptyRanges(SCORES)); setSearch(""); setSector(""); }}
                  style={{ color: "var(--text-secondary)", border: "1px solid var(--border-subtle)" }}>
            Clear filters
          </button>
        )}
      </div>

      <div className="flex flex-wrap gap-3 mb-4">
        <input type="text" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search name or symbol…"
               className="rounded-md px-3 py-1.5 text-xs w-56"
               style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)", color: "var(--text-primary)" }} />
        <select value={sector} onChange={(e) => setSector(e.target.value)}
                className="rounded-md px-3 py-1.5 text-xs"
                style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)", color: "var(--text-primary)" }}>
          <option value="">All sectors</option>
          {sectors.map((sec) => <option key={sec} value={sec}>{sec}</option>)}
        </select>
      </div>

      <div className={`grid grid-cols-2 md:grid-cols-4 ${source === "quick" ? "xl:grid-cols-9" : "xl:grid-cols-7"} gap-x-4 gap-y-3 mb-5`}>
        {SCORES.map(({ key, label }) => (
          <div key={key}>
            <div className="flex items-baseline justify-between mb-0.5">
              <p className="text-[11px] font-semibold" style={{ color: "var(--text-secondary)" }}>{label}</p>
              <p className="text-[11px] tabular-nums"
                 style={{ color: isActive(ranges[key]) ? "var(--accent-gold-bright)" : "var(--text-dim)" }}>
                {ranges[key][0]}–{ranges[key][1]}
              </p>
            </div>
            <RangeSlider value={ranges[key]} onChange={(v) => setRanges((r) => ({ ...r, [key]: v }))} />
          </div>
        ))}
      </div>

      {error && <p className="text-sm mb-3" style={{ color: "#d9694f" }}>{error}</p>}
      <p className="text-xs mb-2" style={{ color: "var(--text-dim)" }}>
        {total} {total === 1 ? "company" : "companies"} match{rows.length < total ? ` · showing top ${rows.length}` : ""}
      </p>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr style={{ color: "var(--text-dim)" }} className="text-[11px] uppercase tracking-wide">
              <th className="text-left py-2 pr-3 font-semibold">Company</th>
              {SCORES.map(({ key, label }) => (
                <th key={key} className="text-right py-2 px-2 font-semibold cursor-pointer select-none whitespace-nowrap" onClick={() => clickSort(key)}>
                  {label}{sortBy === key && <SortIcon size={11} className="inline ml-0.5" />}
                </th>
              ))}
              <th className="text-right py-2 pl-3 font-semibold cursor-pointer select-none whitespace-nowrap" onClick={() => clickSort("scored_at")}>
                Scored{sortBy === "scored_at" && <SortIcon size={11} className="inline ml-0.5" />}
              </th>
              {source === "quick" && <th className="pl-3" />}
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.stock_id} className={source === "full" && r.analysis_id ? "cursor-pointer" : ""}
                  onClick={() => source === "full" && r.analysis_id && onViewAnalysis?.(r.analysis_id)}
                  style={{ borderTop: "1px solid var(--border-subtle)" }}>
                <td className="py-2 pr-3">
                  <div className="font-semibold" style={{ color: "var(--text-primary)" }}>{r.company_name}</div>
                  <div className="text-[11px]" style={{ color: "var(--text-dim)" }}>{r.symbol}{r.sector ? ` · ${r.sector}` : ""}</div>
                </td>
                {SCORES.map(({ key }) => (
                  <td key={key} className="text-right py-2 px-2 tabular-nums font-semibold" style={{ color: scoreColor(r[key]) }}>
                    {r[key] === null ? "—" : r[key]!.toFixed(0)}
                  </td>
                ))}
                <td className="text-right py-2 pl-3 text-[11px] whitespace-nowrap" style={{ color: "var(--text-dim)" }}
                    title={r.latest_quarter_end ? `Latest reported quarter at scoring: ${fmtDate(r.latest_quarter_end)}`
                      : r.latest_fy ? `Yahoo data through ${r.latest_fy}` : undefined}>
                  {fmtDate(r.scored_at)}
                </td>
                {source === "quick" && (
                  <td className="text-right py-2 pl-3">
                    <button className="text-[11px] px-2.5 py-1 rounded-md whitespace-nowrap"
                            onClick={() => onAnalyse?.(r.stock_id)}
                            style={{ color: "var(--accent-gold-bright)", border: "1px solid rgba(201,162,39,0.35)" }}>
                      Full analysis
                    </button>
                  </td>
                )}
              </tr>
            ))}
            {rows.length === 0 && !error && (
              <tr><td colSpan={SCORES.length + (source === "quick" ? 3 : 2)} className="py-6 text-center text-sm" style={{ color: "var(--text-dim)" }}>
                {source === "quick" ? "No scored companies match these filters yet." : "No analysed companies match these filters."}
              </td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
