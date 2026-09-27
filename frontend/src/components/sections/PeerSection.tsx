import { useState, useEffect } from "react";
import { api } from "../../api";
import type { FullAnalysis, PeerPerformanceSeries } from "../../types";
import ChartCard from "../charts/ChartCard";
import PeerScatterChart from "../charts/PeerScatterChart";
import RebasedPerformanceChart from "../charts/RebasedPerformanceChart";
import PercentileBar from "../charts/PercentileBar";

function fmt(v: number | null | undefined, suffix = "", d = 1) {
  if (v === null || v === undefined) return "—";
  return `${v.toFixed(d)}${suffix}`;
}

// Same unit-formatting convention as SectorSection/EditorialReport — a
// sector metric's `unit` is a free-form string ("%", "INR", "days",
// "count", ...), not a fixed enum, so this stays permissive rather than
// hardcoding every unit this codebase's ~35 sector frameworks use.
function fmtSectorVal(v: number | null | undefined, unit?: string) {
  if (v === null || v === undefined) return "—";
  const u = (unit || "").toLowerCase();
  if (u === "%") return `${v.toFixed(1)}%`;
  if (u === "x") return `${v.toFixed(2)}x`;
  if (u === "inr" || u === "inr cr" || u === "cr") return `₹${v.toLocaleString("en-IN", { maximumFractionDigits: 0 })}${u === "inr" ? "" : " Cr"}`;
  if (u === "days") return `${v.toFixed(1)} days`;
  if (u === "count") return v.toLocaleString("en-IN", { maximumFractionDigits: 0 });
  return unit ? `${v.toLocaleString("en-IN", { maximumFractionDigits: 2 })} ${unit}` : v.toLocaleString("en-IN", { maximumFractionDigits: 2 });
}

