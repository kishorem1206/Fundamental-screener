// The convergence read on the Combined Score page. The combined number only ranks;
// the gates set the class. Everything here comes from app/convergence/, built from
// stored scores and prices.
import { useEffect, useState } from "react";
import { Check, X } from "lucide-react";
import { api } from "../api";

export interface Dimension { key: string; name: string; score: number | null; label: string; status: string; text: string; fit?: number | null }
export interface HistoryRow { on: string; quality: number | null; fundamental: number | null; technical: number | null; relative_strength: number | null; valuation: number | null;
  stage: number | null; sub_stage: string | null; risk_reward?: number | null; combined?: number | null; classification?: string; method_version?: string }
export interface Convergence { combined: number | null; classification: string; why: string; warnings: string[]; confidence: number; confidence_label: string; confidence_notes: string[]; coverage: number;
  dimensions: Dimension[]; qualifies: { area: string; text: string }[]; invalidates: { area: string; text: string }[]; high_gates: { gate: string; passed: boolean }[];
  rr: { ratio: number | null; upside_pct: number | null; downside_pct: number | null; target: number | null; target_basis: string | null; invalidation: number | null; invalidation_basis: string | null;
    entry_low: number | null; entry_high: number | null; in_zone: boolean; entry_note: string; reason?: string };
  windows: Record<string, number | null>; as_of: string; method_version: string; history: HistoryRow[]; moves: { on: string; from: string; to: string; direction: string }[]; canslim: number | null }
interface Setting { key: string; value: number; default: number; min: number; max: number; group: string; label: string }

export const RESEARCH_COLOR: Record<string, string> = { "High Priority": "#4fb3a0", "Strong Candidate": "#7fb8ff", "Early Opportunity": "#e8c766", "Watchlist": "#a9b3c9", "Caution": "#e0793c", "Low Priority": "#d9694f", "Not Rated": "#6f7c96" };
export const STAGE_DOT: Record<number, string> = { 1: "#7fb8ff", 2: "#4fb3a0", 3: "#e8c766", 4: "#d9694f" };
const tone = (v: number | null | undefined) => (v === null || v === undefined ? "var(--text-dim)" : v >= 65 ? "#4fb3a0" : v >= 50 ? "#c9a227" : v >= 40 ? "#e0793c" : "#d9694f");
const num = (v: number | null | undefined, digits = 0) => (v === null || v === undefined ? "—" : v.toFixed(digits));
const rupee = (v: number | null | undefined) => (v === null || v === undefined ? "—" : `₹${v.toLocaleString("en-IN", { maximumFractionDigits: 2 })}`);
export const stageName = (stage: number | null | undefined, sub?: string | null) => sub ?? (stage ? `Stage ${stage}` : "Unclassified");

function Stat({ label, value, color }: { label: string; value: string; color?: string }) {
  return <div><div className="text-[10.5px]" style={{ color: "var(--text-dim)" }}>{label}</div><div className="text-sm font-semibold tabular-nums" style={{ color: color ?? "var(--text-primary)" }}>{value}</div></div>;
}

