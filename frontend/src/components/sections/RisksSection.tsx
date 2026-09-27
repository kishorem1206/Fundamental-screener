import type { FullAnalysis, Risk, Catalyst } from "../../types";

function severityColor(severity: string | undefined) {
  switch (severity?.toUpperCase()) {
    case "HIGH":
    case "CRITICAL":
      return { bg: "rgba(217,105,79,0.1)", border: "rgba(217,105,79,0.3)", text: "#d9694f" };
    case "MEDIUM":
      return { bg: "rgba(224,121,60,0.08)", border: "rgba(224,121,60,0.25)", text: "#e0793c" };
    default:
      return { bg: "rgba(111,124,150,0.1)", border: "rgba(111,124,150,0.2)", text: "#a9b3c9" };
  }
}

function impactColor(impact: string | undefined) {
  switch (impact?.toUpperCase()) {
    case "HIGH":
      return { bg: "rgba(79,179,160,0.1)", border: "rgba(79,179,160,0.3)", text: "#4fb3a0" };
    case "MEDIUM":
      return { bg: "rgba(201,162,39,0.1)", border: "rgba(201,162,39,0.3)", text: "#c9a227" };
    default:
      return { bg: "rgba(111,124,150,0.1)", border: "rgba(111,124,150,0.2)", text: "#a9b3c9" };
  }
}

export default function RisksSection({ analysis }: { analysis: FullAnalysis }) {
  const risks: Risk[] = analysis.risks || [];
  const catalysts: Catalyst[] = analysis.catalysts || [];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {/* Risks */}
      <div>
        <h3 className="text-xs font-semibold uppercase tracking-widest mb-3"
            style={{ color: "var(--text-dim)" }}>
          Risk Factors ({risks.length})
        </h3>
        <div className="space-y-2">
          {risks.length === 0 ? (
            <div className="card p-4 text-sm text-center" style={{ color: "var(--text-muted)" }}>
              No risks identified
            </div>
          ) : (
            risks.map((r, i) => {
              const c = severityColor(r.severity);
              return (
                <div key={i} className="rounded-xl p-4"
                     style={{ background: c.bg, border: `1px solid ${c.border}` }}>
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <div className="text-sm font-semibold" style={{ color: c.text }}>
                      {r.category || "Risk"}
                    </div>
                    {r.severity && (
                      <span className="text-xs px-2 py-0.5 rounded"
                            style={{ background: `${c.border}`, color: c.text, flexShrink: 0 }}>
                        {r.severity}
                      </span>
                    )}
                  </div>
                  <p className="text-sm" style={{ color: "var(--text-secondary)" }}>{r.description}</p>
                  {r.mitigation && (
                    <p className="text-xs mt-2" style={{ color: "var(--text-muted)" }}>
                      Mitigation: {r.mitigation}
                    </p>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Catalysts */}
      <div>
        <h3 className="text-xs font-semibold uppercase tracking-widest mb-3"
            style={{ color: "var(--text-dim)" }}>
          Catalysts ({catalysts.length})
        </h3>
        <div className="space-y-2">
          {catalysts.length === 0 ? (
            <div className="card p-4 text-sm text-center" style={{ color: "var(--text-muted)" }}>
              No catalysts identified
            </div>
          ) : (
            catalysts.map((cat, i) => {
              const c = impactColor(cat.impact);
              return (
                <div key={i} className="rounded-xl p-4"
                     style={{ background: c.bg, border: `1px solid ${c.border}` }}>
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <div className="text-sm font-semibold" style={{ color: c.text }}>
                      {cat.category || "Catalyst"}
                    </div>
                    <div className="flex items-center gap-1 flex-shrink-0">
                      {cat.timeframe && (
                        <span className="text-xs px-1.5 py-0.5 rounded"
                              style={{ background: "rgba(111,124,150,0.2)", color: "var(--text-muted)" }}>
                          {cat.timeframe}
                        </span>
                      )}
                      {cat.impact && (
                        <span className="text-xs px-1.5 py-0.5 rounded"
                              style={{ background: `${c.border}`, color: c.text }}>
                          {cat.impact}
                        </span>
                      )}
                    </div>
                  </div>
                  <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                    {cat.description}
                  </p>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
