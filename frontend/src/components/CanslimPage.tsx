// CANSLIM screen for every stock. A separate read: nothing here feeds the framework's scores.
import { Fragment, useEffect, useState } from "react";
import { ArrowDown, ArrowUp, CircleHelp } from "lucide-react";
import { api } from "../api";
import CanslimGuide from "./CanslimGuide";

type Letter = "c" | "a" | "n" | "s" | "l" | "i" | "m";
type SortKey = Letter | "canslim" | "peer_quality" | "combined";
interface Part { score: number | null; text: string }
export interface CanslimRow { stock_id: string; symbol: string; company_name: string; sector: string | null; basic_industry: string | null;
  c: number | null; a: number | null; n: number | null; s: number | null; l: number | null; i: number | null; m: number | null;
  canslim: number | null; peer_quality: number | null; combined: number | null; letters: number; basis: string | null;
  detail: (Record<Letter, Part> & { peer: { rank: number; of: number; group: string; level: string } | null }) | null }
export interface CanslimResponse { total: number; as_of: string | null; market: (Part & { view?: string }) | null; results: CanslimRow[] }

const LETTERS: { key: Letter; name: string; rule: string }[] = [
  { key: "c", name: "Current earnings", rule: "Latest quarter's profit against a year ago: 25%+ strong, 15%+ ok. Sales only nudge it." },
  { key: "a", name: "Annual earnings", rule: "3-year profit CAGR: 25%+ strong, 15%+ ok. Strong growth with ROE of 17%+ scores 100." },
  { key: "n", name: "New highs", rule: "Within 15% of the 52-week high scores high, within 5% highest." },
  { key: "s", name: "Supply and demand", rule: "10-day volume against the 50-day: 1.25x strong, 1.0x ok." },
  { key: "l", name: "Leader", rule: "RS Rating 1-99, ranked against every stock. 80+ is a leader." },
  { key: "i", name: "Institutions", rule: "FII + DII holding: 20-70% healthy, 10-20% fair, above 70% crowded." },
  { key: "m", name: "Market", rule: "Nifty 50 against its 50- and 200-day averages. The same for every stock." },
];
const PAGE = 100;
const tone = (v: number | null) => (v === null ? "var(--text-dim)" : v >= 70 ? "#4fb3a0" : v >= 50 ? "#c9a227" : "#d9694f");
const cell = (v: number | null) => (v === null ? "—" : v.toFixed(0));