export default function ConvergencePanel({ c, row }: { c: Convergence; row: { fundamental: number | null; technical: number | null; relative_strength: number | null; valuation_view: string | null; stage?: number | null; sub_stage?: string | null } }) {
  const color = RESEARCH_COLOR[c.classification];
  const rr = c.rr;
  return (
    <div className="space-y-3">
      <div className="rounded-lg p-3" style={{ border: `1px solid ${color}` }}>
        <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1 mb-2">
          <b className="text-base" style={{ color }}>{c.classification}</b>
          <span className="text-xs" style={{ color: "var(--text-secondary)" }}>{c.why}.</span>
          <span className="text-[11px] ml-auto" style={{ color: "var(--text-dim)" }} title={c.confidence_notes.join("; ") || "Nothing lowered it"}>
            Confidence {c.confidence_label.toLowerCase()} ({c.confidence.toFixed(0)}) · method {c.method_version} · prices to {c.as_of}</span>
        </div>
        <div className="grid grid-cols-4 md:grid-cols-8 gap-3">
          <Stat label="Combined" value={num(c.combined, 1)} color={tone(c.combined)} />
          <Stat label="Fundamental" value={num(row.fundamental)} color={tone(row.fundamental)} />
          <Stat label="Technical" value={num(row.technical)} color={tone(row.technical)} />
          <Stat label="Stage" value={stageName(row.stage, row.sub_stage).replace(" Stage 2", "").replace("Stage 2 ", "")} />
          <Stat label="Relative strength" value={num(row.relative_strength)} color={tone(row.relative_strength)} />
          <Stat label="Valuation" value={row.valuation_view ? row.valuation_view[0] + row.valuation_view.slice(1).toLowerCase() : "—"} />
          <Stat label="Reward/risk" value={rr.ratio === null ? "—" : `${rr.ratio.toFixed(1)} to 1`} />
          <Stat label="CANSLIM (not scored)" value={num(c.canslim)} />
        </div>
        {c.warnings.length > 0 && <div className="text-xs mt-2" style={{ color: "#e0793c" }}>Warning: {c.warnings.join("; ")}.</div>}
      </div>

      <div className="grid gap-2 md:grid-cols-5">
        {c.dimensions.map((d) => (
          <div key={d.key} className="rounded-lg p-3" style={{ background: "var(--glass-hi)" }}>
            <div className="flex items-center justify-between gap-1 mb-1">
              <span className="text-xs font-semibold" style={{ color: "var(--text-primary)" }}>{d.name}</span>
              <span className="text-[10px] flex-shrink-0" style={{ color: d.status === "New" ? "#e8c766" : "var(--text-dim)" }}>{d.status.split(",")[0]}</span>
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-xl font-bold tabular-nums" style={{ color: tone(d.score) }}>{num(d.score)}</span>
              <span className="text-xs" style={{ color: "var(--text-secondary)" }}>{d.label}</span>
            </div>
            <div className="h-1 rounded-sm my-1.5" style={{ background: "var(--border-subtle)" }}><div className="h-1 rounded-sm" style={{ width: `${d.score ?? 0}%`, background: tone(d.score) }} /></div>
            <p className="text-[11px] leading-snug" style={{ color: "var(--text-secondary)" }}>{d.text}{d.key === "technical_stage" && d.fit != null ? `, stage fit ${d.fit.toFixed(0)}.` : d.key === "technical_stage" ? "." : ""}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        {([["Why this stock qualifies", c.qualifies, "#4fb3a0", "Nothing stands out in its favour."], ["What could invalidate the thesis", c.invalidates, "#e0793c", "No specific risk read."]] as const).map(([title, items, mark, none]) => (
          <div key={title} className="rounded-lg p-3" style={{ border: "1px solid var(--border-subtle)" }}>
            <div className="text-xs font-semibold mb-1.5" style={{ color: "var(--text-primary)" }}>{title}</div>
            {items.length === 0 && <div className="text-xs" style={{ color: "var(--text-dim)" }}>{none}</div>}
            {items.map((x, i) => (
              <div key={i} className="flex gap-2 text-xs py-0.5" style={{ color: "var(--text-secondary)" }}>
                <span className="w-1 flex-shrink-0 rounded-sm" style={{ background: mark }} />
                <span><span style={{ color: "var(--text-dim)" }}>{x.area}:</span> {x.text}</span>
              </div>
            ))}
          </div>
        ))}
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <div className="rounded-lg p-3 text-xs" style={{ border: "1px solid var(--border-subtle)", color: "var(--text-secondary)" }}>
          <div className="font-semibold mb-1.5" style={{ color: "var(--text-primary)" }}>Risk and reward <span className="font-normal" style={{ color: "var(--text-dim)" }}>calculated from chart levels, not a forecast</span></div>
          {rr.ratio === null ? <div>{rr.reason}</div> : <>
            <div>Target {rupee(rr.target)} ({rr.target_basis}), {rr.upside_pct! >= 0 ? "+" : ""}{rr.upside_pct}%.</div>
            <div>Invalidation {rupee(rr.invalidation)} ({rr.invalidation_basis}), -{rr.downside_pct}%.</div></>}
          <div>{rr.entry_low !== null ? <>Entry zone {rupee(rr.entry_low)} to {rupee(rr.entry_high)}: {rr.entry_note.toLowerCase()}{rr.in_zone ? ". The price is in it now." : "."}</> : `${rr.entry_note}.`}</div>
          <div>Against the Nifty 500: {Object.entries(c.windows).map(([k, v]) => `${k} ${v === null ? "—" : `${v > 0 ? "+" : ""}${v.toFixed(1)}%`}`).join(" · ")}</div>
        </div>
        <div className="rounded-lg p-3 text-xs" style={{ border: "1px solid var(--border-subtle)" }}>
          <div className="font-semibold mb-1.5" style={{ color: "var(--text-primary)" }}>High Priority needs all of these</div>
          <div className="grid grid-cols-2 gap-x-3">
            {c.high_gates.map((g) => (
              <div key={g.gate} className="flex items-center gap-1.5 py-0.5" style={{ color: g.passed ? "var(--text-primary)" : "var(--text-dim)" }}>
                {g.passed ? <Check size={12} color="#4fb3a0" /> : <X size={12} color="#d9694f" />}{g.gate}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="rounded-lg p-3" style={{ border: "1px solid var(--border-subtle)" }}>
        <div className="text-xs font-semibold mb-1" style={{ color: "var(--text-primary)" }}>How its profile has changed</div>
        {c.moves.length > 0 && <div className="text-xs mb-1" style={{ color: "var(--text-secondary)" }}>{c.moves.slice(0, 4).map((m) => `${m.on}: ${m.direction} from ${m.from} to ${m.to}`).join(" · ")}</div>}
        <div className="overflow-x-auto">
          <table className="w-full text-[11px] tabular-nums">
            <thead><tr style={{ color: "var(--text-dim)" }}>{["Date", "Quality", "Fundamental", "Technical", "Rel. strength", "Valuation", "Stage", "Reward/risk", "Combined", "Class"].map((h, i) => <th key={h} className={`py-1 pr-2 font-medium ${i && i < 6 ? "text-right" : "text-left"}`}>{h}</th>)}</tr></thead>
            <tbody>
              {c.history.slice(0, 12).map((h) => (
                <tr key={h.on} style={{ borderTop: "1px solid var(--border-subtle)", color: "var(--text-secondary)" }}>
                  <td className="py-1 pr-2">{h.on}</td>
                  {[h.quality, h.fundamental, h.technical, h.relative_strength, h.valuation].map((v, i) => <td key={i} className="py-1 pr-2 text-right">{num(v, 1)}</td>)}
                  <td className="py-1 pr-2">{h.stage || h.sub_stage ? stageName(h.stage, h.sub_stage) : "—"}</td>
                  <td className="py-1 pr-2">{num(h.risk_reward, 1)}</td><td className="py-1 pr-2">{num(h.combined, 1)}</td><td className="py-1 pr-2">{h.classification ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="text-[10.5px] mt-1" style={{ color: "var(--text-dim)" }}>Reward/risk, combined and class are recorded daily from 31 Oct 2026. Earlier dates show only what was stored then.</div>
      </div>
    </div>
  );
}

export function Methodology({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const [rows, setRows] = useState<Setting[]>([]);
  const [version, setVersion] = useState("");
  const [edits, setEdits] = useState<Record<string, string>>({});
  const [error, setError] = useState("");
  useEffect(() => { api.convergenceSettings().then((r) => { setRows(r.settings); setVersion(r.version); }).catch((e: Error) => setError(e.message)); }, []);
  const groups = [...new Set(rows.map((r) => r.group))];
  const save = async () => {
    try {
      await api.saveConvergenceSettings(Object.fromEntries(Object.entries(edits).map(([k, v]) => [k, Number(v)])));
      await api.recalculateConvergence();
      onSaved();
    } catch (e: unknown) { setError(e instanceof Error ? e.message : "Could not save"); }
  };
  const input = { background: "var(--bg-input)", border: "1px solid var(--border-subtle)", color: "var(--text-primary)" };
  return (
    <div className="card-rich p-5">
      <div className="flex items-center justify-between mb-1">
        <p className="eyebrow">Method {version}</p>
        <button aria-label="Close method" onClick={onClose} style={{ color: "var(--text-dim)" }}><X size={15} /></button>
      </div>
      <p className="text-xs mb-3 max-w-3xl" style={{ color: "var(--text-secondary)" }}>
        Combined = weighted average of the five dimensions, for ranking only. Technical Stage shares one weight between the Technical score and the stage, so trend counts once.
        Quality is weighted and Fundamental is not, because Quality contains it. CANSLIM, the market and Quantitative are shown but not scored. Saving rebuilds today's read; earlier days stay as recorded.</p>
      {error && <p className="text-xs mb-2" style={{ color: "var(--accent-red)" }}>{error}</p>}
      <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-x-8 gap-y-3">
        {groups.map((g) => (
          <div key={g}>
            <div className="text-xs font-semibold mb-1" style={{ color: "var(--text-primary)" }}>{g}</div>
            {rows.filter((r) => r.group === g).map((r) => (
              <label key={r.key} className="flex items-center justify-between gap-3 text-xs py-0.5" style={{ color: "var(--text-secondary)" }}>
                <span title={`Default ${r.default}, allowed ${r.min} to ${r.max}`}>{r.label}</span>
                <input type="number" step="any" min={r.min} max={r.max} value={edits[r.key] ?? r.value} onChange={(e) => setEdits({ ...edits, [r.key]: e.target.value })}
                       className="w-16 rounded-md px-2 py-0.5 text-right tabular-nums" style={input} />
              </label>
            ))}
          </div>
        ))}
      </div>
      <button onClick={save} disabled={!Object.keys(edits).length} className="mt-3 px-3 py-1.5 rounded-lg text-xs"
              style={{ color: "var(--accent-gold-bright)", border: "1px solid rgba(201,162,39,0.45)", opacity: Object.keys(edits).length ? 1 : 0.45 }}>Save and recalculate</button>
    </div>
  );
}
