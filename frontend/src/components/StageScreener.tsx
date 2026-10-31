// Weinstein stage screener for every stock with prices. Independent of every other score:
// nothing here reads or feeds Quality, CANSLIM or the decisions.
import { useCallback, useEffect, useState } from "react";
import { ArrowDown, ArrowUp, Download, RefreshCw, SlidersHorizontal, Star, X } from "lucide-react";
import { api } from "../api";
import StageDetail from "./StageDetail";

export interface StageRow { stock_id: string; symbol: string; company_name: string; sector: string | null; basic_industry: string | null; close: number | null; sma30: number | null;
  sma10: number | null; sma_slope_pct: number | null; sma_distance_pct: number | null; rs: number | null; rs_change: number | null; rsi: number | null; volume_ratio: number | null;
  high_52w: number | null; low_52w: number | null; high_distance_pct: number | null; resistance: number | null; support: number | null; confidence: number | null; stage: number | null;
  sub_stage: string | null; reason: string | null; prev_stage: number | null; stage_since: string | null; weeks_in_stage: number | null; weeks_above_sma: number | null;
  rs_improving: boolean | null; next_stage: number | null; opportunity: boolean; near_breakout: boolean; provisional: boolean; pending: number | null; watched: boolean }
export interface StageOverview { total: number; unclassified: number; stages: Record<string, number>; sub_stages: Record<string, number>; new_stage_2: number; stage_2_rs: number;
  opportunities: number; transition_watch: number; as_of: string | null; week_end: string | null; provisional: boolean; computed_at: string | null; new_weeks: number; recalculating: boolean; sectors: string[] }
export interface StageThreshold { key: string; value: number; default: number; min: number; max: number; group: string; label: string }

type Preset = "" | "opportunities" | "new_stage_2" | "stage_2_rs" | "transition_watch" | "watchlist";
type SortKey = "symbol" | "company_name" | "sector" | "close" | "stage" | "confidence" | "sma30" | "sma_slope_pct" | "sma_distance_pct" | "rs" | "rsi" | "volume_ratio" | "high_distance_pct" | "weeks_in_stage";

export const STAGE_COLOR: Record<number, string> = { 1: "var(--stage-1)", 2: "var(--stage-2)", 3: "var(--stage-3)", 4: "var(--stage-4)" };
const STAGE_NAME: Record<number, string> = { 1: "Basing", 2: "Advancing", 3: "Topping", 4: "Declining" };
const SUBS = ["Early Stage 2", "Established Stage 2", "Late Stage 2", "Stage 2 Weakening"];
const PAGE = 100;
const money = (v: number | null) => (v === null ? "—" : v.toLocaleString("en-IN", { maximumFractionDigits: 2 }));
const signed = (v: number | null, unit = "%") => (v === null ? "—" : `${v > 0 ? "+" : ""}${v.toFixed(1)}${unit}`);

export function StageChip({ stage, sub }: { stage: number | null; sub?: string | null }) {
  return (
    <span className="inline-flex items-center gap-1.5 whitespace-nowrap">
      <span className="w-2.5 h-2.5 rounded-sm flex-shrink-0" style={{ background: stage ? STAGE_COLOR[stage] : "var(--stage-none)" }} />
      <span>
        <span className="font-semibold" style={{ color: "var(--text-primary)" }}>{stage ? `Stage ${stage}` : "Unclassified"}</span>
        {sub && <span className="block text-[10.5px] leading-tight" style={{ color: "var(--text-dim)" }}>{sub.replace(" Stage 2", "").replace("Stage 2 ", "")}</span>}
      </span>
    </span>
  );
}

