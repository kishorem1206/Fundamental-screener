# backend/app/infrastructure/database/models.py — Beginner Explanation

> **Source file:** `backend/app/infrastructure/database/models.py`

---

## 1. What is this file?

Defines all SQLAlchemy ORM models — one Python class per database table. Alembic reads these via `Base.metadata` to generate migrations.

---

## 2. Original tables

| Table | Purpose |
|---|---|
| `stocks` | Master list of all NSE/BSE stocks |
| `universes` | Screener universes (Nifty 50, Nifty 500, etc.) |
| `universe_memberships` | Which stocks are in which screener universe |
| `indicator_definitions` | RSI, Bollinger, etc. parameter definitions |
| `screen_definitions` | Saved screener filter presets |
| `chat_sessions` / `chat_messages` | AI chat history |
| `data_provenance_log` | Audit trail for data source calls |

---

## 3. New tables (added in migration 0002)

### `index_categories`

```
BROAD_MARKET | SECTORAL | THEMATIC | STRATEGY | FIXED_INCOME | HYBRID
```

Seeded once by `NiftyIndexIngestionService.seed_catalog()`.

---

### `nifty_indices`

The catalogue of known Nifty indices. Each row has:
- `id` / `index_code` — slug like `"nifty-50"`, `"nifty-bank"`
- `index_name` — display name like `"Nifty 50"`, `"Nifty Bank"`
- `category_id` → `index_categories.id`
- `source_url` — the NSE CSV download URL
- `is_active` — whether to include in ingestion runs

---

### `ingestion_runs`

One row per ingestion run execution. Tracks counts of files/records downloaded, inserted, removed, and unchanged. Includes a `change_report` JSON column with per-index diffs.

---

### `source_files`

One row per CSV downloaded. Records the file hash (SHA-256), file size, and processing status. If the same file is downloaded twice with the same hash, it can be detected as unchanged.

---

### `staging_index_constituents`

Temporary staging area — rows are written here before being validated and promoted to `index_constituents`. This ensures a bad CSV cannot corrupt production data.

---

### `index_constituents`

The most important new table. Records which stock belongs to which index, with full historical tracking:

```
stock_id   | index_id    | effective_from | effective_to
NSE:AUBANK | nifty-bank  | 2026-07-01     | NULL         ← currently a member
NSE:OLDCO  | nifty-bank  | 2026-01-01     | 2026-06-30   ← was a member, removed in June
```

`effective_to IS NULL` means the stock is currently a member.

The unique constraint `(index_id, stock_id, effective_from)` prevents duplicate active membership entries.
