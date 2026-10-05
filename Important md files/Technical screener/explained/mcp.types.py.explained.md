# backend/app/mcp/types.py — Beginner Explanation

> **Source file:** `backend/app/mcp/types.py`

---

## 1. What is this file?

Defines data structures and the `MCPAdapter` Protocol used by all MCP provider adapters.

---

## 2. `MCPProviderHealth` — health status dataclass

```python
@dataclass
class MCPProviderHealth:
    provider_id: str
    status: str  # "AVAILABLE" | "UNAVAILABLE" | "UNKNOWN"
    available_tools: list[str]
    blocked_tools: list[str]
    error: str | None = None
```

Returned by every adapter's `health()` method. The `/health` endpoint collects these and includes them in the response.

**`@dataclass`** — Auto-generates `__init__`, `__repr__`, `__eq__`. No need to write `def __init__(self, provider_id, status, ...): self.provider_id = provider_id...` manually.

---

## 3. `MCPQuoteResult` — market data result

```python
@dataclass
class MCPQuoteResult:
    symbol: str
    exchange: str
    last_price: float | None
    open_price: float | None
    high_price: float | None
    low_price: float | None
    close_price: float | None
    volume: int | None
    timestamp: str | None
```

A standardized format for market quote data — regardless of which MCP provider returned it (Kite, TradingView, INDMoney), the data is normalized to this structure.

---

## 4. `MCPAdapter` Protocol

```python
class MCPAdapter(Protocol):
    provider_id: str

    def health(self) -> MCPProviderHealth: ...
    def is_tool_blocked(self, tool_name: str) -> bool: ...
```

**`Protocol`** — Python's equivalent of TypeScript interfaces. Any class that has `provider_id`, `health()`, and `is_tool_blocked()` attributes automatically satisfies the protocol — no explicit `implements` needed.

This is called **structural typing** (duck typing with type checking). If it has `health()` and `is_tool_blocked()`, it's an `MCPAdapter`.

**`def health(self) -> MCPProviderHealth: ...`** — The `...` (Ellipsis) means "no implementation here — this is just the signature". Like TypeScript's `health(): MCPProviderHealth;` in an interface.

---

## 5. How adapters use these types

```python
# In kite.py:
class KiteMCPAdapter:          # No explicit "implements MCPAdapter"
    provider_id = "kite"       # Has the required attribute

    def health(self) -> MCPProviderHealth:    # Has the required method
        return MCPProviderHealth(...)

    def is_tool_blocked(self, tool_name: str) -> bool:  # Has the required method
        return tool_name in BLOCKED_V1_TOOLS
```

Python's type checker verifies that `KiteMCPAdapter` satisfies `MCPAdapter` wherever the `MCPAdapter` type is used in annotations.

---

## 6. TypeScript comparison

```typescript
// TypeScript interface (was):
interface MCPAdapter {
    providerId: string;
    health(): MCPProviderHealth;
    isToolBlocked(toolName: string): boolean;
}

class KiteMCPAdapter implements MCPAdapter { ... }
```

```python
# Python Protocol (now):
class MCPAdapter(Protocol):
    provider_id: str
    def health(self) -> MCPProviderHealth: ...
    def is_tool_blocked(self, tool_name: str) -> bool: ...

class KiteMCPAdapter:  # No "implements" needed
    provider_id = "kite"
    def health(self) -> MCPProviderHealth: ...
    def is_tool_blocked(self, tool_name: str) -> bool: ...
```
