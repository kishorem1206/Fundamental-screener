export interface Stock {
  id: string;
  symbol: string;
  exchange: string;
  company_name: string;
  sector: string | null;
  industry: string | null;
  market_cap: number | null;
  market_cap_category: string | null;
  isin: string | null;
}

export interface TaxonomyCombination {
  macro_sector: string;
  sector: string;
  industry: string;
  basic_industry: string;
}

export interface ScreenedStock {
  symbol: string;
  company_name: string;
  market_cap_cr: number | null;
  macro_sector: string;
  sector: string;
  industry: string;
  basic_industry: string;
  stock_id: string | null;
  exchange: string | null;
  analyzable: boolean;
}

export interface ScreeningResult {
  stocks: ScreenedStock[];
  count: number;
  descriptions: Record<string, string | null>;
}

export interface AnalysisStage {
  stage_name: string;
  status: "PENDING" | "RUNNING" | "COMPLETED" | "FAILED" | "SKIPPED";
  progress: number;
  message: string | null;
  error: string | null;
}

export interface AnalysisStatus {
  analysis_id: string;
  company: {
    company_name: string;
    symbol: string;
    exchange: string;
    macro_sector: string | null;
    sector: string | null;
    industry: string | null;
    basic_industry: string | null;
  } | null;
  status: "QUEUED" | "RUNNING" | "COMPLETED" | "FAILED" | "CANCELLED";
  current_stage: string | null;
  overall_progress: number;
  stage_progress: number;
  overall_score: number | null;
  confidence_score: number | null;
  ai_rating: string | null;
  stages: AnalysisStage[];
  error_message: string | null;
  completed_at: string | null;
  report_available: boolean;
}

export interface Metrics {
  years_available: string[];
  data_years: number;
  latest_fy: string | null;
  missing_fields: string[];
  data_is_stale: boolean;
  fetched_at: string | null;
  revenue_cagr_3y: number | null;
  revenue_cagr_5y: number | null;
  revenue_cagr_10y: number | null;
  ebitda_cagr_3y: number | null;
  pat_cagr_3y: number | null;
  pat_cagr_5y: number | null;
  pat_cagr_10y: number | null;
  eps_cagr_3y: number | null;
  eps_cagr_5y: number | null;
  eps_cagr_10y: number | null;
  fcf_cagr_3y: number | null;
  gross_margin: number | null;
  ebitda_margin: number | null;
  ebit_margin: number | null;
  pat_margin: number | null;
  roe: number | null;
  roce: number | null;
  roic: number | null;
  normalized_eps: number | null;
  cfo_latest: number | null;
  fcf_latest: number | null;
  fcf_yield: number | null;
  cfo_to_pat: number | null;
  fcf_to_pat: number | null;
  fcf_margin: number | null;
  debt_to_equity: number | null;
  net_debt: number | null;
  net_debt_to_ebitda: number | null;
  interest_coverage: number | null;
  current_ratio: number | null;
  quick_ratio: number | null;
  cash_conversion_cycle: number | null;
  inventory_days: number | null;
  receivable_days: number | null;
  payable_days: number | null;
  asset_turnover: number | null;
  capex_to_revenue: number | null;
  pe_ratio: number | null;
  forward_pe: number | null;
  pb_ratio: number | null;
  ev_to_ebitda: number | null;
  ev_to_sales: number | null;
  ev_to_fcf: number | null;
  peg_ratio: number | null;
  earnings_yield: number | null;
  dividend_yield: number | null;
  p_fcf: number | null;
  implied_pe_3y_avg: number | null;
  implied_pe_5y_avg: number | null;
  market_cap: number | null;
  enterprise_value: number | null;
  // Cyclicality
  is_cyclical: boolean | null;
  ebitda_margin_cv: number | null;
  ebitda_margin_peak: number | null;
  ebitda_margin_trough: number | null;
  cycle_position: number | null;
  roce_peak: number | null;
  roce_trough: number | null;
  roce_cycle_position: number | null;
  // Working capital cycle trends
  inventory_days_trend: string | null;
  receivable_days_trend: string | null;
  payable_days_trend: string | null;
  ccc_trend: string | null;
  wc_to_revenue_trend: string | null;
  working_capital_latest: number | null;
  wc_to_revenue_latest: number | null;
  // ROIC decomposition
  nopat_margin_latest: number | null;
  capital_turnover_latest: number | null;
  nopat_margin_3y_avg: number | null;
  capital_turnover_3y_avg: number | null;
  // Historical averages (from engine.py _series_avg)
  ebitda_margin_3y_avg: number | null;
  ebitda_margin_5y_avg: number | null;
  pat_margin_3y_avg: number | null;
  pat_margin_5y_avg: number | null;
  roce_3y_avg: number | null;
  roce_5y_avg: number | null;
  roe_3y_avg: number | null;
  roe_5y_avg: number | null;
  roa_3y_avg: number | null;
  roa_5y_avg: number | null;
  debt_to_equity_3y_avg: number | null;
  debt_to_equity_5y_avg: number | null;
  fcf_to_pat_3y_avg: number | null;
  fcf_to_pat_5y_avg: number | null;
  net_debt_to_ebitda_3y_avg: number | null;
  net_debt_to_ebitda_5y_avg: number | null;
  interest_coverage_3y_avg: number | null;
  asset_turnover_3y_avg: number | null;
  inventory_days_3y_avg: number | null;
  receivable_days_3y_avg: number | null;
  gross_margin_3y_avg: number | null;
  gross_margin_5y_avg: number | null;
  // Trends
  roce_trend: string | null;
  roe_trend: string | null;
  ebitda_margin_trend: string | null;
  pat_margin_trend: string | null;
  debt_trend: string | null;
  fcf_trend: string | null;
  // Series: year → value
  revenue_series: Record<string, number | null>;
  ebitda_series: Record<string, number | null>;
  pat_series: Record<string, number | null>;
  eps_series: Record<string, number | null>;
  cfo_series: Record<string, number | null>;
  fcf_series: Record<string, number | null>;
  roce_series: Record<string, number | null>;
  roe_series: Record<string, number | null>;
  ebitda_margin_series: Record<string, number | null>;
  pat_margin_series: Record<string, number | null>;
  d_e_series: Record<string, number | null>;
  net_debt_series: Record<string, number | null>;
  piotroski: PiotroskiScore | null;
}

