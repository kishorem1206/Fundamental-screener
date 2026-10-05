import type { FilterRow, ScreenResult, Universe, ChatSession, ChatMessage, RSIMomentumResult, DivergenceScanResult, DivergenceType } from "./types";

// Served by the merged backend under /api/technical (was the old app's root).
const BASE = "/api/technical";

export async function fetchUniverses(): Promise<Universe[]> {
  const r = await fetch(`${BASE}/universes`);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  const body = (await r.json()) as { universes: Array<{ id: string; name: string; description: string; stock_count: number }> };
  return body.universes.map((u) => ({
    id: u.id,
    name: u.name,
    description: u.description,
    stockCount: u.stock_count,
  }));
}

export async function runScreen(
  universe: string,
  filters: FilterRow[],
  limit: number,
  offset: number,
): Promise<ScreenResult> {
  const andClauses = filters.map((f) => ({
    type: "indicator",
    indicator: f.indicator,
    field: f.field,
    timeframe: f.timeframe,
    op: f.op,
    value: f.value,
  }));

  const body = {
    universe,
    filters: andClauses.length > 0 ? { and: andClauses } : null,
    rank_by:
      filters.length > 0
        ? { indicator: filters[0].indicator, field: filters[0].field, timeframe: filters[0].timeframe, order: "asc" }
        : null,
    limit,
    offset,
  };

  const r = await fetch(`${BASE}/screens/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    const detail = await r.json().catch(() => ({}));
    throw new Error((detail as { detail?: string }).detail ?? `HTTP ${r.status}`);
  }
  return r.json() as Promise<ScreenResult>;
}

// ─── Chat API ─────────────────────────────────────────────────────────────────

export async function createChatSession(title?: string): Promise<ChatSession> {
  const r = await fetch(`${BASE}/chat/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title: title ?? null }),
  });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json() as Promise<ChatSession>;
}

export async function listChatSessions(): Promise<ChatSession[]> {
  const r = await fetch(`${BASE}/chat/sessions`);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  const body = (await r.json()) as { sessions: ChatSession[] };
  return body.sessions;
}

export async function getChatMessages(sessionId: string): Promise<ChatMessage[]> {
  const r = await fetch(`${BASE}/chat/sessions/${sessionId}/messages`);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  const body = (await r.json()) as { messages: ChatMessage[] };
  return body.messages;
}

export async function sendChatMessage(
  sessionId: string,
  message: string,
): Promise<ChatMessage> {
  const r = await fetch(`${BASE}/chat/sessions/${sessionId}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  if (!r.ok) {
    const detail = await r.json().catch(() => ({}));
    throw new Error((detail as { detail?: string }).detail ?? `HTTP ${r.status}`);
  }
  return r.json() as Promise<ChatMessage>;
}

export async function deleteChatSession(sessionId: string): Promise<void> {
  await fetch(`${BASE}/chat/sessions/${sessionId}`, { method: "DELETE" });
}

// ─── RSI Momentum API ─────────────────────────────────────────────────────────

// ─── Combined RSI Momentum + Indicator Screen ────────────────────────────────

export async function runScreenWithRSIMomentum(params: {
  universe: string;
  signalRanks: number[];
  bbCond?: { op: string; value: number; tf: string };
  macdCond?: { field: string; op: string; value: number; tf: string };
  volCond?: { ratio: number; tf: string };
  displayTfs?: { bb: string; macd: string; vol: string };
  limit?: number;
}): Promise<ScreenResult> {
  const and: object[] = [];

  // RSI Momentum signal_rank filter (OR of selected signals)
  if (params.signalRanks.length > 0) {
    const orItems = params.signalRanks.map(rank => ({
      type: "indicator", indicator: "rsi_momentum",
      field: "signal_rank", timeframe: "1D", op: "eq", value: rank,
    }));
    and.push(orItems.length === 1 ? orItems[0] : { or: orItems });
  }

  if (params.bbCond) {
    and.push({
      type: "indicator", indicator: "bollinger", field: "percent_b",
      timeframe: params.bbCond.tf, op: params.bbCond.op, value: params.bbCond.value,
    });
  }
  if (params.macdCond) {
    and.push({
      type: "indicator", indicator: "macd", field: params.macdCond.field,
      timeframe: params.macdCond.tf, op: params.macdCond.op, value: params.macdCond.value,
    });
  }
  if (params.volCond) {
    and.push({
      type: "indicator", indicator: "volume_strength", field: "volume_ratio",
      timeframe: params.volCond.tf, op: "gt", value: params.volCond.ratio,
    });
  }

  // Always fetch BB, MACD, and Volume for display even when not filtering by them
  const tfs = params.displayTfs ?? { bb: "1D", macd: "1D", vol: "1D" };
  const extraIndicators = [
    { indicator: "bollinger",       timeframe: tfs.bb   },
    { indicator: "macd",            timeframe: tfs.macd },
    { indicator: "volume_strength", timeframe: tfs.vol  },
  ];

  const body = {
    universe: params.universe,
    filters: and.length > 0 ? { and } : null,
    extra_indicators: extraIndicators,
    rank_by: { indicator: "rsi_momentum", field: "signal_rank", timeframe: "1D", order: "desc" },
    limit: params.limit ?? 100,
    offset: 0,
  };

  const r = await fetch(`${BASE}/screens/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    const detail = await r.json().catch(() => ({}));
    throw new Error((detail as { detail?: string }).detail ?? `HTTP ${r.status}`);
  }
  return r.json() as Promise<ScreenResult>;
}

