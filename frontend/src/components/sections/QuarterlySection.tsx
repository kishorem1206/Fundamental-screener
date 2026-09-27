import { useState, useEffect } from "react";
import { api } from "../../api";
import type { FullAnalysis, QuarterlyIntelligence, QuarterlySectorKpiMetric } from "../../types";
import ChartCard, { ChartEmptyState } from "../charts/ChartCard";
import ComboTrendChart from "../charts/ComboTrendChart";
import StatementTypeToggle, { type StatementType } from "../StatementTypeToggle";

function fmtSectorKpiValue(value: number | null | undefined, unit: string): string {
  if (value === null || value === undefined) return "—";
  switch (unit) {
    case "%":
      return `${value.toFixed(1)}%`;
    case "MT":
      return `${value.toFixed(2)} MT`;
    case "tonnes":
      return `${value.toLocaleString("en-IN", { maximumFractionDigits: 0 })} t`;
    case "units":
      return value.toLocaleString("en-IN", { maximumFractionDigits: 0 });
    case "days":
      return `${value.toFixed(2)} days`;
    case "USD/bbl":
      return `$${value.toFixed(2)}/bbl`;
    case "INR Cr":
      return `₹${value.toLocaleString("en-IN", { maximumFractionDigits: 0 })} Cr`;
    case "INR":
      return `₹${value.toLocaleString("en-IN", { maximumFractionDigits: Math.abs(value) < 100 ? 2 : 0 })}`;
    case "x":
      return `${value.toFixed(2)}x`;
    case "kt":
      return `${value.toLocaleString("en-IN", { maximumFractionDigits: 0 })} kt`;
    case "Mn sq ft":
      return `${value.toLocaleString("en-IN", { maximumFractionDigits: 1 })} Mn sq ft`;
    case "Mn dwt":
      return `${value.toLocaleString("en-IN", { maximumFractionDigits: 2 })} Mn dwt`;
    case "Bn GB":
      return `${value.toLocaleString("en-IN", { maximumFractionDigits: 2 })} Bn GB`;
    case "USD":
      return `US$${value.toLocaleString("en-IN", { maximumFractionDigits: 2 })}`;
    case "tpd":
      return `${value.toLocaleString("en-IN", { maximumFractionDigits: 0 })} t/day`;
    case "MLD":
      return `${value.toLocaleString("en-IN", { maximumFractionDigits: 0 })} MLD`;
    case "km":
      return `${value.toLocaleString("en-IN", { maximumFractionDigits: 0 })} km`;
    case "TBtu":
      return `${value.toLocaleString("en-IN", { maximumFractionDigits: 0 })} TBtu`;
    case "MMTPA":
      return `${value.toLocaleString("en-IN", { maximumFractionDigits: 1 })} MMTPA`;
    case "MMSCM":
      return `${value.toLocaleString("en-IN", { maximumFractionDigits: 1 })} MMSCM`;
    case "MMSCMD":
      return `${value.toLocaleString("en-IN", { maximumFractionDigits: 2 })} MMSCMD`;
    case "lakh":
      return `${value.toLocaleString("en-IN", { maximumFractionDigits: 2 })} lakh`;
    case "INR/SCM":
      return `₹${value.toLocaleString("en-IN", { maximumFractionDigits: 2 })}/SCM`;
    case "MW":
      return `${value.toLocaleString("en-IN", { maximumFractionDigits: 0 })} MW`;
    case "MU":
      return `${value.toLocaleString("en-IN", { maximumFractionDigits: 0 })} MU`;
    case "INR/kWh":
      return `₹${value.toLocaleString("en-IN", { maximumFractionDigits: 2 })}/kWh`;
    case "ckm":
      return `${value.toLocaleString("en-IN", { maximumFractionDigits: 0 })} ckm`;
    case "MVA":
      return `${value.toLocaleString("en-IN", { maximumFractionDigits: 0 })} MVA`;
    case "Bn units":
      return `${value.toLocaleString("en-IN", { maximumFractionDigits: 2 })} Bn units`;
    case "GB":
      return `${value.toLocaleString("en-IN", { maximumFractionDigits: 1 })} GB`;
    case "Mn":
      return `${value.toLocaleString("en-IN", { maximumFractionDigits: 2 })} Mn`;
    case "Bn":
      return `${value.toLocaleString("en-IN", { maximumFractionDigits: 2 })} Bn`;
    case "USD/day":
      return `US$${value.toLocaleString("en-IN", { maximumFractionDigits: 0 })}/day`;
    case "USD Bn":
      return `US$${value.toFixed(2)} Bn`;
    case "USD Mn":
      return `US$${value.toLocaleString("en-IN", { maximumFractionDigits: 0 })} Mn`;
    case "USD k":
      return `US$${value.toFixed(1)}k`;
    default:
      return value.toLocaleString("en-IN", { maximumFractionDigits: 2 });
  }
}

