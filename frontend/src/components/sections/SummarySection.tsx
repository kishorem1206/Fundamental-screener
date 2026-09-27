import { useState, useEffect } from "react";
import { api } from "../../api";
import type { FullAnalysis, InsiderActivityItem, BusinessSegmentItem, BrandItem } from "../../types";
import ChartCard from "../charts/ChartCard";
import SegmentRevenueChart from "../charts/SegmentRevenueChart";

function BrandPortfolio({ brands }: { brands: BrandItem[] }) {
  if (brands.length === 0) return null;
  return (
    <div className="card-rich overflow-hidden">
      <div className="px-4 py-3" style={{ borderBottom: "1px solid var(--border-subtle)" }}>
        <span className="eyebrow">Brand Portfolio</span>
      </div>
      <div className="overflow-x-auto">
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>
              {["Brand", "Category", "Ownership", "Market Share"].map((h) => (
                <th key={h} style={{
                  padding: "6px 12px", fontSize: 11, fontWeight: 600, textTransform: "uppercase",
                  letterSpacing: "0.06em", color: "var(--text-dim)", background: "var(--bg-input)", textAlign: "left",
                }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {brands.map((b) => (
              <tr key={b.brand_name} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                <td style={{ padding: "8px 12px", fontSize: 13, color: "var(--text-primary)", fontWeight: 500 }}>{b.brand_name}</td>
                <td style={{ padding: "8px 12px", fontSize: 12.5, color: "var(--text-secondary)" }}>{b.category || "—"}</td>
                <td style={{ padding: "8px 12px", fontSize: 12.5, color: "var(--text-secondary)" }}>
                  {b.ownership ? b.ownership.charAt(0).toUpperCase() + b.ownership.slice(1) : "—"}
                </td>
                <td style={{ padding: "8px 12px", fontSize: 12.5, color: "var(--text-secondary)" }}>
                  {b.market_share_pct !== null ? `${b.market_share_pct}%${b.market_share_context ? ` (${b.market_share_context})` : ""}` : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// Screener.in's scraped text carries footnote markers ([1], [2]...) and,
// for the free (unauthenticated) preview, a stray "{#" anchor fragment
// where the rest of the wiki markup was cut off — cosmetic artifacts of
// the source, not content, so stripped before display. Collapses only
// horizontal whitespace — blank lines between sections are preserved
// (see splitKeyPointSections, which depends on them).
// Screener.in's own unauthenticated preview sometimes renders its upsell
// copy ("Please upgrade to premium to read more key insights...") in the
// same spot real key-points content would occupy (confirmed live on Netweb
// Technologies) — the backend now filters this at ingestion time, but this
// is a second, independent check so the section never shows it regardless
// of when the underlying row was written.
function isKeyPointsPaywall(text: string): boolean {
  return text.toLowerCase().includes("upgrade to premium");
}

function cleanScreenerText(text: string): string {
  return text
    .replace(/\[\d+\]/g, "")
    .replace(/\{#[^}]*\}/g, "")
    .replace(/\{#/g, "")
    .replace(/[ \t]{2,}/g, " ")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

// The full (logged-in) Key Points commentary is a series of
// "Title\nBody..." blocks separated by a blank line (confirmed on
// Persistent Systems, 2026-09-14: "Solutions Offered\n...\n\nBrand
// Value\n...\n\nRevenue Mix\n..."). The free-preview fallback is just one
// such block with no title worth extracting on its own.
interface KeyPointSection { title: string | null; body: string; }
function splitKeyPointSections(text: string): KeyPointSection[] {
  const blocks = text.split(/\n{2,}/).map((b) => b.trim()).filter(Boolean);
  return blocks.map((block) => {
    const nl = block.indexOf("\n");
    if (nl === -1 || nl > 40) return { title: null, body: block };
    const title = block.slice(0, nl).trim();
    // A real section title is short and doesn't end in sentence punctuation.
    if (!title || /[.!?]$/.test(title)) return { title: null, body: block };
    return { title, body: block.slice(nl + 1).trim() };
  });
}

function fmtDate(d: string | null) {
  if (!d) return "—";
  const dt = new Date(d);
  return Number.isNaN(dt.getTime()) ? d : dt.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
}

export default function SummarySection({ analysis }: { analysis: FullAnalysis }) {
  const companyId = analysis.company_info?.stock_id || analysis.stock_id;
  const [summary, setSummary] = useState<{ about: string | null; key_points: string | null; retrieved_at: string } | null>(null);
  const [insiders, setInsiders] = useState<InsiderActivityItem[]>([]);
  const [segments, setSegments] = useState<BusinessSegmentItem[]>([]);
  const [brands, setBrands] = useState<BrandItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!companyId) { setLoading(false); return; }
    setLoading(true);
    Promise.all([
      api.getCompanySummary(companyId).catch(() => ({ summary: null })),
      api.getInsiderActivity(companyId).catch(() => ({ transactions: [] })),
      api.getBusinessSegments(companyId).catch(() => ({ segments: [] })),
      api.getBrands(companyId).catch(() => ({ brands: [] })),
    ]).then(([s, i, seg, br]) => {
      setSummary(s.summary);
      setInsiders(i.transactions.slice(0, 8));
      setSegments(seg.segments);
      setBrands(br.brands);
    }).finally(() => setLoading(false));
  }, [companyId]);

  if (loading) {
    return <div className="py-12 flex items-center justify-center"><div className="spinner" /></div>;
  }

  const hasSummary = summary && (summary.about || (summary.key_points && !isKeyPointsPaywall(summary.key_points)));
  if (!hasSummary && segments.length === 0 && insiders.length === 0 && brands.length === 0) {
    return (
      <div className="card-rich p-6 text-center text-sm" style={{ color: "var(--text-muted)" }}>
        No company summary available yet — it's ingested from Screener.in/TradingView during analysis.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {segments.length > 0 && (
        <ChartCard eyebrow="Business Segments" title="Segment revenue by fiscal year">
          <SegmentRevenueChart segments={segments} />
        </ChartCard>
      )}

      <BrandPortfolio brands={brands} />

      {summary?.about && (
        <div className="card-rich p-5">
          <p className="eyebrow mb-2">About</p>
          <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
            {cleanScreenerText(summary.about)}
          </p>
        </div>
      )}

      {summary?.key_points && !isKeyPointsPaywall(summary.key_points) && (
        <div className="card-rich p-5">
          <p className="eyebrow mb-3">Key Points</p>
          <div className="space-y-4">
            {splitKeyPointSections(cleanScreenerText(summary.key_points)).map((section, i) => (
              <div key={i}>
                {section.title && (
                  <p className="text-sm font-semibold mb-1" style={{ color: "var(--text-primary)" }}>
                    {section.title}
                  </p>
                )}
                <p className="text-sm leading-relaxed whitespace-pre-line" style={{ color: "var(--text-secondary)" }}>
                  {section.body}
                </p>
              </div>
            ))}
          </div>
          <p className="text-xs mt-4 pt-3" style={{ color: "var(--text-dim)", borderTop: "1px solid var(--border-subtle)" }}>
            Source: Screener.in · updated {fmtDate(summary?.retrieved_at ?? null)}
          </p>
        </div>
      )}

      {insiders.length > 0 && (
        <div className="card-rich overflow-hidden">
          <div className="px-4 py-3" style={{ borderBottom: "1px solid var(--border-subtle)" }}>
            <span className="eyebrow">Recent Insider Activity</span>
          </div>
          <div className="overflow-x-auto">
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                  {["Date", "Insider", "Position", "Type", "Shares", "Value"].map((h) => (
                    <th key={h} style={{
                      padding: "6px 12px", fontSize: 11, fontWeight: 600, textTransform: "uppercase",
                      letterSpacing: "0.06em", color: "var(--text-dim)", background: "var(--bg-input)",
                      textAlign: h === "Date" || h === "Insider" || h === "Position" ? "left" : "right",
                    }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {insiders.map((t, i) => (
                  <tr key={i} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                    <td style={{ padding: "8px 12px", fontSize: 12, color: "var(--text-secondary)" }}>{fmtDate(t.date)}</td>
                    <td style={{ padding: "8px 12px", fontSize: 12, color: "var(--text-primary)", fontWeight: 500 }}>{t.insider_name || "—"}</td>
                    <td style={{ padding: "8px 12px", fontSize: 12, color: "var(--text-secondary)" }}>{t.position || "—"}</td>
                    <td style={{ padding: "8px 12px", fontSize: 12, textAlign: "right", color: "var(--text-secondary)" }}>{t.ownership_type || "—"}</td>
                    <td style={{ padding: "8px 12px", fontSize: 12, textAlign: "right", color: "var(--text-primary)", fontVariantNumeric: "tabular-nums" }}>
                      {t.shares !== null ? t.shares.toLocaleString("en-IN") : "—"}
                    </td>
                    <td style={{ padding: "8px 12px", fontSize: 12, textAlign: "right", color: "var(--text-primary)", fontVariantNumeric: "tabular-nums" }}>
                      {t.value !== null ? `₹${t.value.toLocaleString("en-IN")}` : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