export interface PiotroskiComponent {
  key: string;
  label: string;
  passed: boolean | null;
  detail: string;
}
export interface PiotroskiScore {
  score: number | null;
  checks_available: number;
  fiscal_year?: string;
  prior_fiscal_year?: string;
  components: PiotroskiComponent[];
}

export interface Scores {
  overall: number | null;
  growth: number | null;
  // Components blended into `growth` above (see backend scoring.py's
  // `_growth_score()`): annual is FY-CAGR-based, quarterly is a recency-
  // weighted trailing-4Q-vs-prior-4Q score. `growth_quarterly` is null
  // when too few quarters are on record, in which case growth == growth_annual.
  growth_annual: number | null;
  growth_quarterly: number | null;
  profitability: number | null;
  cash_flow: number | null;
  balance_sheet: number | null;
  efficiency: number | null;
  valuation: number | null;
  overall_rating: string | null;
  valuation_view: string | null;
  sector_matched: boolean;
  red_flags: string[];
  weights: Record<string, number>;
}

export interface Risk {
  severity: string;
  category: string;
  title?: string;
  description: string;
  mitigation?: string;
  evidence?: Record<string, unknown>;
  confidence?: number;
}

export interface Catalyst {
  type?: string;
  category?: string;
  title?: string;
  description: string;
  impact?: string;
  timeframe?: string;
  severity?: string;
  confidence?: number;
}

export interface AIAnalysis {
  rating: string;
  conviction?: string;
  confidence?: number;
  valuation_view?: string;
  model?: string;
  // Quantitative sub-scores
  business_quality?: number;
  growth_quality?: number;
  financial_quality?: number;
  // Narrative fields
  executive_summary?: string;
  business_quality_assessment?: string;
  financial_health_summary?: string;
  growth_outlook?: string;
  valuation_commentary?: string;
  investment_thesis?: string[];
  bull_case?: string[] | string;
  bear_case?: string[] | string;
  key_risks?: string[];
  key_catalysts?: string[];
  catalysts?: string[];
  monitoring_points?: string[];
  competitive_position?: string;
  industry_attractiveness?: string;
}

export interface SectorMetric {
  name: string;
  label?: string;
  value?: number | string | null;
  unit?: string;
  status?: string;    // EXCELLENT | GOOD | FAIR | POOR | N/A
  score?: number | null;
  weight?: number;
  importance?: string;
  direction?: string;
  description?: string;
  available?: boolean;
  na_message?: string | null;
  applicable_to?: string[];
  sector_median?: number | null;
  sector_percentile?: number | null;
}

export interface SectorRedFlag {
  name: string;
  triggered: boolean;
  severity?: string;
  message?: string;
}

export interface SectorAnalysis {
  sector_name?: string;
  framework?: string;
  framework_class?: string;
  description?: string;
  sector_matched: boolean;
  sector_score?: number | null;
  key_metrics?: SectorMetric[];
  available_metric_names?: string[];
  unavailable_metric_names?: string[];
  red_flags?: SectorRedFlag[];
  sector_metrics?: Record<string, number | null>;
  sector_risks?: Risk[];
  sector_weights?: Record<string, number>;
}

export interface PeerEntry {
  stock_id?: string;
  company_name: string;
  symbol: string;
  exchange?: string;
  market_cap?: number | null;
  market_cap_category?: string | null;
  // Key metrics fetched from yfinance per peer
  revenue_cagr_3y?: number | null;
  ebitda_margin?: number | null;
  pat_margin?: number | null;
  roce?: number | null;
  roe?: number | null;
  roa?: number | null;
  debt_to_equity?: number | null;
  net_debt_to_ebitda?: number | null;
  fcf_to_pat?: number | null;
  pe_ratio?: number | null;
  pb_ratio?: number | null;
  ev_to_ebitda?: number | null;
  peg_ratio?: number | null;
  // Sector-specific key metrics (e.g. hospitals' bed_occupancy_pct/arpob/
  // alos_days/arpp — see app/sectors/*.py's key_metrics()), keyed by the
  // same metric `name` used in SectorAnalysis.key_metrics. Only populated
  // for metric ids this peer already has on file in metric_store — most
  // peers that haven't themselves been analyzed on this platform will show
  // null here, which is a real "not yet available" state, not a bug.
  sector_metrics?: Record<string, number | null>;
}

