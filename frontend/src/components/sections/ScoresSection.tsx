import { useState, useEffect } from "react";
import { Check, X, MinusCircle } from "lucide-react";
import { api } from "../../api";
import type { FullAnalysis, PiotroskiScore, SourceLedgerEntry } from "../../types";
import ChartCard from "../charts/ChartCard";
import RadarScoreChart from "../charts/RadarScoreChart";
import DonutChart from "../charts/DonutChart";
import type { DonutSlice } from "../charts/DonutChart";

const TIER_COLOR: Record<number, string> = { 1: "#4fb3a0", 2: "#c9a227", 3: "#a9b3c9" };

function SourceLedgerTable({ ledger }: { ledger: SourceLedgerEntry[] }) {
  if (ledger.length === 0) return null;
  return (
    <div className="card-rich overflow-hidden">
      <div className="px-4 py-3" style={{ borderBottom: "1px solid var(--border-subtle)" }}>
        <span className="eyebrow">Sources &amp; Evidence</span>
        <p className="text-[11px] mt-0.5" style={{ color: "var(--text-dim)" }}>
          Every data source used in this report, by reliability tier (1 = regulatory/exchange filing, 2 = high-quality secondary aggregator, 3 = context/industry).
        </p>
      </div>
      <div className="overflow-x-auto">
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>
              {["Source", "Used For", "Tier", "Date Range", "Facts"].map((h) => (
                <th key={h} style={{
                  padding: "6px 12px", fontSize: 11, fontWeight: 600, textTransform: "uppercase",
                  letterSpacing: "0.06em", color: "var(--text-dim)", background: "var(--bg-input)", textAlign: "left",
                }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {ledger.map((e, i) => (
              <tr key={i} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                <td style={{ padding: "8px 12px", fontSize: 12.5, color: "var(--text-primary)", fontWeight: 500 }}>{e.source}</td>
                <td style={{ padding: "8px 12px", fontSize: 12.5, color: "var(--text-secondary)" }}>{e.used_for}</td>
                <td style={{ padding: "8px 12px" }}>
                  <span className="badge" style={{
                    color: TIER_COLOR[e.tier] || "var(--text-dim)", background: `${TIER_COLOR[e.tier] || "#a9b3c9"}18`,
                    border: `1px solid ${TIER_COLOR[e.tier] || "#a9b3c9"}35`, fontSize: 10,
                  }}>Tier {e.tier}</span>
                </td>
                <td style={{ padding: "8px 12px", fontSize: 12, color: "var(--text-dim)" }}>
                  {e.date_from && e.date_to ? `${e.date_from.slice(0, 10)} – ${e.date_to.slice(0, 10)}` : e.date_from?.slice(0, 10) || "—"}
                </td>
                <td style={{ padding: "8px 12px", fontSize: 12.5, color: "var(--text-secondary)", textAlign: "right" }}>{e.fact_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function PiotroskiCard({ piotroski }: { piotroski: PiotroskiScore }) {
  if (piotroski.score === null) {
    return (
      <div className="card-rich p-5 text-center text-sm" style={{ color: "var(--text-muted)" }}>
        Not enough year-over-year data to compute a Piotroski F-Score yet.
      </div>
    );
  }
  const color = piotroski.score >= 7 ? "#4fb3a0" : piotroski.score >= 4 ? "#e0793c" : "#d9694f";
  return (
    <div className="card-rich p-5">
      <div className="flex items-start justify-between gap-4 mb-4">
        <div>
          <p className="eyebrow mb-1">Piotroski F-Score</p>
          <p className="text-xs" style={{ color: "var(--text-dim)" }}>
            Fundamental strength checklist, {piotroski.prior_fiscal_year} → {piotroski.fiscal_year} — every check computed
            here from this report's own numbers, not a third-party black box.
          </p>
        </div>
        <div className="text-center flex-shrink-0">
          <div className="text-3xl font-bold tabular-nums" style={{ color }}>{piotroski.score}</div>
          <div className="text-xs" style={{ color: "var(--text-dim)" }}>of {piotroski.checks_available} evaluable</div>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-x-6 gap-y-2">
        {piotroski.components.map((c) => (
          <div key={c.key} className="flex items-start gap-2 py-1" title={c.detail}>
            {c.passed === true && <Check className="h-3.5 w-3.5 mt-0.5 flex-shrink-0" style={{ color: "#4fb3a0" }} />}
            {c.passed === false && <X className="h-3.5 w-3.5 mt-0.5 flex-shrink-0" style={{ color: "#d9694f" }} />}
            {c.passed === null && <MinusCircle className="h-3.5 w-3.5 mt-0.5 flex-shrink-0" style={{ color: "var(--text-dim)" }} />}
            <span className="text-xs leading-snug" style={{ color: c.passed === null ? "var(--text-dim)" : "var(--text-secondary)" }}>
              {c.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function ScoreTile({ label, value, sub, color }: {
  label: string; value: string; sub?: string; color: string;
}) {
  return (
    <div className="rounded-xl p-4 text-center"
         style={{ background: `${color}12`, border: `1px solid ${color}30` }}>
      <div className="text-xs uppercase tracking-widest mb-1" style={{ color: "var(--text-dim)" }}>
        {label}
      </div>
      <div className="text-3xl font-bold" style={{ color }}>{value}</div>
      {sub && <div className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>{sub}</div>}
    </div>
  );
}

const CATEGORY_COLORS: Record<string, string> = {
  growth: "#c9a227", profitability: "#4fb3a0", cash_flow: "#e0793c",
  balance_sheet: "#e8c766", efficiency: "#7fb8ff", valuation: "#d9694f",
};
const CATEGORY_LABELS: Record<string, string> = {
  growth: "Growth", profitability: "Profitability", cash_flow: "Cash Flow",
  balance_sheet: "Balance Sheet", efficiency: "Efficiency", valuation: "Valuation",
};

export default function ScoresSection({ analysis }: { analysis: FullAnalysis }) {
  const s = analysis.scores;
  const overallScore = analysis.overall_score;
  const confidence = analysis.confidence_score;
  const dq = analysis.data_quality_score;
  const companyId = analysis.company_info?.stock_id || analysis.stock_id;
  const [sourceLedger, setSourceLedger] = useState<SourceLedgerEntry[]>([]);

  useEffect(() => {
    if (!companyId) return;
    api.getPremiumExtras(companyId)
      .then((r) => setSourceLedger(r.source_ledger || []))
      .catch(() => setSourceLedger([]));
  }, [companyId]);

  const scoreColor = (v: number | null | undefined) => {
    if (v === null || v === undefined) return "#6f7c96";
    if (v >= 75) return "#4fb3a0";
    if (v >= 55) return "#c9a227";
    if (v >= 40) return "#e0793c";
    return "#d9694f";
  };

  const weightSlices: DonutSlice[] = s?.weights
    ? Object.entries(s.weights)
        .filter(([, w]) => w !== null && w !== undefined && w > 0)
        .map(([key, w]) => ({
          name: CATEGORY_LABELS[key] || key.replace(/_/g, " "),
          value: w as number,
          color: CATEGORY_COLORS[key] || "#6f7c96",
        }))
    : [];

  return (
    <div className="space-y-5">
      {/* Top tiles */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <ScoreTile
          label="Composite Score"
          value={overallScore !== null && overallScore !== undefined ? `${overallScore.toFixed(0)}` : "—"}
          sub={s?.overall_rating || undefined}
          color={scoreColor(overallScore)}
        />
        <ScoreTile
          label="Confidence"
          value={confidence !== null && confidence !== undefined ? `${confidence.toFixed(0)}%` : "—"}
          sub="analysis quality"
          color="#e8c766"
        />
        <ScoreTile
          label="Data Quality"
          value={dq !== null && dq !== undefined ? `${dq.toFixed(0)}%` : "—"}
          sub="data completeness"
          color="#7fb8ff"
        />
        {s?.sector_matched !== undefined && (
          <ScoreTile
            label="Sector Match"
            value={s.sector_matched ? "Yes" : "Generic"}
            sub={analysis.sector_analysis?.framework || undefined}
            color={s.sector_matched ? "#4fb3a0" : "#e0793c"}
          />
        )}
      </div>

      {/* Radar + weight donut */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        <div className="lg:col-span-3">
          <ChartCard eyebrow="Score Breakdown" title="Category scores (0–100)">
            <RadarScoreChart scores={s} />
          </ChartCard>
        </div>
        <div className="lg:col-span-2">
          <ChartCard eyebrow="Composite Weighting" title="How the score is built">
            <DonutChart data={weightSlices} formatter={(v) => `${(v * 100).toFixed(0)}%`} />
          </ChartCard>
        </div>
      </div>

      {analysis.metrics?.piotroski && <PiotroskiCard piotroski={analysis.metrics.piotroski} />}

      <SourceLedgerTable ledger={sourceLedger} />

      {/* Red flags */}
      {s?.red_flags && s.red_flags.length > 0 && (
        <div className="card-rich p-5">
          <h3 className="text-xs font-semibold uppercase tracking-widest mb-3"
              style={{ color: "var(--text-dim)" }}>Red Flags Detected</h3>
          <div className="space-y-2">
            {s.red_flags.map((flag: string, i: number) => (
              <div key={i} className="flex items-start gap-2 text-sm"
                   style={{ color: "#f2c9bd" }}>
                <span className="mt-0.5" style={{ color: "#d9694f", flexShrink: 0 }}>▲</span>
                {flag}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