// ─── RSI Divergence API ───────────────────────────────────────────────────────

export async function scanRSIDivergence(params: {
  universe:            string;
  timeframe?:          string;
  pivot_left?:         number;
  pivot_right?:        number;
  max_recency_bars?:   number;
  min_bars_between?:   number;
  max_bars_between?:   number;
  min_rsi_change?:     number;
  min_price_chg_pct?:  number;
  max_pivot_rsi?:      number;
  min_pivot_rsi?:      number;
  require_rsi_rising?: boolean;
  div_types?:          DivergenceType[];
  limit?:              number;
  offset?:             number;
}): Promise<DivergenceScanResult> {
  const r = await fetch(`${BASE}/rsi-divergence/scan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!r.ok) {
    const detail = await r.json().catch(() => ({}));
    throw new Error((detail as { detail?: string }).detail ?? `HTTP ${r.status}`);
  }
  return r.json() as Promise<DivergenceScanResult>;
}

// ─── MACD API ────────────────────────────────────────────────────────────────

import type { MACDScanResult, MACDChartData } from "./types";

export async function scanMACD(params: {
  universe:           string;
  source?:            string;
  fast?:              number;
  slow?:              number;
  signal_period?:     number;
  osc_ma_type?:       string;
  sig_ma_type?:       string;
  timeframe?:         string;
  hist_filters?:      string[];
  cross_filters?:     string[];
  cross_bars?:        number;
  crossover_lookback?: number;
  limit?:             number;
  offset?:            number;
}): Promise<MACDScanResult> {
  const r = await fetch(`${BASE}/macd/scan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!r.ok) {
    const detail = await r.json().catch(() => ({}));
    throw new Error((detail as { detail?: string }).detail ?? `HTTP ${r.status}`);
  }
  return r.json() as Promise<MACDScanResult>;
}

export async function getMACDChart(params: {
  exchange:      string;
  symbol:        string;
  source?:       string;
  fast?:         number;
  slow?:         number;
  signal_period?: number;
  osc_ma_type?:  string;
  sig_ma_type?:  string;
  timeframe?:    string;
  num_bars?:     number;
}): Promise<MACDChartData> {
  const r = await fetch(`${BASE}/macd/chart`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!r.ok) {
    const detail = await r.json().catch(() => ({}));
    throw new Error((detail as { detail?: string }).detail ?? `HTTP ${r.status}`);
  }
  return r.json() as Promise<MACDChartData>;
}

// ─── RSI Momentum API ─────────────────────────────────────────────────────────

export async function scanRSIMomentum(params: {
  universe: string;
  lookback_days: number;
  threshold: number;
  signals: string[];
}): Promise<RSIMomentumResult> {
  const r = await fetch(`${BASE}/rsi-momentum/scan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!r.ok) {
    const detail = await r.json().catch(() => ({}));
    throw new Error((detail as { detail?: string }).detail ?? `HTTP ${r.status}`);
  }
  return r.json() as Promise<RSIMomentumResult>;
}

// ─── TradingView screener API ────────────────────────────────────────────────

export interface TVField { name: string; label: string; type: string; timeframes: string[]; value_count: number; values: string[] }
export interface TVMarkets { countries: string[]; other: string[]; operators: Record<string, string>; asset_scopes: string[] }
export interface TVFilterNode { op: string; field?: string; value?: unknown; value2?: unknown; value3?: unknown; children?: TVFilterNode[] }
export interface TVScanRequest {
  markets: string[]; columns: string[]; filters: TVFilterNode | null; sort_by: string | null;
  ascending: boolean; limit: number; offset?: number; tickers?: string[]; index?: string | null; asset_scope?: string;
}
export interface TVScanResult { total: number; columns: string[]; rows: Record<string, unknown>[]; cached: boolean }
export interface TVPreset extends Partial<TVScanRequest> { id: string; name: string; market: string }

async function tvJson<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${BASE}/tv${path}`, init);
  if (!r.ok) {
    const d = await r.json().catch(() => ({})) as { message?: string; detail?: string };
    throw new Error(d.message ?? d.detail ?? `HTTP ${r.status}`);
  }
  return r.json() as Promise<T>;
}
export const getTVMarkets = () => tvJson<TVMarkets>("/markets");
export const getTVFields  = (market: string) => tvJson<TVField[]>(`/fields?market=${encodeURIComponent(market)}`);
export const getTVPresets = () => tvJson<TVPreset[]>("/presets");
export const scanTV = (body: TVScanRequest) =>
  tvJson<TVScanResult>("/scan", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