export interface PeersData {
  sector?: string;
  industry?: string;
  peer_count?: number;
  peers: PeerEntry[];
  company_metrics?: Record<string, number | null>;
  sector_medians?: Record<string, number | null>;
  company_percentiles?: Record<string, number | null>;
  // Which keys in company_metrics/sector_medians/company_percentiles above
  // are the sector-specific (non-yfinance) ones for this analysis's
  // framework — lets the UI split "universal financial ratios" from
  // "sector-specific operating KPIs" without hardcoding a per-sector list.
  sector_metric_ids?: string[];
  note?: string;
}

export interface CompanySummaryResponse {
  company_id: string;
  summary: {
    about: string | null;
    key_points: string | null;
    source: string;
    retrieved_at: string;
  } | null;
}

export interface NewsItem {
  headline: string;
  summary: string | null;
  provider: string | null;
  url: string | null;
  published_at: string | null;
}
export interface CompanyNewsResponse {
  company_id: string;
  source: string;
  news: NewsItem[];
}

export interface EarningsCalendarResponse {
  company_id: string;
  source: string;
  calendar: {
    next_earnings_date: string | null;
    ex_dividend_date: string | null;
    expected_eps_avg: number | null;
    expected_eps_low: number | null;
    expected_eps_high: number | null;
    expected_revenue_avg: number | null;
    expected_revenue_low: number | null;
    expected_revenue_high: number | null;
  } | null;
}

export interface CorporateActionItem {
  date: string;
  type: string;
  value: number;
}
export interface CorporateActionsResponse {
  company_id: string;
  source: string;
  actions: CorporateActionItem[];
}

export interface ForwardEstimateItem {
  period_label: string;
  avg: number | null;
  low: number | null;
  high: number | null;
  num_analysts: number | null;
  growth_pct: number | null;
}
export interface ForwardEstimatesResponse {
  company_id: string;
  source: string;
  estimates: Record<string, ForwardEstimateItem[]>;
}

export interface InsiderActivityItem {
  date: string;
  insider_name: string | null;
  position: string | null;
  text: string | null;
  shares: number | null;
  value: number | null;
  ownership_type: string | null;
}
export interface InsiderActivityResponse {
  company_id: string;
  source: string;
  transactions: InsiderActivityItem[];
}

export interface BusinessSegmentItem {
  segment_name: string;
  fiscal_year: string;
  revenue: number;
  currency: string;
}
export interface BusinessSegmentsResponse {
  company_id: string;
  source: string;
  segments: BusinessSegmentItem[];
}

export interface BlueprintItem {
  title?: string;
  description?: string;
  question?: string;
  answer?: string;
  severity?: string;
}
export interface BlueprintSection {
  id: string;
  type: "text" | "business_model" | "insight_cards" | "risk_cards" | "qa_cards" | string;
  title: string;
  content?: string;
  key_points?: string[];
  items?: BlueprintItem[];
}
export interface ReportBlueprint {
  report: { company: string | null };
  sections: BlueprintSection[];
}

export interface AnalystConsensusEntry {
  num_analysts: number | null;
  sentiment: string | null;
  buy_pct: number | null;
  hold_pct: number | null;
  sell_pct: number | null;
  target_price_mean: number | null;
  target_price_low: number | null;
  target_price_high: number | null;
  price_at_capture: number | null;
  implied_upside_pct: number | null;
  source: string;
  retrieved_at: string;
  disclaimer: string;
}
export interface AnalystConsensusResponse {
  company_id: string;
  by_source: Record<string, AnalystConsensusEntry>;
}

export interface MoverStock {
  ticker_id?: string;
  ticker?: string;
  company_name?: string;
  company?: string;
  price?: string | number;
  percent_change?: string | number;
  net_change?: string | number;
  volume?: string | number;
  overall_rating?: string;
  [key: string]: unknown;
}
export interface MarketMoversResponse {
  trending: { trending_stocks?: { top_gainers?: MoverStock[]; top_losers?: MoverStock[] } } | null;
  nse_most_active: MoverStock[] | null;
  bse_most_active: MoverStock[] | null;
  price_shockers: Record<string, MoverStock[]> | null;
  week_52_high_low: Record<string, { high52Week?: MoverStock[]; low52Week?: MoverStock[] }> | null;
}

export interface SectorMemberStock {
  stock_id: string | null;
  symbol: string;
  company_name: string;
  basic_industry: string | null;
  market_cap_cr: number | null;
  market_cap_category: string | null;
}
export interface SectorCount {
  sector: string;
  count: number;
  stocks: SectorMemberStock[];
}
export interface SectorCountsResponse {
  sector_counts: SectorCount[];
  total: number;
}

export interface BrokerReportItem {
  report_date: string;
  broker_name: string;
  rating: string | null;
  target_price: number | null;
  ltp_at_capture: number | null;
  price_at_reco: number | null;
  change_since_reco_pct: number | null;
  upside_pct: number | null;
  reco_changed: boolean;
  target_changed: boolean;
}
export interface BrokerReportsResponse {
  company_id: string;
  source: string;
  reports: BrokerReportItem[];
}

