import { useEffect, useMemo, useState } from "react";
import { api } from "../../api";
import type {
  BankRoeAnalysis, BankRoeSimParams, BankRoeSimulation, BankRoeYearRow, FullAnalysis,
} from "../../types";
import ChartCard, { ChartEmptyState, LegendDot } from "../charts/ChartCard";

/* ── Client-side port of `simulate()` in backend/app/calculations/bank_roe_engine.py
   (itself a line-for-line port of the mentor's IDFC FIRST ROE simulator).
   Kept in sync by the backend parity tests; runs here so sliders are instant
   and still work in the offline HTML export. ─────────────────────────────── */
interface Start { px0: number; bv0: number; sh0: number; roe0: number }

function simulate(start: Start, p: BankRoeSimParams): { rows: BankRoeYearRow[]; raised: number; dilution: number; endShares: number } {
  const { px0, bv0, sh0, roe0 } = start;
  const pb0 = px0 / bv0;
  const roeT = p.roe / 100, g = p.g / 100, pay = p.pay / 100, disc = p.disc / 100;
  const yrs = Math.max(p.yrs, 1);
  let eq = bv0 * sh0, sh = sh0, raised = 0, cumDiv = 0;
  const rows: BankRoeYearRow[] = [];
  for (let y = 1; y <= 10; y++) {
    const roe = roe0 + (roeT - roe0) * Math.min(y / yrs, 1);
    let prog = roeT !== roe0 ? (roe - roe0) / (roeT - roe0) : Math.min(y / yrs, 1);
    prog = Math.max(0, Math.min(1, prog));
    const pb = pb0 + (p.pb - pb0) * prog;
    const opening = eq, pat = opening * roe, div = pat * pay;
    cumDiv += div / sh;
    eq = opening + pat - div;
    const need = opening * (1 + g);
    const raise = Math.max(0, need - eq);
    if (raise > 0) {
      const issuePx = (eq / sh) * pb * (1 - disc);
      sh += raise / issuePx;
      eq += raise;
      raised += raise;
    }
    const bvps = eq / sh, eps = pat / sh, price = bvps * pb;
    rows.push({
      year: y, roe, pb, pat, raise, shares: sh, bvps, eps, price, multiple: price / px0,
      total_return_multiple: (price + cumDiv) / px0, cagr: Math.pow(price / px0, 1 / y) - 1,
    });
  }
  return { rows, raised, dilution: sh / sh0 - 1, endShares: sh };
}

function verdictOf(x: number): { text: string; color: string } {
  if (x < 1.3) return { text: "Dead money", color: "#d9694f" };
  if (x < 2.0) return { text: "Underwhelming — below a fixed deposit's cousin", color: "#e0793c" };
  if (x < 3.0) return { text: "Modest compounder", color: "#c9a227" };
  if (x < 5.0) return { text: "Strong compounder", color: "#4fb3a0" };
  if (x < 10.0) return { text: "Multibagger territory", color: "#4fb3a0" };
  return { text: "Rare outcome — check your assumptions twice", color: "#7fb8ff" };
}

const fmtRs = (n: number) => `₹${Math.round(n).toLocaleString("en-IN")}`;
const fmtCr = (n: number | null | undefined) => (n == null ? "—" : `₹${Math.round(n).toLocaleString("en-IN")} Cr`);
const pct = (n: number | null | undefined, d = 1) => (n == null ? "—" : `${n.toFixed(d)}%`);
const CHART_TEXT = "var(--text-dim)";
const GRID = "rgba(255,255,255,0.07)";

function StatBlock({ label, value, sub, color }: { label: string; value: string; sub?: string | null; color?: string }) {
  return (
    <div>
      <p className="text-xs" style={{ color: "var(--text-dim)" }}>{label}</p>
      <p className="text-lg font-semibold mt-0.5" style={{ color: color ?? "var(--text-primary)", fontFamily: "var(--font-display)" }}>{value}</p>
      {sub && <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>{sub}</p>}
    </div>
  );
}

