from datetime import datetime, timezone
from app.technical.mcp.types import MCPProviderHealth


class INDMoneyMCPAdapter:
    provider_id = "INDMONEY_MCP"

    def health(self) -> MCPProviderHealth:
        return MCPProviderHealth(
            provider_id="INDMONEY_MCP",
            status="AVAILABLE",
            checked_at=datetime.now(timezone.utc).isoformat(),
        )
