# backend/app/services/nifty_index_ingestion_service.py — Beginner Explanation

> **Source file:** `backend/app/services/nifty_index_ingestion_service.py`

---

## 1. What is this file?

Downloads official NSE index constituent CSVs, validates them, computes diffs against the current DB, and applies changes transactionally with full historical tracking.

This is the data layer behind `NiftyIndexAgent`. It replaces the earlier `NiftyRefreshService` approach for the new index classification tables.

---

## 2. Key design principles

**PostgreSQL is the source of truth.** The LLM and UI must never claim index membership from anywhere other than the `index_constituents` table.

**History is preserved.** When a stock leaves an index, its row gets `effective_to = today`. It's never deleted. You can query "which indices did AUBANK belong to on 2026-03-01?" with a date filter.

**Staging before production.** Every row parsed from a CSV is inserted into `staging_index_constituents` first. Only after passing validation and sanity checks does it affect the live `index_constituents` table.

**Sanity guard.** If a new CSV shows fewer than 50% of the previous constituent count, the ingestion for that index is rejected to prevent a malformed/empty CSV from destroying good data.

---

## 3. Index catalog bootstrap

```python
_INITIAL_INDICES = [
    ("nifty-50", "Nifty 50", "BROAD_MARKET", "ind_nifty50list.csv"),
    ("nifty-bank", "Nifty Bank", "SECTORAL", "ind_niftybank_list.csv"),
    ...
]
```

29 indices are seeded on first `POST /admin/nifty/seed`. After that, new indices can be added directly to the `nifty_indices` table without code changes.

---

## 4. Ingestion workflow per index

```
1. Download CSV via httpx (browser User-Agent + Referer headers)
2. Compute SHA-256 hash → record in source_files
3. Parse CSV (normalize column name variations: "Symbol" / "SYMBOL" / "Ticker")
4. Insert rows into staging_index_constituents (resolve stock via ISIN then symbol)
5. Sanity check: new valid count ≥ 50% of current active count?
6. Diff: new_stock_ids - current_stock_ids = ADDED; reverse = REMOVED
7. If not dry_run:
   - UPDATE effective_to = today on removed rows
   - INSERT new rows with effective_from = today
8. Record outcome in ingestion_runs
```

---

## 5. Dry-run mode

```python
if dry_run:
    db.rollback()
```

The entire DB session is rolled back, so nothing persists. The returned `change_report` still shows what *would have* changed, which is useful for sanity-checking before a real ingestion.

---

## 6. Change report structure

```json
{
  "run_id": "...",
  "dry_run": false,
  "date": "2026-08-23",
  "indices": [
    {
      "index_id": "nifty-bank",
      "index_name": "Nifty Bank",
      "records_read": 12,
      "added": ["NEWSTOCK"],
      "removed": ["OLDSTOCK"],
      "unchanged": 10,
      "error": null
    }
  ],
  "totals": { "records_inserted": 5, "records_removed": 3, ... }
}
```

---

## 7. How to run

```bash
# Seed catalog (once after migration)
make nifty-seed

# Dry run — see what would change
make nifty-dry-run

# Real ingestion
make nifty-ingest

# Restrict to specific indices
make nifty-ingest INDEX_IDS=nifty-50,nifty-bank

# Status of last run
make nifty-status
```

---

## 8. Error handling

If one CSV fails to download, its error is logged in `source_files` and the service continues with other indices. If **all** indices fail, `status = "FAILED"`. A partial failure (some indices OK) gives `status = "PARTIAL_SUCCESS"`. The DB is never left half-updated — failed indices simply don't change their current data.

---

## Changes on 2026-10-05 (after the merge into Fundamental screener)

- The file now lives at `backend/app/technical/services/nifty_index_ingestion_service.py`.
- **File names corrected.** NSE had renamed most sector and strategy constituent files (for example `ind_niftybank_list.csv` is now `ind_niftybanklist.csv`). With the old names the site returned an HTML page instead of a CSV, so those indices silently loaded zero constituents. 19 names in `_INITIAL_INDICES` were corrected.
- **`seed_catalog()` now repairs URLs.** If an index is already in the catalog but its stored `source_url` differs from the one in `_INITIAL_INDICES`, the stored URL is updated. Before, a row seeded with a stale name kept it forever.
- **Six benchmark indices added** (Consumer Durables, Chemicals, Capital Markets, Infrastructure, India Consumption, Transportation & Logistics) because `backend/app/prices/benchmarks.py` measures stocks against them.
- Still without a working file: `nifty-100-esg` and `nifty-high-beta-50`.
