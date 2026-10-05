# backend/app/services/stock_index_classification_service.py — Beginner Explanation

> **Source file:** `backend/app/services/stock_index_classification_service.py`

---

## 1. What is this file?

Answers classification questions by querying PostgreSQL directly:

- Which Nifty indices does AUBANK currently belong to?
- Which stocks are in Nifty Bank?
- What Nifty indices did AUBANK belong to on 2026-03-01? (historical)
- Which stocks are common between Nifty Bank and Nifty Financial Services?

**This service never scrapes a website.** It only reads from `index_constituents`.

---

## 2. Methods

### `stock_indices(symbol, as_of=None, category=None)`

```sql
SELECT ni.index_name, ic2.name AS cat_name, ic.weight
FROM index_constituents ic
JOIN nifty_indices ni ON ni.id = ic.index_id
JOIN index_categories ic2 ON ic2.id = ni.category_id
JOIN stocks s ON s.id = ic.stock_id
WHERE s.symbol = 'AUBANK'
  AND ic.effective_from <= :as_of
  AND (ic.effective_to IS NULL OR ic.effective_to >= :as_of)
```

`as_of=None` → today → current membership.
`as_of=<date>` → membership on that specific date.

The result is grouped by category:

```json
{
  "symbol": "AUBANK",
  "indices": {
    "broad-market": [{"name": "Nifty 500"}],
    "sectoral": [{"name": "Nifty Bank"}, {"name": "Nifty Private Bank"}]
  }
}
```

---

### `index_constituents(index_code, as_of=None)`

Returns all stocks in a given index. `index_code` is the slug like `"nifty-bank"` or `"nifty-50"`.

---

### `list_indices(category=None)`

Returns all known indices from the `nifty_indices` table. Pass `category="SECTORAL"` to filter.

---

### `index_intersection(index_a, index_b)`

Computes which stocks appear in both indices at the same time using Python set intersection on the fetched stock IDs. This is a precise DB-backed query — the LLM never guesses.

---

## 3. Historical queries

The `effective_from` / `effective_to` columns in `index_constituents` record the membership period:

```
effective_to IS NULL      → currently a member
effective_to = 2026-06-30 → was a member until June 30, 2026
```

Querying `WHERE effective_from <= '2026-03-01' AND (effective_to IS NULL OR effective_to >= '2026-03-01')` correctly returns membership active on that date.

---

## 4. Data freshness

Every response includes `data_as_of`: the `completed_at` timestamp of the most recent successful non-dry-run ingestion. If this is stale, the API caller knows to trigger a refresh.
