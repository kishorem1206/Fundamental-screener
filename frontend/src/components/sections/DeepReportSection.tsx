import { useCallback, useEffect, useState } from "react";
import { api } from "../../api";
import type { FullAnalysis } from "../../types";
import DeepReportButton from "../DeepReportButton";

type Lens = { dcf: number | null; sotp: number | null; relative: number | null; average: number | null; gap: number | null };
export interface DeepReportSummary {
  symbol: string; company_name: string; generated: string; basis: string | null; classification: string[]; cutoff: string | null;
  headline: string | null;
  latest_year: { label: string; revenue: number | null; profit: number | null; revenue_growth: number | null } | null;
  evidence: { facts: number; reported: number; calculated: number; verified: number; failed: number }; sources: number;
  segments: { name: string; revenue: number | null; result: number | null; margin: number | null; revenue_share: number | null; result_share: number | null }[];
  sector_measures: { label: string; value: number; unit: string; quote: string; kind: string; page: number; period: string; period_kind: string;
                     earlier: number | null; earlier_period: string | null; earlier_date: string | null; by_model: boolean; date: string }[];
  outlook: { text: string; page: number; quarter: string | null }[];
  questions: { q: string; a: string }[]; narrative_by: string;
  risks: { kind: string; severity: string; text: string }[];
  triggers: { bullish: string[]; bearish: string[]; watch: string[] };
  exhibits: { n: number; title: string; unit: string; note: string; svg: string }[];
  valuation: null | {
    price: number; price_date: string; is_lender: boolean; by_segment: boolean; overrides: number; weights: Record<string, number> | null;
    scenarios: Record<"Bear" | "Base" | "Bull", Lens>;
    forecast: { label: string; revenue: number; profit: number; eps: number }[];
    breaks: { name: string; growth: number; history_growth: number; margin: number; history_margin: number }[];
    bridge: { label: string; value: number; basis: string }[];
  };
}

const num = (v: number | null | undefined, digits = 0) =>
  v === null || v === undefined ? "–" : v.toLocaleString("en-IN", { maximumFractionDigits: digits, minimumFractionDigits: digits });
const pct = (v: number | null | undefined, digits = 1) => (v === null || v === undefined ? "–" : `${(v * 100).toFixed(digits)}%`);
const signed = (v: number | null | undefined) => (v === null || v === undefined ? "–" : `${v >= 0 ? "+" : ""}${(v * 100).toFixed(1)}%`);
const day = (iso: string) => new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });

function measure(value: number, unit: string): string {
  if (unit === "INR crore") return `₹${num(value)} crore`;
  if (unit === "%") return `${value.toFixed(1)}%`;
  if (unit === "INR") return `₹${num(value, value < 100 ? 2 : 0)}`;
  if (unit === "count" || unit === "units") return num(value);
  return `${num(value, value % 1 ? 2 : 0)} ${unit}`;
}
const COVERS: Record<string, string> = { level: "Level", quarter: "Quarter", year: "Full year", month: "Month", "half year": "Half year",
                                         "nine months": "Nine months", "year to date": "Year to date" };
const SEVERITY: Record<string, string> = { HIGH: "#d9694f", MEDIUM: "#c9a227", LOW: "#4fb3a0" };

const th: React.CSSProperties = { textAlign: "right", padding: "8px 10px", fontSize: 11, letterSpacing: "0.06em", textTransform: "uppercase",
                                  color: "var(--text-muted)", borderBottom: "1px solid var(--border-subtle)", fontWeight: 600 };
const td: React.CSSProperties = { textAlign: "right", padding: "8px 10px", fontSize: 13, borderBottom: "1px solid var(--border-subtle)", color: "var(--text-primary)" };
const left: React.CSSProperties = { textAlign: "left" };

function Card({ eyebrow, title, children }: { eyebrow: string; title?: string; children: React.ReactNode }) {
  return (
    <div className="card-rich p-6">
      <p className="eyebrow">{eyebrow}</p>
      {title && <h2 className="text-lg font-semibold mb-3" style={{ color: "var(--text-primary)" }}>{title}</h2>}
      {children}
    </div>
  );
}

