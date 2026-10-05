# backend/app/routes/quotes.py — Beginner Explanation

> **Source file:** `backend/app/routes/quotes.py`

---

## 1. What is this file?

Defines the `GET /stocks/{exchange}/{symbol}/quote` route. Receives the request, builds an `AgentTask` for `MarketDataAgent`, dispatches it via the message bus, and returns the quote data.

---

## 2. Endpoint

```
GET /stocks/NSE/INFY/quote
GET /stocks/BSE/RELIANCE/quote
```

Returns a JSON quote object (see `market_data_agent.py.explained.md` for the full shape).

---

## 3. Error mapping

| Agent error code | HTTP status |
|---|---|
| `DATA_UNAVAILABLE` | 404 |
| anything else | 500 |

This is deliberate: if yfinance can't find the symbol, the user should get a 404 (not found), not a 500 (server error).
