# backend/app/services/nifty_refresh_service.py — Beginner Explanation

> **Source file:** `backend/app/services/nifty_refresh_service.py`

---

## 1. What is this file?

Keeps the Nifty universe data accurate and up-to-date by downloading the **official NSE index CSV files** from niftyindices.com and synchronising the database.

Previously the DB was seeded once from a static JSON file. That file could go stale as NSE rebalances its indices quarterly. This service replaces that with live data from the source.

---

## 2. What it fixes

Before this service:
- `NIFTY_TOTAL_MARKET` had only 488 stocks (same as Nifty 500 — copy/paste from seed file)
- Micro-cap stocks (e.g. SILGO, OBCL < 300 Cr market cap) were appearing in Nifty 500 scans
- Market cap categories were incorrectly assigned

After first refresh:
- `NIFTY_50`: 50 stocks (exact)
- `NIFTY_500`: 500 stocks (exact) — LARGE + MID + SMALL only
- `NIFTY_TOTAL_MARKET`: 752 stocks — full real index

---

## 3. Market cap classification (follows SEBI rules)

| Source CSV | Cap Category | SEBI Rule |
|---|---|---|
| Nifty 50 | LARGE_CAP | Ranks 1–50 |
| Nifty Next 50 | LARGE_CAP | Ranks 51–100 |
| Nifty Midcap 150 | MID_CAP | Ranks 101–250 |
| Nifty Smallcap 250 | SMALL_CAP | Ranks 251–500 |
| Total Market (remainder) | MICRO_CAP | Ranks 500+ |

CSVs are processed in that order — **first assignment wins**. A stock in both Nifty 50 and Total Market gets LARGE_CAP (from Nifty 50, processed first), not MICRO_CAP.

---

## 4. CSV format from niftyindices.com

```
Company Name,Industry,Symbol,Series,ISIN Code
HDFC Bank Limited,Financial Services,HDFCBANK,EQ,INE040A01034
```

Only `Symbol`, `ISIN Code`, `Company Name`, and `Industry` columns are used. The `Series` column (EQ = equity) is not filtered — NSE only lists EQ shares in index CSVs.

---

## 5. How the refresh works

```python
def refresh(force=False):
    # 1. Check staleness — skip if < 90 days old (unless force=True)
    # 2. Fetch all 5 CSVs in sequence, build {isin: StockRecord} dict
    # 3. Upsert universe rows (ensure NIFTY_50/500/TOTAL_MARKET exist)
    # 4. Upsert stock rows (symbol, ISIN, company name, cap category)
    # 5. DELETE all memberships for the 3 managed universes
    # 6. INSERT fresh memberships from the fetched data
    # 7. UPDATE stock_count + last_synced_at on each universe
    # 8. Commit
```

Step 5 (delete-all, re-insert) is simpler and safer than trying to diff old vs new memberships. Since rebalancing moves stocks between indices, a full replacement is the only accurate approach.

---

## 6. Staleness guard

```python
_STALE_DAYS = 90  # NSE rebalances indices quarterly

if not force and age_days < _STALE_DAYS:
    return {"skipped": True, "reason": "Data is fresh"}
```

NSE typically rebalances Nifty indices in March and September. The 90-day guard prevents accidental double-refreshes while still ensuring the refresh runs at least once per rebalance cycle.

---

## 7. How to run

```bash
# Manual refresh (skips if data is < 90 days old)
make refresh-universes

# Force refresh regardless of age
make refresh-universes FORCE=true

# Or directly via API
curl -X POST "http://localhost:3001/admin/universes/refresh?force=true"

# Check staleness
curl "http://localhost:3001/admin/universes/status"
```

---

## 8. Error handling

If one CSV fetch fails (e.g. niftyindices.com temporarily unavailable), the error is recorded in `fetch_errors` but the service continues with the other CSVs. If **all** CSVs fail, the service raises `RuntimeError` and the DB is not modified (transaction rolls back).
