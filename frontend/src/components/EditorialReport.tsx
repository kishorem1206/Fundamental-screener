/**
 * Editorial Report — a long-form, cover-page narrative view of a completed
 * analysis, styled as an institutional research note (forest-green/gold
 * editorial palette). Same visual language for every sector: nothing here
 * is hand-written per company. Every displayed value is either read
 * directly off `FullAnalysis` (already-computed scores, sector metrics,
 * peers, risks, AI output) or a deterministic template built from those
 * real fields — never invented prose.
 *
 * Provenance discipline (2026-09-20, user's explicit instruction after a
 * reference report was found to contain fabricated per-hospital detail):
 * every figure carries a `ProvenanceTag` — REPORTED / CALCULATED /
 * BENCHMARK / AI · THIRD-PARTY / UNAVAILABLE — and a missing field renders
 * as "Not disclosed in supplied sources", never a guess. See the
 * Methodology section at the foot of the report for the legend and the
 * real source list (NSE/BSE/Screener.in/Yahoo Finance — this app's actual
 * ingestion pipeline, not an aspirational one).
 */
import { useEffect, useState } from "react";
import type {
  FullAnalysis, SectorMetric, PeerEntry, CompanySummaryResponse,
  PlIntelligence, BalanceSheetIntelligence, CashFlowIntelligence, QuarterlyIntelligence,
  BankRoeAnalysis, ConcallIntelligenceResponse, NewsItem, EarningsCalendarResponse,
  AnalystConsensusEntry, BlueprintSection, PricePoint, SalesMarginPoint, ValuationHistoryPoint, RoceHistoryPoint,
  PeerPerformanceSeries, Scores,
} from "../types";
import { api } from "../api";
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import ComboTrendChart from "./charts/ComboTrendChart";
import TrendChart from "./TrendChart";
import WaterfallChart from "./charts/WaterfallChart";
import type { WaterfallStep } from "./charts/WaterfallChart";
import DonutChart from "./charts/DonutChart";
import type { DonutSlice } from "./charts/DonutChart";
import RadarScoreChart from "./charts/RadarScoreChart";
import PeerScatterChart from "./charts/PeerScatterChart";
import RebasedPerformanceChart from "./charts/RebasedPerformanceChart";

// Same "FY26" style axis labels + year->series conversion
// OverviewSection.tsx's own toSeries()/fyLabel() already use for the live
// dashboard's Sales & Margins / EPS & P/E charts — duplicated here (not
// imported) since that file's helpers are module-private, not exported.
function fyLabel(period: string): string {
  const year = period.slice(0, 4);
  return year ? `FY${year.slice(2)}` : period;
}
function toSeries<T extends { period: string }>(points: T[], key: keyof T): Record<string, number | null> {
  const out: Record<string, number | null> = {};
  for (const p of points) {
    const v = p[key];
    out[fyLabel(p.period)] = typeof v === "number" ? v : null;
  }
  return out;
}
// Same latest-common-year P&L bridge OverviewSection.tsx builds for its own
// Waterfall chart — duplicated for the same module-private reason above.
function latestPnlBridge(m: FullAnalysis["metrics"]): WaterfallStep[] {
  if (!m?.revenue_series || !m?.ebitda_series || !m?.pat_series) return [];
  const years = Object.keys(m.revenue_series)
    .filter((y) => m.revenue_series[y] != null && m.ebitda_series[y] != null && m.pat_series[y] != null)
    .sort();
  const latest = years.at(-1);
  if (!latest) return [];
  return [
    { label: "Revenue", value: m.revenue_series[latest]! },
    { label: "EBITDA", value: m.ebitda_series[latest]! },
    { label: "PAT", value: m.pat_series[latest]! },
  ];
}
const CATEGORY_COLORS: Record<string, string> = {
  growth: "#c9a227", profitability: "#4fb3a0", cash_flow: "#e0793c",
  balance_sheet: "#e8c766", efficiency: "#7fb8ff", valuation: "#d9694f",
};

// Backs the "Margin trend" card's direction labels with real numbers —
// previously showed only "Volatile"/"Expansion"/etc. with nothing to
// substantiate it, leaving a reader unable to tell a mild wobble from a
// wide swing without cross-checking the chart above by eye.
function marginSeriesStats(series: Record<string, number>): { latest: number | null; min: number | null; max: number | null } {
  const periods = Object.keys(series).sort();
  if (periods.length === 0) return { latest: null, min: null, max: null };
  const values = periods.map((p) => series[p]);
  return { latest: series[periods[periods.length - 1]], min: Math.min(...values), max: Math.max(...values) };
}

// Color-coded key for every bar/line chart's series — real gap found live
// (user's own report, 2026-09-22: "Which line represents which? I want for
// all charts"): ComboTrendChart/WaterfallChart render fine on screen where a
// hover tooltip names each series, but a printed PDF has no hover, so an
// unlabeled red line or gold bar is genuinely ambiguous there. `shape`
// distinguishes a bar-series swatch (square) from a line-series swatch
// (circle) at a glance, matching each chart's own visual language.
function ChartLegend({ items }: { items: { color: string; label: string; shape?: "square" | "circle" }[] }) {
  return (
    <div style={{ display: "flex", gap: 16, marginTop: 8, flexWrap: "wrap", fontSize: 11, color: "var(--er-muted)" }}>
      {items.map((it) => (
        <span key={it.label} style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span style={{
            width: 10, height: 10, display: "inline-block", background: it.color,
            borderRadius: (it.shape ?? "square") === "circle" ? 999 : 3,
          }} />
          {it.label}
        </span>
      ))}
    </div>
  );
}

// A print/editorial-styled equivalent of charts/PriceHistoryChart.tsx —
// not reused directly, because that component wraps itself in the live
// dashboard's own dark "card-rich" chrome plus an interactive 1Y/5Y toggle
// button, neither of which belongs inside a static, cream/gold-themed
// printed report. Fixed to 1 year (the report's other history views are
// already multi-year fiscal tables) and uses editorial's own palette.
function EditorialPriceChart({ points }: { points: { date: string; close: number }[] }) {
  if (points.length < 2) return null;
  const rows = points.map((p) => ({
    date: new Date(p.date).toLocaleDateString("en-IN", { month: "short", day: "2-digit" }),
    close: p.close,
  }));
  return (
    <ResponsiveContainer width="100%" height={220}>
      <AreaChart data={rows} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="er-price-grad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#c79a3b" stopOpacity={0.35} />
            <stop offset="100%" stopColor="#c79a3b" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#dedfd7" vertical={false} />
        <XAxis dataKey="date" tick={{ fill: "#66716d", fontSize: 10 }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fill: "#66716d", fontSize: 10 }} axisLine={false} tickLine={false} width={54}
               domain={["auto", "auto"]} tickFormatter={(v) => `₹${v}`} />
        <Tooltip formatter={(v: number) => [`₹${v.toFixed(2)}`, "Close"]}
                 contentStyle={{ background: "#fffdf8", border: "1px solid #dedfd7", borderRadius: 10, fontSize: 12 }} />
        <Area type="monotone" dataKey="close" stroke="#c79a3b" strokeWidth={2} fill="url(#er-price-grad)" isAnimationActive={false} />
      </AreaChart>
    </ResponsiveContainer>
  );
}

type Provenance = "reported" | "calculated" | "benchmark" | "ai" | "third_party" | "unavailable";

const PROV_LABEL: Record<Provenance, string> = {
  reported: "Reported", calculated: "Calculated", benchmark: "Benchmark",
  ai: "Platform AI", third_party: "Third-party", unavailable: "Unavailable",
};
const PROV_COLOR: Record<Provenance, string> = {
  reported: "#286d5d", calculated: "#426982", benchmark: "#795b1d", ai: "#6b382d", third_party: "#5b4a8a", unavailable: "#8d9994",
};
const PROV_BG: Record<Provenance, string> = {
  reported: "#dceee7", calculated: "#e4edf3", benchmark: "#f6ecd4", ai: "#f8e4dd", third_party: "#ebe6f5", unavailable: "#eceae2",
};

function Tag({ kind }: { kind: Provenance }) {
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", borderRadius: 999, padding: "2px 8px",
      fontSize: 9, fontWeight: 800, letterSpacing: ".04em", textTransform: "uppercase",
      color: PROV_COLOR[kind], background: PROV_BG[kind], marginLeft: 6, whiteSpace: "nowrap",
    }}>{PROV_LABEL[kind]}</span>
  );
}

const NA = "Not disclosed in supplied sources";

