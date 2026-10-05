const BASE = "/api";

async function req<T>(path: string, options?: RequestInit): Promise<T> {
  // Standalone export build: every GET the dashboard needs was pre-fetched
  // and embedded by html_export_service.py, keyed by this exact path string.
  // No section component needs to know this — same call, same path, either
  // build. See frontend/src/vite-env.d.ts + main.tsx.
  const bundle = window.__EXPORT_BUNDLE__;
  if (bundle) {
    if (path in bundle) return bundle[path] as T;
    throw new Error(`No embedded data for ${path} in this exported report`);
  }
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: res.statusText }));
    throw new Error(err.message || err.detail || "Request failed");
  }
  return res.json() as Promise<T>;
}

export const api = {
  bieSummary: (symbol: string) =>
    req<import("./components/sections/DeepReportSection").DeepReportSummary>(`/bie/${encodeURIComponent(symbol)}/summary`),
  bieStatus: (symbol: string) =>
    req<import("./components/DeepReportButton").DeepReportStatus>(`/bie/${encodeURIComponent(symbol)}/status`),
  bieBuild: (symbol: string) =>
    req<{ status: string }>(`/bie/${encodeURIComponent(symbol)}/build`, { method: "POST" }),
  bieReports: () =>
    req<{ reports: { symbol: string; company_name: string; basic_industry: string | null; built_at: string }[]; building: string[] }>("/bie/reports"),
  bieAssumptions: (symbol: string, scenario: string) =>
    req<import("./components/AssumptionCenter").ControlCentre>(`/bie/${encodeURIComponent(symbol)}/assumptions?scenario=${scenario}`),
  bieSetOverride: (symbol: string, body: Record<string, unknown>) =>
    req<{ id: string }>(`/bie/${encodeURIComponent(symbol)}/overrides`, { method: "POST", body: JSON.stringify(body) }),
  bieResetOverride: (symbol: string, id: string) =>
    req<{ reset: string }>(`/bie/${encodeURIComponent(symbol)}/overrides/${id}`, { method: "DELETE" }),
  bieOverrideHistory: (symbol: string) =>
    req<{ history: import("./components/AssumptionCenter").HistoryRow[] }>(`/bie/${encodeURIComponent(symbol)}/overrides/history`),
  bieRanking: (symbol: string) =>
    req<{ ranking: import("./components/AssumptionCenter").RankRow[] }>(`/bie/${encodeURIComponent(symbol)}/assumption-ranking`),
  bieWhatIf: (symbol: string, params: Record<string, string>) =>
    req<{ results: (import("./components/AssumptionCenter").Lenses & { value: number })[] }>(`/bie/${encodeURIComponent(symbol)}/what-if?${new URLSearchParams(params).toString()}`),
  getSectors: () => req<{ sectors: string[] }>("/stocks/sectors"),
  getSectorCounts: () =>
    req<import("./types").SectorCountsResponse>("/stocks/sector-counts"),
  getStocks: (sector?: string, limit = 200) => {
    const params = new URLSearchParams();
    if (sector) params.set("sector", sector);
    params.set("limit", String(limit));
    return req<{ stocks: import("./types").Stock[]; count: number }>(`/stocks?${params.toString()}`);
  },
  startAnalysis: (stockId: string) =>
    req<{ analysis_id: string; status: string }>("/fundamental/analyses", {
      method: "POST",
      body: JSON.stringify({ stock_id: stockId }),
    }),
  getAnalysisStatus: (id: string) =>
    req<import("./types").AnalysisStatus>(`/fundamental/analyses/${id}/status`),
  getAnalysis: (id: string) =>
    req<import("./types").FullAnalysis>(`/fundamental/analyses/${id}`),
  getAnalyses: () =>
    req<{ analyses: import("./types").FullAnalysis[] }>("/fundamental/analyses"),
  generateReport: (id: string) =>
    req<{ report_path: string }>(`/fundamental/analyses/${id}/generate-report`, { method: "POST" }),
  getReportUrl: (id: string) => `${BASE}/fundamental/analyses/${id}/report`,
  getHtmlReportUrl: (id: string) => `${BASE}/fundamental/analyses/${id}/report?format=html`,
  getScreeningTaxonomy: () =>
    req<{ combinations: import("./types").TaxonomyCombination[] }>("/screening/taxonomy"),
  screenStocks: (filters: {
    macro_sector?: string;
    sector?: string;
    industry?: string;
    basic_industry?: string;
  }) => {
    const params = new URLSearchParams();
    for (const [k, v] of Object.entries(filters)) {
      if (v) params.set(k, v);
    }
    const qs = params.toString();
    return req<import("./types").ScreeningResult>(`/screening/stocks${qs ? `?${qs}` : ""}`);
  },
  getCompanySummary: (companyId: string) =>
    req<import("./types").CompanySummaryResponse>(`/company-summary/${companyId}`),
  getCompanyNews: (companyId: string) =>
    req<import("./types").CompanyNewsResponse>(`/yfinance/${companyId}/news`),
  getEarningsCalendar: (companyId: string) =>
    req<import("./types").EarningsCalendarResponse>(`/yfinance/${companyId}/calendar`),
  getCorporateActions: (companyId: string) =>
    req<import("./types").CorporateActionsResponse>(`/yfinance/${companyId}/corporate-actions`),
  getForwardEstimates: (companyId: string) =>
    req<import("./types").ForwardEstimatesResponse>(`/yfinance/${companyId}/forward-estimates`),
  getInsiderActivity: (companyId: string) =>
    req<import("./types").InsiderActivityResponse>(`/yfinance/${companyId}/insider-activity`),
  getBusinessSegments: (companyId: string) =>
    req<import("./types").BusinessSegmentsResponse>(`/segments/${companyId}`),
  getAnalystConsensus: (companyId: string) =>
    req<import("./types").AnalystConsensusResponse>(`/analyst-consensus/${companyId}`),
  getMarketMovers: () =>
    req<import("./types").MarketMoversResponse>(`/market-movers`),
  getBrokerReports: (companyId: string) =>
    req<import("./types").BrokerReportsResponse>(`/broker-reports/${companyId}`),
  getBrands: (companyId: string) =>
    req<import("./types").BrandsResponse>(`/brands/${companyId}`),
  getConcallIntelligence: (companyId: string) =>
    req<import("./types").ConcallIntelligenceResponse>(`/concall/${companyId}`),
  getPremiumExtras: (companyId: string) =>
    req<import("./types").PremiumExtrasResponse>(`/premium/${companyId}`),
  getHistoryCharts: (companyId: string) =>
    req<import("./types").HistoryChartsResponse>(`/history-charts/${companyId}`),
  // `statementType` powers the Consolidated/Standalone toggle on each of
  // these three tabs — omit it to let the backend pick whichever actually
  // has data (preferring CONSOLIDATED); pass it to force exactly that one.
  getPlIntelligence: (companyId: string, statementType?: "CONSOLIDATED" | "STANDALONE") =>
    req<import("./types").PlIntelligence>(`/pl-intelligence/${companyId}${statementType ? `?statement_type=${statementType}` : ""}`),
  getBalanceSheetIntelligence: (companyId: string, statementType?: "CONSOLIDATED" | "STANDALONE") =>
    req<import("./types").BalanceSheetIntelligence>(`/balance-sheet-intelligence/${companyId}${statementType ? `?statement_type=${statementType}` : ""}`),
  getCashFlowIntelligence: (companyId: string, statementType?: "CONSOLIDATED" | "STANDALONE") =>
    req<import("./types").CashFlowIntelligence>(`/cash-flow-intelligence/${companyId}${statementType ? `?statement_type=${statementType}` : ""}`),
  getQuarterlyIntelligence: (companyId: string, statementType?: "CONSOLIDATED" | "STANDALONE") =>
    req<import("./types").QuarterlyIntelligence>(`/quarterly-intelligence/${companyId}${statementType ? `?statement_type=${statementType}` : ""}`),
  getBankRoe: (companyId: string) =>
    req<import("./types").BankRoeAnalysis>(`/bank-roe/${companyId}`),
  getCompanyScores: (params: Record<string, string>) =>
    req<import("./types").CompanyScoresResponse>(`/company-scores?${new URLSearchParams(params).toString()}`),
  getFrameworkStock: (symbol: string) =>
    req<import("./components/CombinedScore").FrameworkStockDetail>(`/framework/${encodeURIComponent(symbol)}`),
  getFrameworkScores: (params: Record<string, string>) =>
    req<import("./components/CombinedScore").FrameworkScoresResponse>(`/framework/scores?${new URLSearchParams(params).toString()}`),
  getQuickScores: (params: Record<string, string>) =>
    req<import("./types").CompanyScoresResponse>(`/quick-scores?${new URLSearchParams(params).toString()}`),
};
