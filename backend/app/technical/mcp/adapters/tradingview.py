from datetime import datetime, timezone
from app.technical.mcp.types import MCPProviderHealth


class TradingViewMCPAdapter:
    provider_id = "TRADINGVIEW_MCP"

    def health(self) -> MCPProviderHealth:
        return MCPProviderHealth(
            provider_id="TRADINGVIEW_MCP",
            status="AVAILABLE",
            checked_at=datetime.now(timezone.utc).isoformat(),
        )
