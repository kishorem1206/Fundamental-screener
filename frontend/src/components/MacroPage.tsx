// Market & Macro: the economy, rates, currency, risk appetite and FPI money, each with
// its source and date. Context for reading the market only: nothing on this page feeds
// a score, a gate or a classification.
import { useEffect, useState } from "react";
import { Bar, BarChart, Cell, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../api";
import ResultsCalendar from "./ResultsCalendar";

export interface MacroSeries { id: string; label: string; unit: string; source: string; frequency: string; value: number; date: string;
  stale: boolean; previous: number | null; change: number | null; history: { date: string; value: number }[] }
export interface SectorFlow { sector: string; period_end: string; fortnights: number; latest_net_cr: number; net_cr: number; held_cr: number | null;
  net_pct_of_holding: number | null; rank: number; of: number; history: { date: string; net_cr: number }[] }
export interface MacroOverview { groups: { group: string; series: MacroSeries[] }[];
  yield_curve: { as_of: string; points: { tenor: string; yield: number }[]; source: string } | null;
  imf_gdp: { year: string; growth: number }[]; sector_flows: SectorFlow[];
  headlines: { headline: string; url: string; publisher: string; symbols: string[]; published_at: string | null }[];
  not_read: string[]; not_available: string[] }

const UP = "#4fb3a0", DOWN = "#d9694f", LINE = "#c9a227", INK = "var(--text-secondary)", DIM = "var(--text-dim)";
const tip = { contentStyle: { background: "var(--bg-card)", border: "1px solid var(--border-subtle)", borderRadius: 8, fontSize: 12 },
  labelStyle: { color: "var(--text-dim)" }, itemStyle: { color: "var(--text-primary)" } };
const cr = (v: number) => `${v > 0 ? "+" : v < 0 ? "−" : ""}₹${Math.abs(v).toLocaleString("en-IN", { maximumFractionDigits: 0 })} cr`;
const signed = (v: number, d = 2) => `${v > 0 ? "+" : v < 0 ? "−" : ""}${Math.abs(v).toFixed(d)}`;

function show(s: MacroSeries) {
  if (s.unit === "₹ cr") return cr(s.value);
  const digits = s.unit === "$ bn" || s.id.includes("brent") || s.id === "gold" ? 1 : 2;
  const n = s.value.toLocaleString("en-IN", { maximumFractionDigits: digits, minimumFractionDigits: digits });
  return s.unit === "₹" ? `₹${n}` : s.unit.startsWith("$") ? `$${n}${s.unit === "$ bn" ? " bn" : ""}` : s.unit.startsWith("%") ? `${n}%` : s.unit === "x" ? `${n}x` : n;
}

function Tile({ s }: { s: MacroSeries }) {
  const flow = s.unit === "₹ cr";
  return (
    <div className="card-rich p-3" title={`${s.source}, ${s.frequency}`}>
      <div className="text-xs" style={{ color: DIM }}>{s.label}</div>
      <div className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>{show(s)}</div>
      <div className="text-[11px]" style={{ color: DIM }}>
        {s.date}{s.unit === "% yoy" ? ", yoy" : ""}
        {s.change !== null && s.change !== 0 && !flow && <span style={{ color: INK }}> · {signed(s.change)} on the last reading</span>}
        {s.stale && <span style={{ color: "#e0793c" }}> · old: source has not updated</span>}
      </div>
      {s.history.length > 2 && (
        <div style={{ height: 44, marginTop: 6 }}>
          <ResponsiveContainer width="100%" height="100%">
            {flow ? (
              <BarChart data={s.history} margin={{ top: 2, right: 2, bottom: 2, left: 2 }}>
                <Tooltip {...tip} formatter={(v: number) => [cr(v), s.label]} cursor={{ fill: "rgba(255,255,255,0.05)" }} />
                <ReferenceLine y={0} stroke="var(--border-subtle)" />
                <Bar dataKey="value" radius={[2, 2, 0, 0]}>{s.history.map((p) => <Cell key={p.date} fill={p.value >= 0 ? UP : DOWN} />)}</Bar>
              </BarChart>
            ) : (
              <LineChart data={s.history} margin={{ top: 4, right: 4, bottom: 4, left: 4 }}>
                <YAxis hide domain={["auto", "auto"]} />
                <Tooltip {...tip} formatter={(v: number) => [v.toLocaleString("en-IN"), s.label]} />
                <Line type="monotone" dataKey="value" stroke={LINE} strokeWidth={2} dot={false} isAnimationActive={false} />
              </LineChart>
            )}
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

function MonthlyFlows({ s }: { s: MacroSeries }) {
  return (
    <div className="card-rich p-4">
      <div className="text-sm" style={{ color: "var(--text-primary)" }}>FPI net investment in Indian equity, by month</div>
      <div className="text-[11px] mb-2" style={{ color: DIM }}>{s.source}. Above the line is money in, below is money out.</div>
      <div style={{ height: 200 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={s.history} margin={{ top: 4, right: 8, bottom: 0, left: 8 }}>
            <XAxis dataKey="date" tickFormatter={(d: string) => d.slice(0, 7)} tick={{ fontSize: 10, fill: "#8d99ad" }} minTickGap={40} axisLine={false} tickLine={false} />
            <YAxis tickFormatter={(v: number) => `${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 10, fill: "#8d99ad" }} width={36} axisLine={false} tickLine={false} />
            <Tooltip {...tip} formatter={(v: number) => [cr(v), "Net equity"]} labelFormatter={(d: string) => d.slice(0, 7)} cursor={{ fill: "rgba(255,255,255,0.05)" }} />
            <ReferenceLine y={0} stroke="var(--border-subtle)" />
            <Bar dataKey="value" radius={[3, 3, 0, 0]}>{s.history.map((p) => <Cell key={p.date} fill={p.value >= 0 ? UP : DOWN} />)}</Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function SectorFlows({ rows }: { rows: SectorFlow[] }) {
  const widest = Math.max(...rows.map((r) => Math.abs(r.net_pct_of_holding ?? 0)), 0.01);
  return (
    <div className="card-rich p-4">
      <div className="text-sm" style={{ color: "var(--text-primary)" }}>FPI money by sector, last {rows[0].fortnights} fortnights to {rows[0].period_end}</div>
      <div className="text-[11px] mb-2" style={{ color: DIM }}>
        NSDL fortnightly sector report. Net equity investment as a share of what FPIs hold in the sector, so a small sector can be compared with a large one.
        Shown for context; not part of Relative Strength or any score.</div>
      <table className="w-full text-xs">
        <thead><tr style={{ color: DIM }}>
          <th className="text-left font-medium py-1">Sector</th><th className="text-right font-medium">Net, 3 months</th>
          <th className="text-right font-medium">Last fortnight</th><th className="text-right font-medium">FPI holding</th>
          <th className="text-right font-medium pr-3">% of holding</th><th className="font-medium" style={{ width: "24%" }} /></tr></thead>
        <tbody>{rows.map((r) => {
          const pct = r.net_pct_of_holding ?? 0, w = Math.abs(pct) / widest * 50;
          return (
            <tr key={r.sector} style={{ color: INK, borderTop: "1px solid var(--border-subtle)" }}>
              <td className="py-1">{r.sector}</td>
              <td className="text-right">{cr(r.net_cr)}</td>
              <td className="text-right">{cr(r.latest_net_cr)}</td>
              <td className="text-right">{r.held_cr === null ? "—" : `₹${Math.round(r.held_cr).toLocaleString("en-IN")} cr`}</td>
              <td className="text-right pr-3" style={{ color: "var(--text-primary)" }}>{r.net_pct_of_holding === null ? "—" : `${signed(pct)}%`}</td>
              <td><div className="relative" style={{ height: 10 }}>
                <div className="absolute" style={{ left: "50%", top: 0, bottom: 0, width: 1, background: "var(--border-subtle)" }} />
                <div className="absolute" style={{ top: 1, height: 8, borderRadius: 2, width: `${w}%`, background: pct >= 0 ? UP : DOWN, ...(pct >= 0 ? { left: "50%" } : { right: "50%" }) }} />
              </div></td>
            </tr>);
        })}</tbody>
      </table>
    </div>
  );
}

export default function MacroPage() {
  const [d, setD] = useState<MacroOverview | null>(null);
  const [err, setErr] = useState("");
  useEffect(() => { api.macroOverview().then(setD).catch((e: unknown) => setErr(e instanceof Error ? e.message : "Could not load")); }, []);
  const monthly = d?.groups.flatMap((g) => g.series).find((s) => s.id === "fpi_equity_month");
  return (
    <div className="space-y-6 fade-in">
      <div className="card-rich p-6">
        <p className="eyebrow">Market &amp; Macro</p>
        <h1 className="text-xl font-semibold mb-1" style={{ color: "var(--text-primary)" }}>The backdrop to every stock</h1>
        <p className="text-sm max-w-3xl" style={{ color: "var(--text-secondary)" }}>
          The economy, rates, the rupee, risk appetite and foreign money, from official sources, each with its date. For reading the market only:
          nothing here feeds a score or a decision. Hover a tile for its source.</p>
      </div>
      {err && <div className="text-xs" style={{ color: "var(--accent-red)" }}>{err}</div>}
      {!d && !err && <div className="text-xs" style={{ color: DIM }}>Loading…</div>}
      <ResultsCalendar />
      {d && d.groups.map((g) => (
        <section key={g.group} className="space-y-2">
          <h2 className="text-xs font-semibold uppercase tracking-widest" style={{ color: DIM }}>{g.group}</h2>
          <div className="grid gap-3 grid-cols-2 lg:grid-cols-4">{g.series.map((s) => <Tile key={s.id} s={s} />)}</div>
          {g.group === "FPI flows" && monthly && <MonthlyFlows s={monthly} />}
          {g.group === "FPI flows" && d.sector_flows.length > 0 && <SectorFlows rows={d.sector_flows} />}
          {g.group === "Rates and liquidity" && d.yield_curve && d.yield_curve.points.length > 2 && (
            <div className="card-rich p-4">
              <div className="text-sm" style={{ color: "var(--text-primary)" }}>Government bond yield curve, {d.yield_curve.as_of}</div>
              <div className="text-[11px] mb-2" style={{ color: DIM }}>{d.yield_curve.source}. The deep report's DCF uses this curve's ten-year point as its risk-free rate.</div>
              <div style={{ height: 180 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={d.yield_curve.points} margin={{ top: 6, right: 12, bottom: 0, left: 0 }}>
                    <XAxis dataKey="tenor" tick={{ fontSize: 10, fill: "#8d99ad" }} interval="preserveStartEnd" axisLine={false} tickLine={false} />
                    <YAxis domain={["auto", "auto"]} tick={{ fontSize: 10, fill: "#8d99ad" }} width={34} axisLine={false} tickLine={false} />
                    <Tooltip {...tip} formatter={(v: number) => [`${v.toFixed(2)}%`, "Yield"]} />
                    <Line type="monotone" dataKey="yield" stroke={LINE} strokeWidth={2} dot={{ r: 3, fill: LINE }} isAnimationActive={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
          {g.group === "Long run" && d.imf_gdp.length > 0 && (
            <div className="text-xs" style={{ color: INK }}>IMF projection of India's real GDP growth: {d.imf_gdp.map((p) => `${p.year} ${p.growth.toFixed(1)}%`).join(", ")}.</div>
          )}
        </section>
      ))}
      {d && d.headlines.length > 0 && (
        <section className="space-y-2">
          <h2 className="text-xs font-semibold uppercase tracking-widest" style={{ color: DIM }}>Latest headlines</h2>
          <div className="card-rich p-4 space-y-1.5 text-xs">{d.headlines.map((h) => (
            <div key={h.url} style={{ color: INK }}>
              <a href={h.url} target="_blank" rel="noreferrer" className="underline">{h.headline}</a>
              <span style={{ color: DIM }}> {h.publisher}{h.published_at ? `, ${h.published_at.slice(0, 16).replace("T", " ")}` : ""}{h.symbols.length ? ` · ${h.symbols.join(", ")}` : ""}</span>
            </div>))}</div>
        </section>
      )}
      {d && (d.not_available.length > 0 || d.not_read.length > 0) && (
        <div className="text-[11px]" style={{ color: DIM }}>
          {d.not_available.join(" ")}{d.not_read.length > 0 ? ` Not read yet: ${d.not_read.join(", ")}.` : ""}
          {" "}Policy rates, the dollar rate and bond yields build up day by day: RBI's page shows only today's.</div>
      )}
    </div>
  );
}
