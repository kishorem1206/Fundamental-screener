import { Fragment, useEffect, useState } from "react";
import { api } from "../api";

// Portfolio — framework sections 12-14: what is owned against better
// alternatives, size limits, sector and asset allocation. Holdings from Kite
// (read-only), a broker CSV, or entered by hand.

type Scores = Record<string, number | null>;
interface Holding {
  id: string; source: string; name: string; symbol: string | null; asset_class: string; class_basis: string | null;
  quantity: number | null; last_price: number | null; value: number; pct_of_total: number; pct_of_equity?: number;
  framework?: (Scores & { classification: string | null; action: string | null; size: string | null; matrix: string | null }) | null;
  sector?: string; sector_pct_of_equity?: number; size_after_checks?: string | null; target_band_pct?: [number, number] | null;
  add_value_to_band_mid?: number | null; notes?: string[]; correlation_with_rest?: number | null;
  comparison?: { candidate: string; candidate_classification: string; candidate_action: string; clearly_better: boolean; why: string;
    better_company: boolean; better_opportunity: boolean; scores: Record<string, { held: number | null; candidate: number | null }> } | null;
  final_action?: string; final_reason?: string;
}
export interface PortfolioResponse {
  empty: boolean; total: number; equity_book?: number; prices_as_of?: string;
  allocation?: { asset_class: string; value: number; pct: number; target_pct: number | null; status: string | null }[];
  sectors?: { sector: string; value: number; pct_of_equity: number | null; over_limit: boolean }[];
  holdings: Holding[];
  risk?: { volatility_pct?: number; max_fall_1y_pct?: number; return_1y_pct?: number; within_drawdown_tolerance?: boolean; basis?: string; reason?: string };
  candidates?: (Scores & { symbol: string; company_name: string; sector: string; classification: string; action: string; size: string | null;
    vs_weakest_holding_in_sector: { holding: string; clearly_better: boolean; why: string } | null })[];
  settings: { max_stock_pct: number; max_sector_pct: number; drawdown_tolerance_pct: number; targets: Record<string, number> };
}

const CLASSES = ["EQUITY", "EQUITY_FUND", "DEBT", "GOLD", "CASH", "INTERNATIONAL", "OTHER"];
const CLASS_LABEL: Record<string, string> = { EQUITY: "Stocks", EQUITY_FUND: "Equity funds", DEBT: "Debt", GOLD: "Gold", CASH: "Cash",
  INTERNATIONAL: "International", OTHER: "Other" };
const ACTION_COLOR: Record<string, string> = { "Add gradually": "#4fb3a0", "Add on confirmation": "#4fb3a0", Hold: "#a9b3c9",
  Watch: "#e8c766", Reduce: "#e0793c", Replace: "#d9694f", Avoid: "#d9694f" };
const inr = (v: number | null | undefined) => v === null || v === undefined ? "—" : `₹${Math.round(v).toLocaleString("en-IN")}`;
const fmt = (v: number | null | undefined, d = 1) => v === null || v === undefined ? "—" : v.toFixed(d);

