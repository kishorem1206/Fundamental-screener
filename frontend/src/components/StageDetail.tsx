// One stock's stage: chart, history, the conditions for and against, what comes next.
import { useEffect, useState } from "react";
import { ArrowLeft, Check, Minus, Star, X } from "lucide-react";
import { api } from "../api";
import StageChart, { type StageWeek } from "./StageChart";
import { StageChip, STAGE_COLOR, type StageRow } from "./StageScreener";

interface Condition { key: string; label: string; met: boolean | null; weight: number; value: string }
interface Spell { stage: number; start: string; end: string; weeks: number; first: number; last: number }
interface Signal { from: number; to: number; met: number; of: number; watch: boolean; checks: { label: string; met: boolean | null }[] }
export interface StageStock extends StageRow { as_of: string; week_end: string; explanation: string; supporting: Condition[]; contradicting: Condition[]; not_read: Condition[]; spells: Spell[]; weeks: StageWeek[];
  detail: { scores?: Record<string, number | null>; signal?: Signal | null; pending?: number | null; macd?: number | null; macd_signal?: number | null; updown?: number | null; range_pct?: number | null;
    higher_highs?: boolean | null; higher_lows?: boolean | null; failed_highs?: number | null; last_breakout?: string | null } }

const num = (v: number | null | undefined, digits = 2) => (v === null || v === undefined ? "—" : v.toLocaleString("en-IN", { maximumFractionDigits: digits }));
const STRUCTURE: Record<string, string> = { "true,true": "Higher highs, higher lows", "false,false": "Lower highs, lower lows", "true,false": "Higher highs, lower lows", "false,true": "Lower highs, higher lows" };

function Conditions({ title, rows, kind }: { title: string; rows: Condition[]; kind: "for" | "against" }) {
  const Icon = kind === "for" ? Check : X;
  return (
    <div className="card-white p-5">
      <p className="eyebrow mb-2">{title}</p>
      {rows.length === 0 && <p className="text-xs" style={{ color: "var(--text-dim)" }}>None.</p>}
      {rows.map((c) => (
        <div key={c.key} className="flex items-start gap-2 py-1 text-[13px]">
          <Icon size={14} className="mt-0.5 flex-shrink-0" style={{ color: kind === "for" ? "var(--stage-2)" : "var(--stage-4)" }} />
          <span className="flex-1">{c.label}</span>
          {c.value && <span className="tabular-nums" style={{ color: "var(--text-secondary)" }}>{c.value}</span>}
        </div>
      ))}
    </div>
  );
}

