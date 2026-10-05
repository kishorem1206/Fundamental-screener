export type MarketCapCategory = "LARGE_CAP" | "MID_CAP" | "SMALL_CAP" | "MICRO_CAP";
export type Timeframe = "1H" | "4H" | "1D" | "1W" | "1M" | "15M" | "5M";
export type Op = "lt" | "lte" | "gt" | "gte" | "eq" | "neq";
export type IndicatorName = "rsi" | "bollinger" | "volume_strength" | "macd";

export interface FilterRow {
  id: string;
  indicator: IndicatorName;
  field: string;
  timeframe: Timeframe;
  op: Op;
  value: number;
}

export interface Universe {
  id: string;
  name: string;
  description: string;
  stockCount: number;
}

export interface StockMatch {
  id: string;
  symbol: string;
  exchange: string;
  company_name: string;
  sector: string;
  macro_sector: string;
  market_cap_category: MarketCapCategory;
  indicators: Record<string, Record<string, number | null>>;
}

export interface ScreenResult {
  executed_at: string;
  universe: string;
  total_matched: number;
  stocks_screened: number;
  execution_time_ms: number;
  stocks: StockMatch[];
}

export interface ChatSession {
  id: string;
  title: string | null;
  llm_provider: string | null;
  llm_model: string | null;
  message_count: number;
  last_active_at: string;
  created_at: string;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  llm_intent_type: string | null;
  created_at: string;
}

// ─── RSI Divergence ───────────────────────────────────────────────────────────

export type DivergenceType   = "REGULAR_BULLISH" | "REGULAR_BEARISH" | "HIDDEN_BULLISH" | "HIDDEN_BEARISH";
export type DivergenceStatus = "DEVELOPING" | "CONFIRMED" | "RECENT_CONFIRMED";

export interface DivergenceHit {
  id:                   string;
  symbol:               string;
  exchange:             string;
  company_name:         string;
  sector:               string;
  macro_sector:         string;
  market_cap_category:  MarketCapCategory;
  div_type:             DivergenceType;
  status:               DivergenceStatus;
  pivot1_date:          string;
  pivot2_date:          string;
  pivot1_price:         number;
  pivot2_price:         number;
  pivot1_rsi:           number;
  pivot2_rsi:           number;
  price_chg_pct:        number;
  rsi_change:           number;
  bars_between:         number;
  divergence_age:       number;
  strength_score:       number;
  rsi_today:            number | null;
  rsi_prev:             number | null;
}

export interface DivergenceScanResult {
  executed_at:       string;
  universe:          string;
  total_matched:     number;
  stocks_screened:   number;
  execution_time_ms: number;
  divergences:       DivergenceHit[];
}

// ─── MACD ─────────────────────────────────────────────────────────────────────

export type MACDHistState  = "STRONG_BULLISH" | "BULLISH_FADING" | "STRONG_BEARISH" | "BEARISH_FADING" | "NEUTRAL";
export type MACDCrossover  = "BULLISH" | "BEARISH" | "NONE";
export type MACDCrossLoc   = "ABOVE_ZERO" | "BELOW_ZERO" | "NONE";
export type MACDZeroStatus = "ABOVE" | "BELOW" | "AT";
export type MACDCrossType  = "BULLISH_BELOW_ZERO" | "BULLISH_ABOVE_ZERO" | "BEARISH_ABOVE_ZERO" | "BEARISH_BELOW_ZERO";

export interface MACDResult {
  id:                      string;
  symbol:                  string;
  exchange:                string;
  company_name:            string;
  sector:                  string;
  macro_sector:            string;
  market_cap_category:     MarketCapCategory;
  close_price:             number;
  macd:                    number;
  signal_line:             number;
  histogram:               number;
  histogram_prev:          number;
  histogram_direction:     "INCREASING" | "DECREASING" | "FLAT";
  histogram_state:         MACDHistState;
  zero_line_status:        MACDZeroStatus;
  crossover:               MACDCrossover;
  crossover_location:      MACDCrossLoc;
  last_crossover_type:     MACDCrossType | null;
  last_crossover_bars_ago: number | null;
  macd_state:              string;
}

export interface MACDScanResult {
  executed_at:       string;
  universe:          string;
  total_matched:     number;
  stocks_screened:   number;
  execution_time_ms: number;
  results:           MACDResult[];
}

export interface MACDChartBar {
  date:            string;
  close:           number;
  macd:            number;
  signal:          number;
  histogram:       number;
  histogram_state: MACDHistState;
}

export interface MACDChartData {
  symbol:    string;
  exchange:  string;
  timeframe: string;
  bars:      MACDChartBar[];
}

// ─── RSI Momentum ─────────────────────────────────────────────────────────────

export type RSIMomentumSignal =
  | "FRESH_BREAKOUT"
  | "APPROACHING_AGAIN"
  | "APPROACHING"
  | "ALREADY_STRONG"
  | "EXTENDED"
  | "NEUTRAL";

export interface RSIMomentumStock {
  id: string;
  symbol: string;
  exchange: string;
  company_name: string;
  sector: string;
  macro_sector: string;
  market_cap_category: MarketCapCategory;
  rsi_today: number;
  rsi_prev: number;
  rsi_change: number;
  distance_to_60: number;
  rsi_trend: "RISING" | "FLAT" | "FALLING";
  above_60_in_20d: boolean;
  days_since_above_60: number | null;
  signal: RSIMomentumSignal;
  signal_rank: number;
}

export interface RSIMomentumResult {
  executed_at: string;
  universe: string;
  total_matched: number;
  stocks_screened: number;
  execution_time_ms: number;
  stocks: RSIMomentumStock[];
}
