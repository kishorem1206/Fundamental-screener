# backend/app/services/classification_service.py — Beginner Explanation

> **Source file:** `backend/app/services/classification_service.py`

---

## 1. What is this file?

Contains the business logic for querying stocks and universes from the database. Routes call agents, agents call this service, this service talks to PostgreSQL via SQLAlchemy.

Equivalent to TypeScript's `classificationService.ts`.

---

## 2. The data flow

```
HTTP Request
  ↓
Route handler (stocks.py / universes.py)
  ↓
Agent (classification_agent.py / universe_agent.py)
  ↓
ClassificationService  ← this file
  ↓
SQLAlchemy ORM query
  ↓
PostgreSQL
```

---

## 3. Dataclasses — the return types

```python
@dataclass
class StockRow:
    id: str
    symbol: str
    exchange: str
    company_name: str
    sector: str | None
    macro_sector: str | None
    market_cap_category: str | None
    is_active: bool
```

**`@dataclass`** — Python decorator that auto-generates `__init__`, `__repr__`, `__eq__` for a class based on its annotated fields. Like TypeScript's `type StockRow = {id: string, symbol: string, ...}` but it's a real class.

We use dataclasses (not Pydantic models) for service return types because:
1. No validation needed — data comes from our own trusted database
2. `dataclasses.asdict()` converts to dict easily for JSON responses

---

## 4. `StockListFilters`

```python
@dataclass
class StockListFilters:
    universe_id: str | None = None
    sector: str | None = None
    macro_sector: str | None = None
    market_cap_category: str | None = None
    limit: int = 50
    offset: int = 0
```

A dataclass for grouping query filter parameters. Instead of passing 6 separate arguments, you pass one `StockListFilters` object.

---

## 5. Query patterns

### Simple query: `list_universes`

```python
def list_universes(self) -> list[UniverseRow]:
    db = get_db()
    try:
        rows = db.query(Universe).filter(Universe.is_active == True).all()
        return [UniverseRow(
            id=r.id,
            slug=r.slug,
            display_name=r.display_name,
            description=r.description,
            stock_count=r.stock_count,
            last_synced_at=r.last_synced_at,
        ) for r in rows]
    finally:
        db.close()
```

**`db.query(Universe)`** — Creates a query that will `SELECT * FROM universes`.

**`.filter(Universe.is_active == True)`** — Adds a `WHERE is_active = true` clause. SQLAlchemy translates Python `==` to SQL `=`.

**`.all()`** — Executes the query and returns all matching rows as a list of `Universe` ORM objects.

**List comprehension `[UniverseRow(...) for r in rows]`** — Converts each ORM object to our dataclass. Separates the "DB layer" (ORM objects) from the "service layer" (our dataclasses).

---

### Filtered query: `list_stocks`

```python
def list_stocks(self, filters: StockListFilters) -> list[StockRow]:
    db = get_db()
    try:
        query = db.query(Stock)

        if filters.universe_id:
            query = query.join(
                UniverseMembership,
                Stock.id == UniverseMembership.stock_id,
            ).filter(UniverseMembership.universe_id == filters.universe_id)

        if filters.sector:
            query = query.filter(Stock.sector == filters.sector)

        if filters.market_cap_category:
            query = query.filter(Stock.market_cap_category == filters.market_cap_category)

        query = query.filter(Stock.is_active == True)
        return [StockRow(...) for r in query.offset(filters.offset).limit(filters.limit).all()]
    finally:
        db.close()
```

**Conditional JOIN** — Only joins the `universe_memberships` table when filtering by universe. Avoids unnecessary joins.

**`.join(UniverseMembership, Stock.id == UniverseMembership.stock_id)`** — SQL: `JOIN universe_memberships ON stocks.id = universe_memberships.stock_id`.

**`.offset(n).limit(n)`** — Pagination. `offset=0, limit=50` is the first page; `offset=50, limit=50` is the second page.

---

### Single item: `get_stock`

```python
def get_stock(self, exchange: str, symbol: str) -> StockRow:
    db = get_db()
    try:
        stock_id = f"{exchange.upper()}:{symbol.upper()}"
        row = db.get(Stock, stock_id)
        if row is None:
            raise NotFoundError("Stock", stock_id)
        return StockRow(...)
    finally:
        db.close()
```

**`db.get(Model, pk)`** — Fetches by primary key. Returns `None` if not found (vs raising an exception). We then raise `NotFoundError` ourselves for consistent error handling.

---

## 6. The `try/finally` pattern

Every method follows:
```python
db = get_db()
try:
    # do the work
    return result
finally:
    db.close()
```

`finally` always runs, even if an exception is raised. This guarantees the connection is returned to the pool. Without `db.close()`, connections would accumulate until the pool is exhausted.
