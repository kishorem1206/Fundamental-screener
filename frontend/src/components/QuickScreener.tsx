import { useEffect, useState } from "react";
import { api } from "../api";
import ScoreScreener from "./ScoreScreener";

interface Props {
  onAnalyse: (stockId: string) => void;
  totalStocks: number;
}

// Separate screen for the Yahoo-only quick analysis (its own table, never
// mixed with full-analysis scores). The scoring run fills this in gradually,
// so the coverage counter refreshes until every stock has a score.
export default function QuickScreener({ onAnalyse, totalStocks }: Props) {
  const [scored, setScored] = useState<number | null>(null);

  useEffect(() => {
    const load = () => api.getQuickScores({ limit: "1" }).then((r) => setScored(r.total)).catch(() => {});
    load();
    const t = setInterval(load, 20000);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="space-y-6 fade-in">
      <div className="card-rich p-6">
        <div className="flex items-start justify-between gap-6 flex-wrap">
          <div className="max-w-2xl">
            <p className="eyebrow">Quick analysis</p>
            <h1 className="text-xl font-semibold mb-1" style={{ color: "var(--text-primary)" }}>
              Fast, Yahoo-only scores for the whole market
            </h1>
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
              Same six scores and sector weights as the full analysis, computed in seconds from consolidated Yahoo
              Finance statements. On the 18 companies with both, the overall score differs by about 1.6 points on
              average. Profitability is unrefined and efficiency runs slightly high, so treat these as a
              shortlist, then run a full analysis on the ones that matter.
            </p>
          </div>
          <div className="text-right">
            <a
              href="/api/quick-scores/export.xlsx"
              download
              className="inline-block mb-3 px-3 py-1.5 rounded-md text-xs font-semibold"
              style={{ background: "var(--accent-blue)", color: "#fff", textDecoration: "none" }}
            >
              Download Excel (all stocks)
            </a>
            <div className="text-3xl font-bold tabular-nums" style={{ color: "var(--accent-blue)" }}>
              {scored === null ? "—" : scored.toLocaleString("en-IN")}
            </div>
            <div className="text-xs" style={{ color: "var(--text-dim)" }}>
              of {totalStocks > 0 ? totalStocks.toLocaleString("en-IN") : "all"} stocks scored
            </div>
          </div>
        </div>
      </div>

      <ScoreScreener source="quick" onAnalyse={onAnalyse} />
    </div>
  );
}
