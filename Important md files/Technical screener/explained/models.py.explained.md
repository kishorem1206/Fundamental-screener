# backend/app/infrastructure/database/models.py — Beginner Explanation

> **Source file:** `backend/app/infrastructure/database/models.py`

---

## 1. What is this file?

This file defines the **SQLAlchemy ORM models** — Python classes that map to database tables. Each class represents one table; each class attribute represents one column.

Equivalent to the TypeScript `schema.ts` which used Drizzle ORM to define the same 8 tables.

---

## 2. SQLAlchemy ORM vs Drizzle ORM

| Drizzle (was) | SQLAlchemy 2.0 (now) |
|--------------|---------------------|
| `pgTable("stocks", {...})` | `class Stock(Base):` |
| `text("id").primaryKey()` | `id: Mapped[str] = mapped_column(String, primary_key=True)` |
| `text("company_name").notNull()` | `company_name: Mapped[str] = mapped_column(String, nullable=False)` |
| `bigint(..., {mode: "number"})` | `BigInteger` column, `Mapped[int | None]` |
| `index("idx").on(t.col)` | `Index("idx", "column")` in `__table_args__` |
| `primaryKey({columns: [...]})` | `PrimaryKeyConstraint(...)` in `__table_args__` |

---

## 5. Key concepts

### `DeclarativeBase`

```python
class Base(DeclarativeBase):
    pass
```

`Base` is the foundation all models inherit from. It registers all subclasses with SQLAlchemy's metadata — when Alembic generates migrations, it reads from `Base.metadata` to know what tables exist.

---

### `Mapped[T]` and `mapped_column()`

```python
class Stock(Base):
    __tablename__ = "stocks"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    company_name: Mapped[str] = mapped_column("company_name", String, nullable=False)
    isin: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column("is_active", Boolean, default=True, nullable=False)
```

**`Mapped[str]`** — A type annotation that tells SQLAlchemy and Python type checkers: this attribute is always a string. `Mapped[str | None]` means it can be `None` (nullable column).

**`mapped_column("company_name", ...)`** — The first argument is the actual database column name. Python uses `company_name` (snake_case); the DB column is also `company_name`.

**`nullable=False`** — Equivalent to `.notNull()` in Drizzle. The DB will reject `NULL` values for this column.

---

### `__table_args__` — indexes and composite keys

```python
class UniverseMembership(Base):
    __tablename__ = "universe_memberships"

    universe_id: Mapped[str] = mapped_column(...)
    stock_id: Mapped[str] = mapped_column(...)
    added_at: Mapped[datetime] = mapped_column(...)

    __table_args__ = (
        PrimaryKeyConstraint("universe_id", "stock_id"),
        Index("universe_memberships_universe_idx", "universe_id"),
        Index("universe_memberships_stock_idx", "stock_id"),
    )
```

**`PrimaryKeyConstraint`** — Composite primary key (both columns together form the PK). Equivalent to Drizzle's `primaryKey({columns: [t.universeId, t.stockId]})`.

**`Index`** — Creates a database index to speed up queries. Equivalent to Drizzle's `index("name").on(column)`.

---

### Foreign keys

```python
universe_id: Mapped[str] = mapped_column(
    "universe_id", String,
    ForeignKey("universes.id", ondelete="CASCADE"),
    nullable=False
)
```

**`ForeignKey("universes.id")`** — Links this column to the `id` column in the `universes` table.

**`ondelete="CASCADE"`** — If a universe is deleted, all its memberships are automatically deleted too. Same as Drizzle's `references(() => universes.id, {onDelete: "cascade"})`.

---

## 6. The 8 tables

| Python class | DB table | Purpose |
|-------------|----------|---------|
| `Stock` | `stocks` | One row per NSE/BSE listed stock |
| `Universe` | `universes` | Stock collections (Nifty 50, etc.) |
| `UniverseMembership` | `universe_memberships` | Which stocks belong to which universe |
| `IndicatorDefinition` | `indicator_definitions` | RSI_14, BB_20_2 etc. definitions |
| `ScreenDefinition` | `screen_definitions` | Saved screening criteria |
| `ChatSession` | `chat_sessions` | LLM chat session metadata |
| `ChatMessage` | `chat_messages` | Individual chat messages |
| `DataProvenanceLog` | `data_provenance_log` | Audit trail: where each data point came from |

---

## 7. Simple mental model

An ORM model is a **blueprint** for a database table:
- The class = the table
- Each attribute = a column
- An instance of the class = one row in that table

When you do `db.add(Stock(id="NSE:INFY", symbol="INFY", ...))`, SQLAlchemy translates it into `INSERT INTO stocks (id, symbol, ...) VALUES ('NSE:INFY', 'INFY', ...)`.
