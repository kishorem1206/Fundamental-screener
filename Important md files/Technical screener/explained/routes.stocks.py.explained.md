# backend/app/routes/stocks.py — Beginner Explanation

> **Source file:** `backend/app/routes/stocks.py`

---

## 1. What is this file?

Defines two HTTP endpoints for listing and fetching stocks. Demonstrates FastAPI's query parameter handling and path parameter parsing.

---

## 2. The two endpoints

| Endpoint | Returns |
|----------|---------|
| `GET /stocks` | Filtered, paginated list of stocks |
| `GET /stocks/{exchange}/{symbol}` | One stock by exchange and symbol |

---

## 3. Line-by-line explanation

### Query parameters in FastAPI

```python
@router.get("/stocks")
def get_stocks(
    request: Request,
    universe_id: str | None = None,
    sector: str | None = None,
    macro_sector: str | None = None,
    market_cap_category: Literal["LARGE_CAP", "MID_CAP", "SMALL_CAP", "MICRO_CAP", "NANO_CAP"] | None = None,
    limit: int = 50,
    offset: int = 0,
):
```

**Function parameters as query params** — FastAPI automatically maps function parameters to URL query parameters. `GET /stocks?sector=IT&limit=20` would set `sector="IT"` and `limit=20`.

**`str | None = None`** — Optional query parameter. If not in the URL, defaults to `None`.

**`Literal["LARGE_CAP", ...]`** — FastAPI validates this automatically. If the caller sends `?market_cap_category=INVALID`, FastAPI returns a 422 error before the function even runs.

**`limit: int = 50`** — FastAPI automatically converts the string `"50"` from the URL to the integer `50`. Default is 50 if not specified.

---

### Building the task

```python
    task = AgentTask(
        correlation_id=request.state.correlation_id,
        from_agent="stocks_route",
        to_agent="classification_agent",
        task_type="LIST_STOCKS",
        payload={
            "universe_id": universe_id,
            "sector": sector,
            "macro_sector": macro_sector,
            "market_cap_category": market_cap_category,
            "limit": limit,
            "offset": offset,
        },
        created_at=now_iso(),
    )
```

All query parameters are bundled into the `payload` dict. The agent extracts and uses them.

---

### `GET /stocks/{exchange}/{symbol}`

```python
@router.get("/stocks/{exchange}/{symbol}")
def get_stock(exchange: str, symbol: str, request: Request):
    task = AgentTask(
        correlation_id=request.state.correlation_id,
        from_agent="stocks_route",
        to_agent="classification_agent",
        task_type="GET_STOCK",
        payload={"exchange": exchange, "symbol": symbol},
        created_at=now_iso(),
    )
    result = agent_message_bus.dispatch(task)

    if result.status == "FAILED":
        errors = result.errors
        if errors and errors[0].code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=errors[0].message)
        raise HTTPException(status_code=500, detail=errors[0].message if errors else "Unknown error")

    return result.data
```

**Two path parameters** — `{exchange}` and `{symbol}` are both extracted from the URL path. `GET /stocks/NSE/INFY` sets `exchange="NSE"` and `symbol="INFY"`.

**Why two path params instead of one?** — The primary key in the database is `"NSE:INFY"`. Splitting it makes the URL cleaner (`/stocks/NSE/INFY` vs `/stocks/NSE:INFY`). The agent reconstructs `"NSE:INFY"` from the two parts.

---

## 4. Example requests

```bash
# All stocks (first 50)
GET /stocks

# Stocks in Nifty 50
GET /stocks?universe_id=nifty50

# Large-cap IT stocks, page 2
GET /stocks?sector=IT&market_cap_category=LARGE_CAP&limit=20&offset=20

# One specific stock
GET /stocks/NSE/INFY
```

---

## 5. HTTP status codes returned

| Scenario | Status |
|---------|--------|
| Success | 200 OK |
| Stock not found | 404 Not Found |
| Invalid query param value | 422 Unprocessable Entity (FastAPI automatic) |
| Service error | 500 Internal Server Error |
