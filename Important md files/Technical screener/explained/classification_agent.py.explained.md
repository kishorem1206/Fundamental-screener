# backend/app/agents/classification_agent.py — Beginner Explanation

> **Source file:** `backend/app/agents/classification_agent.py`

---

## 1. What is this file?

Defines `ClassificationAgent` — the agent responsible for stock-related tasks (`LIST_STOCKS`, `GET_STOCK`). It receives an `AgentTask`, extracts filter parameters from the payload, calls the classification service, and returns an `AgentResult`.

---

## 2. Supported task types

| `task_type` | What it does |
|-------------|-------------|
| `LIST_STOCKS` | Returns a filtered, paginated list of stocks |
| `GET_STOCK` | Returns one stock by exchange + symbol |

---

## 3. Line-by-line explanation

### `_list_stocks`

```python
def _list_stocks(self, task: AgentTask) -> AgentResult:
    try:
        payload = task.payload or {}
        filters = StockListFilters(
            universe_id=payload.get("universe_id"),
            sector=payload.get("sector"),
            macro_sector=payload.get("macro_sector"),
            market_cap_category=payload.get("market_cap_category"),
            limit=int(payload.get("limit", 50)),
            offset=int(payload.get("offset", 0)),
        )
        stocks = classification_service.list_stocks(filters)
        return self._success(task, [dataclasses.asdict(s) for s in stocks])
    except Exception as e:
        logger.error("ClassificationAgent: list_stocks failed", error=str(e))
        return self._failure(task, "LIST_FAILED", str(e))
```

**`task.payload or {}`** — If the payload is `None` (no filters sent), use an empty dict so `payload.get(...)` works without crashing.

**`payload.get("limit", 50)`** — Returns the value at key `"limit"` or `50` if the key doesn't exist (default pagination).

**`int(payload.get("limit", 50))`** — Explicit conversion to int because JSON numbers can sometimes come through as strings depending on how the payload is built.

**`StockListFilters(...)`** — Groups all the individual filter values into one object to pass to the service.

---

### `_get_stock`

```python
def _get_stock(self, task: AgentTask) -> AgentResult:
    try:
        payload = task.payload or {}
        exchange = payload.get("exchange", "NSE")
        symbol = payload.get("symbol", "")

        if not symbol:
            return self._failure(task, "VALIDATION_ERROR", "Symbol is required")

        stock = classification_service.get_stock(exchange, symbol)
        return self._success(task, dataclasses.asdict(stock))
    except NotFoundError as e:
        return self._failure(task, "NOT_FOUND", e.message)
    except Exception as e:
        logger.error("ClassificationAgent: get_stock failed", error=str(e))
        return self._failure(task, "GET_FAILED", str(e))
```

**`except NotFoundError as e:`** — Catches `NotFoundError` separately from generic exceptions. This produces a specific `"NOT_FOUND"` error code in the result, which routes can translate to a 404 HTTP response.

**`except Exception as e:`** — Catch-all for any other exception. Produces a generic `"GET_FAILED"` error.

Two `except` blocks — Python tries them in order, using the first one that matches.

---

## 4. The payload convention

Route handlers build `AgentTask` with a `payload` dict containing the query parameters:

```python
# In stocks.py route handler:
task = AgentTask(
    from_agent="stocks_route",
    to_agent="classification_agent",
    task_type="LIST_STOCKS",
    payload={
        "universe_id": universe_id,  # from query string
        "sector": sector,
        "limit": limit,
        "offset": offset,
    },
    ...
)
```

The agent then reads these from `task.payload`. This loose coupling means the route doesn't need to import `StockListFilters` — the agent handles that translation.

---

## 5. Module-level singleton

```python
classification_agent = ClassificationAgent()
```

One instance, registered in `main.py` lifespan, shared by all requests.
