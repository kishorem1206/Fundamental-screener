import { useState, useEffect } from "react";
import { api } from "../../api";
import type { FullAnalysis, BalanceSheetIntelligence, BsRiskFlag } from "../../types";
import ChartCard, { ChartEmptyState } from "../charts/ChartCard";
import StatementTypeToggle, { type StatementType } from "../StatementTypeToggle";

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
  return s.toLowerCase().split("_").map((w) => (w ? w[0].toUpperCase() + w.slice(1) : w)).join(" ");
}

function archetypeColor(classification: string): string {
  switch (classification) {
    case "STRONG": return "#4fb3a0";
    case "TRANSFORMING": return "#c9a227";
    case "MIDDLE": return "#7fb8ff";
    case "WEAK": return "#d9694f";
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

// Two columns of proportional-width horizontal bars — Sources left,
// Applications right, both scaled to the same total (equal by
// construction). Not a literal house illustration (pure decoration, no
// extra information density) — a proportional bar list conveys the same
// funding-vs-deployment story more legibly.
function BalanceSheetHouse({ house }: { house: BalanceSheetIntelligence["house"] }) {
  const total = Math.max(house.sources_total, house.applications_total, 1);
  const palette = ["#c9a227", "#e0793c", "#4fb3a0", "#7fb8ff", "#d9694f", "#a9b3c9"];
  return (
    <div className="grid grid-cols-2 gap-6">
      <div>
        <p className="text-xs uppercase tracking-widest mb-2" style={{ color: "var(--text-dim)" }}>Sources</p>
        <div className="space-y-1.5">
          {house.sources.map((s, i) => (
            <div key={s.label} title={s.note}>
              <div className="flex justify-between text-xs mb-0.5">
                <span style={{ color: "var(--text-muted)" }}>{s.label}</span>
                <span style={{ color: "var(--text-secondary)" }}>{fmtCr(s.value)}</span>
              </div>
              <div className="h-2 rounded-full" style={{ background: "rgba(255,255,255,0.06)" }}>
                <div className="h-2 rounded-full" style={{ width: `${(s.value / total) * 100}%`, background: palette[i % palette.length] }} />
              </div>
            </div>
          ))}
        </div>
      </div>
      <div>
        <p className="text-xs uppercase tracking-widest mb-2" style={{ color: "var(--text-dim)" }}>Applications</p>
        <div className="space-y-1.5">
          {house.applications.map((a, i) => (
            <div key={a.label}>
              <div className="flex justify-between text-xs mb-0.5">
                <span style={{ color: "var(--text-muted)" }}>{a.label}{a.source === "YFINANCE" ? "*" : ""}</span>
                <span style={{ color: "var(--text-secondary)" }}>{fmtCr(a.value)}</span>
              </div>
              <div className="h-2 rounded-full" style={{ background: "rgba(255,255,255,0.06)" }}>
                <div className="h-2 rounded-full" style={{ width: `${(a.value / total) * 100}%`, background: palette[i % palette.length] }} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function CoverageBar({ coverage }: { coverage: BalanceSheetIntelligence["coverage"] }) {
  const [expanded, setExpanded] = useState(false);
  const gaps = Object.entries(coverage.metrics).filter(([, m]) => m.status === "MISSING_INPUT" || m.status === "SOURCE_REQUIRED");
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

function RiskFlagRow({ flag }: { flag: BsRiskFlag }) {
  const isTriggered = flag.status === "TRIGGERED";
  const isSourceRequired = flag.status === "SOURCE_REQUIRED";
  const color = isTriggered ? (flag.severity === "RED" ? "#d9694f" : "#e0793c") : "var(--text-dim)";
  return (
    <li className="flex items-start gap-2 text-sm" style={{ color, opacity: isSourceRequired ? 0.55 : 1 }}>
      <span className="w-1.5 h-1.5 rounded-full flex-shrink-0 mt-1.5" style={{ background: "currentColor" }} />
      <div>
        <span>{readable(flag.flag_id)}</span>
        {isSourceRequired && <span className="text-xs ml-1.5">(not available — {flag.evidence[0]})</span>}
        {isTriggered && flag.evidence.length > 0 && (
          <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>{flag.evidence.join("; ")}</p>
        )}
      </div>
    </li>
  );
}

export default function BalanceSheetIntelligenceSection({ analysis }: { analysis: FullAnalysis }) {
  const companyId = analysis.company_info?.stock_id || analysis.stock_id;
  // `null` = "auto" — see CashFlowIntelligenceSection.tsx's identical
  // pattern for why forcing "CONSOLIDATED" on every initial load is wrong
  // (it silently disables the backend's own STANDALONE fallback).
  const [statementType, setStatementType] = useState<StatementType | null>(null);
  const [bsi, setBsi] = useState<BalanceSheetIntelligence | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    setStatementType(null);
  }, [companyId]);

  useEffect(() => {
    if (!companyId) return;
    setLoading(true);
    api.getBalanceSheetIntelligence(companyId, statementType ?? undefined)
      .then((r) => { setBsi(r); setError(false); })
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [companyId, statementType]);

  const displayedType: StatementType = statementType ?? (bsi?.statement_type as StatementType | undefined) ?? "CONSOLIDATED";
  // No real Standalone-vs-Consolidated choice to offer when the company
  // only has data under one of the two on Screener.in — see types.ts.
  const toggle = bsi?.single_statement_source
    ? null
    : <StatementTypeToggle value={displayedType} onChange={setStatementType} />;

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="flex justify-end">{toggle}</div>
        <div className="text-sm p-6" style={{ color: "var(--text-dim)" }}>Loading Balance Sheet Intelligence…</div>
      </div>
    );
  }
  if (error || !bsi) {
    return (
      <div className="space-y-4">
        <div className="flex justify-end">{toggle}</div>
        <div className="text-sm p-6" style={{ color: "var(--text-dim)" }}>Balance Sheet Intelligence is unavailable for this company right now.</div>
      </div>
    );
  }
  if (!bsi.period) {
    return (
      <div className="space-y-4">
        <div className="flex justify-end">{toggle}</div>
        <div className="card-rich p-6 text-sm" style={{ color: "var(--text-dim)" }}>
          No {displayedType === "CONSOLIDATED" ? "consolidated" : "standalone"} Screener balance-sheet data
          available for this company — try the other statement type, or re-run the analysis to ingest it.
        </div>
      </div>
    );
  }
  if (bsi.balance_sheet_integrity.status === "BALANCE_SHEET_INTEGRITY_ERROR") {
    return (
      <div className="space-y-4">
        <div className="flex justify-end">{toggle}</div>
        <div className="card-rich p-6 text-sm" style={{ color: "#d9694f" }}>
          This company's balance sheet failed the accounting-identity check for {bsi.period}
          (Total Assets {fmtCr(bsi.balance_sheet_integrity.total_assets)} vs. Total Liabilities + Equity{" "}
          {fmtCr(bsi.balance_sheet_integrity.total_liabilities_equity)}) — analysis is withheld for this period
          rather than shown on unreliable data.
        </div>
      </div>
    );
  }

  const dm = bsi.derived_metrics;
  const isBank = bsi.archetype.classification === "NOT_APPLICABLE";
  const triggeredFlags = bsi.risk_flags.filter((f) => f.status === "TRIGGERED");
  const otherFlags = bsi.risk_flags.filter((f) => f.status !== "TRIGGERED");

  return (
    <div className="space-y-6">
      <div className="flex justify-end">{toggle}</div>

      {/* 1. Archetype tile */}
      <div className="card-rich p-5">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <p className="eyebrow">Balance Sheet Archetype</p>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-3xl font-bold" style={{ color: archetypeColor(bsi.archetype.classification), fontFamily: "var(--font-display)" }}>
                {readable(bsi.archetype.classification)}
              </span>
            </div>
            {bsi.archetype.evidence.length > 0 && (
              <ul className="text-sm mt-2 space-y-0.5" style={{ color: "var(--text-muted)" }}>
                {bsi.archetype.evidence.map((e, i) => <li key={i}>• {e}</li>)}
              </ul>
            )}
          </div>
          <span className="text-xs text-right" style={{ color: "var(--text-dim)" }}>
            {bsi.period} · {bsi.statement_type}
          </span>
        </div>
      </div>

      {isBank && bsi.financial_institution_summary && (
        <ChartCard eyebrow="Financial Institution" title="Balance sheet summary">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <StatBlock label="Deposits" value={fmtCr(bsi.financial_institution_summary.deposits)} />
            <StatBlock label="Borrowings" value={fmtCr(bsi.financial_institution_summary.borrowings)} />
            <StatBlock label="Investments" value={fmtCr(bsi.financial_institution_summary.investments)} />
            <StatBlock label="Total Assets" value={fmtCr(bsi.financial_institution_summary.total_assets)} />
          </div>
          <p className="text-xs mt-3" style={{ color: "var(--text-dim)" }}>{bsi.financial_institution_summary.note}</p>
        </ChartCard>
      )}

      {/* 2. Balance Sheet House */}
      <ChartCard eyebrow="Sources vs. Applications of Funds" title="Balance Sheet House">
        <BalanceSheetHouse house={bsi.house} />
        {bsi.house.cash_source === "YFINANCE_CASH" || bsi.house.applications.some((a) => a.source === "YFINANCE") ? (
          <p className="text-xs mt-3" style={{ color: "var(--text-dim)" }}>* Cash sourced from a different provider than the rest of this table (Screener.in has no separate cash line).</p>
        ) : null}
      </ChartCard>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 3. Leverage & ROCE */}
        <ChartCard eyebrow="Leverage & Capital Efficiency" title={`${bsi.period} · ${bsi.statement_type}`}>
          <div className="grid grid-cols-2 gap-4">
            <StatBlock label="Debt/Equity" value={fmt(dm.debt_to_equity, "x", 3)} />
            <StatBlock label="Liabilities/Equity" value={fmt(dm.liabilities_to_equity, "x", 2)} />
            <StatBlock label="Net Debt" value={fmtCr(dm.net_debt)} sub={dm.net_cash_position ? "Net cash position" : undefined} />
            <StatBlock label="Net Debt/EBITDA" value={fmt(dm.net_debt_to_ebitda, "x")} />
            <StatBlock label="ROCE" value={fmt(dm.roce, "%")}
                       sub={dm.roce_source ? "as published by Screener.in" : dm.capital_employed_methodology ? "computed: Total Assets − Current Liabilities" : undefined} />
            <StatBlock label="EBIT Margin × Turnover" value={`${fmt(dm.ebit_margin, "%")} × ${fmt(dm.capital_employed_turnover, "x", 2)}`} />
          </div>
        </ChartCard>

        {/* 4. Working capital */}
        <ChartCard eyebrow="Working Capital" title={isBank ? "Not applicable" : ""}>
          {isBank ? (
            <ChartEmptyState message="Inventory/DIO/DPO/CCC don't apply to a financial institution's balance sheet" />
          ) : (
            <>
              <div className="grid grid-cols-2 gap-4">
                <StatBlock label="DSO" value={fmt(bsi.working_capital.dso_series?.[bsi.working_capital.latest_period || ""], " days", 0)}
                  sub={bsi.working_capital.single_period_fallback?.dso ? "Screener (preferred)" : undefined} />
                <StatBlock label="Inventory Days" value={fmt(bsi.working_capital.dio_series?.[bsi.working_capital.latest_period || ""], " days", 0)}
                  sub={bsi.working_capital.single_period_fallback?.dio ? "Screener (preferred)" : undefined} />
                <StatBlock label="DPO" value={fmt(bsi.working_capital.dpo_series?.[bsi.working_capital.latest_period || ""], " days", 0)}
                  sub={bsi.working_capital.single_period_fallback?.dpo ? "Screener (preferred)" : undefined} />
                <StatBlock label="Cash Conversion Cycle" value={fmt(bsi.working_capital.ccc_latest, " days", 0)}
                  sub={bsi.working_capital.single_period_fallback?.ccc ? "Screener (preferred)" : undefined} />
              </div>
              <p className="text-xs mt-3" style={{ color: "var(--text-dim)" }}>
                Closing-balance / total-revenue methodology (not average balance / credit sales).
                {Object.values(bsi.working_capital.single_period_fallback || {}).some(Boolean) &&
                  " Figures marked \"Screener (preferred)\" use Screener's own reported latest-period value, which is preferred over the yfinance-based multi-year series for the most recent period (older periods still come from yfinance)."}
              </p>
            </>
          )}
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 5. Common size */}
        <ChartCard eyebrow="Common-Size Balance Sheet" title={`% of Total Assets, ${bsi.period}`}>
          {Object.keys(bsi.common_size).length ? (
            <table className="w-full text-sm">
              <tbody>
                {Object.entries(bsi.common_size).map(([field, pct]) => (
                  <tr key={field}>
                    <td className="py-1.5" style={{ color: "var(--text-muted)" }}>{readable(field)}</td>
                    <td className="py-1.5 text-right tabular-nums" style={{ color: "var(--text-secondary)" }}>{pct.toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : <ChartEmptyState />}
        </ChartCard>

        {/* 6. Risk flags */}
        <ChartCard eyebrow="Risk Flags" title={`${triggeredFlags.length} triggered`}>
          {bsi.risk_flags.length ? (
            <ul className="space-y-2.5">
              {[...triggeredFlags, ...otherFlags].map((f) => <RiskFlagRow key={f.flag_id} flag={f} />)}
            </ul>
          ) : <ChartEmptyState message="No flags evaluated" />}
        </ChartCard>
      </div>

      {/* 7. Data coverage */}
      <ChartCard eyebrow="Data Coverage" title="What analysis is possible from the data available">
        <CoverageBar coverage={bsi.coverage} />
      </ChartCard>
    </div>
  );
}
