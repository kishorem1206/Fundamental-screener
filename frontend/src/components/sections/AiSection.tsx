import type { FullAnalysis } from "../../types";

const RATING_CFG: Record<string, { color: string; bg: string; label: string }> = {
  STRONG: { color: "#4fb3a0", bg: "rgba(79,179,160,0.12)", label: "Strong Buy" },
  GOOD:   { color: "#c9a227", bg: "rgba(201,162,39,0.12)", label: "Good" },
  FAIR:   { color: "#e0793c", bg: "rgba(224,121,60,0.12)", label: "Fair / Hold" },
  WEAK:   { color: "#d9694f", bg: "rgba(217,105,79,0.10)", label: "Weak" },
  POOR:   { color: "#d9694f", bg: "rgba(217,105,79,0.10)", label: "Poor / Avoid" },
};

function Pill({ text, color }: { text: string; color: string }) {
  return (
    <span className="inline-block px-2.5 py-0.5 rounded text-xs font-medium"
          style={{ background: `${color}18`, color, border: `1px solid ${color}30` }}>
      {text}
    </span>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h4 className="text-xs font-semibold uppercase tracking-widest mb-2"
          style={{ color: "var(--text-dim)" }}>
        {title}
      </h4>
      {children}
    </div>
  );
}

export default function AiSection({ analysis }: { analysis: FullAnalysis }) {
  const ai = analysis.ai_analysis;
  const rating = ai?.rating || analysis.ai_rating;
  const rc = rating ? (RATING_CFG[rating] || null) : null;

  if (!ai) {
    return (
      <div className="card p-6 text-center" style={{ color: "var(--text-muted)" }}>
        <div className="text-sm">AI analysis not available</div>
        <div className="text-xs mt-1">
          The AI analysis stage may have been skipped or failed.
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Rating hero */}
      {rc && (
        <div className="card p-5 flex items-center gap-5">
          <div className="rounded-2xl p-4 text-center flex-shrink-0"
               style={{ background: rc.bg, border: `1px solid ${rc.color}30`, minWidth: 90 }}>
            <div className="text-xs uppercase tracking-widest mb-1" style={{ color: "var(--text-dim)" }}>
              AI Rating
            </div>
            <div className="text-2xl font-bold" style={{ color: rc.color }}>{rc.label}</div>
            {ai.valuation_view && (
              <div className="text-xs mt-1" style={{ color: rc.color }}>
                {ai.valuation_view}
              </div>
            )}
          </div>
          {ai.executive_summary && (
            <div className="flex-1 text-sm leading-relaxed"
                 style={{ color: "var(--text-secondary)" }}>
              {ai.executive_summary}
            </div>
          )}
        </div>
      )}

      {/* Detailed sections */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {ai.business_quality_assessment && (
          <div className="card p-4">
            <Section title="Business Quality">
              <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
                {ai.business_quality_assessment}
              </p>
            </Section>
          </div>
        )}
        {ai.financial_health_summary && (
          <div className="card p-4">
            <Section title="Financial Health">
              <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
                {ai.financial_health_summary}
              </p>
            </Section>
          </div>
        )}
        {ai.growth_outlook && (
          <div className="card p-4">
            <Section title="Growth Outlook">
              <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
                {ai.growth_outlook}
              </p>
            </Section>
          </div>
        )}
        {ai.valuation_commentary && (
          <div className="card p-4">
            <Section title="Valuation Commentary">
              <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
                {ai.valuation_commentary}
              </p>
            </Section>
          </div>
        )}
      </div>

      {/* Bull/Bear */}
      {(ai.bull_case || ai.bear_case) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {ai.bull_case && (
            <div className="card p-4"
                 style={{ border: "1px solid rgba(79,179,160,0.25)" }}>
              <Section title="Bull Case">
                {Array.isArray(ai.bull_case) ? (
                  <ul className="space-y-1">
                    {ai.bull_case.map((item: string, i: number) => (
                      <li key={i} className="flex gap-2 text-sm"
                          style={{ color: "var(--text-secondary)" }}>
                        <span style={{ color: "#4fb3a0", flexShrink: 0 }}>↑</span>
                        {item}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm" style={{ color: "var(--text-secondary)" }}>{ai.bull_case}</p>
                )}
              </Section>
            </div>
          )}
          {ai.bear_case && (
            <div className="card p-4"
                 style={{ border: "1px solid rgba(217,105,79,0.2)" }}>
              <Section title="Bear Case">
                {Array.isArray(ai.bear_case) ? (
                  <ul className="space-y-1">
                    {ai.bear_case.map((item: string, i: number) => (
                      <li key={i} className="flex gap-2 text-sm"
                          style={{ color: "var(--text-secondary)" }}>
                        <span style={{ color: "#d9694f", flexShrink: 0 }}>↓</span>
                        {item}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm" style={{ color: "var(--text-secondary)" }}>{ai.bear_case}</p>
                )}
              </Section>
            </div>
          )}
        </div>
      )}

      {/* Investment thesis */}
      {ai.investment_thesis && ai.investment_thesis.length > 0 && (
        <div className="card p-4">
          <Section title="Investment Thesis">
            <ul className="space-y-1.5">
              {ai.investment_thesis.map((point: string, i: number) => (
                <li key={i} className="flex gap-2 text-sm"
                    style={{ color: "var(--text-secondary)" }}>
                  <span style={{ color: "#c9a227", flexShrink: 0, marginTop: 1 }}>•</span>
                  {point}
                </li>
              ))}
            </ul>
          </Section>
        </div>
      )}

      {/* Key risks from AI */}
      {ai.key_risks && ai.key_risks.length > 0 && (
        <div className="card p-4">
          <Section title="Key Risks (AI Assessment)">
            <div className="flex flex-wrap gap-2 mt-1">
              {ai.key_risks.map((risk: string, i: number) => (
                <Pill key={i} text={risk} color="#d9694f" />
              ))}
            </div>
          </Section>
        </div>
      )}

      {/* Catalysts from AI — handles both key_catalysts and catalysts field names */}
      {(() => {
        const cats = ai.key_catalysts?.length ? ai.key_catalysts : ai.catalysts;
        if (!cats || cats.length === 0) return null;
        return (
          <div className="card p-4">
            <Section title="Key Catalysts (AI Assessment)">
              <div className="flex flex-wrap gap-2 mt-1">
                {cats.map((cat: string, i: number) => (
                  <Pill key={i} text={cat} color="#4fb3a0" />
                ))}
              </div>
            </Section>
          </div>
        );
      })()}

      {/* Model disclaimer */}
      <div className="text-xs leading-relaxed p-4 rounded-xl"
           style={{ background: "rgba(111,124,150,0.08)", color: "var(--text-dim)",
                    border: "1px solid var(--border-subtle)" }}>
        AI analysis generated by {analysis.ai_analysis?.model || "GPT-OSS 20B via Groq"}.
        This is not financial advice. All calculations are deterministic; LLM provides qualitative interpretation only.
        Do your own due diligence before making investment decisions.
      </div>
    </div>
  );
}
