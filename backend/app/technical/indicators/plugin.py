from dataclasses import dataclass, field
from typing import Protocol, Any


@dataclass
class OHLCVBar:
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class IndicatorResult:
    name: str
    params: dict[str, Any]
    values: dict[str, Any]
    signal: str  # OVERSOLD | OVERBOUGHT | NEAR_LOWER | NEAR_UPPER | NEUTRAL | UNKNOWN


@dataclass
class DataProvenanceItem:
    source: str
    symbol: str
    timeframe: str
    bars_used: int
    data_range: str


class IndicatorPlugin(Protocol):
    name: str
    default_params: dict[str, Any]

    def calculate(self, bars: list[OHLCVBar], params: dict[str, Any]) -> IndicatorResult: ...


@dataclass
class TechnicalSnapshot:
    symbol: str
    exchange: str
    timeframe: str
    requested_at: str
    data_date: str
    last_price: float | None
    indicators: dict[str, dict]
    provenance: list[DataProvenanceItem] = field(default_factory=list)
