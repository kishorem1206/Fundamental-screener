import { useState } from "react";
import type { MarketCapCategory, ScreenResult, StockMatch } from "../types";

const MCAP_BADGE: Record<MarketCapCategory, string> = {
  LARGE_CAP: "bg-blue-900/50 text-blue-300 border border-blue-800",
  MID_CAP:   "bg-purple-900/50 text-purple-300 border border-purple-800",
  SMALL_CAP: "bg-yellow-900/50 text-yellow-300 border border-yellow-800",
  MICRO_CAP: "bg-gray-800 text-gray-400 border border-gray-700",
};

const MCAP_LABEL: Record<MarketCapCategory, string> = {
  LARGE_CAP: "Large",
  MID_CAP:   "Mid",
  SMALL_CAP: "Small",
  MICRO_CAP: "Micro",
};

function rsiColor(v: number | null): string {
  if (v === null) return "text-gray-500";
  if (v < 30) return "text-green-400 font-semibold";
  if (v > 70) return "text-red-400 font-semibold";
  return "text-gray-200";
}

function pbColor(v: number | null): string {
  if (v === null) return "text-gray-500";
  if (v < 0.2) return "text-green-400 font-semibold";
  if (v > 0.8) return "text-red-400 font-semibold";
  return "text-gray-200";
}

function volumeRatioColor(v: number | null): string {
  if (v === null) return "text-gray-500";
  if (v >= 200) return "text-purple-400 font-semibold";
  if (v >= 150) return "text-blue-400 font-semibold";
  if (v >= 100) return "text-green-400";
  return "text-gray-500";
}

function volumeSignalLabel(ratio: number | null): string {
  if (ratio === null) return "—";
  if (ratio >= 200) return "EXCEPTIONAL";
  if (ratio >= 150) return "STRONG";
  if (ratio >= 100) return "ABOVE AVG";
  return "BELOW AVG";
}

function getIndicatorValue(stock: StockMatch, indicator: string, field: string, tf: string): number | null {
  const key = `${indicator}_${tf}`;
  const data = stock.indicators?.[key];
  return data?.[field] ?? null;
}

interface Column {
  key: string;
  label: string;
  indicator: string;
  field: string;
  tf: string;
}

function detectColumns(stocks: StockMatch[]): Column[] {
  const cols: Column[] = [];
  const seen = new Set<string>();
  for (const s of stocks) {
    for (const key of Object.keys(s.indicators ?? {})) {
      if (seen.has(key)) continue;
      seen.add(key);
      const [indicator, tf] = key.split("_");
      if (indicator === "rsi") {
        cols.push({ key: `${key}_value`, label: `RSI (${tf})`, indicator, field: "value", tf });
      } else if (indicator === "bollinger") {
        cols.push({ key: `${key}_percent_b`, label: `%B (${tf})`, indicator, field: "percent_b", tf });
        cols.push({ key: `${key}_upper`, label: `Upper (${tf})`, indicator, field: "upper", tf });
      } else if (indicator === "volume_strength") {
        cols.push({ key: `${key}_volume_ratio`, label: `Vol Ratio (${tf})`, indicator, field: "volume_ratio", tf });
        cols.push({ key: `${key}_volume_score`, label: `Vol Score (${tf})`, indicator, field: "volume_score", tf });
      }
    }
  }
  return cols;
}

type SortDir = "asc" | "desc";

interface Props {
  result:       ScreenResult;
  page:         number;
  pageSize:     number;
  onPageChange: (p: number) => void;
  divMatches?:  Set<string>;
  macdMatches?: Set<string>;
}