export default function CanslimPage({ onAnalyse }: { onAnalyse?: (stockId: string) => void }) {
  const [data, setData] = useState<CanslimResponse | null>(null);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [sector, setSector] = useState("");
  const [sectors, setSectors] = useState<string[]>([]);
  const [strong, setStrong] = useState("");
  const [sortBy, setSortBy] = useState<SortKey>("canslim");
  const [order, setOrder] = useState<"desc" | "asc">("desc");
  const [page, setPage] = useState(0);
  const [open, setOpen] = useState<string | null>(null);
  const [guide, setGuide] = useState(false);

  useEffect(() => { api.getSectors().then((r) => setSectors(r.sectors)).catch(() => setSectors([])); }, []);
  useEffect(() => { setPage(0); }, [search, sector, strong, sortBy, order]);
  useEffect(() => {
    const params: Record<string, string> = { sort_by: sortBy, order, limit: String(PAGE), offset: String(page * PAGE) };
    if (search.trim()) params.q = search.trim();
    if (sector) params.sector = sector;
    if (strong) params.strong = strong;
    const t = setTimeout(() => {
      api.canslimScores(params).then((r) => { setData(r); setError(""); })
        .catch((e: unknown) => setError(e instanceof Error ? e.message : "Could not load"));
    }, 250);
    return () => clearTimeout(t);
  }, [search, sector, strong, sortBy, order, page]);

  const sort = (key: SortKey) => {
    if (sortBy === key) setOrder((o) => (o === "desc" ? "asc" : "desc"));
    else { setSortBy(key); setOrder("desc"); }
  };
  const Icon = order === "desc" ? ArrowDown : ArrowUp;
  const head = (key: SortKey, label: string, title?: string) => (
    <th key={key} title={title} onClick={() => sort(key)} className="text-right py-2 px-2 font-semibold cursor-pointer select-none whitespace-nowrap">
      {label}{sortBy === key && <Icon size={11} className="inline ml-0.5" />}
    </th>
  );
  const field = { background: "var(--bg-card)", border: "1px solid var(--border-subtle)", color: "var(--text-primary)" };
  const m = data?.market;

  return (
    <div className="space-y-6 fade-in">
      {guide && <CanslimGuide onClose={() => setGuide(false)} />}
      <div className="card-rich p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="eyebrow">CANSLIM</p>
            <h1 className="text-xl font-semibold mb-1" style={{ color: "var(--text-primary)" }}>Growth leaders, on William O'Neil's seven letters</h1>
          </div>
          <button onClick={() => setGuide(true)} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs flex-shrink-0"
                  style={{ color: "var(--accent-gold-bright)", border: "1px solid rgba(201,162,39,0.45)" }}><CircleHelp size={14} /> Explain</button>
        </div>
        <p className="text-sm max-w-3xl" style={{ color: "var(--text-secondary)" }}>
          Every stock scored on earnings growth, new highs, volume, relative strength, institutions and the market. Combined is 60% CANSLIM and 40% peer quality.
          A letter with no data is left out, never counted as zero. This is a separate read: it does not change your Quality, classifications or any other score.</p>
        {m && <p className="text-xs mt-3" style={{ color: "var(--text-secondary)" }}>
          <b style={{ color: tone(m.score) }}>Market (M): {m.view}.</b> {m.text}.
          {(m.score ?? 0) < 50 ? " O'Neil's rule is to hold back from new buying until the market recovers." : ""}{data?.as_of ? ` Prices to ${data.as_of}.` : ""}</p>}
      </div>

      <div className="card-rich p-6">
        <div className="flex flex-wrap items-center gap-3 mb-3">
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search name or symbol…" className="rounded-md px-3 py-1.5 text-xs w-56" style={field} />
          <select value={sector} onChange={(e) => setSector(e.target.value)} className="rounded-md px-3 py-1.5 text-xs" style={field}>
            <option value="">All sectors</option>
            {sectors.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
          <span className="text-[11px]" style={{ color: "var(--text-dim)" }}>Must be strong (70+) on:</span>
          {LETTERS.filter((l) => l.key !== "m").map(({ key, name }) => {
            const on = strong.includes(key);
            return (
              <button key={key} title={name} onClick={() => setStrong(on ? strong.replace(key, "") : strong + key)} className="w-7 h-7 rounded-md text-xs font-semibold"
                      style={{ color: on ? "var(--accent-gold-bright)" : "var(--text-secondary)", background: on ? "rgba(201,162,39,0.14)" : "transparent",
                               border: `1px solid ${on ? "rgba(201,162,39,0.45)" : "var(--border-subtle)"}` }}>{key.toUpperCase()}</button>
            );
          })}
        </div>
        {error && <p className="text-sm mb-2" style={{ color: "#d9694f" }}>{error}</p>}
        {!data && !error && <p className="text-xs" style={{ color: "var(--text-dim)" }}>Loading…</p>}
        {data && <>
          <p className="text-xs mb-2" style={{ color: "var(--text-dim)" }}>{data.total.toLocaleString("en-IN")} {data.total === 1 ? "company" : "companies"}</p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="text-[11px] uppercase tracking-wide" style={{ color: "var(--text-dim)" }}>
                <th className="text-left py-2 pr-3 font-semibold">Company</th>
                {LETTERS.map((l) => head(l.key, l.key.toUpperCase(), `${l.name}. ${l.rule}`))}
                {head("canslim", "CANSLIM", "Average of the letters available")}
                {head("peer_quality", "Peer quality", "Quality percentile among its peers")}
                {head("combined", "Combined", "60% CANSLIM + 40% peer quality")}
              </tr></thead>
              <tbody>
                {data.results.map((r) => (
                  <Fragment key={r.stock_id}>
                    <tr className="cursor-pointer" onClick={() => setOpen(open === r.stock_id ? null : r.stock_id)} style={{ borderTop: "1px solid var(--border-subtle)" }}>
                      <td className="py-2 pr-3">
                        <div className="font-semibold" style={{ color: "var(--text-primary)" }}>{r.company_name}</div>
                        <div className="text-[11px]" style={{ color: "var(--text-dim)" }}>{r.symbol}{r.basic_industry ? ` · ${r.basic_industry}` : ""}</div>
                      </td>
                      {LETTERS.map(({ key }) => <td key={key} className="text-right py-2 px-2 tabular-nums font-semibold" style={{ color: tone(r[key]) }}>{cell(r[key])}</td>)}
                      <td className="text-right py-2 px-2 tabular-nums font-bold" style={{ color: tone(r.canslim) }}>{r.canslim === null ? "—" : r.canslim.toFixed(1)}</td>
                      <td className="text-right py-2 px-2 tabular-nums" style={{ color: tone(r.peer_quality) }}>{cell(r.peer_quality)}</td>
                      <td className="text-right py-2 px-2 tabular-nums font-semibold" style={{ color: tone(r.combined) }}>{r.combined === null ? "—" : r.combined.toFixed(1)}</td>
                    </tr>
                    {open === r.stock_id && r.detail && (
                      <tr><td colSpan={LETTERS.length + 4} className="p-3 text-xs space-y-1" style={{ background: "var(--glass)", color: "var(--text-secondary)" }}>
                        {LETTERS.map(({ key, name }) => (
                          <div key={key}><b style={{ color: tone(r[key]) }}>{key.toUpperCase()} {cell(r[key])}</b> <span style={{ color: "var(--text-dim)" }}>{name}:</span> {r.detail![key]?.text ?? "not read"}</div>
                        ))}
                        <div className="pt-1" style={{ color: "var(--text-dim)" }}>
                          {r.letters} of 7 letters read{r.basis ? ` · Combined: ${r.basis}` : ""}
                          {r.detail.peer ? ` · Quality ranks #${r.detail.peer.rank} of ${r.detail.peer.of} in ${r.detail.peer.group}` : ""}
                          {onAnalyse && <button onClick={() => onAnalyse(r.stock_id)} className="ml-3 underline" style={{ color: "var(--accent-gold-bright)" }}>Run full analysis</button>}
                        </div>
                      </td></tr>
                    )}
                  </Fragment>
                ))}
                {data.results.length === 0 && <tr><td colSpan={LETTERS.length + 4} className="py-6 text-center text-sm" style={{ color: "var(--text-dim)" }}>No stocks match.</td></tr>}
              </tbody>
            </table>
          </div>
          {data.total > PAGE && (
            <div className="flex items-center justify-end gap-3 mt-3 text-xs" style={{ color: "var(--text-secondary)" }}>
              <button disabled={page === 0} onClick={() => setPage(page - 1)} className="px-3 py-1.5 rounded-lg" style={{ border: "1px solid var(--border-subtle)", opacity: page === 0 ? 0.5 : 1 }}>Previous</button>
              <span>Page {page + 1} of {Math.ceil(data.total / PAGE)}</span>
              <button disabled={(page + 1) * PAGE >= data.total} onClick={() => setPage(page + 1)} className="px-3 py-1.5 rounded-lg" style={{ border: "1px solid var(--border-subtle)", opacity: (page + 1) * PAGE >= data.total ? 0.5 : 1 }}>Next</button>
            </div>
          )}
        </>}
      </div>
    </div>
  );
}