function Thresholds({ onClose, onRecalculate }: { onClose: () => void; onRecalculate: () => void }) {
  const [rows, setRows] = useState<StageThreshold[]>([]);
  const [edits, setEdits] = useState<Record<string, string>>({});
  const [error, setError] = useState("");
  useEffect(() => { api.stageThresholds().then((r) => setRows(r.thresholds)).catch((e: Error) => setError(e.message)); }, []);
  const groups = [...new Set(rows.map((r) => r.group))];
  const save = async () => {
    try {
      await api.saveStageThresholds(Object.fromEntries(Object.entries(edits).map(([k, v]) => [k, Number(v)])));
      onRecalculate();
    } catch (e: unknown) { setError(e instanceof Error ? e.message : "Could not save"); }
  };
  return (
    <div className="card-rich p-6 mb-6">
      <div className="flex items-center justify-between mb-1">
        <h2 className="text-lg font-semibold">Thresholds</h2>
        <button aria-label="Close thresholds" onClick={onClose}><X size={16} /></button>
      </div>
      <p className="text-xs mb-4" style={{ color: "var(--text-secondary)" }}>Saving replays every stock's whole history with the new values, so past stages change too.</p>
      {error && <p className="text-sm mb-2" style={{ color: "var(--stage-4)" }}>{error}</p>}
      <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-x-8 gap-y-4">
        {groups.map((g) => (
          <div key={g}>
            <p className="eyebrow mb-2">{g}</p>
            {rows.filter((r) => r.group === g).map((r) => (
              <label key={r.key} className="flex items-center justify-between gap-3 text-xs py-1" style={{ color: "var(--text-secondary)" }}>
                <span title={`Default ${r.default}, allowed ${r.min} to ${r.max}`}>{r.label}</span>
                <input type="number" step="any" min={r.min} max={r.max} value={edits[r.key] ?? r.value} onChange={(e) => setEdits({ ...edits, [r.key]: e.target.value })}
                       className="w-16 rounded-md px-2 py-1 text-right tabular-nums" />
              </label>
            ))}
          </div>
        ))}
      </div>
      <button onClick={save} disabled={!Object.keys(edits).length} className="stage-pill mt-4" aria-pressed="true" style={{ opacity: Object.keys(edits).length ? 1 : 0.4 }}>Save and recalculate</button>
    </div>
  );
}