const SLIDERS: { key: keyof BankRoeSimParams; label: string; min: number; max: number; step: number; fmt: (v: number) => string; help: string }[] = [
  { key: "roe", label: "Terminal ROE", min: 4, max: 22, step: 0.5, fmt: (v) => `${v.toFixed(1)}%`, help: "Where ROE ends up. Mature private banks sit at 15–18%." },
  { key: "yrs", label: "Years to get there", min: 1, max: 10, step: 1, fmt: (v) => `${v}`, help: "ROE ramps in a straight line, then holds flat." },
  { key: "g", label: "Balance sheet growth", min: 5, max: 25, step: 1, fmt: (v) => `${v}%`, help: "Equity must grow roughly in step to hold capital adequacy." },
  { key: "pay", label: "Dividend payout", min: 0, max: 35, step: 1, fmt: (v) => `${v}%`, help: "Every rupee paid out is a rupee not retained for growth." },
  { key: "pb", label: "Exit price-to-book", min: 0.6, max: 4, step: 0.1, fmt: (v) => `${v.toFixed(1)}x`, help: "The multiple re-rates gradually, in step with ROE progress." },
  { key: "disc", label: "Placement discount", min: 0, max: 25, step: 1, fmt: (v) => `${v}%`, help: "Fresh equity is issued at a discount to market." },
];

const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));

