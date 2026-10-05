import { useEffect, useMemo, useState } from "react";
import { getTVFields, getTVMarkets, getTVPresets, scanTV } from "../api";
import type { TVField, TVFilterNode, TVMarkets, TVPreset, TVScanResult } from "../api";

// A condition row as edited in the UI. `rhsField` compares against another column instead of a number.
interface Cond { field: string; op: string; value: string; value2: string; rhsField: boolean }

const LS_KEY = "tv_screener_settings_v1";
const NUM_OPS_NO_VALUE = ["empty", "not_empty"];
const RANGE_OPS = ["between", "not_between", "in_day_range", "in_week_range", "in_month_range"];
const LIST_OPS = ["isin", "not_in", "has", "has_none_of"];

function parseVal(s: string): unknown {
  const t = s.trim();
  if (t !== "" && !isNaN(Number(t))) return Number(t);
  return t;
}

function toNode(c: Cond): TVFilterNode {
  const rhs = (s: string) => (c.rhsField ? { field: s } : parseVal(s));
  if (NUM_OPS_NO_VALUE.includes(c.op)) return { op: c.op, field: c.field };
  if (LIST_OPS.includes(c.op)) return { op: c.op, field: c.field, value: c.value.split(",").map((s) => s.trim()).filter(Boolean) };
  if (RANGE_OPS.includes(c.op)) return { op: c.op, field: c.field, value: parseVal(c.value), value2: parseVal(c.value2) };
  if (c.op.endsWith("_pct")) return { op: c.op, field: c.field, value: { field: c.value }, value2: parseVal(c.value2) };
  return { op: c.op, field: c.field, value: rhs(c.value) };
}

function fmt(v: unknown): string {
  if (v === null || v === undefined) return "—";
  if (typeof v === "number") {
    const a = Math.abs(v);
    if (a >= 1e12) return (v / 1e12).toFixed(2) + "T";
    if (a >= 1e9) return (v / 1e9).toFixed(2) + "B";
    if (a >= 1e6) return (v / 1e6).toFixed(2) + "M";
    return Number.isInteger(v) ? v.toLocaleString() : v.toFixed(Math.abs(v) < 1 ? 4 : 2);
  }
  return String(v);
}

function FieldPicker({ fields, value, onChange, listId }: { fields: TVField[]; value: string; onChange: (v: string) => void; listId: string }) {
  // Free-text with datalist: type to search, e.g. "RSI", "donch", "gross_profit". Timeframe via `name|tf`.
  const base = value.split("|")[0];
  const meta = fields.find((f) => f.name === base);
  const tf = value.includes("|") ? value.split("|")[1] : "";
  return (
    <div className="flex gap-1 min-w-0">
      <input
        list={listId} value={base} placeholder="field…"
        onChange={(e) => onChange(e.target.value + (tf ? "|" + tf : ""))}
        className="flex-1 min-w-0 bg-gray-900 border border-gray-700 rounded px-2 py-1 text-xs text-gray-200"
        title={meta?.label}
      />
      {meta && meta.timeframes.length > 0 && (
        <select value={tf} onChange={(e) => onChange(base + (e.target.value ? "|" + e.target.value : ""))}
          className="bg-gray-900 border border-gray-700 rounded px-1 py-1 text-xs text-gray-200" title="Timeframe (minutes / 1W / 1M); blank = daily">
          <option value="">1D</option>
          {meta.timeframes.map((t) => <option key={t} value={t}>{/^\d+$/.test(t) ? t + "m" : t}</option>)}
        </select>
      )}
    </div>
  );
}