export default function StageDetail({ stockId, onBack, onAnalyse }: { stockId: string; onBack: () => void; onAnalyse?: (stockId: string) => void }) {
  const [data, setData] = useState<StageStock | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { api.stageStock(stockId).then(setData).catch((e: Error) => setError(e.message)); }, [stockId]);
  const toggle = async () => {
    if (!data) return;
    const r = await api.stageWatch(stockId, !data.watched);
    setData({ ...data, watched: r.watched });
  };
  const back = <button onClick={onBack} className="stage-pill flex items-center gap-1.5 mb-5"><ArrowLeft size={13} /> Stage Screener</button>;
  if (!data) return <div className="max-w-[1500px] mx-auto px-4 md:px-10 py-8">{back}<p className="text-sm" style={{ color: error ? "var(--stage-4)" : "var(--text-dim)" }}>{error || "Loading…"}</p></div>;

  const d = data.detail, signal = d.signal;
  const stats: [string, string][] = [
    ["CMP", num(data.close)], ["30-week SMA", num(data.sma30)], ["10-week SMA", num(data.sma10)], ["SMA slope, 4 weeks", data.sma_slope_pct === null ? "—" : `${data.sma_slope_pct.toFixed(1)}%`],
    ["Resistance", num(data.resistance)], ["Support", num(data.support)], ["52-week high", num(data.high_52w)], ["52-week low", num(data.low_52w)],
    ["Weekly RSI", num(data.rsi, 1)], ["Weekly MACD", d.macd === null || d.macd === undefined ? "—" : `${num(d.macd)} (signal ${num(d.macd_signal)})`], ["Volume ratio", data.volume_ratio === null ? "—" : `${data.volume_ratio.toFixed(2)}x`],
    ["Up ÷ down week volume", d.updown === null || d.updown === undefined ? "—" : `${d.updown.toFixed(2)}x`], ["Weeks above 30-week SMA", String(data.weeks_above_sma ?? "—")],
    ["12-week range", d.range_pct === null || d.range_pct === undefined ? "—" : `${d.range_pct.toFixed(1)}%`], ["Swing structure", STRUCTURE[`${d.higher_highs},${d.higher_lows}`] ?? "—"], ["Last breakout", d.last_breakout ?? "None in 8 weeks"],
  ];

  return (
    <div className="max-w-[1500px] mx-auto px-4 md:px-10 py-8 fade-in">
      {back}
      <div className="flex flex-wrap items-start justify-between gap-4 mb-5">
        <div>
          <p className="eyebrow mb-1">{data.symbol}{data.basic_industry ? ` / ${data.basic_industry}` : ""}</p>
          <h1 className="text-3xl font-bold mb-2">{data.company_name}</h1>
          <div className="flex items-center gap-4 text-sm">
            <StageChip stage={data.stage} sub={data.sub_stage} />
            {data.confidence !== null && <span style={{ color: "var(--text-secondary)" }}>Confidence <b style={{ color: "var(--text-primary)" }}>{data.confidence.toFixed(0)}</b></span>}
            {data.provisional && <span style={{ color: "var(--text-secondary)" }}>Week still open</span>}
          </div>
        </div>
        <div className="flex gap-2">
          <button className="stage-pill flex items-center gap-1.5" onClick={toggle}><Star size={13} fill={data.watched ? "#e0a92a" : "none"} color={data.watched ? "#e0a92a" : "currentColor"} /> {data.watched ? "On watchlist" : "Add to watchlist"}</button>
          {onAnalyse && <button className="stage-pill" onClick={() => onAnalyse(data.stock_id)}>Run full analysis</button>}
        </div>
      </div>
      <p className="text-sm mb-5 max-w-4xl" style={{ color: "var(--text-secondary)" }}>{data.explanation}
        {d.pending ? ` A move to Stage ${d.pending} is waiting for a second week to confirm.` : ""}</p>

      <div className="card-white p-4 mb-5"><StageChart weeks={data.weeks} resistance={data.resistance} support={data.support} /></div>

      {data.stage !== null && <div className="grid md:grid-cols-2 gap-4 mb-5">
        <Conditions title="Supports this stage" rows={data.supporting} kind="for" />
        <Conditions title="Contradicts this stage" rows={data.contradicting} kind="against" />
      </div>}

      <div className="grid lg:grid-cols-3 gap-4">
        <div className="card-rich p-6">
          <p className="eyebrow mb-2">What to watch next</p>
          {signal ? <>
            <h3 className="text-base font-semibold mb-2">Stage {signal.from} → Stage {signal.to}: {signal.met} of {signal.of} checks</h3>
            {signal.checks.map((c) => (
              <div key={c.label} className="flex items-center gap-2 py-1 text-[13px]">
                {c.met === null ? <Minus size={14} style={{ color: "var(--text-dim)" }} /> : c.met ? <Check size={14} style={{ color: "var(--stage-2)" }} /> : <X size={14} style={{ color: "var(--text-dim)" }} />}
                <span style={{ color: c.met ? "var(--text-primary)" : "var(--text-secondary)" }}>{c.label}</span>
              </div>
            ))}
          </> : <p className="text-sm" style={{ color: "var(--text-secondary)" }}>No stage, so no next stage to read.</p>}
        </div>
        <div className="card-rich p-6">
          <p className="eyebrow mb-2">Stage history</p>
          <div className="max-h-72 overflow-y-auto">
            <table className="w-full text-[13px]">
              <thead><tr className="text-[11px]" style={{ color: "var(--text-dim)" }}><th className="text-left font-semibold py-1">Stage</th><th className="text-left font-semibold">From</th><th className="text-right font-semibold">Weeks</th><th className="text-right font-semibold">Price</th></tr></thead>
              <tbody>
                {[...data.spells].reverse().map((s) => (
                  <tr key={s.start} style={{ borderTop: "1px solid var(--border-subtle)" }}>
                    <td className="py-1.5"><span className="inline-block w-2.5 h-2.5 rounded-sm mr-1.5" style={{ background: STAGE_COLOR[s.stage] }} />Stage {s.stage}</td>
                    <td className="tabular-nums" style={{ color: "var(--text-secondary)" }}>{s.start}</td>
                    <td className="text-right tabular-nums">{s.weeks}</td>
                    <td className="text-right tabular-nums">{s.last >= s.first ? "+" : ""}{((s.last / s.first - 1) * 100).toFixed(1)}%</td>
                  </tr>
                ))}
                {data.spells.length === 0 && <tr><td colSpan={4} className="py-3 text-xs" style={{ color: "var(--text-dim)" }}>Not enough weeks of prices yet.</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
        <div className="card-rich p-6">
          <p className="eyebrow mb-2">The numbers</p>
          {stats.map(([k, v]) => (
            <div key={k} className="flex justify-between gap-3 py-[3px] text-[13px]"><span style={{ color: "var(--text-secondary)" }}>{k}</span><span className="tabular-nums text-right">{v}</span></div>
          ))}
        </div>
      </div>
    </div>
  );
}
