# backend/app/mcp/registry.py — Beginner Explanation

> **Source file:** `backend/app/mcp/registry.py`

---

## 1. What is this file?

Manages all MCP (Model Context Protocol) provider adapters. Stores them in a dict and provides a `health_all()` method used by the `/health` endpoint.

Equivalent to TypeScript's `mcpRegistry.ts`.

---

## 2. What is MCP?

MCP (Model Context Protocol) is an open standard that lets LLMs call external tools. In this app:

- **Kite MCP** — gives the LLM access to Zerodha brokerage tools (portfolio, quotes, orders)
- **TradingView MCP** — gives the LLM access to chart data and technical indicators
- **INDMoney MCP** — gives the LLM access to the user's networth and mutual funds

Each MCP provider is accessed via a Python adapter class.

---

## 3. Line-by-line explanation

```python
class MCPRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, MCPAdapter] = {}
```

A dict from provider ID strings (like `"kite"`) to adapter instances.

---

```python
    def register(self, adapter: MCPAdapter) -> None:
        self._adapters[adapter.provider_id] = adapter
        logger.info("MCP adapter registered", provider_id=adapter.provider_id)
```

Stores the adapter by its `provider_id` string.

---

```python
    def get(self, provider_id: str) -> MCPAdapter | None:
        return self._adapters.get(provider_id)
```

Returns the adapter for a given provider, or `None` if not registered.

---

```python
    def health_all(self) -> list[MCPProviderHealth]:
        results = []
        for adapter in self._adapters.values():
            try:
                health = adapter.health()
                results.append(health)
            except Exception as e:
                results.append(MCPProviderHealth(
                    provider_id=adapter.provider_id,
                    status="UNAVAILABLE",
                    available_tools=[],
                    blocked_tools=[],
                    error=str(e),
                ))
        return results
```

Calls `health()` on each registered adapter. If any adapter's health check throws, we catch the exception and return an UNAVAILABLE status instead of crashing the whole health endpoint.

---

```python
mcp_registry = MCPRegistry()
mcp_registry.register(KiteMCPAdapter())
mcp_registry.register(TradingViewMCPAdapter())
mcp_registry.register(INDMoneyMCPAdapter())
```

The registry is populated at module load time, not in `lifespan`. This is OK because the adapters don't open network connections — they just define the interface. Actual MCP connections happen when tools are called.

---

## 4. V1 security constraint

The Kite adapter has a set of blocked tools that must never be called in V1 (read-only phase):

```python
BLOCKED_V1_TOOLS = {
    "place_order", "modify_order", "cancel_order",
    "place_gtt_order", "modify_gtt_order", "delete_gtt_order"
}
```

These appear in the health response's `blocked_tools` list so the `/health` endpoint makes the restriction visible. In Phase 3, the LLM orchestrator will check `adapter.is_tool_blocked(tool_name)` before calling any Kite tool.
