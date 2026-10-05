# backend/app/agents/nifty_index_agent.py — Beginner Explanation

> **Source file:** `backend/app/agents/nifty_index_agent.py`

---

## 1. What is this file?

An agent that acts as the interface between routes/LLM and the Nifty index data system. It follows the standard project agent pattern:

```python
class NiftyIndexAgent:
    agent_id = "NiftyIndexAgent"
    task_types = ["NIFTY_INGEST", "NIFTY_STOCK_INDICES", ...]

    def handle(self, task: AgentTask) -> AgentResult:
        ...

nifty_index_agent = NiftyIndexAgent()  # module-level singleton
```

---

## 2. Registered in main.py

```python
agent_registry.register(nifty_index_agent)
```

Routes dispatch to it via `AgentTask(to_agent="NiftyIndexAgent", ...)`.

---

## 3. Task types

| Task type | What it does |
|---|---|
| `NIFTY_SEED_CATALOG` | Seed index_categories + nifty_indices rows (idempotent, run once after migration) |
| `NIFTY_INGEST` | Full ingestion — downloads CSVs, diffs, commits to DB |
| `NIFTY_DRY_RUN` | Same as NIFTY_INGEST but rolls back at end (preview-only) |
| `NIFTY_INGEST_STATUS` | Returns last ingestion_run status |
| `NIFTY_STOCK_INDICES` | Which indices does stock X belong to? (payload: `{symbol, as_of?, category?}`) |
| `NIFTY_INDEX_STOCKS` | Which stocks are in index Y? (payload: `{index_code, as_of?}`) |
| `NIFTY_LIST_INDICES` | List all known Nifty indices (payload: `{category?}`) |
| `NIFTY_INDEX_INTERSECTION` | Common stocks between two indices (payload: `{index_a, index_b}`) |

---

## 4. Guardrails

The agent delegates everything to `NiftyIndexIngestionService` and `StockIndexClassificationService`. Neither service invents data — they only read what is in `index_constituents`. The agent cannot hallucinate an index membership because it is structurally impossible for it to do so.

---

## 5. API surface

Admin routes (ingestion management):
```
POST /admin/nifty/seed
POST /admin/nifty/ingest?dry_run=false
POST /admin/nifty/ingest?dry_run=true
GET  /admin/nifty/ingestion/status
```

Public classification routes:
```
GET /nifty/indices
GET /nifty/indices/{index_code}/constituents
GET /nifty/stocks/{symbol}/indices
GET /nifty/indices/{index_a}/intersection/{index_b}
```

Historical lookup example:
```
GET /nifty/stocks/AUBANK/indices?as_of=2026-03-01
```
