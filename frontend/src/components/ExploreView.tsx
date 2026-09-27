import { useState, useEffect, useMemo } from "react";
import { Building2, Layers, Wallet, CheckCircle2, ArrowUpDown } from "lucide-react";
import { api } from "../api";
import type { TaxonomyCombination, ScreenedStock, FullAnalysis } from "../types";
import KpiCard from "./charts/KpiCard";
import ChartCard from "./charts/ChartCard";
import IndustryTreemap from "./charts/IndustryTreemap";
import SectorCounts from "./SectorCounts";
import ScoreScreener from "./ScoreScreener";

interface Props {
  onAnalysisStarted: (analysisId: string) => void;
  recentAnalyses: FullAnalysis[];
  onViewAnalysis: (id: string) => void;
}

type Level = "macro_sector" | "sector" | "industry" | "basic_industry";
type SortMode = "market_cap_desc" | "market_cap_asc" | "name_asc";

const LEVELS: { key: Level; label: string }[] = [
  { key: "macro_sector", label: "Macro Sector" },
  { key: "sector", label: "Sector" },
  { key: "industry", label: "Industry" },
  { key: "basic_industry", label: "Basic Industry" },
];

const STATUS_COLOR: Record<string, string> = {
  COMPLETED: "#4fb3a0", RUNNING: "#c9a227", FAILED: "#d9694f", QUEUED: "#6f7c96",
};
const RATING_COLOR: Record<string, string> = {
  STRONG: "#4fb3a0", GOOD: "#c9a227", FAIR: "#e0793c", WEAK: "#d9694f", POOR: "#d9694f",
};

