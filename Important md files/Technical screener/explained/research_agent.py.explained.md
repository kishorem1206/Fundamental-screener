# backend/app/agents/research_agent.py — Beginner Explanation

> **Source file:** `backend/app/agents/research_agent.py`

---

## 1. What is this file?

Defines `ResearchAgent` — a **stub** placeholder for Phase 9 functionality (news sentiment, FII/DII flows, analyst ratings). It currently returns a structured `PARTIAL` response so that any caller already wired to this agent interface can handle it gracefully.

---

## 2. Task type: `RESEARCH_STOCK`

**Payload:** `{"symbol": "INFY"}`

**Result (status = PARTIAL):**
```json
{
  "symbol": "INFY",
  "status": "stub",
  "message": "ResearchAgent is a stub — full implementation arrives in Phase 9",
  "available_in": "Phase 9"
}
```

---

## 3. Why `PARTIAL` not `FAILED`?

`PARTIAL` signals "the agent ran but returned incomplete data" — appropriate for a stub that intentionally returns less than it will eventually return. `FAILED` would suggest something went wrong, which is misleading.

---

## 4. What Phase 9 will add

- News headlines and sentiment from news MCP
- FII/DII institutional flow data
- Analyst target prices and ratings
- Promoter holding changes
