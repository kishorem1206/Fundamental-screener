# backend/app/agents/fundamental_agent.py — Beginner Explanation

> **Source file:** `backend/app/agents/fundamental_agent.py`

---

## 1. What is this file?

Defines `FundamentalAgent` — fetches company fundamentals (valuation ratios, profitability, balance sheet metrics) from yfinance. Results are cached for 24 hours since fundamentals change slowly (quarterly reports, annual filings).

When INDMoney MCP is reconnected it can serve as a richer enrichment layer on top without changing this file's interface.

---

## 2. Task type: `GET_FUNDAMENTALS`

**Payload:** `{"exchange": "NSE", "symbol": "INFY"}`

**Key fields returned:**

| Category | Fields |
|---|---|
| Valuation | `trailing_pe`, `forward_pe`, `price_to_book`, `price_to_sales`, `ev_to_ebitda` |
| Per-share | `trailing_eps`, `forward_eps`, `book_value`, `dividend_yield`, `dividend_rate` |
| Growth | `revenue_growth`, `earnings_growth` |
| Profitability | `profit_margin`, `operating_margin`, `return_on_equity`, `return_on_assets` |
| Balance sheet | `debt_to_equity`, `current_ratio`, `quick_ratio` |
| Price stats | `beta`, `week52_high`, `week52_low`, `avg_volume` |

---

## 3. `_safe_float` and `_safe_int` helpers

```python
def _safe_float(val) -> float | None:
    try:
        return round(float(val), 4)
    except (TypeError, ValueError):
        return None
```

yfinance sometimes returns `None`, `"N/A"`, or other non-numeric values for fields that aren't available. `_safe_float` converts what it can and returns `None` otherwise — so the response JSON always has the field (as `null`) rather than crashing.

---

## 4. Description truncation

```python
"description": (info.get("longBusinessSummary") or "")[:500] or None,
```

`longBusinessSummary` can be hundreds of words long. We cap at 500 characters for the API response. The `or None` at the end converts an empty string `""` back to `None`.

---

## 5. Redis cache key

```
fundamentals:{exchange}:{symbol}   →   TTL 24 hours
```

Long TTL because PE ratios don't change intraday.
