import { useState, useEffect, useMemo } from "react";
import { Layers, X, ChevronRight, Loader2 } from "lucide-react";
import { api } from "../api";
import type { SectorCount, SectorMemberStock } from "../types";
import { MAIN_SECTORS, mainSectorFor } from "../sectorTaxonomy";

const CATEGORY_LABEL: Record<string, string> = {
  LARGE_CAP: "Large Cap",
  MID_CAP: "Mid Cap",
  SMALL_CAP: "Small Cap",
  MICRO_CAP: "Micro Cap",
  NANO_CAP: "Nano Cap",
};
const CATEGORY_COLOR: Record<string, string> = {
  LARGE_CAP: "#4fb3a0",
  MID_CAP: "#c9a227",
  SMALL_CAP: "#e0793c",
  MICRO_CAP: "#d9694f",
  NANO_CAP: "#8b7fd1",
};

function CategoryBadge({ category }: { category: string | null }) {
  if (!category) {
    return <span className="text-[11px]" style={{ color: "var(--text-dim)" }}>—</span>;
  }
  const color = CATEGORY_COLOR[category] || "var(--text-dim)";
  return (
    <span
      className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full flex-shrink-0"
      style={{ background: `${color}17`, border: `1px solid ${color}30`, color }}
    >
      {CATEGORY_LABEL[category] || category}
    </span>
  );
}

function fmtCr(v: number | null) {
  if (v === null) return "—";
  return v >= 1000 ? `₹${(v / 1000).toFixed(1)}k Cr` : `₹${v.toFixed(0)} Cr`;
}

interface Division {
  name: string;
  stocks: SectorMemberStock[];
}

interface MainGroup {
  name: string;
  macroSector: string;
  count: number;
  divisions: Division[];
}

function groupByBasicIndustry(stocks: SectorMemberStock[]): Division[] {
  const byBI = new Map<string, SectorMemberStock[]>();
  const order: string[] = [];
  for (const s of stocks) {
    const key = s.basic_industry || "Other";
    if (!byBI.has(key)) { byBI.set(key, []); order.push(key); }
    byBI.get(key)!.push(s);
  }
  return order
    .map((name) => ({ name, stocks: byBI.get(name)! }))
    .sort((a, b) => b.stocks.length - a.stocks.length);
}

function buildMainGroups(sectors: SectorCount[]): MainGroup[] {
  // sector.sector here is the backend's already-resolved framework name
  // (e.g. "Banks", "Healthcare") — bucket those into the 22 NSE main
  // sectors (+ Other), keeping every underlying stock accounted for.
  const byMain = new Map<string, SectorCount[]>();
  for (const s of sectors) {
    const main = mainSectorFor(s.sector);
    if (!byMain.has(main)) byMain.set(main, []);
    byMain.get(main)!.push(s);
  }

  const macroFor = (name: string) => MAIN_SECTORS.find((m) => m.name === name)?.macroSector || "Other";

  const groups: MainGroup[] = [];
  for (const [name, buckets] of byMain) {
    const allStocks = buckets.flatMap((b) => b.stocks);
    const divisions = buckets.length > 1
      ? buckets
          .map((b) => ({ name: b.sector, stocks: b.stocks }))
          .sort((a, b) => b.stocks.length - a.stocks.length)
      : groupByBasicIndustry(buckets[0].stocks);
    groups.push({ name, macroSector: macroFor(name), count: allStocks.length, divisions });
  }
  return groups.sort((a, b) => b.count - a.count);
}

function MainSectorCard({ group, active, onClick }: { group: MainGroup; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="card-rich interactive p-3.5 text-left"
      style={active ? { borderColor: "rgba(201,162,39,0.5)", background: "rgba(201,162,39,0.06)" } : undefined}
    >
      <span className="text-[10px] uppercase tracking-wide block truncate" style={{ color: "var(--text-dim)" }}>
        {group.macroSector}
      </span>
      <span className="eyebrow block truncate">{group.name}</span>
      <p className="text-2xl font-bold tracking-tight tabular-nums mt-1"
         style={{ color: "var(--text-primary)", fontFamily: "var(--font-display)" }}>
        {group.count}
      </p>
      <span className="text-[11px]" style={{ color: "var(--text-dim)" }}>
        {group.count === 1 ? "stock tracked" : "stocks tracked"}
      </span>
    </button>
  );
}

