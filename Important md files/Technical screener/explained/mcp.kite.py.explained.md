# backend/app/mcp/adapters/kite.py — Beginner Explanation

> **Source file:** `backend/app/mcp/adapters/kite.py`

---

## 1. What is this file?

Defines `KiteMCPAdapter` — the integration point for Zerodha's Kite MCP server. It manages the list of available tools, enforces V1 write-blocking, and reports health status.

---

## 2. V1 security constraint

In Phase 1 (V1), the application is **strictly read-only**. No order placement or modification is allowed — not by the user, and not by the LLM.

```python
BLOCKED_V1_TOOLS: frozenset[str] = frozenset({
    "place_order",
    "modify_order",
    "cancel_order",
    "place_gtt_order",
    "modify_gtt_order",
    "delete_gtt_order",
})
```

**`frozenset`** — An immutable set. Faster for `in` membership checks than a list, and can't be accidentally modified.

Any code trying to call these tools will first call `is_tool_blocked(tool_name)` — if it returns `True`, the call is rejected with `MCPBlockedError`.

---

## 3. Available tools (read-only)

```python
AVAILABLE_V1_TOOLS: list[str] = [
    "get_holdings",
    "get_positions",
    "get_orders",
    "get_trades",
    "get_order_history",
    "get_order_trades",
    "get_margins",
    "get_ltp",
    "get_ohlc",
    "get_quotes",
    "get_historical_data",
    "get_profile",
    "get_gtts",
    "get_mf_holdings",
    "search_instruments",
    "login",
]
```

These are all read operations — fetching data, never modifying anything.

---

## 4. Line-by-line explanation

```python
class KiteMCPAdapter:
    provider_id = "kite"
```

Class-level attribute. The registry uses this as the key.

---

```python
    def is_tool_blocked(self, tool_name: str) -> bool:
        return tool_name in BLOCKED_V1_TOOLS
```

`in frozenset` is an O(1) hash lookup.

---

```python
    def health(self) -> MCPProviderHealth:
        return MCPProviderHealth(
            provider_id=self.provider_id,
            status="AVAILABLE",
            available_tools=AVAILABLE_V1_TOOLS,
            blocked_tools=list(BLOCKED_V1_TOOLS),
        )
```

Returns a health object that the MCP registry's `health_all()` collects. The `/health` endpoint includes this in its response, making the blocked tools visible to developers.

**Note**: Phase 1 always returns `"AVAILABLE"` — we're not actually connecting to Kite's MCP server yet (that's Phase 3). In Phase 3, this will check the actual MCP connection status.

---

## 5. Where blocked tool enforcement happens (Phase 3 preview)

When the LLM agent wants to call a Kite tool:
```python
adapter = mcp_registry.get("kite")
if adapter.is_tool_blocked(tool_name):
    raise MCPBlockedError(tool_name)
# else: proceed with the MCP call
```

The check happens in the agent, not in the route. This keeps the security enforcement close to where the action would occur.