function fmt(v: number | null | undefined, suffix = "", d = 1) {
  if (v === null || v === undefined) return "—";
  return `${v.toFixed(d)}${suffix}`;
}

function fmtCr(v: number | null | undefined) {
  if (v === null || v === undefined) return "—";
  return `₹${v.toLocaleString("en-IN", { maximumFractionDigits: 0 })} Cr`;
}

function readable(s: string | null | undefined): string {
  if (!s) return "—";
  return s.toLowerCase().split("_").map((w) => w[0].toUpperCase() + w.slice(1)).join(" ");
}

function trendColor(direction: string | undefined): string {
  switch (direction) {
    case "EXPANSION": return "#4fb3a0";
    case "COMPRESSION": return "#d9694f";
    case "VOLATILE": return "#e0793c";
    case "STABLE": return "#7fb8ff";
    default: return "var(--text-dim)";
  }
}

function growthColor(v: number | null | undefined): string {
  if (v === null || v === undefined) return "var(--text-dim)";
  return v >= 0 ? "#4fb3a0" : "#d9694f";
}

const FLAG_LABELS: Record<string, string> = {
  sequential_deceleration: "Sequential Deceleration",
  margin_inflection: "Margin Inflection",
  other_income_dependency: "Other-Income Dependency",
  tax_rate_anomaly: "Tax Rate Anomaly",
};
const POSITIVE_FLAGS = new Set<string>([]); // every flag here is a caution signal, not a positive one

function StatBlock({ label, value, sub, color }: { label: string; value: string; sub?: string | null; color?: string }) {
  return (
    <div>
      <p className="text-xs" style={{ color: "var(--text-dim)" }}>{label}</p>
      <p className="text-lg font-semibold mt-0.5" style={{ color: color ?? "var(--text-primary)", fontFamily: "var(--font-display)" }}>
        {value}
      </p>
      {sub && <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>{sub}</p>}
    </div>
  );
}