function StockRow({ stock, onAnalyze, starting }: { stock: SectorMemberStock; onAnalyze: (s: SectorMemberStock) => void; starting: boolean }) {
  const clickable = !!stock.stock_id;
  return (
    <div
      onClick={clickable ? () => onAnalyze(stock) : undefined}
      className={`flex items-center gap-3 py-1.5 ${clickable ? "interactive cursor-pointer" : ""}`}
      style={{ borderBottom: "1px solid var(--border-subtle)" }}
    >
      <div className="flex-1 min-w-0">
        <div className="text-xs truncate" style={{ color: "var(--text-secondary)" }}>{stock.company_name}</div>
        <div className="text-[10px]" style={{ color: "var(--text-dim)" }}>{stock.symbol}</div>
      </div>
      <span className="text-xs tabular-nums flex-shrink-0" style={{ color: "var(--text-primary)", minWidth: 72, textAlign: "right" }}>
        {fmtCr(stock.market_cap_cr)}
      </span>
      <CategoryBadge category={stock.market_cap_category} />
      {clickable && (
        starting
          ? <Loader2 className="h-3.5 w-3.5 animate-spin flex-shrink-0" style={{ color: "var(--text-dim)" }} />
          : <ChevronRight className="h-3.5 w-3.5 flex-shrink-0" style={{ color: "var(--text-dim)" }} />
      )}
    </div>
  );
}

interface Props {
  onAnalysisStarted?: (analysisId: string) => void;
}

export default function SectorCounts({ onAnalysisStarted }: Props) {
  const [sectors, setSectors] = useState<SectorCount[]>([]);
  const [total, setTotal] = useState(0);
  const [loaded, setLoaded] = useState(false);
  const [selectedMain, setSelectedMain] = useState<string | null>(null);
  const [selectedDivision, setSelectedDivision] = useState<string | null>(null);
  const [starting, setStarting] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getSectorCounts().then((data) => {
      setSectors(data.sector_counts || []);
      setTotal(data.total || 0);
      setLoaded(true);
    }).catch(() => setLoaded(true));
  }, []);

  const groups = useMemo(() => buildMainGroups(sectors), [sectors]);

  if (!loaded || groups.length === 0) return null;

  const activeGroup = groups.find((g) => g.name === selectedMain) || null;
  const activeDivision = activeGroup?.divisions.find((d) => d.name === selectedDivision) || null;
  const showDivisionChips = !!activeGroup && activeGroup.divisions.length > 1;
  const visibleStocks = activeGroup
    ? (showDivisionChips ? activeDivision?.stocks : activeGroup.divisions[0]?.stocks) || null
    : null;

  const handleSelectMain = (name: string) => {
    if (name === selectedMain) {
      setSelectedMain(null);
      setSelectedDivision(null);
      return;
    }
    setSelectedMain(name);
    setSelectedDivision(null);
  };

  const handleAnalyze = async (stock: SectorMemberStock) => {
    if (!stock.stock_id || !onAnalysisStarted) return;
    setStarting(stock.stock_id);
    setError("");
    try {
      const { analysis_id } = await api.startAnalysis(stock.stock_id);
      onAnalysisStarted(analysis_id);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to start analysis");
    } finally {
      setStarting(null);
    }
  };

  return (
    <div className="space-y-3 fade-in">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <Layers className="h-3.5 w-3.5" style={{ color: "#c9a227" }} />
          <span className="eyebrow">Stocks by Sector</span>
        </div>
        <span className="text-xs tabular-nums" style={{ color: "var(--text-dim)" }}>{total} tracked</span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-6 gap-2.5">
        {groups.map((g) => (
          <MainSectorCard
            key={g.name}
            group={g}
            active={g.name === selectedMain}
            onClick={() => handleSelectMain(g.name)}
          />
        ))}
      </div>

      {activeGroup && (
        <div className="card-rich p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
              {activeGroup.name} <span style={{ color: "var(--text-dim)", fontWeight: 400 }}>({activeGroup.count})</span>
            </span>
            <button onClick={() => handleSelectMain(activeGroup.name)} aria-label="Close">
              <X className="h-4 w-4" style={{ color: "var(--text-dim)" }} />
            </button>
          </div>

          {showDivisionChips && (
            <div className="flex flex-wrap gap-1.5 mb-3">
              {activeGroup.divisions.map((d) => (
                <button
                  key={d.name}
                  onClick={() => setSelectedDivision(d.name === selectedDivision ? null : d.name)}
                  className="text-[11px] px-2.5 py-1 rounded-full"
                  style={
                    d.name === selectedDivision
                      ? { background: "rgba(201,162,39,0.14)", border: "1px solid rgba(201,162,39,0.5)", color: "var(--text-primary)" }
                      : { background: "var(--surface-2)", border: "1px solid var(--border-subtle)", color: "var(--text-secondary)" }
                  }
                >
                  {d.name} <span style={{ color: "var(--text-dim)" }}>({d.stocks.length})</span>
                </button>
              ))}
            </div>
          )}

          {error && <p className="text-xs mb-2" style={{ color: "#d9694f" }}>{error}</p>}

          {visibleStocks ? (
            <div className="max-h-96 overflow-y-auto space-y-0.5 pr-1">
              {visibleStocks.map((stock) => (
                <StockRow key={stock.symbol} stock={stock} onAnalyze={handleAnalyze} starting={starting === stock.stock_id} />
              ))}
            </div>
          ) : (
            <p className="text-xs" style={{ color: "var(--text-dim)" }}>Select a division above to see its stocks.</p>
          )}
        </div>
      )}
    </div>
  );
}
