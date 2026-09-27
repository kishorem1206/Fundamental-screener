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
  getQuickScores: (params: Record<string, string>) =>
    req<import("./types").CompanyScoresResponse>(`/quick-scores?${new URLSearchParams(params).toString()}`),
};
