import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import DeepReportButton from "./DeepReportButton";

export interface Lenses {
  revenue: number; profit_before_tax: number; profit_after_tax: number; free_cash_flow: number | null;
  dcf: number | null; sotp: number | null; peer_multiple: number | null; average: number | null;
}
interface Cell { year: number; system: number; active: number; override_id: string | null }
interface Unit { name: string; revenue_growth: Cell[]; margin: Cell[] }
interface Scalar { metric: string; unit: string; system: number; active: number; override_id: string | null }
interface Override { id: string | null; metric: string; unit: string; scenario: string; year: number | null; system: number; value: number; reason: string }
export interface ControlCentre {
  skipped?: string; scenario: string; fiscal_years: number[]; units: Unit[]; scalars: Scalar[]; overrides: Override[];
  system_assumptions: number; analyst_overrides: number; before: Lenses; after: Lenses; price: number;
}
export interface HistoryRow {
  id: string; metric: string; unit: string; scenario: string; fiscal_year: number | null; value: number; reason: string;
  created_at: string; active: boolean; superseded_at: string | null; superseded_reason: string | null;
}
export interface RankRow { unit: string; metric: string; test: string; low: number; high: number; swing_pct: number }

interface Target { metric: string; unit: string; year: number | null; system: number; active: number }

const MULTIPLES = new Set(["beta", "peer_price_to_earnings", "ev_ebit_multiple"]);
const label = (m: string) => m.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase());
const show = (metric: string, v: number) => (MULTIPLES.has(metric) ? `${v.toFixed(2)}×` : `${(v * 100).toFixed(1)}%`);
const crore = (v: number | null) => (v == null ? "–" : Math.round(v / 1e7).toLocaleString("en-IN"));
const rupee = (v: number | null) => (v == null ? "–" : Math.round(v).toLocaleString("en-IN"));
const fy = (y: number) => `FY${String(y).slice(2)}`;

const th: React.CSSProperties = { textAlign: "right", padding: "8px 10px", fontSize: 11, letterSpacing: "0.06em", textTransform: "uppercase", color: "var(--text-muted)", borderBottom: "1px solid var(--border-subtle)" };
const td: React.CSSProperties = { textAlign: "right", padding: "8px 10px", borderBottom: "1px solid rgba(255,255,255,0.06)", fontVariantNumeric: "tabular-nums" };
const left: React.CSSProperties = { textAlign: "left" };