function PriceChart({ rows, start }: { rows: BankRoeYearRow[]; start: Start }) {
  const W = 720, H = 240, L = 52, R = 16, T = 16, B = 30;
  const iw = W - L - R, ih = H - T - B;
  const mx = Math.max(...rows.map((r) => r.price), start.px0 * 1.15);
  const X = (i: number) => L + (i / 10) * iw;
  const Y = (v: number) => T + ih - (v / mx) * ih;
  const path = (pts: number[][]) => pts.map((p, i) => `${i ? "L" : "M"}${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join(" ");
  const px = [[X(0), Y(start.px0)], ...rows.map((r, i) => [X(i + 1), Y(r.price)])];
  const bv = [[X(0), Y(start.bv0)], ...rows.map((r, i) => [X(i + 1), Y(r.bvps)])];
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Projected share price by year">
      {[0, 1, 2, 3, 4].map((i) => (
        <g key={i}>
          <line x1={L} x2={W - R} y1={Y((mx * i) / 4)} y2={Y((mx * i) / 4)} stroke={GRID} />
          <text x={L - 8} y={Y((mx * i) / 4) + 4} textAnchor="end" fontSize="11" fill={CHART_TEXT}>₹{Math.round((mx * i) / 4)}</text>
        </g>
      ))}
      <line x1={L} x2={W - R} y1={Y(start.px0)} y2={Y(start.px0)} stroke="var(--text-dim)" strokeDasharray="5 5" />
      <path d={`${path(bv)} L ${X(10)} ${T + ih} L ${X(0)} ${T + ih} Z`} fill="rgba(255,255,255,0.08)" />
      <path d={path(px)} fill="none" stroke="#c9a227" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
      {[2, 4, 6, 8, 10].map((y) => (
        <g key={y}>
          <circle cx={X(y)} cy={Y(rows[y - 1].price)} r="5" fill="#c9a227" />
          <text x={X(y)} y={Y(rows[y - 1].price) - 12} textAnchor="middle" fontSize="12" fontWeight="700" fill="var(--text-primary)">{rows[y - 1].multiple.toFixed(1)}x</text>
        </g>
      ))}
      {[0, 2, 4, 6, 8, 10].map((y) => (
        <text key={y} x={X(y)} y={H - 8} textAnchor="middle" fontSize="11" fill={CHART_TEXT}>{y === 0 ? "Now" : `Y${y}`}</text>
      ))}
    </svg>
  );
}

function RaiseChart({ rows, eq0 }: { rows: BankRoeYearRow[]; eq0: number }) {
  const W = 720, H = 180, L = 56, R = 16, T = 14, B = 28;
  const iw = W - L - R, ih = H - T - B;
  const mx = Math.max(...rows.map((r) => r.raise), 1);
  const bw = (iw / 10) * 0.62;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Fresh equity raised by year">
      {[0, 1, 2, 3].map((i) => (
        <g key={i}>
          <line x1={L} x2={W - R} y1={T + ih - (i / 3) * ih} y2={T + ih - (i / 3) * ih} stroke={GRID} />
          <text x={L - 8} y={T + ih - (i / 3) * ih + 4} textAnchor="end" fontSize="11" fill={CHART_TEXT}>{Math.round((mx * i) / 3 / 1000)}k</text>
        </g>
      ))}
      {rows.map((r, i) => {
        const cx = L + (i + 0.5) * (iw / 10);
        const h = (r.raise / mx) * ih;
        return (
          <g key={r.year}>
            {h > 0.5 && <rect x={cx - bw / 2} y={T + ih - h} width={bw} height={h} rx="5" fill={r.raise > eq0 * 0.1 ? "#d9694f" : "rgba(255,255,255,0.25)"} />}
            <text x={cx} y={H - 8} textAnchor="middle" fontSize="11" fill={CHART_TEXT}>Y{r.year}</text>
          </g>
        );
      })}
    </svg>
  );
}

function CrossChart({ p, roe0 }: { p: BankRoeSimParams; roe0: number }) {
  const W = 560, H = 260, L = 44, R = 16, T = 16, B = 40;
  const iw = W - L - R, ih = H - T - B;
  const pay = p.pay / 100, rMin = 4, rMax = 22, gMax = 26;
  const X = (r: number) => L + ((r - rMin) / (rMax - rMin)) * iw;
  const Y = (g: number) => T + ih - (g / gMax) * ih;
  const cross = p.g / (1 - pay);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Self-funded growth versus balance sheet growth">
      {[0, 5, 10, 15, 20, 25].map((g) => (
        <g key={g}>
          <line x1={L} x2={W - R} y1={Y(g)} y2={Y(g)} stroke={GRID} />
          <text x={L - 8} y={Y(g) + 4} textAnchor="end" fontSize="11" fill={CHART_TEXT}>{g}%</text>
        </g>
      ))}
      <line x1={L} x2={W - R} y1={Y(p.g)} y2={Y(p.g)} stroke="#d9694f" strokeWidth="2.5" />
      <line x1={X(rMin)} y1={Y(rMin * (1 - pay))} x2={X(rMax)} y2={Y(rMax * (1 - pay))} stroke="var(--text-primary)" strokeWidth="2.5" />
      {cross >= rMin && cross <= rMax && (
        <g>
          <circle cx={X(cross)} cy={Y(p.g)} r="6" fill="#d9694f" />
          <text x={X(cross)} y={Y(p.g) - 12} textAnchor="middle" fontSize="12" fontWeight="700" fill="var(--text-primary)">{cross.toFixed(1)}% ROE</text>
        </g>
      )}
      {[[roe0, "Today"], [p.roe, "Your target"]].map(([r, lab]) =>
        (r as number) >= rMin && (r as number) <= rMax ? (
          <g key={lab as string}>
            <line x1={X(r as number)} x2={X(r as number)} y1={T} y2={T + ih} stroke="var(--text-dim)" strokeDasharray="4 4" />
            <text x={X(r as number)} y={T + ih + 16} textAnchor="middle" fontSize="11" fill="var(--text-muted)">{lab as string}</text>
          </g>
        ) : null)}
      {[4, 10, 16, 22].map((r) => (
        <text key={r} x={X(r)} y={H - 6} textAnchor="middle" fontSize="11" fill={CHART_TEXT}>{r}%</text>
      ))}
    </svg>
  );
}

export default function BankRoeSection({ analysis }: { analysis: FullAnalysis }) {
  const companyId = analysis.company_info?.stock_id || analysis.stock_id;
  const [data, setData] = useState<BankRoeAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [params, setParams] = useState<BankRoeSimParams | null>(null);
  const [activePreset, setActivePreset] = useState<string | null>(null);

  useEffect(() => {
    if (!companyId) return;
    setLoading(true);
    api.getBankRoe(companyId)
      .then((r) => {
        setData(r);
        setError(false);
        const def = r.presets?.find((p) => p.key === r.default_preset) ?? r.presets?.[0];
        if (def) { setParams(def.params); setActivePreset(def.key ?? null); }
      })
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [companyId]);

  const start: Start | null = useMemo(() => {
    const s = data?.start;
    return s ? { px0: s.price, bv0: s.bvps, sh0: s.shares_cr, roe0: s.run_rate_roe / 100 } : null;
  }, [data]);

  const sim = useMemo(() => (start && params ? simulate(start, params) : null), [start, params]);

  if (loading) return <div className="text-sm p-6" style={{ color: "var(--text-dim)" }}>Loading ROE &amp; Valuation…</div>;
  if (error || !data) return <div className="text-sm p-6" style={{ color: "var(--text-dim)" }}>ROE &amp; Valuation is unavailable for this company right now.</div>;
  if (!data.available || !data.start || !start || !params || !sim) {
    return (
      <div className="card-rich p-6 text-sm" style={{ color: "var(--text-dim)" }}>
        {data.reason ?? "ROE & Valuation modelling is not available for this company."}
      </div>
    );
  }

  const s = data.start;
  const last = sim.rows[9];
  const verdict = verdictOf(last.multiple);
  const selfG = params.roe * (1 - params.pay / 100);
  const cross = params.pay < 100 ? params.g / (1 - params.pay / 100) : null;
  const bvMult = last.bvps / s.bvps;
  const pbMult = last.pb / (s.price / s.bvps);
  const attrMax = Math.max(bvMult, pbMult, 1);
  const latestDupont = data.dupont?.[data.dupont.length - 1];
  const vc = data.valuation_check;

  const setParam = (key: keyof BankRoeSimParams, v: number) => {
    setActivePreset(null);
    setParams({ ...params, [key]: v });
  };

  return (
    <div className="space-y-6">
      {/* 1. Where the bank stands */}
      <div className="card-rich p-5">
        <p className="eyebrow">Where it stands today</p>
        <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>
          A good bank and a good investment are two different things. The number that connects them is ROE — and what it does to book value and the price.
        </p>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-5">
          <StatBlock label="Run-rate ROE" value={pct(s.run_rate_roe)} sub={s.run_rate_source} color="#c9a227" />
          <StatBlock label="Price / Book" value={`${s.pb.toFixed(2)}x`} sub={`₹${s.price.toFixed(2)} on BV ₹${s.bvps.toFixed(1)}`} />
          <StatBlock label="Market-implied ROE" value={pct(vc?.market_implied_roe)} sub={vc ? `at COE ${vc.coe}% / growth ${vc.long_run_growth}%` : null} />
          <StatBlock label="Payout ratio" value={pct(s.payout_pct)} />
          <StatBlock label="Book value / share" value={`₹${s.bvps.toFixed(1)}`} sub={`Net worth ${fmtCr(s.equity_cr)}`} />
          <StatBlock label="Shares outstanding" value={`${Math.round(s.shares_cr).toLocaleString("en-IN")} Cr`} />
          <StatBlock label="ROA / leverage (last FY)" value={latestDupont ? `${latestDupont.roa.toFixed(2)}% × ${latestDupont.leverage.toFixed(1)}x` : "—"} sub={latestDupont ? `= ROE ${latestDupont.roe.toFixed(1)}% (${latestDupont.fy}, avg balances)` : null} />
          <StatBlock label="Trailing P/E" value={s.ttm_pe != null ? `${s.ttm_pe.toFixed(1)}x` : "—"} sub={s.ttm_pat_cr != null ? `TTM PAT ${fmtCr(s.ttm_pat_cr)}` : null} />
        </div>
        {data.insights && data.insights.length > 0 && (
          <ul className="space-y-2 mt-5">
            {data.insights.map((t, i) => (
              <li key={i} className="flex items-start gap-2 text-sm" style={{ color: "var(--text-muted)" }}>
                <span className="w-1.5 h-1.5 rounded-full flex-shrink-0 mt-1.5" style={{ background: "#c9a227" }} />
                <span>{t}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* 2. Simulator */}
      <div className="grid grid-cols-1 lg:grid-cols-[340px_1fr] gap-6 items-start">
        <div className="card-rich p-5">
          <p className="eyebrow">The ROE simulator</p>
          <div className="flex flex-wrap gap-2 mt-3 mb-5">
            {data.presets?.map((pr) => (
              <button
                key={pr.key}
                onClick={() => { setParams(pr.params); setActivePreset(pr.key ?? null); }}
                className="text-xs font-semibold rounded-full px-3 py-1.5"
                style={{
                  background: activePreset === pr.key ? "#c9a227" : "rgba(255,255,255,0.05)",
                  color: activePreset === pr.key ? "#1a1a1a" : "var(--text-muted)",
                  border: "1px solid var(--border-subtle)",
                }}
              >
                {pr.name}
              </button>
            ))}
          </div>
          {SLIDERS.map((sl) => (
            <div key={sl.key} className="mb-4">
              <div className="flex justify-between items-baseline">
                <span className="text-xs font-semibold" style={{ color: "var(--text-primary)" }}>{sl.label}</span>
                <span className="text-sm font-semibold" style={{ color: "var(--text-primary)", fontFamily: "var(--font-display)" }}>{sl.fmt(params[sl.key])}</span>
              </div>
              <input
                type="range" min={sl.min} max={sl.max} step={sl.step} className="w-full"
                value={clamp(params[sl.key], sl.min, sl.max)}
                onChange={(e) => setParam(sl.key, parseFloat(e.target.value))}
                aria-label={sl.label}
              />
              <p className="text-[11px]" style={{ color: "var(--text-dim)" }}>{sl.help}</p>
            </div>
          ))}
          <p className="text-[11px]" style={{ color: "var(--text-dim)" }}>
            Today: ROE {s.run_rate_roe.toFixed(1)}%, P/B {s.pb.toFixed(2)}x, payout {s.payout_pct.toFixed(0)}%
            {s.balance_sheet_growth_pct != null ? `, balance sheet grew ${s.balance_sheet_growth_pct.toFixed(0)}% last year` : ""}.
          </p>
        </div>

        <div className="space-y-6">
          <div className="card-rich p-5">
            <div className="flex items-end gap-8 flex-wrap">
              <div>
                <p className="text-xs" style={{ color: "var(--text-dim)" }}>Price multiple in 10 years</p>
                <p className="font-bold" style={{ fontSize: 56, lineHeight: 1, fontFamily: "var(--font-display)", color: "var(--text-primary)" }}>
                  {last.multiple.toFixed(1)}<span style={{ fontSize: 24 }}>x</span>
                </p>
              </div>
              <StatBlock label="Price in 10 yrs" value={fmtRs(last.price)} />
              <StatBlock label="Price CAGR" value={pct(last.cagr * 100)} />
              <StatBlock label="With dividends" value={`${last.total_return_multiple.toFixed(1)}x`} />
            </div>
            <span className="inline-block mt-4 rounded-full px-4 py-1.5 text-sm font-semibold" style={{ background: "rgba(255,255,255,0.06)", color: verdict.color }}>
              {verdict.text}
            </span>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 mt-5">
              {[2, 4, 6, 8, 10].map((y) => {
                const r = sim.rows[y - 1];
                return (
                  <div key={y} className="rounded-xl p-3" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)" }}>
                    <p className="text-[11px] uppercase" style={{ color: "var(--text-dim)" }}>Year {y}</p>
                    <p className="text-lg font-semibold" style={{ color: "var(--text-primary)", fontFamily: "var(--font-display)" }}>{fmtRs(r.price)}</p>
                    <p className="text-xs" style={{ color: "var(--text-muted)" }}>{r.multiple.toFixed(2)}x · {pct(r.cagr * 100)} p.a.</p>
                  </div>
                );
              })}
            </div>
          </div>

          <ChartCard eyebrow="Price trajectory" title="Book value per share compounding × the P/B the market pays as ROE improves"
            legend={<><LegendDot color="#c9a227" label="Projected price" /><LegendDot color="rgba(255,255,255,0.25)" label="Book value / share" /></>}>
            <PriceChart rows={sim.rows} start={start} />
          </ChartCard>

          <ChartCard eyebrow="Where the return comes from" title="Total multiple = book value compounding × multiple re-rating. Nothing else.">
            {[["Book value compounding", bvMult, "var(--text-primary)"], ["Multiple re-rating", pbMult, "#c9a227"]].map(([lab, v, col]) => (
              <div key={lab as string} className="grid grid-cols-[150px_1fr_60px] gap-3 items-center text-sm mb-2">
                <span style={{ color: "var(--text-muted)" }}>{lab as string}</span>
                <span className="h-3 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.08)" }}>
                  <span className="block h-full rounded-full" style={{ width: `${((v as number) / attrMax) * 100}%`, background: col as string }} />
                </span>
                <span className="text-right font-semibold" style={{ color: "var(--text-primary)" }}>{(v as number).toFixed(2)}x</span>
              </div>
            ))}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-5">
              <StatBlock label="Fresh equity raised" value={`${fmtRs(sim.raised / 1000)}k Cr`} sub="over 10 years" />
              <StatBlock label="Share count" value={`+${(sim.dilution * 100).toFixed(0)}%`} sub={`${Math.round(sim.endShares).toLocaleString("en-IN")} Cr shares`} />
              <StatBlock label="EPS in year 10" value={`₹${last.eps.toFixed(1)}`} sub={s.eps_ttm != null ? `from ₹${s.eps_ttm.toFixed(2)} trailing` : null} />
              <StatBlock label="Book value year 10" value={`₹${Math.round(last.bvps)}`} sub={`from ₹${s.bvps.toFixed(1)} today`} />
            </div>
          </ChartCard>

          <ChartCard eyebrow="Dilution" title="Fresh equity the bank has to raise, year by year (red = more than 10% of today's equity)">
            <RaiseChart rows={sim.rows} eq0={s.equity_cr} />
            <div className="overflow-x-auto mt-4">
              <table className="w-full text-xs">
                <thead>
                  <tr style={{ color: "var(--text-dim)" }}>
                    {["Year", "ROE", "PAT ₹Cr", "Raise ₹Cr", "Shares Cr", "BVPS ₹", "EPS ₹", "P/B", "Price ₹"].map((h) => (
                      <th key={h} className={`py-2 ${h === "Year" ? "text-left" : "text-right"} font-semibold`}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {sim.rows.map((r) => (
                    <tr key={r.year} style={{ borderTop: "1px solid rgba(255,255,255,0.06)", color: "var(--text-muted)" }}>
                      <td className="py-1.5">Year {r.year}</td>
                      <td className="text-right tabular-nums">{pct(r.roe * 100)}</td>
                      <td className="text-right tabular-nums">{Math.round(r.pat).toLocaleString("en-IN")}</td>
                      <td className="text-right tabular-nums" style={{ color: r.raise > s.equity_cr * 0.1 ? "#d9694f" : undefined }}>{r.raise < 1 ? "—" : Math.round(r.raise).toLocaleString("en-IN")}</td>
                      <td className="text-right tabular-nums">{Math.round(r.shares)}</td>
                      <td className="text-right tabular-nums">{r.bvps.toFixed(1)}</td>
                      <td className="text-right tabular-nums">{r.eps.toFixed(1)}</td>
                      <td className="text-right tabular-nums">{r.pb.toFixed(2)}x</td>
                      <td className="text-right tabular-nums" style={{ color: "var(--text-primary)" }}>{Math.round(r.price)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </ChartCard>
        </div>
      </div>

      {/* 3. The crossover */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card-rich p-5">
          <p className="eyebrow">The crossover that decides everything</p>
          <p className="text-sm font-semibold mt-1" style={{ color: "var(--text-primary)" }}>Self-funded growth = ROE × (1 − payout)</p>
          <p className="text-sm mt-3" style={{ color: "var(--text-muted)" }}>
            A bank can fund its own growth only out of retained profit. At <strong>{s.run_rate_roe.toFixed(1)}% ROE</strong> and a {s.payout_pct.toFixed(0)}% payout it
            funds about <strong>{data.sustainability?.self_funded_growth.toFixed(1)}%</strong> growth
            {s.balance_sheet_growth_pct != null ? <> against a balance sheet that grew <strong>{s.balance_sheet_growth_pct.toFixed(0)}%</strong></> : null}.
            The gap has to come from new shares — which is why ROE, not profit, is the number worth watching.
          </p>
          <p className="text-sm mt-3" style={{ color: "var(--text-muted)" }}>
            {selfG >= params.g
              ? <>At your <strong>{params.roe}% ROE</strong> setting it funds <strong>{selfG.toFixed(1)}%</strong> — more than the <strong>{params.g}%</strong> growth you set. No dilution needed.</>
              : <>At your <strong>{params.roe}% ROE</strong> setting it funds only <strong>{selfG.toFixed(1)}%</strong> against <strong>{params.g}%</strong> — a <strong>{(params.g - selfG).toFixed(1)}-point gap</strong> paid for in new shares every year{cross != null ? <>; it needs <strong>{cross.toFixed(1)}% ROE</strong> to stop asking</> : null}.</>}
          </p>
        </div>
        <ChartCard eyebrow="Move ROE, watch the gap close" title="Self-funded growth vs your growth setting"
          legend={<><LegendDot color="var(--text-primary)" label="Self-funded growth" /><LegendDot color="#d9694f" label="Your growth setting" /></>}>
          <CrossChart p={params} roe0={s.run_rate_roe} />
        </ChartCard>
      </div>

      {/* 4. Diagnostics: DuPont + dilution + valuation cross-check */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <ChartCard eyebrow="DuPont" title="ROE = ROA × leverage (average balances)">
          {data.dupont && data.dupont.length > 0 ? (
            <table className="w-full text-xs">
              <thead><tr style={{ color: "var(--text-dim)" }}>{["FY", "ROE", "ROA", "Leverage", "Equity growth"].map((h, i) => <th key={h} className={`py-2 font-semibold ${i ? "text-right" : "text-left"}`}>{h}</th>)}</tr></thead>
              <tbody>
                {data.dupont.map((d) => (
                  <tr key={d.fy} style={{ borderTop: "1px solid rgba(255,255,255,0.06)", color: "var(--text-muted)" }}>
                    <td className="py-1.5">{d.fy}</td>
                    <td className="text-right tabular-nums" style={{ color: "var(--text-primary)" }}>{pct(d.roe)}</td>
                    <td className="text-right tabular-nums">{pct(d.roa, 2)}</td>
                    <td className="text-right tabular-nums">{d.leverage.toFixed(1)}x</td>
                    <td className="text-right tabular-nums">{pct(d.equity_growth)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : <ChartEmptyState message="Not enough balance-sheet history" />}
          <p className="text-[11px] mt-3" style={{ color: "var(--text-dim)" }}>
            Do not credit a high ROE to business quality without checking leverage and credit cost.
          </p>
        </ChartCard>

        <ChartCard eyebrow="Valuation cross-check" title="What ROE does the market price in?">
          <div className="grid grid-cols-2 gap-4">
            <StatBlock label="Current P/B" value={`${s.pb.toFixed(2)}x`} />
            <StatBlock label="Market-implied ROE" value={pct(vc?.market_implied_roe)} sub="(P/B × (COE − g)) + g" />
            <StatBlock label="Justified P/B at run-rate ROE" value={vc?.justified_pb_at_run_rate != null ? `${vc.justified_pb_at_run_rate.toFixed(2)}x` : "—"} sub="(ROE − g) / (COE − g)" />
            <StatBlock label="Mentor's P/B for this ROE" value={vc ? `${vc.pb_anchor_for_run_rate_roe.toFixed(2)}x` : "—"} sub="anchor curve used for presets" />
          </div>
          <p className="text-[11px] mt-3" style={{ color: "var(--text-dim)" }}>
            COE {vc?.coe}% and long-run growth {vc?.long_run_growth}% are fixed assumptions for this cross-check only; the simulator's exit P/B is always your own input.
          </p>
          {data.share_history && data.share_history.length > 0 ? (
            <div className="mt-4">
              <p className="text-xs font-semibold mb-1" style={{ color: "var(--text-primary)" }}>Implied share count (equity ÷ BVPS)</p>
              {data.share_history.map((h) => (
                <p key={h.fy} className="text-xs" style={{ color: "var(--text-muted)" }}>
                  {h.fy}: {Math.round(h.shares_cr).toLocaleString("en-IN")} Cr {h.yoy_pct != null ? `(${h.yoy_pct >= 0 ? "+" : ""}${h.yoy_pct.toFixed(1)}% YoY)` : ""}
                </p>
              ))}
            </div>
          ) : (
            <p className="text-[11px] mt-4" style={{ color: "var(--text-dim)" }}>
              Share-count history unavailable — it is derived from historical book value per share, which fills in once this company's valuation history has been built.
            </p>
          )}
        </ChartCard>
      </div>

      {/* 5. Checklist */}
      <ChartCard eyebrow="What to actually check each quarter" title="Not the share price. These seven, in this order.">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {data.checklist?.map((c, i) => (
            <div key={c.key} className="rounded-xl p-4 flex gap-3" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)" }}>
              <span className="w-6 h-6 rounded-full flex-shrink-0 grid place-items-center text-[11px] font-bold" style={{ background: "#c9a227", color: "#1a1a1a" }}>{i + 1}</span>
              <div>
                <p className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                  {c.title}
                  {c.value != null && <span className="ml-2" style={{ color: "#e8c766" }}>{c.value.toFixed(1)} {c.unit}</span>}
                </p>
                <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>{c.why}</p>
                {c.series && c.series.length > 1 && (
                  <p className="text-[11px] mt-1 tabular-nums" style={{ color: "var(--text-dim)" }}>
                    {c.series.map((x) => x.annualised_roe.toFixed(1)).join(" → ")}% (annualised, last {c.series.length} quarters)
                  </p>
                )}
                {c.value == null && <p className="text-[11px] mt-1" style={{ color: "var(--text-dim)" }}>Not yet sourced for this company.</p>}
              </div>
            </div>
          ))}
        </div>
      </ChartCard>

      <p className="text-xs rounded-xl p-4" style={{ background: "rgba(255,255,255,0.03)", color: "var(--text-dim)" }}>{data.disclaimer}</p>
    </div>
  );
}