export default function PeerSection({ analysis }: { analysis: FullAnalysis }) {
  const [tab, setTab] = useState<"table" | "percentile">("table");
  const companyId = analysis.company_info?.stock_id || analysis.stock_id;
  const [perfSeries, setPerfSeries] = useState<PeerPerformanceSeries[]>([]);

  useEffect(() => {
    if (!companyId) return;
    api.getPremiumExtras(companyId)
      .then((r) => setPerfSeries(r.peer_performance?.series || []))
      .catch(() => setPerfSeries([]));
  }, [companyId]);

  const peersData = analysis.peers;
  const peers = peersData?.peers || [];
  const subject = analysis.company_info;
  const metrics = analysis.metrics;

  if (peers.length === 0) {
    return (
      <div className="card p-6 text-center text-sm" style={{ color: "var(--text-muted)" }}>
        No peer comparison data available
      </div>
    );
  }

  const sectorLabel = peersData?.industry || peersData?.sector || "sector";

  // ── Sector-specific metrics (ALOS/ARPOB for hospitals, ARR/RevPAR for
  // hotels, ARPU/churn for telecom, ...) — same fields the Sector tab shows
  // for the subject, now compared across the named peer set too. Only
  // rendered for metric ids this analysis's framework actually declares as
  // non-yfinance (`sector_metric_ids`), and only the ones with a label in
  // sector_analysis.key_metrics so the table never shows a bare metric key.
  const sectorMetricIds = peersData?.sector_metric_ids || [];
  const sectorMetricMeta = new Map((analysis.sector_analysis?.key_metrics || []).map((m) => [m.name, m]));
  const sectorMetricRows = sectorMetricIds
    .map((id) => sectorMetricMeta.get(id))
    .filter((m): m is NonNullable<typeof m> => !!m);
  const hasAnySectorMetricValue = sectorMetricRows.some((m) =>
    (peersData?.company_metrics?.[m.name] ?? null) !== null ||
    peers.some((p) => (p.sector_metrics?.[m.name] ?? null) !== null),
  );

  // ── Peer table columns ─────────────────────────────────────────────────────
  type PeerCol = {
    key: string; label: string; suffix?: string; digits?: number;
    align?: "left" | "right";
  };
  const peerCols: PeerCol[] = [
    { key: "company_name",    label: "Company",       align: "left" },
    { key: "symbol",          label: "Symbol",        align: "left" },
    { key: "market_cap_b",    label: "Mkt Cap (₹B)",  suffix: "" },
    { key: "revenue_cagr_3y", label: "Rev CAGR",      suffix: "%" },
    { key: "ebitda_margin",   label: "EBITDA%",       suffix: "%" },
    { key: "roce",            label: "ROCE%",         suffix: "%" },
    { key: "roe",             label: "ROE%",          suffix: "%" },
    { key: "debt_to_equity",  label: "D/E",           suffix: "x" },
    { key: "fcf_to_pat",      label: "FCF/PAT",       suffix: "%" },
    { key: "pe_ratio",        label: "P/E",           suffix: "x" },
    { key: "pb_ratio",        label: "P/B",           suffix: "x" },
    { key: "peg_ratio",       label: "PEG",           suffix: "x" },
  ];

  // Build rows: subject first, then peers
  type RowData = Record<string, string | number | boolean | null | undefined>;

  const subjectRow: RowData = {
    _isSubject: true,
    company_name: subject?.company_name || "Subject",
    symbol: subject?.symbol || "",
    market_cap_b: subject?.market_cap ? +(subject.market_cap / 1e9).toFixed(1) : null,
    revenue_cagr_3y: metrics?.revenue_cagr_3y ?? null,
    ebitda_margin: metrics?.ebitda_margin ?? null,
    roce: metrics?.roce ?? null,
    roe: metrics?.roe ?? null,
    debt_to_equity: metrics?.debt_to_equity ?? null,
    fcf_to_pat: metrics?.fcf_to_pat ?? null,
    pe_ratio: metrics?.pe_ratio ?? null,
    pb_ratio: metrics?.pb_ratio ?? null,
    peg_ratio: metrics?.peg_ratio ?? null,
  };

  const peerRows: RowData[] = peers.map((p) => ({
    _isSubject: false,
    company_name: p.company_name,
    symbol: p.symbol,
    market_cap_b: p.market_cap ? +(p.market_cap / 1e9).toFixed(1) : null,
    revenue_cagr_3y: p.revenue_cagr_3y ?? null,
    ebitda_margin: p.ebitda_margin ?? null,
    roce: p.roce ?? null,
    roe: p.roe ?? null,
    debt_to_equity: p.debt_to_equity ?? null,
    fcf_to_pat: p.fcf_to_pat ?? null,
    pe_ratio: p.pe_ratio ?? null,
    pb_ratio: p.pb_ratio ?? null,
    peg_ratio: p.peg_ratio ?? null,
  }));

  // Sector median row
  const medians = peersData?.sector_medians;
  const medianRow: RowData | null = medians ? {
    _isMedian: true,
    company_name: "Peer Median",
    symbol: "—",
    market_cap_b: null,
    revenue_cagr_3y: medians.revenue_cagr_3y,
    ebitda_margin: medians.ebitda_margin,
    roce: medians.roce,
    roe: medians.roe,
    debt_to_equity: medians.debt_to_equity,
    fcf_to_pat: medians.fcf_to_pat,
    pe_ratio: medians.pe_ratio,
    pb_ratio: medians.pb_ratio,
    peg_ratio: medians.peg_ratio,
  } : null;

  const allRows: RowData[] = [subjectRow, ...(medianRow ? [medianRow] : []), ...peerRows];

  // ── Percentile view ────────────────────────────────────────────────────────
  const percentiles = peersData?.company_percentiles;
  const pctRows: { label: string; key: string; company: string; median: string; pct: number | null | undefined; suffix: string }[] = [
    { label: "Revenue CAGR (3Y)", key: "revenue_cagr_3y", suffix: "%" },
    { label: "EBITDA Margin",     key: "ebitda_margin",   suffix: "%" },
    { label: "ROCE",              key: "roce",            suffix: "%" },
    { label: "ROE",               key: "roe",             suffix: "%" },
    { label: "FCF / PAT",         key: "fcf_to_pat",      suffix: "%" },
    { label: "Debt / Equity",     key: "debt_to_equity",  suffix: "x" },
    { label: "Net Debt / EBITDA", key: "net_debt_to_ebitda", suffix: "x" },
    { label: "P/E",               key: "pe_ratio",        suffix: "x" },
    { label: "P/B",               key: "pb_ratio",        suffix: "x" },
    { label: "EV / EBITDA",       key: "ev_to_ebitda",    suffix: "x" },
    { label: "PEG",               key: "peg_ratio",       suffix: "x" },
  ].map((r) => ({
    ...r,
    company: fmt(metrics?.[r.key as keyof typeof metrics] as number | null | undefined, r.suffix),
    median: fmt(medians?.[r.key] as number | null | undefined, r.suffix),
    pct: percentiles?.[r.key] as number | null | undefined,
  }));

  const thBase: React.CSSProperties = {
    color: "var(--text-dim)", textAlign: "right", padding: "6px 12px",
    fontSize: 11, fontWeight: 600, textTransform: "uppercase",
    letterSpacing: "0.06em", background: "var(--bg-input)", whiteSpace: "nowrap",
  };

  return (
    <div className="space-y-4">
      {/* Peer positioning scatter */}
      <ChartCard eyebrow="Peer Positioning" title={`${subject?.company_name || "Subject"} vs ${peers.length} peers`}>
        <PeerScatterChart peers={peers} subject={subject ? {
          company_name: subject.company_name,
          market_cap: subject.market_cap,
          revenue_cagr_3y: metrics?.revenue_cagr_3y,
          roce: metrics?.roce,
          pe_ratio: metrics?.pe_ratio,
        } : null} />
      </ChartCard>

      {perfSeries.length >= 2 && (
        <ChartCard eyebrow="Price Performance" title="Relative Price Performance vs. Peers (1Y, rebased to 100)">
          <RebasedPerformanceChart series={perfSeries} />
        </ChartCard>
      )}

      {/* Sector-specific operating metrics — ALOS/ARPOB for hospitals, ARR/
          RevPAR for hotels, ARPU/churn for telecom, etc. Unlike the generic
          table below (same ~11 financial ratios for every sector), these
          columns are specific to this company's own sector framework. */}
      {sectorMetricRows.length > 0 && (
        <ChartCard
          eyebrow={`${peersData?.sector || "Sector"}-Specific Metrics`}
          title="Operating KPIs unique to this sector, compared across the named peer set"
        >
          {hasAnySectorMetricValue ? (
            <div className="overflow-x-auto">
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                    <th style={{ ...thBase, textAlign: "left" }}>Metric</th>
                    <th style={{ ...thBase, textAlign: "right", color: "#e8c766" }}>{subject?.company_name || "This company"}</th>
                    {peers.map((p) => (
                      <th key={p.stock_id || p.symbol} style={thBase}>{p.symbol}</th>
                    ))}
                    <th style={thBase}>Peer Median</th>
                  </tr>
                </thead>
                <tbody>
                  {sectorMetricRows.map((m) => {
                    const companyVal = peersData?.company_metrics?.[m.name] ?? null;
                    const medianVal = peersData?.sector_medians?.[m.name] ?? null;
                    return (
                      <tr key={m.name} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                        <td style={{ padding: "8px 12px", fontSize: 13, color: "var(--text-secondary)" }}>
                          {m.label || m.name}
                        </td>
                        <td style={{ padding: "8px 12px", fontSize: 13, textAlign: "right", fontWeight: 600, color: "#e8c766", fontVariantNumeric: "tabular-nums" }}>
                          {fmtSectorVal(companyVal as number | null, m.unit)}
                        </td>
                        {peers.map((p) => (
                          <td key={p.stock_id || p.symbol} style={{ padding: "8px 12px", fontSize: 13, textAlign: "right", color: "var(--text-secondary)", fontVariantNumeric: "tabular-nums" }}>
                            {fmtSectorVal(p.sector_metrics?.[m.name], m.unit)}
                          </td>
                        ))}
                        <td style={{ padding: "8px 12px", fontSize: 13, textAlign: "right", color: "var(--text-dim)", fontVariantNumeric: "tabular-nums" }}>
                          {fmtSectorVal(medianVal as number | null, m.unit)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              <p style={{ padding: "10px 12px 0", fontSize: 11, color: "var(--text-dim)" }}>
                A peer shows "—" when it hasn't itself been analyzed on this platform yet (or hasn't disclosed the
                figure) — never a guess. Analyze that peer directly to populate its own sector-specific metrics.
              </p>
            </div>
          ) : (
            <p style={{ padding: "0 12px 12px", fontSize: 12.5, color: "var(--text-dim)" }}>
              {sectorMetricRows.map((m) => m.label || m.name).join(", ")} — not yet available for this company or any
              of its named peers. These come from quarterly filings/investor presentations, not yfinance, so coverage
              depends on what's been ingested so far for each company.
            </p>
          )}
        </ChartCard>
      )}

      {/* Tab bar */}
      <div style={{ display: "flex", gap: 8 }}>
        {(["table", "percentile"] as const).map((t) => (
          <button key={t} onClick={() => setTab(t)}
            style={{
              padding: "5px 14px", borderRadius: 6, fontSize: 12, fontWeight: 600,
              border: "1px solid",
              borderColor: tab === t ? "var(--accent)" : "var(--border-subtle)",
              background: tab === t ? "rgba(201,162,39,0.12)" : "transparent",
              color: tab === t ? "var(--accent)" : "var(--text-secondary)",
              cursor: "pointer",
            }}>
            {t === "table" ? "Peer Table" : "Percentile Rank"}
          </button>
        ))}
        <span style={{ marginLeft: "auto", alignSelf: "center", fontSize: 11, color: "var(--text-dim)" }}>
          {peers.length} peers · {sectorLabel}
        </span>
      </div>

      {/* ── Peer Table ── */}
      {tab === "table" && (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                  {peerCols.map((c) => (
                    <th key={c.key} style={{
                      ...thBase,
                      textAlign: c.align === "left" ? "left" : "right",
                    }}>
                      {c.label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {allRows.map((row, i) => {
                  const isSubject = !!row._isSubject;
                  const isMedian = !!row._isMedian;
                  return (
                    <tr key={i} style={{
                      borderBottom: "1px solid var(--border-subtle)",
                      background: isSubject
                        ? "rgba(201,162,39,0.07)"
                        : isMedian
                        ? "rgba(232,199,102,0.05)"
                        : "transparent",
                    }}>
                      {peerCols.map((c) => {
                        const val = row[c.key];
                        const isLeft = c.align === "left";
                        if (c.key === "company_name") {
                          return (
                            <td key={c.key} style={{
                              padding: "8px 12px", fontSize: 13, fontWeight: 500,
                              color: isSubject ? "#e8c766" : isMedian ? "#e8c766" : "var(--text-primary)",
                              whiteSpace: "nowrap",
                            }}>
                              {isSubject && <span style={{ marginRight: 6, fontSize: 11 }}>★</span>}
                              {isMedian && <span style={{ marginRight: 6, fontSize: 10 }}>⊘</span>}
                              {String(val ?? "—")}
                            </td>
                          );
                        }
                        if (c.key === "symbol") {
                          return (
                            <td key={c.key} style={{
                              padding: "8px 12px", fontSize: 11, fontFamily: "monospace",
                              color: "var(--text-secondary)",
                            }}>
                              {String(val ?? "—")}
                            </td>
                          );
                        }
                        return (
                          <td key={c.key} style={{
                            padding: "8px 12px", fontSize: 13,
                            textAlign: isLeft ? "left" : "right",
                            color: "var(--text-secondary)",
                            fontVariantNumeric: "tabular-nums",
                          }}>
                            {val !== null && val !== undefined
                              ? `${(val as number).toFixed(c.digits ?? 1)}${c.suffix ?? ""}`
                              : "—"}
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── Percentile View ── */}
      {tab === "percentile" && (
        <div className="card overflow-hidden">
          <div style={{ padding: "10px 12px", borderBottom: "1px solid var(--border-subtle)" }}>
            <span style={{ fontSize: 11, color: "var(--text-dim)", fontWeight: 600,
                           textTransform: "uppercase", letterSpacing: "0.06em" }}>
              How {subject?.company_name || "Company"} ranks vs {peers.length} peers
            </span>
          </div>
          <div className="overflow-x-auto">
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                  {[
                    { label: "Metric", align: "left" as const },
                    { label: "Company", align: "right" as const },
                    { label: "Peer Median", align: "right" as const },
                    { label: "Percentile", align: "right" as const },
                  ].map((h) => (
                    <th key={h.label} style={{ ...thBase, textAlign: h.align }}>{h.label}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {pctRows.map((row) => (
                  <tr key={row.key} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                    <td style={{ padding: "8px 12px", fontSize: 13, color: "var(--text-secondary)" }}>
                      {row.label}
                    </td>
                    <td style={{ padding: "8px 12px", fontSize: 13, textAlign: "right",
                                  fontVariantNumeric: "tabular-nums", color: "#e8c766", fontWeight: 600 }}>
                      {row.company}
                    </td>
                    <td style={{ padding: "8px 12px", fontSize: 13, textAlign: "right",
                                  fontVariantNumeric: "tabular-nums", color: "var(--text-secondary)" }}>
                      {row.median}
                    </td>
                    <td style={{ padding: "8px 12px" }}>
                      <PercentileBar value={row.pct} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={{ padding: "8px 12px", fontSize: 11, color: "var(--text-dim)",
                         borderTop: "1px solid var(--border-subtle)" }}>
            Percentile = rank among peers (higher = better, except for leverage metrics)
          </div>
        </div>
      )}
    </div>
  );
}
