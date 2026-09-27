import { useState, useEffect } from "react";
import { api } from "../../api";
import type { FullAnalysis, PlIntelligence, PlDoublingResult } from "../../types";
import ChartCard, { ChartEmptyState } from "../charts/ChartCard";
import WaterfallChart from "../charts/WaterfallChart";
import DonutChart from "../charts/DonutChart";
import PercentileBar from "../charts/PercentileBar";
import StatementTypeToggle, { type StatementType } from "../StatementTypeToggle";

function fmt(v: number | null | undefined, suffix = "", d = 1) {
  if (v === null || v === undefined) return "—";
  return `${v.toFixed(d)}${suffix}`;
}

function fmtCr(v: number | null | undefined) {
  if (v === null || v === undefined) return "—";
  return `₹${v.toLocaleString("en-IN", { maximumFractionDigits: 0 })} Cr`;
}

// "PREMIUM_QUALITY_GROWTH_EFFICIENCY_LEADER" -> "Premium Quality Growth Efficiency Leader"
function readable(s: string | null | undefined): string {
  if (!s) return "—";
  return s.toLowerCase().split("_").map((w) => w[0].toUpperCase() + w.slice(1)).join(" ");
}

function scoreColor(score: number | null): string {
  if (score === null) return "var(--text-dim)";
  if (score >= 75) return "#4fb3a0";
  if (score >= 55) return "#c9a227";
  if (score >= 40) return "#e0793c";
  return "#d9694f";
}

const FLAG_LABELS: Record<string, string> = {
  profit_conversion_weak: "Profit Conversion Weak",
  margin_compression: "Margin Compression",
  margin_expansion_candidate: "Margin Expansion Candidate",
  near_sector_peak: "Near Sector Peak",
  non_core_income_dependency: "Non-Core Income Dependency",
  high_subsidiary_global_reliance: "High Subsidiary/Global Reliance",
  interest_burden: "Interest Burden",
  operating_overhead_pressure: "Operating Overhead Pressure",
};
const POSITIVE_FLAGS = new Set(["margin_expansion_candidate", "near_sector_peak"]);

function StatBlock({ label, value, sub }: { label: string; value: string; sub?: string | null }) {
  return (
    <div>
      <p className="text-xs" style={{ color: "var(--text-dim)" }}>{label}</p>
      <p className="text-lg font-semibold mt-0.5" style={{ color: "var(--text-primary)", fontFamily: "var(--font-display)" }}>
        {value}
      </p>
      {sub && <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>{sub}</p>}
    </div>
  );
}

function PlScoreTile({ label, value, color }: { label: string; value: number | null; color: string }) {
  return (
    <div className="rounded-xl p-3 text-center" style={{ background: `${color}12`, border: `1px solid ${color}30` }}>
      <div className="text-[10px] uppercase tracking-widest mb-1" style={{ color: "var(--text-dim)" }}>{label}</div>
      <div className="text-xl font-bold" style={{ color: value !== null ? color : "var(--text-dim)" }}>
        {value !== null ? value.toFixed(0) : "—"}
      </div>
    </div>
  );
}

function doublingLabel(d: PlDoublingResult): string {
  if (d.doubling_years === null) return "Not doubling";
  if (d.method === "EMPIRICAL" && d.start_year && d.end_year) {
    return `${d.doubling_years.toFixed(0)}y (FY${d.start_year}→FY${d.end_year})`;
  }
  const method = d.method === "CAGR_THEORETICAL" ? " (est. from historical CAGR)" : "";
  return `${d.doubling_years.toFixed(1)}y${method}`;
}

function velocityInterpretation(v: PlIntelligence["doubling"]["velocity_comparison"]): string {
  switch (v) {
    case "PAT_FASTER":
      return "PAT is compounding faster than revenue — suggests margin expansion / operating leverage.";
    case "PAT_SLOWER":
      return "PAT is compounding slower than revenue — suggests margin compression or cost pressure.";
    case "ROUGHLY_SAME":
      return "PAT and revenue are doubling at a similar pace — stable economics.";
    default:
      return "Insufficient data to compare revenue and PAT growth velocity.";
  }
}