// Physical KPIs (production/sales volume, market share, dealer inventory,
// per-tonne economics) sourced from NSE quarterly Investor Presentation
// filings — a genuinely different document source than the rest of this
// tab (Screener-sourced financials). Renders its own trailing-quarters
// history as a compact table rather than a chart when 2+ quarters exist —
// most companies only have 1 quarter on record so far (this engine was
// just built), so a full chart component isn't warranted yet; the table
// scales naturally as more quarters accumulate over time.
function SectorKpiCard({ metric }: { metric: QuarterlySectorKpiMetric }) {
  const periods = Object.keys(metric.series).sort();
  const hasHistory = periods.length > 1;
  return (
    <div className="rounded-xl p-4" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)" }}>
      <p className="text-xs" style={{ color: "var(--text-dim)" }}>{metric.label}</p>
      <p className="text-xl font-semibold mt-0.5" style={{ color: "var(--text-primary)", fontFamily: "var(--font-display)" }}>
        {fmtSectorKpiValue(metric.latest_value, metric.unit)}
      </p>
      {metric.source_label && (
        <p className="text-[11px] mt-1.5" style={{ color: "var(--text-dim)" }} title={metric.source_document ?? undefined}>
          {metric.source_url ? (
            <a href={metric.source_url} target="_blank" rel="noreferrer" style={{ color: "var(--text-muted)", textDecoration: "underline" }}>
              {metric.source_label}
            </a>
          ) : metric.source_label}
          {metric.confidence ? ` · ${metric.confidence.toLowerCase()} confidence` : ""}
          {metric.data_type === "CALCULATED" ? " · derived" : ""}
        </p>
      )}
      {hasHistory && (
        <table className="w-full text-xs mt-3">
          <tbody>
            {periods.slice(-4).reverse().map((p) => (
              <tr key={p}>
                <td className="py-0.5 pr-2" style={{ color: "var(--text-dim)" }}>{p}</td>
                <td className="py-0.5 text-right tabular-nums" style={{ color: "var(--text-muted)" }}>
                  {fmtSectorKpiValue(metric.series[p], metric.unit)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default function QuarterlySection({ analysis }: { analysis: FullAnalysis }) {
  const companyId = analysis.company_info?.stock_id || analysis.stock_id;
  const [statementType, setStatementType] = useState<StatementType | null>(null);
  const [qi, setQi] = useState<QuarterlyIntelligence | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    setStatementType(null);
  }, [companyId]);

  useEffect(() => {
    if (!companyId) return;
    setLoading(true);
    api.getQuarterlyIntelligence(companyId, statementType ?? undefined)
      .then((r) => { setQi(r); setError(false); })
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [companyId, statementType]);

  const displayedType: StatementType = statementType ?? (qi?.statement_type as StatementType | undefined) ?? "CONSOLIDATED";
  const toggle = qi?.single_statement_source
    ? null
    : <StatementTypeToggle value={displayedType} onChange={setStatementType} />;

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="flex justify-end">{toggle}</div>
        <div className="text-sm p-6" style={{ color: "var(--text-dim)" }}>Loading Quarterly Analysis…</div>
      </div>
    );
  }
  if (error || !qi) {
    return (
      <div className="space-y-4">
        <div className="flex justify-end">{toggle}</div>
        <div className="text-sm p-6" style={{ color: "var(--text-dim)" }}>Quarterly Analysis is unavailable for this company right now.</div>
      </div>
    );
  }
  if (!qi.period) {
    return (
      <div className="space-y-4">
        <div className="flex justify-end">{toggle}</div>
        <div className="card-rich p-6 text-sm" style={{ color: "var(--text-dim)" }}>
          No {displayedType === "CONSOLIDATED" ? "consolidated" : "standalone"} quarterly data available for this
          company yet — re-run the analysis to ingest it.
        </div>
      </div>
    );
  }

  const latestQoqSales = qi.qoq.sales[qi.period];
  const latestYoySales = qi.yoy.sales[qi.period];
  const latestQoqNetProfit = qi.qoq.net_profit[qi.period];
  const latestYoyNetProfit = qi.yoy.net_profit[qi.period];

  const netMargin: Record<string, number> = {};
  for (const period of Object.keys(qi.series.sales || {})) {
    const sales = qi.series.sales[period];
    const netProfit = qi.series.net_profit?.[period];
    if (sales && netProfit !== undefined) netMargin[period] = (netProfit / sales) * 100;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-end">{toggle}</div>

      {/* 1. Latest quarter snapshot */}
      <div className="card-rich p-5">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <p className="eyebrow">Latest Quarter</p>
            <p className="text-lg font-semibold mt-1" style={{ color: "var(--text-primary)", fontFamily: "var(--font-display)" }}>
              {qi.period} · {qi.statement_type}
            </p>
          </div>
          <span className="text-xs text-right" style={{ color: "var(--text-dim)" }}>
            {qi.quarters_available} quarter(s) on record
          </span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-5">
          <StatBlock label="Sales QoQ" value={fmt(latestQoqSales, "%")} color={growthColor(latestQoqSales)} />
          <StatBlock label="Sales YoY" value={fmt(latestYoySales, "%")} color={growthColor(latestYoySales)} />
          <StatBlock label="Net Profit QoQ" value={fmt(latestQoqNetProfit, "%")} color={growthColor(latestQoqNetProfit)} />
          <StatBlock label="Net Profit YoY" value={fmt(latestYoyNetProfit, "%")} color={growthColor(latestYoyNetProfit)} />
        </div>
      </div>

      {/* 2. Trailing quarters chart */}
      <ChartCard eyebrow="Trailing Quarters" title="Sales, Operating Margin & Net Margin">
        <ComboTrendChart
          barData={qi.series.sales || {}}
          lineData={qi.series.opm || {}}
          lineData2={netMargin}
          barLabel="Sales"
          lineLabel="OPM %"
          line2Label="Net Margin %"
          barFormatter={(v) => fmtCr(v)}
          lineFormatter={(v) => fmt(v, "%")}
        />
      </ChartCard>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 3. Margin trend */}
        <ChartCard eyebrow="Margin Trend" title={`Trailing ${qi.quarters_available > 8 ? 8 : qi.quarters_available} quarters`}>
          <div className="grid grid-cols-2 gap-4">
            <StatBlock label="OPM Direction" value={readable(qi.margin_trend.opm_direction)} color={trendColor(qi.margin_trend.opm_direction)} />
            <StatBlock label="Net Margin Direction" value={readable(qi.margin_trend.net_margin_direction)} color={trendColor(qi.margin_trend.net_margin_direction)} />
          </div>
        </ChartCard>

        {/* 4. Flags */}
        <ChartCard eyebrow="Diagnostics" title="What changed">
          {qi.flags.length ? (
            <ul className="space-y-2.5">
              {qi.flags.map((f, i) => (
                <li key={`${f.flag}-${f.period}-${i}`} className="flex items-start gap-2 text-sm" style={{ color: POSITIVE_FLAGS.has(f.flag) ? "#4fb3a0" : "#e0793c" }}>
                  <span className="w-1.5 h-1.5 rounded-full flex-shrink-0 mt-1.5" style={{ background: "currentColor" }} />
                  <span>
                    <span className="font-medium">{FLAG_LABELS[f.flag] || readable(f.flag)}</span>
                    {" "}<span style={{ color: "var(--text-muted)" }}>({f.period})</span>
                    <br /><span style={{ color: "var(--text-muted)" }}>{f.detail}</span>
                  </span>
                </li>
              ))}
            </ul>
          ) : <ChartEmptyState message="No flags raised" />}
        </ChartCard>
      </div>

      {/* 5. Sector-specific quarterly KPIs (Quarterly Sector KPI Extraction
          Engine, 2026-09-20) — only rendered for sectors with a
          configured area and only once this company's presentation has
          actually resolved to real data; a clean no-op otherwise, not an
          empty/broken-looking card. */}
      {qi.sector_kpis?.available && qi.sector_kpis.metrics && qi.sector_kpis.metrics.length > 0 && (
        <ChartCard
          eyebrow={`${qi.sector_kpis.sector_name} — Sector KPIs`}
          title={`From the latest NSE filings${qi.sector_kpis.latest_quarter ? ` · ${qi.sector_kpis.latest_quarter}` : ""}`}
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {qi.sector_kpis.metrics.map((m) => (
              <SectorKpiCard key={m.metric_key} metric={m} />
            ))}
          </div>
          <p className="text-xs mt-4" style={{ color: "var(--text-dim)" }}>
            Sourced from NSE filings (investor presentation, results press release, earnings call), not the financial
            statements above — physical volumes, occupancy, unit economics and similar aren't in Screener/yfinance.
          </p>
        </ChartCard>
      )}
    </div>
  );
}