/** The deep report for this stock: built from exchange filings alongside the full analysis, shown here and downloadable as PDF and Excel. */
export default function DeepReportSection({ analysis }: { analysis: FullAnalysis }) {
  const symbol = analysis.company_info?.symbol;
  const [summary, setSummary] = useState<DeepReportSummary | null>(null);
  const [state, setState] = useState<"loading" | "ready" | "not-built" | "error">("loading");
  const [error, setError] = useState("");
  const [showPdf, setShowPdf] = useState(false);

  const load = useCallback(async () => {
    if (!symbol) return;
    setState("loading");
    try {
      setSummary(await api.bieSummary(symbol));
      setState("ready");
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : "";
      if (/not been built/i.test(message) || /409/.test(message)) setState("not-built");
      else { setError(message || "Could not load the deep report"); setState("error"); }
    }
  }, [symbol]);

  useEffect(() => { load(); }, [load]);

  if (!symbol) return null;
  const v = summary?.valuation ?? null;

  return (
    <div className="space-y-6">
      <div className="card-rich p-6">
        <p className="eyebrow">Deep report</p>
        <h2 className="text-xl font-semibold mb-1" style={{ color: "var(--text-primary)" }}>Sector first, then the company, from the filings themselves</h2>
        <p className="text-sm mb-4" style={{ color: "var(--text-secondary)", maxWidth: 760 }}>
          Built from exchange filings alongside this analysis: results, the annual report, presentations, press releases and call transcripts.
          Every figure is cited to its page and re-checked against the archived copy. The forecast and valuation are rule-based and can be
          challenged on the Assumptions page.
        </p>
        <DeepReportButton symbol={symbol} onBuilt={load} />
        {state === "loading" && <div className="text-sm mt-4" style={{ color: "var(--text-muted)" }}>Loading the report…</div>}
        {state === "not-built" && (
          <div className="text-sm mt-4" style={{ color: "var(--text-secondary)" }}>
            No deep report is on file for {symbol} yet. A build starts automatically with each full analysis and takes a few minutes; its
            progress shows above, and this page fills in when it finishes.
          </div>
        )}
        {state === "error" && <div className="text-sm mt-4" style={{ color: "var(--accent-red)" }}>{error}</div>}
      </div>

      {summary && state === "ready" && (
        <>
          <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
            {[
              { k: summary.latest_year ? `${summary.latest_year.label} revenue` : "Revenue", v: summary.latest_year ? `₹${num(summary.latest_year.revenue)} cr` : "–",
                n: summary.latest_year ? `${signed(summary.latest_year.revenue_growth)} on the year` : "" },
              { k: summary.latest_year ? `${summary.latest_year.label} profit after tax` : "Profit", v: summary.latest_year ? `₹${num(summary.latest_year.profit)} cr` : "–",
                n: `${summary.basis ?? ""} accounts` },
              { k: "Blended reference value", v: v?.scenarios.Base.average != null ? `₹${num(v.scenarios.Base.average)}` : "–",
                n: v ? `${signed(v.scenarios.Base.gap)} against ₹${num(v.price, 2)}` : "No model" },
              { k: "Sourced facts", v: num(summary.evidence.facts), n: `${num(summary.evidence.verified)} verified · ${summary.sources} documents` },
            ].map((c) => (
              <div key={c.k} className="card-rich p-5">
                <div className="text-xs" style={{ color: "var(--text-muted)" }}>{c.k}</div>
                <div className="text-2xl font-semibold mt-1" style={{ color: "var(--text-primary)" }}>{c.v}</div>
                <div className="text-xs mt-1" style={{ color: "var(--text-secondary)" }}>{c.n}</div>
              </div>
            ))}
          </div>

          {summary.headline && (
            <div className="card-rich p-6" style={{ borderLeft: "3px solid var(--accent-gold-bright)" }}>
              <p className="text-lg" style={{ color: "var(--text-primary)" }}>{summary.headline}</p>
              <p className="text-xs mt-2" style={{ color: "var(--text-muted)" }}>
                {summary.classification.join(" · ")} · results through {summary.cutoff ? day(summary.cutoff) : "–"} · generated {day(summary.generated)}
              </p>
            </div>
          )}

          {v && (
            <Card eyebrow={`Valuation · price ₹${num(v.price, 2)} on ${day(v.price_date)}`} title="Three ways of valuing the forecast">
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse" }}>
                  <thead><tr>
                    <th style={{ ...th, ...left }}>₹ per share</th><th style={th}>Discounted cash flow</th><th style={th}>Sum of the parts</th>
                    <th style={th}>Peer multiple</th><th style={th}>Blended reference</th><th style={th}>Against price</th>
                  </tr></thead>
                  <tbody>
                    {(["Bear", "Base", "Bull"] as const).map((name) => {
                      const s = v.scenarios[name];
                      return (
                        <tr key={name} style={name === "Base" ? { fontWeight: 600, background: "rgba(255,255,255,0.04)" } : undefined}>
                          <td style={{ ...td, ...left }}>{name}</td><td style={td}>{num(s.dcf)}</td><td style={td}>{num(s.sotp)}</td>
                          <td style={td}>{num(s.relative)}</td><td style={td}>{num(s.average)}</td>
                          <td style={{ ...td, color: (s.gap ?? 0) >= 0 ? "#4fb3a0" : "#d9694f" }}>{signed(s.gap)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <p className="text-xs mt-3" style={{ color: "var(--text-muted)" }}>
                A mechanical model, not a recommendation. The methods are expected to disagree; the spread is the uncertainty.
                {v.is_lender ? " For a lender or insurer only the peer multiple applies." : ""}
                {v.overrides ? ` ${v.overrides} analyst override${v.overrides > 1 ? "s" : ""} in force.` : " No analyst overrides."}
              </p>
              {v.breaks.length > 0 && (
                <p className="text-sm mt-3" style={{ color: "var(--accent-gold-bright)" }}>
                  Break from history: {v.breaks.map((b) => `${b.name} (revenue ${signed(b.growth)} so far this year against ${signed(b.history_growth)} implied by the record; margin ${pct(b.history_margin)} → ${pct(b.margin)})`).join("; ")}.
                </p>
              )}
              <div className="mt-4" style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse" }}>
                  <thead><tr><th style={{ ...th, ...left }}>Base case, ₹ crore</th>{v.forecast.map((y) => <th key={y.label} style={th}>{y.label}</th>)}</tr></thead>
                  <tbody>
                    <tr><td style={{ ...td, ...left }}>Revenue</td>{v.forecast.map((y) => <td key={y.label} style={td}>{num(y.revenue)}</td>)}</tr>
                    <tr><td style={{ ...td, ...left }}>Profit after tax</td>{v.forecast.map((y) => <td key={y.label} style={td}>{num(y.profit)}</td>)}</tr>
                    <tr><td style={{ ...td, ...left }}>Earnings per share (₹)</td>{v.forecast.map((y) => <td key={y.label} style={td}>{num(y.eps, 2)}</td>)}</tr>
                  </tbody>
                </table>
              </div>
            </Card>
          )}

          {summary.sector_measures.length > 0 && (
            <Card eyebrow="Sector measures" title="The operating figures this business is judged on, as the company states them">
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse" }}>
                  <thead><tr>
                    <th style={{ ...th, ...left }}>Measure</th><th style={th}>Latest</th><th style={{ ...th, ...left }}>Covers</th>
                    <th style={{ ...th, ...left }}>As stated</th><th style={th}>Filed</th><th style={th}>Same measure, earlier</th>
                  </tr></thead>
                  <tbody>
                    {summary.sector_measures.map((m) => (
                      <tr key={m.label}>
                        <td style={{ ...td, ...left, fontWeight: 600 }}>{m.label}{m.by_model && <span className="badge badge-gray text-xs ml-2">Read by AI</span>}</td>
                        <td style={{ ...td, whiteSpace: "nowrap" }}>{measure(m.value, m.unit)}</td>
                        <td style={{ ...td, ...left }}>{COVERS[m.period_kind] ?? "Not stated"}<div style={{ fontSize: 11, color: "var(--text-muted)" }}>{m.period}</div></td>
                        <td style={{ ...td, ...left, color: "var(--text-secondary)" }}>“{m.quote}” <span style={{ color: "var(--text-muted)" }}>({m.kind}, p. {m.page})</span></td>
                        <td style={{ ...td, whiteSpace: "nowrap" }}>{day(m.date)}</td>
                        <td style={{ ...td, whiteSpace: "nowrap" }}>{m.earlier != null ? measure(m.earlier, m.unit) : "–"}
                          {m.earlier_period && <div style={{ fontSize: 11, color: "var(--text-muted)" }}>{m.earlier_period}</div>}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="text-xs mt-3" style={{ color: "var(--text-muted)" }}>
                The company's own statements, not audited figures. An earlier figure is shown only when it covers the same kind of period.
              </p>
            </Card>
          )}

          <Card eyebrow={summary.narrative_by === "llm" ? "Assessment · written by the language model, every number checked" : "Assessment · written by fixed rules"} title="Five questions">
            <div className="space-y-4">
              {summary.questions.map((item) => (
                <div key={item.q}>
                  <div className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{item.q}</div>
                  <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>{item.a}</p>
                </div>
              ))}
            </div>
          </Card>

          {summary.risks.length > 0 && (
            <Card eyebrow="Risk register" title="Each risk is a threshold crossed by a figure in the report">
              <div className="space-y-2">
                {summary.risks.map((risk) => (
                  <div key={risk.kind + risk.text} className="flex gap-3 text-sm">
                    <span style={{ color: SEVERITY[risk.severity.toUpperCase()] ?? "var(--text-muted)", fontWeight: 700, minWidth: 64, textTransform: "uppercase", fontSize: 11, paddingTop: 2 }}>{risk.severity}</span>
                    <span style={{ color: "var(--text-primary)", fontWeight: 600, minWidth: 190 }}>{risk.kind}</span>
                    <span style={{ color: "var(--text-secondary)" }}>{risk.text}</span>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {summary.outlook.length > 0 && (
            <Card eyebrow="From the earnings call" title="Forward-looking statements with a figure">
              <div className="space-y-3">
                {summary.outlook.map((o) => (
                  <p key={o.text.slice(0, 60)} className="text-sm" style={{ color: "var(--text-secondary)" }}>“{o.text}” <span style={{ color: "var(--text-muted)" }}>— transcript p. {o.page}</span></p>
                ))}
              </div>
            </Card>
          )}

          {summary.exhibits.length > 0 && (
            <Card eyebrow="Exhibits" title="History and the Base-case forecast">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                {summary.exhibits.map((e) => (
                  <figure key={e.n} style={{ margin: 0, background: "#fffdf8", borderRadius: 14, padding: 14 }}>
                    <div style={{ fontWeight: 600, fontSize: 13, color: "#123b38" }}>Exhibit {e.n}. {e.title}</div>
                    <div style={{ fontSize: 11, color: "#66716d", marginBottom: 4 }}>{e.unit}</div>
                    <div dangerouslySetInnerHTML={{ __html: e.svg }} />
                    <figcaption style={{ fontSize: 11, color: "#66716d", marginTop: 4 }}>{e.note}</figcaption>
                  </figure>
                ))}
              </div>
            </Card>
          )}

          <div className="card-rich p-6">
            <div className="flex items-center justify-between flex-wrap gap-3">
              <div>
                <p className="eyebrow">The full document</p>
                <h2 className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>Read the PDF here</h2>
              </div>
              <button onClick={() => setShowPdf((x) => !x)} className="px-3 py-2 rounded-md text-sm font-semibold"
                      style={{ border: "1px solid var(--border-subtle)", color: "var(--text-primary)", background: "var(--bg-input)" }}>
                {showPdf ? "Hide the PDF" : "Show the PDF on this page"}
              </button>
            </div>
            {showPdf && (
              <iframe title={`${symbol} deep report`} src={`/api/bie/${symbol}/report.pdf`}
                      style={{ width: "100%", height: "85vh", border: "1px solid var(--border-subtle)", borderRadius: 12, marginTop: 16, background: "#fff" }} />
            )}
          </div>
        </>
      )}
    </div>
  );
}