// ── Premium PDF System, Stage B1 — Brand Portfolio ──────────────────────
export interface BrandItem {
  brand_name: string;
  category: string | null;
  ownership: string | null;
  market_share_pct: number | null;
  market_share_context: string | null;
  license_expiry: string | null;
}
export interface BrandsResponse {
  company_id: string;
  brands: BrandItem[];
}

// ── Concall Intelligence System (Stage C5) + Premium PDF System Stages
// B2/B3/B5, plus Results & Concall Highlights (arthneeti.com primary /
// generated fallback) — this app's first frontend surface for any of it. ──
export interface ConcallGuidanceItem {
  metric: string;
  category: string | null;
  period: string | null;
  guidance_type: string;
  target_low: number | null;
  target_high: number | null;
  target_value: number | null;
  unit: string | null;
  tone: string | null;
  confidence: string | null;
  certainty: string | null;
  conditional: boolean;
  status: string;
  // The verbatim (lightly transcribed) management quote this row was
  // extracted from — real context for a generic/"other" row that has no
  // clean structured target.
  statement?: string | null;
}
export interface ConcallCredibilityItem {
  metric: string;
  guidance_count: number;
  upgraded_count: number;
  downgraded_count: number;
  reiterated_count: number;
  last_status: string;
}
export interface ConcallPromiseItem {
  promise: string;
  category: string | null;
}
export interface ConcallTopicSentimentItem {
  topic: string;
  sentiment: "POSITIVE" | "NEGATIVE" | "NEUTRAL" | "MIXED";
  arrow: string;
}
export interface ConcallGuidanceConsistency {
  score: number;
  metrics_tracked: number;
  total_updates: number;
}
export interface ConcallHighlightSection {
  heading: string;
  bullets: string[];
}
export interface ConcallHighlights {
  source: "ARTHNEETI" | "GENERATED";
  source_url: string | null;
  sections: ConcallHighlightSection[];
}
export interface ConcallLatestTranscript {
  quarter: string | null;
  call_date: string | null;
  filing_date: string | null;
  management_participants: { name: string; title?: string }[];
}
export interface ConcallIntelligenceResponse {
  latest_transcript: ConcallLatestTranscript | null;
  topic_sentiment: ConcallTopicSentimentItem[];
  what_changed: string[];
  has_previous_call: boolean;
  guidance_consistency: ConcallGuidanceConsistency | null;
  guidance: ConcallGuidanceItem[];
  credibility: ConcallCredibilityItem[];
  promises: ConcallPromiseItem[];
  highlights: ConcallHighlights | null;
}

// ── Premium PDF System, Stages B4/B6/B7 ─────────────────────────────────
export interface PeerPerformancePoint {
  date: string;
  value: number;
}
export interface PeerPerformanceSeries {
  name: string;
  symbol: string;
  is_subject: boolean;
  points: PeerPerformancePoint[];
}
export interface PeerPerformanceData {
  period: string;
  series: PeerPerformanceSeries[];
}
export interface SourceLedgerEntry {
  source: string;
  type: string;
  used_for: string;
  tier: number;
  date_from: string | null;
  date_to: string | null;
  fact_count: number;
}
export interface ChangeLogData {
  previous_analysis_id: string;
  previous_completed_at: string | null;
  changes: string[];
  new_risks: string[];
  resolved_risks: string[];
  has_material_change: boolean;
}
export interface PricePoint {
  date: string;
  close: number;
}
export interface PriceChartData {
  "1y": PricePoint[];
  "5y": PricePoint[];
}
export interface SalesMarginPoint {
  period: string;
  sales: number | null;
  opm: number | null;
  npm: number | null;
  net_profit: number | null;
}
export interface ValuationHistoryPoint {
  period: string;
  eps: number | null;
  pe: number | null;
  pb: number | null;
}
export interface RoceHistoryPoint {
  period: string;
  roce: number | null;
}
export interface HistoryChartsResponse {
  company_id: string;
  sales_and_margins: SalesMarginPoint[];
  valuation: ValuationHistoryPoint[];
  roce_history: RoceHistoryPoint[];
}

export interface PremiumExtrasResponse {
  company_id: string;
  peer_performance: PeerPerformanceData;
  source_ledger: SourceLedgerEntry[];
  change_log: ChangeLogData | null;
  price_chart: PriceChartData;
}

export interface FullAnalysis {
  id: string;
  stock_id: string;
  status: string;
  overall_score: number | null;
  confidence_score: number | null;
  data_quality_score: number | null;
  ai_rating: string | null;
  valuation_rating: string | null;
  company_info: {
    stock_id?: string;
    symbol: string;
    exchange: string;
    company_name: string;
    sector: string | null;
    industry: string | null;
    basic_industry?: string | null;
    market_cap: number | null;
    market_cap_category: string | null;
    current_price?: {
      price: number;
      previous_close: number | null;
      change_pct: number | null;
      day_high: number | null;
      day_low: number | null;
      currency: string;
      as_of: string;
      source: string;
    } | null;
    week52_high?: number | null;
    week52_low?: number | null;
  } | null;
  metrics: Metrics | null;
  scores: Scores | null;
  sector_analysis: SectorAnalysis | null;
  peers: PeersData | null;
  risks: Risk[];
  catalysts: Catalyst[];
  ai_analysis: AIAnalysis | null;
  metric_validations: Record<string, { status: string; value: number | null }> | null;
  report_blueprint: ReportBlueprint | null;
  report_available: boolean;
  completed_at: string | null;
}

