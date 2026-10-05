# backend/app/shared/types.py — Beginner Explanation

> **Source file:** `backend/app/shared/types.py`

---

## 1. What is this file?

Defines Python `Literal` types — string constants that the type checker enforces. These replace TypeScript's union types and enums.

---

## 2. TypeScript → Python type equivalents

| TypeScript | Python |
|-----------|--------|
| `type Status = "ok" \| "error"` | `Status = Literal["ok", "error"]` |
| `enum FilterResult { PASS = "PASS", ... }` | `FilterResult = Literal["PASS", "FAIL", "SKIP", "ERROR"]` |
| `type Exchange = "NSE" \| "BSE"` | `Exchange = Literal["NSE", "BSE"]` |

---

## 3. What are `Literal` types?

```python
from typing import Literal

FilterResult = Literal["PASS", "FAIL", "SKIP", "ERROR"]
```

This is a **type alias** — `FilterResult` is now a name for the type `Literal["PASS", "FAIL", "SKIP", "ERROR"]`. You can use it in function signatures:

```python
def evaluate_screen(result: FilterResult) -> bool:
    return result == "PASS"
```

At runtime, Python doesn't enforce this — any string would work. But **mypy** (the Python type checker) will flag `evaluate_screen("invalid")` as an error.

---

## 4. The types defined

| Type alias | Valid values | Used for |
|-----------|-------------|---------|
| `FilterResult` | PASS, FAIL, SKIP, ERROR | Screen evaluation results |
| `Timeframe` | 1m, 5m, 15m, 1h, 4h, 1d, 1w | Chart timeframes |
| `Exchange` | NSE, BSE | Stock exchanges |
| `MarketCapCategory` | LARGE_CAP, MID_CAP, SMALL_CAP, MICRO_CAP, NANO_CAP | Size categories |
| `MCPProviderId` | kite, tradingview, indmoney | MCP provider names |
| `MCPCapabilityStatus` | AVAILABLE, UNAVAILABLE, UNKNOWN | MCP health status |
| `TaskPriority` | HIGH, NORMAL, LOW | Agent task scheduling |
| `TaskStatus` | SUCCESS, PARTIAL, FAILED, UNKNOWN | Agent task results |
| `LLMProviderId` | gpt_oss | LLM backend identifiers |
| `AgentId` | universe_agent, classification_agent, ... | Agent registry keys |

---

## 5. Usage in other files

```python
from app.shared.types import Exchange, MarketCapCategory

class StockListFilters:
    market_cap_category: MarketCapCategory | None = None
```

When Pydantic sees `market_cap_category: Literal["LARGE_CAP", ...]`, it validates that the value must be one of those strings. This is why FastAPI automatically returns a 422 error when you pass an invalid `market_cap_category` as a query parameter.

---

## 6. Why not Python enums?

Python has built-in `Enum`:
```python
from enum import Enum
class Exchange(Enum):
    NSE = "NSE"
    BSE = "BSE"
```

We use `Literal` instead because:
1. Simpler — no `.value` property needed (`"NSE"` vs `Exchange.NSE.value`)
2. Works directly with Pydantic validation (Pydantic understands `Literal` natively)
3. More Pythonic for string constants
4. Closer to the TypeScript union type pattern we're migrating from