function fmtNum(v: number | null | undefined, unit = "", digits = 2): string {
  if (v === null || v === undefined || Number.isNaN(v)) return NA;
  const u = unit.toLowerCase();
  if (u === "%") return `${v.toFixed(1)}%`;
  if (u === "x") return `${v.toFixed(2)}x`;
  if (u === "cr" || u === "inr cr") return `₹${v.toLocaleString("en-IN", { maximumFractionDigits: 0 })} Cr`;
  if (u === "inr" || u === "rs") return `₹${v.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
  if (u === "count" || u === "units" || u === "days") {
    const rounded = Number.isInteger(v) ? v.toLocaleString("en-IN") : v.toFixed(2);
    return `${rounded}${u === "days" ? " days" : ""}`;
  }
  return `${v.toFixed(digits)}${unit ? ` ${unit}` : ""}`;
}

// Same formatting as fmtNum, but "—" instead of the full "Not disclosed…"
// sentence for a missing value — used only in dense many-column comparison
// tables (sector-specific peer metrics), where repeating that sentence in
// most cells makes the table unreadable both on screen and (worse) in
// print, where narrow fixed-width columns wrap it mid-word. The table's own
// footnote explains what "—" means once, rather than per cell.
function fmtDense(v: number | null | undefined, unit = ""): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return fmtNum(v, unit);
}

function scoreBand(score: number | null): { headline: string; band: string } {
  if (score === null) return { headline: "Scoring incomplete for this company.", band: "UNSCORED" };
  if (score >= 75) return { headline: "A strong operator across most measured dimensions.", band: "STRONG" };
  if (score >= 60) return { headline: "A fair operator, with real strengths and real gaps.", band: "FAIR" };
  if (score >= 45) return { headline: "A business under pressure on several fronts.", band: "WATCH" };
  return { headline: "A business under material stress on the metrics measured here.", band: "WEAK" };
}

const SCORE_DIMENSION_LABEL: Record<string, string> = {
  growth: "growth", profitability: "profitability", cash_flow: "cash flow",
  balance_sheet: "balance sheet", efficiency: "efficiency", valuation: "valuation",
};

// "PREMIUM_QUALITY_GROWTH_EFFICIENCY_LEADER" -> "Premium Quality Growth Efficiency Leader"
// — same convention every *IntelligenceSection.tsx uses for its own classification strings.
function readable(s: string | null | undefined): string {
  if (!s) return NA;
  return s.toLowerCase().split("_").map((w) => (w ? w[0].toUpperCase() + w.slice(1) : w)).join(" ");
}

// Joins two already-formatted display strings with " · " — collapses to
// just `a` when either side is the "Not disclosed…" placeholder, so two
// missing fields next to each other don't render as "Not disclosed in
// supplied sources · Not disclosed in supplied sources".
function pairText(a: string, b: string, sep = " · "): string {
  if (a === NA || b === NA) return a === NA ? b : a;
  return `${a}${sep}${b}`;
}

// Same "which years" pattern PlIntelligenceSection.tsx's own doublingLabel()
// already uses for the live dashboard tab — the editorial report's version
// omitted the actual FY-to-FY window, showing only the derived years-to-double
// figure with no way to see which two data points it was measured between.
function doublingLabel(d: { doubling_years: number | null; method: string | null; start_year?: number; end_year?: number }): string {
  if (d.doubling_years == null) return "Not doubling";
  if (d.method === "EMPIRICAL" && d.start_year && d.end_year) {
    return `${d.doubling_years.toFixed(1)}y (FY${d.start_year} → FY${d.end_year})`;
  }
  const methodNote = d.method === "CAGR_THEORETICAL" ? " (est. from historical CAGR)" : "";
  return `${d.doubling_years.toFixed(1)}y${methodNote}`;
}

type FlagTone = "risk" | "watch" | "good" | "info";
const FLAG_TONE_COLOR: Record<FlagTone, string> = { risk: "#bd624d", watch: "#c79a3b", good: "#3f8c72", info: "#4d7190" };

function FlagList({ items, emptyMessage }: { items: { label: string; detail?: string | null; tone: FlagTone }[]; emptyMessage?: string }) {
  if (items.length === 0) return <p className="er-muted" style={{ fontSize: 12.5 }}>{emptyMessage || "No flags evaluated for this company/period."}</p>;
  return (
    <ul style={{ margin: 0, padding: 0, listStyle: "none", display: "grid", gap: 11 }}>
      {items.map((it, i) => (
        <li key={i} style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
          <span style={{ width: 7, height: 7, borderRadius: 999, background: FLAG_TONE_COLOR[it.tone], marginTop: 5, flexShrink: 0 }} />
          <div>
            <div style={{ fontSize: 12.5, fontWeight: 700, color: "var(--er-deep)" }}>{it.label}</div>
            {it.detail && <div style={{ fontSize: 11.5, color: "var(--er-muted)", marginTop: 2 }}>{it.detail}</div>}
          </div>
        </li>
      ))}
    </ul>
  );
}

// Groups flags by quarter instead of one bullet per flag (each repeating
// its own quarter in the heading) — real gap found live on TANLA
// (2026-09-23, user's own report — "Quarterly values are so big. club
// each quarters."): a company with a persistent Other Income Dependency
// and swinging tax rate raised 2-3 flags in nearly every one of 8
// trailing quarters, so the flat list ran to 16-24 verbose two-line
// bullets and spilled across two PDF pages. Grouping means the quarter
// date is stated once per group, not once per flag within it.
function GroupedFlagList({ flags, emptyMessage }: { flags: { flag: string; period: string; detail: string }[]; emptyMessage?: string }) {
  if (flags.length === 0) return <p className="er-muted" style={{ fontSize: 12.5 }}>{emptyMessage || "No flags evaluated for this company/period."}</p>;
  const byPeriod = new Map<string, { flag: string; detail: string }[]>();
  for (const f of flags) byPeriod.set(f.period, [...(byPeriod.get(f.period) || []), { flag: f.flag, detail: f.detail }]);
  const periods = [...byPeriod.keys()].sort().reverse();
  return (
    <div style={{ display: "grid", gap: 12 }}>
      {periods.map((period) => (
        <div key={period}>
          <div style={{ fontSize: 12.5, fontWeight: 700, color: "var(--er-deep)", marginBottom: 4 }}>{period}</div>
          <ul style={{ margin: 0, padding: 0, listStyle: "none", display: "grid", gap: 4 }}>
            {(byPeriod.get(period) || []).map((f, i) => (
              <li key={i} style={{ display: "flex", gap: 7, alignItems: "flex-start", fontSize: 11.5, color: "var(--er-muted)" }}>
                <span style={{ width: 6, height: 6, borderRadius: 999, background: FLAG_TONE_COLOR.watch, marginTop: 4, flexShrink: 0 }} />
                <span><strong style={{ color: "var(--er-deep)", fontWeight: 600 }}>{readable(f.flag)}:</strong> {f.detail}</span>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}

function CoverageMeter({ pct, total }: { pct: number; total: number }) {
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11.5, color: "var(--er-muted)", marginBottom: 6 }}>
        <span>{pct.toFixed(0)}% of {total} tracked metrics available <Tag kind="calculated" /></span>
      </div>
      <div style={{ height: 8, borderRadius: 999, background: "rgba(18,59,56,0.08)" }}>
        <div style={{ height: 8, borderRadius: 999, width: `${Math.min(100, Math.max(0, pct))}%`, background: "var(--er-mint-2)" }} />
      </div>
      <p className="er-muted" style={{ fontSize: 10.5, marginTop: 8 }}>
        This denominator includes several metrics (aging schedules, contingent liabilities, related-party loans, debt maturity)
        that no source this platform ingests can ever provide for any company — they count against the percentage every time,
        not just for this one. A well-covered company can still show well under 100% for that reason alone.
      </p>
    </div>
  );
}

interface Props { analysis: FullAnalysis; }

export default function EditorialReport({ analysis }: Props) {
  const [qi, setQi] = useState<QuarterlyIntelligence | null>(null);
  const [kpiLoaded, setKpiLoaded] = useState(false);
  const [companySummary, setCompanySummary] = useState<CompanySummaryResponse["summary"] | null>(null);
  const [pli, setPli] = useState<PlIntelligence | null>(null);
  const [bsi, setBsi] = useState<BalanceSheetIntelligence | null>(null);
  const [cfi, setCfi] = useState<CashFlowIntelligence | null>(null);
  const [bankRoe, setBankRoe] = useState<BankRoeAnalysis | null>(null);
  const [concall, setConcall] = useState<ConcallIntelligenceResponse | null>(null);
  const [news, setNews] = useState<NewsItem[]>([]);
  const [calendar, setCalendar] = useState<EarningsCalendarResponse["calendar"]>(null);
  const [analystConsensus, setAnalystConsensus] = useState<Record<string, AnalystConsensusEntry>>({});
  const [priceChart, setPriceChart] = useState<{ "1y": PricePoint[]; "5y": PricePoint[] }>({ "1y": [], "5y": [] });
  const [perfSeries, setPerfSeries] = useState<PeerPerformanceSeries[]>([]);
  const [salesMargins, setSalesMargins] = useState<SalesMarginPoint[]>([]);
  const [valuationHistory, setValuationHistory] = useState<ValuationHistoryPoint[]>([]);
  const [roceHistory, setRoceHistory] = useState<RoceHistoryPoint[]>([]);

  // Every engine below is a separate, independent fetch — each fails
  // silently into its own "not disclosed"/omitted state (never a crash)
  // exactly like the single sector-KPI fetch this replaces. The Editorial
  // Report is meant to be the one place that surfaces every analysis this
  // platform runs on a company, so it now pulls from every engine tab
  // (P&L/Balance Sheet/Cash Flow/Quarterly/ROE/Concall/News/AI), not just
  // the sector-KPI subset it used to.
  useEffect(() => {
    let cancelled = false;
    const companyId = analysis.company_info?.stock_id || analysis.stock_id;
    api.getQuarterlyIntelligence(companyId)
      .then((d) => { if (!cancelled) setQi(d); })
      .catch(() => { /* leave null -> renders as unavailable, not a crash */ })
      .finally(() => { if (!cancelled) setKpiLoaded(true); });
    api.getCompanySummary(companyId)
      .then((d) => { if (!cancelled) setCompanySummary(d.summary ?? null); })
      .catch(() => { /* leave null -> section omitted, not a crash */ });
    api.getPlIntelligence(companyId).then((d) => { if (!cancelled) setPli(d); }).catch(() => {});
    api.getBalanceSheetIntelligence(companyId).then((d) => { if (!cancelled) setBsi(d); }).catch(() => {});
    api.getCashFlowIntelligence(companyId).then((d) => { if (!cancelled) setCfi(d); }).catch(() => {});
    api.getBankRoe(companyId).then((d) => { if (!cancelled) setBankRoe(d); }).catch(() => {});
    api.getConcallIntelligence(companyId).then((d) => { if (!cancelled) setConcall(d); }).catch(() => {});
    api.getCompanyNews(companyId).then((d) => { if (!cancelled) setNews(d.news || []); }).catch(() => {});
    api.getEarningsCalendar(companyId).then((d) => { if (!cancelled) setCalendar(d.calendar ?? null); }).catch(() => {});
    api.getAnalystConsensus(companyId).then((d) => { if (!cancelled) setAnalystConsensus(d.by_source || {}); }).catch(() => {});
    // Charts, matching the live dashboard's Overview/Peer tabs (2026-09-21,
    // user's explicit "I want the charts as well as in live dashboard" —
    // the report was previously text/table-only everywhere).
    api.getPremiumExtras(companyId)
      .then((d) => {
        if (cancelled) return;
        setPriceChart(d.price_chart || { "1y": [], "5y": [] });
        setPerfSeries(d.peer_performance?.series || []);
      })
      .catch(() => {});
    api.getHistoryCharts(companyId)
      .then((d) => {
        if (cancelled) return;
        setSalesMargins(d.sales_and_margins || []);
        setValuationHistory(d.valuation || []);
        setRoceHistory(d.roce_history || []);
      })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [analysis.stock_id, analysis.company_info?.stock_id, analysis.id, analysis.completed_at]);

  const sectorKpis = qi?.sector_kpis ?? null;
  const blueprintSections = (analysis.report_blueprint?.sections ?? []).filter((s) => s.id !== "key_questions");

  const company = analysis.company_info;
  const scores = analysis.scores;
  const sector = analysis.sector_analysis;
  const ai = analysis.ai_analysis;
  const metrics = analysis.metrics;
  const peers = analysis.peers;
  const { headline, band } = scoreBand(analysis.overall_score);

  const priceChart1y = priceChart["1y"] ?? [];
  const pnlBridge = latestPnlBridge(metrics);
  const weightSlices: DonutSlice[] = scores?.weights
    ? Object.entries(scores.weights)
        .filter(([, w]) => w !== null && w !== undefined && w > 0)
        .map(([key, w]) => ({ name: SCORE_DIMENSION_LABEL[key] || key.replace(/_/g, " "), value: w as number, color: CATEGORY_COLORS[key] || "#a9b3c9" }))
    : [];

  const dimEntries = (["growth", "profitability", "cash_flow", "balance_sheet", "efficiency", "valuation"] as const)
    .map((k) => ({ key: k, label: SCORE_DIMENSION_LABEL[k], value: scores?.[k] ?? null }))
    .filter((d) => d.value !== null);
  const strongest = dimEntries.length ? dimEntries.reduce((a, b) => (b.value! > a.value! ? b : a)) : null;
  const weakest = dimEntries.length ? dimEntries.reduce((a, b) => (b.value! < a.value! ? b : a)) : null;

  // `metrics.revenue_series` is yfinance-sourced, in raw Rupees (confirmed live
  // on GPT Healthcare: FY2026 = 4,723,486,000 = Rs 472.3 Cr) — every other
  // absolute-currency yfinance series in this codebase needs the same /1e7
  // Rupees-to-Crores conversion (see balance_sheet_intelligence/snapshot.py's
  // `yfinance_value_in_crores` for the backend precedent this mirrors).
  const toCr = (v: number | null | undefined): number | null => (v == null ? null : v / 1e7);
  const years = metrics?.years_available ?? [];
  const revenueSeries = years.map((y) => ({ year: y, value: toCr(metrics?.revenue_series?.[y]) }));
  const hasRevenue = revenueSeries.some((p) => p.value !== null);
  const maxRevenue = Math.max(1, ...revenueSeries.map((p) => p.value ?? 0));

  const latestYear = years.at(-1);
  // Screener's own Ratios section is a real multi-year table (confirmed
  // live 2026-09-22, user's own report — "we can take ROCE directly from
  // screener right?") — ingest_ratios() previously only stored the latest
  // year (openscreener's own parser discarded the rest; fixed at the
  // source, see screener_client.py's docstring). Preferred here over
  // metrics.roce_series (yfinance) wherever it has a value for a given
  // year, computed ONCE so every consumer (this latest-value card, the
  // peer-scatter subject point, the trend chart+table below) agrees —
  // previously roceLatest stayed yfinance-only even after the chart
  // below was fixed to prefer Screener, showing two different "latest
  // ROCE" numbers in the same report.
  const screenerRoceSeries: Record<string, number> = {};
  for (const p of roceHistory) {
    if (p.roce != null) screenerRoceSeries[`FY${p.period.slice(0, 4)}`] = p.roce;
  }
  const mergedRoceSeries: Record<string, number | null> = {};
  for (const y of years) mergedRoceSeries[y] = screenerRoceSeries[y] ?? metrics?.roce_series?.[y] ?? null;
  const roceUsesScreener = Object.keys(screenerRoceSeries).length > 0;
  const roceLatest = latestYear ? mergedRoceSeries[latestYear] ?? null : null;
  const ebitdaMarginLatest = latestYear ? metrics?.ebitda_margin_series?.[latestYear] ?? null : null;

  const namedPeers: PeerEntry[] = (peers?.peers ?? []).slice(0, 8);
  const sectorMedians = peers?.sector_medians ?? {};
  const sectorMetricIds = peers?.sector_metric_ids ?? [];
  const sectorMetricMeta = new Map((sector?.key_metrics ?? []).map((m) => [m.name, m]));
  const sectorMetricRows = sectorMetricIds.map((id) => sectorMetricMeta.get(id)).filter((m): m is SectorMetric => !!m);
  const hasAnySectorMetricValue = sectorMetricRows.some((m) =>
    (peers?.company_metrics?.[m.name] ?? null) !== null || namedPeers.some((p) => (p.sector_metrics?.[m.name] ?? null) !== null));

  const availableKeyMetrics: SectorMetric[] = (sector?.key_metrics ?? []).filter((m) => m.available !== false && m.value !== null && m.value !== undefined);
  const unavailableKeyMetrics: SectorMetric[] = (sector?.key_metrics ?? []).filter((m) => m.available === false || m.value === null || m.value === undefined);

  const investmentView = ai?.rating || analysis.ai_rating || scores?.overall_rating || "—";
  const today = new Date().toLocaleDateString("en-IN", { day: "2-digit", month: "long", year: "numeric" });

  return (
    <div className="er-root">
      <style>{EDITORIAL_CSS}</style>
      <div className="er-shell">
        <aside className="er-rail">
          <div className="er-mark"><span className="er-mark-icon">{(company?.company_name || "?").charAt(0)}</span> Fundamental research</div>
          <div className="er-rail-title">{company?.company_name || analysis.stock_id}</div>
          <small>{company?.exchange}:{company?.symbol} · editorial edition</small>
          <nav className="er-toc">
            <a href="#er-summary">01 · Executive view</a>
            <a href="#er-business">02 · Business &amp; operations</a>
            <a href="#er-quarterly">03 · Quarterly momentum</a>
            <a href="#er-financials">04 · Financial trajectory</a>
            <a href="#er-pl">05 · P&amp;L quality &amp; structure</a>
            <a href="#er-bs">06 · Balance sheet architecture</a>
            <a href="#er-cf">07 · Cash flow quality</a>
            {bankRoe?.available && <a href="#er-roe">08 · ROE-driven valuation</a>}
            <a href="#er-valuation">09 · Scoring &amp; multiples</a>
            <a href="#er-peer">10 · Peer benchmark</a>
            <a href="#er-risks">11 · Risks &amp; scenarios</a>
            <a href="#er-concall">12 · Concalls &amp; guidance</a>
            <a href="#er-market">13 · News &amp; analyst view</a>
            <a href="#er-ai">14 · AI analysis</a>
            <a href="#er-research">15 · Deep research</a>
            <a href="#er-review">16 · Methodology &amp; sources</a>
          </nav>
          <div className="er-rail-foot">Generated from analysis {analysis.id}.<br />Snapshot: {today}</div>
        </aside>

        <main className="er-main">
          <div className="er-topbar">
            <span>Editorial research · {company?.sector || "—"}</span>
            <div className="er-topbar-actions">
              <span>{analysis.id}</span>
              <button className="er-button" onClick={() => window.print()}>Print / save PDF</button>
            </div>
          </div>

          {/* Cover */}
          <section className="er-cover" aria-label="Cover page">
            <div className="er-cover-top">
              <span className="er-cover-kicker">Institutional research · editorial edition</span>
              <span className="er-cover-date">{today}</span>
            </div>
            <div>
              <h1>{company?.company_name || analysis.stock_id}</h1>
              <p className="er-cover-deck">{company?.sector || "—"}{company?.industry ? ` · ${company.industry}` : ""}{company?.basic_industry ? ` · ${company.basic_industry}` : ""}</p>
              {/* Price/market-cap deliberately NOT repeated here — real
                  duplication found live 2026-09-22 (user's own report —
                  "first 2 pages seem identical"): this cover and the metric
                  cards row right after it (same page now, see the removed
                  er-page-break below) both showed price/market-cap, and the
                  cover's own score facts duplicated the hero's score ring
                  below too. Cover now carries only what's genuinely unique
                  to a title page — the investment view and the headline
                  score — everything else (price, market cap, P/E, 52-week
                  range, revenue, sector) lives in exactly one place: the
                  metric cards row. */}
              <div className="er-cover-grid" style={{ gridTemplateColumns: "repeat(2,1fr)" }}>
                <div className="er-cover-fact"><span>Investment view</span><strong>{investmentView}</strong></div>
                <div className="er-cover-fact"><span>Deterministic score{" "}<Tag kind="calculated" /></span><strong>{analysis.overall_score ?? "—"} / 100</strong></div>
              </div>
              <div className="er-cover-thesis">
                <div>
                  <h3>Executive summary {ai?.executive_summary ? <Tag kind="ai" /> : null}</h3>
                  <p>{ai?.executive_summary || `${headline} Score dimensions are shown in the Ratios & Valuation section.`}</p>
                </div>
                <div className="er-cover-stamp">{band}<br /><span style={{ fontWeight: 500, letterSpacing: 0, textTransform: "none" }}>Not investment advice</span></div>
              </div>
            </div>
            <div className="er-cover-bottom">
              <span>{company?.exchange} · {company?.symbol}</span>
              <span>{latestYear ? `FY ending ${latestYear}` : "Annual period n/a"} · price as of {company?.current_price?.as_of ? new Date(company.current_price.as_of).toLocaleDateString("en-IN") : "—"}</span>
              <span>Source: {company?.current_price?.source || "—"}</span>
            </div>
          </section>

          {/* 01 Executive view */}
          <header className="er-hero" id="er-summary">
            <div className="er-hero-grid">
              <div>
                <div className="er-kicker">Editorial report · {today}</div>
                <h1>{headline}</h1>
                {strongest && weakest && strongest.key !== weakest.key && (
                  <p className="er-hero-sub">
                    {strongest.label.charAt(0).toUpperCase() + strongest.label.slice(1)} ({strongest.value}/100) is the strongest measured dimension;
                    {" "}{weakest.label} ({weakest.value}/100) is the weakest. <Tag kind="calculated" />
                  </p>
                )}
                <div className="er-hero-meta">
                  <span className="er-pill">{company?.exchange} · {company?.symbol}</span>
                  <span className="er-pill">{company?.sector || "—"}</span>
                  {company?.market_cap_category && <span className="er-pill">{company.market_cap_category.replace(/_/g, " ")}</span>}
                  <span className="er-pill">Data quality {analysis.data_quality_score != null ? `${analysis.data_quality_score.toFixed(1)}%` : "—"}</span>
                </div>
              </div>
              <div className="er-score-card">
                <div className="er-score-ring" style={{ background: `conic-gradient(var(--er-gold) 0 ${Math.min(100, Math.max(0, analysis.overall_score ?? 0))}%, rgba(255,255,255,.12) ${Math.min(100, Math.max(0, analysis.overall_score ?? 0))}% 100%)` }}>
                  <div><strong>{analysis.overall_score ?? "—"}</strong><span>out of 100</span></div>
                </div>
                <div><div className="er-score-label">{band}</div><div className="er-score-note">Deterministic score<br />Confidence {analysis.confidence_score != null ? `${analysis.confidence_score.toFixed(1)}%` : "—"}</div></div>
              </div>
            </div>
          </header>

          <section className="er-section">
            <div className="er-grid er-grid-3">
              <MetricCard label="Price" value={company?.current_price?.price != null ? `₹${company.current_price.price.toFixed(2)}` : NA}
                          foot={company?.current_price?.change_pct != null ? `${company.current_price.change_pct >= 0 ? "+" : ""}${company.current_price.change_pct.toFixed(2)}% today` : undefined} kind="reported" />
              <MetricCard label="Market cap" value={company?.market_cap != null ? `₹${(company.market_cap / 1e7).toLocaleString("en-IN", { maximumFractionDigits: 0 })} Cr` : NA}
                          foot={company?.market_cap_category?.replace(/_/g, " ")} kind="reported" />
              <MetricCard label="P/E (TTM)" value={fmtNum(metrics?.pe_ratio ?? null, "x")} foot="Trailing twelve months" kind="reported" />
              <MetricCard label="52-week range" value={company?.week52_low != null && company?.week52_high != null ? `₹${company.week52_low.toLocaleString("en-IN")} – ₹${company.week52_high.toLocaleString("en-IN")}` : NA}
                          foot="Yahoo Finance" kind="reported" />
              <MetricCard label={`${latestYear || "Latest"} revenue`} value={latestYear ? fmtNum(toCr(metrics?.revenue_series?.[latestYear]), "cr") : NA}
                          foot={sector?.key_metrics?.find((m) => m.name === "revenue_cagr_3y")?.value != null ? `3-year CAGR: ${sector!.key_metrics!.find((m) => m.name === "revenue_cagr_3y")!.value}%` : undefined} kind="reported" />
              <MetricCard label="Sector framework" value={sector?.sector_name || NA} foot={sector?.sector_matched ? "Sector-specific scoring applied" : "Generic framework — sector not matched"} kind="calculated" />
            </div>
          </section>

          {(priceChart1y.length > 0 || pnlBridge.length > 0) && (
            <section className="er-section">
              {/* Full-width, stacked — not side-by-side — real gap found
                  live (user's own report, 2026-09-23: "I want the chart to
                  be big", "I don't want 2 line charts in single line"):
                  every chart in this report used to get squeezed to half
                  width whenever it was paired with another card in a
                  2-column grid, leaving both noticeably smaller and harder
                  to read than they need to be. Applied consistently to
                  every chart-pair in this file, not just this one. */}
              <div className="er-grid er-grid-2" style={{ gridTemplateColumns: "1fr" }}>
                {priceChart1y.length > 1 && (
                  <div className="er-card er-chart-card">
                    <div className="er-chart-title"><div><h3>Price, trailing 1 year</h3><p>Daily close <Tag kind="reported" /></p></div></div>
                    <EditorialPriceChart points={priceChart1y} />
                  </div>
                )}
                {pnlBridge.length > 0 && (
                  <div className="er-card er-chart-card">
                    <div className="er-chart-title"><div><h3>P&amp;L bridge — {latestYear || "latest year"}</h3><p>Revenue → EBITDA → PAT <Tag kind="calculated" /></p></div></div>
                    <WaterfallChart steps={pnlBridge} formatter={(v) => `₹${(v / 1e7).toFixed(0)}Cr`} />
                    <ChartLegend items={[
                      { color: "#c9a227", label: "Revenue / EBITDA / PAT (totals)", shape: "square" },
                      { color: "#4fb3a0", label: "Increase to next total", shape: "square" },
                      { color: "#e0793c", label: "Decrease to next total", shape: "square" },
                    ]} />
                  </div>
                )}
              </div>
            </section>
          )}

          <section className="er-section">
            <div className="er-verdict er-card">
              <div className="er-accent-line" />
              <h3>Bottom line</h3>
              <p>{ai?.financial_health_summary || ai?.executive_summary || `Overall score ${analysis.overall_score ?? "—"}/100 (${band}). See the Ratios & Valuation section for the full score breakdown.`} {ai?.financial_health_summary ? <Tag kind="ai" /> : <Tag kind="calculated" />}</p>
            </div>
          </section>

          {/* 02 Business & operations */}
          <section className="er-section" id="er-business">
            <div className="er-section-head">
              <div><div className="er-eyebrow">02 · Business &amp; operations</div><h2>Sector-specific operating metrics.</h2></div>
              <p>{sector?.description || `${sector?.sector_name || "This sector's"} framework applied to this company's disclosed operating metrics.`}</p>
            </div>

            {kpiLoaded && sectorKpis?.available && sectorKpis.metrics && sectorKpis.metrics.length > 0 ? (
              <div className="er-card" style={{ marginBottom: 16 }}>
                <div className="er-chart-title">
                  <div><div className="er-eyebrow">Quarterly operating KPIs</div><h3>Latest disclosed quarter: {sectorKpis.latest_quarter || "—"}</h3></div>
                  <span className="er-tag er-tag-info">{sectorKpis.statement_type || "—"}{sectorKpis.single_statement_source ? " · single source" : ""}</span>
                </div>
                <div className="er-grid er-grid-3">
                  {sectorKpis.metrics.map((m) => (
                    <div key={m.metric_key} className="er-hospital">
                      <h4>{m.label}</h4>
                      <p><b>{m.latest_value != null ? fmtNum(m.latest_value, m.unit) : NA}</b>{m.latest_period ? ` · ${m.latest_period}` : ""}</p>
                      <p style={{ fontSize: 10, marginTop: 2 }}>{m.source_label || "Source not recorded"} <Tag kind={m.confidence === "HIGH" ? "reported" : "calculated"} /></p>
                    </div>
                  ))}
                </div>
              </div>
            ) : kpiLoaded ? (
              <div className="er-callout er-callout-blue"><div className="er-icon">i</div><div><strong>Quarterly operating KPIs</strong>{NA} for this sector/company — see the Methodology section for how this gap is tracked.</div></div>
            ) : null}

            {availableKeyMetrics.length > 0 && (
              // er-card-flowing, not a plain er-card — real gap found live
              // on TANLA (2026-09-23, user's own report — "3rd page looks
              // so blank"): an IT-sector company's key-metrics table has
              // enough rows (CAGRs, margins, ROCE, leverage, multiples...)
              // that the whole card often doesn't fit in whatever space is
              // left on the page after the short "Quarterly operating
              // KPIs" callout above it — the blanket break-inside:avoid
              // rule then pushed the ENTIRE table to the next page rather
              // than letting it split at a row boundary (already safe:
              // tr{break-inside:avoid} plus thead{display:table-header-group}
              // repeat the header), leaving the previous page mostly blank.
              // Same fix already applied to the concall highlights card.
              <div className="er-card er-card-flowing" style={{ marginTop: 16, overflow: "auto" }}>
                <div className="er-chart-title"><div><h3>Sector key metrics</h3><p>Company value vs sector median, from the {sector?.sector_name || "sector"} framework</p></div></div>
                <table>
                  <thead><tr><th>Metric</th><th className="er-right">Value</th><th className="er-right">Sector median</th><th className="er-right">Percentile</th><th>Status</th></tr></thead>
                  <tbody>
                    {availableKeyMetrics.map((m) => (
                      <tr key={m.name}>
                        <td>{m.label || m.name}</td>
                        <td className="er-right"><ValueTag value={fmtNum(typeof m.value === "number" ? m.value : null, m.unit)} kind="reported" /></td>
                        <td className="er-right"><ValueTag value={m.sector_median != null ? fmtNum(m.sector_median, m.unit) : "—"} kind={m.sector_median != null ? "benchmark" : null} /></td>
                        <td className="er-right">{m.sector_percentile != null ? `${m.sector_percentile}th` : "—"}</td>
                        <td><StatusTag status={m.status} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {unavailableKeyMetrics.length > 0 && (
              <div className="er-callout er-callout-blue" style={{ marginTop: 16 }}>
                <div className="er-icon">i</div>
                <div><strong>Not measured for this company</strong>{unavailableKeyMetrics.map((m) => m.label || m.name).join(", ")} — {unavailableKeyMetrics[0]?.na_message || NA}.</div>
              </div>
            )}

            {companySummary?.key_points && (
              <div className="er-card" style={{ marginTop: 16 }}>
                <div className="er-chart-title">
                  <div><div className="er-eyebrow">Company overview</div><h3>As described by {companySummary.source || "a third-party source"}</h3></div>
                  <Tag kind="third_party" />
                </div>
                <p className="er-muted" style={{ whiteSpace: "pre-line", fontSize: 12.5, lineHeight: 1.7 }}>{companySummary.key_points}</p>
                <p style={{ fontSize: 10, color: "var(--er-faint)", marginTop: 10 }}>
                  This is {companySummary.source || "a third-party provider"}'s own AI-assisted company summary (numbered citations, where present, are theirs) —
                  not independently re-verified against primary filings by this platform. Any facility, capacity or expansion detail here may describe a
                  planned or in-progress item, not necessarily a currently operating one; cross-check against the Reported figures above before relying on it.
                </p>
              </div>
            )}
          </section>

          {/* 03 Quarterly momentum */}
          <section className="er-section" id="er-quarterly">
            <div className="er-section-head">
              <div><div className="er-eyebrow">03 · Quarterly momentum</div><h2>How the most recently reported quarter compares.</h2></div>
              <p>{kpiLoaded && qi?.period ? `${qi.quarters_available} quarter(s) on record · latest ${qi.period} (${qi.statement_type}).` : NA} <Tag kind="reported" /></p>
            </div>
            {kpiLoaded && qi?.period ? (() => {
              const period = qi.period;
              const periods = Object.keys(qi.series.sales || {}).sort();
              const netMarginSeries: Record<string, number> = {};
              for (const period of periods) {
                const sales = qi.series.sales?.[period];
                const netProfit = qi.series.net_profit?.[period];
                if (sales && netProfit !== undefined && netProfit !== null) netMarginSeries[period] = (netProfit / sales) * 100;
              }
              const opmStats = marginSeriesStats(qi.series.opm || {});
              const npmStats = marginSeriesStats(netMarginSeries);
              const flagsByPeriod = new Map<string, string[]>();
              for (const f of qi.flags) flagsByPeriod.set(f.period, [...(flagsByPeriod.get(f.period) || []), readable(f.flag)]);
              const periodsDesc = [...periods].reverse();

              // Previous-period → present, so the reader sees the actual
              // rupee figures a QoQ/YoY % was built from, not just the
              // percentage on its own — real gap found live (user's own
              // report, 2026-09-23: "I want the values, not just
              // percentage. Previous quarter values - Present, then
              // percentage"). QoQ's "previous" is simply the immediately
              // preceding period on record; YoY's is the same calendar
              // quarter one year back (matches the backend's own
              // yoy_growth() pairing, not a fixed index offset, since a
              // quarter can be missing from the ledger).
              const qoqPrevPeriod = periods[periods.indexOf(period) - 1];
              const yoyPrevPeriod = (() => {
                const d = new Date(period);
                if (Number.isNaN(d.getTime())) return undefined;
                d.setUTCFullYear(d.getUTCFullYear() - 1);
                return d.toISOString().slice(0, 10);
              })();
              const trend = (series: Record<string, number> | undefined, prevPeriod: string | undefined, pct: number | null | undefined) => {
                const prevVal = prevPeriod ? series?.[prevPeriod] : undefined;
                const currVal = series?.[period];
                const values = prevVal != null && currVal != null ? `${fmtNum(prevVal, "cr")} → ${fmtNum(currVal, "cr")}` : (currVal != null ? fmtNum(currVal, "cr") : NA);
                return { value: values, foot: fmtNum(pct, "%") };
              };
              const salesQoQ = trend(qi.series.sales, qoqPrevPeriod, qi.qoq.sales[period]);
              const salesYoY = trend(qi.series.sales, yoyPrevPeriod, qi.yoy.sales[period]);
              const npQoQ = trend(qi.series.net_profit, qoqPrevPeriod, qi.qoq.net_profit[period]);
              const npYoY = trend(qi.series.net_profit, yoyPrevPeriod, qi.yoy.net_profit[period]);

              return (
                <>
                  <div className="er-grid er-grid-4">
                    <MetricCard label="Sales QoQ" value={salesQoQ.value} foot={salesQoQ.foot} kind="calculated" />
                    <MetricCard label="Sales YoY" value={salesYoY.value} foot={salesYoY.foot} kind="calculated" />
                    <MetricCard label="Net profit QoQ" value={npQoQ.value} foot={npQoQ.foot} kind="calculated" />
                    <MetricCard label="Net profit YoY" value={npYoY.value} foot={npYoY.foot} kind="calculated" />
                  </div>
                  {periods.length > 1 && (
                    <div className="er-card er-chart-card" style={{ marginTop: 16 }}>
                      <div className="er-chart-title"><div><h3>Trailing quarters — sales, operating &amp; net margin</h3><p>Bars = sales (₹Cr); lines = margin % <Tag kind="calculated" /></p></div></div>
                      <ComboTrendChart
                        barData={qi.series.sales || {}} lineData={qi.series.opm || {}} lineData2={netMarginSeries}
                        barLabel="Sales" lineLabel="OPM %" line2Label="Net Margin %"
                        barColor="#c79a3b" lineColor="#bd624d" line2Color="#1f5d55"
                        barFormatter={(v) => `₹${v.toFixed(0)}Cr`} lineFormatter={(v) => `${v.toFixed(1)}%`}
                        height={220}
                      />
                      <ChartLegend items={[
                        { color: "#c79a3b", label: "Sales", shape: "square" },
                        { color: "#bd624d", label: "OPM %", shape: "circle" },
                        { color: "#1f5d55", label: "Net Margin %", shape: "circle" },
                      ]} />
                    </div>
                  )}
                  <div className="er-grid er-grid-2" style={{ marginTop: 16 }}>
                    <div className="er-card">
                      <div className="er-chart-title"><div><h3>Margin trend</h3><p>Trailing {Math.min(8, qi.quarters_available)} quarters, operating &amp; net margin <Tag kind="calculated" /></p></div></div>
                      <div className="er-mini-stat"><span>Operating margin direction</span><strong>{readable(qi.margin_trend.opm_direction)}</strong></div>
                      <div className="er-mini-stat"><span>Operating margin — latest</span><strong>{fmtNum(opmStats.latest, "%")}</strong></div>
                      <div className="er-mini-stat"><span>Operating margin — range (low–high)</span><strong>{opmStats.min != null && opmStats.max != null ? `${opmStats.min.toFixed(1)}% – ${opmStats.max.toFixed(1)}%` : "—"}</strong></div>
                      <div className="er-mini-stat" style={{ marginTop: 10 }}><span>Net margin direction</span><strong>{readable(qi.margin_trend.net_margin_direction)}</strong></div>
                      <div className="er-mini-stat"><span>Net margin — latest</span><strong>{fmtNum(npmStats.latest, "%")}</strong></div>
                      <div className="er-mini-stat"><span>Net margin — range (low–high)</span><strong>{npmStats.min != null && npmStats.max != null ? `${npmStats.min.toFixed(1)}% – ${npmStats.max.toFixed(1)}%` : "—"}</strong></div>
                      <p className="er-muted" style={{ fontSize: 11, marginTop: 10 }}>
                        "Volatile" means the quarter-on-quarter swing exceeds this framework's stable/expanding/compressing thresholds in both directions within the window, rather than moving consistently one way — see the full quarter-by-quarter figures below.
                      </p>
                    </div>
                    <div className="er-card er-card-flowing">
                      <div className="er-chart-title"><div><h3>What changed, trailing quarters</h3><p>Deterministic diagnostics over the last {Math.min(8, qi.quarters_available)} quarters on record, grouped by quarter — not AI commentary</p></div></div>
                      <GroupedFlagList
                        emptyMessage="No sequential-deceleration, margin-inflection, other-income-dependency or tax-rate flags raised in the trailing quarters on record."
                        flags={qi.flags}
                      />
                    </div>
                  </div>
                  {periodsDesc.length > 0 && (
                    <div className="er-card" style={{ marginTop: 16, overflow: "auto" }}>
                      <div className="er-chart-title"><div><h3>Every trailing quarter, not just the flagged ones</h3><p>The full series the diagnostics above were computed from — so a flag landing on the same calendar quarter across years is checkable, not asserted. Most recent quarter first.</p></div></div>
                      <table>
                        <thead><tr><th>Period</th><th className="er-right">Sales</th><th className="er-right">Sales QoQ</th><th className="er-right">OPM</th><th className="er-right">Net margin</th><th className="er-right">PAT</th><th className="er-right">PAT QoQ</th><th>Flags raised this quarter</th></tr></thead>
                        <tbody>
                          {periodsDesc.map((p) => {
                            const flags = flagsByPeriod.get(p) || [];
                            return (
                              <tr key={p}>
                                <td>{p}</td>
                                <td className="er-right">{fmtNum(qi.series.sales?.[p] ?? null, "cr")}</td>
                                <td className="er-right"><ValueTag value={fmtNum(qi.qoq.sales?.[p] ?? null, "%")} kind={qi.qoq.sales?.[p] != null ? "calculated" : null} /></td>
                                <td className="er-right">{fmtNum(qi.series.opm?.[p] ?? null, "%")}</td>
                                <td className="er-right">{fmtNum(netMarginSeries[p] ?? null, "%")}</td>
                                <td className="er-right">{fmtNum(qi.series.net_profit?.[p] ?? null, "cr")}</td>
                                <td className="er-right"><ValueTag value={fmtNum(qi.qoq.net_profit?.[p] ?? null, "%")} kind={qi.qoq.net_profit?.[p] != null ? "calculated" : null} /></td>
                                <td>{flags.length > 0 ? flags.join(", ") : <span className="er-muted">none</span>}</td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  )}
                </>
              );
            })() : (
              <div className="er-callout er-callout-blue"><div className="er-icon">i</div><div><strong>Quarterly analysis</strong>{NA} for this company yet.</div></div>
            )}
          </section>

          {/* 04 Financial trajectory */}
          <section className="er-section" id="er-financials">
            <div className="er-section-head">
              <div><div className="er-eyebrow">04 · Financial trajectory</div><h2>Reported financials over the available history.</h2></div>
              <p>{years.length > 0 ? `${years.length} fiscal years on record (${years[0]}–${years.at(-1)}).` : NA} <Tag kind="reported" /></p>
            </div>
            <div className="er-grid er-grid-2" style={{ gridTemplateColumns: "1fr" }}>
              <div className="er-card er-chart-card">
                <div className="er-chart-title"><div><h3>Revenue vs operating margin</h3><p>Bars = revenue (₹Cr); line = OPM % <Tag kind="reported" /></p></div></div>
                {/* Sourced from the same Screener-derived table as the
                    "Sales & margins" chart further down, NOT
                    metrics.revenue_series/ebitda_margin_series (yfinance) —
                    real gap found live on GROWW (2026-09-22, user's own
                    report, comparing directly against Screener.in's own P&L
                    page): yfinance's own multi-year coverage for a recently
                    listed company only goes back 1-2 fiscal years, so this
                    chart showed just 2 bars where Screener (which captures
                    pre-listing history from filings, not limited by listing
                    date) has 5+ years. */}
                {salesMargins.length > 0 ? (
                  <>
                    <ComboTrendChart
                      barData={toSeries(salesMargins, "sales")} lineData={toSeries(salesMargins, "opm")}
                      barLabel="Revenue" lineLabel="OPM %"
                      barColor="#c79a3b" lineColor="#bd624d"
                      barFormatter={(v) => `₹${v.toFixed(0)}Cr`} lineFormatter={(v) => `${v.toFixed(0)}%`}
                      height={280}
                    />
                    <ChartLegend items={[
                      { color: "#c79a3b", label: "Revenue", shape: "square" },
                      { color: "#bd624d", label: "OPM %", shape: "circle" },
                    ]} />
                  </>
                ) : <p className="er-muted">{NA}</p>}
              </div>
              <div className="er-card er-chart-card">
                {(() => {
                  const coveredYears = Object.values(mergedRoceSeries).filter((v) => v != null).length;
                  return (
                    <>
                      <div className="er-chart-title"><div><h3>ROCE, trailing years</h3><p>Percent · by fiscal year <Tag kind={roceUsesScreener ? "reported" : "calculated"} /></p></div></div>
                      {years.length > 1 && coveredYears > 0 ? (
                        <TrendChart data={mergedRoceSeries} color="#1f5d55" formatter={(v) => `${v.toFixed(1)}%`} height={280} />
                      ) : <p className="er-muted">{NA}</p>}
                      {years.length > 1 && (
                        <table style={{ marginTop: 10 }}>
                          <thead><tr><th>Year</th><th className="er-right">ROCE</th><th className="er-right">EBITDA margin</th></tr></thead>
                          <tbody>
                            {years.map((y) => (
                              <tr key={y}>
                                <td>{y}</td>
                                <td className="er-right"><ValueTag value={mergedRoceSeries[y] != null ? `${mergedRoceSeries[y]!.toFixed(1)}%` : "—"} kind={screenerRoceSeries[y] != null ? "reported" : mergedRoceSeries[y] != null ? "calculated" : null} /></td>
                                <td className="er-right">{metrics?.ebitda_margin_series?.[y] != null ? `${metrics!.ebitda_margin_series![y]!.toFixed(1)}%` : "—"}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      )}
                      {coveredYears > 0 && coveredYears < years.length && (
                        <p className="er-muted" style={{ fontSize: 10.5, marginTop: 10 }}>
                          {coveredYears} of {years.length} years shown{roceUsesScreener ? " (Screener's own Ratios section, cross-checked against this engine's own calculation where both are available)" : ""} —
                          the remaining year(s) aren't on record from Screener or computable from yfinance's own balance-sheet coverage for this company.
                        </p>
                      )}
                    </>
                  );
                })()}
              </div>
            </div>
            <div className="er-grid er-grid-4" style={{ marginTop: 16 }}>
              <MetricCard label="EBITDA margin (latest)" value={fmtNum(ebitdaMarginLatest, "%")} kind="reported" />
              <MetricCard label="ROCE (latest)" value={fmtNum(roceLatest, "%")} kind="reported" />
              <MetricCard label="FCF / PAT" value={fmtNum(metrics?.fcf_to_pat ?? null, "%")} kind="calculated" />
              <MetricCard label="CFO / PAT" value={fmtNum(metrics?.cfo_to_pat ?? null, "%")} kind="calculated" />
            </div>
            {salesMargins.length >= 2 && (
              <div className="er-card er-chart-card" style={{ marginTop: 16 }}>
                <div className="er-chart-title"><div><h3>Sales &amp; margins, {salesMargins.length}-year history</h3><p>Bars = sales; lines = OPM % / NPM % <Tag kind="reported" /></p></div></div>
                <ComboTrendChart
                  barData={toSeries(salesMargins, "sales")} lineData={toSeries(salesMargins, "opm")} lineData2={toSeries(salesMargins, "npm")}
                  barLabel="Sales" lineLabel="OPM %" line2Label="NPM %"
                  barColor="#c79a3b" lineColor="#bd624d" line2Color="#1f5d55"
                  barFormatter={(v) => `₹${v.toFixed(0)}Cr`} lineFormatter={(v) => `${v.toFixed(0)}%`}
                  height={240}
                />
                <ChartLegend items={[
                  { color: "#c79a3b", label: "Sales", shape: "square" },
                  { color: "#bd624d", label: "OPM %", shape: "circle" },
                  { color: "#1f5d55", label: "NPM %", shape: "circle" },
                ]} />
                <p className="er-muted" style={{ fontSize: 11, marginTop: 8 }}>Gross Profit Margin isn't shown — Screener.in's P&amp;L data has no material-cost/COGS breakdown to compute one from.</p>
              </div>
            )}
            {valuationHistory.length >= 2 && (
              <div className="er-card er-chart-card" style={{ marginTop: 16 }}>
                <div className="er-chart-title"><div><h3>EPS &amp; P/E, {valuationHistory.length}-year history</h3><p>Bars = EPS; line = P/E <Tag kind="reported" /></p></div></div>
                <ComboTrendChart
                  barData={toSeries(valuationHistory, "eps")} lineData={toSeries(valuationHistory, "pe")}
                  barLabel="EPS" lineLabel="P/E"
                  barColor="#c79a3b" lineColor="#bd624d"
                  barFormatter={(v) => `₹${v.toFixed(1)}`} lineFormatter={(v) => `${v.toFixed(1)}x`}
                  height={240}
                />
                <ChartLegend items={[
                  { color: "#c79a3b", label: "EPS", shape: "square" },
                  { color: "#bd624d", label: "P/E", shape: "circle" },
                ]} />
              </div>
            )}
          </section>

          {/* 05 P&L quality & structure */}
          <section className="er-section" id="er-pl">
            <div className="er-section-head">
              <div><div className="er-eyebrow">05 · P&amp;L quality &amp; structure</div><h2>Margin durability, growth velocity and earnings quality.</h2></div>
              <p>{pli?.period ? `${pli.period} · ${pli.statement_type}.` : NA} <Tag kind="calculated" /></p>
            </div>
            {pli?.period ? (
              <>
                {(() => {
                  const latest = pli.cascade[pli.period];
                  const cascadeSteps: WaterfallStep[] = latest
                    ? ([
                        { label: "Revenue", value: latest.revenue },
                        { label: "EBITDA", value: latest.ebitda },
                        { label: "EBIT", value: latest.ebit },
                        { label: "PBT", value: latest.pbt },
                        { label: "PAT", value: latest.pat },
                      ] as { label: string; value: number | null }[]).filter((s): s is WaterfallStep => s.value !== null)
                    : [];
                  if (cascadeSteps.length === 0) return null;
                  return (
                    <div className="er-card er-chart-card" style={{ marginBottom: 16 }}>
                      <div className="er-chart-title"><div><h3>Income cascade</h3><p>{pli.period} · {pli.statement_type} <Tag kind="reported" /></p></div></div>
                      <WaterfallChart steps={cascadeSteps} formatter={(v) => `₹${v.toFixed(0)}Cr`} />
                      <ChartLegend items={[
                        { color: "#c9a227", label: "Revenue / EBITDA / EBIT / PBT / PAT (totals)", shape: "square" },
                        { color: "#4fb3a0", label: "Increase to next total", shape: "square" },
                        { color: "#e0793c", label: "Decrease to next total", shape: "square" },
                      ]} />
                      <p className="er-muted" style={{ fontSize: 11, marginTop: 8 }}>Gross Profit isn't shown — Screener.in's P&amp;L view has no material-cost/COGS breakdown for any sector, so it's never estimated.</p>
                    </div>
                  );
                })()}
                <div className="er-grid er-grid-2">
                  <div className="er-card">
                    <div className="er-chart-title"><div><h3>P&amp;L master score</h3><p>Algorithm {pli.score.algorithm_version}</p></div></div>
                    <div className="er-mini-stat"><span>Master P&amp;L score</span><strong>{pli.score.master_pl_score ?? "—"}/100</strong></div>
                    <div className="er-mini-stat"><span>Classification</span><strong>{readable(pli.score.classification)}</strong></div>
                    <table style={{ marginTop: 10 }}>
                      <thead><tr><th>Component</th><th className="er-right">Weight</th><th className="er-right">Score</th></tr></thead>
                      <tbody>
                        {([
                          ["M1 · Sector margin", "25%", pli.score.components.M1],
                          ["M2 · Margin headroom", "20%", pli.score.components.M2],
                          ["M3 · Doubling velocity", "20%", pli.score.components.M3],
                          ["M4 · Earnings quality", "20%", pli.score.components.M4],
                          ["M5 · Structural ratio", "15%", pli.score.components.M5],
                        ] as [string, string, number | null][]).map(([label, weight, v]) => (
                          <tr key={label}><td>{label}</td><td className="er-right">{weight}</td><td className="er-right">{v ?? "—"}</td></tr>
                        ))}
                      </tbody>
                    </table>
                    <p className="er-muted" style={{ fontSize: 10.5, marginTop: 10, lineHeight: 1.5 }}>
                      <strong>M1</strong> where EBITDA margin ranks vs. sector peers (percentile) · {" "}
                      <strong>M2</strong> room for margins to expand, combined with the growth trend · {" "}
                      <strong>M3</strong> how fast revenue is compounding (years to double) · {" "}
                      <strong>M4</strong> how much of income is genuine core operating profit vs. one-off/non-operating income · {" "}
                      <strong>M5</strong> how much of consolidated revenue is the parent vs. subsidiaries (a missing component's weight is redistributed across the rest, never scored as zero). <Tag kind="calculated" />
                    </p>
                  </div>
                  <div className="er-card">
                    <div className="er-chart-title"><div><h3>Margin quality</h3><p>Direction &amp; stability</p></div></div>
                    <div className="er-mini-stat"><span>EBITDA margin</span><strong>{pairText(fmtNum(pli.margins.ebitda_margin, "%"), readable(pli.margins.ebitda_margin_direction))}</strong></div>
                    <div className="er-mini-stat"><span>PAT margin</span><strong>{pairText(fmtNum(pli.margins.pat_margin, "%"), readable(pli.margins.margin_direction))}</strong></div>
                    <div className="er-mini-stat"><span>5-year avg PAT margin</span><strong>{fmtNum(pli.margins.stability.avg_5y, "%")}</strong></div>
                    <div className="er-mini-stat"><span>Stability</span><strong>{readable(pli.margins.stability.classification)}</strong></div>
                    <div className="er-mini-stat"><span>Margin headroom</span><strong>{pairText(fmtNum(pli.margin_headroom.headroom_pct, "%"), readable(pli.margin_headroom.classification))}</strong></div>
                  </div>
                </div>

                <div className="er-grid er-grid-2" style={{ marginTop: 16 }}>
                  <div className="er-card">
                    <div className="er-chart-title"><div><h3>Growth velocity — doubling time</h3><p>Empirical where possible, CAGR-estimated otherwise</p></div></div>
                    <div className="er-mini-stat">
                      <span>Revenue doubling</span>
                      <strong>{pairText(doublingLabel(pli.doubling.revenue), readable(pli.doubling.revenue.speed))}</strong>
                    </div>
                    <div className="er-mini-stat">
                      <span>PAT doubling</span>
                      <strong>{pairText(doublingLabel(pli.doubling.pat), readable(pli.doubling.pat.speed))}</strong>
                    </div>
                    <p className="er-muted" style={{ fontSize: 12, marginTop: 10 }}>
                      {pli.doubling.velocity_comparison === "PAT_FASTER" ? "PAT is compounding faster than revenue — consistent with margin expansion / operating leverage."
                        : pli.doubling.velocity_comparison === "PAT_SLOWER" ? "PAT is compounding slower than revenue — consistent with margin compression or cost pressure."
                        : pli.doubling.velocity_comparison === "ROUGHLY_SAME" ? "PAT and revenue are doubling at a similar pace — stable underlying economics."
                        : "Insufficient data to compare revenue and PAT growth velocity."} <Tag kind="calculated" />
                    </p>
                  </div>
                  <div className="er-card">
                    <div className="er-chart-title"><div><h3>Earnings quality index</h3><p>Core operating income vs. total income</p></div></div>
                    {pli.earnings_quality.eqi != null && (
                      <DonutChart
                        data={[
                          { name: "Core operating income", value: pli.earnings_quality.eqi, color: "#1f5d55" },
                          { name: "Non-core / other income", value: 1 - pli.earnings_quality.eqi, color: "#bd624d" },
                        ]}
                        formatter={(v) => `${(v * 100).toFixed(0)}%`}
                        height={140}
                      />
                    )}
                    <div className="er-mini-stat"><span>EQI</span><strong>{pli.earnings_quality.eqi != null ? `${(pli.earnings_quality.eqi * 100).toFixed(0)}%` : "—"}</strong></div>
                    <div className="er-mini-stat"><span>Classification</span><strong>{readable(pli.earnings_quality.classification)}</strong></div>
                    <div className="er-mini-stat"><span>Core operating income</span><strong>{fmtNum(pli.earnings_quality.core_operating_income, "cr")}</strong></div>
                    <div className="er-mini-stat"><span>Total income</span><strong>{fmtNum(pli.earnings_quality.total_income, "cr")}</strong></div>
                  </div>
                </div>

                <div className="er-grid er-grid-2" style={{ marginTop: 16 }}>
                  <div className="er-card">
                    <div className="er-chart-title"><div><h3>Corporate structure</h3><p>Standalone vs. consolidated</p></div></div>
                    <div className="er-mini-stat"><span>Standalone revenue</span><strong>{fmtNum(pli.structure.standalone_revenue, "cr")}</strong></div>
                    <div className="er-mini-stat">
                      <span>Consolidated revenue</span>
                      <strong>
                        {pli.structure.consolidated_revenue != null
                          ? fmtNum(pli.structure.consolidated_revenue, "cr")
                          : pli.structure.consolidated_ever_reported
                            ? NA
                            : "No consolidated filing (standalone-only)"}
                      </strong>
                    </div>
                    <div className="er-mini-stat">
                      <span>Consolidation-to-standalone ratio (CSR)</span>
                      <strong>
                        {pli.structure.csr != null
                          ? pairText(pli.structure.csr.toFixed(2), readable(pli.structure.csr_band))
                          : pli.structure.consolidated_ever_reported ? NA : "N/A — standalone-only"}
                      </strong>
                    </div>
                    <div className="er-mini-stat"><span>Structure</span><strong>{pli.structure.sotp_required ? "Sum-of-the-parts required" : "Single business"}{pli.structure.segment_count > 0 ? ` · ${pli.structure.segment_count} material segment(s)` : ""}</strong></div>
                    {pli.structure.segment_names.length > 0 && (
                      <p className="er-muted" style={{ fontSize: 12, marginTop: 8 }}>Segments: {pli.structure.segment_names.join(", ")}.</p>
                    )}
                    {!pli.structure.consolidated_ever_reported && (
                      <p className="er-muted" style={{ fontSize: 12, marginTop: 8 }}>
                        No consolidated financial statements found on Screener for this company (verified directly) — treated as a standalone-only entity, not a data gap.
                      </p>
                    )}
                  </div>
                  <div className="er-card">
                    <div className="er-chart-title"><div><h3>Operating leverage</h3><p>How EBITDA and PAT move relative to revenue</p></div></div>
                    <div className="er-mini-stat"><span>EBITDA vs. revenue</span><strong>{readable(pli.diagnostics.operating_leverage.ebitda_vs_revenue)}</strong></div>
                    <div className="er-mini-stat"><span>Operating leverage</span><strong>{readable(pli.diagnostics.operating_leverage.operating_leverage)}</strong></div>
                    <div className="er-mini-stat"><span>PAT vs. EBITDA</span><strong>{readable(pli.diagnostics.operating_leverage.pat_vs_ebitda)}</strong></div>
                    {pli.diagnostics.margin_cascade_break && (
                      <p className="er-muted" style={{ fontSize: 12, marginTop: 8 }}>
                        Margin cascade break detected ({pli.diagnostics.margin_cascade_break.severity}, {readable(pli.diagnostics.margin_cascade_break.type)}):{" "}
                        {pli.diagnostics.margin_cascade_break.likely_drivers.join(", ")}.
                      </p>
                    )}
                  </div>
                </div>

                <div className="er-card" style={{ marginTop: 16 }}>
                  <div className="er-chart-title"><div><h3>Diagnostic flags</h3><p>Deterministic signals raised from the P&amp;L cascade</p></div></div>
                  <FlagList items={pli.diagnostic_flags.map((f) => ({
                    label: f.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
                    tone: (f === "margin_expansion_candidate" || f === "near_sector_peak") ? "good" as const : "watch" as const,
                  }))} />
                </div>
              </>
            ) : (
              <div className="er-callout er-callout-blue"><div className="er-icon">i</div><div><strong>P&amp;L Intelligence</strong>{NA} for this company/statement type.</div></div>
            )}
          </section>

          {/* 06 Balance sheet architecture */}
          <section className="er-section" id="er-bs">
            <div className="er-section-head">
              <div><div className="er-eyebrow">06 · Balance sheet architecture</div><h2>How the business is funded and how it deploys capital.</h2></div>
              <p>{bsi?.period ? `${bsi.period} · ${bsi.statement_type}.` : NA} <Tag kind="reported" /></p>
            </div>
            {bsi?.period && bsi.balance_sheet_integrity.status !== "BALANCE_SHEET_INTEGRITY_ERROR" ? (
              <>
                <div className="er-verdict er-card" style={{ marginBottom: 16 }}>
                  <div className="er-accent-line" />
                  <h3>{readable(bsi.archetype.classification)} <Tag kind="calculated" /></h3>
                  {bsi.archetype.evidence.length > 0 && (
                    <ul style={{ marginTop: 8, paddingLeft: 18, fontSize: 13, color: "var(--er-muted)" }}>
                      {bsi.archetype.evidence.map((e, i) => <li key={i}>{e}</li>)}
                    </ul>
                  )}
                </div>

                {bsi.archetype.classification === "NOT_APPLICABLE" && bsi.financial_institution_summary ? (
                  <div className="er-grid er-grid-4">
                    <MetricCard label="Deposits" value={fmtNum(bsi.financial_institution_summary.deposits, "cr")} kind="reported" />
                    <MetricCard label="Borrowings" value={fmtNum(bsi.financial_institution_summary.borrowings, "cr")} kind="reported" />
                    <MetricCard label="Investments" value={fmtNum(bsi.financial_institution_summary.investments, "cr")} kind="reported" />
                    <MetricCard label="Total assets" value={fmtNum(bsi.financial_institution_summary.total_assets, "cr")} kind="reported" />
                  </div>
                ) : (
                  <div className="er-grid er-grid-2">
                    <div className="er-card">
                      <div className="er-chart-title"><div><h3>Leverage &amp; capital efficiency</h3></div></div>
                      <div className="er-mini-stat"><span>Debt / equity</span><strong>{fmtNum(bsi.derived_metrics.debt_to_equity, "x")}</strong></div>
                      <div className="er-mini-stat"><span>Net debt</span><strong>{fmtNum(bsi.derived_metrics.net_debt, "cr")}{bsi.derived_metrics.net_cash_position ? " (net cash)" : ""}</strong></div>
                      <div className="er-mini-stat"><span>Net debt / EBITDA</span><strong>{fmtNum(bsi.derived_metrics.net_debt_to_ebitda, "x")}</strong></div>
                      <div className="er-mini-stat"><span>ROCE</span><strong>{fmtNum(bsi.derived_metrics.roce, "%")}</strong></div>
                      <div className="er-mini-stat"><span>EBIT margin × capital turnover</span><strong>{pairText(fmtNum(bsi.derived_metrics.ebit_margin, "%"), fmtNum(bsi.derived_metrics.capital_employed_turnover, "x"), " × ")}</strong></div>
                    </div>
                    <div className="er-card">
                      <div className="er-chart-title"><div><h3>Working capital</h3><p>Closing-balance / total-revenue methodology</p></div></div>
                      {(() => {
                        const lp = bsi.working_capital.latest_period || "";
                        return (
                          <>
                            <div className="er-mini-stat"><span>Days sales outstanding</span><strong>{fmtNum(bsi.working_capital.dso_series?.[lp], "days")}</strong></div>
                            <div className="er-mini-stat"><span>Inventory days</span><strong>{fmtNum(bsi.working_capital.dio_series?.[lp], "days")}</strong></div>
                            <div className="er-mini-stat"><span>Days payable outstanding</span><strong>{fmtNum(bsi.working_capital.dpo_series?.[lp], "days")}</strong></div>
                            <div className="er-mini-stat"><span>Cash conversion cycle</span><strong>{fmtNum(bsi.working_capital.ccc_latest, "days")}</strong></div>
                            <div className="er-mini-stat"><span>Current ratio</span><strong>{fmtNum(bsi.working_capital.current_ratio_latest, "x")}</strong></div>
                          </>
                        );
                      })()}
                    </div>
                  </div>
                )}

                <div className="er-grid er-grid-2" style={{ marginTop: 16 }}>
                  <div className="er-card">
                    {(() => {
                      const triggered = bsi.risk_flags.filter((f) => f.status === "TRIGGERED").length;
                      return (
                        <div className="er-chart-title"><div><h3>Risk flags</h3><p>
                          {triggered} triggered of {bsi.risk_flags.length} evaluated
                          {triggered === 0 ? " — each rule below was actually checked against this company's own numbers and genuinely didn't cross its threshold; a 0 here reflects a clean balance sheet, not a skipped check." : ""}
                        </p></div></div>
                      );
                    })()}
                    <FlagList items={bsi.risk_flags.map((f) => ({
                      label: readable(f.flag_id),
                      detail: f.status === "SOURCE_REQUIRED" ? `Not available — ${f.evidence[0] || "source required"}` : f.evidence.join("; ") || undefined,
                      tone: f.status !== "TRIGGERED" ? "info" as const : f.severity === "RED" ? "risk" as const : "watch" as const,
                    }))} />
                  </div>
                  <div className="er-card">
                    <div className="er-chart-title"><div><h3>Data coverage</h3><p>What analysis is possible from the data available</p></div></div>
                    <CoverageMeter pct={bsi.coverage.coverage_pct} total={bsi.coverage.total_metrics} />
                  </div>
                </div>
              </>
            ) : bsi?.balance_sheet_integrity.status === "BALANCE_SHEET_INTEGRITY_ERROR" ? (
              <div className="er-callout" style={{ background: "var(--er-coral-soft)", borderColor: "#eccbc0", color: "#7a3325" }}>
                <div className="er-icon">!</div>
                <div><strong>Balance sheet failed the accounting-identity check</strong>Analysis withheld for {bsi.period} rather than shown on unreliable data.</div>
              </div>
            ) : (
              <div className="er-callout er-callout-blue"><div className="er-icon">i</div><div><strong>Balance Sheet Intelligence</strong>{NA} for this company/statement type.</div></div>
            )}
          </section>

          {/* 07 Cash flow quality */}
          <section className="er-section" id="er-cf">
            <div className="er-section-head">
              <div><div className="er-eyebrow">07 · Cash flow quality</div><h2>Where cash actually came from and where it went.</h2></div>
              <p>{cfi?.period ? `${cfi.period} · ${cfi.statement_type}.` : NA} <Tag kind="reported" /></p>
            </div>
            {cfi?.period ? (
              <>
                <div className="er-verdict er-card" style={{ marginBottom: 16 }}>
                  <div className="er-accent-line" />
                  <h3>{readable(cfi.archetype.classification)} <Tag kind="calculated" /></h3>
                  {cfi.archetype.evidence.length > 0 && (
                    <ul style={{ marginTop: 8, paddingLeft: 18, fontSize: 13, color: "var(--er-muted)" }}>
                      {cfi.archetype.evidence.map((e, i) => <li key={i}>{e}</li>)}
                    </ul>
                  )}
                </div>

                <div className="er-grid er-grid-2">
                  <div className="er-card">
                    <div className="er-chart-title"><div><h3>CFO reconciliation</h3><p>Operating profit → cash from operations</p></div></div>
                    <div className="er-mini-stat"><span>Computed CFO</span><strong>{fmtNum(cfi.reconciliation.cfo_bridge.computed_cfo, "cr")}</strong></div>
                    <div className="er-mini-stat"><span>Bridge check</span><strong>{readable(cfi.reconciliation.cfo_bridge_check.status)}</strong></div>
                    {cfi.reconciliation.cfo_bridge_check.status === "DIVERGENT" && (
                      <p className="er-muted" style={{ fontSize: 12, marginTop: 6 }}>Diverges from reported CFO by {fmtNum(cfi.reconciliation.cfo_bridge_check.difference_pct, "%")} — likely an exceptional/one-off item.</p>
                    )}
                  </div>
                  <div className="er-card">
                    <div className="er-chart-title"><div><h3>Cash conversion</h3></div></div>
                    <div className="er-mini-stat"><span>CFO / operating profit</span><strong>{fmtNum(cfi.conversion.latest.ratio_pct, "%")} · {cfi.conversion.latest.band || "—"}</strong></div>
                    <div className="er-mini-stat"><span>Prior period</span><strong>{fmtNum(cfi.conversion.prior_ratio_pct, "%")}</strong></div>
                    <div className="er-mini-stat"><span>Trend</span><strong>{readable(cfi.conversion.trend)}</strong></div>
                    <div className="er-mini-stat"><span>3-year cumulative</span><strong>{fmtNum(cfi.conversion.cumulative_3y?.cumulative_cfo_to_operating_profit_pct, "%")}</strong></div>
                  </div>
                </div>

                <div className="er-grid er-grid-2" style={{ marginTop: 16 }}>
                  <div className="er-card">
                    <div className="er-chart-title"><div><h3>Free cash flow</h3><p>{readable(cfi.free_cash_flow.quality.classification)}</p></div></div>
                    <div className="er-mini-stat"><span>Reported FCF</span><strong>{fmtNum(cfi.free_cash_flow.reconciliation.reported_fcf, "cr")}</strong></div>
                    <div className="er-mini-stat"><span>CFO − capex</span><strong>{fmtNum(cfi.free_cash_flow.reconciliation.computed_fcf, "cr")}</strong></div>
                    {cfi.free_cash_flow.reconciliation.divergent && (
                      <p className="er-muted" style={{ fontSize: 12, marginTop: 6 }}>Reported and computed FCF diverge by {fmtNum(cfi.free_cash_flow.reconciliation.divergence_pct, "%")}.</p>
                    )}
                  </div>
                  <div className="er-card">
                    <div className="er-chart-title"><div><h3>Investing &amp; financing</h3></div></div>
                    <div className="er-mini-stat"><span>Debt direction</span><strong>{readable(cfi.financing.debt_financing.classification)}</strong></div>
                    <div className="er-mini-stat"><span>Dividends paid</span><strong>{fmtNum(cfi.financing.dividend_analysis.dividends_paid, "cr")}{cfi.financing.dividend_analysis.dividend_to_cfo_pct != null ? ` (${fmtNum(cfi.financing.dividend_analysis.dividend_to_cfo_pct, "%")} of CFO)` : ""}</strong></div>
                    {cfi.investing.asset_sale_dependency.triggered && (
                      <p className="er-muted" style={{ fontSize: 12, marginTop: 6 }}>Investing cash flow relies materially on asset/investment sales this period.</p>
                    )}
                  </div>
                </div>

                <div className="er-grid er-grid-2" style={{ marginTop: 16 }}>
                  <div className="er-card">
                    {(() => {
                      const triggered = cfi.risk_flags.filter((f) => f.status === "TRIGGERED").length;
                      return (
                        <div className="er-chart-title"><div><h3>Risk flags</h3><p>
                          {triggered} triggered of {cfi.risk_flags.length} evaluated
                          {triggered === 0 ? " — each rule was checked and genuinely didn't fire; not a skipped check." : ""}
                        </p></div></div>
                      );
                    })()}
                    <FlagList items={cfi.risk_flags.map((f) => ({
                      label: readable(f.flag_id),
                      detail: f.evidence.join("; ") || undefined,
                      tone: f.status !== "TRIGGERED" ? "info" as const : f.severity === "RED" ? "risk" as const : f.severity === "AMBER" ? "watch" as const : "good" as const,
                    }))} />
                  </div>
                  <div className="er-card">
                    <div className="er-chart-title"><div><h3>Forensic patterns</h3><p>{cfi.forensic_patterns.filter((p) => p.status === "TRIGGERED" || p.status === "OBSERVED").length} active of {cfi.forensic_patterns.length} evaluated — a smaller, more specific set of cash-vs-earnings warning signs (e.g. profit growing while cash doesn't, receivables/inventory quietly eating cash) than the Risk Flags list to the left; "observation" means the pattern is present but isn't itself a red flag on its own.</p></div></div>
                    <FlagList items={cfi.forensic_patterns.map((p) => ({
                      label: readable(p.pattern_id) + (p.status === "OBSERVED" ? " (observation, not a risk)" : ""),
                      detail: p.evidence.join("; ") || undefined,
                      tone: (p.status === "TRIGGERED" || p.status === "OBSERVED") ? "watch" as const : "info" as const,
                    }))} />
                  </div>
                </div>

                <div className="er-card" style={{ marginTop: 16 }}>
                  <div className="er-chart-title"><div><h3>Data coverage</h3><p>What analysis is possible from the data available</p></div></div>
                  <CoverageMeter pct={cfi.coverage.coverage_pct} total={cfi.coverage.total_metrics} />
                </div>
              </>
            ) : (
              <div className="er-callout er-callout-blue"><div className="er-icon">i</div><div><strong>Cash Flow Intelligence</strong>{NA} for this company/statement type.</div></div>
            )}
          </section>

          {/* 08 ROE-driven valuation — lenders only */}
          {bankRoe?.available && bankRoe.start && (
            <section className="er-section" id="er-roe">
              <div className="er-section-head">
                <div><div className="er-eyebrow">08 · ROE-driven valuation</div><h2>A lender's return comes from ROE compounding book value, not the P/E multiple.</h2></div>
                <p>Static snapshot of the default scenario — the ROE &amp; Valuation tab has the full interactive 10-year simulator. <Tag kind="calculated" /></p>
              </div>
              <div className="er-grid er-grid-4">
                <MetricCard label="Run-rate ROE" value={fmtNum(bankRoe.start.run_rate_roe, "%")} foot={bankRoe.start.run_rate_source} kind="reported" />
                <MetricCard label="Price / book" value={`${bankRoe.start.pb.toFixed(2)}x`} foot={`₹${bankRoe.start.price.toFixed(2)} on BV ₹${bankRoe.start.bvps.toFixed(1)}`} kind="reported" />
                <MetricCard label="Market-implied ROE" value={fmtNum(bankRoe.valuation_check?.market_implied_roe ?? null, "%")} foot={bankRoe.valuation_check ? `at COE ${bankRoe.valuation_check.coe}% / growth ${bankRoe.valuation_check.long_run_growth}%` : undefined} kind="calculated" />
                <MetricCard label="Payout ratio" value={fmtNum(bankRoe.start.payout_pct, "%")} kind="reported" />
              </div>
              <div className="er-grid er-grid-2" style={{ marginTop: 16 }}>
                <div className="er-card">
                  <div className="er-chart-title"><div><h3>Self-funded growth</h3><p>Self-funded growth = ROE × (1 − payout)</p></div></div>
                  <p style={{ fontSize: 13, color: "var(--er-muted)" }}>
                    At <b>{fmtNum(bankRoe.start.run_rate_roe, "%")}</b> ROE and a <b>{fmtNum(bankRoe.start.payout_pct, "%")}</b> payout, this lender funds about{" "}
                    <b>{bankRoe.sustainability ? fmtNum(bankRoe.sustainability.self_funded_growth, "%") : NA}</b> growth from retained profit alone
                    {bankRoe.start.balance_sheet_growth_pct != null ? <> against a balance sheet that grew <b>{fmtNum(bankRoe.start.balance_sheet_growth_pct, "%")}</b> last year</> : ""}.
                    {bankRoe.sustainability?.crossover_roe != null ? <> Closing that gap without dilution would need roughly <b>{fmtNum(bankRoe.sustainability.crossover_roe, "%")}</b> ROE.</> : ""} <Tag kind="calculated" />
                  </p>
                </div>
                <div className="er-card">
                  <div className="er-chart-title"><div><h3>DuPont — latest FY</h3><p>ROE = ROA × leverage</p></div></div>
                  {(() => {
                    const d = bankRoe.dupont?.at(-1);
                    return d ? (
                      <>
                        <div className="er-mini-stat"><span>ROE</span><strong>{fmtNum(d.roe, "%")}</strong></div>
                        <div className="er-mini-stat"><span>ROA</span><strong>{d.roa.toFixed(2)}%</strong></div>
                        <div className="er-mini-stat"><span>Leverage</span><strong>{d.leverage.toFixed(1)}x</strong></div>
                        <div className="er-mini-stat"><span>Equity growth</span><strong>{fmtNum(d.equity_growth, "%")}</strong></div>
                      </>
                    ) : <p className="er-muted">{NA}</p>;
                  })()}
                </div>
              </div>
              {bankRoe.checklist && bankRoe.checklist.length > 0 && (
                <div className="er-card" style={{ marginTop: 16 }}>
                  <div className="er-chart-title"><div><h3>What to check each quarter</h3><p>Not the share price — these, in this order</p></div></div>
                  <div className="er-grid er-grid-2">
                    {bankRoe.checklist.map((c, i) => (
                      <div key={c.key} className="er-mini-stat" style={{ display: "block" }}>
                        <span style={{ fontWeight: 700, color: "var(--er-deep)" }}>{i + 1}. {c.title}</span>
                        {c.value != null && <strong style={{ marginLeft: 8 }}>{c.value.toFixed(1)} {c.unit}</strong>}
                        <p className="er-muted" style={{ fontSize: 11.5, marginTop: 2 }}>{c.why}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {bankRoe.insights && bankRoe.insights.length > 0 && (
                <div className="er-callout er-callout-blue" style={{ marginTop: 16 }}>
                  <div className="er-icon">i</div>
                  <div><strong>Reading this simulator</strong>{bankRoe.insights.join(" ")}</div>
                </div>
              )}
              {bankRoe.disclaimer && <p className="er-peer-note" style={{ marginTop: 12 }}>{bankRoe.disclaimer}</p>}
            </section>
          )}

          {/* 09 Scoring & multiples */}
          <section className="er-section" id="er-valuation">
            <div className="er-section-head">
              <div><div className="er-eyebrow">09 · Scoring &amp; multiples</div><h2>Score composition and multiples in context.</h2></div>
              <p>Every sub-score below feeds the overall {analysis.overall_score ?? "—"}/100 at its stated weight. <Tag kind="calculated" /></p>
            </div>
            {dimEntries.length > 0 && (
              <div className="er-grid er-grid-2" style={{ marginBottom: 16, gridTemplateColumns: "1fr" }}>
                <div className="er-card er-chart-card">
                  <div className="er-chart-title"><div><h3>Score breakdown</h3><p>Category scores, 0–100 <Tag kind="calculated" /></p></div></div>
                  <RadarScoreChart scores={scores ?? null} />
                </div>
                {weightSlices.length > 0 && (
                  <div className="er-card er-chart-card">
                    <div className="er-chart-title"><div><h3>Composite weighting</h3><p>How the overall score is built <Tag kind="calculated" /></p></div></div>
                    <DonutChart data={weightSlices} formatter={(v) => `${(v * 100).toFixed(0)}%`} />
                  </div>
                )}
              </div>
            )}
            <div className="er-grid er-grid-2">
              <div className="er-card">
                <div className="er-chart-title"><div><h3>Score composition</h3><p>Weighted dimensions</p></div></div>
                {dimEntries.map((d) => (
                  <div key={d.key}>
                    <div className="er-mini-stat">
                      <span style={{ textTransform: "capitalize" }}>{d.label} ({((scores?.weights?.[d.key] ?? 0) * 100).toFixed(0)}% weight)</span>
                      <strong>{d.value}{scores && (scores as unknown as Record<string, unknown>)["refinement"] && ((scores as unknown as { refinement?: Record<string, { source?: string }> }).refinement?.[d.key]?.source) ? <Tag kind="calculated" /> : null}</strong>
                    </div>
                    {d.key === "growth" && scores?.growth_annual != null && (
                      <div className="er-mini-stat" style={{ paddingLeft: 12, fontSize: 11.5, color: "var(--er-muted)" }}>
                        <span>Annual (FY CAGR) {scores.growth_quarterly != null ? "· 35% of blend" : ""}</span>
                        <span>{scores.growth_annual}</span>
                      </div>
                    )}
                    {d.key === "growth" && scores?.growth_quarterly != null && (
                      <div className="er-mini-stat" style={{ paddingLeft: 12, fontSize: 11.5, color: "var(--er-muted)" }}>
                        <span>Quarterly (last 4Q vs prior 4Q) · 65% of blend</span>
                        <span>{scores.growth_quarterly}</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
              <div className="er-card">
                <div className="er-chart-title"><div><h3>Multiples vs sector median</h3><p>Company vs peer universe</p></div></div>
                <table>
                  <thead><tr><th>Multiple</th><th className="er-right">Company</th><th className="er-right">Sector median</th></tr></thead>
                  <tbody>
                    {(["pe_ratio", "ev_to_ebitda", "pb_ratio", "peg_ratio"] as const).map((k) => (
                      <tr key={k}>
                        <td>{k === "pe_ratio" ? "P/E" : k === "ev_to_ebitda" ? "EV / EBITDA" : k === "pb_ratio" ? "P/B" : "PEG"}</td>
                        <td className="er-right"><ValueTag value={fmtNum((metrics as unknown as Record<string, number | null>)?.[k] ?? null, "x")} kind={metrics?.peg_ratio != null && k === "peg_ratio" ? "calculated" : "reported"} /></td>
                        <td className="er-right"><ValueTag value={sectorMedians[k] != null ? fmtNum(sectorMedians[k], "x") : "—"} kind={sectorMedians[k] != null ? "benchmark" : null} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <p className="er-muted" style={{ fontSize: 10.5, marginTop: 8 }}>PEG = P/E ÷ 3-year EPS CAGR; below 1x is conventionally read as growth not yet fully priced in, above 2x as rich even after accounting for growth. Meaningful only when both P/E and EPS growth are positive — shown as "—" otherwise (e.g. a loss-making or EPS-declining company).</p>
              </div>
            </div>
            <p className="er-muted" style={{ fontSize: 11.5, marginTop: 10 }}>Balance sheet leverage, working capital and coverage are covered in full in Section 06 · Balance sheet architecture above.</p>
          </section>

          {/* 10 Peer benchmark */}
          <section className="er-section" id="er-peer">
            <div className="er-section-head">
              <div><div className="er-eyebrow">10 · Peer benchmark</div><h2>Named peers in the same sector.</h2></div>
              <p>{peers?.peer_count ? `${peers.peer_count} peers matched on sector/industry.` : NA} <Tag kind="reported" /></p>
            </div>
            {namedPeers.length > 0 && (() => {
              const subjectPoint = company ? {
                company_name: company.company_name, market_cap: company.market_cap,
                revenue_cagr_3y: sector?.key_metrics?.find((m) => m.name === "revenue_cagr_3y")?.value as number ?? null,
                roce: roceLatest, pe_ratio: metrics?.pe_ratio ?? null,
              } : null;
              return (
                <>
                  <div className="er-grid er-grid-2" style={{ marginBottom: 16, gridTemplateColumns: "1fr" }}>
                    <div className="er-card er-chart-card">
                      <div className="er-chart-title"><div><h3>Peer positioning — ROCE</h3><p>Revenue CAGR (3Y) vs. ROCE %, sized by market cap <Tag kind="reported" /></p></div></div>
                      <PeerScatterChart peers={namedPeers} subject={subjectPoint} fixedMetric="roce" height={420} />
                    </div>
                    <div className="er-card er-chart-card">
                      <div className="er-chart-title"><div><h3>Peer positioning — P/E</h3><p>Revenue CAGR (3Y) vs. P/E, sized by market cap <Tag kind="reported" /></p></div></div>
                      <PeerScatterChart peers={namedPeers} subject={subjectPoint} fixedMetric="pe_ratio" height={420} />
                    </div>
                  </div>
                  {perfSeries.length >= 2 && (
                    <div className="er-card er-chart-card" style={{ marginBottom: 16 }}>
                      <div className="er-chart-title"><div><h3>Relative price performance</h3><p>1 year, rebased to 100 <Tag kind="reported" /></p></div></div>
                      <RebasedPerformanceChart series={perfSeries} />
                    </div>
                  )}
                </>
              );
            })()}
            {namedPeers.length > 0 ? (
              <div className="er-card" style={{ overflow: "auto" }}>
                <table>
                  <thead><tr><th>Company</th><th className="er-right">Market cap</th><th className="er-right">Revenue CAGR (3Y)</th><th className="er-right">EBITDA margin</th><th className="er-right">ROCE</th><th className="er-right">P/E</th></tr></thead>
                  <tbody>
                    <tr style={{ fontWeight: 700 }}>
                      <td>{company?.company_name} (this company)</td>
                      <td className="er-right">{company?.market_cap != null ? `₹${(company.market_cap / 1e7).toLocaleString("en-IN", { maximumFractionDigits: 0 })} Cr` : "—"}</td>
                      <td className="er-right">{fmtNum(sector?.key_metrics?.find((m) => m.name === "revenue_cagr_3y")?.value as number ?? null, "%")}</td>
                      <td className="er-right">{fmtNum(ebitdaMarginLatest, "%")}</td>
                      <td className="er-right">{fmtNum(roceLatest, "%")}</td>
                      <td className="er-right">{fmtNum(metrics?.pe_ratio ?? null, "x")}</td>
                    </tr>
                    {namedPeers.map((p) => (
                      <tr key={p.stock_id || p.symbol}>
                        <td>{p.company_name}</td>
                        <td className="er-right">{p.market_cap != null ? `₹${(p.market_cap / 1e7).toLocaleString("en-IN", { maximumFractionDigits: 0 })} Cr` : "—"}</td>
                        <td className="er-right">{fmtNum(p.revenue_cagr_3y ?? null, "%")}</td>
                        <td className="er-right">{fmtNum(p.ebitda_margin ?? null, "%")}</td>
                        <td className="er-right">{fmtNum(p.roce ?? null, "%")}</td>
                        <td className="er-right">{fmtNum(p.pe_ratio ?? null, "x")}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <p className="er-peer-note">Named peers, matched on sector/industry classification. <Tag kind="reported" /> All figures fetched at analysis time; not a live feed.</p>
              </div>
            ) : (
              <div className="er-callout er-callout-blue"><div className="er-icon">i</div><div><strong>No peer set</strong>{NA}.</div></div>
            )}
            {sector?.framework_class && sector.framework_class !== sector.sector_name && (
              <div className="er-callout er-callout-blue" style={{ marginTop: 16 }}>
                <div className="er-icon">i</div>
                <div><strong>Scoring framework note</strong>This company is routed through the internal <code>{sector.framework_class}</code> scoring class under the <b>{sector.sector_name}</b> sector label — several related sectors share one scoring implementation by design.</div>
              </div>
            )}
            {sectorMetricRows.length > 0 && (
              <div className="er-card" style={{ marginTop: 16, overflow: "auto" }}>
                <div className="er-chart-title"><div><h3>{sector?.sector_name || "Sector"}-specific metrics vs. peers</h3><p>Operating KPIs unique to this sector — not generic financial ratios</p></div></div>
                {hasAnySectorMetricValue ? (
                  <>
                    <table>
                      <thead>
                        <tr>
                          <th>Metric</th>
                          <th className="er-right">{company?.company_name || "This company"}</th>
                          {namedPeers.map((p) => <th key={p.stock_id || p.symbol} className="er-right">{p.symbol}</th>)}
                          <th className="er-right">Median</th>
                        </tr>
                      </thead>
                      <tbody>
                        {sectorMetricRows.map((m) => {
                          const companyVal = peers?.company_metrics?.[m.name] as number ?? null;
                          const medianVal = sectorMedians[m.name] as number ?? null;
                          return (
                            <tr key={m.name}>
                              <td>{m.label || m.name}</td>
                              <td className="er-right"><ValueTag value={fmtDense(companyVal, m.unit)} kind={companyVal != null ? "reported" : null} /></td>
                              {namedPeers.map((p) => (
                                <td key={p.stock_id || p.symbol} className="er-right">{fmtDense(p.sector_metrics?.[m.name] ?? null, m.unit)}</td>
                              ))}
                              <td className="er-right"><ValueTag value={fmtDense(medianVal, m.unit)} kind={medianVal != null ? "benchmark" : null} /></td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                    <p className="er-peer-note">A peer showing "—" hasn't itself been analyzed on this platform yet — never a guessed value.</p>
                  </>
                ) : (
                  <p className="er-muted">{sectorMetricRows.map((m) => m.label || m.name).join(", ")} — {NA} for this company or any named peer yet.</p>
                )}
              </div>
            )}
          </section>

          {/* 11 Risks & scenarios */}
          <section className="er-section" id="er-risks">
            <div className="er-section-head">
              <div><div className="er-eyebrow">11 · Risks &amp; scenarios</div><h2>Deterministic red flags and catalysts.</h2></div>
              <p>{analysis.risks.length} risk flag(s) and {analysis.catalysts.length} catalyst(s) computed from the sector framework and financial-intelligence engines. <Tag kind="calculated" /></p>
            </div>
            {analysis.risks.length === 0 && analysis.catalysts.length === 0 && (
              <div className="er-card"><p className="er-muted">{NA}</p></div>
            )}
            {analysis.risks.length > 0 && (
              <div style={{ marginBottom: analysis.catalysts.length > 0 ? 20 : 0 }}>
                <div className="er-chart-title"><div><h3>Risk flags</h3><p>{analysis.risks.length} raised by the sector framework and financial-intelligence engines</p></div></div>
                <div className="er-grid er-grid-3">
                  {analysis.risks.map((r, i) => (
                    <div key={`risk-${i}`} className="er-card er-risk-card">
                      <span className={`er-tag ${r.severity === "HIGH" ? "er-tag-risk" : "er-tag-watch"}`}>{r.severity} · {r.category}</span>
                      <h3 style={{ marginTop: 16 }}>{r.title || r.category}</h3>
                      <p>{r.description}</p>
                      {r.confidence != null && <div className="er-evidence">Confidence {(r.confidence * 100).toFixed(0)}% <Tag kind="calculated" /></div>}
                    </div>
                  ))}
                </div>
              </div>
            )}
            {analysis.catalysts.length > 0 && (
              <div>
                <div className="er-chart-title"><div><h3>Catalysts</h3><p>{analysis.catalysts.length} positive signal(s) computed the same way, from the same engines</p></div></div>
                <div className="er-grid er-grid-3">
                  {analysis.catalysts.map((c, i) => (
                    <div key={`cat-${i}`} className="er-card er-risk-card er-risk-card-good">
                      <span className="er-tag er-tag-good">{c.type || c.category || "CATALYST"}</span>
                      <h3 style={{ marginTop: 16 }}>{c.title || "Catalyst"}</h3>
                      <p>{c.description}</p>
                      {c.confidence != null && <div className="er-evidence">Confidence {(c.confidence * 100).toFixed(0)}% <Tag kind="calculated" /></div>}
                    </div>
                  ))}
                </div>
              </div>
            )}
            <p className="er-muted" style={{ fontSize: 11.5, marginTop: 16 }}>The AI layer's own bull/bear case and monitoring points are in Section 14 · AI analysis below.</p>
          </section>

          {/* 12 Concalls & guidance */}
          <section className="er-section" id="er-concall">
            <div className="er-section-head">
              <div><div className="er-eyebrow">12 · Concalls &amp; guidance</div><h2>Management commentary, extracted from earnings-call transcripts.</h2></div>
              <p>{concall?.latest_transcript ? `Latest call: ${concall.latest_transcript.quarter || concall.latest_transcript.call_date || concall.latest_transcript.filing_date || "—"}.` : NA} <Tag kind="reported" /></p>
            </div>
            {concall?.latest_transcript ? (
              <>
                {concall.latest_transcript.management_participants.length > 0 && (
                  <p className="er-muted" style={{ fontSize: 12.5, marginBottom: 16 }}>
                    Management on the call: {concall.latest_transcript.management_participants.slice(0, 6).map((p) => p.name).join(", ")}.
                  </p>
                )}
                {concall.highlights && concall.highlights.sections.length > 0 && (
                  <div className="er-card er-card-flowing" style={{ marginBottom: 16 }}>
                    <div className="er-chart-title">
                      <div><h3>Results &amp; concall highlights</h3></div>
                      <Tag kind={concall.highlights.source === "ARTHNEETI" ? "third_party" : "ai"} />
                    </div>
                    <div className="er-grid er-grid-2">
                      {concall.highlights.sections.map((s) => (
                        <div key={s.heading} className="er-highlight-topic">
                          <p style={{ fontSize: 12.5, fontWeight: 700, color: "var(--er-deep)", marginBottom: 6 }}>{s.heading}</p>
                          <ul style={{ paddingLeft: 16, fontSize: 12, color: "var(--er-muted)" }}>
                            {s.bullets.slice(0, 6).map((b, i) => <li key={i} style={{ marginBottom: 4 }}>{b}</li>)}
                          </ul>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                <div className="er-grid er-grid-2">
                  {concall.topic_sentiment.length > 0 && (
                    <div className="er-card">
                      <div className="er-chart-title"><div><h3>Management tone by topic</h3></div><Tag kind="ai" /></div>
                      <table>
                        <thead><tr><th>Topic</th><th className="er-right">Sentiment</th></tr></thead>
                        <tbody>
                          {concall.topic_sentiment.map((t) => (
                            <tr key={t.topic}><td>{t.topic}</td><td className="er-right">{t.arrow} {t.sentiment.charAt(0) + t.sentiment.slice(1).toLowerCase()}</td></tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                  <div className="er-card">
                    <div className="er-chart-title"><div><h3>What changed since last call</h3></div>{concall.what_changed.length > 0 && <Tag kind="ai" />}</div>
                    {concall.what_changed.length > 0 ? (
                      <ul style={{ paddingLeft: 16, fontSize: 12.5, color: "var(--er-muted)" }}>
                        {concall.what_changed.map((c, i) => <li key={i} style={{ marginBottom: 4 }}>{c}</li>)}
                      </ul>
                    ) : <p className="er-muted">{concall.has_previous_call ? "No material change flagged versus the prior call." : NA}</p>}
                  </div>
                </div>
                {concall.guidance_consistency && (
                  <div className="er-card" style={{ marginTop: 16 }}>
                    <div className="er-chart-title">
                      <div><h3>Guidance consistency</h3><p>{concall.guidance_consistency.metrics_tracked} metrics tracked, {concall.guidance_consistency.total_updates} quarter-over-quarter updates on record</p></div>
                      <span className="er-tag er-tag-info">{Math.round(concall.guidance_consistency.score)}/100 <Tag kind="calculated" /></span>
                    </div>
                  </div>
                )}
                {concall.guidance.length > 0 && (
                  <div className="er-card" style={{ marginTop: 16, overflow: "auto" }}>
                    <div className="er-chart-title"><div><h3>Management guidance</h3><p>A metric of "Other" means the extraction couldn't map this remark to a named category (capex/demand/pricing/revenue) — the quote itself is shown instead of a bare "qualitative" label</p></div><Tag kind="reported" /></div>
                    <table>
                      <thead><tr><th>Metric</th><th>Period</th><th className="er-right">Target / what was said</th><th>Tone</th><th>Status</th></tr></thead>
                      <tbody>
                        {concall.guidance.slice(0, 12).map((g, i) => {
                          let target = "—";
                          if (g.guidance_type === "quantitative") {
                            if (g.target_low !== null && g.target_high !== null) target = `${g.target_low}–${g.target_high} ${g.unit || ""}`;
                            else if (g.target_value !== null) target = `${g.target_value} ${g.unit || ""}`;
                          }
                          if (target === "—" && g.statement) {
                            target = g.statement.length > 160 ? `"${g.statement.slice(0, 160).trim()}…"` : `"${g.statement}"`;
                          } else if (target === "—") {
                            target = "qualitative — no verbatim quote on file";
                          }
                          return (
                            <tr key={i}>
                              <td>{readable(g.metric)}{g.category ? ` (${g.category})` : ""}</td>
                              <td>{g.period || "—"}</td>
                              <td className="er-right" style={{ fontStyle: g.guidance_type !== "quantitative" ? "italic" : "normal" }}>{target}</td>
                              <td>{g.tone || "—"}</td>
                              <td><StatusTag status={g.status} /></td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </>
            ) : (
              <div className="er-callout er-callout-blue"><div className="er-icon">i</div><div><strong>Concall intelligence</strong>No earnings-call transcript has been analyzed for this company yet.</div></div>
            )}
          </section>

          {/* 13 News & analyst view */}
          <section className="er-section" id="er-market">
            <div className="er-section-head">
              <div><div className="er-eyebrow">13 · News &amp; analyst view</div><h2>External coverage — not this platform's own view.</h2></div>
              <p>Every figure in this section is a third party's opinion or a market-data snapshot. <Tag kind="third_party" /></p>
            </div>
            <div className="er-grid er-grid-2">
              <div className="er-card">
                <div className="er-chart-title"><div><h3>Calendar</h3></div></div>
                <div className="er-mini-stat"><span>Next earnings date</span><strong>{calendar?.next_earnings_date || NA}</strong></div>
                <div className="er-mini-stat"><span>Ex-dividend date</span><strong>{calendar?.ex_dividend_date || NA}</strong></div>
                {calendar?.expected_eps_avg != null && (
                  <div className="er-mini-stat"><span>Consensus forward EPS</span><strong>₹{calendar.expected_eps_avg.toFixed(2)}</strong></div>
                )}
              </div>
              <div className="er-card">
                <div className="er-chart-title"><div><h3>Analyst consensus</h3></div></div>
                {Object.keys(analystConsensus).length > 0 ? Object.entries(analystConsensus).map(([source, e]) => {
                  const split = [e.buy_pct != null ? `Buy ${fmtNum(e.buy_pct, "%")}` : null, e.hold_pct != null ? `Hold ${fmtNum(e.hold_pct, "%")}` : null, e.sell_pct != null ? `Sell ${fmtNum(e.sell_pct, "%")}` : null].filter(Boolean).join(" · ");
                  const target = e.target_price_mean != null
                    ? `Target ₹${e.target_price_mean.toFixed(0)}${e.implied_upside_pct != null ? ` (${e.implied_upside_pct >= 0 ? "+" : ""}${e.implied_upside_pct.toFixed(1)}% implied)` : ""}`
                    : null;
                  const line = [split, target].filter(Boolean).join(" · ");
                  return (
                    <div key={source} style={{ marginBottom: 10 }}>
                      <div className="er-mini-stat">
                        <span>{source} ({e.num_analysts ?? "—"} analysts)</span>
                        <strong>{readable(e.sentiment)}</strong>
                      </div>
                      <p className="er-muted" style={{ fontSize: 11.5 }}>{line || NA}</p>
                    </div>
                  );
                }) : <p className="er-muted">{NA}</p>}
              </div>
            </div>
            {news.length > 0 && (
              <div className="er-card" style={{ marginTop: 16 }}>
                <div className="er-chart-title"><div><h3>Recent news</h3></div></div>
                <ul style={{ margin: 0, padding: 0, listStyle: "none", display: "grid", gap: 12 }}>
                  {news.slice(0, 6).map((n, i) => (
                    <li key={i}>
                      <div style={{ fontSize: 12.5, fontWeight: 700, color: "var(--er-deep)" }}>{n.headline}</div>
                      {n.summary && <div style={{ fontSize: 11.5, color: "var(--er-muted)", marginTop: 2 }}>{n.summary}</div>}
                      <div style={{ fontSize: 10.5, color: "var(--er-faint)", marginTop: 2 }}>{n.provider || "—"}{n.published_at ? ` · ${new Date(n.published_at).toLocaleDateString("en-IN")}` : ""}</div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </section>

          {/* 14 AI analysis */}
          <section className="er-section" id="er-ai">
            <div className="er-section-head">
              <div><div className="er-eyebrow">14 · AI analysis</div><h2>This platform's own AI layer, reading only the deterministic data already shown above.</h2></div>
              <p>Qualitative interpretation, not a verified fact — see the Methodology section for what this tag means. <Tag kind="ai" /></p>
            </div>
            {ai ? (
              <>
                <div className="er-verdict er-card" style={{ marginBottom: 16 }}>
                  <div className="er-accent-line" />
                  <h3>{ai.rating}{ai.valuation_view ? ` · ${readable(ai.valuation_view)}` : ""}{ai.conviction ? ` · ${readable(ai.conviction)} conviction` : ""} <Tag kind="ai" /></h3>
                  <p>{ai.executive_summary || NA}</p>
                </div>
                <div className="er-grid er-grid-3" style={{ marginBottom: 16 }}>
                  <MetricCard label="Business quality" value={ai.business_quality != null ? `${ai.business_quality}/100` : NA} kind="ai" />
                  <MetricCard label="Growth quality" value={ai.growth_quality != null ? `${ai.growth_quality}/100` : NA} kind="ai" />
                  <MetricCard label="Financial quality" value={ai.financial_quality != null ? `${ai.financial_quality}/100` : NA} kind="ai" />
                </div>
                <div className="er-grid er-grid-2">
                  {ai.business_quality_assessment && (
                    <div className="er-card"><div className="er-chart-title"><div><h3>Business quality</h3></div></div><p style={{ fontSize: 12.5, color: "var(--er-muted)" }}>{ai.business_quality_assessment}</p></div>
                  )}
                  {ai.financial_health_summary && (
                    <div className="er-card"><div className="er-chart-title"><div><h3>Financial health</h3></div></div><p style={{ fontSize: 12.5, color: "var(--er-muted)" }}>{ai.financial_health_summary}</p></div>
                  )}
                  {ai.growth_outlook && (
                    <div className="er-card"><div className="er-chart-title"><div><h3>Growth outlook</h3></div></div><p style={{ fontSize: 12.5, color: "var(--er-muted)" }}>{ai.growth_outlook}</p></div>
                  )}
                  {ai.valuation_commentary && (
                    <div className="er-card"><div className="er-chart-title"><div><h3>Valuation commentary</h3></div></div><p style={{ fontSize: 12.5, color: "var(--er-muted)" }}>{ai.valuation_commentary}</p></div>
                  )}
                  {ai.competitive_position && (
                    <div className="er-card"><div className="er-chart-title"><div><h3>Competitive position</h3></div></div><p style={{ fontSize: 12.5, color: "var(--er-muted)" }}>{ai.competitive_position}</p></div>
                  )}
                  {ai.industry_attractiveness && (
                    <div className="er-card"><div className="er-chart-title"><div><h3>Industry attractiveness</h3></div></div><p style={{ fontSize: 12.5, color: "var(--er-muted)" }}>{ai.industry_attractiveness}</p></div>
                  )}
                </div>
                {(ai.bull_case || ai.bear_case) && (
                  <div className="er-grid er-grid-2" style={{ marginTop: 16 }}>
                    <div className="er-card" style={{ background: "#f1f8f3", borderColor: "#cbe5d5" }}>
                      <h3>Bull case</h3>
                      <ul style={{ marginTop: 10, paddingLeft: 18, color: "var(--er-muted)", fontSize: 12 }}>
                        {(Array.isArray(ai.bull_case) ? ai.bull_case : ai.bull_case ? [ai.bull_case] : []).length > 0
                          ? (Array.isArray(ai.bull_case) ? ai.bull_case : [ai.bull_case as string]).map((t, i) => <li key={i}>{t}</li>)
                          : <li>{NA}</li>}
                      </ul>
                    </div>
                    <div className="er-card" style={{ background: "#fff5f1", borderColor: "#eccbc0" }}>
                      <h3>Bear case</h3>
                      <ul style={{ marginTop: 10, paddingLeft: 18, color: "var(--er-muted)", fontSize: 12 }}>
                        {(Array.isArray(ai.bear_case) ? ai.bear_case : ai.bear_case ? [ai.bear_case] : []).length > 0
                          ? (Array.isArray(ai.bear_case) ? ai.bear_case : [ai.bear_case as string]).map((t, i) => <li key={i}>{t}</li>)
                          : <li>{NA}</li>}
                      </ul>
                    </div>
                  </div>
                )}
                {ai.investment_thesis && ai.investment_thesis.length > 0 && (
                  <div className="er-card" style={{ marginTop: 16 }}>
                    <h3>Investment thesis</h3>
                    <ul style={{ marginTop: 10, paddingLeft: 18, color: "var(--er-muted)", fontSize: 12.5 }}>
                      {ai.investment_thesis.map((t, i) => <li key={i} style={{ marginBottom: 4 }}>{t}</li>)}
                    </ul>
                  </div>
                )}
                {((ai.key_risks?.length ?? 0) > 0 || (ai.key_catalysts?.length ?? ai.catalysts?.length ?? 0) > 0) && (
                  <div className="er-grid er-grid-2" style={{ marginTop: 16 }}>
                    {ai.key_risks && ai.key_risks.length > 0 && (
                      <div className="er-card">
                        <h3>Key risks</h3>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 10 }}>
                          {ai.key_risks.map((r, i) => <span key={i} className="er-tag er-tag-risk">{r}</span>)}
                        </div>
                      </div>
                    )}
                    {(ai.key_catalysts?.length ? ai.key_catalysts : ai.catalysts)?.length ? (
                      <div className="er-card">
                        <h3>Key catalysts</h3>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 10 }}>
                          {(ai.key_catalysts?.length ? ai.key_catalysts : ai.catalysts)!.map((c, i) => <span key={i} className="er-tag er-tag-good">{c}</span>)}
                        </div>
                      </div>
                    ) : null}
                  </div>
                )}
                {ai.monitoring_points && ai.monitoring_points.length > 0 && (
                  <div className="er-callout er-callout-blue" style={{ marginTop: 16 }}>
                    <div className="er-icon">✓</div>
                    <div><strong>What to monitor next</strong>{ai.monitoring_points.join("; ")}.</div>
                  </div>
                )}
                <p className="er-peer-note" style={{ marginTop: 16 }}>
                  Generated by {ai.model || "this platform's AI layer"}. All calculations feeding this analysis are deterministic; the AI layer provides qualitative
                  interpretation only, constrained to the data already shown in this report. Not financial advice — do your own due diligence.
                </p>
              </>
            ) : (
              <div className="er-callout er-callout-blue"><div className="er-icon">i</div><div><strong>AI analysis</strong>Not available — the AI analysis stage may have been skipped or failed for this run.</div></div>
            )}
          </section>

          {/* 15 Deep research */}
          {blueprintSections.length > 0 && (
            <section className="er-section" id="er-research">
              <div className="er-section-head">
                <div><div className="er-eyebrow">15 · Deep research</div><h2>Interpretation of this report's own deterministic data.</h2></div>
                <p>Generated by a local model, constrained to figures already shown elsewhere in this report. <Tag kind="ai" /></p>
              </div>
              <div className="er-grid er-grid-2">
                {blueprintSections.map((s: BlueprintSection) => (
                  <div key={s.id} className="er-card">
                    <h3 style={{ marginBottom: 8 }}>{s.title}</h3>
                    {(s.type === "text" || s.type === "business_model") && s.content && (
                      <p style={{ fontSize: 12.5, color: "var(--er-muted)" }}>{s.content}</p>
                    )}
                    {s.key_points && s.key_points.length > 0 && (
                      <ul style={{ marginTop: 8, paddingLeft: 16, fontSize: 12, color: "var(--er-muted)" }}>
                        {s.key_points.map((kp, i) => <li key={i} style={{ marginBottom: 4 }}>{kp}</li>)}
                      </ul>
                    )}
                    {s.items && s.items.length > 0 && (
                      <div style={{ display: "grid", gap: 8, marginTop: 8 }}>
                        {s.items.map((it, i) => (
                          <div key={i} style={{ fontSize: 12, color: "var(--er-muted)" }}>
                            <b style={{ color: "var(--er-deep)" }}>{it.title}</b>{it.severity ? ` (${it.severity})` : ""}{it.description ? ` — ${it.description}` : ""}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* 16 Methodology & sources */}
          <section className="er-section er-page-break" id="er-review">
            <div className="er-section-head">
              <div><div className="er-eyebrow">16 · Methodology &amp; sources</div><h2>How to read this report.</h2></div>
              <p>Every figure above is tagged with where it came from. Nothing displayed as a number is invented.</p>
            </div>
            <div className="er-grid er-grid-2">
              <div className="er-card">
                <div className="er-eyebrow">Provenance legend</div>
                <h3>What each tag means.</h3>
                <ul className="er-source-list" style={{ marginTop: 14 }}>
                  <li><Tag kind="reported" /> — taken directly from a company filing, exchange disclosure, or live market-data feed.</li>
                  <li><Tag kind="calculated" /> — derived from reported values (e.g. CAGR, margins, composite scores).</li>
                  <li><Tag kind="benchmark" /> — computed across the matched sector/peer universe (median, percentile).</li>
                  <li><Tag kind="ai" /> — generated by this platform's own AI layer; a qualitative assessment, not a verified fact.</li>
                  <li><Tag kind="third_party" /> — from an external provider's own content (e.g. Screener.in's company summary); not independently re-verified by this platform.</li>
                  <li><Tag kind="unavailable" /> — not present in any source this platform ingests for this company/period.</li>
                </ul>
              </div>
              <div className="er-card">
                <div className="er-eyebrow">Source register</div>
                <h3>Primary inputs used by this platform.</h3>
                <ul className="er-source-list" style={{ marginTop: 14 }}>
                  <li>NSE — investor presentations, results press releases, earnings-call transcripts, annual reports.</li>
                  <li>BSE — fallback annual-report source when NSE has no filing on file.</li>
                  <li>Screener.in — multi-year standalone/consolidated P&amp;L, balance sheet and cash-flow history.</li>
                  <li>Yahoo Finance — live price, market cap, and extended market data.</li>
                  <li>Sector-specific industry regulator reports (TRAI/CEA/PPAC/PNGRB) where applicable to this sector.</li>
                </ul>
              </div>
            </div>
            <div className="er-card" style={{ marginTop: 16 }}>
              <div className="er-eyebrow">This analysis</div>
              <h3>Data quality {analysis.data_quality_score != null ? `${analysis.data_quality_score.toFixed(1)}%` : "—"} · Confidence {analysis.confidence_score != null ? `${analysis.confidence_score.toFixed(1)}%` : "—"}</h3>
              <p className="er-muted" style={{ marginTop: 8 }}>Sector match: {sector?.sector_matched ? "matched to a dedicated sector framework" : "no dedicated sector framework matched — generic scoring applied"}. Analysis ID {analysis.id}, generated {analysis.completed_at ? new Date(analysis.completed_at).toLocaleString("en-IN") : "—"}.</p>
            </div>
            <div className="er-callout" style={{ marginTop: 16 }}>
              <div className="er-icon">i</div>
              <div><strong>Not investment advice</strong>This is a generated presentation of the platform's own computed analysis. It is not a recommendation to buy or sell securities. Verify the latest filings, price, share count and company disclosures before making an investment decision.</div>
            </div>
          </section>

          <footer className="er-footer"><span>{company?.company_name || analysis.stock_id} · Editorial report</span><span>Generated {today} · {analysis.id}</span></footer>
        </main>
      </div>
    </div>
  );
}

// A table cell's numeric value plus its provenance tag, always stacked
// value-then-tag rather than left to wrap inline — real bug found live:
// `{value} <Tag/>` wrapped onto one line for a short value ("3.0%") and
// two lines for a longer one, so the numbers themselves landed at
// different heights row to row and no longer read as a straight right-
// aligned column. Forcing the same flex-column layout every time, tag
// omitted entirely (not just hidden) when there's no value, fixes that
// regardless of how wide the cell or how long the formatted number is.
function ValueTag({ value, kind }: { value: string; kind: Provenance | null }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 3 }}>
      <span>{value}</span>
      {kind && <Tag kind={kind} />}
    </div>
  );
}

function StatusTag({ status }: { status?: string }) {
  const map: Record<string, string> = { EXCELLENT: "er-tag-good", GOOD: "er-tag-good", FAIR: "er-tag-watch", POOR: "er-tag-risk" };
  return <span className={`er-tag ${map[status || ""] || "er-tag-info"}`}>{status || "—"}</span>;
}

function MetricCard({ label, value, foot, kind }: { label: string; value: string; foot?: string; kind: Provenance }) {
  return (
    <div className="er-card er-metric-card">
      <div className="er-metric-label">{label} <Tag kind={kind} /></div>
      <div className="er-metric-value">{value}</div>
      {foot && <div className="er-metric-foot">{foot}</div>}
    </div>
  );
}

const EDITORIAL_CSS = `
.er-root{--er-ink:#17211f;--er-muted:#66716d;--er-faint:#8d9994;--er-paper:#f5f3ed;--er-card:#fffdf8;--er-line:#dedfd7;--er-deep:#123b38;--er-deep-2:#1f5d55;--er-mint:#dceee7;--er-mint-2:#a8d5c6;--er-gold:#c79a3b;--er-gold-soft:#f6ecd4;--er-coral:#bd624d;--er-coral-soft:#f8e4dd;--er-blue:#4d7190;--er-blue-soft:#e4edf3;--er-shadow:0 16px 38px rgba(25,45,40,.08);--er-radius:18px;background:var(--er-paper);color:var(--er-ink);font:14px/1.55 Inter,ui-sans-serif,system-ui,sans-serif}
/* Reused live-dashboard chart components (DonutChart's legend, ComboTrendChart/
   RadarScoreChart/PeerScatterChart/RebasedPerformanceChart's axis/tooltip
   helpers, added 2026-09-21) read the dashboard's own dark-theme CSS custom
   properties (--text-secondary, --text-dim, etc. — see src/index.css) which
   resolve to near-white colors meant for a navy background. Left unaliased,
   those legends/axis labels render nearly invisible on this report's cream
   background (confirmed live: the Earnings Quality donut's legend numerals
   were nearly unreadable). Aliasing them to editorial's own palette, scoped
   to .er-root only, fixes every reused chart at once without forking them.*/
.er-root{--text-primary:var(--er-ink);--text-secondary:var(--er-muted);--text-dim:var(--er-faint);--bg-card:var(--er-card);--bg-base:var(--er-paper);--bg-input:#f6f5ef;--border-subtle:var(--er-line);--accent:var(--er-gold);--font-display:Georgia,"Times New Roman",serif}
.er-root h1,.er-root h2,.er-root h3{font-family:Georgia,"Times New Roman",serif;font-weight:500;letter-spacing:-.025em;margin:0}
.er-root h1{font-size:clamp(32px,4vw,58px);line-height:1.02}
.er-root h2{font-size:27px;line-height:1.1}
.er-root h3{font-size:19px;line-height:1.15}
.er-root p{margin:0}
.er-root a{color:inherit}
.er-root ul{margin:0}
.er-root table{width:100%;border-collapse:collapse;font-size:12px}
.er-root th{text-align:left;color:var(--er-faint);font-size:10px;text-transform:uppercase;letter-spacing:.08em;font-weight:800;padding:10px 11px;background:#f6f5ef;border-bottom:1px solid var(--er-line)}
.er-root td{padding:11px;border-bottom:1px solid var(--er-line);vertical-align:top}
.er-root tr:last-child td{border-bottom:0}
.er-root td:first-child{font-weight:700;color:var(--er-deep)}
.er-right{text-align:right}
/* Real bug found live 2026-09-22 (user's own report -- "heading is far
   from values" / "missed alignment between values"): the ".er-root th"
   rule (class + element = specificity 0,1,1) beat the ".er-right" utility
   class alone (0,1,0) on every right-aligned <th>, so EVERY right-aligned
   table header silently reverted to left-align while its own column's
   right-aligned <td> values correctly right-aligned -- the header sat far
   from its own numbers in every single table with a numeric column, not
   just one. One rule, scoped past the blanket th rule, fixes every table
   at once. */
.er-root th.er-right{text-align:right}
.er-shell{display:grid;grid-template-columns:245px minmax(0,1fr);min-height:100vh}
.er-rail{position:sticky;top:0;height:100vh;padding:32px 22px;background:var(--er-deep);color:#f4f3e9;display:flex;flex-direction:column;overflow-y:auto}
.er-mark{display:flex;align-items:center;gap:10px;font-weight:800;letter-spacing:.12em;font-size:11px;text-transform:uppercase}
.er-mark-icon{width:28px;height:28px;border-radius:9px;background:var(--er-gold);display:grid;place-items:center;color:var(--er-deep);font:700 16px Georgia}
.er-rail-title{margin:38px 0 6px;color:#fff;font:500 22px/1.1 Georgia}
.er-rail small{color:#afc3be;font-size:11px}
.er-toc{display:grid;gap:4px;margin-top:30px}
.er-toc a{padding:9px 10px;border-radius:8px;color:#b8cbc5;text-decoration:none;font-size:12px}
.er-toc a:hover{background:rgba(255,255,255,.08);color:#fff}
.er-rail-foot{margin-top:auto;border-top:1px solid rgba(255,255,255,.14);padding-top:18px;color:#a9bbb6;font-size:11px}
.er-main{max-width:1400px;width:100%;padding:26px 40px 70px}
.er-topbar{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:26px;color:var(--er-muted);font-size:11px;text-transform:uppercase;letter-spacing:.12em}
.er-topbar-actions{display:flex;gap:8px;align-items:center}
.er-button{border:1px solid var(--er-line);background:var(--er-card);color:var(--er-deep);border-radius:999px;padding:8px 13px;font:700 11px inherit;letter-spacing:.04em;cursor:pointer}
.er-hero{background:var(--er-deep);color:#f8f5ea;border-radius:26px;padding:40px 42px;position:relative;overflow:hidden;box-shadow:var(--er-shadow)}
.er-hero-grid{position:relative;z-index:1;display:grid;grid-template-columns:minmax(0,1fr) 220px;gap:36px;align-items:end}
.er-kicker{text-transform:uppercase;letter-spacing:.16em;font-size:10px;font-weight:800;color:#d9b765;margin-bottom:16px}
.er-eyebrow{text-transform:uppercase;letter-spacing:.16em;font-size:10px;font-weight:800;color:var(--er-deep-2);margin-bottom:8px}
.er-hero h1{max-width:680px;color:#f8f5ea}
.er-hero-sub{margin-top:16px;max-width:620px;color:#c8d7d1;font-size:15px}
.er-hero-meta{display:flex;flex-wrap:wrap;gap:9px;margin-top:22px}
.er-pill{border:1px solid rgba(255,255,255,.18);border-radius:999px;padding:6px 10px;color:#d5e2dc;font-size:11px}
.er-score-card{border-left:1px solid rgba(255,255,255,.18);padding-left:24px}
.er-score-ring{width:126px;height:126px;border-radius:50%;display:grid;place-items:center;position:relative;margin-bottom:12px}
.er-score-ring:before{content:"";position:absolute;inset:9px;border-radius:50%;background:var(--er-deep)}
.er-score-ring strong,.er-score-ring span{position:relative;z-index:1;display:block;text-align:center}
.er-score-ring strong{font:500 36px Georgia}
.er-score-ring span{color:#aebfb9;font-size:10px;margin-top:-6px}
.er-score-label{color:#e4c474;font-weight:800;letter-spacing:.12em;text-transform:uppercase;font-size:11px}
.er-score-note{color:#afc3be;font-size:11px;margin-top:6px}
.er-section{padding-top:58px;scroll-margin-top:20px}
.er-section-head{display:flex;justify-content:space-between;align-items:end;gap:20px;margin-bottom:20px;flex-wrap:wrap}
.er-section-head p{max-width:560px;color:var(--er-muted)}
.er-grid{display:grid;gap:14px}
.er-grid-4{grid-template-columns:repeat(4,minmax(0,1fr))}
.er-grid-3{grid-template-columns:repeat(3,minmax(0,1fr))}
.er-grid-2{grid-template-columns:repeat(2,minmax(0,1fr))}
.er-card{background:var(--er-card);border:1px solid var(--er-line);border-radius:var(--er-radius);padding:20px;box-shadow:0 6px 20px rgba(25,45,40,.035)}
.er-metric-card{min-height:110px;display:flex;flex-direction:column;justify-content:space-between}
.er-metric-label{color:var(--er-muted);font-size:11px;display:flex;align-items:center;flex-wrap:wrap}
.er-metric-value{font:500 26px Georgia;color:var(--er-deep);letter-spacing:-.03em;margin-top:6px}
.er-metric-foot{font-size:10px;color:var(--er-faint);margin-top:4px}
.er-accent-line{height:3px;width:32px;border-radius:4px;background:var(--er-gold);margin-bottom:13px}
.er-verdict{background:var(--er-mint);border-color:#c8e2d8;padding:24px}
.er-verdict h3{color:var(--er-deep);margin-bottom:8px}
.er-verdict p{font-size:15px;max-width:900px}
.er-callout{display:flex;gap:12px;align-items:flex-start;border-radius:14px;padding:14px 16px;background:var(--er-gold-soft);border:1px solid #ead9ad;color:#57451f}
.er-callout strong{display:block;color:#765b20;margin-bottom:3px}
.er-callout-blue{background:var(--er-blue-soft);border-color:#c6dbe7;color:#36566b}
.er-callout-blue strong{color:#426982}
.er-icon{width:21px;height:21px;border-radius:50%;display:grid;place-items:center;flex:0 0 auto;background:var(--er-gold);color:#fff;font-weight:800;font-size:11px}
.er-callout-blue .er-icon{background:var(--er-blue)}
.er-chart-card{padding:22px}
.er-chart-title{display:flex;justify-content:space-between;gap:16px;align-items:start;margin-bottom:16px;flex-wrap:wrap}
.er-chart-title p{color:var(--er-muted);font-size:12px;margin-top:4px}
.er-bars{height:190px;display:flex;align-items:end;gap:clamp(6px,2vw,20px);padding:0 8px 22px;border-bottom:1px solid var(--er-line)}
.er-bar-col{flex:1;height:100%;display:flex;align-items:end;justify-content:center;position:relative}
.er-bar{width:min(50px,70%);background:linear-gradient(180deg,#d5b35c,var(--er-gold));border-radius:7px 7px 2px 2px;min-height:6px;position:relative}
.er-bar span{position:absolute;bottom:calc(100% + 6px);left:50%;transform:translateX(-50%);font-size:9px;color:var(--er-deep);white-space:nowrap;font-weight:700}
.er-bar-col label{position:absolute;bottom:-22px;color:var(--er-faint);font-size:9px}
.er-mini-stat{display:flex;justify-content:space-between;gap:14px;border-bottom:1px solid var(--er-line);padding:10px 0;font-size:12px}
.er-mini-stat>span:first-child{flex-shrink:1;min-width:0}
.er-mini-stat strong{text-align:right;flex-shrink:0;max-width:60%}
.er-mini-stat:last-child{border-bottom:0}
.er-mini-stat strong{color:var(--er-deep)}
.er-hospital{position:relative;padding-left:16px;border-left:3px solid var(--er-mint-2)}
.er-hospital h4{font:700 13px Inter;margin-bottom:3px;color:var(--er-deep)}
.er-hospital p{font-size:11px;color:var(--er-muted);margin:0}
.er-tag{display:inline-flex;align-items:center;border-radius:999px;padding:4px 8px;font-size:10px;font-weight:800;letter-spacing:.04em}
.er-tag-good{background:var(--er-mint);color:#286d5d}.er-tag-watch{background:var(--er-gold-soft);color:#795b1d}.er-tag-risk{background:var(--er-coral-soft);color:#9d4e3d}.er-tag-info{background:var(--er-blue-soft);color:#426982}
.er-risk-card{border-top:4px solid var(--er-coral)}
.er-risk-card-good{border-top-color:#58a893}
.er-risk-card p{color:var(--er-muted);font-size:13px;margin-top:6px}
.er-risk-card .er-evidence{margin-top:13px;padding-top:10px;border-top:1px solid var(--er-line);font-size:10px;color:var(--er-faint)}
.er-source-list{margin:0;padding-left:18px;color:var(--er-muted);font-size:12px}
.er-source-list li{margin:8px 0}
.er-footer{margin-top:60px;padding-top:20px;border-top:1px solid var(--er-line);display:flex;justify-content:space-between;gap:20px;color:var(--er-faint);font-size:11px;flex-wrap:wrap}
.er-muted{color:var(--er-muted)}
/* Only .er-review (the report's closing appendix) forces a fresh page now
   -- real bug found live on GNFC (2026-09-22, user's own report -- "so
   many blank spaces from page 13-19", then separately "first 2 pages
   seem identical"): every major section used to force one (Executive
   view right after the cover, P&L quality, cash flow, peer benchmark, AI
   analysis), and each forced break wastes however much of the PRECEDING
   page its own content didn't fill -- confirmed live twice: the "AI
   Analysis" section's forced break left roughly 80% of the page before it
   blank, and the cover page's own forced break before "01 Executive view"
   left the cover looking like a near-duplicate title/score splash screen
   sitting right before a second one, instead of one continuous page.
   Keeping only the closing appendix as a bookend lets every section flow
   continuously, with the already-tuned break-inside:avoid rules (card/
   table-row level, never the whole grid or a whole multi-topic card)
   still preventing anything from splitting awkwardly mid-content. */
.er-page-break{break-before:page}
.er-peer-note{font-size:11px;color:var(--er-faint);margin-top:12px}
.er-cover{min-height:520px;background:var(--er-card);border:1px solid var(--er-line);border-radius:26px;padding:44px 48px;position:relative;overflow:hidden;box-shadow:var(--er-shadow);display:flex;flex-direction:column;justify-content:space-between;margin-bottom:8px}
.er-cover:after{content:"";position:absolute;left:0;top:0;width:8px;height:100%;background:var(--er-gold)}
.er-cover-top,.er-cover-bottom,.er-cover-grid,.er-cover-thesis{position:relative;z-index:1}
.er-cover-top,.er-cover-bottom{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap}
.er-cover-kicker{color:var(--er-deep-2);font-size:11px;font-weight:800;letter-spacing:.16em;text-transform:uppercase}
.er-cover-date{color:var(--er-faint);font-size:11px;text-transform:uppercase;letter-spacing:.1em}
.er-cover h1{font-size:clamp(40px,6vw,80px);color:var(--er-deep);margin-top:50px}
.er-cover-deck{max-width:620px;color:var(--er-muted);font:500 17px/1.35 Georgia;margin-top:14px}
.er-cover-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:0;border-top:1px solid var(--er-line);border-bottom:1px solid var(--er-line);margin-top:36px}
.er-cover-fact{padding:15px 16px 15px 0;border-right:1px solid var(--er-line)}
.er-cover-fact:not(:first-child){padding-left:16px}
.er-cover-fact:last-child{border-right:0}
.er-cover-fact span{display:block;color:var(--er-faint);font-size:9px;text-transform:uppercase;letter-spacing:.1em;font-weight:800;margin-bottom:6px}
.er-cover-fact strong{display:block;color:var(--er-deep);font:500 21px Georgia;letter-spacing:-.02em}
.er-cover-thesis{display:grid;grid-template-columns:1fr 1fr;gap:22px;margin-top:30px}
.er-cover-thesis h3{font-size:16px;color:var(--er-deep);margin-bottom:6px}
.er-cover-thesis p{color:var(--er-muted);font-size:12px;max-width:460px}
.er-cover-stamp{border:1px solid var(--er-gold);background:var(--er-gold-soft);color:#765b20;border-radius:10px;padding:11px 14px;font-size:10px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;max-width:210px;justify-self:end;align-self:end}
.er-cover-bottom{border-top:1px solid var(--er-line);padding-top:14px;color:var(--er-faint);font-size:10px;text-transform:uppercase;letter-spacing:.09em}
@media(max-width:1050px){.er-shell{grid-template-columns:1fr}.er-rail{position:relative;height:auto;padding:18px 22px}.er-rail-title,.er-toc{display:none}.er-main{padding:20px}.er-hero-grid{grid-template-columns:1fr}.er-score-card{border-left:0;border-top:1px solid rgba(255,255,255,.18);padding:20px 0 0;display:flex;align-items:center;gap:20px}.er-grid-4{grid-template-columns:repeat(2,1fr)}.er-cover-grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:700px){.er-grid-3,.er-grid-2,.er-grid-4{grid-template-columns:1fr}.er-section-head{display:block}.er-cover h1{font-size:44px;margin-top:36px}}
@media print{
@page{size:A4;margin:16mm 12mm}
html,body{background:#fff}
.er-root{background:#fff;font-size:10.5px;color:#17211f}
.er-shell{display:block}
.er-rail{display:none}
.er-main{max-width:none;width:100%;padding:0}
.er-topbar{display:none}
.er-button{display:none}
.er-root h1{font-size:26px}
.er-root h2{font-size:18px}
.er-root h3{font-size:13px}
.er-cover{min-height:0;box-shadow:none;margin-bottom:0}
/* box-shadow is a screen-only nicety — each card's shadow has a 20px blur
   radius against only an 8px print grid gap, so adjacent cards' shadows
   overlap and stack into visible gray smudges between cards (real bug seen
   live in the Quarterly Momentum section's 2x2 grid). The border already
   on every card is enough definition in print. */
.er-card{box-shadow:none}
.er-cover h1{font-size:36px;margin-top:16px}
.er-hero{box-shadow:none}
.er-section{padding-top:20px}
.er-section:first-of-type{padding-top:0}
/* Real bug found live: a section's heading ("02 · Business & operations")
   landing alone at the very bottom of a page, with every card that
   actually belongs to it pushed onto the next page — because nothing told
   the renderer to keep the heading attached to what follows it. Both
   properties matter: break-after on the heading block itself, AND
   break-inside:avoid on the section as a whole for exactly the first
   chunk of it (heading + section-head paragraph, which is small and
   should never split), so the heading is only ever placed where at least
   its own intro text — and normally the next card too — fits alongside it. */
.er-section-head{break-after:avoid;page-break-after:avoid;break-inside:avoid;page-break-inside:avoid}
/* Never split a card, stat block or table row across a page boundary —
   the single biggest cause of the "cut off mid-card" print artifact.
   Deliberately NOT applied to .er-grid itself (real bug found live: forcing
   the whole grid to avoid breaking pushes every card in it to the next
   page the moment ANY one card doesn't fit in the remaining space, leaving
   a large blank gap at the bottom of the previous page for no reason) — a
   grid is allowed to split between rows of cards; only a single card's own
   content never splits. */
.er-card,.er-metric-card,.er-risk-card,.er-verdict,.er-chart-card,.er-callout,
.er-cover-fact,.er-mini-stat,.er-hospital{break-inside:avoid;page-break-inside:avoid}
/* Real bug found live on GNFC (2026-09-22, user's own report -- "so many
   blank spaces from page 13-19" and "order book pipeline management
   commentary goes into other page breaking"): the "Results & concall
   highlights" card bundles 5 independent topic write-ups (Revenue & Sales
   Performance, Profitability & Margins, Capital Expenditure Plans,
   Fundraising & Capital Structure, Order Book & Pipeline) inside ONE
   .er-card -- the same avoid-break-the-whole-grid mistake the comment
   above already fixed for grids, just one level up: forcing this whole
   multi-topic card to never split meant the moment it didn't fit in the
   space left on a page, the ENTIRE card (taller than a full page in two
   columns) jumped to the next page, leaving the previous page mostly
   blank -- and however the printed page happened to cut across it before
   this fix, the Order Book & Pipeline topic (last in the list) was the
   one most often caught mid-break. .er-card-flowing opts this specific
   card back OUT of the blanket avoid-break rule (so the page can break
   between its topics, not just refuse to), while .er-highlight-topic
   keeps EACH individual topic's own heading+bullets from splitting
   mid-list -- the same "avoid at the small-unit level, allow at the
   container level" fix already applied to grids generally. */
.er-card-flowing{break-inside:auto;page-break-inside:auto}
.er-highlight-topic{break-inside:avoid;page-break-inside:avoid}
tr{break-inside:avoid;page-break-inside:avoid}
thead{display:table-header-group}
/* Every grid still fits its cards on one row at print width, just tighter — a
   4-column grid at ~185mm usable width is still readable at this font size,
   and keeping the column count avoids re-flowing card heights awkwardly. */
.er-grid{gap:8px}
/* Wide comparison tables (sector-specific peer metrics, peer benchmark,
   management guidance) previously relied on horizontal scroll
   (overflow-x:auto), which just clips in print since there is no scrollbar —
   this is the literal "columns missing" bug. Force every such wrapper to lay
   out at full print-page width instead, with a fixed table layout so long
   cells wrap onto multiple lines rather than overflowing. */
[style*="overflow"]{overflow:visible!important}
table{table-layout:fixed;font-size:8.5px;width:100%}
th,td{padding:5px 6px;word-break:break-word;overflow-wrap:break-word}
.er-root th{font-size:7.5px;padding:6px}
.er-source-list,.er-peer-note,.er-muted{font-size:9.5px}
.er-tag{font-size:8px;padding:3px 6px}
a[href]{color:inherit;text-decoration:none}
/* Anchor every numbered section to its own page — the reader flips to "05"
   and lands exactly there, and a card never straddles the section break. */
.er-page-break{break-before:page;page-break-before:always}
.er-footer{margin-top:24px}
}
`;
