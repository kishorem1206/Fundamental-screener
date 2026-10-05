from datetime import datetime, timezone
from app.technical.mcp.types import MCPProviderHealth

# V1 blocked tools — order execution is read-only in V1
BLOCKED_V1_TOOLS: set[str] = {
    "place_order",
    "modify_order",
    "cancel_order",
    "place_gtt_order",
    "modify_gtt_order",
    "delete_gtt_order",
}


class KiteMCPAdapter:
    provider_id = "KITE_MCP"

    def is_tool_blocked(self, tool_name: str) -> bool:
        return tool_name in BLOCKED_V1_TOOLS

    def health(self) -> MCPProviderHealth:
        return MCPProviderHealth(
            provider_id="KITE_MCP",
            status="AVAILABLE",
            checked_at=datetime.now(timezone.utc).isoformat(),
        )
