from typing import Protocol
from dataclasses import dataclass


@dataclass
class MCPProviderHealth:
    provider_id: str
    status: str                         # AVAILABLE | UNAVAILABLE | BLOCKED_V1 | DEGRADED
    checked_at: str
    detail: str | None = None


@dataclass
class MCPQuoteResult:
    symbol: str
    exchange: str
    last_price: float
    open: float | None
    high: float | None
    low: float | None
    close: float | None
    volume: float | None
    timestamp: str
    provider_raw: object = None


class MCPAdapter(Protocol):
    provider_id: str

    def health(self) -> MCPProviderHealth: ...
