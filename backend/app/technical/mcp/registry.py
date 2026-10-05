from app.technical.mcp.types import MCPProviderHealth
from app.technical.mcp.adapters.kite import KiteMCPAdapter
from app.technical.mcp.adapters.tradingview import TradingViewMCPAdapter
from app.technical.mcp.adapters.indmoney import INDMoneyMCPAdapter


class MCPRegistry:
    def __init__(self) -> None:
        self._adapters: dict = {
            "KITE_MCP": KiteMCPAdapter(),
            "TRADINGVIEW_MCP": TradingViewMCPAdapter(),
            "INDMONEY_MCP": INDMoneyMCPAdapter(),
        }

    def get_adapter(self, provider_id: str):
        adapter = self._adapters.get(provider_id)
        if adapter is None:
            raise ValueError(f"No adapter registered for {provider_id}")
        return adapter

    def health_all(self) -> list[MCPProviderHealth]:
        return [adapter.health() for adapter in self._adapters.values()]


mcp_registry = MCPRegistry()