// P&L Analysis Engine ("P&L Intelligence") — matches
// backend/app/calculations/pl_intelligence/__init__.py::compute_pl_intelligence()'s
// output, served by GET /api/pl-intelligence/{company_id}. A separate live
// fetch (like history-charts/premium), not part of FullAnalysis.
export interface PlCascadePeriod {
  revenue: number | null;
  cogs: null;
  gross_profit: null;
  gross_margin: null;
  gross_margin_confidence: "LOW";
  opex: number | null;
  ebitda: number | null;
  ebitda_margin: number | null;
  depreciation: number | null;
  ebit: number | null;
  ebit_margin: number | null;
  finance_cost: number | null;
  other_income: number | null;
  exceptional_items: null;
  pbt: number | null;
  tax: number | null;
  pat: number | null;
  pat_margin: number | null;
}

export interface PlPeerMetricStats {
  company_value: number | null;
  peer_median: number | null;
  peer_mean: number | null;
  peer_min: number | null;
  peer_max: number | null;
  percentile: number | null;
}

export interface PlDoublingResult {
  doubling_years: number | null;
  start_year?: number;
  end_year?: number;
  method: "EMPIRICAL" | "CAGR_THEORETICAL" | null;
  speed: string | null;
}

export interface PlIntelligence {
  period: string | null;
  statement_type: string;
  // True only when this company has NO data under the other statement
  // type at all (confirmed live on Netweb/Bandhan Bank — not an ingestion
  // gap, Screener.in genuinely has nothing there) — the toggle should be
  // hidden in that case, not offer a choice that doesn't really exist.
  single_statement_source: boolean;
  cascade: Record<string, PlCascadePeriod>;
  margins: {
    ebitda_margin: number | null;
    ebit_margin: number | null;
    pat_margin: number | null;
    margin_direction: string | null;
    ebitda_margin_direction: string | null;
    stability: {
      current: number | null; avg_5y: number | null; avg_10y: number | null;
      stdev: number | null; max: number | null; min: number | null; classification: string;
    };
  };
  peer_percentiles: {
    peer_count: number;
    period: string | null;
    statement_type: string;
    // Where each margin's peer set came from: the P&L ledger, or the Yahoo
    // figures behind the Peers tab when no peer has ledger data yet.
    peer_source?: Record<string, "LEDGER" | "YAHOO_PEER_TAB">;
    ebitda_margin: PlPeerMetricStats;
    pat_margin: PlPeerMetricStats;
  };
  // Fintech companies only (sector === "Fintech") — null for everyone else.
  // Same shape/degrade-gracefully contract as peer_percentiles above, but
  // sourced from earnings-call-transcript extraction (metric_store ledger),
  // not the pnl_* cascade, so peer coverage depends on whether each peer
  // has itself been analyzed with fintech extraction turned on.
  fintech_peer_percentiles: {
    peer_count: number;
    gtv_growth: PlPeerMetricStats;
    take_rate: PlPeerMetricStats;
  } | null;
  margin_headroom: {
    headroom: number | null;
    headroom_pct: number | null;
    classification: string | null;
    interpretation: string | null;
  };
  doubling: {
    revenue: PlDoublingResult;
    pat: PlDoublingResult;
    velocity_comparison: "PAT_FASTER" | "PAT_SLOWER" | "ROUGHLY_SAME" | "INSUFFICIENT_DATA";
  };
  earnings_quality: {
    eqi: number | null;
    confidence: string;
    core_operating_income: number | null;
    total_income: number | null;
    classification: string | null;
  };
  non_core_income: {
    decomposition: "not_available";
    reason: string;
    aggregate_ratios: { other_income_to_pat_pct: number | null; other_income_to_ebitda_pct: number | null };
  };
  structure: {
    csr: number | null;
    csr_band: string | null;
    standalone_revenue: number | null;
    consolidated_revenue: number | null;
    consolidated_ever_reported: boolean;
    pat_structural_ratio: number | null;
    standalone_pat: number | null;
    consolidated_pat: number | null;
    subsidiary_revenue: number | null;
    subsidiary_revenue_share: number | null;
    segment_names: string[];
    segment_count: number;
    is_conglomerate: boolean;
    sotp_required: boolean;
  };
  diagnostics: {
    operating_leverage: {
      ebitda_vs_revenue: string; operating_leverage: string;
      pat_vs_ebitda: string; below_ebitda_effect: string;
    };
    margin_cascade_break: { type: string; severity: string; ebitda_margin: number; pat_margin: number; likely_drivers: string[] } | null;
  };
  diagnostic_flags: string[];
  score: {
    master_pl_score: number | null;
    classification: string | null;
    components: { M1: number | null; M2: number | null; M3: number | null; M4: number | null; M5: number | null };
    weights: { M1: number; M2: number; M3: number; M4: number; M5: number };
    algorithm_version: string;
  };
}

