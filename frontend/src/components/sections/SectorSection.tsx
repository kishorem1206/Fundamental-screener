import type { FullAnalysis } from "../../types";

const STATUS_CFG: Record<string, { color: string; label: string; score: number }> = {
  PASS: { color: "#4fb3a0", label: "Pass", score: 100 },
  EXCELLENT: { color: "#4fb3a0", label: "Excellent", score: 100 },
  GOOD: { color: "#4fb3a0", label: "Good", score: 80 },
  ADEQUATE: { color: "#c9a227", label: "Adequate", score: 60 },
  FAIR: { color: "#e0793c", label: "Fair", score: 40 },
  WARN: { color: "#e0793c", label: "Warn", score: 40 },
  POOR: { color: "#d9694f", label: "Poor", score: 20 },
  FAIL: { color: "#d9694f", label: "Fail", score: 10 },
};

function StatusDot({ status }: { status: "PASS" | "WARN" | "FAIL" | string }) {
  const c = STATUS_CFG[status?.toUpperCase()] || { color: "#a9b3c9", label: status, score: 0 };
  return (
    <span className="flex items-center gap-1.5 text-xs font-medium" style={{ color: c.color }}>
      <span className="w-2 h-2 rounded-full inline-block" style={{ background: c.color }} />
      {c.label}
    </span>
  );
}

// Compact horizontal bar showing where a metric's qualitative status falls
// on a 0–100 band, alongside its raw value — a quick visual read without
// implying false numeric precision for what's really a categorical status.
function MetricStatusBar({ status }: { status?: string }) {
  const c = status ? STATUS_CFG[status.toUpperCase()] : undefined;
  if (!c) return null;
  return (
    <div className="h-1.5 rounded-full mt-1.5" style={{ background: "var(--bg-input)", width: 96 }}>
      <div className="h-1.5 rounded-full" style={{ width: `${c.score}%`, background: c.color }} />
    </div>
  );
}

export default function SectorSection({ analysis }: { analysis: FullAnalysis }) {
  const sa = analysis.sector_analysis;
  if (!sa) {
    return (
      <div className="card p-6 text-center text-sm" style={{ color: "var(--text-muted)" }}>
        Sector analysis not available
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="card p-5">
        <div className="flex items-center gap-3 mb-1">
          <h2 className="text-base font-bold" style={{ color: "var(--text-primary)" }}>
            {sa.framework || "Generic"} Framework
          </h2>
          {sa.sector_matched && (
            <span className="badge badge-blue text-xs">Sector-Specific</span>
          )}
        </div>
        {sa.description && (
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>{sa.description}</p>
        )}
      </div>

      {/* Key metrics */}
      {sa.key_metrics && sa.key_metrics.length > 0 && (
        <div className="card p-5">
          <h3 className="text-xs font-semibold uppercase tracking-widest mb-4"
              style={{ color: "var(--text-dim)" }}>
            Sector Key Metrics
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8">
            {sa.key_metrics.map((m: {
              name: string;
              value?: number | string | null;
              unit?: string;
              status?: string;
              threshold?: number;
              description?: string;
              sector_median?: number | null;
              sector_percentile?: number | null;
            }) => (
              <div key={m.name} className="metric-row">
                <div className="flex-1 min-w-0">
                  <div className="text-sm" style={{ color: "var(--text-secondary)" }}>{m.name}</div>
                  {m.description && (
                    <div className="text-xs" style={{ color: "var(--text-dim)" }}>{m.description}</div>
                  )}
                </div>
                <div className="flex flex-col items-end gap-0.5 flex-shrink-0">
                  <div className="flex items-center gap-3">
                    {m.status && <StatusDot status={m.status} />}
                    <span className="text-sm font-semibold tabular-nums"
                          style={{ color: "var(--text-primary)" }}>
                      {m.value !== null && m.value !== undefined ? `${m.value}${m.unit || ""}` : "—"}
                    </span>
                  </div>
                  {m.sector_median !== null && m.sector_median !== undefined && (
                    <div className="text-[11px] tabular-nums" style={{ color: "var(--text-dim)" }}>
                      vs sector avg {m.sector_median}{m.unit || ""}
                      {m.sector_percentile !== null && m.sector_percentile !== undefined && (
                        <span> · {m.sector_percentile}th pct</span>
                      )}
                    </div>
                  )}
                  {m.status && <MetricStatusBar status={m.status} />}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Red flags */}
      {sa.red_flags && sa.red_flags.length > 0 && (
        <div className="card p-5">
          <h3 className="text-xs font-semibold uppercase tracking-widest mb-3"
              style={{ color: "var(--text-dim)" }}>Sector Red Flags</h3>
          <div className="space-y-3">
            {sa.red_flags.map((rf: {
              name: string;
              triggered: boolean;
              severity?: string;
              message?: string;
            }, i: number) => (
              rf.triggered && (
                <div key={i} className="rounded-lg p-3"
                     style={{
                       background: rf.severity === "CRITICAL"
                         ? "rgba(217,105,79,0.1)" : "rgba(224,121,60,0.08)",
                       border: `1px solid ${rf.severity === "CRITICAL"
                         ? "rgba(217,105,79,0.3)" : "rgba(224,121,60,0.25)"}`,
                     }}>
                  <div className="flex items-center gap-2 text-sm font-medium"
                       style={{ color: rf.severity === "CRITICAL" ? "#d9694f" : "#e0793c" }}>
                    <span>{rf.severity === "CRITICAL" ? "▲" : "⚠"}</span>
                    {rf.name}
                    {rf.severity && (
                      <span className="text-xs font-normal ml-auto">{rf.severity}</span>
                    )}
                  </div>
                  {rf.message && (
                    <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>{rf.message}</p>
                  )}
                </div>
              )
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