export default function AssumptionCenter() {
  const [input, setInput] = useState("ITC");
  const [symbol, setSymbol] = useState("ITC");
  const [scenario, setScenario] = useState("Base");
  const [data, setData] = useState<ControlCentre | null>(null);
  const [history, setHistory] = useState<HistoryRow[]>([]);
  const [ranking, setRanking] = useState<RankRow[] | null>(null);
  const [rankBusy, setRankBusy] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [target, setTarget] = useState<Target | null>(null);
  const [form, setForm] = useState({ value: "", reason: "", allYears: false, thisScenario: false, evidence: "" });
  const [trial, setTrial] = useState<(Lenses & { value: number })[] | null>(null);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const [d, h] = await Promise.all([api.bieAssumptions(symbol, scenario), api.bieOverrideHistory(symbol)]);
      setData(d); setHistory(h.history);
    } catch (e) {
      setData(null); setError(e instanceof Error ? e.message : "Could not load assumptions");
    } finally { setLoading(false); }
  }, [symbol, scenario]);

  useEffect(() => { load(); }, [load]);
  const [reports, setReports] = useState<{ symbol: string; company_name: string; built_at: string }[]>([]);
  const loadReports = useCallback(() => { api.bieReports().then((r) => setReports(r.reports)).catch(() => {}); }, []);
  useEffect(() => { loadReports(); }, [loadReports]);
  useEffect(() => { setRanking(null); }, [symbol]);

  const open = (t: Target) => {
    setTarget(t); setTrial(null);
    setForm({ value: (MULTIPLES.has(t.metric) ? t.active : t.active * 100).toFixed(MULTIPLES.has(t.metric) ? 2 : 1), reason: "", allYears: false, thisScenario: false, evidence: "" });
  };

  const parsed = () => {
    const n = parseFloat(form.value);
    if (Number.isNaN(n) || !target) return null;
    return MULTIPLES.has(target.metric) ? n : n / 100;
  };
  const isPath = target ? target.year !== null : false;
  const scope = () => ({
    unit: target!.unit,
    scenario: isPath && form.thisScenario ? scenario : "All",
    fiscal_year: isPath && !form.allYears ? target!.year : null,
  });

  const save = async () => {
    const value = parsed();
    if (value === null || !target) return;
    setSaving(true); setError("");
    try {
      await api.bieSetOverride(symbol, { metric: target.metric, value, reason: form.reason, evidence_url: form.evidence || null, ...scope() });
      setTarget(null); await load();
    } catch (e) { setError(e instanceof Error ? e.message : "Could not save"); } finally { setSaving(false); }
  };

  const tryRange = async () => {
    const value = parsed();
    if (value === null || !target) return;
    const step = MULTIPLES.has(target.metric) ? Math.max(Math.abs(value) * 0.1, 0.1) : 0.025;
    const values = [-2, -1, 0, 1, 2].map((k) => +(value + k * step).toFixed(4));
    const s = scope();
    const params: Record<string, string> = { metric: target.metric, values: values.join(","), unit: s.unit, scenario: s.scenario };
    if (s.fiscal_year) params.fiscal_year = String(s.fiscal_year);
    try { setTrial((await api.bieWhatIf(symbol, params)).results); } catch (e) { setError(e instanceof Error ? e.message : "What-if failed"); }
  };

  const reset = async (id: string) => { await api.bieResetOverride(symbol, id); await load(); };

  const cell = (unit: string, metric: string, c: Cell) => (
    <td key={c.year} style={{ ...td, cursor: "pointer", color: c.override_id ? "var(--accent-gold-bright)" : "var(--text-primary)", fontWeight: c.override_id ? 600 : 400 }}
        title={c.override_id ? `Model: ${show(metric, c.system)}` : "Click to override"}
        onClick={() => open({ metric, unit, year: c.year, system: c.system, active: c.active })}>
      {show(metric, c.active)}
      {c.override_id && <div style={{ fontSize: 10, color: "var(--text-muted)", fontWeight: 400 }}>model {show(metric, c.system)}</div>}
    </td>
  );

  const lensRow = (name: string, l: Lenses, strong = false) => (
    <tr style={strong ? { fontWeight: 600, background: "rgba(255,255,255,0.04)" } : undefined}>
      <td style={{ ...td, ...left }}>{name}</td><td style={td}>{crore(l.revenue)}</td><td style={td}>{crore(l.profit_after_tax)}</td>
      <td style={td}>{crore(l.free_cash_flow)}</td><td style={td}>{rupee(l.dcf)}</td><td style={td}>{rupee(l.sotp)}</td>
      <td style={td}>{rupee(l.peer_multiple)}</td><td style={td}>{rupee(l.average)}</td>
    </tr>
  );

  return (
    <div className="space-y-6 fade-in">
      <div className="card-rich p-6">
        <p className="eyebrow">Assumption control centre</p>
        <h1 className="text-xl font-semibold mb-1" style={{ color: "var(--text-primary)" }}>Challenge the model's assumptions</h1>
        <p className="text-sm mb-4" style={{ color: "var(--text-secondary)", maxWidth: 720 }}>
          The model's estimates are the default. Click any figure to override it; the forecast and every valuation recalculate.
          An override needs a reason, is never overwritten, and can be reset to the model at any time.
        </p>
        <form className="flex items-center gap-3 flex-wrap" onSubmit={(e) => { e.preventDefault(); setSymbol(input.trim().toUpperCase()); }}>
          <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="NSE symbol" className="px-3 py-2 rounded-md text-sm"
                 style={{ background: "var(--bg-input)", border: "1px solid var(--border-subtle)", color: "var(--text-primary)", width: 160 }} />
          <button type="submit" className="px-3 py-2 rounded-md text-sm font-semibold" style={{ background: "var(--accent-blue)", color: "#10182b" }}>Load</button>
          <select value={scenario} onChange={(e) => setScenario(e.target.value)} className="px-3 py-2 rounded-md text-sm"
                  style={{ background: "var(--bg-input)", border: "1px solid var(--border-subtle)", color: "var(--text-primary)" }}>
            {["Bear", "Base", "Bull"].map((s) => <option key={s} value={s}>{s} case</option>)}
          </select>
          {data && !data.skipped && (
            <span className="text-sm" style={{ color: "var(--text-muted)", marginLeft: "auto" }}>
              {data.system_assumptions} model assumptions · <b style={{ color: "var(--accent-gold-bright)" }}>{data.analyst_overrides} analyst overrides</b>
            </span>
          )}
        </form>
        {error && <div className="text-sm mt-3" style={{ color: "var(--accent-red)" }}>{error}</div>}
        {loading && <div className="text-sm mt-3" style={{ color: "var(--text-muted)" }}>Recalculating…</div>}
        {data?.skipped && <div className="text-sm mt-3" style={{ color: "var(--text-secondary)" }}>No model for {symbol} yet: {data.skipped}. Build its deep report below, then the assumptions appear here.</div>}
        {symbol && <div className="mt-4"><DeepReportButton symbol={symbol} onBuilt={() => { load(); loadReports(); }} /></div>}
        {reports.length > 0 && (
          <div className="mt-5">
            <p className="eyebrow">Deep reports on file</p>
            <div className="flex gap-2 flex-wrap mt-2">
              {reports.map((r) => (
                <button key={r.symbol} onClick={() => { setInput(r.symbol); setSymbol(r.symbol); }} title={`${r.company_name} · built ${new Date(r.built_at).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}`}
                        className="px-2 py-1 rounded-md text-xs"
                        style={{ border: "1px solid var(--border-subtle)", color: r.symbol === symbol ? "var(--accent-gold-bright)" : "var(--text-secondary)", background: "var(--bg-input)" }}>
                  {r.symbol}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {data && !data.skipped && (
        <>
          <div className="card-rich p-6">
            <p className="eyebrow">Effect of the overrides · {data.scenario} case · price ₹{data.price.toFixed(2)}</p>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
              <thead><tr>
                <th style={{ ...th, ...left }}></th><th style={th}>Year-1 revenue (₹ cr)</th><th style={th}>Profit after tax</th><th style={th}>Free cash flow</th>
                <th style={th}>Cash-flow value (₹)</th><th style={th}>Sum of parts</th><th style={th}>Peer multiple</th><th style={th}>Average</th>
              </tr></thead>
              <tbody>{lensRow("Model alone", data.before)}{lensRow("With overrides", data.after, true)}</tbody>
            </table>
          </div>

          <div className="card-rich p-6" style={{ overflowX: "auto" }}>
            <p className="eyebrow">Growth and margin by segment and year</p>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
              <thead><tr><th style={{ ...th, ...left }}>Segment</th><th style={{ ...th, ...left }}>Metric</th>{data.fiscal_years.map((y) => <th key={y} style={th}>{fy(y)}</th>)}</tr></thead>
              <tbody>
                {data.units.flatMap((u) => ([["revenue_growth", u.revenue_growth], ["margin", u.margin]] as [string, Cell[]][]).map(([metric, cells]) => (
                  <tr key={u.name + metric}>
                    <td style={{ ...td, ...left, color: metric === "margin" ? "transparent" : "var(--text-primary)" }}>{u.name}</td>
                    <td style={{ ...td, ...left, color: "var(--text-secondary)" }}>{label(metric)}</td>
                    {cells.map((c) => cell(u.name, metric, c))}
                  </tr>
                )))}
              </tbody>
            </table>
          </div>

          <div className="card-rich p-6">
            <p className="eyebrow">Company-level inputs and segment multiples</p>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
              <thead><tr><th style={{ ...th, ...left }}>Input</th><th style={{ ...th, ...left }}>Applies to</th><th style={th}>Model</th><th style={th}>In force</th><th style={th}></th></tr></thead>
              <tbody>
                {data.scalars.map((s) => (
                  <tr key={s.metric + s.unit}>
                    <td style={{ ...td, ...left }}>{label(s.metric)}</td><td style={{ ...td, ...left, color: "var(--text-secondary)" }}>{s.unit}</td>
                    <td style={td}>{show(s.metric, s.system)}</td>
                    <td style={{ ...td, color: s.override_id ? "var(--accent-gold-bright)" : undefined, fontWeight: s.override_id ? 600 : 400 }}>{show(s.metric, s.active)}</td>
                    <td style={td}><button onClick={() => open({ metric: s.metric, unit: s.unit, year: null, system: s.system, active: s.active })} style={{ color: "var(--accent-gold-bright)" }}>Override</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {target && (
            <div className="card-rich p-6" style={{ border: "1px solid var(--border-accent)" }}>
              <p className="eyebrow">Override</p>
              <h2 className="text-lg font-semibold mb-3" style={{ color: "var(--text-primary)" }}>
                {label(target.metric)} · {target.unit}{target.year ? ` · ${fy(target.year)}` : ""}
              </h2>
              <div className="text-sm mb-3" style={{ color: "var(--text-secondary)" }}>Model estimate: <b>{show(target.metric, target.system)}</b></div>
              <div className="flex gap-4 flex-wrap items-center mb-3">
                <label className="text-sm" style={{ color: "var(--text-secondary)" }}>Your value ({MULTIPLES.has(target.metric) ? "×" : "%"})
                  <input value={form.value} onChange={(e) => setForm({ ...form, value: e.target.value })} className="ml-2 px-3 py-2 rounded-md text-sm"
                         style={{ background: "var(--bg-input)", border: "1px solid var(--border-subtle)", color: "var(--text-primary)", width: 110 }} />
                </label>
                {isPath && <>
                  <label className="text-sm" style={{ color: "var(--text-secondary)" }}><input type="checkbox" checked={form.allYears} onChange={(e) => setForm({ ...form, allYears: e.target.checked })} /> every forecast year</label>
                  <label className="text-sm" style={{ color: "var(--text-secondary)" }}><input type="checkbox" checked={form.thisScenario} onChange={(e) => setForm({ ...form, thisScenario: e.target.checked })} /> {scenario} case only</label>
                </>}
              </div>
              <textarea value={form.reason} onChange={(e) => setForm({ ...form, reason: e.target.value })} rows={3} placeholder="Reason (required): why is the model's estimate wrong here?"
                        className="w-full px-3 py-2 rounded-md text-sm mb-3" style={{ background: "var(--bg-input)", border: "1px solid var(--border-subtle)", color: "var(--text-primary)" }} />
              <input value={form.evidence} onChange={(e) => setForm({ ...form, evidence: e.target.value })} placeholder="Evidence link (optional)"
                     className="w-full px-3 py-2 rounded-md text-sm mb-3" style={{ background: "var(--bg-input)", border: "1px solid var(--border-subtle)", color: "var(--text-primary)" }} />
              <div className="flex gap-3">
                <button onClick={save} disabled={saving || form.reason.trim().length < 10 || parsed() === null} className="px-3 py-2 rounded-md text-sm font-semibold"
                        style={{ background: "var(--accent-blue)", color: "#10182b", opacity: saving || form.reason.trim().length < 10 ? 0.5 : 1 }}>Save override</button>
                <button onClick={tryRange} className="px-3 py-2 rounded-md text-sm" style={{ border: "1px solid var(--border-subtle)", color: "var(--text-primary)" }}>Test a range first</button>
                <button onClick={() => setTarget(null)} className="px-3 py-2 rounded-md text-sm" style={{ color: "var(--text-muted)" }}>Cancel</button>
              </div>
              {trial && (
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13, marginTop: 16 }}>
                  <thead><tr><th style={{ ...th, ...left }}>If set to</th><th style={th}>Profit after tax (₹ cr)</th><th style={th}>Cash-flow value (₹)</th><th style={th}>Sum of parts</th><th style={th}>Peer multiple</th><th style={th}>Average</th></tr></thead>
                  <tbody>{trial.map((t) => (
                    <tr key={t.value}><td style={{ ...td, ...left }}>{show(target.metric, t.value)}</td><td style={td}>{crore(t.profit_after_tax)}</td><td style={td}>{rupee(t.dcf)}</td><td style={td}>{rupee(t.sotp)}</td><td style={td}>{rupee(t.peer_multiple)}</td><td style={td}>{rupee(t.average)}</td></tr>
                  ))}</tbody>
                </table>
              )}
            </div>
          )}

          <div className="card-rich p-6">
            <p className="eyebrow">Overrides in force</p>
            {data.overrides.length === 0 ? <div className="text-sm" style={{ color: "var(--text-muted)" }}>None. Every assumption is the model's own estimate.</div> : (
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                <thead><tr><th style={{ ...th, ...left }}>Assumption</th><th style={{ ...th, ...left }}>Applies to</th><th style={th}>Model</th><th style={th}>Yours</th><th style={{ ...th, ...left }}>Reason</th><th style={th}></th></tr></thead>
                <tbody>{data.overrides.map((o) => (
                  <tr key={o.id ?? o.metric + o.unit}>
                    <td style={{ ...td, ...left }}>{label(o.metric)}</td>
                    <td style={{ ...td, ...left, color: "var(--text-secondary)" }}>{o.unit}{o.year ? `, ${fy(o.year)}` : ""}{o.scenario !== "All" ? `, ${o.scenario}` : ""}</td>
                    <td style={td}>{show(o.metric, o.system)}</td><td style={{ ...td, color: "var(--accent-gold-bright)", fontWeight: 600 }}>{show(o.metric, o.value)}</td>
                    <td style={{ ...td, ...left, color: "var(--text-secondary)", maxWidth: 360 }}>{o.reason}</td>
                    <td style={td}>{o.id && <button onClick={() => reset(o.id!)} style={{ color: "var(--accent-red)" }}>Reset to model</button>}</td>
                  </tr>
                ))}</tbody>
              </table>
            )}
          </div>

          <div className="card-rich p-6">
            <p className="eyebrow">Which assumptions matter most</p>
            {ranking === null ? (
              <button disabled={rankBusy} onClick={async () => { setRankBusy(true); try { setRanking((await api.bieRanking(symbol)).ranking); } finally { setRankBusy(false); } }}
                      className="px-3 py-2 rounded-md text-sm" style={{ border: "1px solid var(--border-subtle)", color: "var(--text-primary)" }}>
                {rankBusy ? "Testing each assumption…" : "Rank assumptions by effect on value"}
              </button>
            ) : ranking.map((r) => {
              const max = Math.max(...ranking.map((x) => x.swing_pct));
              return (
                <div key={r.unit + r.metric} style={{ display: "grid", gridTemplateColumns: "300px 1fr", alignItems: "center", gap: 12, padding: "5px 0", fontSize: 13 }}>
                  <div style={{ color: "var(--text-secondary)" }}>{r.unit}: {r.test}</div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span style={{ height: 12, width: `${(r.swing_pct / max) * 70}%`, minWidth: 2, background: "var(--accent-blue)", borderRadius: "0 3px 3px 0" }} />
                    <span style={{ color: "var(--text-secondary)", fontVariantNumeric: "tabular-nums" }}>{(r.swing_pct * 100).toFixed(1)}% (₹{rupee(r.low)}–{rupee(r.high)})</span>
                  </div>
                </div>
              );
            })}
          </div>

          {history.length > 0 && (
            <div className="card-rich p-6">
              <p className="eyebrow">History</p>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                <thead><tr><th style={{ ...th, ...left }}>Date</th><th style={{ ...th, ...left }}>Assumption</th><th style={th}>Value</th><th style={{ ...th, ...left }}>Reason</th><th style={{ ...th, ...left }}>Status</th></tr></thead>
                <tbody>{history.map((h) => (
                  <tr key={h.id} style={{ opacity: h.active ? 1 : 0.6 }}>
                    <td style={{ ...td, ...left }}>{new Date(h.created_at).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })}</td>
                    <td style={{ ...td, ...left }}>{label(h.metric)} · {h.unit}{h.fiscal_year ? `, ${fy(h.fiscal_year)}` : ""}{h.scenario !== "All" ? `, ${h.scenario}` : ""}</td>
                    <td style={td}>{show(h.metric, h.value)}</td>
                    <td style={{ ...td, ...left, color: "var(--text-secondary)", maxWidth: 380 }}>{h.reason}</td>
                    <td style={{ ...td, ...left, color: h.active ? "var(--accent-green)" : "var(--text-muted)" }}>{h.active ? "In force" : h.superseded_reason ?? "Retired"}</td>
                  </tr>
                ))}</tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
}