export default function ExploreView({ onAnalysisStarted, recentAnalyses, onViewAnalysis }: Props) {
  const [combinations, setCombinations] = useState<TaxonomyCombination[]>([]);
  const [taxonomyLoading, setTaxonomyLoading] = useState(true);
  const [filters, setFilters] = useState<Record<Level, string>>({
    macro_sector: "", sector: "", industry: "", basic_industry: "",
  });
  const [stocks, setStocks] = useState<ScreenedStock[]>([]);
  const [descriptions, setDescriptions] = useState<Record<string, string | null>>({});
  const [loading, setLoading] = useState(false);
  const [starting, setStarting] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [sortMode, setSortMode] = useState<SortMode>("market_cap_desc");

  useEffect(() => {
    api.getScreeningTaxonomy()
      .then(({ combinations }) => setCombinations(combinations))
      .catch(() => setCombinations([]))
      .finally(() => setTaxonomyLoading(false));
  }, []);

  const options = useMemo(() => {
    const forLevel = (level: Level, ancestors: Level[]) => {
      const matches = combinations.filter((c) =>
        ancestors.every((a) => !filters[a] || c[a] === filters[a])
      );
      return Array.from(new Set(matches.map((c) => c[level]))).sort();
    };
    return {
      macro_sector: forLevel("macro_sector", []),
      sector: forLevel("sector", ["macro_sector"]),
      industry: forLevel("industry", ["macro_sector", "sector"]),
      basic_industry: forLevel("basic_industry", ["macro_sector", "sector", "industry"]),
    };
  }, [combinations, filters]);

  const handleChange = (level: Level, value: string) => {
    setFilters((prev) => {
      const next = { ...prev, [level]: value };
      const idx = LEVELS.findIndex((l) => l.key === level);
      for (let i = idx + 1; i < LEVELS.length; i++) next[LEVELS[i].key] = "";
      return next;
    });
  };

  const hasAnyFilter = Object.values(filters).some(Boolean);

  useEffect(() => {
    if (!hasAnyFilter) {
      setStocks([]);
      setDescriptions({});
      return;
    }
    setLoading(true);
    setError("");
    api.screenStocks(filters)
      .then(({ stocks, descriptions }) => { setStocks(stocks); setDescriptions(descriptions); })
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to screen stocks"))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.macro_sector, filters.sector, filters.industry, filters.basic_industry]);

  const filteredStocks = stocks.filter((s) =>
    !searchQuery ||
    s.company_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    s.symbol.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const sortStocks = (arr: ScreenedStock[]) => {
    const sorted = [...arr];
    if (sortMode === "market_cap_desc") sorted.sort((a, b) => (b.market_cap_cr ?? -1) - (a.market_cap_cr ?? -1));
    else if (sortMode === "market_cap_asc") sorted.sort((a, b) => (a.market_cap_cr ?? Infinity) - (b.market_cap_cr ?? Infinity));
    else sorted.sort((a, b) => a.company_name.localeCompare(b.company_name));
    return sorted;
  };

  const groups = useMemo(() => {
    const order: string[] = [];
    const byBasicIndustry = new Map<string, ScreenedStock[]>();
    for (const s of filteredStocks) {
      if (!byBasicIndustry.has(s.basic_industry)) { byBasicIndustry.set(s.basic_industry, []); order.push(s.basic_industry); }
      byBasicIndustry.get(s.basic_industry)!.push(s);
    }
    const groupsList = order.map((name) => ({
      name,
      stocks: sortStocks(byBasicIndustry.get(name)!),
      totalCap: byBasicIndustry.get(name)!.reduce((s, x) => s + (x.market_cap_cr ?? 0), 0),
    }));
    return groupsList.sort((a, b) => b.totalCap - a.totalCap);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filteredStocks, sortMode]);

  const handleAnalyze = async (s: ScreenedStock) => {
    if (!s.stock_id) return;
    setStarting(s.stock_id);
    setError("");
    try {
      const { analysis_id } = await api.startAnalysis(s.stock_id);
      onAnalysisStarted(analysis_id);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to start analysis");
    } finally {
      setStarting(null);
    }
  };

  const handleTreemapSelect = (basicIndustry: string) => handleChange("basic_industry", basicIndustry);

  // ── KPI strip figures ────────────────────────────────────────────────────
  const uniqueSectors = new Set(filteredStocks.map((s) => s.sector)).size;
  const avgMarketCap = filteredStocks.length
    ? filteredStocks.reduce((s, x) => s + (x.market_cap_cr ?? 0), 0) / filteredStocks.length
    : 0;
  const analyzableCount = filteredStocks.filter((s) => s.analyzable).length;

  const fmtCr = (v: number) => v >= 1000 ? `₹${(v / 1000).toFixed(1)}k Cr` : `₹${v.toFixed(0)} Cr`;

  return (
    <div className="space-y-6 fade-in">
      <SectorCounts onAnalysisStarted={onAnalysisStarted} />

      <ScoreScreener source="full" onViewAnalysis={onViewAnalysis} />

      {/* Recently analyzed */}
      {recentAnalyses.length > 0 && (
        <div>
          <p className="eyebrow mb-3">Recently Analyzed</p>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
            {recentAnalyses.map((a) => (
              <RecentCard key={a.id} analysis={a} onClick={() => onViewAnalysis(a.id)} />
            ))}
          </div>
        </div>
      )}

      {/* Hero + cascading filters */}
      <div className="card-rich p-6">
        <h2 className="text-lg font-semibold mb-1" style={{ color: "var(--text-primary)" }}>
          Explore by industry classification
        </h2>
        <p className="text-sm mb-5" style={{ color: "var(--text-secondary)" }}>
          {taxonomyLoading
            ? "Loading taxonomy…"
            : `Full NSE classification (Macro Sector → Sector → Industry → Basic Industry) across ${new Set(combinations.map((c) => c.basic_industry)).size} basic industries`}
        </p>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {LEVELS.map(({ key, label }) => (
            <div key={key}>
              <label className="block eyebrow mb-2">{label}</label>
              <select
                value={filters[key]}
                onChange={(e) => handleChange(key, e.target.value)}
                disabled={taxonomyLoading}
                className="w-full rounded-lg px-3 py-2.5 text-sm"
                style={{
                  background: "var(--bg-card)", border: "1px solid var(--border-subtle)",
                  color: filters[key] ? "var(--text-primary)" : "var(--text-muted)",
                  outline: "none", opacity: taxonomyLoading ? 0.5 : 1,
                }}
              >
                <option value="">Any {label.toLowerCase()}…</option>
                {options[key].map((v) => <option key={v} value={v}>{v}</option>)}
              </select>
            </div>
          ))}
        </div>
      </div>

      {!hasAnyFilter ? (
        <div className="rounded-xl px-4 py-10 text-center text-sm"
             style={{ border: "1px dashed var(--border-subtle)", color: "var(--text-muted)" }}>
          Choose at least one level above, or search a stock directly from the top bar.
        </div>
      ) : loading ? (
        <div className="py-12 flex items-center justify-center"><div className="spinner" /></div>
      ) : (
        <>
          {/* KPI strip */}
          <div className="flex flex-wrap gap-4">
            <KpiCard label="Stocks in view" value={String(filteredStocks.length)} icon={Building2} accent="#c9a227" />
            <KpiCard label="Sectors covered" value={String(uniqueSectors)} icon={Layers} accent="#e8c766" />
            <KpiCard label="Avg Market Cap" value={fmtCr(avgMarketCap)} icon={Wallet} accent="#e0793c" />
            <KpiCard label="Analyzable" value={String(analyzableCount)} sub={`of ${filteredStocks.length}`} icon={CheckCircle2} accent="#4fb3a0" />
          </div>

          {/* Treemap */}
          <ChartCard eyebrow="Basic Industry" title="Market cap distribution — click a tile to narrow">
            <IndustryTreemap stocks={filteredStocks} onSelect={handleTreemapSelect} />
          </ChartCard>

          {/* Controls */}
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <label className="eyebrow">
              {`${filteredStocks.length} of ${stocks.length} stocks · ${groups.length} basic industries`}
            </label>
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1 rounded-lg p-1" style={{ border: "1px solid var(--border-subtle)" }}>
                <ArrowUpDown className="h-3 w-3 ml-1.5" style={{ color: "var(--text-dim)" }} />
                <select
                  value={sortMode}
                  onChange={(e) => setSortMode(e.target.value as SortMode)}
                  className="text-xs rounded-md px-2 py-1"
                  style={{ background: "transparent", color: "var(--text-secondary)", border: "none", outline: "none" }}
                >
                  <option value="market_cap_desc">Market Cap (High→Low)</option>
                  <option value="market_cap_asc">Market Cap (Low→High)</option>
                  <option value="name_asc">Name (A→Z)</option>
                </select>
              </div>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Filter by name or symbol…"
                className="rounded-lg px-3 py-2 text-sm"
                style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)", color: "var(--text-primary)", outline: "none", width: 220 }}
              />
            </div>
          </div>

          {groups.length === 0 ? (
            <div className="py-8 text-center text-sm" style={{ color: "var(--text-muted)" }}>No stocks found</div>
          ) : (
            <div className="space-y-5">
              {groups.map((group) => (
                <div key={group.name} className="card-rich overflow-hidden">
                  <div className="px-4 py-3" style={{ background: "rgba(201,162,39,0.06)", borderBottom: "1px solid var(--border-subtle)" }}>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{group.name}</span>
                      <span className="badge badge-gray" style={{ fontSize: 10 }}>
                        {group.stocks.length} stock{group.stocks.length === 1 ? "" : "s"}
                      </span>
                      <span className="badge badge-blue" style={{ fontSize: 10 }}>{fmtCr(group.totalCap)}</span>
                    </div>
                    {descriptions[group.name] && (
                      <p className="text-xs mt-1" style={{ color: "var(--text-secondary)" }}>{descriptions[group.name]}</p>
                    )}
                  </div>
                  {group.stocks.map((s) => (
                    <div key={s.symbol} className="w-full text-left px-4 py-3 flex items-center justify-between gap-4"
                         style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-semibold text-sm" style={{ color: "var(--text-primary)" }}>{s.company_name}</span>
                          <span className="text-xs font-mono" style={{ color: "var(--text-dim)" }}>{s.exchange || "—"}:{s.symbol}</span>
                        </div>
                        <div className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                          {s.macro_sector} · {s.sector} · {s.industry}
                        </div>
                      </div>
                      <div className="flex items-center gap-3 flex-shrink-0">
                        {s.market_cap_cr !== null && (
                          <div className="text-right">
                            <div className="text-xs" style={{ color: "var(--text-dim)" }}>Mkt Cap</div>
                            <div className="text-sm font-semibold tabular-nums" style={{ color: "var(--text-primary)" }}>
                              {fmtCr(s.market_cap_cr)}
                            </div>
                          </div>
                        )}
                        {s.analyzable ? (
                          <button
                            onClick={() => handleAnalyze(s)}
                            disabled={starting === s.stock_id}
                            className="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all"
                            style={{ background: starting === s.stock_id ? "rgba(201,162,39,0.3)" : "#c9a227", color: "white", cursor: starting === s.stock_id ? "not-allowed" : "pointer" }}
                          >
                            {starting === s.stock_id ? "Starting…" : "Analyze"}
                          </button>
                        ) : (
                          <span className="badge badge-gray" style={{ fontSize: 10 }} title="Not in the analysis universe (yfinance-backed stocks table)">Not tracked</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {error && (
        <div className="rounded-lg px-4 py-3 text-sm" style={{ background: "rgba(217,105,79,0.1)", border: "1px solid rgba(217,105,79,0.3)", color: "#d9694f" }}>
          {error}
        </div>
      )}
    </div>
  );
}

function RecentCard({ analysis, onClick }: { analysis: FullAnalysis; onClick: () => void }) {
  const company = analysis.company_info;
  const score = analysis.overall_score;
  return (
    <button onClick={onClick} className="card-rich interactive p-4 text-left w-full">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-semibold text-sm truncate" style={{ color: "var(--text-primary)" }}>
              {company?.company_name || analysis.stock_id}
            </span>
          </div>
          <div className="text-xs font-mono mt-0.5" style={{ color: "var(--text-dim)" }}>
            {company?.exchange}:{company?.symbol}
          </div>
          <div className="flex items-center gap-2 mt-2">
            <span className="badge badge-gray" style={{ color: STATUS_COLOR[analysis.status] || "#6f7c96" }}>{analysis.status}</span>
            {analysis.ai_rating && (
              <span className="badge" style={{
                color: RATING_COLOR[analysis.ai_rating] || "#a9b3c9",
                background: `${RATING_COLOR[analysis.ai_rating] || "#a9b3c9"}15`,
                border: `1px solid ${RATING_COLOR[analysis.ai_rating] || "#a9b3c9"}30`,
              }}>{analysis.ai_rating}</span>
            )}
          </div>
        </div>
        {score !== null && score !== undefined && (
          <div className="flex-shrink-0 text-center">
            <div className="text-2xl font-bold tabular-nums" style={{ color: "var(--accent-blue)" }}>{score.toFixed(0)}</div>
            <div className="text-xs" style={{ color: "var(--text-dim)" }}>/100</div>
          </div>
        )}
      </div>
    </button>
  );
}
