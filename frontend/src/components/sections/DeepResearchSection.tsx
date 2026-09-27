import { useEffect, useState } from "react";
import { Sparkles } from "lucide-react";
import { api } from "../../api";
import type { FullAnalysis, BlueprintSection, BusinessSegmentItem } from "../../types";
import ChartCard from "../charts/ChartCard";
import DonutChart from "../charts/DonutChart";
import type { DonutSlice } from "../charts/DonutChart";

const SEGMENT_COLORS = ["#c9a227", "#4fb3a0", "#e0793c", "#e8c766", "#7fb8ff", "#d9694f"];

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

function SectionCard({ section }: { section: BlueprintSection }) {
  return (
    <div className="card-rich p-5">
      <p className="eyebrow mb-2">{section.title}</p>

      {(section.type === "text" || section.type === "business_model") && section.content && (
        <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
          {section.content}
        </p>
      )}

      {section.key_points && section.key_points.length > 0 && (
        <ul className="mt-2 space-y-1">
          {section.key_points.map((kp, i) => (
            <li key={i} className="text-sm flex items-start gap-2" style={{ color: "var(--text-secondary)" }}>
              <span style={{ color: "var(--accent-blue)" }}>•</span>{kp}
            </li>
          ))}
        </ul>
      )}

      {section.type === "insight_cards" && section.items && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {section.items.map((item, i) => (
            <div key={i} className="rounded-xl p-3" style={{ background: "var(--bg-input)", border: "1px solid var(--border-subtle)" }}>
              <p className="text-sm font-semibold mb-1" style={{ color: "var(--text-primary)" }}>{item.title}</p>
              <p className="text-xs leading-relaxed" style={{ color: "var(--text-secondary)" }}>{item.description}</p>
            </div>
          ))}
        </div>
      )}

      {section.type === "risk_cards" && section.items && (
        <div className="space-y-2">
          {section.items.map((item, i) => {
            const c = severityColor(item.severity);
            return (
              <div key={i} className="rounded-lg p-3" style={{ background: c.bg, border: `1px solid ${c.border}` }}>
                <div className="flex items-center gap-2 text-sm font-medium" style={{ color: c.text }}>
                  {item.title}
                  {item.severity && <span className="text-xs font-normal ml-auto">{item.severity}</span>}
                </div>
                {item.description && (
                  <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>{item.description}</p>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

/** Latest fiscal year's segment revenue as donut slices — same "latest
 * year, share of that year's total" logic the PDF renderer's business-mix
 * section uses, so the two surfaces agree. */
function segmentSlices(segments: BusinessSegmentItem[]): DonutSlice[] {
  if (segments.length === 0) return [];
  const latestYear = segments.reduce((max, s) => (s.fiscal_year > max ? s.fiscal_year : max), segments[0].fiscal_year);
  return segments
    .filter((s) => s.fiscal_year === latestYear)
    .sort((a, b) => b.revenue - a.revenue)
    .slice(0, 6)
    .map((s, i) => ({ name: s.segment_name, value: s.revenue / 1e7, color: SEGMENT_COLORS[i % SEGMENT_COLORS.length] }));
}

/** This app only has an aggregate concentration ratio (e.g. "top 10 clients
 * = 45% of revenue"), never named per-client revenue — so the only honest
 * chart is a 2-slice split of that ratio against the remainder, not a
 * fabricated multi-client breakdown. */
function clientConcentrationSlices(analysis: FullAnalysis): { label: string; slices: DonutSlice[] } | null {
  const metrics = analysis.sector_analysis?.key_metrics || [];
  const candidates: Array<[string, string]> = [
    ["client_concentration_top10", "Top 10 Clients"],
    ["customer_concentration_top3", "Top 3 Customers"],
  ];
  for (const [name, label] of candidates) {
    const m = metrics.find((x) => x.name === name);
    if (m && m.value !== null && m.value !== undefined && typeof m.value === "number") {
      const pct = Math.max(0, Math.min(100, m.value));
      return {
        label,
        slices: [
          { name: label, value: pct, color: "#c9a227" },
          { name: "Other", value: 100 - pct, color: "#2a3550" },
        ],
      };
    }
  }
  return null;
}

export default function DeepResearchSection({ analysis }: { analysis: FullAnalysis }) {
  const blueprint = analysis.report_blueprint;
  // Defensive filter, not just a backend generation change — an analysis
  // run before this section was removed can still have a stale
  // "key_questions" entry stored in its report_blueprint.
  const sections = (blueprint?.sections || []).filter((s) => s.id !== "key_questions");

  const companyId = analysis.company_info?.stock_id;
  const [segments, setSegments] = useState<BusinessSegmentItem[]>([]);

  useEffect(() => {
    if (!companyId) return;
    let cancelled = false;
    api.getBusinessSegments(companyId).then((res) => {
      if (!cancelled) setSegments(res.segments);
    }).catch(() => { /* optional chart, silent */ });
    return () => { cancelled = true; };
  }, [companyId]);

  const revenueMix = segmentSlices(segments);
  const clientMix = clientConcentrationSlices(analysis);

  if (sections.length === 0 && revenueMix.length === 0 && !clientMix) {
    return (
      <div className="card-rich p-6 text-center text-sm" style={{ color: "var(--text-muted)" }}>
        No interpretation generated yet for this analysis.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-xs" style={{ color: "var(--text-dim)" }}>
        <Sparkles className="h-3.5 w-3.5" />
        Generated by a local Llama model, interpreting only the deterministic data in this report —
        every figure cited is validated to appear elsewhere in it.
      </div>

      {(revenueMix.length > 0 || clientMix) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {revenueMix.length > 0 && (
            <ChartCard eyebrow="Business Mix" title="Revenue by vertical (latest year)">
              <DonutChart data={revenueMix} formatter={(v) => `Rs. ${v.toFixed(0)} Cr`} />
            </ChartCard>
          )}
          {clientMix && (
            <ChartCard eyebrow="Client Base" title={`${clientMix.label} vs. rest of revenue`}>
              <DonutChart data={clientMix.slices} formatter={(v) => `${v.toFixed(0)}%`} />
            </ChartCard>
          )}
        </div>
      )}

      {sections.map((s) => <SectionCard key={s.id} section={s} />)}
    </div>
  );
}
