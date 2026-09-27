import { useState, useEffect } from "react";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import { CalendarClock, TrendingDown, Target, Banknote, ArrowUpCircle, ArrowRightCircle } from "lucide-react";
import { api } from "../../api";
import type { FullAnalysis, EarningsCalendarResponse, CorporateActionItem, ForwardEstimateItem, AnalystConsensusEntry, BrokerReportItem } from "../../types";
import KpiCard from "../charts/KpiCard";
import ChartCard from "../charts/ChartCard";
import { axisTick, gridStroke, chartTooltipStyle, ChartEmptyState } from "../charts/ChartCard";

// Prefer IndianAPI's rating distribution (has real buy/hold/sell %) over
// Yahoo's (mean target only, no distribution) when both are on file —
// never blended, just a display preference between two independently
// sourced, separately attributed rows.
const SOURCE_PRIORITY = ["INDIANAPI", "INDMONEY", "YAHOO_FINANCE"];

function AnalystRatingCard({ bySource }: { bySource: Record<string, AnalystConsensusEntry> }) {
  const sourceKey = SOURCE_PRIORITY.find((s) => bySource[s]) || Object.keys(bySource)[0];
  const entry = sourceKey ? bySource[sourceKey] : null;
  if (!entry) return null;

  const hasDistribution = entry.buy_pct !== null && entry.hold_pct !== null && entry.sell_pct !== null;

  return (
    <ChartCard eyebrow={`Analyst Ratings · ${entry.source}`} title={`${entry.num_analysts ?? "—"} analysts covering this stock`}>
      {hasDistribution && (
        <div className="mb-3">
          <div className="h-2.5 rounded-full overflow-hidden flex" style={{ background: "var(--bg-input)" }}>
            <div style={{ width: `${entry.buy_pct}%`, background: "#4fb3a0" }} />
            <div style={{ width: `${entry.hold_pct}%`, background: "#e0793c" }} />
            <div style={{ width: `${entry.sell_pct}%`, background: "#d9694f" }} />
          </div>
          <div className="flex items-center gap-4 mt-2 text-xs" style={{ color: "var(--text-dim)" }}>
            <span style={{ color: "#4fb3a0" }}>● Buy {entry.buy_pct}%</span>
            <span style={{ color: "#e0793c" }}>● Hold {entry.hold_pct}%</span>
            <span style={{ color: "#d9694f" }}>● Sell {entry.sell_pct}%</span>
          </div>
        </div>
      )}
      {entry.target_price_mean !== null && (
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
          Target price: <span className="font-semibold tabular-nums" style={{ color: "var(--text-primary)" }}>₹{entry.target_price_mean.toFixed(0)}</span>
          {entry.target_price_low !== null && entry.target_price_high !== null && (
            <span style={{ color: "var(--text-dim)" }}> (₹{entry.target_price_low.toFixed(0)}–₹{entry.target_price_high.toFixed(0)})</span>
          )}
          {entry.implied_upside_pct !== null && (
            <span className="ml-2" style={{ color: entry.implied_upside_pct >= 0 ? "#4fb3a0" : "#d9694f" }}>
              {entry.implied_upside_pct >= 0 ? "+" : ""}{entry.implied_upside_pct.toFixed(1)}% upside
            </span>
          )}
        </p>
      )}
      <p className="text-[11px] mt-2" style={{ color: "var(--text-dim)" }}>{entry.disclaimer}</p>
    </ChartCard>
  );
}

function ratingColor(rating: string | null): string {
  const r = (rating || "").toLowerCase();
  if (r.includes("buy") || r.includes("accumulate") || r.includes("outperform")) return "#4fb3a0";
  if (r.includes("sell") || r.includes("reduce") || r.includes("underperform")) return "#d9694f";
  return "#e0793c"; // hold/neutral/accumulate-adjacent
}

