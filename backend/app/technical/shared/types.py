from typing import Literal
from enum import Enum


FilterResult = Literal["PASS", "FAIL", "UNKNOWN"]

Timeframe = Literal[
    "1m", "3m", "5m", "10m", "15m", "30m",
    "1h", "4h", "1D", "1W", "1M",
]

Exchange = Literal["NSE", "BSE", "MCX", "NFO", "BFO"]

MarketCapCategory = Literal[
    "LARGE_CAP", "MID_CAP", "SMALL_CAP",
    "MICRO_CAP", "NANO_CAP", "CUSTOM",
]

MCPProviderId = Literal["KITE_MCP", "TRADINGVIEW_MCP", "INDMONEY_MCP"]

MCPCapabilityStatus = Literal["AVAILABLE", "UNAVAILABLE", "BLOCKED_V1", "DEGRADED"]

TaskPriority = Literal["HIGH", "NORMAL", "LOW"]

TaskStatus = Literal["PENDING", "IN_PROGRESS", "SUCCESS", "PARTIAL", "FAILED", "UNKNOWN"]

LLMProviderId = Literal["GPT_OSS", "CLAUDE", "OPENAI", "OLLAMA"]

AgentId = Literal[
    "OrchestratorAgent",
    "LLMChatAgent",
    "UniverseAgent",
    "MarketDataAgent",
    "IndicatorAgent",
    "ClassificationAgent",
    "FundamentalAgent",
    "FilterAgent",
    "ScoringAgent",
    "RankingAgent",
    "ExplanationAgent",
    "ResearchAgent",
    "CandlestickAgent",
    "StrategyAgent",
    "RiskAgent",
]