export default function StageScreener({ onAnalyse }: { onAnalyse?: (stockId: string) => void }) {
  const [overview, setOverview] = useState<StageOverview | null>(null);
  const [rows, setRows] = useState<{ total: number; results: StageRow[] } | null>(null);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [sector, setSector] = useState("");
  const [stage, setStage] = useState<number | null>(null);
  const [sub, setSub] = useState("");
  const [minConfidence, setMinConfidence] = useState("");
  const [minRs, setMinRs] = useState("");
  const [preset, setPreset] = useState<Preset>("");
  const [sortBy, setSortBy] = useState<SortKey>("confidence");
  const [order, setOrder] = useState<"desc" | "asc">("desc");
  const [page, setPage] = useState(0);
  const [selected, setSelected] = useState<string | null>(null);
  const [showThresholds, setShowThresholds] = useState(false);
  const [version, setVersion] = useState(0);

  const loadOverview = useCallback(() => api.stageOverview().then(setOverview).catch((e: Error) => setError(e.message)), []);
  useEffect(() => { loadOverview(); }, [loadOverview, version]);
  useEffect(() => { setPage(0); }, [search, sector, stage, sub, minConfidence, minRs, preset, sortBy, order]);

  const filters: Record<string, string> = { sort_by: sortBy, order };
  if (search.trim()) filters.q = search.trim();
  if (sector) filters.sector = sector;
  if (stage !== null) filters.stage = String(stage);
  if (sub) filters.sub_stage = sub;
  if (minConfidence) filters.min_confidence = minConfidence;
  if (minRs) filters.min_rs = minRs;
  if (preset === "watchlist") filters.watchlist = "true";
  else if (preset) filters.preset = preset;
  const key = JSON.stringify(filters);

  useEffect(() => {
    const t = setTimeout(() => {
      api.stageScores({ ...filters, limit: String(PAGE), offset: String(page * PAGE) }).then((r) => { setRows(r); setError(""); })
        .catch((e: unknown) => setError(e instanceof Error ? e.message : "Could not load"));
    }, 200);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, page, version]);

  // while a recalculation runs, check every few seconds and reload when it ends
  useEffect(() => {
    if (!overview?.recalculating) return;
    const t = setInterval(() => api.stageOverview().then((o) => { setOverview(o); if (!o.recalculating) setVersion((v) => v + 1); }).catch(() => undefined), 3000);
    return () => clearInterval(t);
  }, [overview?.recalculating]);

  const recalculate = async () => {
    setShowThresholds(false);
    await api.recalculateStages().catch(() => undefined);
    loadOverview();
  };
  const sort = (k: SortKey) => {
    if (sortBy === k) setOrder((o) => (o === "desc" ? "asc" : "desc"));
    else { setSortBy(k); setOrder("desc"); }
  };
  const toggleWatch = async (r: StageRow) => {
    await api.stageWatch(r.stock_id, !r.watched);
    setVersion((v) => v + 1);
  };
  const clear = () => { setSearch(""); setSector(""); setStage(null); setSub(""); setMinConfidence(""); setMinRs(""); setPreset(""); };
  const Icon = order === "desc" ? ArrowDown : ArrowUp;
  const head = (k: SortKey, label: string, title?: string, left = false) => (
    <th key={k} title={title} onClick={() => sort(k)} className={`${left ? "text-left" : "text-right"} py-2 px-2 font-semibold cursor-pointer select-none whitespace-nowrap`}>
      {label}{sortBy === k && <Icon size={11} className="inline ml-0.5" />}
    </th>
  );

  if (selected) return (
    <div className="stage-root">
      <StageDetail stockId={selected} onBack={() => { setSelected(null); setVersion((v) => v + 1); }} onAnalyse={onAnalyse} />
    </div>
  );

  const o = overview;
  const largest = o ? Math.max(...Object.values(o.stages), o.unclassified, 1) : 1;
  const tiles: { label: string; value: number | undefined; note: string; apply?: () => void }[] = [
    { label: "Stocks analysed", value: o?.total, note: `${o?.unclassified ?? 0} unclassified`, apply: clear },
    ...[1, 2, 3, 4].map((s) => ({ label: `Stage ${s}`, value: o?.stages[s], note: STAGE_NAME[s], apply: () => { clear(); setStage(s); } })),
    { label: "New Stage 2", value: o?.new_stage_2, note: `Within ${o?.new_weeks ?? 4} weeks`, apply: () => { clear(); setPreset("new_stage_2"); } },
    { label: "Stage 2, RS improving", value: o?.stage_2_rs, note: "Against the Nifty 500", apply: () => { clear(); setPreset("stage_2_rs"); } },
  ];
  const presets: { key: Preset; label: string; count?: number }[] = [
    { key: "", label: "All stocks" }, { key: "opportunities", label: "Stage 2 Opportunities", count: o?.opportunities }, { key: "new_stage_2", label: "New Stage 2", count: o?.new_stage_2 },
    { key: "stage_2_rs", label: "Stage 2, RS improving", count: o?.stage_2_rs }, { key: "transition_watch", label: "Transition watch", count: o?.transition_watch }, { key: "watchlist", label: "Watchlist" },
  ];

  return (
    <div className="stage-root">
      <div className="max-w-[1500px] mx-auto px-4 md:px-10 py-8 fade-in">
        <div className="flex flex-wrap items-center justify-between gap-2 mb-5">
          <p className="eyebrow">Stage Screener / All stocks</p>
          <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
            {o?.as_of ? `Prices to ${o.as_of}` : ""}{o?.provisional ? " · this week is still open, so its stages are provisional until Friday's close" : o?.as_of ? " · weekly close" : ""}</p>
        </div>
        <div className="flex flex-wrap items-end justify-between gap-4 mb-6">
          <div>
            <h1 className="text-4xl font-bold mb-2">Know the stage before the stock.</h1>
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>Stan Weinstein's four stages, read from weekly prices. Every stage shows the conditions behind it. This is a separate read: it changes no other score.</p>
          </div>
          <div className="flex gap-2">
            <button className="stage-pill flex items-center gap-1.5" onClick={() => setShowThresholds(!showThresholds)}><SlidersHorizontal size={13} /> Thresholds</button>
            <button className="stage-pill flex items-center gap-1.5" disabled={o?.recalculating} onClick={recalculate}>
              <RefreshCw size={13} className={o?.recalculating ? "animate-spin" : ""} /> {o?.recalculating ? "Recalculating…" : "Recalculate"}</button>
          </div>
        </div>
        {showThresholds && <Thresholds onClose={() => setShowThresholds(false)} onRecalculate={recalculate} />}

        <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-7 py-5 mb-6" style={{ borderTop: "1px solid var(--border-subtle)", borderBottom: "1px solid var(--border-subtle)" }}>
          {tiles.map((t, i) => (
            <button key={t.label} onClick={t.apply} className="text-left px-4 py-1" style={i ? { borderLeft: "1px solid var(--border-subtle)" } : undefined}>
              <div className="text-xs mb-1.5" style={{ color: "var(--text-secondary)" }}>{t.label}</div>
              <div className="text-3xl font-bold tabular-nums" style={{ letterSpacing: "-0.03em" }}>{t.value ?? "—"}</div>
              <div className="text-[11px] mt-1" style={{ color: "var(--text-dim)" }}>{t.note}</div>
            </button>
          ))}
        </div>

        <div className="grid lg:grid-cols-5 gap-4 mb-6">
          <div className="card-rich p-6 lg:col-span-3">
            <p className="eyebrow mb-1">01 / Stage distribution</p>
            <h2 className="text-xl font-semibold mb-4">Where the market stands</h2>
            {o && [1, 2, 3, 4, 0].map((s) => {
              const count = s ? o.stages[s] : o.unclassified;
              const on = stage === s;
              return (
                <button key={s} aria-pressed={on} title={`Show ${s ? `Stage ${s}` : "Unclassified"}`} onClick={() => { setPreset(""); setSub(""); setStage(on ? null : s); }}
                        className="w-full flex items-center gap-3 py-1.5 text-left rounded-lg" style={{ opacity: stage === null || on ? 1 : 0.45 }}>
                  <span className="w-32 text-xs flex-shrink-0" style={{ color: "var(--text-primary)", fontWeight: on ? 700 : 500 }}>{s ? `Stage ${s} · ${STAGE_NAME[s]}` : "Unclassified"}</span>
                  <span className="flex-1 h-5"><span className="block h-5" style={{ width: `${Math.max((count / largest) * 100, 0.5)}%`, background: s ? STAGE_COLOR[s] : "var(--stage-none)", borderRadius: "0 4px 4px 0" }} /></span>
                  <span className="w-20 text-right text-xs tabular-nums" style={{ color: "var(--text-secondary)" }}>{count} · {o.total ? Math.round((count / o.total) * 100) : 0}%</span>
                </button>
              );
            })}
          </div>
          <div className="card-rich p-6 lg:col-span-2">
            <p className="eyebrow mb-1">02 / Inside Stage 2</p>
            <h2 className="text-xl font-semibold mb-4">How mature the advance is</h2>
            {SUBS.map((s) => (
              <button key={s} aria-pressed={sub === s} onClick={() => { setPreset(""); setStage(null); setSub(sub === s ? "" : s); }}
                      className="w-full flex items-center justify-between py-2 text-sm" style={{ borderTop: "1px solid var(--border-subtle)", fontWeight: sub === s ? 700 : 400 }}>
                <span>{s}</span><span className="tabular-nums font-semibold">{o?.sub_stages[s] ?? 0}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="flex flex-wrap gap-2 mb-3">
          {presets.map((p) => (
            <button key={p.key} className="stage-pill" aria-pressed={preset === p.key} onClick={() => { clear(); setPreset(p.key); }}>{p.label}{p.count !== undefined ? ` · ${p.count}` : ""}</button>
          ))}
        </div>
        {preset === "opportunities" && <p className="text-xs mb-3" style={{ color: "var(--text-secondary)" }}>
          Stage 2 above a rising 30-week average, relative strength improving, up weeks on heavier volume. Stocks near a new high or a recent breakout come first.</p>}
        {preset === "transition_watch" && <p className="text-xs mb-3" style={{ color: "var(--text-secondary)" }}>Stocks showing most of the checks for their next stage. A watch, not a stage change.</p>}

        <div className="flex flex-wrap items-center gap-2 mb-3">
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search company or symbol…" className="rounded-lg px-3 py-1.5 text-xs w-56" />
          <select aria-label="Sector" value={sector} onChange={(e) => setSector(e.target.value)} className="rounded-lg px-3 py-1.5 text-xs">
            <option value="">All sectors</option>{o?.sectors.map((s) => <option key={s}>{s}</option>)}
          </select>
          <select aria-label="Stage" value={stage ?? ""} onChange={(e) => setStage(e.target.value === "" ? null : Number(e.target.value))} className="rounded-lg px-3 py-1.5 text-xs">
            <option value="">All stages</option>{[1, 2, 3, 4].map((s) => <option key={s} value={s}>Stage {s}</option>)}<option value={0}>Unclassified</option>
          </select>
          <select aria-label="Confidence" value={minConfidence} onChange={(e) => setMinConfidence(e.target.value)} className="rounded-lg px-3 py-1.5 text-xs">
            <option value="">Any confidence</option>{[60, 70, 80, 90].map((v) => <option key={v} value={v}>Confidence {v}+</option>)}
          </select>
          <select aria-label="Relative strength" value={minRs} onChange={(e) => setMinRs(e.target.value)} className="rounded-lg px-3 py-1.5 text-xs">
            <option value="">Any RS</option><option value="0">RS above 0</option><option value="5">RS +5 or more</option><option value="10">RS +10 or more</option><option value="20">RS +20 or more</option>
          </select>
          <button onClick={clear} className="text-xs underline" style={{ color: "var(--text-secondary)" }}>Clear</button>
          <span className="flex-1" />
          <a className="stage-pill flex items-center gap-1.5" href={api.stageExportUrl(filters, "csv")}><Download size={13} /> CSV</a>
          <a className="stage-pill flex items-center gap-1.5" href={api.stageExportUrl(filters, "xlsx")}><Download size={13} /> Excel</a>
        </div>

        {error && <p className="text-sm mb-2" style={{ color: "var(--stage-4)" }}>{error}</p>}
        {!rows && !error && <p className="text-xs" style={{ color: "var(--text-dim)" }}>Loading…</p>}
        {rows && <>
          <p className="text-xs mb-1" style={{ color: "var(--text-dim)" }}>{rows.total.toLocaleString("en-IN")} {rows.total === 1 ? "stock" : "stocks"}</p>
          <div className="overflow-x-auto">
            <table className="w-full text-[13px]">
              <thead><tr className="text-[11px]" style={{ color: "var(--text-dim)", borderBottom: "1px solid var(--border-subtle)" }}>
                <th className="w-6" aria-label="Watchlist" />
                {head("symbol", "Symbol", undefined, true)}
                {head("company_name", "Company", undefined, true)}
                {head("sector", "Sector", undefined, true)}
                {head("close", "CMP", "Last weekly close")}
                {head("stage", "Stage", undefined, true)}
                {head("confidence", "Confidence", "Weight of this stage's conditions that are met, out of 100")}
                {head("sma30", "30W SMA")}
                {head("sma_slope_pct", "SMA slope", "Change in the 30-week average over 4 weeks")}
                {head("sma_distance_pct", "From SMA")}
                {head("rs", "RS", "Mansfield relative strength against the Nifty 500: % above or below its own 52-week average")}
                {head("rsi", "RSI", "Weekly RSI 14")}
                {head("volume_ratio", "Volume", "This week's daily volume ÷ the 10 weeks before")}
                {head("high_distance_pct", "From 52W high")}
                {head("weeks_in_stage", "Stage change", "Previous stage, and weeks in this one")}
              </tr></thead>
              <tbody>
                {rows.results.map((r) => (
                  <tr key={r.stock_id} className="cursor-pointer" onClick={() => setSelected(r.stock_id)} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                    <td className="pl-1" onClick={(e) => { e.stopPropagation(); toggleWatch(r); }}>
                      <button aria-label={r.watched ? `Remove ${r.symbol} from watchlist` : `Add ${r.symbol} to watchlist`}><Star size={14} fill={r.watched ? "#e0a92a" : "none"} color={r.watched ? "#e0a92a" : "#b9b8b1"} /></button>
                    </td>
                    <td className="py-2 px-2 font-semibold whitespace-nowrap">{r.symbol}</td>
                    <td className="py-2 px-2 max-w-[190px] truncate" title={r.company_name}>{r.company_name}</td>
                    <td className="py-2 px-2 max-w-[130px] truncate" style={{ color: "var(--text-secondary)" }} title={r.basic_industry ?? r.sector ?? ""}>{r.sector ?? "—"}</td>
                    <td className="py-2 px-2 text-right tabular-nums">{money(r.close)}</td>
                    <td className="py-2 px-2" title={r.stage ? undefined : r.reason ?? undefined}><StageChip stage={r.stage} sub={r.sub_stage} /></td>
                    <td className="py-2 px-2 text-right tabular-nums font-semibold">{r.confidence === null ? "—" : r.confidence.toFixed(0)}</td>
                    <td className="py-2 px-2 text-right tabular-nums">{money(r.sma30)}</td>
                    <td className="py-2 px-2 text-right tabular-nums">{signed(r.sma_slope_pct)}</td>
                    <td className="py-2 px-2 text-right tabular-nums">{signed(r.sma_distance_pct)}</td>
                    <td className="py-2 px-2 text-right tabular-nums">{signed(r.rs, "")}{r.rs_improving === null ? "" : r.rs_improving ? " ↑" : " ↓"}</td>
                    <td className="py-2 px-2 text-right tabular-nums">{r.rsi === null ? "—" : r.rsi.toFixed(0)}</td>
                    <td className="py-2 px-2 text-right tabular-nums">{r.volume_ratio === null ? "—" : `${r.volume_ratio.toFixed(2)}x`}</td>
                    <td className="py-2 px-2 text-right tabular-nums">{signed(r.high_distance_pct)}</td>
                    <td className="py-2 px-2 text-right whitespace-nowrap" style={{ color: "var(--text-secondary)" }}>
                      {r.stage ? <>{r.prev_stage ? `${r.prev_stage} → ${r.stage}` : `${r.stage}`} · {r.weeks_in_stage}w</> : "—"}
                      {r.pending ? <span className="block text-[10.5px]">→ {r.pending} pending</span> : r.next_stage ? <span className="block text-[10.5px]">watch → {r.next_stage}</span> : null}
                    </td>
                  </tr>
                ))}
                {rows.results.length === 0 && <tr><td colSpan={15} className="py-6 text-center text-sm" style={{ color: "var(--text-dim)" }}>{preset === "watchlist" ? "Your watchlist is empty. Star a stock to add it." : "No stocks match."}</td></tr>}
              </tbody>
            </table>
          </div>
          {rows.total > PAGE && (
            <div className="flex items-center justify-end gap-3 mt-3 text-xs" style={{ color: "var(--text-secondary)" }}>
              <button disabled={page === 0} onClick={() => setPage(page - 1)} className="stage-pill" style={{ opacity: page === 0 ? 0.5 : 1 }}>Previous</button>
              <span>Page {page + 1} of {Math.ceil(rows.total / PAGE)}</span>
              <button disabled={(page + 1) * PAGE >= rows.total} onClick={() => setPage(page + 1)} className="stage-pill" style={{ opacity: (page + 1) * PAGE >= rows.total ? 0.5 : 1 }}>Next</button>
            </div>
          )}
        </>}
      </div>
    </div>
  );
}
