# backend/app/services/stock_seed_loader.py — Beginner Explanation

> **Source file:** `backend/app/services/stock_seed_loader.py`

---

## 1. What is this file?

Loads the initial stock data from a JSON file into the database. It's called by `scripts/seed_stocks.py` during setup.

Equivalent to TypeScript's `seedStocks.ts`.

---

## 2. What it does

1. Reads `scripts/seeds/nifty50.json` (50 stock records)
2. For each stock:
   - If already in DB → update fields
   - If not in DB → insert new row
3. Updates the stock count on the Nifty 50 universe
4. Commits everything in one transaction

---

## 3. Line-by-line explanation

### `load_from_file`

```python
def load_from_file(self, json_path: str) -> None:
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"Seed file not found: {json_path}")
    with open(path) as f:
        data = json.load(f)
    self.load(data)
```

**`Path(json_path)`** — Python's `pathlib.Path` provides OS-independent file path operations. `path.exists()` checks if the file is there.

**`with open(path) as f:`** — Context manager for file I/O. Automatically closes the file when the block exits (even on exception).

**`json.load(f)`** — Reads and parses the JSON file into a Python dict.

---

### `load` — the upsert logic

```python
def load(self, data: dict) -> None:
    db = get_db()
    try:
        stocks_data: list[dict] = data.get("stocks", [])
        universe_slug: str = data.get("universe", "nifty50")

        for stock_data in stocks_data:
            stock_id = f"{stock_data['exchange']}:{stock_data['symbol']}"

            existing = db.get(Stock, stock_id)
            if existing:
                # Update existing record
                existing.company_name = stock_data["company_name"]
                existing.sector = stock_data.get("sector")
                # ...more fields
            else:
                # Insert new record
                db.add(Stock(
                    id=stock_id,
                    symbol=stock_data["symbol"],
                    # ...
                ))
```

**`db.get(Stock, stock_id)`** — Fetches by primary key. Returns the existing `Stock` ORM object, or `None`.

**Updating an existing object** — SQLAlchemy tracks changes to ORM objects. When you do `existing.company_name = "new name"`, SQLAlchemy marks this object as "dirty" and includes it in the next `commit()`.

**`db.add(new_stock)`** — Stages a new insert. The INSERT actually runs at `commit()`.

---

### Universe + stock count update

```python
        universe = db.query(Universe).filter(Universe.slug == universe_slug).first()
        if universe:
            result = db.execute(
                text("SELECT COUNT(*) FROM universe_memberships WHERE universe_id = :uid"),
                {"uid": universe.id},
            )
            universe.stock_count = result.scalar()
```

**`db.query(...).filter(...).first()`** — Returns the first matching row or `None`.

**`text("SELECT COUNT(*) ...")`** — Raw SQL using SQLAlchemy's `text()` wrapper. Used here because the `COUNT` is simpler to express in SQL than via ORM.

**`result.scalar()`** — Returns the single value from the first column of the first row. For `SELECT COUNT(*)`, this is the integer count.

---

### Transaction: commit or rollback

```python
        db.commit()
        logger.info("Seed completed", stocks_loaded=len(stocks_data))
    except Exception as e:
        db.rollback()
        logger.error("Seed failed", error=str(e))
        raise
    finally:
        db.close()
```

**`db.commit()`** — Applies all staged inserts and updates to the database in one atomic transaction.

**`db.rollback()`** — If anything fails, undo all changes since the last commit. Keeps the database clean (no partial seed data).

**`raise`** — Re-raises the exception after rollback, so the caller sees the error.

---

## 4. Why get-or-create instead of upsert?

PostgreSQL has `INSERT ... ON CONFLICT DO UPDATE` (upsert), but we chose get-or-create for simplicity and cross-database compatibility. It's slightly slower (one SELECT per stock) but easier to understand.

For 50 stocks, the performance difference is negligible. The seed runs once at setup, not on every request.