export default function PlIntelligenceSection({ analysis }: { analysis: FullAnalysis }) {
  const companyId = analysis.company_info?.stock_id || analysis.stock_id;
  // `null` = "auto" — see CashFlowIntelligenceSection.tsx's identical
  // pattern for why forcing "CONSOLIDATED" on every initial load is wrong
  // (it silently disables `compute_pl_intelligence()`'s own STANDALONE
  // fallback for a company whose pnl_* ledger data is STANDALONE-only).
  const [statementType, setStatementType] = useState<StatementType | null>(null);
  const [pli, setPli] = useState<PlIntelligence | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    setStatementType(null);
  }, [companyId]);

  useEffect(() => {
    if (!companyId) return;
    setLoading(true);
    api.getPlIntelligence(companyId, statementType ?? undefined)
      .then((r) => { setPli(r); setError(false); })
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [companyId, statementType]);

  const displayedType: StatementType = statementType ?? (pli?.statement_type as StatementType | undefined) ?? "CONSOLIDATED";
  // No real Standalone-vs-Consolidated choice to offer when the company
  // only has data under one of the two on Screener.in — see types.ts.
  const toggle = pli?.single_statement_source
    ? null
    : <StatementTypeToggle value={displayedType} onChange={setStatementType} />;

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="flex justify-end">{toggle}</div>
        <div className="text-sm p-6" style={{ color: "var(--text-dim)" }}>Loading P&L Intelligence…</div>
      </div>
    );
  }
  if (error || !pli) {
    return (
      <div className="space-y-4">
        <div className="flex justify-end">{toggle}</div>
        <div className="text-sm p-6" style={{ color: "var(--text-dim)" }}>P&L Intelligence is unavailable for this company right now.</div>
      </div>
    );
  }
  if (!pli.period) {
    return (
      <div className="space-y-4">
        <div className="flex justify-end">{toggle}</div>
        <div className="card-rich p-6 text-sm" style={{ color: "var(--text-dim)" }}>
          No {displayedType === "CONSOLIDATED" ? "consolidated" : "standalone"} P&L ledger data available for this
          company — try the other statement type, or re-run the analysis to ingest it.
        </div>
      </div>
    );
  }

  const latest = pli.cascade[pli.period];
  const score = pli.score;
  const cascadeSteps = latest
    ? [
        { label: "Revenue", value: latest.revenue },
        { label: "EBITDA", value: latest.ebitda },
        { label: "EBIT", value: latest.ebit },
        { label: "PBT", value: latest.pbt },
        { label: "PAT", value: latest.pat },
      ].filter((s): s is { label: string; value: number } => s.value !== null)
    : [];

  return (
    <div className="space-y-6">
      <div className="flex justify-end">{toggle}</div>

      {/* 1. Score card */}
      <div className="card-rich p-5">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <p className="eyebrow">P&L Master Score</p>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-4xl font-bold" style={{ color: scoreColor(score.master_pl_score), fontFamily: "var(--font-display)" }}>
                {score.master_pl_score !== null ? score.master_pl_score.toFixed(0) : "—"}
              </span>
              <span className="text-lg" style={{ color: "var(--text-dim)" }}>/100</span>
            </div>
            <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>{readable(score.classification)}</p>
          </div>
          <span className="text-xs text-right" style={{ color: "var(--text-dim)" }}>
            Algorithm {score.algorithm_version}<br />{pli.period} · {pli.statement_type}
          </span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mt-5">
          <PlScoreTile label="M1 · Sector Margin" value={score.components.M1} color="#c9a227" />
          <PlScoreTile label="M2 · Margin Headroom" value={score.components.M2} color="#4fb3a0" />
          <PlScoreTile label="M3 · Doubling Velocity" value={score.components.M3} color="#e0793c" />
          <PlScoreTile label="M4 · Earnings Quality" value={score.components.M4} color="#e8c766" />
          <PlScoreTile label="M5 · Structural Ratio" value={score.components.M5} color="#7fb8ff" />
        </div>
      </div>

      {/* 2. Income cascade */}
      <ChartCard eyebrow="Income Cascade" title={`${pli.period} · ${pli.statement_type}`}>
        {cascadeSteps.length ? <WaterfallChart steps={cascadeSteps} formatter={fmtCr} /> : <ChartEmptyState />}
        <p className="text-xs mt-2" style={{ color: "var(--text-dim)" }}>
          Gross Profit isn't shown — Screener.in's P&L view has no material-cost/COGS breakdown for any sector, so
          it's never estimated.
        </p>
      </ChartCard>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 3. Margin trend & stability */}
        <ChartCard eyebrow="Margin Quality" title="Margin trend & stability">
          <div className="grid grid-cols-2 gap-4">
            <StatBlock label="EBITDA Margin" value={fmt(pli.margins.ebitda_margin, "%")} sub={readable(pli.margins.ebitda_margin_direction)} />
            <StatBlock label="PAT Margin" value={fmt(pli.margins.pat_margin, "%")} sub={readable(pli.margins.margin_direction)} />
            <StatBlock label="5Y Avg PAT Margin" value={fmt(pli.margins.stability.avg_5y, "%")} />
            <StatBlock label="Stability" value={readable(pli.margins.stability.classification)} />
          </div>
        </ChartCard>

        {/* 4. Peer benchmark */}
        <ChartCard eyebrow="Peer Benchmark" title={`${pli.peer_percentiles.peer_count} sector/industry peers`}>
          {(() => {
            const fpp = pli.fintech_peer_percentiles;
            const hasMargins = pli.peer_percentiles.peer_count > 0 && pli.peer_percentiles.pat_margin.percentile !== null;
            const hasFintech = !!fpp && (fpp.gtv_growth.percentile !== null || fpp.take_rate.percentile !== null);
            if (!hasMargins && !hasFintech) {
              return <ChartEmptyState message="No peer comparison available yet — peers haven't been re-ingested under the new P&L engine" />;
            }
            const yahooPeers = Object.values(pli.peer_percentiles.peer_source ?? {}).includes("YAHOO_PEER_TAB");
            return (
              <>
              <table className="w-full text-sm">
                <tbody>
                  {hasMargins && (
                    <>
                      <tr>
                        <td className="py-2" style={{ color: "var(--text-muted)" }}>PAT Margin</td>
                        <td className="py-2 text-right tabular-nums">{fmt(pli.peer_percentiles.pat_margin.company_value, "%")}</td>
                        <td className="py-2 pl-4"><PercentileBar value={pli.peer_percentiles.pat_margin.percentile} /></td>
                      </tr>
                      <tr>
                        <td className="py-2" style={{ color: "var(--text-muted)" }}>EBITDA Margin</td>
                        <td className="py-2 text-right tabular-nums">{fmt(pli.peer_percentiles.ebitda_margin.company_value, "%")}</td>
                        <td className="py-2 pl-4"><PercentileBar value={pli.peer_percentiles.ebitda_margin.percentile} /></td>
                      </tr>
                    </>
                  )}
                  {fpp?.gtv_growth.percentile !== null && fpp && (
                    <tr>
                      <td className="py-2" style={{ color: "var(--text-muted)" }}>GTV/TPV Growth</td>
                      <td className="py-2 text-right tabular-nums">{fmt(fpp.gtv_growth.company_value, "%")}</td>
                      <td className="py-2 pl-4"><PercentileBar value={fpp.gtv_growth.percentile} /></td>
                    </tr>
                  )}
                  {fpp?.take_rate.percentile !== null && fpp && (
                    <tr>
                      <td className="py-2" style={{ color: "var(--text-muted)" }}>Take Rate</td>
                      <td className="py-2 text-right tabular-nums">{fmt(fpp.take_rate.company_value, "bps")}</td>
                      <td className="py-2 pl-4"><PercentileBar value={fpp.take_rate.percentile} /></td>
                    </tr>
                  )}
                </tbody>
              </table>
              {yahooPeers && (
                <p className="text-[11px] mt-3" style={{ color: "var(--text-dim)" }}>
                  Peer margins from Yahoo Finance (same figures as the Peers tab) — these peers haven't been
                  analysed in full yet, so their P&L history isn't in the ledger.
                </p>
              )}
              </>
            );
          })()}
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 5/6. Doubling velocity */}
        <ChartCard eyebrow="Growth Velocity" title="Revenue & PAT doubling">
          <div className="grid grid-cols-2 gap-4">
            <StatBlock label="Revenue Doubling" value={doublingLabel(pli.doubling.revenue)} sub={readable(pli.doubling.revenue.speed)} />
            <StatBlock label="PAT Doubling" value={doublingLabel(pli.doubling.pat)} sub={readable(pli.doubling.pat.speed)} />
          </div>
          <p className="text-xs mt-3" style={{ color: "var(--text-muted)" }}>{velocityInterpretation(pli.doubling.velocity_comparison)}</p>
        </ChartCard>

        {/* 7. Standalone vs Consolidated */}
        <ChartCard eyebrow="Structure" title="Standalone vs Consolidated">
          <div className="grid grid-cols-2 gap-4">
            <StatBlock label="Standalone Revenue" value={fmtCr(pli.structure.standalone_revenue)} />
            <StatBlock label="Consolidated Revenue" value={fmtCr(pli.structure.consolidated_revenue)} />
            <StatBlock label="CSR" value={pli.structure.csr !== null ? pli.structure.csr.toFixed(2) : "—"} sub={readable(pli.structure.csr_band)} />
            <StatBlock label="Structure" value={pli.structure.sotp_required ? "SOTP required" : "Single business"}
                       sub={pli.structure.segment_count > 0 ? `${pli.structure.segment_count} material segment(s)` : undefined} />
          </div>
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 8. Earnings quality */}
        <ChartCard eyebrow="Earnings Quality" title={pli.earnings_quality.eqi !== null ? `EQI ${(pli.earnings_quality.eqi * 100).toFixed(0)}%` : "EQI"}>
          {pli.earnings_quality.eqi !== null ? (
            <DonutChart
              data={[
                { name: "Core operating income", value: pli.earnings_quality.eqi, color: "#4fb3a0" },
                { name: "Non-core / other income", value: 1 - pli.earnings_quality.eqi, color: "#d9694f" },
              ]}
              formatter={(v) => `${(v * 100).toFixed(0)}%`}
            />
          ) : <ChartEmptyState />}
          <p className="text-xs mt-2" style={{ color: "var(--text-dim)" }}>{readable(pli.earnings_quality.classification)}</p>
        </ChartCard>

        {/* 9. Red flags */}
        <ChartCard eyebrow="Diagnostics" title="Flags & signals">
          {pli.diagnostic_flags.length ? (
            <ul className="space-y-2.5">
              {pli.diagnostic_flags.map((f) => (
                <li key={f} className="flex items-center gap-2 text-sm" style={{ color: POSITIVE_FLAGS.has(f) ? "#4fb3a0" : "#e0793c" }}>
                  <span className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ background: "currentColor" }} />
                  {FLAG_LABELS[f] || readable(f)}
                </li>
              ))}
            </ul>
          ) : <ChartEmptyState message="No flags raised" />}
        </ChartCard>
      </div>
    </div>
  );
}