// Quarterly Report Extraction Engine, Tier 1 — separate fetch
// (`/api/quarterly-intelligence/{companyId}`), same compute-on-read pattern
// as PlIntelligence above. Mirrors
// `app/calculations/quarterly_intelligence/__init__.py::compute_quarterly_intelligence()`'s
// output shape exactly.
export interface QuarterlyFlag {
  flag: string;
  period: string;
  detail: string;
}

export interface QuarterlyIntelligence {
  period: string | null;
  statement_type: string;
  single_statement_source: boolean;
  quarters_available: number;
  series: Record<string, Record<string, number>>;
  qoq: {
    sales: Record<string, number>;
    net_profit: Record<string, number>;
    operating_profit: Record<string, number>;
    opm_delta_pp: Record<string, number>;
  };
  yoy: {
    sales: Record<string, number>;
    net_profit: Record<string, number>;
    operating_profit: Record<string, number>;
  };
  margin_trend: {
    opm_direction: "EXPANSION" | "STABLE" | "COMPRESSION" | "VOLATILE" | "INSUFFICIENT_DATA" | undefined;
    net_margin_direction: "EXPANSION" | "STABLE" | "COMPRESSION" | "VOLATILE" | "INSUFFICIENT_DATA" | undefined;
  };
  flags: QuarterlyFlag[];
  latest_quarter: Record<string, number | null>;
  sector_kpis: QuarterlySectorKpis;
}

// Quarterly Sector KPI Extraction Engine (2026-09-20) — sourced from NSE
// quarterly Investor Presentation filings, not annual reports. Only
// `available: true` for the 5 sectors with a configured quarterly area
// (Automobile, Cement, Metals/Mining, Forest Materials, Chemicals/
// Specialty Chemicals) AND when this company's presentation actually
// resolved to real extractable data — `available: false` is the normal,
// expected case for every other sector, not an error state.
export interface QuarterlySectorKpiMetric {
  metric_key: string;
  label: string;
  unit: string;
  series: Record<string, number>;
  latest_value: number;
  /** Provenance of the latest value (added 2026-09-20) — where it came from. */
  latest_period?: string;
  source?: string | null;
  source_label?: string | null;
  confidence?: "HIGH" | "MEDIUM" | "LOW" | null;
  data_type?: "REPORTED" | "CALCULATED" | null;
  source_document?: string | null;
  source_url?: string | null;
}

export interface QuarterlySectorKpis {
  available: boolean;
  sector_name?: string | null;
  statement_type?: string;
  single_statement_source?: boolean;
  latest_quarter?: string | null;
  metrics?: QuarterlySectorKpiMetric[];
}

// Balance Sheet Analysis Engine — separate fetch (`/api/balance-sheet-intelligence/{companyId}`),
// same pattern as PlIntelligence above. Mirrors
// `app/calculations/balance_sheet_intelligence/__init__.py`'s output shape
// exactly (field-for-field, including which sub-objects are just `{}` when
// a company/period has no data, e.g. `working_capital` for a bank).
export interface BsRiskFlag {
  flag_id: string;
  severity: "RED" | "AMBER";
  status: "TRIGGERED" | "NOT_TRIGGERED" | "SOURCE_REQUIRED";
  metric: string;
  threshold: unknown;
  actual: unknown;
  comparison: unknown;
  period: string | null;
  evidence: string[];
  source: string[];
  confidence: "HIGH" | "MEDIUM" | "LOW" | "UNAVAILABLE";
}

export interface BsCoverageMetric {
  status: "AVAILABLE" | "CALCULABLE" | "PARTIAL" | "MISSING_INPUT" | "SOURCE_REQUIRED" | "NOT_APPLICABLE" | "INVALID";
  reason: string | null;
  dependencies: string[];
}

