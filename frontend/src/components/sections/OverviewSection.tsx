import { useState, useEffect } from "react";
import { History } from "lucide-react";
import type { FullAnalysis, ChangeLogData, PricePoint, SalesMarginPoint, ValuationHistoryPoint } from "../../types";

const RANGE_OPTIONS = [
  { key: "3y", label: "3Yr", years: 3 },
  { key: "5y", label: "5Yr", years: 5 },
  { key: "10y", label: "10Yr", years: 10 },
  { key: "max", label: "Max", years: Infinity },
] as const;
type RangeKey = (typeof RANGE_OPTIONS)[number]["key"];

function RangeSwitcher({ value, onChange, disabledKeys }: {
  value: RangeKey; onChange: (k: RangeKey) => void; disabledKeys?: Set<RangeKey>;
}) {
  return (
    <div style={{ display: "flex", gap: 4 }}>
      {RANGE_OPTIONS.map((opt) => {
        const disabled = disabledKeys?.has(opt.key);
        return (
          <button key={opt.key} onClick={() => onChange(opt.key)} disabled={disabled}
            style={{
              padding: "3px 10px", borderRadius: 6, fontSize: 11, fontWeight: 600,
              border: "1px solid",
              borderColor: value === opt.key ? "var(--accent)" : "var(--border-subtle)",
              background: value === opt.key ? "rgba(201,162,39,0.12)" : "transparent",
              color: value === opt.key ? "var(--accent)" : "var(--text-secondary)",
              cursor: disabled ? "not-allowed" : "pointer", opacity: disabled ? 0.35 : 1,
            }}>
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
import { api } from "../../api";
import TrendChart from "../TrendChart";
import ChartCard, { LegendDot } from "../charts/ChartCard";
import ComboTrendChart from "../charts/ComboTrendChart";
import WaterfallChart from "../charts/WaterfallChart";
import type { WaterfallStep } from "../charts/WaterfallChart";
import PriceHistoryChart from "../charts/PriceHistoryChart";

function ChangeLogCallout({ changeLog }: { changeLog: ChangeLogData | null }) {
  if (!changeLog || !changeLog.has_material_change) return null;
  return (
    <div className="card-rich p-5" style={{ borderColor: "rgba(201,162,39,0.3)" }}>
      <div className="flex items-center gap-2 mb-2">
        <History className="h-4 w-4" style={{ color: "var(--accent-blue)" }} />
        <p className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>What Changed Since Last Analysis</p>
      </div>
      <ul className="space-y-1">
        {changeLog.changes.map((c, i) => (
          <li key={i} className="text-sm flex items-start gap-2" style={{ color: "var(--text-secondary)" }}>
            <span style={{ color: "var(--accent-blue)" }}>•</span>{c}
          </li>
        ))}
        {changeLog.new_risks.map((r, i) => (
          <li key={`nr-${i}`} className="text-sm flex items-start gap-2" style={{ color: "#d9694f" }}>
            <span>•</span>New risk: {r}
          </li>
        ))}
        {changeLog.resolved_risks.map((r, i) => (
          <li key={`rr-${i}`} className="text-sm flex items-start gap-2" style={{ color: "#4fb3a0" }}>
            <span>•</span>Resolved risk: {r}
          </li>
        ))}
      </ul>
    </div>
  );
}

function fmt(v: number | null | undefined, suffix = "", d = 1) {
  if (v === null || v === undefined) return "—";
  return `${v.toFixed(d)}${suffix}`;
}

function TrendBadge({ trend }: { trend: string | null | undefined }) {
  if (!trend) return null;
  const cfg: Record<string, { label: string; color: string; bg: string }> = {
    STRONGLY_IMPROVING: { label: "↑↑ Strongly Improving", color: "#4fb3a0", bg: "rgba(79,179,160,0.15)" },
    IMPROVING: { label: "↑ Improving", color: "#4fb3a0", bg: "rgba(79,179,160,0.12)" },
    STABLE: { label: "→ Stable", color: "#a9b3c9", bg: "rgba(111,124,150,0.12)" },
    DETERIORATING: { label: "↓ Deteriorating", color: "#e0793c", bg: "rgba(224,121,60,0.12)" },
    STRONGLY_DETERIORATING: { label: "↓↓ Deteriorating", color: "#d9694f", bg: "rgba(217,105,79,0.12)" },
    VOLATILE: { label: "⚡ Volatile", color: "#e8c766", bg: "rgba(232,199,102,0.12)" },
    INSUFFICIENT_DATA: { label: "N/A", color: "#6f7c96", bg: "rgba(111,124,150,0.12)" },
  };
  const c = cfg[trend] || { label: trend, color: "#a9b3c9", bg: "rgba(111,124,150,0.12)" };
  return (
    <span className="badge" style={{ color: c.color, background: c.bg, border: `1px solid ${c.color}30`, fontSize: 11 }}>
      {c.label}
    </span>
  );
}

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

function applyRange<T>(points: T[], range: RangeKey): T[] {
  const opt = RANGE_OPTIONS.find((o) => o.key === range)!;
  return Number.isFinite(opt.years) ? points.slice(-opt.years) : points;
}

// Latest fiscal year present in all three series — the bridge only makes
// sense when Revenue/EBITDA/PAT are all from the same reporting year.
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

export default function OverviewSection({ analysis }: { analysis: FullAnalysis }) {
  const m = analysis.metrics;
  const companyId = analysis.company_info?.stock_id || analysis.stock_id;
  const [changeLog, setChangeLog] = useState<ChangeLogData | null>(null);
  const [priceChart, setPriceChart] = useState<{ "1y": PricePoint[]; "5y": PricePoint[] }>({ "1y": [], "5y": [] });
  const [salesMargins, setSalesMargins] = useState<SalesMarginPoint[]>([]);
  const [valuationHistory, setValuationHistory] = useState<ValuationHistoryPoint[]>([]);
  const [salesRange, setSalesRange] = useState<RangeKey>("10y");
  const [valuationRange, setValuationRange] = useState<RangeKey>("10y");

  useEffect(() => {
    if (!companyId) return;
    api.getPremiumExtras(companyId)
      .then((r) => {
        setChangeLog(r.change_log);
        setPriceChart(r.price_chart || { "1y": [], "5y": [] });
      })
      .catch(() => { setChangeLog(null); setPriceChart({ "1y": [], "5y": [] }); });
    api.getHistoryCharts(companyId)
      .then((r) => {
        setSalesMargins(r.sales_and_margins || []);
        setValuationHistory(r.valuation || []);
      })
      .catch(() => { setSalesMargins([]); setValuationHistory([]); });
  }, [companyId]);

  const summaryRows = [
    { label: "Revenue CAGR (3Y)", value: fmt(m?.revenue_cagr_3y, "%"), trend: null },
    { label: "EBITDA Margin", value: fmt(m?.ebitda_margin, "%"), trend: m?.ebitda_margin_trend },
    { label: "PAT Margin", value: fmt(m?.pat_margin, "%"), trend: m?.pat_margin_trend },
    { label: "ROCE", value: fmt(m?.roce, "%"), trend: m?.roce_trend },
    { label: "ROE", value: fmt(m?.roe, "%"), trend: m?.roe_trend },
    { label: "FCF/PAT", value: fmt(m?.fcf_to_pat, "%"), trend: m?.fcf_trend },
    { label: "Debt/Equity", value: fmt(m?.debt_to_equity, "x"), trend: m?.debt_trend },
    { label: "P/E", value: fmt(m?.pe_ratio, "x"), trend: null },
    { label: "EV/EBITDA", value: fmt(m?.ev_to_ebitda, "x"), trend: null },
  ];

  const crFmt = (v: number) => `₹${(v / 1e7).toFixed(0)}Cr`;
  const bridge = latestPnlBridge(m);

  return (
    <div className="space-y-4">
      <ChangeLogCallout changeLog={changeLog} />

      <PriceHistoryChart oneYear={priceChart["1y"]} fiveYear={priceChart["5y"]} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Key metrics */}
        <div className="lg:col-span-1 card-rich p-5 space-y-1">
          <h2 className="text-xs font-semibold uppercase tracking-widest mb-3"
              style={{ color: "var(--text-dim)" }}>
            Key Metrics
          </h2>
          {summaryRows.map(({ label, value, trend }) => (
            <div key={label} className="metric-row">
              <span className="text-sm" style={{ color: "var(--text-secondary)" }}>{label}</span>
              <div className="flex items-center gap-2">
                {trend && <TrendBadge trend={trend} />}
                <span className="text-sm font-semibold tabular-nums"
                      style={{ color: "var(--text-primary)" }}>{value}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Revenue + margin combo */}
        <div className="lg:col-span-2 space-y-4">
          {m?.revenue_series && (
            <ChartCard
              eyebrow="Growth & Profitability"
              title="Revenue vs EBITDA Margin"
              legend={<><LegendDot color="#c9a227" label="Revenue" /><LegendDot color="#e0793c" label="EBITDA %" /></>}
            >
              <ComboTrendChart
                barData={m.revenue_series} lineData={m.ebitda_margin_series || {}}
                barLabel="Revenue" lineLabel="EBITDA %"
                barColor="#c9a227" lineColor="#e0793c"
                barFormatter={crFmt} lineFormatter={(v) => `${v.toFixed(0)}%`}
                height={220}
              />
            </ChartCard>
          )}
        </div>
      </div>

      {bridge.length > 0 && (
        <ChartCard eyebrow="Latest Fiscal Year" title="P&L Bridge — Revenue → EBITDA → PAT">
          <WaterfallChart steps={bridge} formatter={crFmt} />
        </ChartCard>
      )}

      {salesMargins.length >= 2 && (() => {
        const ranged = applyRange(salesMargins, salesRange);
        const availableYears = salesMargins.length;
        const disabledKeys = new Set(RANGE_OPTIONS.filter((o) => Number.isFinite(o.years) && o.years > availableYears).map((o) => o.key));
        return (
          <ChartCard
            eyebrow={`${ranged.length}-Year History`}
            title="Sales & Margins"
            legend={
              <div className="flex items-center gap-4 flex-wrap">
                <LegendDot color="#c9a227" label="Sales" />
                <LegendDot color="#e0793c" label="OPM %" />
                <LegendDot color="#4fb3a0" label="NPM %" />
                <RangeSwitcher value={salesRange} onChange={setSalesRange} disabledKeys={disabledKeys} />
              </div>
            }
          >
            <ComboTrendChart
              barData={toSeries(ranged, "sales")}
              lineData={toSeries(ranged, "opm")}
              lineData2={toSeries(ranged, "npm")}
              barLabel="Sales" lineLabel="OPM %" line2Label="NPM %"
              barColor="#c9a227" lineColor="#e0793c" line2Color="#4fb3a0"
              barFormatter={(v) => `₹${v.toFixed(0)}Cr`} lineFormatter={(v) => `${v.toFixed(0)}%`}
              height={240}
            />
            <p className="text-[11px] mt-2" style={{ color: "var(--text-dim)" }}>
              Gross Profit Margin isn't shown — Screener.in's P&L data only reports one aggregate expense line, not a material-cost/COGS breakdown, so a GPM figure isn't available to compute here.
            </p>
          </ChartCard>
        );
      })()}

      {valuationHistory.length >= 2 && (() => {
        const ranged = applyRange(valuationHistory, valuationRange);
        const availableYears = valuationHistory.length;
        const disabledKeys = new Set(RANGE_OPTIONS.filter((o) => Number.isFinite(o.years) && o.years > availableYears).map((o) => o.key));
        return (
          <ChartCard
            eyebrow={`${ranged.length}-Year History`}
            title="EPS & P/E Ratio"
            legend={
              <div className="flex items-center gap-4 flex-wrap">
                <LegendDot color="#c9a227" label="EPS" />
                <LegendDot color="#e0793c" label="P/E" />
                <RangeSwitcher value={valuationRange} onChange={setValuationRange} disabledKeys={disabledKeys} />
              </div>
            }
          >
            <ComboTrendChart
              barData={toSeries(ranged, "eps")}
              lineData={toSeries(ranged, "pe")}
              barLabel="EPS" lineLabel="P/E"
              barColor="#c9a227" lineColor="#e0793c"
              barFormatter={(v) => `₹${v.toFixed(1)}`} lineFormatter={(v) => `${v.toFixed(1)}x`}
              height={240}
            />
          </ChartCard>
        );
      })()}
    </div>
  );
}
