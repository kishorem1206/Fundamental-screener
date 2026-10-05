# backend/app/routes/nifty_index.py — Beginner Explanation

> **Source file:** `backend/app/routes/nifty_index.py`

---

## 1. What is this file?

FastAPI routes for Nifty index classification queries — the public-facing API layer. Each handler dispatches to `NiftyIndexAgent` via `agent_message_bus`.

---

## 2. Endpoints

### `GET /nifty/indices`
List all known Nifty indices. Optional `?category=SECTORAL` filter.

### `GET /nifty/indices/{index_code}/constituents`
Return all stocks currently in the named index.

```
GET /nifty/indices/nifty-bank/constituents
GET /nifty/indices/nifty-50/constituents?as_of=2026-03-01
```

`index_code` is the slug form: `nifty-50`, `nifty-bank`, `nifty-pharma`, etc.
`?as_of=YYYY-MM-DD` returns the historical membership on that date.

### `GET /nifty/stocks/{symbol}/indices`
Return all Nifty indices a stock currently belongs to, grouped by category.

```
GET /nifty/stocks/AUBANK/indices
GET /nifty/stocks/AUBANK/indices?as_of=2026-06-15
GET /nifty/stocks/ITC/indices?category=SECTORAL
```

### `GET /nifty/indices/{index_a}/intersection/{index_b}`
Return stocks that appear in both indices simultaneously.

```
GET /nifty/indices/nifty-bank/intersection/nifty-financial-services
```

---

## 3. Response examples

**`GET /nifty/stocks/AUBANK/indices`**
```json
{
  "symbol": "AUBANK",
  "company_name": "AU Small Finance Bank Limited",
  "data_as_of": "2026-08-23",
  "queried_date": "2026-08-23",
  "source": "NSE Indices",
  "indices": {
    "broad-market": [{"name": "Nifty 500", "index_id": "nifty-500"}],
    "sectoral": [
      {"name": "Nifty Bank", "index_id": "nifty-bank"},
      {"name": "Nifty Private Bank", "index_id": "nifty-private-bank"}
    ]
  }
}
```

**`GET /nifty/indices/nifty-bank/constituents`**
```json
{
  "index": "Nifty Bank",
  "category": "Sectoral",
  "total": 12,
  "constituents": [
    {"symbol": "AUBANK", "company_name": "...", "market_cap_category": "MID_CAP"},
    ...
  ]
}
```

---

## 4. When data is missing

If the catalog has not been seeded (`POST /admin/nifty/seed`) or no ingestion has run yet, the classification queries return `{"error": "Stock '...' not found in database"}` or empty `indices: {}`. This is correct — the LLM should surface this to the user rather than guessing.
