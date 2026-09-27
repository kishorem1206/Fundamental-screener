import { useState, useEffect, useRef } from "react";
import { Check, X, Loader2, ChevronRight } from "lucide-react";
import { api } from "../api";
import type { AnalysisStatus } from "../types";

const STAGE_LABELS: Record<string, string> = {
  company_identification: "Company ID",
  financial_data_collection: "Financial Data",
  income_statement_analysis: "Income Statement",
  balance_sheet_analysis: "Balance Sheet",
  cash_flow_analysis: "Cash Flow",
  ratio_calculations: "Ratios",
  metric_validation: "Validation",
  sector_analysis: "Sector",
  peer_comparison: "Peers",
  risk_analysis: "Risks",
  scoring: "Scoring",
  ai_analysis: "AI Analysis",
  report_blueprint: "Interpretation",
  pl_intelligence_scoring: "P&L Intelligence",
  balance_sheet_intelligence_scoring: "BS Intelligence",
  report_generation: "Report",
};

interface Props {
  analysisId: string;
  onComplete: (id: string) => void;
}

export default function AnalysisProgress({ analysisId, onComplete }: Props) {
  const [status, setStatus] = useState<AnalysisStatus | null>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const completedRef = useRef(false);

  useEffect(() => {
    timerRef.current = setInterval(() => setElapsedSeconds((s) => s + 1), 1000);
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, []);

  useEffect(() => {
    const poll = async () => {
      try {
        const s = await api.getAnalysisStatus(analysisId);
        setStatus(s);
        if ((s.status === "COMPLETED" || s.status === "FAILED") && !completedRef.current) {
          completedRef.current = true;
          if (intervalRef.current) clearInterval(intervalRef.current);
          if (timerRef.current) clearInterval(timerRef.current);
          if (s.status === "COMPLETED") {
            setTimeout(() => onComplete(analysisId), 800);
          }
        }
      } catch { /* silent */ }
    };
    poll();
    intervalRef.current = setInterval(poll, 2000);
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [analysisId, onComplete]);

  // Clamped defensively — real bug found live 2026-09-22: the backend's
  // STAGES table (orchestrator.py) had two stages pushed past 100 by a
  // later insertion that didn't renumber the tail, so this bar and the
  // "%" label briefly read e.g. 102%. The backend is now fixed at the
  // source, but a stage list is easy to miscount again later, and a
  // progress bar wider than its own track / a number claiming more than
  // "done" is a visibly broken UI either way — cheap enough to guard here too.
  const progress = Math.min(100, status?.overall_progress ?? 0);
  const currentStage = status?.current_stage;
  const stages = Object.entries(STAGE_LABELS);
  const elapsed = `${Math.floor(elapsedSeconds / 60)}:${String(elapsedSeconds % 60).padStart(2, "0")}`;

  const stageStatus = (key: string): "done" | "active" | "pending" | "failed" => {
    const found = status?.stages?.find((s) => s.stage_name === key);
    if (!found) return "pending";
    if (found.status === "COMPLETED") return "done";
    if (found.status === "RUNNING") return "active";
    if (found.status === "FAILED") return "failed";
    return "pending";
  };

  const activeMessage = currentStage
    ? status?.stages?.find((s) => s.stage_name === currentStage)?.message
    : null;

  return (
    <div className="max-w-4xl mx-auto space-y-6 fade-in">
      <div className="text-center space-y-1.5">
        <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
          {status?.company?.company_name ?? "Analyzing Stock"}
        </h1>
        {status?.company && (
          <>
            <p className="text-xs font-mono" style={{ color: "var(--text-dim)" }}>
              {status.company.exchange}:{status.company.symbol}
            </p>
            <div className="flex items-center justify-center gap-1.5 flex-wrap text-xs pt-1">
              {[status.company.macro_sector, status.company.sector, status.company.industry, status.company.basic_industry]
                .filter((level): level is string => !!level)
                .map((level, i, all) => (
                  <span key={`${i}-${level}`} className="flex items-center gap-1.5">
                    <span className="px-2 py-0.5 rounded-md" style={{
                      color: i === all.length - 1 ? "#e8c766" : "var(--text-secondary)",
                      background: i === all.length - 1 ? "rgba(201,162,39,0.14)" : "rgba(255,255,255,0.05)",
                      border: "1px solid var(--border-subtle)",
                    }}>{level}</span>
                    {i < all.length - 1 && <span style={{ color: "var(--text-dim)" }}>›</span>}
                  </span>
                ))}
            </div>
          </>
        )}
        <p className="text-sm pt-1" style={{ color: "var(--text-secondary)" }}>
          Analysis ID: <span className="font-mono" style={{ color: "#e8c766" }}>{analysisId}</span>
        </p>
      </div>

      {/* Overall progress */}
      <div className="card-rich p-6 space-y-4">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div>
            <div className="text-sm font-semibold" style={{ color: "var(--text-secondary)" }}>Overall Progress</div>
            {currentStage && (
              <div className="text-xs mt-0.5 pulse" style={{ color: "var(--text-muted)" }}>
                {STAGE_LABELS[currentStage] || currentStage}{activeMessage ? ` — ${activeMessage}` : ""}
              </div>
            )}
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold tabular-nums" style={{ color: "var(--accent-blue)" }}>{progress}%</div>
            <div className="text-xs tabular-nums" style={{ color: "var(--text-dim)" }}>{elapsed}</div>
          </div>
        </div>
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${progress}%` }} />
        </div>
      </div>

      {/* Horizontal pipeline */}
      <div className="card-rich p-5">
        <p className="eyebrow mb-4">Analysis Pipeline</p>
        <div className="flex items-start flex-wrap gap-y-4">
          {stages.map(([key, label], i) => {
            const st = stageStatus(key);
            return (
              <div key={key} className="flex items-center">
                <div className="flex flex-col items-center gap-1.5 px-2 min-w-[84px] text-center">
                  <StageIcon status={st} />
                  <span
                    className="text-[10px] font-semibold uppercase tracking-wider leading-tight"
                    style={{
                      color: st === "active" ? "var(--text-primary)"
                        : st === "done" ? "var(--text-secondary)"
                        : st === "failed" ? "#d9694f" : "var(--text-dim)",
                    }}
                  >
                    {label}
                  </span>
                </div>
                {i < stages.length - 1 && (
                  <ChevronRight className="h-3.5 w-3.5 flex-shrink-0 -mx-0.5" style={{ color: "var(--text-dim)", opacity: 0.4 }} />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {status?.status === "FAILED" && (
        <div className="rounded-xl p-4" style={{ background: "rgba(217,105,79,0.1)", border: "1px solid rgba(217,105,79,0.3)" }}>
          <div className="font-semibold text-sm" style={{ color: "#d9694f" }}>Analysis Failed</div>
          <div className="text-xs mt-1" style={{ color: "#f2c9bd" }}>{status.error_message}</div>
        </div>
      )}
    </div>
  );
}

function StageIcon({ status }: { status: "done" | "active" | "pending" | "failed" }) {
  const base = "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0";
  if (status === "done") {
    return (
      <div className={base} style={{ background: "rgba(79,179,160,0.15)", border: "1.5px solid #4fb3a0" }}>
        <Check className="h-3.5 w-3.5" style={{ color: "#4fb3a0" }} />
      </div>
    );
  }
  if (status === "active") {
    return (
      <div className={base} style={{ background: "rgba(201,162,39,0.15)", border: "1.5px solid #c9a227" }}>
        <Loader2 className="h-3.5 w-3.5 animate-spin" style={{ color: "#c9a227" }} />
      </div>
    );
  }
  if (status === "failed") {
    return (
      <div className={base} style={{ background: "rgba(217,105,79,0.15)", border: "1.5px solid #d9694f" }}>
        <X className="h-3.5 w-3.5" style={{ color: "#d9694f" }} />
      </div>
    );
  }
  return (
    <div className={base} style={{ border: "1.5px solid var(--border-subtle)", opacity: 0.6 }} />
  );
}
