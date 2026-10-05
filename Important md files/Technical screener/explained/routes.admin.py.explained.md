# backend/app/routes/admin.py — Beginner Explanation

> **Source file:** `backend/app/routes/admin.py`

---

## 1. What is this file?

Admin-only endpoints for managing universe data. Currently has two endpoints — one to trigger a refresh from NSE CSV sources and one to check staleness.

---

## 2. Endpoints

### `POST /admin/universes/refresh`

Downloads all Nifty index CSVs and rebuilds universe membership in the database.

```
POST /admin/universes/refresh
POST /admin/universes/refresh?force=true   ← bypasses 90-day staleness guard
```

**Response (success):**
```json
{
  "refreshed_at": "2026-08-23T07:40:53Z",
  "total_stocks": 752,
  "by_cap_category": {"LARGE_CAP": 100, "MID_CAP": 150, "SMALL_CAP": 250, "MICRO_CAP": 252},
  "universe_counts": {"NIFTY_50": 50, "NIFTY_500": 500, "NIFTY_TOTAL_MARKET": 752},
  "fetch_errors": []
}
```

**Response (skipped — data still fresh):**
```json
{
  "skipped": true,
  "reason": "Data is 12d old — less than 90d threshold. Pass force=true to override.",
  "last_synced_at": "2026-08-11T..."
}
```

**Error (all CSV sources down):** HTTP 502 with detail message.

---

### `GET /admin/universes/status`

Check whether the universe data is stale without triggering a refresh.

```json
{
  "is_stale": false,
  "age_days": 1,
  "stale_threshold_days": 90,
  "message": "Data is fresh"
}
```

---

## 3. Makefile shortcut

```bash
make refresh-universes           # skips if < 90 days old
make refresh-universes FORCE=true  # force regardless
```

Run this quarterly (or after each NSE index rebalance, typically March and September).
