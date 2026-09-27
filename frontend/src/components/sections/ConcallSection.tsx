import { useState, useEffect } from "react";
import { Mic, ExternalLink } from "lucide-react";
import { api } from "../../api";
import type {
  FullAnalysis, ConcallIntelligenceResponse, ConcallTopicSentimentItem,
} from "../../types";

const SENTIMENT_COLOR: Record<string, string> = {
  POSITIVE: "#4fb3a0", NEGATIVE: "#d9694f", NEUTRAL: "#a9b3c9", MIXED: "#e0793c",
};

function TopicGrid({ topics }: { topics: ConcallTopicSentimentItem[] }) {
  if (topics.length === 0) return null;
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
      {topics.map((t) => (
        <div key={t.topic} className="flex items-center justify-between px-3 py-2 rounded-lg"
             style={{ background: "var(--bg-input)", border: "1px solid var(--border-subtle)" }}>
          <span className="text-xs" style={{ color: "var(--text-secondary)" }}>{t.topic}</span>
          <span className="text-xs font-semibold" style={{ color: SENTIMENT_COLOR[t.sentiment] || "var(--text-dim)" }}>
            {t.arrow} {t.sentiment.charAt(0) + t.sentiment.slice(1).toLowerCase()}
          </span>
        </div>
      ))}
    </div>
  );
}