export function TVScreenerPage() {
  const saved = useMemo(() => { try { return JSON.parse(localStorage.getItem(LS_KEY) ?? "{}"); } catch { return {}; } }, []);
  const [meta, setMeta] = useState<TVMarkets | null>(null);
  const [presets, setPresets] = useState<TVPreset[]>([]);
  const [market, setMarket] = useState<string>(saved.market ?? "india");
  const [fields, setFields] = useState<TVField[]>([]);
  const [columns, setColumns] = useState<string[]>(saved.columns ?? ["name", "close", "change", "volume", "market_cap_basic"]);
  const [conds, setConds] = useState<Cond[]>(saved.conds ?? []);
  const [join, setJoin] = useState<"and" | "or">(saved.join ?? "and");
  const [sortBy, setSortBy] = useState<string>(saved.sortBy ?? "market_cap_basic");
  const [asc, setAsc] = useState<boolean>(saved.asc ?? false);
  const [limit, setLimit] = useState<number>(saved.limit ?? 100);
  const [assetScope, setAssetScope] = useState<string>(saved.assetScope ?? "all");
  const [tickers, setTickers] = useState<string>(saved.tickers ?? "");
  const [index, setIndex] = useState<string>(saved.index ?? "");
  const [result, setResult] = useState<TVScanResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ms, setMs] = useState<number | null>(null);
  const [addCol, setAddCol] = useState("");

  useEffect(() => { getTVMarkets().then(setMeta).catch((e) => setError(String(e.message))); getTVPresets().then(setPresets).catch(() => {}); }, []);
  useEffect(() => { getTVFields(market).then(setFields).catch((e) => setError(String(e.message))); }, [market]);
  useEffect(() => {
    try { localStorage.setItem(LS_KEY, JSON.stringify({ market, columns, conds, join, sortBy, asc, limit, assetScope, tickers, index })); } catch { /* ignore */ }
  }, [market, columns, conds, join, sortBy, asc, limit, assetScope, tickers, index]);

  const listId = "tv-fields-" + market;
  const isStock = meta?.countries.includes(market) ?? true;

  function applyPreset(p: TVPreset) {
    setMarket(p.market);
    setColumns(p.columns ?? []);
    const children = p.filters?.children ?? [];
    setJoin((p.filters?.op as "and" | "or") ?? "and");
    setConds(children.map((c) => {
      const rhsField = typeof c.value === "object" && c.value !== null && "field" in (c.value as object);
      return { field: c.field ?? "", op: c.op, rhsField,
        value: rhsField ? (c.value as { field: string }).field : c.value == null ? "" : Array.isArray(c.value) ? c.value.join(",") : String(c.value),
        value2: c.value2 == null ? "" : String(c.value2) };
    }));
    setSortBy(p.sort_by ?? ""); setAsc(p.ascending ?? false); setAssetScope(p.asset_scope ?? "all");
    setResult(null);
  }

  async function run() {
    setLoading(true); setError(null);
    const t0 = performance.now();
    try {
      const valid = conds.filter((c) => c.field);
      const filters: TVFilterNode | null = valid.length ? { op: join, children: valid.map(toNode) } : null;
      const r = await scanTV({
        markets: [market], columns, filters, sort_by: sortBy || null, ascending: asc, limit,
        tickers: tickers.split(",").map((s) => s.trim()).filter(Boolean),
        index: index.trim() || null, asset_scope: isStock ? assetScope : "all",
      });
      setResult(r); setMs(Math.round(performance.now() - t0));
    } catch (e) { setError((e as Error).message); setResult(null); }
    finally { setLoading(false); }
  }

  function exportCsv() {
    if (!result) return;
    const esc = (v: unknown) => `"${String(v ?? "").replace(/"/g, '""')}"`;
    const csv = [result.columns.map(esc).join(","), ...result.rows.map((r) => result.columns.map((c) => esc(r[c])).join(","))].join("\n");
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" })); a.download = `tv_${market}.csv`; a.click();
  }

  const inp = "bg-gray-900 border border-gray-700 rounded px-2 py-1 text-xs text-gray-200 focus:border-blue-600 focus:outline-none";
  const allMarkets = meta ? [...meta.countries, ...meta.other] : [market];

  return (
    <div className="flex flex-1 min-h-0">
      <aside className="w-96 shrink-0 overflow-y-auto border-r border-gray-800 p-3 space-y-4 text-xs">
        <datalist id={listId}>{fields.map((f) => <option key={f.name} value={f.name}>{f.label}</option>)}</datalist>

        <section className="space-y-1.5">
          <div className="text-[11px] uppercase tracking-wider text-gray-500">Presets</div>
          <select className={inp + " w-full"} value="" onChange={(e) => { const p = presets.find((x) => x.id === e.target.value); if (p) applyPreset(p); }}>
            <option value="">Load a preset…</option>
            {presets.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
        </section>

        <section className="space-y-1.5">
          <div className="text-[11px] uppercase tracking-wider text-gray-500">Market</div>
          <select className={inp + " w-full"} value={market} onChange={(e) => { setMarket(e.target.value); setConds([]); setColumns(["name", "close"]); setSortBy(""); }}>
            {allMarkets.map((m) => <option key={m} value={m}>{m}</option>)}
          </select>
          {isStock && (
            <select className={inp + " w-full"} value={assetScope} onChange={(e) => setAssetScope(e.target.value)} title="Default 'all' keeps TradingView's built-in filter (common/preferred stocks, non-ETF funds, DRs)">
              {(meta?.asset_scopes ?? ["all"]).map((s) => <option key={s} value={s}>{s === "all" ? "Default stock scope" : "Only " + s}</option>)}
            </select>
          )}
          <input className={inp + " w-full"} placeholder="Index e.g. SYML:NSE;NIFTY (optional)" value={index} onChange={(e) => setIndex(e.target.value)} />
          <input className={inp + " w-full"} placeholder="Tickers e.g. NSE:TCS, NSE:INFY (optional)" value={tickers} onChange={(e) => setTickers(e.target.value)} />
        </section>

        <section className="space-y-1.5">
          <div className="flex items-center justify-between">
            <div className="text-[11px] uppercase tracking-wider text-gray-500">Filters</div>
            <select className={inp} value={join} onChange={(e) => setJoin(e.target.value as "and" | "or")}>
              <option value="and">match ALL</option><option value="or">match ANY</option>
            </select>
          </div>
          {conds.map((c, i) => {
            const upd = (patch: Partial<Cond>) => setConds(conds.map((x, j) => (j === i ? { ...x, ...patch } : x)));
            const noVal = NUM_OPS_NO_VALUE.includes(c.op), range = RANGE_OPS.includes(c.op), pct = c.op.endsWith("_pct");
            return (
              <div key={i} className="rounded border border-gray-800 p-1.5 space-y-1">
                <FieldPicker fields={fields} value={c.field} onChange={(v) => upd({ field: v })} listId={listId} />
                <div className="flex gap-1">
                  <select className={inp} value={c.op} onChange={(e) => upd({ op: e.target.value })}>
                    {Object.keys(meta?.operators ?? { ">": 1 }).map((o) => <option key={o} value={o}>{o}</option>)}
                  </select>
                  {!noVal && (
                    <input className={inp + " flex-1 min-w-0"} value={c.value} onChange={(e) => upd({ value: e.target.value })}
                      list={c.rhsField || pct ? listId : undefined}
                      placeholder={pct ? "other field" : LIST_OPS.includes(c.op) ? "a, b, c" : c.rhsField ? "other field" : "value"} />
                  )}
                  {(range || pct) && <input className={inp + " w-20"} value={c.value2} onChange={(e) => upd({ value2: e.target.value })} placeholder={pct ? "pct" : "to"} />}
                  <button className="text-gray-500 hover:text-red-400 px-1" onClick={() => setConds(conds.filter((_, j) => j !== i))}>✕</button>
                </div>
                {!noVal && !range && !pct && !LIST_OPS.includes(c.op) && (
                  <label className="flex items-center gap-1 text-[10px] text-gray-500">
                    <input type="checkbox" checked={c.rhsField} onChange={(e) => upd({ rhsField: e.target.checked })} /> compare to another field
                  </label>
                )}
              </div>
            );
          })}
          <button className="text-blue-400 hover:text-blue-300" onClick={() => setConds([...conds, { field: "", op: ">", value: "", value2: "", rhsField: false }])}>+ Add condition</button>
        </section>

        <section className="space-y-1.5">
          <div className="text-[11px] uppercase tracking-wider text-gray-500">Columns ({columns.length})</div>
          <div className="flex flex-wrap gap-1">
            {columns.map((c) => (
              <span key={c} className="inline-flex items-center gap-1 rounded bg-gray-800 px-1.5 py-0.5 text-[11px] text-gray-300">
                {c}<button className="text-gray-500 hover:text-red-400" onClick={() => setColumns(columns.filter((x) => x !== c))}>×</button>
              </span>
            ))}
          </div>
          <div className="flex gap-1">
            <div className="flex-1 min-w-0"><FieldPicker fields={fields} value={addCol} onChange={setAddCol} listId={listId} /></div>
            <button className={inp} onClick={() => { if (addCol && !columns.includes(addCol)) setColumns([...columns, addCol]); setAddCol(""); }}>Add</button>
          </div>
          <div className="text-[10px] text-gray-600">{fields.length} fields available for {market}. Pick a timeframe (1m–1M) from the dropdown next to a field.</div>
        </section>

        <section className="space-y-1.5">
          <div className="text-[11px] uppercase tracking-wider text-gray-500">Sort & limit</div>
          <div className="flex gap-1">
            <div className="flex-1 min-w-0"><FieldPicker fields={fields} value={sortBy} onChange={setSortBy} listId={listId} /></div>
            <select className={inp} value={asc ? "asc" : "desc"} onChange={(e) => setAsc(e.target.value === "asc")}><option value="desc">desc</option><option value="asc">asc</option></select>
            <input type="number" className={inp + " w-16"} value={limit} min={1} max={1000} onChange={(e) => setLimit(Math.max(1, Math.min(1000, Number(e.target.value) || 100)))} />
          </div>
        </section>

        <button onClick={run} disabled={loading} className="w-full rounded bg-blue-600 hover:bg-blue-500 disabled:opacity-50 py-2 text-sm font-medium text-white">
          {loading ? "Scanning…" : "Run scan"}
        </button>
      </aside>

      <main className="flex-1 min-w-0 overflow-auto p-3">
        {error && <div className="mb-3 rounded border border-red-800 bg-red-950/40 p-2 text-xs text-red-300">{error}</div>}
        {!result && !error && <div className="text-gray-600 text-sm p-8 text-center">Choose a market, add filters and columns, then run the scan. Data comes from TradingView (may be delayed).</div>}
        {result && (
          <>
            <div className="mb-2 flex items-center justify-between text-xs text-gray-500">
              <span>{result.total.toLocaleString()} matched · showing {result.rows.length}{result.cached ? " · cached" : ""}{ms !== null ? ` · ${ms} ms` : ""}</span>
              <button className="text-blue-400 hover:text-blue-300" onClick={exportCsv}>Export CSV</button>
            </div>
            <div className="overflow-x-auto rounded-lg border border-gray-800">
              <table className="w-full text-xs">
                <thead><tr className="border-b border-gray-800 bg-gray-900/60">
                  {result.columns.map((c) => <th key={c} className="py-1.5 px-2 text-left text-[11px] font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">{c}</th>)}
                </tr></thead>
                <tbody className="divide-y divide-gray-800/50">
                  {result.rows.length === 0 && <tr><td colSpan={result.columns.length} className="py-10 text-center text-gray-600">No symbols matched</td></tr>}
                  {result.rows.map((r, i) => (
                    <tr key={i} className="hover:bg-gray-800/30">
                      {result.columns.map((c) => {
                        const v = r[c];
                        const neg = typeof v === "number" && v < 0 && /change|perf|growth|chg/i.test(c);
                        const pos = typeof v === "number" && v > 0 && /change|perf|growth|chg/i.test(c);
                        return <td key={c} className={`py-1 px-2 whitespace-nowrap tabular-nums ${neg ? "text-red-400" : pos ? "text-emerald-400" : "text-gray-300"}`}>{fmt(v)}</td>;
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