export default function Portfolio() {
  const [data, setData] = useState<PortfolioResponse | null>(null);
  const [kite, setKite] = useState<{ connected: boolean; user: { user_name?: string } | null } | null>(null);
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);
  const [open, setOpen] = useState<string | null>(null);
  const [manual, setManual] = useState({ name: "", asset_class: "GOLD", value: "" });
  const [csvSource, setCsvSource] = useState("DHAN_CSV");
  const [settings, setSettings] = useState<PortfolioResponse["settings"] | null>(null);

  const load = () => api.getPortfolio().then((r) => { setData(r); setSettings(r.settings); }).catch((e) => setMsg(String(e)));
  useEffect(() => { load(); api.kiteStatus().then(setKite).catch(() => setKite({ connected: false, user: null })); }, []);

  const run = async (label: string, fn: () => Promise<unknown>) => {
    setBusy(true); setMsg(label);
    try { const r = await fn(); setMsg(typeof r === "string" ? r : `${label} done`); await load(); }
    catch (e) { setMsg(e instanceof Error ? e.message : String(e)); }
    finally { setBusy(false); }
  };

  const connect = async () => {
    const { login_url } = await api.kiteLogin();
    window.open(login_url, "_blank");
    setMsg("Log in to Kite in the new tab, then press “Sync from Kite”.");
  };
  const box = { border: "1px solid var(--border-subtle)" };
  const input = { background: "var(--bg-input)", border: "1px solid var(--border-subtle)", color: "var(--text-primary)" };

  return (
    <div className="space-y-6 fade-in">
      <div className="card-rich p-6">
        <p className="eyebrow">Portfolio</p>
        <h1 className="text-xl font-semibold mb-1" style={{ color: "var(--text-primary)" }}>Is it better than what you already own?</h1>
        <p className="text-sm max-w-3xl" style={{ color: "var(--text-secondary)" }}>
          Every holding is set against the best same-sector stock that passes the quality gate, sized within your limits,
          and the whole portfolio checked against your asset-allocation targets and drawdown tolerance. Holdings are read
          from Kite (read only — this app never places orders), a broker CSV, or entered by hand.
        </p>
        <div className="flex flex-wrap items-center gap-3 mt-4 text-sm">
          <span style={{ color: kite?.connected ? "#4fb3a0" : "var(--text-dim)" }}>
            Kite: {kite?.connected ? `connected${kite.user?.user_name ? ` (${kite.user.user_name})` : ""}` : "not connected"}
          </span>
          <button disabled={busy} onClick={connect} className="px-3 py-1.5 rounded-lg text-xs" style={box}>Connect Kite</button>
          <button disabled={busy} onClick={() => run("Syncing from Kite", async () => {
            const r = await api.kiteSync(); return `Read ${r.rows} rows from Kite`; })} className="px-3 py-1.5 rounded-lg text-xs" style={box}>Sync from Kite</button>
          <button disabled={busy} title="Latest NSE closing price for every listed stock held (for CSV and hand-entered holdings)"
                  onClick={() => run("Refreshing prices from NSE", async () => { const r = await api.repricePortfolio(); return `Repriced ${r.updated} of ${r.of} holdings at NSE's ${r.price_date ?? "latest"} close`; })}
                  className="px-3 py-1.5 rounded-lg text-xs" style={box}>Refresh prices (NSE)</button>
          <label className="px-3 py-1.5 rounded-lg text-xs cursor-pointer" style={box}>
            Upload holdings CSV
            <input type="file" accept=".csv,text/csv" className="hidden" onChange={(e) => {
              const f = e.target.files?.[0]; if (!f) return;
              run("Reading the CSV", async () => { const r = await api.importCsv(await f.text(), csvSource); return `Read ${r.rows} rows (${r.matched_stocks} matched to listed stocks, ${r.skipped} skipped)`; });
            }} />
          </label>
          <select value={csvSource} onChange={(e) => setCsvSource(e.target.value)} className="rounded-lg px-2 py-1.5 text-xs" style={input}>
            <option value="DHAN_CSV">from Dhan</option><option value="ZERODHA_CSV">from Zerodha console</option><option value="CSV">from another broker</option>
          </select>
          {msg && <span className="text-xs" style={{ color: "var(--text-secondary)" }}>{msg}</span>}
        </div>
      </div>

      <div className="card-rich p-4 grid gap-4 lg:grid-cols-2">
        <div>
          <p className="eyebrow mb-2">Add a holding by hand</p>
          <div className="flex flex-wrap gap-2">
            <input placeholder="Name (e.g. Sovereign gold bonds)" value={manual.name} onChange={(e) => setManual({ ...manual, name: e.target.value })}
                   className="rounded-lg px-3 py-1.5 text-sm w-56" style={input} />
            <select value={manual.asset_class} onChange={(e) => setManual({ ...manual, asset_class: e.target.value })} className="rounded-lg px-2 py-1.5 text-sm" style={input}>
              {CLASSES.map((c) => <option key={c} value={c}>{CLASS_LABEL[c]}</option>)}
            </select>
            <input placeholder="Value ₹" value={manual.value} onChange={(e) => setManual({ ...manual, value: e.target.value })}
                   className="rounded-lg px-3 py-1.5 text-sm w-32" style={input} />
            <button disabled={busy || !manual.name || !Number(manual.value)} className="px-3 py-1.5 rounded-lg text-xs" style={box}
                    onClick={() => run("Adding", () => api.addManualHolding({ name: manual.name, asset_class: manual.asset_class, value: Number(manual.value) }).then(() => setManual({ ...manual, name: "", value: "" })))}>Add</button>
          </div>
        </div>
        {settings && (
          <div>
            <p className="eyebrow mb-2">Your limits and targets</p>
            <div className="flex flex-wrap gap-3 text-xs items-center" style={{ color: "var(--text-secondary)" }}>
              {([["max_stock_pct", "Max per stock %"], ["max_sector_pct", "Max per sector %"], ["drawdown_tolerance_pct", "Drawdown tolerance %"]] as const).map(([k, l]) => (
                <label key={k} className="flex items-center gap-1">{l}
                  <input type="number" value={settings[k]} onChange={(e) => setSettings({ ...settings, [k]: Number(e.target.value) })}
                         className="rounded px-2 py-1 w-16" style={input} /></label>
              ))}
            </div>
            <div className="flex flex-wrap gap-3 text-xs items-center mt-2" style={{ color: "var(--text-secondary)" }}>
              Targets %:
              {CLASSES.map((c) => (
                <label key={c} className="flex items-center gap-1">{CLASS_LABEL[c]}
                  <input type="number" value={settings.targets?.[c] ?? ""} placeholder="—"
                         onChange={(e) => { const t = { ...(settings.targets || {}) }; if (e.target.value === "") delete t[c]; else t[c] = Number(e.target.value); setSettings({ ...settings, targets: t }); }}
                         className="rounded px-2 py-1 w-14" style={input} /></label>
              ))}
              <button disabled={busy} className="px-3 py-1 rounded-lg" style={box} onClick={() => run("Saving", () => api.savePortfolioSettings(settings))}>Save</button>
            </div>
          </div>
        )}
      </div>

      {data && data.empty && (
        <div className="card-rich p-6 text-sm" style={{ color: "var(--text-secondary)" }}>No holdings yet. Connect Kite and sync, upload a CSV, or add holdings by hand.</div>
      )}

      {data && !data.empty && (
        <>
          <div className="grid gap-4 lg:grid-cols-3">
            <div className="card-rich p-4">
              <p className="eyebrow mb-2">Asset allocation · {inr(data.total)}</p>
              <table className="w-full text-xs"><tbody>
                {data.allocation!.map((a) => (
                  <tr key={a.asset_class} style={{ borderTop: "1px solid var(--border-subtle)" }}>
                    <td className="py-1" style={{ color: "var(--text-secondary)" }}>{CLASS_LABEL[a.asset_class] ?? a.asset_class}</td>
                    <td className="py-1 text-right tabular-nums">{a.pct}%</td>
                    <td className="py-1 text-right tabular-nums" style={{ color: "var(--text-dim)" }}>{a.target_pct === null ? "no target" : `target ${a.target_pct}%`}</td>
                    <td className="py-1 text-right" style={{ color: a.status === "on target" ? "#4fb3a0" : a.status ? "#e0793c" : "var(--text-dim)" }}>{a.status ?? ""}</td>
                  </tr>))}
              </tbody></table>
            </div>
            <div className="card-rich p-4">
              <p className="eyebrow mb-2">Sector exposure (share of equity)</p>
              <table className="w-full text-xs"><tbody>
                {data.sectors!.map((s) => (
                  <tr key={s.sector} style={{ borderTop: "1px solid var(--border-subtle)" }}>
                    <td className="py-1" style={{ color: "var(--text-secondary)" }}>{s.sector}</td>
                    <td className="py-1 text-right tabular-nums" style={{ color: s.over_limit ? "#e0793c" : "var(--text-primary)" }}>{fmt(s.pct_of_equity)}%{s.over_limit ? " over limit" : ""}</td>
                  </tr>))}
              </tbody></table>
            </div>
            <div className="card-rich p-4 text-xs space-y-1" style={{ color: "var(--text-secondary)" }}>
              <p className="eyebrow mb-2">Risk</p>
              {data.risk?.reason ? <div>{data.risk.reason}</div> : (<>
                <div>Volatility <b style={{ color: "var(--text-primary)" }}>{fmt(data.risk?.volatility_pct)}%</b> a year</div>
                <div>Worst fall in the last year <b style={{ color: data.risk?.within_drawdown_tolerance ? "#4fb3a0" : "#d9694f" }}>{fmt(data.risk?.max_fall_1y_pct)}%</b>
                  {" "}({data.risk?.within_drawdown_tolerance ? "within" : "beyond"} your {data.settings.drawdown_tolerance_pct}% tolerance)</div>
                <div>Return over the year {fmt(data.risk?.return_1y_pct)}%</div>
                <div style={{ color: "var(--text-dim)" }}>{data.risk?.basis}; prices to {data.prices_as_of}.</div>
              </>)}
            </div>
          </div>

          <div className="card-rich p-4">
            <p className="eyebrow mb-2">Holdings</p>
            <div className="overflow-x-auto"><table className="w-full text-sm">
              <thead><tr style={{ color: "var(--text-dim)", borderBottom: "1px solid var(--border-subtle)" }} className="text-xs">
                <th className="text-left py-2 px-2 font-medium">Holding</th><th className="text-right py-2 px-2 font-medium">Value</th>
                <th className="text-right py-2 px-2 font-medium">Weight</th><th className="text-left py-2 px-2 font-medium">Classification</th>
                <th className="text-right py-2 px-2 font-medium">Quality</th><th className="text-left py-2 px-2 font-medium">Final action</th>
                <th className="text-left py-2 px-2 font-medium">Why</th><th className="py-2 px-2" />
              </tr></thead>
              <tbody>
                {data.holdings.map((h) => (
                  <Fragment key={h.id}>
                    <tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                      <td className="py-2 px-2">
                        <button onClick={() => setOpen(open === h.id ? null : h.id)} className="text-left">
                          <div className="font-medium" style={{ color: "var(--text-primary)" }}>{h.symbol ?? h.name}</div>
                          <div className="text-xs" style={{ color: "var(--text-dim)" }}>{CLASS_LABEL[h.asset_class]} · {h.source}{h.sector ? ` · ${h.sector}` : ""}</div>
                        </button>
                      </td>
                      <td className="py-2 px-2 text-right tabular-nums">{inr(h.value)}</td>
                      <td className="py-2 px-2 text-right tabular-nums text-xs">{h.pct_of_equity !== undefined ? `${fmt(h.pct_of_equity)}% of equity` : `${fmt(h.pct_of_total)}%`}</td>
                      <td className="py-2 px-2 text-xs">{h.framework?.classification ?? "—"}</td>
                      <td className="py-2 px-2 text-right tabular-nums">{fmt(h.framework?.quality)}</td>
                      <td className="py-2 px-2 text-xs font-semibold" style={{ color: ACTION_COLOR[h.final_action ?? ""] ?? "var(--text-dim)" }}>{h.final_action ?? "—"}</td>
                      <td className="py-2 px-2 text-xs max-w-md" style={{ color: "var(--text-secondary)" }}>{h.final_reason ?? h.class_basis}</td>
                      <td className="py-2 px-2 text-right">
                        {h.source === "MANUAL" && <button className="text-xs underline" style={{ color: "var(--text-dim)" }}
                          onClick={() => run("Removing", () => api.deleteHolding(h.id))}>remove</button>}
                      </td>
                    </tr>
                    {open === h.id && h.framework && (
                      <tr><td colSpan={8} className="p-3 text-xs space-y-1" style={{ background: "var(--glass)", color: "var(--text-secondary)" }}>
                        <div>Decision: {h.framework.classification} · {h.framework.action}{h.framework.matrix ? ` (${h.framework.matrix})` : ""}.
                          {" "}Size after checks: {h.size_after_checks ?? "none"}{h.target_band_pct ? ` (${h.target_band_pct[0]}–${h.target_band_pct[1]}% of equity)` : ""}
                          {h.add_value_to_band_mid ? `; adding about ${inr(h.add_value_to_band_mid)} reaches the middle of the band` : ""}.</div>
                        {h.notes && h.notes.length > 0 && <div>Checks: {h.notes.join("; ")}.</div>}
                        {h.correlation_with_rest !== null && h.correlation_with_rest !== undefined && <div>Correlation with the rest of the portfolio: {h.correlation_with_rest}.</div>}
                        {h.comparison && (
                          <div>Against {h.comparison.candidate} ({h.comparison.candidate_classification}, {h.comparison.candidate_action.toLowerCase()}):{" "}
                            {h.comparison.better_company ? "the better company" : "not the better company"},{" "}
                            {h.comparison.better_opportunity ? "the better opportunity now" : "not the better opportunity now"} — {h.comparison.why}.{" "}
                            {Object.entries(h.comparison.scores).map(([k, v]) => `${k.replace(/_/g, " ")} ${fmt(v.held, 0)}→${fmt(v.candidate, 0)}`).join(", ")}.</div>
                        )}
                      </td></tr>
                    )}
                  </Fragment>
                ))}
              </tbody>
            </table></div>
          </div>

          {data.candidates && data.candidates.length > 0 && (
            <div className="card-rich p-4">
              <p className="eyebrow mb-2">For new money: pass the gate, ready to buy, outside sectors at your limit</p>
              <table className="w-full text-xs"><tbody>
                {data.candidates.map((c) => (
                  <tr key={c.symbol} style={{ borderTop: "1px solid var(--border-subtle)" }}>
                    <td className="py-1.5 px-2"><b style={{ color: "var(--text-primary)" }}>{c.symbol}</b> <span style={{ color: "var(--text-dim)" }}>{c.sector}</span></td>
                    <td className="py-1.5 px-2">{c.classification} · {c.action.toLowerCase()}{c.size && c.size !== "None" ? ` · ${c.size.toLowerCase()}` : ""}</td>
                    <td className="py-1.5 px-2 tabular-nums">Quality {fmt(c.quality)} · RS {fmt(c.relative_strength, 0)} · technical {fmt(c.technical, 0)} · valuation {fmt(c.valuation, 0)}</td>
                    <td className="py-1.5 px-2" style={{ color: "var(--text-secondary)" }}>{c.vs_weakest_holding_in_sector ? `vs your ${c.vs_weakest_holding_in_sector.holding}: ${c.vs_weakest_holding_in_sector.why}` : "a sector you do not own"}</td>
                  </tr>))}
              </tbody></table>
            </div>
          )}
        </>
      )}
    </div>
  );
}
