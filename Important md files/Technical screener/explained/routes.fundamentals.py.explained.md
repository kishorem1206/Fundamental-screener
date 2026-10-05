# backend/app/routes/fundamentals.py — Beginner Explanation

> **Source file:** `backend/app/routes/fundamentals.py`

---

## 1. What is this file?

Defines `GET /stocks/{exchange}/{symbol}/fundamentals`. Thin route that dispatches to `FundamentalAgent` and maps agent error codes to appropriate HTTP statuses.

---

## 2. Endpoint

```
GET /stocks/NSE/INFY/fundamentals
GET /stocks/NSE/TCS/fundamentals
```

---

## 3. Error mapping

| Agent error code | HTTP status | Reason |
|---|---|---|
| `DATA_UNAVAILABLE` | 404 | Symbol not found on yfinance |
| `VALIDATION_ERROR` | 404 | Missing symbol in payload |
| anything else | 500 | Unexpected fetch/parse failure |
