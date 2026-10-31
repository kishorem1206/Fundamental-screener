// Month view of results dates from NSE. Click a date to see who reports, holdings first.
// Expected figures are analysts' consensus from Yahoo: shown, never scored.
import { useEffect, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { api } from "../api";

export interface ResultsMonth { month: string; today: string; first: string | null; last: string | null; updated: number; waiting: number; gave_up: number;
  days: { date: string; count: number; held: number }[] }
export interface ResultsStock { symbol: string; company_name: string; basic_industry: string | null; group: "held" | "strong" | "other"; held: boolean;
  fundamental: number | null; quality: number | null; classification: string | null; status: string; quarter: string | null;
  eps_estimate: number | null; eps_low: number | null; eps_high: number | null; eps_year_ago: number | null; eps_analysts: number | null;
  revenue_estimate_cr: number | null; revenue_year_ago_cr: number | null; revenue_analysts: number | null;
  actual_eps: number | null; actual_sales_cr: number | null; eps_surprise_pct: number | null; revenue_surprise_pct: number | null }
export interface ResultsDay { date: string; stocks: ResultsStock[] }

const WEEK = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const GROUPS: { key: ResultsStock["group"]; title: string }[] = [
  { key: "held", title: "In your holdings" }, { key: "strong", title: "Strong fundamentals (70+)" }, { key: "other", title: "Everything else" },
];
const DIM = "var(--text-dim)", INK = "var(--text-secondary)", TOP = "var(--text-primary)", BORDER = "1px solid var(--border-subtle)";
const tone = (v: number | null) => (v === null ? DIM : v >= 70 ? "#4fb3a0" : v >= 50 ? "#c9a227" : "#d9694f");
const money = (v: number | null) => (v === null ? "—" : `₹${v.toLocaleString("en-IN", { maximumFractionDigits: 2 })}`);
const crore = (v: number | null) => (v === null ? "—" : `₹${Math.round(v).toLocaleString("en-IN")} cr`);
const growth = (now: number | null, then: number | null) => {
  if (now === null || !then || then < 0) return "";
  const g = (now / then - 1) * 100;
  return ` (${g >= 0 ? "+" : "−"}${Math.abs(g).toFixed(0)}%)`;
};
const monthName = (m: string) => new Date(`${m}-01T00:00:00`).toLocaleDateString("en-IN", { month: "long", year: "numeric" });
const dayName = (d: string) => new Date(`${d}T00:00:00`).toLocaleDateString("en-IN", { weekday: "long", day: "numeric", month: "long" });
const shift = (m: string, by: number) => {
  const d = new Date(`${m}-01T00:00:00`);
  d.setMonth(d.getMonth() + by);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
};

function Surprise({ pct }: { pct: number | null }) {
  if (pct === null) return null;
  return <span style={{ color: pct >= 0 ? "#4fb3a0" : "#d9694f" }}> {pct >= 0 ? "beat" : "missed"} {Math.abs(pct).toFixed(1)}%</span>;
}

function StockRow({ s, past }: { s: ResultsStock; past: boolean }) {
  const reported = s.status === "DONE" && s.actual_eps !== null;
  return (
    <tr style={{ borderTop: BORDER }}>
      <td className="py-1.5 pr-3">
        <div className="font-semibold" style={{ color: TOP }}>{s.company_name}</div>
        <div className="text-[11px]" style={{ color: DIM }}>{s.symbol}{s.basic_industry ? ` · ${s.basic_industry}` : ""}</div>
      </td>
      <td className="text-right px-2 tabular-nums font-semibold" style={{ color: tone(s.fundamental) }}>{s.fundamental === null ? "—" : s.fundamental.toFixed(0)}</td>
      <td className="text-right px-2 tabular-nums" style={{ color: tone(s.quality) }}>{s.quality === null ? "—" : s.quality.toFixed(0)}</td>
      <td className="text-right px-2 tabular-nums whitespace-nowrap" style={{ color: INK }} title={s.eps_low !== null ? `Analysts' range ${money(s.eps_low)} to ${money(s.eps_high)}` : undefined}>
        {money(s.eps_estimate)}<span style={{ color: DIM }}>{growth(s.eps_estimate, s.eps_year_ago)}</span></td>
      <td className="text-right px-2 tabular-nums whitespace-nowrap" style={{ color: INK }}>{crore(s.revenue_estimate_cr)}<span style={{ color: DIM }}>{growth(s.revenue_estimate_cr, s.revenue_year_ago_cr)}</span></td>
      <td className="text-right px-2 tabular-nums" style={{ color: DIM }}>{s.eps_analysts ?? s.revenue_analysts ?? "—"}</td>
      <td className="text-right pl-2 whitespace-nowrap" style={{ color: INK }}>
        {reported ? <>EPS {money(s.actual_eps)}<Surprise pct={s.eps_surprise_pct} /></> : !past ? null : s.status === "PENDING" ? <span style={{ color: DIM }}>Waiting</span> : s.status === "GAVE_UP" ? <span style={{ color: DIM }}>Not found</span> : "—"}
      </td>
    </tr>
  );
}

function DayPanel({ on }: { on: string }) {
  const [data, setData] = useState<ResultsDay | null>(null);
  useEffect(() => { setData(null); api.resultsDay(on).then(setData).catch(() => setData({ date: on, stocks: [] })); }, [on]);
  if (!data) return <p className="text-xs p-2" style={{ color: DIM }}>Loading…</p>;
  const now = new Date();
  const past = on < `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
  return (
    <div className="pt-3" style={{ borderTop: BORDER }}>
      <div className="text-sm font-semibold mb-1" style={{ color: TOP }}>{dayName(on)}: {data.stocks.length} {data.stocks.length === 1 ? "result" : "results"}</div>
      {data.stocks.length === 0 ? <p className="text-xs" style={{ color: DIM }}>No results on this date.</p> : (
        <div className="overflow-x-auto" style={{ maxHeight: 520, overflowY: "auto" }}>
          <table className="w-full text-xs">
            <thead><tr className="text-[10px] uppercase tracking-wide" style={{ color: DIM }}>
              <th className="text-left py-1 font-semibold">Stock</th>
              <th className="text-right px-2 font-semibold">Fundamental</th><th className="text-right px-2 font-semibold">Quality</th>
              <th className="text-right px-2 font-semibold" title="Analysts' consensus EPS for the quarter, with growth on a year ago">Expected EPS</th>
              <th className="text-right px-2 font-semibold" title="Analysts' consensus revenue for the quarter, with growth on a year ago">Expected revenue</th>
              <th className="text-right px-2 font-semibold">Analysts</th>
              <th className="text-right pl-2 font-semibold">{past ? "Result" : ""}</th>
            </tr></thead>
            <tbody>
              {GROUPS.map(({ key, title }) => {
                const rows = data.stocks.filter((s) => s.group === key);
                if (rows.length === 0) return null;
                return [
                  <tr key={key}><td colSpan={7} className="pt-3 pb-1 text-[11px] font-semibold" style={{ color: key === "held" ? "var(--accent-gold-bright)" : DIM }}>{title} ({rows.length})</td></tr>,
                  ...rows.map((s) => <StockRow key={s.symbol} s={s} past={past} />),
                ];
              })}
            </tbody>
          </table>
        </div>
      )}
      <p className="text-[11px] mt-2" style={{ color: DIM }}>Expected figures are analysts' consensus from Yahoo Finance, for context only, and not every stock has them. Actual EPS is from Screener and can differ slightly in basis from the estimate.</p>
    </div>
  );
}

export default function ResultsCalendar() {
  const [data, setData] = useState<ResultsMonth | null>(null);
  const [month, setMonth] = useState<string | undefined>(undefined);
  const [picked, setPicked] = useState<string | null>(null);

  useEffect(() => {
    api.resultsCalendar(month).then((r) => {
      setData(r);
      setPicked((p) => p ?? (r.days.find((d) => d.date >= r.today) ?? r.days[r.days.length - 1])?.date ?? null);
    }).catch(() => setData(null));
  }, [month]);
  if (!data) return null;

  const byDate = new Map(data.days.map((d) => [d.date, d]));
  const peak = Math.max(1, ...data.days.map((d) => d.count));
  const [year, mon] = data.month.split("-").map(Number);
  const blanks = (new Date(year, mon - 1, 1).getDay() + 6) % 7;
  const total = new Date(year, mon, 0).getDate();
  const canBack = !data.first || data.month > data.first, canNext = !data.last || data.month < data.last;
  const nav = (on: boolean) => ({ color: INK, border: BORDER, opacity: on ? 1 : 0.35 });

  return (
    <section className="space-y-2">
      <h2 className="text-xs font-semibold uppercase tracking-widest" style={{ color: DIM }}>Results calendar</h2>
      <div className="card-rich p-4 space-y-3">
        <div className="flex items-center gap-3 flex-wrap">
          <button aria-label="Previous month" disabled={!canBack} onClick={() => setMonth(shift(data.month, -1))} className="p-1 rounded-md" style={nav(canBack)}><ChevronLeft size={15} /></button>
          <div className="text-sm font-semibold w-36 text-center" style={{ color: TOP }}>{monthName(data.month)}</div>
          <button aria-label="Next month" disabled={!canNext} onClick={() => setMonth(shift(data.month, 1))} className="p-1 rounded-md" style={nav(canNext)}><ChevronRight size={15} /></button>
          <div className="ml-auto text-[11px]" style={{ color: DIM }}>
            Re-read the day after each result: <b style={{ color: INK }}>{data.updated}</b> updated · <b style={{ color: INK }}>{data.waiting}</b> waiting for Screener{data.gave_up ? ` · ${data.gave_up} not found` : ""}
          </div>
        </div>
        <div className="grid grid-cols-7 gap-1.5">
          {WEEK.map((d) => <div key={d} className="text-center text-[10px] uppercase tracking-wide" style={{ color: DIM }}>{d}</div>)}
          {Array.from({ length: blanks }, (_, i) => <div key={`blank-${i}`} />)}
          {Array.from({ length: total }, (_, i) => {
            const date = `${data.month}-${String(i + 1).padStart(2, "0")}`;
            const d = byDate.get(date), selected = picked === date, today = date === data.today;
            return (
              <button key={date} disabled={!d} onClick={() => setPicked(date)} aria-pressed={selected} aria-label={d ? `${date}: ${d.count} results` : date}
                      className="rounded-lg p-2 text-left" style={{ minHeight: 68, cursor: d ? "pointer" : "default",
                        background: d ? `rgba(201,162,39,${(0.05 + 0.3 * d.count / peak).toFixed(3)})` : "transparent",
                        border: selected ? "1px solid var(--accent-gold-bright)" : today ? "1px solid rgba(201,162,39,0.5)" : BORDER }}>
                <div className="text-[11px]" style={{ color: today ? "var(--accent-gold-bright)" : DIM }}>{i + 1}{today ? " · Today" : ""}</div>
                {d && <div className="text-sm font-semibold tabular-nums" style={{ color: TOP }}>{d.count} <span className="text-[10px] font-normal" style={{ color: INK }}>{d.count === 1 ? "stock" : "stocks"}</span></div>}
                {d && d.held > 0 && <div className="text-[10px] font-semibold" style={{ color: "var(--accent-gold-bright)" }}>{d.held} held</div>}
              </button>
            );
          })}
        </div>
        {picked && <DayPanel on={picked} />}
      </div>
    </section>
  );
}