function downloadCsv(filename: string, rows: Record<string, unknown>[]) {
  if (!rows.length) return;
  const keys = Object.keys(rows[0]);
  const escape = (v: unknown) => {
    const s = String(v ?? "");
    return s.includes(",") || s.includes('"') || s.includes("\n")
      ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const csv = [keys.join(","), ...rows.map(r => keys.map(k => escape(r[k])).join(","))].join("\n");
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
  a.download = filename;
  a.click();
}

// Score for cross-signal sorting: 2 = both, 1 = one, 0 = neither
function crossScore(symbol: string, divMatches: Set<string>, macdMatches: Set<string>): number {
  return (divMatches.has(symbol) ? 1 : 0) + (macdMatches.has(symbol) ? 1 : 0);
}

export function ResultsTable({ result, page, pageSize, onPageChange, divMatches = new Set(), macdMatches = new Set() }: Props) {
  const [sortCol, setSortCol] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<SortDir>("asc");

  const hasCrossFilters = divMatches.size > 0 || macdMatches.size > 0;

  const indCols = detectColumns(result.stocks);

  function toggleSort(col: string) {
    if (sortCol === col) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortCol(col);
      setSortDir("asc");
    }
  }

  const sortedStocks = [...result.stocks].sort((a, b) => {
    // Cross-signal matches always float to top (highest score first)
    if (hasCrossFilters) {
      const diff = crossScore(b.symbol, divMatches, macdMatches) - crossScore(a.symbol, divMatches, macdMatches);
      if (diff !== 0) return diff;
    }

    if (!sortCol) return 0;
    let aVal: string | number | null = null;
    let bVal: string | number | null = null;
    if (sortCol === "symbol") {
      aVal = a.symbol;
      bVal = b.symbol;
    } else {
      const col = indCols.find((c) => c.key === sortCol);
      if (col) {
        aVal = getIndicatorValue(a, col.indicator, col.field, col.tf);
        bVal = getIndicatorValue(b, col.indicator, col.field, col.tf);
      }
    }
    if (aVal === null && bVal === null) return 0;
    if (aVal === null) return 1;
    if (bVal === null) return -1;
    const cmp = aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
    return sortDir === "asc" ? cmp : -cmp;
  });

  const totalPages = Math.ceil(result.total_matched / pageSize);

  // Count matches for the stats bar
  const divCount  = result.stocks.filter((s) => divMatches.has(s.symbol)).length;
  const macdCount = result.stocks.filter((s) => macdMatches.has(s.symbol)).length;
  const bothCount = result.stocks.filter((s) => divMatches.has(s.symbol) && macdMatches.has(s.symbol)).length;

  const SortIcon = ({ col }: { col: string }) =>
    sortCol !== col ? (
      <span className="opacity-30">↕</span>
    ) : sortDir === "asc" ? (
      <span className="text-blue-400">↑</span>
    ) : (
      <span className="text-blue-400">↓</span>
    );

  return (
    <div className="flex flex-col gap-3">
      {/* Stats bar */}
      <div className="flex items-center justify-between text-xs text-gray-500">
        <div className="flex items-center gap-3 flex-wrap">
          <span>
            <span className="text-gray-200 font-medium">{result.total_matched}</span> matched /{" "}
            {result.stocks_screened} screened · {result.execution_time_ms.toFixed(0)}ms
          </span>
          {hasCrossFilters && (
            <span className="flex items-center gap-2">
              {divMatches.size > 0 && (
                <span className="flex items-center gap-1">
                  <span className="inline-block w-2 h-2 rounded-full bg-emerald-400" />
                  <span className="text-emerald-400">{divCount} div</span>
                </span>
              )}
              {macdMatches.size > 0 && (
                <span className="flex items-center gap-1">
                  <span className="inline-block w-2 h-2 rounded-full bg-blue-400" />
                  <span className="text-blue-400">{macdCount} MACD</span>
                </span>
              )}
              {divMatches.size > 0 && macdMatches.size > 0 && (
                <span className="text-yellow-400 font-medium">{bothCount} both ✦</span>
              )}
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <span className="text-gray-600">{result.universe.replace(/_/g, " ")}</span>
          <button
            onClick={() => {
              const rows = sortedStocks.map(s => {
                const base: Record<string, unknown> = {
                  symbol: s.symbol, exchange: s.exchange,
                  company: s.company_name, sector: s.sector,
                  cap: s.market_cap_category,
                  rsi_div_match: divMatches.has(s.symbol),
                  macd_match: macdMatches.has(s.symbol),
                };
                indCols.forEach(c => {
                  base[c.label] = getIndicatorValue(s, c.indicator, c.field, c.tf) ?? "";
                });
                return base;
              });
              downloadCsv(`screen_${result.universe}_${new Date().toISOString().slice(0,10)}.csv`, rows);
            }}
            className="flex items-center gap-1 px-2 py-1 rounded border border-gray-700 text-gray-400 hover:border-gray-500 hover:text-gray-200 transition-colors"
          >
            ↓ CSV
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-lg border border-gray-800">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800 bg-gray-900/60">
              <th className="text-left py-2.5 px-3 text-xs font-medium text-gray-500 uppercase tracking-wider w-8">#</th>
              <th
                className="text-left py-2.5 px-3 text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-300 select-none"
                onClick={() => toggleSort("symbol")}
              >
                Symbol <SortIcon col="symbol" />
              </th>
              <th className="text-left py-2.5 px-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
                Company
              </th>
              <th className="text-left py-2.5 px-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
                Cap
              </th>
              <th className="text-left py-2.5 px-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
                Sector
              </th>
              {indCols.map((c) => (
                <th
                  key={c.key}
                  className="text-right py-2.5 px-3 text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-300 select-none whitespace-nowrap"
                  onClick={() => toggleSort(c.key)}
                >
                  {c.label} <SortIcon col={c.key} />
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800/50">
            {sortedStocks.length === 0 && (
              <tr>
                <td colSpan={5 + indCols.length} className="py-10 text-center text-gray-600 text-sm">
                  No stocks matched the criteria
                </td>
              </tr>
            )}
            {sortedStocks.map((stock, i) => {
              const hasDiv  = divMatches.has(stock.symbol);
              const hasMacd = macdMatches.has(stock.symbol);
              const hasBoth = hasDiv && hasMacd;

              // Highlight the row background slightly if it matches any cross-filter
              const rowBg = hasBoth
                ? "bg-yellow-950/20 hover:bg-yellow-950/30"
                : hasDiv || hasMacd
                ? "bg-gray-800/20 hover:bg-gray-800/40"
                : "hover:bg-gray-800/30";

              return (
                <tr key={stock.id} className={`transition-colors ${rowBg}`}>
                  <td className="py-2.5 px-3 text-gray-600 text-xs tabular-nums">
                    {page * pageSize + i + 1}
                  </td>
                  <td className="py-2.5 px-3">
                    <div className="flex items-center gap-1.5">
                      <span className="font-mono font-semibold text-gray-100 text-xs tracking-wide">
                        {stock.symbol}
                      </span>
                      {hasDiv && (
                        <span
                          title="RSI Divergence match"
                          className="inline-flex items-center rounded px-1 py-0.5 text-xs font-medium bg-emerald-900/60 text-emerald-300 border border-emerald-800/50"
                        >
                          DIV
                        </span>
                      )}
                      {hasMacd && (
                        <span
                          title="MACD Crossover match"
                          className="inline-flex items-center rounded px-1 py-0.5 text-xs font-medium bg-blue-900/60 text-blue-300 border border-blue-800/50"
                        >
                          MACD
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="py-2.5 px-3 text-gray-400 text-xs max-w-48 truncate" title={stock.company_name}>
                    {stock.company_name}
                  </td>
                  <td className="py-2.5 px-3">
                    <span
                      className={`inline-flex items-center rounded px-1.5 py-0.5 text-xs ${MCAP_BADGE[stock.market_cap_category] ?? "bg-gray-800 text-gray-400"}`}
                    >
                      {MCAP_LABEL[stock.market_cap_category] ?? stock.market_cap_category}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-gray-500 text-xs max-w-36 truncate" title={stock.sector}>
                    {stock.sector}
                  </td>
                  {indCols.map((c) => {
                    const v = getIndicatorValue(stock, c.indicator, c.field, c.tf);
                    if (c.indicator === "volume_strength" && c.field === "volume_ratio") {
                      const colorClass = volumeRatioColor(v);
                      return (
                        <td key={c.key} className={`py-2.5 px-3 text-right tabular-nums text-xs ${colorClass}`}>
                          {v === null ? (
                            <span className="text-gray-700">—</span>
                          ) : (
                            <span title={`${v.toFixed(1)}%`}>{volumeSignalLabel(v)} {v.toFixed(0)}%</span>
                          )}
                        </td>
                      );
                    }
                    const colorClass = c.field === "value" && c.indicator === "rsi"
                      ? rsiColor(v)
                      : c.field === "percent_b"
                      ? pbColor(v)
                      : "text-gray-300";
                    return (
                      <td key={c.key} className={`py-2.5 px-3 text-right tabular-nums text-xs ${colorClass}`}>
                        {v === null ? <span className="text-gray-700">—</span> : v.toFixed(2)}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between text-xs">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page === 0}
            className="px-3 py-1.5 rounded border border-gray-700 text-gray-400 hover:border-gray-500 disabled:opacity-30 disabled:cursor-not-allowed"
          >
            ← Previous
          </button>
          <span className="text-gray-600">
            Page {page + 1} of {totalPages}
          </span>
          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages - 1}
            className="px-3 py-1.5 rounded border border-gray-700 text-gray-400 hover:border-gray-500 disabled:opacity-30 disabled:cursor-not-allowed"
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}