export interface BalanceSheetIntelligence {
  period: string | null;
  statement_type: string;
  single_statement_source: boolean;
  balance_sheet_integrity: {
    status: "VALID" | "BALANCE_SHEET_INTEGRITY_ERROR" | "MISSING_DATA";
    total_assets?: number | null;
    total_liabilities_equity?: number | null;
    difference?: number | null;
    difference_pct?: number | null;
  };
  assets: Record<string, number | null>;
  liabilities: Record<string, number | null>;
  equity: { equity_capital: number | null; reserves: number | null; total_equity: number | null };
  derived_metrics: {
    total_equity?: number | null;
    external_liabilities?: number | null;
    debt_to_equity: number | null;
    liabilities_to_equity: number | null;
    debt_to_assets?: number | null;
    debt_to_capital?: number | null;
    net_debt: number | null;
    net_debt_source?: string;
    net_debt_to_ebitda: number | null;
    net_cash_position?: boolean;
    capital_employed?: number | null;
    capital_employed_methodology?: string;
    capital_employed_source?: string;
    roce: number | null;
    ebit_margin?: number | null;
    capital_employed_turnover?: number | null;
  };
  house: {
    sources: { label: string; value: number; note?: string }[];
    applications: { label: string; value: number; source?: string }[];
    sources_total: number;
    applications_total: number;
    cash_source: string;
  };
  common_size: Record<string, number>;
  working_capital: {
    methodology?: string;
    latest_period?: string | null;
    dso_series?: Record<string, number | null>;
    dio_series?: Record<string, number | null>;
    dpo_series?: Record<string, number | null>;
    ccc_series?: Record<string, number | null>;
    current_ratio_series?: Record<string, number | null>;
    quick_ratio_series?: Record<string, number | null>;
    cash_ratio_series?: Record<string, number | null>;
    latest_cross_check?: Record<string, { yfinance: number | null; screener_latest: number | null; divergence_pct: number | null }>;
    single_period_fallback?: Record<string, boolean>;
    ccc_latest?: number | null;
    current_ratio_latest?: number | null;
    quick_ratio_latest?: number | null;
    cash_ratio_latest?: number | null;
    amounts?: { gross_working_capital: number | null; net_working_capital: number | null; working_capital_pct_revenue: number | null };
  };
  archetype: {
    classification: "STRONG" | "WEAK" | "MIDDLE" | "TRANSFORMING" | "NOT_APPLICABLE";
    evidence: string[];
    ruleset_version?: string;
    confidence: string;
  };
  risk_flags: BsRiskFlag[];
  historical_trends: Record<string, Record<string, {
    absolute_change: number | null; pct_change: number | null; cagr: number | null;
    average: number | null; median: number | null; peak: number | null; trough: number | null;
    periods_available: number;
  }>>;
  coverage: {
    metrics: Record<string, BsCoverageMetric>;
    summary: Record<string, number>;
    coverage_pct: number;
    total_metrics: number;
  };
  financial_institution_summary: {
    deposits: number | null; borrowings: number | null; investments: number | null;
    total_assets: number | null; note: string;
  } | null;
}

// Cash Flow Analysis Engine — separate fetch (`/api/cash-flow-intelligence/{companyId}`),
// same pattern as BalanceSheetIntelligence above. Mirrors
// `app/calculations/cash_flow_intelligence/__init__.py`'s output shape
// exactly. Primary-sourced from Screener.in's undocumented "schedules" API.
export interface CfRiskFlag {
  flag_id: string;
  severity: "RED" | "AMBER" | "WATCH";
  status: "TRIGGERED" | "NOT_TRIGGERED";
  metric: string;
  actual: unknown;
  threshold: unknown;
  period: string | null;
  persistence: number;
  evidence: string[];
  source: string[];
  confidence: "HIGH" | "MEDIUM" | "LOW" | "UNAVAILABLE";
}

export interface CfForensicPattern {
  pattern_id: string;
  status: "TRIGGERED" | "NOT_TRIGGERED" | "OBSERVED" | "NOT_OBSERVED";
  evidence: string[];
}

export interface CfCoverageMetric {
  status: "AVAILABLE" | "CALCULABLE" | "PARTIAL" | "MISSING_INPUT" | "SOURCE_REQUIRED" | "NOT_APPLICABLE" | "INVALID";
  reason: string | null;
  dependencies: string[];
}

export interface CashFlowIntelligence {
  period: string | null;
  statement_type: string;
  single_statement_source: boolean;
  reconciliation: {
    cfo_bridge: {
      operating_profit: number | null; receivables_change: number | null; inventory_change: number | null;
      payables_change: number | null; loans_advances_change: number | null; other_wc_change: number | null;
      working_capital_change: number | null; taxes_paid: number | null; exceptional_items: number | null;
      computed_cfo: number | null;
    };
    cfo_bridge_check: { status: "VALID" | "DIVERGENT" | "MISSING_DATA"; difference: number | null; difference_pct: number | null };
    cash_bridge: {
      opening_cash: number | null; cfo: number | null; cfi: number | null; cff: number | null;
      other_adjustment: number | null; closing_cash: number | null;
      status: "VALID" | "CASH_FLOW_RECONCILIATION_ERROR" | "MISSING_DATA"; difference_pct: number | null;
    };
  };
  working_capital_impact: {
    receivables?: number | null; inventory?: number | null; payables?: number | null;
    other_wc?: number | null; net_wc_impact?: number | null;
    receivables_cash_drag?: { status: string; triggered: boolean; flag_id: string | null };
    inventory_cash_drag?: { status: string; triggered: boolean; flag_id: string | null };
    payables_cash_support?: { status: string; interpretation: string | null };
  };
  investing: {
    breakdown: Record<string, number | null>;
    asset_sale_dependency: { status: string; triggered: boolean; flag_id: string | null };
    unallocated_capital_drag: { status: string; triggered: boolean; flag_id: string | null; ratio_pct?: number };
  };
  financing: {
    breakdown: Record<string, number | null>;
    debt_financing: { status: string; classification: "NET_BORROWING" | "NET_DELEVERAGING" | "NEUTRAL" | null; net_debt_cash_flow?: number | null };
    dividend_analysis: { status: string; dividends_paid?: number | null; dividend_to_cfo_pct?: number | null; dividend_to_fcf_pct?: number | null };
    buyback_analysis: { status: string; buyback_proxy_value?: number | null; confidence?: string };
  };
  free_cash_flow: {
    reconciliation: { reported_fcf: number | null; computed_fcf: number | null; divergence_pct: number | null; divergent: boolean };
    quality: { classification: string; periods_available: number; positive_periods?: number; negative_periods?: number };
    yfinance_cross_check: { screener: number | null; yfinance: number | null; divergence_pct: number | null };
  };
  conversion: {
    latest: { status: string; ratio_pct: number | null; band: string | null };
    prior_ratio_pct: number | null;
    trend: string;
    cumulative_3y: { status: string; cumulative_cfo_to_operating_profit_pct?: number | null; cumulative_cfo_to_pat_pct?: number | null };
  };
  volatility: {
    classification: "STABLE_CFO" | "DECLINING_CFO" | "VOLATILE_CFO" | "NEGATIVE_CFO_PATTERN" | "INSUFFICIENT_DATA";
    periods_available: number;
    coefficient_of_variation?: number | null;
  };
  forensic_patterns: CfForensicPattern[];
  archetype: {
    classification: "CASH_COMPOUNDER" | "CASH_HARVEST" | "GROWTH_REINVESTMENT" | "ASSET_LIQUIDATION_SUPPORTED"
      | "WORKING_CAPITAL_TRAP" | "DEBT_FUNDED_BUSINESS" | "MIXED";
    evidence: string[];
    ruleset_version?: string;
    confidence: string;
  };
  risk_flags: CfRiskFlag[];
  historical_trends: Record<string, Record<string, {
    absolute_change: number | null; pct_change: number | null; cagr: number | null;
    average: number | null; median: number | null; peak: number | null; trough: number | null;
    periods_available: number;
  }>>;
  coverage: {
    metrics: Record<string, CfCoverageMetric>;
    summary: Record<string, number>;
    coverage_pct: number;
    total_metrics: number;
  };
}