function HighlightsBlock({ highlights }: { highlights: ConcallIntelligenceResponse["highlights"] }) {
  if (!highlights || highlights.sections.length === 0) return null;
  return (
    <div className="card-rich p-5">
      <div className="flex items-center justify-between mb-3">
        <p className="eyebrow">Results &amp; Concall Highlights</p>
        {highlights.source_url ? (
          <a href={highlights.source_url} target="_blank" rel="noopener noreferrer"
             className="text-[11px] flex items-center gap-1" style={{ color: "var(--text-dim)" }}>
            arthneeti.com <ExternalLink className="h-3 w-3" />
          </a>
        ) : (
          <span className="text-[11px]" style={{ color: "var(--text-dim)" }}>
            generated from this report's own extracted data
          </span>
        )}
      </div>
      <div className="space-y-4">
        {highlights.sections.map((s) => (
          <div key={s.heading}>
            <p className="text-sm font-semibold mb-1.5" style={{ color: "var(--text-primary)" }}>{s.heading}</p>
            <ul className="space-y-1">
              {s.bullets.slice(0, 6).map((b, i) => (
                <li key={i} className="text-sm flex items-start gap-2" style={{ color: "var(--text-secondary)" }}>
                  <span style={{ color: "var(--accent-blue)" }}>•</span>{b}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}

const TONE_COLOR: Record<string, string> = { positive: "#4fb3a0", negative: "#d9694f", neutral: "#a9b3c9" };
const STATUS_COLOR: Record<string, string> = {
  NEW: "#c9a227", REITERATED: "#a9b3c9", UPGRADED: "#4fb3a0", DOWNGRADED: "#d9694f",
};

function GuidanceTable({ guidance }: { guidance: ConcallIntelligenceResponse["guidance"] }) {
  if (guidance.length === 0) return null;
  return (
    <div className="card-rich overflow-hidden">
      <div className="px-4 py-3" style={{ borderBottom: "1px solid var(--border-subtle)" }}>
        <span className="eyebrow">Management Guidance</span>
      </div>
      <div className="overflow-x-auto">
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>
              {["Metric", "Period", "Target", "Tone", "Status"].map((h) => (
                <th key={h} style={{
                  padding: "6px 12px", fontSize: 11, fontWeight: 600, textTransform: "uppercase",
                  letterSpacing: "0.06em", color: "var(--text-dim)", background: "var(--bg-input)", textAlign: "left",
                }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {guidance.map((g, i) => {
              let target = "—";
              if (g.guidance_type === "quantitative") {
                if (g.target_low !== null && g.target_high !== null) target = `${g.target_low}-${g.target_high} ${g.unit || ""}`;
                else if (g.target_value !== null) target = `${g.target_value} ${g.unit || ""}`;
              } else {
                target = "qualitative";
              }
              return (
                <tr key={i} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                  <td style={{ padding: "8px 12px", fontSize: 12.5, color: "var(--text-primary)" }}>
                    {g.metric.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                  </td>
                  <td style={{ padding: "8px 12px", fontSize: 12.5, color: "var(--text-secondary)" }}>{g.period || "—"}</td>
                  <td style={{ padding: "8px 12px", fontSize: 12.5, color: "var(--text-secondary)" }}>{target}</td>
                  <td style={{ padding: "8px 12px", fontSize: 12.5, color: TONE_COLOR[g.tone || ""] || "var(--text-dim)" }}>{g.tone || "—"}</td>
                  <td style={{ padding: "8px 12px" }}>
                    <span className="badge" style={{
                      color: STATUS_COLOR[g.status] || "var(--text-dim)", background: `${STATUS_COLOR[g.status] || "#a9b3c9"}18`,
                      border: `1px solid ${STATUS_COLOR[g.status] || "#a9b3c9"}35`, fontSize: 10,
                    }}>{g.status}</span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function ConcallSection({ analysis }: { analysis: FullAnalysis }) {
  const companyId = analysis.company_info?.stock_id || analysis.stock_id;
  const [data, setData] = useState<ConcallIntelligenceResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!companyId) { setLoading(false); return; }
    setLoading(true);
    api.getConcallIntelligence(companyId)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [companyId]);

  if (loading) {
    return <div className="py-12 flex items-center justify-center"><div className="spinner" /></div>;
  }

  if (!data || !data.latest_transcript) {
    return (
      <div className="card-rich p-6 text-center text-sm" style={{ color: "var(--text-muted)" }}>
        No earnings call transcript has been analyzed for this company yet.
      </div>
    );
  }

  const t = data.latest_transcript;
  const gc = data.guidance_consistency;

  return (
    <div className="space-y-4">
      <div className="card-rich p-5">
        <div className="flex items-center gap-2 mb-1">
          <Mic className="h-4 w-4" style={{ color: "var(--accent-blue)" }} />
          <p className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            Latest earnings call: {t.quarter || t.call_date || t.filing_date}
          </p>
        </div>
        {t.management_participants.length > 0 && (
          <p className="text-xs" style={{ color: "var(--text-dim)" }}>
            Management: {t.management_participants.slice(0, 4).map((p) => p.name).join(", ")}
          </p>
        )}
      </div>

      <HighlightsBlock highlights={data.highlights} />

      {data.topic_sentiment.length > 0 && (
        <div className="card-rich p-5">
          <p className="eyebrow mb-3">Management Tone by Topic</p>
          <TopicGrid topics={data.topic_sentiment} />
        </div>
      )}

      {data.what_changed.length > 0 && (
        <div className="card-rich p-5">
          <p className="eyebrow mb-3">What Changed Since Last Call</p>
          <ul className="space-y-1.5">
            {data.what_changed.map((c, i) => (
              <li key={i} className="text-sm flex items-start gap-2" style={{ color: "var(--text-secondary)" }}>
                <span style={{ color: "var(--accent-blue)" }}>•</span>{c}
              </li>
            ))}
          </ul>
        </div>
      )}

      {gc && (
        <div className="card-rich p-5 flex items-center justify-between flex-wrap gap-2">
          <div>
            <p className="eyebrow mb-1">Guidance Consistency</p>
            <p className="text-[11px]" style={{ color: "var(--text-dim)" }}>
              {gc.metrics_tracked} metrics tracked, {gc.total_updates} quarter-over-quarter updates on record —
              reiterated/upgraded vs. downgraded, not a hit-rate accuracy score.
            </p>
          </div>
          <span className="text-2xl font-bold tabular-nums" style={{ color: "var(--text-primary)" }}>
            {Math.round(gc.score)}<span className="text-sm font-normal" style={{ color: "var(--text-dim)" }}>/100</span>
          </span>
        </div>
      )}

      <GuidanceTable guidance={data.guidance} />

      {data.credibility.length > 0 && (
        <div className="card-rich p-5">
          <p className="eyebrow mb-3">Guidance Consistency (across quarters on record)</p>
          <ul className="space-y-1.5">
            {data.credibility.map((c) => (
              <li key={c.metric} className="text-sm" style={{ color: "var(--text-secondary)" }}>
                <b style={{ color: "var(--text-primary)" }}>{c.metric.replace(/_/g, " ").replace(/\b\w/g, (ch) => ch.toUpperCase())}</b>:
                {" "}{c.guidance_count} updates — {c.upgraded_count} upgraded, {c.downgraded_count} downgraded,
                {" "}{c.reiterated_count} reiterated (latest: {c.last_status})
              </li>
            ))}
          </ul>
        </div>
      )}

    </div>
  );
}
