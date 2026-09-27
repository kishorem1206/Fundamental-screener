import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Legend,
} from "recharts";
import type { FullAnalysis } from "../../types";
import TrendChart from "../TrendChart";
import ChartCard, { LegendDot, axisTick, gridStroke, chartTooltipStyle, ChartEmptyState } from "../charts/ChartCard";
import ComboTrendChart from "../charts/ComboTrendChart";

function fmt(v: number | null | undefined, suffix = "", d = 1) {
  if (v === null || v === undefined) return "—";
  return `${v.toFixed(d)}${suffix}`;
}

function trendArrow(trend: string | null | undefined) {
  if (!trend) return { symbol: "→", color: "var(--text-dim)" };
  const t = trend.toUpperCase();
  if (t === "STRONGLY_IMPROVING" || t === "IMPROVING" || t === "UP") return { symbol: "↑", color: "#4fb3a0" };
  if (t === "STRONGLY_DETERIORATING" || t === "DETERIORATING" || t === "DOWN" || t === "DECLINING") {
    return { symbol: "↓", color: "#d9694f" };
  }
  return { symbol: "→", color: "var(--text-dim)" };
}

// Matches ChartCard's card-rich chrome (glass, rounded, shadowed) so the
// metric-group cards read as the same visual family as the chart cards
// above them, instead of the flatter plain `.card` style they used before.
function MetricTable({ title, accent, rows }: {
  title: string;
  accent: string;
  rows: { label: string; value: string | number; unit?: string; trend?: string | null }[];
}) {
  return (
    <div className="card-rich p-5">
      <div className="flex items-center gap-2 mb-3">
        <span className="w-1.5 h-1.5 rounded-full" style={{ background: accent }} />
        <h3 className="text-[10.5px] font-bold uppercase tracking-widest"
            style={{ color: accent }}>{title}</h3>
      </div>
      <div>
        {rows.map(({ label, value, unit, trend }) => {
          const t = trend !== undefined ? trendArrow(trend) : null;
          return (
            <div key={label} className="metric-row">
              <span className="text-sm" style={{ color: "var(--text-secondary)" }}>{label}</span>
              <span className="flex items-center gap-2">
                <span className="text-sm font-semibold tabular-nums"
                      style={{ color: "var(--text-primary)" }}>
                  {value}{unit}
                </span>
                {t && <span style={{ fontSize: 13, color: t.color, fontWeight: 600 }}>{t.symbol}</span>}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function RatioTable({ m, sector_medians }: {
  m: FullAnalysis["metrics"];
  sector_medians?: Record<string, number | null>;
}) {
  type RatioRow = {
    label: string;
    current: string;
    avg3y: string;
    avg5y: string;
    sector: string;
    trendKey: keyof NonNullable<typeof m>;
    suffix: string;
  };

  const rows: RatioRow[] = [
    {
      label: "ROCE",
      current: fmt(m?.roce, "%"),
      avg3y: fmt(m?.roce_3y_avg, "%"),
      avg5y: fmt(m?.roce_5y_avg, "%"),
      sector: fmt(sector_medians?.roce, "%"),
      trendKey: "roce_trend",
      suffix: "%",
    },
    {
      label: "EBITDA Margin",
      current: fmt(m?.ebitda_margin, "%"),
      avg3y: fmt(m?.ebitda_margin_3y_avg, "%"),
      avg5y: fmt(m?.ebitda_margin_5y_avg, "%"),
      sector: fmt(sector_medians?.ebitda_margin, "%"),
      trendKey: "ebitda_margin_trend",
      suffix: "%",
    },
    {
      label: "ROE",
      current: fmt(m?.roe, "%"),
      avg3y: fmt(m?.roe_3y_avg, "%"),
      avg5y: fmt(m?.roe_5y_avg, "%"),
      sector: fmt(sector_medians?.roe, "%"),
      trendKey: "roe_trend",
      suffix: "%",
    },
    {
      label: "PAT Margin",
      current: fmt(m?.pat_margin, "%"),
      avg3y: fmt(m?.pat_margin_3y_avg, "%"),
      avg5y: fmt(m?.pat_margin_5y_avg, "%"),
      sector: fmt(sector_medians?.pat_margin, "%"),
      trendKey: "pat_margin_trend",
      suffix: "%",
    },
    {
      label: "Gross Margin",
      current: fmt(m?.gross_margin, "%"),
      avg3y: fmt(m?.gross_margin_3y_avg, "%"),
      avg5y: fmt(m?.gross_margin_5y_avg, "%"),
      sector: "—",
      trendKey: "ebitda_margin_trend",
      suffix: "%",
    },
    {
      label: "FCF / PAT",
      current: fmt(m?.fcf_to_pat, "%"),
      avg3y: fmt(m?.fcf_to_pat_3y_avg, "%"),
      avg5y: fmt(m?.fcf_to_pat_5y_avg, "%"),
      sector: fmt(sector_medians?.fcf_to_pat, "%"),
      trendKey: "fcf_trend",
      suffix: "%",
    },
    {
      label: "Debt / Equity",
      current: fmt(m?.debt_to_equity, "x"),
      avg3y: fmt(m?.debt_to_equity_3y_avg, "x"),
      avg5y: fmt(m?.debt_to_equity_5y_avg, "x"),
      sector: fmt(sector_medians?.debt_to_equity, "x"),
      trendKey: "debt_trend",
      suffix: "x",
    },
    {
      label: "Net Debt / EBITDA",
      current: fmt(m?.net_debt_to_ebitda, "x"),
      avg3y: fmt(m?.net_debt_to_ebitda_3y_avg, "x"),
      avg5y: fmt(m?.net_debt_to_ebitda_5y_avg, "x"),
      sector: fmt(sector_medians?.net_debt_to_ebitda, "x"),
      trendKey: "debt_trend",
      suffix: "x",
    },
    {
      label: "Interest Coverage",
      current: fmt(m?.interest_coverage, "x"),
      avg3y: fmt(m?.interest_coverage_3y_avg, "x"),
      avg5y: "—",
      sector: "—",
      trendKey: "debt_trend",
      suffix: "x",
    },
  ];

  const thStyle: React.CSSProperties = {
    padding: "8px 16px", fontSize: 11, fontWeight: 600,
    textTransform: "uppercase", letterSpacing: "0.06em",
    color: "var(--text-dim)", background: "var(--bg-input)",
    textAlign: "right", whiteSpace: "nowrap",
  };

  return (
    <div className="card-rich overflow-hidden">
      <div style={{ padding: "14px 20px", borderBottom: "1px solid var(--border-subtle)" }}>
        <p className="eyebrow">Ratio Table</p>
        <p className="text-sm font-semibold mt-0.5" style={{ color: "var(--text-primary)" }}>
          Current vs 3Y/5Y Averages &amp; Sector
        </p>
      </div>
      <div className="overflow-x-auto">
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>
              <th style={{ ...thStyle, textAlign: "left", paddingLeft: 20 }}>Metric</th>
              <th style={thStyle}>Current</th>
              <th style={thStyle}>3Y Avg</th>
              <th style={thStyle}>5Y Avg</th>
              <th style={thStyle}>Sector</th>
              <th style={{ ...thStyle, paddingRight: 20 }}>Trend</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const trend = trendArrow(m?.[row.trendKey] as string | null);
              return (
                <tr key={row.label} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                  <td style={{ padding: "10px 16px", fontSize: 13, color: "var(--text-secondary)" }}>
                    {row.label}
                  </td>
                  <td style={{ padding: "10px 16px", fontSize: 13, textAlign: "right",
                                fontVariantNumeric: "tabular-nums", fontWeight: 600,
                                color: "var(--text-primary)" }}>
                    {row.current}
                  </td>
                  <td style={{ padding: "10px 16px", fontSize: 13, textAlign: "right",
                                fontVariantNumeric: "tabular-nums", color: "var(--text-secondary)" }}>
                    {row.avg3y}
                  </td>
                  <td style={{ padding: "10px 16px", fontSize: 13, textAlign: "right",
                                fontVariantNumeric: "tabular-nums", color: "var(--text-dim)" }}>
                    {row.avg5y}
                  </td>
                  <td style={{ padding: "10px 16px", fontSize: 13, textAlign: "right",
                                fontVariantNumeric: "tabular-nums", color: "var(--text-dim)" }}>
                    {row.sector}
                  </td>
                  <td style={{ padding: "10px 20px 10px 16px", textAlign: "right" }}>
                    <span style={{ fontSize: 16, color: trend.color, fontWeight: 600 }}>
                      {trend.symbol}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// Grouped bar: Revenue/EBITDA/PAT/EPS CAGR across the horizons the backend
// actually computed (EBITDA only has a 3Y figure; others may have 3/5/10Y).
function CagrBarChart({ m }: { m: FullAnalysis["metrics"] }) {
  const rows = [
    { metric: "Revenue", "3Y": m?.revenue_cagr_3y, "5Y": m?.revenue_cagr_5y, "10Y": m?.revenue_cagr_10y },
    { metric: "EBITDA", "3Y": m?.ebitda_cagr_3y },
    { metric: "PAT", "3Y": m?.pat_cagr_3y, "5Y": m?.pat_cagr_5y, "10Y": m?.pat_cagr_10y },
    { metric: "EPS", "3Y": m?.eps_cagr_3y, "5Y": m?.eps_cagr_5y, "10Y": m?.eps_cagr_10y },
  ].filter((r) => r["3Y"] != null || r["5Y"] != null || r["10Y"] != null);

  if (rows.length === 0) return <ChartEmptyState message="No CAGR data available" />;

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={rows} margin={{ top: 4, right: 4, left: 0, bottom: 0 }} barGap={4}>
        <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} vertical={false} />
        <XAxis dataKey="metric" tick={axisTick} axisLine={false} tickLine={false} />
        <YAxis tick={axisTick} axisLine={false} tickLine={false} tickFormatter={(v) => `${v}%`} width={48} />
        <Tooltip {...chartTooltipStyle} formatter={(v: number) => [`${v.toFixed(1)}%`, ""]} />
        <Legend wrapperStyle={{ fontSize: 11, color: "var(--text-dim)" }} />
        <Bar dataKey="3Y" fill="#c9a227" radius={[4, 4, 0, 0]} maxBarSize={26} />
        <Bar dataKey="5Y" fill="#e8c766" radius={[4, 4, 0, 0]} maxBarSize={26} />
        <Bar dataKey="10Y" fill="#7fb8ff" radius={[4, 4, 0, 0]} maxBarSize={26} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export default function FinancialsSection({ analysis }: { analysis: FullAnalysis }) {
  const m = analysis.metrics;
  const sectorMedians = analysis.peers?.sector_medians;
  const crFmt = (v: number) => `₹${(v / 1e7).toFixed(0)}Cr`;

  return (
    <div className="space-y-4">
      {/* CAGR comparison + CFO vs FCF */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard eyebrow="Growth Consistency" title="CAGR across horizons">
          <CagrBarChart m={m} />
        </ChartCard>
        {m?.cfo_series && m?.fcf_series && (
          <ChartCard
            eyebrow="Cash Generation"
            title="CFO vs Free Cash Flow"
            legend={<><LegendDot color="#c9a227" label="CFO" /><LegendDot color="#e0793c" label="FCF" /></>}
          >
            <ComboTrendChart
              barData={m.cfo_series} lineData={m.fcf_series}
              barLabel="CFO" lineLabel="FCF"
              barColor="#c9a227" lineColor="#e0793c"
              barFormatter={crFmt} lineFormatter={crFmt}
              height={220}
            />
          </ChartCard>
        )}
      </div>

      {/* Trend charts — same ChartCard chrome as the row above, so the whole
          top half of the page reads as one consistent chart family instead
          of two different card styles. */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {m?.pat_series && (
          <ChartCard eyebrow="Earnings" title="Net Income / PAT (₹)">
            <TrendChart data={m.pat_series} color="#4fb3a0" formatter={(v) => `₹${(v / 1e7).toFixed(0)}Cr`} />
          </ChartCard>
        )}
        {m?.roce_series && (
          <ChartCard eyebrow="Returns" title="Return on Capital Employed (ROCE %)">
            <TrendChart data={m.roce_series} color="#e8c766" formatter={(v) => `${v.toFixed(1)}%`} />
          </ChartCard>
        )}
        {m?.fcf_series && (
          <ChartCard eyebrow="Cash Flow" title="Free Cash Flow (₹)">
            <TrendChart data={m.fcf_series} color="#e0793c" formatter={(v) => `₹${(v / 1e7).toFixed(0)}Cr`} />
          </ChartCard>
        )}
        {m?.roe_series && (
          <ChartCard eyebrow="Returns" title="Return on Equity (ROE %)">
            <TrendChart data={m.roe_series} color="#7fb8ff" formatter={(v) => `${v.toFixed(1)}%`} />
          </ChartCard>
        )}
      </div>

      {/* Ratio Table — the definitive profitability/leverage view (current +
          3Y/5Y history + sector + trend), so the cards below only need to
          carry metrics that AREN'T already here. */}
      <RatioTable m={m} sector_medians={sectorMedians} />

      {/* Metric groups — exactly 3 cards (was 5, with an awkward half-empty
          trailing row) after folding out everything the Ratio Table and the
          CAGR chart above already cover; each carries only what's genuinely
          additional, so nothing on this page says the same thing twice. */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricTable title="Profitability & Returns" accent="var(--accent-gold-bright)" rows={[
          { label: "EBIT Margin", value: fmt(m?.ebit_margin, "%") },
          { label: "ROIC", value: fmt(m?.roic, "%") },
          { label: "CFO/PAT", value: fmt(m?.cfo_to_pat, "%") },
          { label: "FCF Margin", value: fmt(m?.fcf_margin, "%") },
          { label: "FCF CAGR 3Y", value: fmt(m?.fcf_cagr_3y, "%") },
        ]} />
        <MetricTable title="Balance Sheet & Efficiency" accent="var(--accent-sky)" rows={[
          { label: "Current Ratio", value: fmt(m?.current_ratio, "x") },
          { label: "Asset Turnover", value: fmt(m?.asset_turnover, "x") },
          { label: "Inventory Days", value: fmt(m?.inventory_days, " days", 0), trend: m?.inventory_days_trend },
          { label: "Receivable Days", value: fmt(m?.receivable_days, " days", 0), trend: m?.receivable_days_trend },
          { label: "Payable Days", value: fmt(m?.payable_days, " days", 0), trend: m?.payable_days_trend },
          { label: "CapEx/Revenue", value: fmt(m?.capex_to_revenue, "%") },
        ]} />
        <MetricTable title="Valuation" accent="var(--accent-yellow)" rows={[
          { label: "P/E", value: fmt(m?.pe_ratio, "x") },
          { label: "Forward P/E", value: fmt(m?.forward_pe, "x") },
          { label: "P/B", value: fmt(m?.pb_ratio, "x") },
          { label: "EV/EBITDA", value: fmt(m?.ev_to_ebitda, "x") },
          { label: "EV/Sales", value: fmt(m?.ev_to_sales, "x") },
          { label: "FCF Yield", value: fmt(m?.fcf_yield, "%") },
          { label: "Dividend Yield", value: fmt(m?.dividend_yield, "%") },
        ]} />
      </div>
    </div>
  );
}
