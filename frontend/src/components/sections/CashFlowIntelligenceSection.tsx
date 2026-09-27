import { useState, useEffect } from "react";
import { api } from "../../api";
import type { FullAnalysis, CashFlowIntelligence, CfRiskFlag, CfForensicPattern } from "../../types";
import ChartCard, { ChartEmptyState } from "../charts/ChartCard";
import StatementTypeToggle, { type StatementType } from "../StatementTypeToggle";

function fmt(v: number | null | undefined, suffix = "", d = 1) {
  if (v === null || v === undefined) return "—";
  return `${v.toFixed(d)}${suffix}`;
}

function fmtCr(v: number | null | undefined) {
  if (v === null || v === undefined) return "—";
  const sign = v < 0 ? "-" : "";
  return `${sign}₹${Math.abs(v).toLocaleString("en-IN", { maximumFractionDigits: 0 })} Cr`;
}

function readable(s: string | null | undefined): string {
  if (!s) return "—";
  return s.toLowerCase().split("_").map((w) => (w ? w[0].toUpperCase() + w.slice(1) : w)).join(" ");
}

function archetypeColor(classification: string): string {
  switch (classification) {
    case "CASH_COMPOUNDER": return "#4fb3a0";
    case "CASH_HARVEST": return "#4fb3a0";
    case "GROWTH_REINVESTMENT": return "#7fb8ff";
    case "ASSET_LIQUIDATION_SUPPORTED": return "#c9a227";
    case "WORKING_CAPITAL_TRAP": return "#e0793c";
    case "DEBT_FUNDED_BUSINESS": return "#d9694f";
    default: return "var(--text-dim)";
  }
}

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

// Waterfall-style bar list: Operating Profit -> +/- Working Capital lines
// -> - Taxes -> Computed CFO. Not a literal chart library waterfall (no
// running-total geometry needed for a handful of named steps) — a signed
// horizontal bar list conveys the same bridge story more legibly at this
// scale, same rationale as BalanceSheetHouse's proportional bars.
function CfoBridge({ bridge }: { bridge: CashFlowIntelligence["reconciliation"]["cfo_bridge"] }) {
  const steps: { label: string; value: number | null }[] = [
    { label: "Operating Profit", value: bridge.operating_profit },
    { label: "Receivables", value: bridge.receivables_change },
    { label: "Inventory", value: bridge.inventory_change },
    { label: "Payables", value: bridge.payables_change },
    { label: "Loans & Advances", value: bridge.loans_advances_change },
    { label: "Other WC Items", value: bridge.other_wc_change },
    { label: "Taxes Paid", value: bridge.taxes_paid },
  ];
  const maxAbs = Math.max(1, ...steps.map((s) => Math.abs(s.value ?? 0)));
  return (
    <div className="space-y-1.5">
      {steps.map((s) => (
        <div key={s.label}>
          <div className="flex justify-between text-xs mb-0.5">
            <span style={{ color: "var(--text-muted)" }}>{s.label}</span>
            <span style={{ color: (s.value ?? 0) < 0 ? "#d9694f" : "var(--text-secondary)" }}>{fmtCr(s.value)}</span>
          </div>
          <div className="h-2 rounded-full" style={{ background: "rgba(255,255,255,0.06)" }}>
            <div
              className="h-2 rounded-full"
              style={{
                width: `${(Math.abs(s.value ?? 0) / maxAbs) * 100}%`,
                background: (s.value ?? 0) < 0 ? "#d9694f" : "#4fb3a0",
              }}
            />
          </div>
        </div>
      ))}
      <div className="pt-2 mt-1 flex justify-between text-sm" style={{ borderTop: "1px solid rgba(255,255,255,0.08)" }}>
        <span style={{ color: "var(--text-secondary)" }}>Computed CFO</span>
        <span className="font-semibold" style={{ color: "var(--text-primary)" }}>{fmtCr(bridge.computed_cfo)}</span>
      </div>
    </div>
  );
}