// ── Bank ROE → P/B simulator (mentor's IDFC FIRST ROE simulator, ported) ──
export interface BankRoeSimParams { roe: number; yrs: number; g: number; pay: number; pb: number; disc: number }
export interface BankRoeYearRow {
  year: number; roe: number; pb: number; pat: number; raise: number; shares: number;
  bvps: number; eps: number; price: number; multiple: number; total_return_multiple: number; cagr: number;
}
export interface BankRoeSimulation {
  params: BankRoeSimParams; rows: BankRoeYearRow[]; raised: number; dilution: number; end_shares: number;
  verdict: string; self_funded_growth: number; growth_gap: number; crossover_roe: number | null;
  attribution: { book_value_compounding: number; multiple_rerating: number; total: number };
  key?: string; name?: string;
}
export interface BankRoeChecklistItem {
  key: string; title: string; why: string; value: number | null; unit: string | null;
  series?: { period: string; annualised_roe: number }[] | null;
}
export interface BankRoeAnalysis {
  available: boolean; reason?: string; sector_name?: string;
  start?: {
    price: number; bvps: number; shares_cr: number; equity_cr: number; pb: number; run_rate_roe: number;
    run_rate_source: string; ttm_pat_cr: number | null; ttm_pe: number | null; payout_pct: number;
    market_cap_cr: number; balance_sheet_growth_pct: number | null; eps_ttm: number | null;
  };
  sustainability?: { self_funded_growth: number; balance_sheet_growth: number | null; gap: number | null; crossover_roe: number | null };
  dupont?: { fy: string; roe: number; roa: number; leverage: number; equity_growth: number | null }[];
  valuation_check?: { coe: number; long_run_growth: number; justified_pb_at_run_rate: number | null; market_implied_roe: number | null; pb_anchor_for_run_rate_roe: number };
  share_history?: { fy: string; shares_cr: number; yoy_pct: number | null }[];
  pb_anchors?: { roe: number; pb: number }[];
  presets?: BankRoeSimulation[];
  default_preset?: string;
  checklist?: BankRoeChecklistItem[];
  insights?: string[];
  disclaimer?: string;
}

export type ScoreKey = "overall" | "growth" | "profitability" | "cash_flow" | "balance_sheet" | "efficiency" | "valuation";
// Quick Screener only (fa_quick_scores columns) — the two components
// blended into `growth` (backend scoring.py's `_growth_score()`). Always
// present in the API response (null on a full-pipeline row, which has no
// equivalent columns yet — see company_scores.py's `_row_dict()`).
export type QuickGrowthKey = "growth_annual" | "growth_quarterly";
export interface CompanyScoreRow extends Record<ScoreKey, number | null>, Record<QuickGrowthKey, number | null> {
  stock_id: string;
  symbol: string;
  company_name: string;
  sector: string | null;
  macro_sector: string | null;
  market_cap: number | null;
  overall_rating: string | null;
  valuation_view: string | null;
  red_flags: string[];
  analysis_id: string | null;
  sector_framework?: string | null;
  latest_fy?: string | null;
  // Set only for a mainboard (EQ/BE) NSE listing promoted from the IPO
  // tracker (backend app/ingestion/nse_ipo_client.py) — null for every
  // stock added before that feature, or never an IPO issue at all.
  ipo_listing_date: string | null;
  scored_at: string | null;
  latest_quarter_end: string | null;
}
export interface CompanyScoresResponse {
  total: number;
  limit: number;
  offset: number;
  results: CompanyScoreRow[];
}