function BrokerReportsTable({ reports }: { reports: BrokerReportItem[] }) {
  if (reports.length === 0) return null;
  return (
    <div className="card-rich overflow-hidden">
      <div className="px-4 py-3 flex items-center justify-between" style={{ borderBottom: "1px solid var(--border-subtle)" }}>
        <span className="eyebrow">Broker Report History</span>
        <span className="text-[11px]" style={{ color: "var(--text-dim)" }}>Trendlyne · {reports.length} reports</span>
      </div>
      <div className="overflow-x-auto" style={{ maxHeight: 360, overflowY: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>
              {["Date", "Broker", "Rating", "Target", "Price at Reco", "Upside", ""].map((h, i) => (
                <th key={h} style={{
                  padding: "6px 12px", fontSize: 11, fontWeight: 600, textTransform: "uppercase",
                  letterSpacing: "0.06em", color: "var(--text-dim)", background: "var(--bg-input)",
                  textAlign: i === 0 || i === 1 ? "left" : "right", position: "sticky", top: 0,
                }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {reports.map((r, i) => (
              <tr key={i} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                <td style={{ padding: "8px 12px", fontSize: 12, color: "var(--text-secondary)", whiteSpace: "nowrap" }}>{fmtDate(r.report_date)}</td>
                <td style={{ padding: "8px 12px", fontSize: 12, color: "var(--text-primary)", fontWeight: 500 }}>{r.broker_name}</td>
                <td style={{ padding: "8px 12px" }}>
                  {r.rating && (
                    <span className="badge" style={{
                      color: ratingColor(r.rating), background: `${ratingColor(r.rating)}18`,
                      border: `1px solid ${ratingColor(r.rating)}35`, fontSize: 10,
                    }}>{r.rating}</span>
                  )}
                </td>
                <td style={{ padding: "8px 12px", fontSize: 12, textAlign: "right", color: "var(--text-primary)", fontVariantNumeric: "tabular-nums" }}>
                  {r.target_price !== null ? `₹${r.target_price.toFixed(0)}` : "—"}
                </td>
                <td style={{ padding: "8px 12px", fontSize: 12, textAlign: "right", color: "var(--text-dim)", fontVariantNumeric: "tabular-nums" }}>
                  {r.price_at_reco !== null ? `₹${r.price_at_reco.toFixed(0)}` : "—"}
                </td>
                <td style={{ padding: "8px 12px", fontSize: 12, textAlign: "right", fontVariantNumeric: "tabular-nums", color: (r.upside_pct ?? 0) >= 0 ? "#4fb3a0" : "#d9694f" }}>
                  {r.upside_pct !== null ? `${r.upside_pct >= 0 ? "+" : ""}${r.upside_pct.toFixed(1)}%` : "—"}
                </td>
                <td style={{ padding: "8px 12px", textAlign: "right" }}>
                  {r.reco_changed && (
                    <span title="Recommendation changed"><ArrowUpCircle className="h-3 w-3 inline" style={{ color: "#e8c766" }} /></span>
                  )}
                  {!r.reco_changed && r.target_changed && (
                    <span title="Target price changed"><ArrowRightCircle className="h-3 w-3 inline" style={{ color: "var(--text-dim)" }} /></span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-[11px] px-4 py-2" style={{ color: "var(--text-dim)", borderTop: "1px solid var(--border-subtle)" }}>
        Third-party broker research metadata, for context only — not part of this platform's own analysis.
        <ArrowUpCircle className="h-2.5 w-2.5 inline mx-1" style={{ color: "#e8c766" }} /> = recommendation changed since that broker's prior report.
      </p>
    </div>
  );
}

function fmtDate(d: string | null | undefined) {
  if (!d) return "—";
  const dt = new Date(d);
  return Number.isNaN(dt.getTime()) ? d : dt.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
}

const PERIOD_LABEL: Record<string, string> = {
  "0q": "This Quarter", "+1q": "Next Quarter", "0y": "This Year", "+1y": "Next Year", "LTG": "Long-Term",
};

function EstimateTable({ title, rows, formatter }: {
  title: string; rows: (ForwardEstimateItem & { period_label: string })[]; formatter: (v: number) => string;
}) {
  if (rows.length === 0) return null;
  return (
    <div className="card-rich overflow-hidden">
      <div className="px-4 py-3" style={{ borderBottom: "1px solid var(--border-subtle)" }}>
        <span className="eyebrow">{title}</span>
      </div>
      <div className="overflow-x-auto">
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>
              {["Period", "Low", "Avg", "High", "Analysts", "Growth"].map((h, i) => (
                <th key={h} style={{
                  padding: "6px 12px", fontSize: 11, fontWeight: 600, textTransform: "uppercase",
                  letterSpacing: "0.06em", color: "var(--text-dim)", background: "var(--bg-input)",
                  textAlign: i === 0 ? "left" : "right",
                }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.period_label} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                <td style={{ padding: "8px 12px", fontSize: 13, color: "var(--text-secondary)" }}>
                  {PERIOD_LABEL[r.period_label] || r.period_label}
                </td>
                <td style={{ padding: "8px 12px", fontSize: 13, textAlign: "right", color: "var(--text-secondary)", fontVariantNumeric: "tabular-nums" }}>
                  {r.low !== null ? formatter(r.low) : "—"}
                </td>
                <td style={{ padding: "8px 12px", fontSize: 13, textAlign: "right", fontWeight: 600, color: "var(--text-primary)", fontVariantNumeric: "tabular-nums" }}>
                  {r.avg !== null ? formatter(r.avg) : "—"}
                </td>
                <td style={{ padding: "8px 12px", fontSize: 13, textAlign: "right", color: "var(--text-secondary)", fontVariantNumeric: "tabular-nums" }}>
                  {r.high !== null ? formatter(r.high) : "—"}
                </td>
                <td style={{ padding: "8px 12px", fontSize: 13, textAlign: "right", color: "var(--text-dim)", fontVariantNumeric: "tabular-nums" }}>
                  {r.num_analysts ?? "—"}
                </td>
                <td style={{ padding: "8px 12px", fontSize: 13, textAlign: "right", fontVariantNumeric: "tabular-nums", color: (r.growth_pct ?? 0) >= 0 ? "#4fb3a0" : "#d9694f" }}>
                  {r.growth_pct !== null ? `${r.growth_pct >= 0 ? "+" : ""}${r.growth_pct.toFixed(1)}%` : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function DividendChart({ actions }: { actions: CorporateActionItem[] }) {
  const dividends = actions
    .filter((a) => a.type === "DIVIDEND")
    .slice()
    .reverse()
    .map((a) => ({ date: fmtDate(a.date), value: a.value }));
  const splits = actions.filter((a) => a.type === "SPLIT");

  return (
    <ChartCard eyebrow="Corporate Actions" title="Dividend history (per share)">
      {dividends.length === 0 ? (
        <ChartEmptyState message="No dividend history on record" />
      ) : (
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={dividends} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} vertical={false} />
            <XAxis dataKey="date" tick={axisTick} axisLine={false} tickLine={false} />
            <YAxis tick={axisTick} axisLine={false} tickLine={false} tickFormatter={(v) => `₹${v}`} width={44} />
            <Tooltip {...chartTooltipStyle} formatter={(v: number) => [`₹${v}`, "Dividend"]} />
            <Bar dataKey="value" fill="#4fb3a0" radius={[4, 4, 0, 0]} maxBarSize={28} />
          </BarChart>
        </ResponsiveContainer>
      )}
      {splits.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {splits.map((s, i) => (
            <span key={i} className="badge badge-blue" style={{ fontSize: 11 }}>
              {fmtDate(s.date)} — Stock Split {s.value}:1
            </span>
          ))}
        </div>
      )}
    </ChartCard>
  );
}

export default function CalendarSection({ analysis }: { analysis: FullAnalysis }) {
  const companyId = analysis.company_info?.stock_id || analysis.stock_id;
  const [calendar, setCalendar] = useState<EarningsCalendarResponse["calendar"]>(null);
  const [actions, setActions] = useState<CorporateActionItem[]>([]);
  const [estimates, setEstimates] = useState<Record<string, ForwardEstimateItem[]>>({});
  const [analystConsensus, setAnalystConsensus] = useState<Record<string, AnalystConsensusEntry>>({});
  const [brokerReports, setBrokerReports] = useState<BrokerReportItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!companyId) { setLoading(false); return; }
    setLoading(true);
    Promise.all([
      api.getEarningsCalendar(companyId).catch(() => ({ calendar: null })),
      api.getCorporateActions(companyId).catch(() => ({ actions: [] })),
      api.getForwardEstimates(companyId).catch(() => ({ estimates: {} })),
      api.getAnalystConsensus(companyId).catch(() => ({ by_source: {} })),
      api.getBrokerReports(companyId).catch(() => ({ reports: [] })),
    ]).then(([c, a, e, ac, br]) => {
      setCalendar(c.calendar);
      setActions(a.actions);
      setEstimates(e.estimates);
      setAnalystConsensus(ac.by_source);
      setBrokerReports(br.reports);
    }).finally(() => setLoading(false));
  }, [companyId]);

  if (loading) {
    return <div className="py-12 flex items-center justify-center"><div className="spinner" /></div>;
  }

  const crFmt = (v: number) => `₹${(v / 1e7).toFixed(0)}Cr`;
  const epsRows = (estimates.eps || []).map((r) => ({ ...r }));
  const revenueRows = (estimates.revenue || []).map((r) => ({ ...r }));

  const hasAnalystConsensus = Object.keys(analystConsensus).length > 0;
  const hasAnything = calendar || actions.length > 0 || epsRows.length > 0 || revenueRows.length > 0
    || hasAnalystConsensus || brokerReports.length > 0;
  if (!hasAnything) {
    return (
      <div className="card-rich p-6 text-center text-sm" style={{ color: "var(--text-muted)" }}>
        No calendar or forward-looking data available for this company.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {calendar && (
        <div className="flex flex-wrap gap-4">
          <KpiCard label="Next Earnings" value={fmtDate(calendar.next_earnings_date)} icon={CalendarClock} accent="#c9a227" />
          <KpiCard label="Ex-Dividend Date" value={fmtDate(calendar.ex_dividend_date)} icon={TrendingDown} accent="#e0793c" />
          {calendar.expected_eps_avg !== null && (
            <KpiCard label="Expected EPS (Qtr)" value={`₹${calendar.expected_eps_avg.toFixed(2)}`}
                     sub={calendar.expected_eps_low !== null && calendar.expected_eps_high !== null
                       ? `₹${calendar.expected_eps_low.toFixed(2)}–₹${calendar.expected_eps_high.toFixed(2)}` : undefined}
                     icon={Target} accent="#e8c766" />
          )}
          {calendar.expected_revenue_avg !== null && (
            <KpiCard label="Expected Revenue (Qtr)" value={crFmt(calendar.expected_revenue_avg)}
                     sub={calendar.expected_revenue_low !== null && calendar.expected_revenue_high !== null
                       ? `${crFmt(calendar.expected_revenue_low)}–${crFmt(calendar.expected_revenue_high)}` : undefined}
                     icon={Banknote} accent="#7fb8ff" />
          )}
        </div>
      )}

      {hasAnalystConsensus && <AnalystRatingCard bySource={analystConsensus} />}

      <BrokerReportsTable reports={brokerReports} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <EstimateTable title="Consensus EPS (₹)" rows={epsRows} formatter={(v) => `₹${v.toFixed(2)}`} />
        <EstimateTable title="Consensus Revenue" rows={revenueRows} formatter={crFmt} />
      </div>

      <DividendChart actions={actions} />
    </div>
  );
}