function CoverageBar({ coverage }: { coverage: CashFlowIntelligence["coverage"] }) {
  const [expanded, setExpanded] = useState(false);
  const gaps = Object.entries(coverage.metrics).filter(([, m]) => m.status === "MISSING_INPUT" || m.status === "SOURCE_REQUIRED" || m.status === "PARTIAL");
  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-sm" style={{ color: "var(--text-secondary)" }}>{fmt(coverage.coverage_pct, "%", 0)} of tracked metrics available</span>
        <span className="text-xs" style={{ color: "var(--text-dim)" }}>{coverage.total_metrics} metrics tracked</span>
      </div>
      <div className="h-2 rounded-full mb-3" style={{ background: "rgba(255,255,255,0.06)" }}>
        <div className="h-2 rounded-full" style={{ width: `${coverage.coverage_pct}%`, background: "#4fb3a0" }} />
      </div>
      <button className="text-xs underline" style={{ color: "var(--text-dim)" }} onClick={() => setExpanded((e) => !e)}>
        {expanded ? "Hide" : "Show"} {gaps.length} data gap(s)
      </button>
      {expanded && (
        <ul className="mt-2 space-y-1.5">
          {gaps.map(([metric, m]) => (
            <li key={metric} className="text-xs" style={{ color: "var(--text-muted)" }}>
              <span style={{ color: "var(--text-secondary)" }}>{readable(metric)}</span> — {m.reason}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function RiskFlagRow({ flag }: { flag: CfRiskFlag }) {
  const isTriggered = flag.status === "TRIGGERED";
  const color = isTriggered ? (flag.severity === "RED" ? "#d9694f" : flag.severity === "AMBER" ? "#e0793c" : "#c9a227") : "var(--text-dim)";
  return (
    <li className="flex items-start gap-2 text-sm" style={{ color }}>
      <span className="w-1.5 h-1.5 rounded-full flex-shrink-0 mt-1.5" style={{ background: "currentColor" }} />
      <div>
        <span>{readable(flag.flag_id)}</span>
        {isTriggered && flag.evidence.length > 0 && (
          <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>{flag.evidence.join("; ")}</p>
        )}
      </div>
    </li>
  );
}

function ForensicPatternRow({ pattern }: { pattern: CfForensicPattern }) {
  const isActive = pattern.status === "TRIGGERED" || pattern.status === "OBSERVED";
  return (
    <li className="flex items-start gap-2 text-sm" style={{ color: isActive ? "#c9a227" : "var(--text-dim)" }}>
      <span className="w-1.5 h-1.5 rounded-full flex-shrink-0 mt-1.5" style={{ background: "currentColor" }} />
      <div>
        <span>{readable(pattern.pattern_id)}</span>
        {pattern.status === "OBSERVED" && <span className="text-xs ml-1.5">(observation, not a risk flag)</span>}
        {isActive && pattern.evidence.length > 0 && (
          <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>{pattern.evidence.join("; ")}</p>
        )}
      </div>
    </li>
  );
}

export default function CashFlowIntelligenceSection({ analysis }: { analysis: FullAnalysis }) {
  const companyId = analysis.company_info?.stock_id || analysis.stock_id;
  // `null` = "auto" — let the backend pick whichever statement_type
  // actually has data (preferring CONSOLIDATED), matching
  // compute_cash_flow_intelligence()'s own no-argument default. Only set
  // to an explicit value once the user clicks a toggle button — forcing
  // "CONSOLIDATED" on every initial load (the previous behavior) silently
  // disabled the backend's own STANDALONE fallback for any company whose
  // schedule data only exists under STANDALONE (real bug found live on
  // Coforge: CONSOLIDATED had top-level cf_* totals but zero cf_sched_*
  // rows, so forcing CONSOLIDATED produced an almost-entirely-blank tab
  // despite STANDALONE having complete data).
  const [statementType, setStatementType] = useState<StatementType | null>(null);
  const [cfi, setCfi] = useState<CashFlowIntelligence | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    setStatementType(null);
  }, [companyId]);

  useEffect(() => {
    if (!companyId) return;
    setLoading(true);
    api.getCashFlowIntelligence(companyId, statementType ?? undefined)
      .then((r) => { setCfi(r); setError(false); })
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [companyId, statementType]);

  const displayedType: StatementType = statementType ?? (cfi?.statement_type as StatementType | undefined) ?? "CONSOLIDATED";
  // No real Standalone-vs-Consolidated choice to offer when the company
  // only has data under one of the two on Screener.in — see types.ts.
  const toggle = cfi?.single_statement_source
    ? null
    : <StatementTypeToggle value={displayedType} onChange={setStatementType} />;

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="flex justify-end">{toggle}</div>
        <div className="text-sm p-6" style={{ color: "var(--text-dim)" }}>Loading Cash Flow Intelligence…</div>
      </div>
    );
  }
  if (error || !cfi) {
    return (
      <div className="space-y-4">
        <div className="flex justify-end">{toggle}</div>
        <div className="text-sm p-6" style={{ color: "var(--text-dim)" }}>Cash Flow Intelligence is unavailable for this company right now.</div>
      </div>
    );
  }
  if (!cfi.period) {
    return (
      <div className="space-y-4">
        <div className="flex justify-end">{toggle}</div>
        <div className="card-rich p-6 text-sm" style={{ color: "var(--text-dim)" }}>
          No {displayedType === "CONSOLIDATED" ? "consolidated" : "standalone"} Screener cash-flow schedule data
          available for this company — try the other statement type, or re-run the analysis to ingest it.
        </div>
      </div>
    );
  }

  const triggeredFlags = cfi.risk_flags.filter((f) => f.status === "TRIGGERED");
  const otherFlags = cfi.risk_flags.filter((f) => f.status !== "TRIGGERED");
  const activePatterns = cfi.forensic_patterns.filter((p) => p.status === "TRIGGERED" || p.status === "OBSERVED");
  const inactivePatterns = cfi.forensic_patterns.filter((p) => p.status !== "TRIGGERED" && p.status !== "OBSERVED");
  const cb = cfi.reconciliation.cash_bridge;
  const bridgeCheck = cfi.reconciliation.cfo_bridge_check;

  return (
    <div className="space-y-6">
      <div className="flex justify-end">{toggle}</div>

      {/* 1. Archetype tile */}
      <div className="card-rich p-5">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <p className="eyebrow">Cash Flow Archetype</p>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-3xl font-bold" style={{ color: archetypeColor(cfi.archetype.classification), fontFamily: "var(--font-display)" }}>
                {readable(cfi.archetype.classification)}
              </span>
            </div>
            {cfi.archetype.evidence.length > 0 && (
              <ul className="text-sm mt-2 space-y-0.5" style={{ color: "var(--text-muted)" }}>
                {cfi.archetype.evidence.map((e, i) => <li key={i}>• {e}</li>)}
              </ul>
            )}
            <p className="text-xs mt-2" style={{ color: "var(--text-dim)" }}>Analytical classification, not an investment rating.</p>
          </div>
          <span className="text-xs text-right" style={{ color: "var(--text-dim)" }}>
            {cfi.period} · {cfi.statement_type}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 2. CFO reconciliation bridge */}
        <ChartCard eyebrow="CFO Reconciliation" title="Operating Profit → Cash from Operations">
          <CfoBridge bridge={cfi.reconciliation.cfo_bridge} />
          {bridgeCheck.status === "DIVERGENT" && (
            <p className="text-xs mt-3" style={{ color: "#e0793c" }}>
              Bridge diverges from reported CFO by {fmt(bridgeCheck.difference_pct, "%")} — likely an exceptional/one-off item outside the standard schedule shape.
            </p>
          )}
        </ChartCard>

        {/* 3. Conversion */}
        <ChartCard eyebrow="Cash Conversion" title={`${cfi.period} · ${cfi.statement_type}`}>
          <div className="grid grid-cols-2 gap-4">
            <StatBlock label="CFO / Operating Profit" value={fmt(cfi.conversion.latest.ratio_pct, "%")} sub={cfi.conversion.latest.band} />
            <StatBlock label="Prior Period" value={fmt(cfi.conversion.prior_ratio_pct, "%")} />
            <StatBlock label="Trend" value={readable(cfi.conversion.trend)} />
            <StatBlock label="3Y Cumulative" value={fmt(cfi.conversion.cumulative_3y?.cumulative_cfo_to_operating_profit_pct, "%")} />
          </div>
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 4. Investing & Financing */}
        <ChartCard eyebrow="Investing Activity" title="Where cash was deployed/received">
          <div className="grid grid-cols-2 gap-4">
            <StatBlock label="Capex" value={fmtCr(cfi.investing.breakdown.fixed_assets_purchased)} />
            <StatBlock label="Asset Sales" value={fmtCr(cfi.investing.breakdown.fixed_assets_sold)} />
            <StatBlock label="Investments (net)" value={fmtCr((cfi.investing.breakdown.investments_purchased ?? 0) + (cfi.investing.breakdown.investments_sold ?? 0))} />
            <StatBlock label="Interest Received" value={fmtCr(cfi.investing.breakdown.interest_received)} />
          </div>
          {cfi.investing.asset_sale_dependency.triggered && (
            <p className="text-xs mt-3" style={{ color: "#c9a227" }}>Investing cash flow relies materially on asset/investment sales this period.</p>
          )}
        </ChartCard>

        <ChartCard eyebrow="Financing Activity" title="Debt, dividends & buybacks">
          <div className="grid grid-cols-2 gap-4">
            <StatBlock label="Borrowings Raised" value={fmtCr(cfi.financing.breakdown.borrowings_raised)} />
            <StatBlock label="Borrowings Repaid" value={fmtCr(cfi.financing.breakdown.borrowings_repaid)} />
            <StatBlock label="Debt Direction" value={readable(cfi.financing.debt_financing.classification)} />
            <StatBlock label="Dividends Paid" value={fmtCr(cfi.financing.dividend_analysis.dividends_paid)} sub={cfi.financing.dividend_analysis.dividend_to_cfo_pct != null ? `${fmt(cfi.financing.dividend_analysis.dividend_to_cfo_pct, "%")} of CFO` : undefined} />
          </div>
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 5. Free Cash Flow & Cash Bridge */}
        <ChartCard eyebrow="Free Cash Flow" title={readable(cfi.free_cash_flow.quality.classification)}>
          <div className="grid grid-cols-2 gap-4">
            <StatBlock label="Reported FCF" value={fmtCr(cfi.free_cash_flow.reconciliation.reported_fcf)} />
            <StatBlock label="CFO − Capex" value={fmtCr(cfi.free_cash_flow.reconciliation.computed_fcf)} />
          </div>
          {cfi.free_cash_flow.reconciliation.divergent && (
            <p className="text-xs mt-3" style={{ color: "#e0793c" }}>Reported and computed FCF diverge by {fmt(cfi.free_cash_flow.reconciliation.divergence_pct, "%")}.</p>
          )}
        </ChartCard>

        <ChartCard eyebrow="Cash Bridge" title="Opening + CFO + CFI + CFF = Closing">
          {cb.status === "MISSING_DATA" ? (
            <ChartEmptyState message="Opening/closing cash balance not available for this period" />
          ) : (
            <>
              <div className="grid grid-cols-2 gap-4">
                <StatBlock label="Opening Cash" value={fmtCr(cb.opening_cash)} />
                <StatBlock label="Closing Cash" value={fmtCr(cb.closing_cash)} />
                <StatBlock label="Net Cash Flow" value={fmtCr((cb.cfo ?? 0) + (cb.cfi ?? 0) + (cb.cff ?? 0))} />
                <StatBlock label="Other Adjustment" value={fmtCr(cb.other_adjustment)} />
              </div>
              {cb.status === "CASH_FLOW_RECONCILIATION_ERROR" && (
                <p className="text-xs mt-3" style={{ color: "#d9694f" }}>Cash bridge residual is beyond rounding-noise tolerance — a line may be missing or misclassified.</p>
              )}
            </>
          )}
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 6. Risk flags & forensic patterns */}
        <ChartCard eyebrow="Risk Flags" title={`${triggeredFlags.length} triggered`}>
          {cfi.risk_flags.length ? (
            <ul className="space-y-2.5">
              {[...triggeredFlags, ...otherFlags].map((f) => <RiskFlagRow key={f.flag_id} flag={f} />)}
            </ul>
          ) : <ChartEmptyState message="No flags evaluated" />}
        </ChartCard>

        <ChartCard eyebrow="Forensic Patterns" title={`${activePatterns.length} active`}>
          {cfi.forensic_patterns.length ? (
            <ul className="space-y-2.5">
              {[...activePatterns, ...inactivePatterns].map((p) => <ForensicPatternRow key={p.pattern_id} pattern={p} />)}
            </ul>
          ) : <ChartEmptyState message="No patterns evaluated" />}
        </ChartCard>
      </div>

      {/* 7. Data coverage */}
      <ChartCard eyebrow="Data Coverage" title="What analysis is possible from the data available">
        <CoverageBar coverage={cfi.coverage} />
      </ChartCard>
    </div>
  );
}
