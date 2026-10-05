# backend/alembic/versions/0001_initial_schema.py — Beginner Explanation

> **Source file:** `backend/alembic/versions/0001_initial_schema.py`

---

## 1. What is this file?

An **Alembic migration** — a Python script that defines how to create (or undo) database schema changes. This specific migration creates all 8 tables from scratch.

Equivalent to the Drizzle migration SQL files.

---

## 2. Alembic vs drizzle-kit

| drizzle-kit | Alembic |
|------------|---------|
| `drizzle-kit generate` | `alembic revision --autogenerate` |
| `drizzle-kit migrate` | `alembic upgrade head` |
| Generated SQL files | Generated Python files |
| `__drizzle_migrations` table | `alembic_version` table |

Both tools track which migrations have been applied using a special database table.

---

## 3. Migration file structure

```python
revision = "0001"
down_revision = None  # This is the first migration (no parent)
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create tables
    ...

def downgrade() -> None:
    # Drop tables
    ...
```

**`revision`** — Unique ID for this migration. When you run `alembic upgrade head`, Alembic looks at the `alembic_version` table, finds the current revision, and runs all migrations with a `down_revision` chain leading from there to `head`.

**`down_revision = None`** — This migration has no parent: it's the first one. A second migration would have `down_revision = "0001"`.

**`upgrade()`** — SQL to apply (create tables, add columns, etc.).

**`downgrade()`** — SQL to undo (drop tables, remove columns). Enables `alembic downgrade -1`.

---

## 4. Key migration patterns

### Creating a table

```python
op.create_table(
    "stocks",
    sa.Column("id", sa.String(), nullable=False),
    sa.Column("symbol", sa.String(), nullable=False),
    sa.Column("exchange", sa.String(), nullable=False),
    sa.Column("company_name", sa.String(), nullable=False),
    sa.Column("sector", sa.String(), nullable=True),
    sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.PrimaryKeyConstraint("id"),
)
```

**`server_default="true"`** — Sets the default value at the database level (not in Python). When you insert a row without specifying `is_active`, PostgreSQL uses `true`.

**`server_default=sa.func.now()`** — PostgreSQL sets `created_at` to the current timestamp automatically.

---

### Creating an index

```python
op.create_index("stocks_symbol_idx", "stocks", ["symbol"])
op.create_index("stocks_exchange_idx", "stocks", ["exchange"])
op.create_index("stocks_sector_idx", "stocks", ["sector"])
```

Indexes speed up queries that filter by these columns. Without them, PostgreSQL scans every row (slow for large tables).

---

### Foreign key constraint

```python
sa.ForeignKeyConstraint(
    ["universe_id"],
    ["universes.id"],
    ondelete="CASCADE",
)
```

Links `universe_memberships.universe_id` to `universes.id`. `CASCADE` means deleting a universe automatically deletes all its memberships.

---

## 5. Running migrations

```bash
# Apply all pending migrations (upgrade to latest)
make migrate
# or:
alembic upgrade head

# Check current migration state
alembic current

# See migration history
alembic history

# Undo last migration
make downgrade
# or:
alembic downgrade -1
```

---

## 6. Generating new migrations

When you add a column to a SQLAlchemy model:
```bash
make generate name="add_pe_ratio_to_stocks"
```

Alembic compares `Base.metadata` (your model definitions) to the database and generates the SQL differences automatically. You should always review the generated file before running `make migrate`.
