# backend/app/agents/chat_agent.py — Beginner Explanation

> **Source file:** `backend/app/agents/chat_agent.py`

---

## 1. What is this file?

Defines `LLMChatAgent` — the brain of the AI Chat feature. It receives a user's natural-language question, figures out what data is needed, fetches that data by dispatching to existing agents, and passes everything to the configured LLM to produce a readable answer.

**Design principle:** the LLM never touches the database or calls tools directly. It only receives pre-fetched data as plain text and synthesises a response.

---

## 2. Task type: `CHAT_TURN`

**Payload:**
```json
{
  "user_message": "Give me Nifty 500 stocks in approaching again zone with uptrend",
  "history": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
}
```

**Result data:**
```json
{
  "reply": "Here are the stocks...",
  "intent": "SCREEN",
  "has_context": true
}
```

---

## 3. Pipeline (in order)

```
1. _detect_intent()           → "SCREEN" | "QUOTE" | "FUNDAMENTALS" | "GENERAL"
2. _do_screen / _do_quote / _do_fundamentals
3. LLM formats the result     → _llm_respond()
```

---

## 4. How screening works — two-phase approach

### Phase 1: LLM extracts structured filters
```python
extracted = _llm_extract_filters(message)
```
A dedicated LLM call with a precise system prompt (`_FILTER_EXTRACTION_SYSTEM`) converts natural language into a JSON object listing exact filter conditions:

```json
{
  "universe": "NIFTY_500",
  "conditions": [
    {"type": "indicator", "indicator": "rsi_momentum", "field": "signal_rank", "op": "gte", "value": 4.5},
    {"type": "indicator", "indicator": "rsi_momentum", "field": "signal_rank", "op": "lt",  "value": 5.0},
    {"type": "indicator", "indicator": "rsi_momentum", "field": "rsi_trend",   "op": "eq",  "value": 1.0}
  ],
  "rank_by": {"indicator": "rsi_momentum", "field": "rsi_today", "timeframe": "1D", "order": "desc"}
}
```

The extraction prompt lists every available signal, indicator field, and numeric threshold so the LLM knows exactly what values to use. This handles natural language far better than regex alone.

### Phase 2: Regex fallback
If the LLM extraction fails or returns invalid JSON, the agent falls back to a comprehensive set of regex patterns covering all signals, RSI trend, Bollinger Band conditions, and volume.

---

## 5. Filter extraction prompt (`_FILTER_EXTRACTION_SYSTEM`)

Covers:
- **RSI Momentum signals** — FRESH_BREAKOUT=5.0, APPROACHING_AGAIN=4.5, APPROACHING=4.0, ALREADY_STRONG=3.0, EXTENDED=2.0, NEUTRAL=1.0
- **RSI Trend** — uptrend=1.0, flat=0.0, downtrend=-1.0 (today vs yesterday RSI)
- **Bollinger Bands** — above upper band (>1.0), touching upper band (≥0.95), near upper band (≥0.88), above middle (>0.5), near lower band (≤0.15)
- **Volume** — volume_ratio > 100 means today's volume exceeds 30-day average
- **MACD** — bullish_crossover=1.0 (crossed above signal today), bearish_crossover=1.0, histogram gt/lt 0
- **Market cap** — classification filter

---

## 6. Bollinger Band thresholds

| %B value | Label | What it means |
|---|---|---|
| > 1.05 | ABOVE UPPER BAND | Price broke above the band |
| ≥ 0.95 | TOUCHING UPPER BAND | Price right at the upper band |
| ≥ 0.88 | NEAR UPPER BAND | Close but not touching |
| > 0.55 | ABOVE MIDDLE (not near upper band) | Between middle and upper |
| ≥ 0.45 | AT MIDDLE BAND | At the 20-SMA |
| > 0.10 | BELOW MIDDLE | Between middle and lower |
| ≥ 0.0  | NEAR/AT LOWER BAND | At the lower band |
| < 0.0  | BELOW LOWER BAND | Price broke below |

"Touches upper BB" in user queries maps to ≥ 0.95 — not 0.85 which only means "above middle".

---

## 7. Filter summary in context

Every screen result now includes a human-readable filter summary injected into the LLM context:
```
Active filters: Signal: APPROACHING_AGAIN — RSI pulled back to within 5pts below threshold | RSI Trend = RISING | Volume > 100% of 30-day average
```
This prevents the LLM from guessing wrong descriptions (e.g. "RSI > 58" when the real threshold is 60).

---

## 8. Quote lookup — key name fix

`_fmt_quote` reads `data.get("price")` (not `"current_price"`) and `data.get("week52_high")` (not `"week_52_high"`) to match the keys that `market_data_agent` actually returns.

---

## 9. LLM context injection

```python
user_content = (
    f"{user_message}\n\n"
    f"═══ FRESH MARKET DATA ═══\n{context}\n═══ END ═══\n\n"
    f"Answer using the fresh data above."
)
```

Fetched data is embedded in the user message so the LLM references exact numbers without hallucinating them.

---

## 10. Multi-timeframe support

Every filter condition has a `timeframe` field. The LLM extraction prompt lists all supported timeframes and their meanings, so queries like:

> "RSI > 60 daily AND MACD bullish on 1W"

generate two separate conditions with different timeframes:
```json
[
  {"indicator": "rsi",  "field": "value",    "timeframe": "1H", "op": "gt", "value": 60},
  {"indicator": "macd", "field": "histogram", "timeframe": "1W", "op": "gt", "value": 0}
]
```

The screening service fetches each `(indicator, timeframe)` pair independently and caches them separately. Supported timeframes: `1H`, `4H`, `1D`, `1W`, `1M`.

In the regex fallback, `_extract_timeframe(message)` detects the primary timeframe keyword and applies it to all non-RSI-momentum conditions (RSI Momentum signals always use 1D since they're computed from daily close).

---

## 11. History handling

```python
for m in history[-10:]:   # last 10 messages only
    messages.append(LLMMessage(role=m["role"], content=m["content"]))
```

Keeps recent conversation context without bloating the prompt with stale turns.
