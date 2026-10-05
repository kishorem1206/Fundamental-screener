# Indian Stock Screener — Agentic Architecture & Claude Code Specification

## Project Objective

Build a production-quality Indian stock market screening and analysis platform in VS Code.

The platform must use an **agent-oriented architecture**, a configurable **LLM chat interface**, multiple independent **MCP servers**, deterministic financial-analysis engines, and an extensible screening DSL.

The primary market universe for V1 is:

> **Nifty Total Market — approximately 750 stocks**

The architecture must also support additional NSE universes and custom universes without changing the core screening engine.

This is NOT intended to be a simple RSI/Bollinger screener.

It must become the foundation for an extensible Indian market-analysis platform supporting:

* Technical indicators
* Fundamental analysis
* Candlestick patterns
* Market-cap classifications
* Sector/industry classification
* Multi-timeframe analysis
* Natural-language screening
* AI chat
* Strategies
* Scoring
* Ranking
* Alerts
* Backtesting
* Future MCP providers
* Future AI agents
* Future autonomous research workflows

V1 is strictly **read-only**.

No automatic order execution.

---

# 1. High-Level Architecture

```text
                         ┌──────────────────────────────┐
                         │          WEB UI              │
                         │                              │
                         │ Dashboard                    │
                         │ Screener                     │
                         │ Stock Details                │
                         │ Charts                       │
                         │ Strategy Builder             │
                         │ AI Chat                      │
                         │ Saved Screens                │
                         └───────────────┬──────────────┘
                                         │
                                         ▼
                         ┌──────────────────────────────┐
                         │       API / GATEWAY          │
                         │                              │
                         │ REST / WebSocket / SSE       │
                         │ Authentication               │
                         │ Request Validation           │
                         └───────────────┬──────────────┘
                                         │
                                         ▼
                 ┌───────────────────────────────────────────────┐
                 │              AGENT ORCHESTRATOR               │
                 │                                               │
                 │ Query Planner                                  │
                 │ Task Planner                                   │
                 │ Agent Router                                   │
                 │ A2A Message Manager                            │
                 │ Result Aggregator                              │
                 │ Validation                                     │
                 │ Context Manager                                │
                 └───────────────┬───────────────────────────────┘
                                 │
          ┌──────────────────────┼─────────────────────────┐
          │                      │                         │
          ▼                      ▼                         ▼
 ┌────────────────┐     ┌──────────────────┐     ┌──────────────────┐
 │ LLM CHAT AGENT │     │ SCREENING AGENT  │     │ RESEARCH AGENT  │
 │                │     │                  │     │                  │
 │ GPT-OSS 20B    │     │ Query → DSL      │     │ Deep analysis    │
 │ Natural Lang.  │     │ Filter planning  │     │ Multi-source     │
 │ Conversation   │     │ Screen execution  │     │ reasoning        │
 └───────┬────────┘     └────────┬─────────┘     └────────┬─────────┘
         │                       │                        │
         └───────────────────────┼────────────────────────┘
                                 │
                                 ▼
              ┌────────────────────────────────────────┐
              │          SPECIALIZED AGENTS             │
              │                                        │
              │ Universe Agent                         │
              │ Market Data Agent                     │
              │ Indicator Agent                       │
              │ Classification Agent                  │
              │ Fundamental Agent                     │
              │ Candlestick Agent                     │
              │ Strategy Agent                         │
              │ Scoring Agent                          │
              │ Risk/Quality Agent                     │
              │ Explanation Agent                      │
              └───────────────────┬────────────────────┘
                                  │
                                  ▼
              ┌────────────────────────────────────────┐
              │       DETERMINISTIC ENGINES            │
              │                                        │
              │ Screening DSL Engine                  │
              │ Indicator Engine                      │
              │ Filter Engine                         │
              │ Ranking Engine                        │
              │ Scoring Engine                        │
              │ Pattern Engine                        │
              │ Data Validation Engine                │
              └───────────────────┬────────────────────┘
                                  │
                                  ▼
              ┌────────────────────────────────────────┐
              │            MCP PROVIDER LAYER          │
              │                                        │
              │ MCP Registry                           │
              │ MCP Router                             │
              │ Provider Adapters                      │
              │ Provider Health                        │
              │ Response Normalization                │
              └───────────────────┬────────────────────┘
                                  │
              ┌───────────────────┼─────────────────────┐
              │                   │                     │
              ▼                   ▼                     ▼
       ┌─────────────┐    ┌──────────────┐     ┌───────────────┐
       │  Kite MCP   │    │ TradingView  │     │ Future MCPs   │
       │             │    │ MCP          │     │               │
       │ Market data │    │ Indicators   │     │ News          │
       │ OHLC        │    │ Technical    │     │ Fundamentals  │
       │ Quotes      │    │ Charts       │     │ FII/DII       │
       └─────────────┘    └──────────────┘     │ etc.          │
                                                └───────────────┘

                         ┌──────────────────────────────┐
                         │       DATA PLATFORM          │
                         │                              │
                         │ PostgreSQL                   │
                         │ Redis                        │
                         │ Historical Data              │
                         │ Indicator Snapshots          │
                         │ Screen Results               │
                         │ Agent Memory/State           │
                         └──────────────────────────────┘
```

---

# 2. Core Architectural Principle

The most important rule in the entire system:

> **LLMs reason. Deterministic software calculates, validates, filters and stores.**

Do NOT allow an LLM to manually calculate financial indicators for hundreds of stocks.

For example:

```text
WRONG

GPT
 ↓
"Calculate RSI for 750 stocks"
 ↓
LLM arithmetic
```

Instead:

```text
CORRECT

User
 ↓
LLM
 ↓
Understand request
 ↓
Create Screening DSL
 ↓
Orchestrator
 ↓
Indicator Agent
 ↓
TradingView MCP / Market Data MCP
 ↓
Normalized indicator data
 ↓
Deterministic Filter Engine
 ↓
Results
 ↓
LLM explains results
```

---

# 3. Default Stock Universe

V1 must use:

## Nifty Total Market

Approximately 750 stocks.

This is the default universe.

Do NOT limit V1 to:

* Nifty 50
* Nifty 100
* Nifty 200
* Nifty 500

Those should be additional optional universes.

The architecture must support:

```text
NIFTY_TOTAL_MARKET
NIFTY_50
NIFTY_NEXT_50
NIFTY_100
NIFTY_200
NIFTY_500
NIFTY_MIDCAP_50
NIFTY_MIDCAP_100
NIFTY_MIDCAP_150
NIFTY_SMALLCAP_50
NIFTY_SMALLCAP_100
NIFTY_SMALLCAP_250
NIFTY_SMALLCAP_500
NIFTY_MICROCAP_250
CUSTOM
```

The universe system must be configurable.

Do not hard-code the stock list into frontend code.

---

# 4. Universe Dimensions

Universe membership and classification are different concepts.

A stock can simultaneously have:

```text
Universe:
NIFTY_TOTAL_MARKET
NIFTY_500
NIFTY_200
NIFTY_100
NIFTY_50

Market Cap:
LARGE_CAP

Sector:
IT

Industry:
Software

Basic Industry:
IT Services
```

These must be independent fields.

---

# 5. Market-Cap Classification

Support:

```text
LARGE_CAP
MID_CAP
SMALL_CAP
MICRO_CAP
NANO_CAP
CUSTOM
```

Also support direct market-cap filters:

```text
marketCap > ₹50,000 crore

marketCap between ₹10,000 crore and ₹50,000 crore

marketCap < ₹5,000 crore
```

Do not assume market-cap categories and Nifty indices are interchangeable.

Store source classification separately from application-defined classification.

Example:

```json
{
  "marketCap": 1250000000000,
  "sourceClassification": {
    "source": "SEBI_AMFI",
    "category": "LARGE_CAP"
  },
  "applicationClassification": {
    "category": "CUSTOM_LARGE"
  }
}
```

---

# 6. Sector Hierarchy

Support:

```text
Macro Sector
    ↓
Sector
    ↓
Industry
    ↓
Basic Industry
```

Example:

```text
Macro Sector: Financial Services
Sector: Financial Services
Industry: Banks
Basic Industry: Private Sector Banks
```

Users must be able to filter at any level.

Example:

```text
Sector = IT

Industry = Software

Basic Industry = IT Services
```

Support:

```text
sector IN ["IT", "Healthcare", "Consumer"]
```

The taxonomy must be updateable independently from application code.

---

# 7. LLM Architecture

The system must contain a dedicated LLM layer.

Initial model:

> GPT-OSS 20B

The LLM should be configurable.

Do NOT hard-code GPT-OSS 20B throughout the code.

Create:

```text
LLMProvider
```

Interface.

Example:

```typescript
interface LLMProvider {

    chat(request: LLMChatRequest): Promise<LLMChatResponse>;

    structuredOutput<T>(
        request: LLMStructuredRequest<T>
    ): Promise<T>;

    stream(
        request: LLMChatRequest
    ): AsyncIterable<LLMToken>;

}
```

Implement:

```text
GPTOSSProvider
```

Future providers can include:

```text
ClaudeProvider
OpenAIProvider
GeminiProvider
LocalLLMProvider
OllamaProvider
vLLMProvider
```

---

# 8. LLM Chat Agent

Create:

```text
LLMChatAgent
```

Responsibilities:

* Natural-language conversation
* Understand stock screening requests
* Ask clarification questions
* Explain screen results
* Explain technical indicators
* Explain why stocks passed/failed
* Build screen definitions
* Modify existing screens
* Create strategies
* Explain strategies
* Navigate dashboard state
* Query specialized agents

The LLM must NOT directly access databases.

The LLM must NOT directly execute arbitrary SQL.

The LLM must NOT directly call arbitrary MCP tools.

The LLM should interact through controlled tools exposed by the Orchestrator.

---

# 9. Example AI Chat Interaction

User:

```text
Find stocks in the total market where RSI is below 35
and price is close to the lower Bollinger Band.
```

LLM:

```text
I understand the following screen:

Universe:
Nifty Total Market

RSI:
14-period
Daily
< 35

Bollinger Bands:
20-period
2 standard deviations
Daily
Price within 3% of lower band

Should I run this screen?
```

The system should then create a structured screen.

---

# 10. Chat Follow-Up Context

The chat must maintain context.

Example:

User:

```text
Find oversold stocks.
```

System:

```text
Do you mean RSI below 30, RSI below 35,
or another definition of oversold?
```

User:

```text
Use RSI below 35.
```

Then:

User:

```text
Only midcaps.
```

The system should modify the existing screen:

```text
Universe = NIFTY_TOTAL_MARKET
AND
MarketCapCategory = MID_CAP
AND
RSI(14, 1D) < 35
```

User:

```text
Also only IT and pharma.
```

Result:

```text
Universe = NIFTY_TOTAL_MARKET
AND
MarketCapCategory = MID_CAP
AND
Sector IN ["IT", "Pharma"]
AND
RSI(14, 1D) < 35
```

The chat is therefore a natural-language interface over the Screening DSL.

---

# 11. LLM Tool Architecture

The LLM should have a controlled toolset.

Example tools:

```text
search_stocks
get_stock
get_quote
get_historical_data
get_indicator
get_stock_classification
get_sector_data
get_universe
run_screen
get_screen_results
create_screen
modify_screen
save_screen
get_strategy
create_strategy
explain_stock
compare_stocks
```

These are APPLICATION TOOLS.

They are not raw MCP tools.

Architecture:

```text
GPT-OSS
   ↓
Application Tool
   ↓
Agent / Service
   ↓
MCP Provider
   ↓
MCP Server
```

This is important because it prevents the LLM from becoming tightly coupled to individual MCP implementations.

---

# 12. MCP Architecture

MCP servers must be treated as external infrastructure.

Create:

```text
MCPRegistry
MCPRouter
MCPProviderAdapter
MCPHealthMonitor
MCPResponseNormalizer
```

Example:

```text
MCPRegistry

KITE_MCP
TRADINGVIEW_MCP
NEWS_MCP
FUNDAMENTALS_MCP
FII_DII_MCP
FUTURE_MCP
```

Each MCP gets an adapter.

---

# 13. Kite MCP

Create:

```text
KiteMCPAdapter
```

Potential capabilities:

```text
quotes
LTP
OHLC
historical candles
volume
market data
```

The implementation must inspect the actual configured MCP tools.

Never invent tool names.

If a tool does not exist:

```text
Capability = UNAVAILABLE
```

Do not fake it.

---

# 14. TradingView MCP

Create:

```text
TradingViewMCPAdapter
```

Potential capabilities:

```text
RSI
Bollinger Bands
technical indicators
charts
technical snapshots
multi-timeframe analysis
```

Again:

> Inspect the actual MCP server and use the tools that really exist.

Do not assume a tool name.

---

# 15. Multiple MCP Servers

The system must allow multiple MCP servers.

Example:

```text
                     MCP ROUTER
                         │
        ┌────────────────┼─────────────────┐
        │                │                 │
        ▼                ▼                 ▼
    Kite MCP        TradingView MCP    Future MCP
        │                │                 │
    Market data       Technical         News
    OHLC              indicators        Fundamentals
    Quotes            Charts            FII/DII
```

The Orchestrator should decide which provider is appropriate.

---

# 16. MCP Capability Registry

Maintain capabilities.

Example:

```json
{
  "KITE_MCP": [
    "QUOTE",
    "OHLC",
    "HISTORICAL_CANDLES"
  ],
  "TRADINGVIEW_MCP": [
    "RSI",
    "BOLLINGER_BANDS",
    "TECHNICAL_ANALYSIS"
  ]
}
```

When a new MCP server is connected, it can register capabilities.

The Orchestrator should query capability information before planning tasks.

---

# 17. Provider Selection

Do not hard-code:

```text
RSI → TradingView
```

Instead:

```text
Capability:
RSI

Available providers:
TradingView MCP
Internal Indicator Engine

Preferred provider:
TradingView MCP
```

Provider selection should consider:

```text
capability
data freshness
provider health
latency
cost
accuracy
timeframe support
```

---

# 18. Provider Fallback

Example:

```text
TradingView MCP
       ↓
unavailable
       ↓
Internal Indicator Engine
       ↓
historical OHLC
       ↓
calculate RSI
```

If no valid provider exists:

```json
{
  "status": "UNAVAILABLE",
  "reason": "No provider supports RSI for requested timeframe"
}
```

Never fabricate.

---

# 19. Indicator Engine

Create a plugin architecture.

Every indicator implements:

```typescript
interface IndicatorPlugin {

    definition(): IndicatorDefinition;

    calculate(
        candles: OHLCV[],
        parameters: Record<string, unknown>
    ): IndicatorResult;

}
```

Initial indicators:

```text
RSI
Bollinger Bands
```

Future:

```text
SMA
EMA
MACD
ATR
ADX
Stochastic
CCI
MFI
OBV
VWAP
ROC
Williams %R
Ichimoku
Supertrend
```

Adding an indicator must not require modifying the Filter Engine.

---

# 20. RSI

Default:

```text
period = 14
```

Support:

```text
RSI < X
RSI <= X
RSI > X
RSI >= X
RSI BETWEEN X AND Y
RSI CROSSING ABOVE X
RSI CROSSING BELOW X
RSI RISING
RSI FALLING
RSI DIVERGENCE
```

Support multiple timeframes.

Example:

```text
RSI(14, 1D) < 35
```

and:

```text
RSI(14, 1W) > 45
```

Do not classify RSI below 30/35 as an automatic buy signal.

---

# 21. Bollinger Bands

Default:

```text
period = 20
standardDeviation = 2
```

Support:

```text
upper band
middle band
lower band
bandwidth
%B
distance from upper band
distance from lower band
band expansion
band contraction
squeeze
crossing
touching
near band
```

Example:

```text
price within 3% of lower Bollinger Band
```

Do not hard-code Bollinger parameters.

---

# 22. Technical Snapshot

Canonical schema:

```json
{
  "symbol": "RELIANCE",
  "timeframe": "1D",
  "timestamp": "...",
  "price": {
    "close": 0
  },
  "indicators": {
    "rsi": {
      "period": 14,
      "value": 32.4
    },
    "bollinger": {
      "period": 20,
      "stdDev": 2,
      "upper": 0,
      "middle": 0,
      "lower": 0,
      "bandwidth": 0,
      "percentB": 0
    }
  },
  "volume": {
    "value": 0
  },
  "provenance": []
}
```

---

# 23. Data Provenance

Every financial value must contain:

```text
source
provider
retrievedAt
calculatedAt
timeframe
parameters
dataVersion
```

Example:

```json
{
  "value": 32.4,
  "source": "TRADINGVIEW_MCP",
  "retrievedAt": "2026-08-21T15:30:00Z",
  "timeframe": "1D",
  "parameters": {
    "period": 14
  }
}
```

The dashboard must expose provenance.

---

# 24. Screening DSL

The Screening DSL is the central abstraction of the entire platform.

Everything must eventually become a Screening DSL query.

Natural language:

```text
Find midcap IT stocks with RSI below 35.
```

becomes:

```json
{
  "and": [
    {
      "field": "marketCap.category",
      "operator": "EQ",
      "value": "MID_CAP"
    },
    {
      "field": "sector",
      "operator": "EQ",
      "value": "IT"
    },
    {
      "field": "technical.rsi",
      "timeframe": "1D",
      "operator": "LT",
      "value": 35
    }
  ]
}
```

---

# 25. Screening DSL Requirements

Support:

```text
AND
OR
NOT
EQ
NE
GT
GTE
LT
LTE
BETWEEN
IN
NOT_IN
CONTAINS
CROSSED_ABOVE
CROSSED_BELOW
RISING
FALLING
NEAR
```

Nested expressions must be supported.

Example:

```json
{
  "and": [
    {
      "field": "technical.rsi",
      "operator": "LT",
      "value": 35
    },
    {
      "or": [
        {
          "field": "technical.bollinger.percentB",
          "operator": "LT",
          "value": 0.1
        },
        {
          "field": "technical.bollinger.bandwidth",
          "operator": "LT",
          "value": 5
        }
      ]
    }
  ]
}
```

---

# 26. PASS / FAIL / UNKNOWN

Every condition must return:

```text
PASS
FAIL
UNKNOWN
```

Example:

```text
RSI = null

Result = UNKNOWN
```

Do NOT convert missing data into:

```text
RSI = 0
```

The user should be able to choose how UNKNOWN values are treated.

---

# 27. Execution Planner

The Orchestrator must transform DSL into an execution plan.

Example:

```text
User query
   ↓
DSL
   ↓
Execution Planner
   ↓
Universe Task
   ↓
Classification Task
   ↓
Technical Data Task
   ↓
Filter Task
   ↓
Ranking Task
   ↓
Explanation Task
```

Independent tasks should execute in parallel.

---

# 28. Example Execution Plan

Query:

```text
Find Nifty Total Market midcaps where
daily RSI < 35 and price is within 3% of
lower Bollinger Band.
```

Execution:

```text
TASK 1
UniverseAgent
→ NIFTY_TOTAL_MARKET

TASK 2
ClassificationAgent
→ MID_CAP

TASK 3
IndicatorAgent
→ RSI(14, 1D)
→ Bollinger(20, 2, 1D)

TASK 4
FilterEngine
→ Apply conditions

TASK 5
RankingEngine
→ Rank candidates

TASK 6
ExplanationAgent
→ Explain results
```

---

# 29. Agent-to-Agent Protocol

All agents communicate using typed messages.

Task:

```json
{
  "taskId": "uuid",
  "correlationId": "uuid",
  "parentTaskId": null,
  "fromAgent": "OrchestratorAgent",
  "toAgent": "IndicatorAgent",
  "taskType": "GET_INDICATORS",
  "payload": {},
  "priority": "NORMAL",
  "createdAt": "...",
  "deadline": null
}
```

Response:

```json
{
  "taskId": "uuid",
  "correlationId": "uuid",
  "agent": "IndicatorAgent",
  "status": "SUCCESS",
  "data": {},
  "errors": [],
  "warnings": [],
  "provenance": []
}
```

---

# 30. Agent Registry

Create:

```text
AgentRegistry
```

Initial agents:

```text
OrchestratorAgent
LLMChatAgent
UniverseAgent
MarketDataAgent
IndicatorAgent
ClassificationAgent
FundamentalAgent
FilterAgent
StrategyAgent
CandlestickAgent
ScoringAgent
RiskAgent
ExplanationAgent
```

Agents should advertise capabilities.

---

# 31. Orchestrator

The Orchestrator is the brain of the application.

Responsibilities:

```text
interpret
plan
route
parallelize
validate
aggregate
recover
explain
```

It must NOT perform financial calculations itself.

It decides:

```text
Which agent?
Which MCP?
Which data?
Which timeframe?
Which sequence?
Which fallback?
```

---

# 32. Chat Agent vs Orchestrator

Do not merge these concepts.

## LLMChatAgent

Responsible for:

```text
conversation
natural language
intent
clarification
explanation
```

## OrchestratorAgent

Responsible for:

```text
execution
task planning
agent routing
MCP routing
validation
aggregation
```

Architecture:

```text
User
 ↓
LLMChatAgent
 ↓
Structured Intent
 ↓
OrchestratorAgent
 ↓
Specialized Agents
 ↓
Results
 ↓
LLMChatAgent
 ↓
Natural Language Response
```

---

# 33. Research Agent

Create a separate:

```text
ResearchAgent
```

This agent can eventually answer:

```text
Why is this stock appearing in my screen?

What changed?

Compare these stocks.

What technical factors agree?

What factors disagree?

What are the risks?

What is the sector doing?

```

It should consume structured data from other agents.

It should never invent missing financial information.

---

# 34. Explanation Agent

The ExplanationAgent converts structured results into human-readable explanations.

Example:

```text
RELIANCE passed the screen because:

✓ RSI(14) = 32.4
✓ RSI condition < 35
✓ Price is 2.1% above lower Bollinger Band
✓ Market-cap classification = Large Cap
✓ Universe = Nifty Total Market
✓ Sector = Energy

Warnings:

⚠ Volume is below 20-day average
⚠ Weekly RSI is still above 50
```

All statements must come from structured data.

---

# 35. Fundamental Agent

Prepare an agent for:

```text
market cap
PE
PB
ROE
ROCE
debt/equity
EPS growth
revenue growth
profit growth
dividend yield
promoter holding
FII holding
DII holding
free cash flow
```

The exact available metrics depend on connected MCP/data providers.

Missing metrics must remain UNKNOWN.

---

# 36. Candlestick Agent

Create plugin architecture for:

```text
Doji
Hammer
Inverted Hammer
Shooting Star
Bullish Engulfing
Bearish Engulfing
Morning Star
Evening Star
Harami
Piercing Line
Dark Cloud Cover
```

Example:

```json
{
  "pattern": "BULLISH_ENGULFING",
  "direction": "BULLISH",
  "timeframe": "1D",
  "timestamp": "...",
  "confidence": null
}
```

Do not present candlestick patterns as guaranteed predictions.

---

# 37. Strategy Agent

A strategy combines multiple conditions.

Example:

```text
Oversold Reversal

RSI(14) < 35
AND
Price near lower Bollinger Band
AND
Bullish Engulfing
AND
Volume > 20-day average
```

Strategies must be versioned.

```text
strategyId
strategyVersion
createdAt
updatedAt
definition
```

Never silently modify an existing strategy.

---

# 38. Scoring Engine

Create configurable scoring.

Example:

```text
RSI condition            +20
Bollinger condition      +20
Volume confirmation      +15
Trend confirmation       +20
Candlestick confirmation +15
Liquidity                 +10

TOTAL                    100
```

Weights must be configurable.

Scoring must remain separate from filtering.

---

# 39. Ranking Engine

Support:

```text
Score
RSI
Market Cap
Volume
Relative Volume
Bollinger %B
Distance from lower band
Distance from upper band
Price change
Custom score
```

Example:

```text
Filter first
    ↓
Rank second
```

Do not rank before applying hard filters.

---

# 40. Multi-Timeframe

Every technical condition must specify a timeframe where applicable.

Supported:

```text
1m
5m
15m
30m
1h
4h
1D
1W
1M
```

Example:

```text
Daily RSI < 35
AND
Weekly RSI > 45
AND
Daily price near lower Bollinger Band
```

---

# 41. Dashboard

Build a professional trading/research dashboard.

## Header

```text
Market Status
Data Status
Last Refresh
Search
AI Chat
```

## Universe

```text
Nifty Total Market
Nifty 50
Nifty Next 50
Nifty 100
Nifty 200
Nifty 500
Midcap
Smallcap
Microcap
Custom
```

## Filters

```text
Market Cap
Sector
Industry
Basic Industry
Price
Volume
RSI
Bollinger Bands
Future indicators
```

## Results

Columns:

```text
Symbol
Company
Price
Change %
Market Cap
Cap Category
Sector
Industry
Universe
RSI
BB Upper
BB Middle
BB Lower
%B
Bandwidth
Volume
Relative Volume
Signal
Score
Timestamp
```

Columns must be configurable.

---

# 42. AI Chat Panel

Add a persistent chat panel.

Example:

```text
┌──────────────────────────────────────────────┐
│ AI Stock Assistant                           │
├──────────────────────────────────────────────┤
│                                              │
│ User: Find oversold midcaps.                 │
│                                              │
│ AI: Should I use RSI < 30 or RSI < 35?       │
│                                              │
│ User: 35                                     │
│                                              │
│ AI: I found 47 matching stocks.              │
│                                              │
│     [View Results]                            │
│                                              │
├──────────────────────────────────────────────┤
│ Ask anything...                         Send │
└──────────────────────────────────────────────┘
```

The AI should be able to interact with the dashboard.

Example:

```text
"Add RSI below 35 to the current screen."

"Remove IT stocks."

"Sort by lowest RSI."

"Only show stocks above ₹10,000 crore market cap."

"Save this as Oversold Midcaps."

"Compare the top 10."

"Explain why ABC passed."
```

---

# 43. Chat Actions

Chat should be capable of controlled UI actions.

Examples:

```text
CREATE_SCREEN
MODIFY_SCREEN
RUN_SCREEN
SAVE_SCREEN
SORT_RESULTS
FILTER_RESULTS
OPEN_STOCK
COMPARE_STOCKS
OPEN_STRATEGY
CREATE_STRATEGY
```

These must be structured commands.

Never allow arbitrary frontend JavaScript from the LLM.

---

# 44. Saved Screens

Users should be able to save:

```text
screenId
name
description
DSL
universe
createdAt
updatedAt
owner
version
```

Example:

```text
Oversold Midcaps

NIFTY_TOTAL_MARKET
AND MID_CAP
AND RSI(14,1D) < 35
AND BB %B < 0.10
```

---

# 45. Stock Detail Page

For every stock show:

```text
Price
Chart
Volume
RSI
Bollinger Bands
Technical indicators
Fundamentals
Market cap
Sector
Industry
Basic industry
Index memberships
Candlestick patterns
Signals
Strategies
AI explanation
Data provenance
```

---

# 46. AI Stock Explanation

Example:

```text
Why is HDFCBANK in this screen?

Technical:
RSI(14) = 33.2
Lower Bollinger proximity = 1.4%

Classification:
Large Cap
Nifty Total Market
Nifty 50

Sector:
Financial Services

Volume:
0.82x 20-day average

Interpretation:
The stock satisfies the configured oversold conditions.

Caution:
Volume does not currently confirm the setup.
Weekly RSI remains neutral.
```

Do not say:

```text
BUY HDFCBANK
```

unless a future strategy/research system explicitly defines such output.

Even then, present it as analysis rather than certainty.

---

# 47. Performance

750 stocks should be handled efficiently.

Do NOT:

```text
for stock in stocks:
    await getIndicator(stock)
```

Sequentially.

Use:

```text
batching
concurrency limits
caching
deduplication
parallel agents
incremental refresh
```

Example:

```text
750 stocks
      ↓
Universe
      ↓
Filter cheap dimensions first
      ↓
Remaining candidates
      ↓
Technical data
      ↓
Final filtering
```

Where possible, apply inexpensive filters before expensive MCP calls.

---

# 48. Query Optimization

For:

```text
Market Cap > ₹20,000 crore
AND
Sector = IT
AND
RSI < 35
AND
Bollinger %B < 0.10
```

The planner should potentially execute:

```text
1. Universe
2. Market cap
3. Sector
4. Technical data only for remaining stocks
```

rather than requesting RSI/Bollinger for every stock.

This should be part of the Execution Planner.

---

# 49. Caching

Use Redis.

Cache:

```text
quotes
historical candles
technical indicators
fundamentals
universe membership
classification
```

Cache key:

```text
provider
symbol
timeframe
indicator
parameters
date
```

Example:

```text
TRADINGVIEW:RELIANCE:1D:RSI:14:2026-08-21
```

Every cached response must include:

```text
retrievedAt
expiresAt
source
```

---

# 50. Database

Use PostgreSQL.

Core tables:

```text
stocks
universes
universe_memberships
market_cap_snapshots
sector_classifications
industry_classifications
ohlcv
indicator_definitions
indicator_snapshots
fundamental_snapshots
screen_definitions
screen_runs
screen_results
strategies
strategy_versions
candlestick_signals
agent_tasks
agent_messages
chat_sessions
chat_messages
llm_requests
data_provenance
```

---

# 51. Chat Persistence

Store:

```text
chatSession
chatMessages
screenContext
activeScreen
userPreferences
toolCalls
```

Do NOT blindly send the entire chat history to the LLM forever.

Implement context management.

Summarize old conversation context when necessary.

---

# 52. LLM Cost/Performance

The LLM should not be called for every stock.

Bad:

```text
750 stocks
×
LLM call
```

Good:

```text
750 stocks
 ↓
deterministic filtering
 ↓
50 candidates
 ↓
optional ranking
 ↓
LLM explanation for selected results
```

LLM usage should be proportional to reasoning complexity, not stock count.

---

# 53. LLM Structured Output

Whenever the LLM needs to create a screen, use structured output.

Example:

```json
{
  "intent": "CREATE_SCREEN",
  "universe": "NIFTY_TOTAL_MARKET",
  "filters": {
    "and": [
      {
        "field": "technical.rsi",
        "timeframe": "1D",
        "operator": "LT",
        "value": 35
      }
    ]
  }
}
```

Validate this using Zod or equivalent schema validation.

Never execute unvalidated LLM output.

---

# 54. LLM Hallucination Protection

The LLM must follow:

```text
No data → say unavailable.

No source → don't claim source.

Conflicting providers → report conflict.

Unknown → don't invent.

Stale data → show stale status.

Missing MCP capability → say capability unavailable.
```

---

# 55. Observability

Every request must have:

```text
correlationId
```

Every agent task:

```text
taskId
```

Every MCP call:

```text
mcpRequestId
```

Every LLM call:

```text
llmRequestId
```

Track:

```text
latency
tokens
cost
provider
cache hit
cache miss
errors
retries
```

---

# 56. Security

Never expose:

```text
Kite credentials
MCP authentication
API keys
LLM credentials
database credentials
Redis credentials
```

to the browser.

Use environment variables.

Create:

```text
.env.example
```

Never commit:

```text
.env
credentials
tokens
secrets
```

---

# 57. Read-Only V1

The system must NOT place orders.

No:

```text
BUY
SELL
MODIFY ORDER
CANCEL ORDER
```

through the AI.

Kite MCP should initially be used as a market-data/information provider.

A future execution subsystem must be completely separate.

---

# 58. Future Trading Architecture

If trading is ever added, create a separate:

```text
ExecutionAgent
```

with:

```text
PermissionService
RiskLimits
OrderValidation
HumanConfirmation
AuditLog
```

The Orchestrator must never directly place an order.

---

# 59. Backtesting

Design for future backtesting.

Separate:

```text
LiveDataProvider
HistoricalDataProvider
```

Strategy:

```text
Strategy
 ↓
Historical Data
 ↓
Indicator Engine
 ↓
Strategy Engine
 ↓
Backtest Engine
 ↓
Performance Report
```

Backtesting must use point-in-time historical data to avoid look-ahead bias.

---

# 60. Future Features

The architecture must allow:

## Technical Indicators

```text
MACD
EMA
SMA
ATR
ADX
VWAP
MFI
OBV
Stochastic
CCI
Ichimoku
Supertrend
```

## Candlestick

```text
Doji
Hammer
Engulfing
Morning Star
Evening Star
Harami
Shooting Star
```

## Chart Patterns

```text
Double Top
Double Bottom
Head & Shoulders
Inverse Head & Shoulders
Triangle
Flag
Pennant
Cup & Handle
Breakout
```

## Fundamentals

```text
PE
PB
ROE
ROCE
Debt/Equity
EPS Growth
Revenue Growth
Profit Growth
Dividend Yield
Promoter Holding
FII
DII
Free Cash Flow
```

## Market Data

```text
FII/DII
Delivery
Open Interest
Options Chain
PCR
India VIX
Bulk Deals
Block Deals
Market Breadth
Advance/Decline
```

---

# 61. Future MCP Servers

The MCP architecture must allow:

```text
Kite MCP
TradingView MCP
News MCP
Fundamental Data MCP
NSE MCP
Economic Data MCP
FII/DII MCP
Options MCP
Research MCP
```

without changing the core application.

---

# 62. Recommended Project Structure

```text
stock-screener/

├── apps/
│   ├── web/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── features/
│   │   ├── hooks/
│   │   └── services/
│   │
│   └── api/
│       ├── routes/
│       ├── controllers/
│       └── middleware/
│
├── src/
│   ├── agents/
│   │   ├── orchestrator/
│   │   ├── llm-chat/
│   │   ├── research/
│   │   ├── universe/
│   │   ├── market-data/
│   │   ├── indicator/
│   │   ├── classification/
│   │   ├── fundamental/
│   │   ├── filter/
│   │   ├── strategy/
│   │   ├── candlestick/
│   │   ├── scoring/
│   │   ├── risk/
│   │   └── explanation/
│   │
│   ├── domain/
│   │   ├── stocks/
│   │   ├── universes/
│   │   ├── indicators/
│   │   ├── screening/
│   │   ├── strategies/
│   │   ├── fundamentals/
│   │   └── market/
│   │
│   ├── application/
│   │   ├── screening/
│   │   ├── orchestration/
│   │   ├── chat/
│   │   └── strategies/
│   │
│   ├── providers/
│   │   ├── llm/
│   │   │   ├── gpt-oss/
│   │   │   ├── claude/
│   │   │   └── openai/
│   │   │
│   │   └── mcp/
│   │       ├── registry/
│   │       ├── router/
│   │       ├── kite/
│   │       ├── tradingview/
│   │       └── future/
│   │
│   ├── engines/
│   │   ├── indicator/
│   │   ├── filter/
│   │   ├── screening/
│   │   ├── ranking/
│   │   ├── scoring/
│   │   └── pattern/
│   │
│   ├── infrastructure/
│   │   ├── database/
│   │   ├── redis/
│   │   ├── messaging/
│   │   ├── logging/
│   │   └── observability/
│   │
│   └── shared/
│       ├── types/
│       ├── schemas/
│       ├── errors/
│       └── utils/
│
├── database/
│   ├── migrations/
│   └── seeds/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── docs/
│   ├── architecture/
│   ├── agents/
│   ├── mcp/
│   ├── indicators/
│   ├── screening-dsl/
│   └── strategies/
│
├── .env.example
├── .gitignore
├── docker-compose.yml
├── package.json
└── README.md
```

---

# 63. Technology Stack

Prefer:

## Frontend

```text
React
TypeScript
Vite
Tailwind CSS
TanStack Table
TradingView Lightweight Charts or equivalent
```

## Backend

```text
Node.js
TypeScript
Fastify
```

## Database

```text
PostgreSQL
```

## Cache

```text
Redis
```

## Validation

```text
Zod
```

## Testing

```text
Vitest
Playwright
```

## LLM

Initial:

```text
GPT-OSS 20B
```

Through:

```text
LLMProvider
```

so that it can be replaced later.

---

# 64. Modular Monolith

Do NOT initially create dozens of microservices.

Use:

```text
Modular Monolith
```

with strict boundaries.

Example:

```text
Orchestrator Module
Indicator Module
Screening Module
MCP Module
LLM Module
Universe Module
Strategy Module
```

Each module should communicate through interfaces.

The architecture should later allow individual modules to become services.

---

# 65. Agent Communication

Initially implement an in-process message bus.

Example:

```text
AgentMessageBus
```

Later it can be replaced with:

```text
Redis Streams
Kafka
NATS
RabbitMQ
```

without changing agent contracts.

---

# 66. Agent Lifecycle

Every agent should implement:

```typescript
interface Agent {

    id(): string;

    capabilities(): AgentCapability[];

    execute(
        task: AgentTask
    ): Promise<AgentResult>;

}
```

Optional lifecycle:

```text
initialize()
healthCheck()
shutdown()
```

---

# 67. Agent Health

The system should expose:

```text
Agent Health
MCP Health
LLM Health
Database Health
Redis Health
```

Example:

```text
✓ Orchestrator
✓ Universe Agent
✓ Indicator Agent
✓ Kite MCP
✓ TradingView MCP
✓ PostgreSQL
✓ Redis
✓ GPT-OSS
```

---

# 68. Error Recovery

If:

```text
TradingView MCP fails
```

The Orchestrator should:

```text
detect failure
 ↓
check fallback provider
 ↓
use internal indicator engine if possible
 ↓
mark provenance
 ↓
continue
```

If impossible:

```text
UNKNOWN
```

not fake data.

---

# 69. Query Planning Example

User:

```text
Find small-cap pharma stocks with RSI below 30,
Bollinger %B below 0.05, volume above its 20-day average,
and a bullish engulfing candle.
```

Planner:

```text
Universe:
NIFTY_TOTAL_MARKET

Classification:
SMALL_CAP

Sector:
PHARMA

Technical:
RSI(14,1D) < 30
BB %B(20,2,1D) < 0.05
Volume > SMA(Volume,20)

Pattern:
Bullish Engulfing 1D
```

Execution graph:

```text
             Universe
                │
                ▼
        Classification
                │
                ▼
             Sector
                │
        ┌───────┴────────┐
        ▼                ▼
      RSI              BB
        │                │
        └───────┬────────┘
                ▼
             Volume
                │
                ▼
          Candlestick
                │
                ▼
          Filter Engine
                │
                ▼
          Ranking Engine
                │
                ▼
       Explanation Agent
                │
                ▼
             Results
```

Independent indicator tasks should run concurrently.

---

# 70. AI Chat Example

User:

```text
Show me oversold stocks.
```

AI:

```text
How would you like to define oversold?

1. RSI < 30
2. RSI < 35
3. RSI < 40
4. Custom
```

User:

```text
RSI below 35.
```

AI:

```text
Using:

Universe: Nifty Total Market
RSI(14): Daily
Condition: < 35

Would you like to add Bollinger Bands?
```

User:

```text
Yes. Within 3% of lower band.
```

AI:

```text
Added:

Bollinger Bands
20-period
2 standard deviations
Price within 3% of lower band

Run the screen?
```

---

# 71. AI Chat Tool Calls

The LLM should produce structured tool calls.

Example:

```json
{
  "tool": "create_screen",
  "arguments": {
    "name": "Oversold Bollinger",
    "dsl": {
      "and": [
        {
          "field": "technical.rsi",
          "timeframe": "1D",
          "operator": "LT",
          "value": 35
        },
        {
          "field": "technical.bollinger.distanceToLowerBand",
          "timeframe": "1D",
          "operator": "LTE",
          "value": 0.03
        }
      ]
    }
  }
}
```

The backend validates the arguments before execution.

---

# 72. AI Should Never Directly Execute MCP

Bad:

```text
GPT
 ↓
raw MCP tool
```

Good:

```text
GPT
 ↓
Application Tool
 ↓
Orchestrator
 ↓
Agent
 ↓
MCP Router
 ↓
MCP Adapter
 ↓
MCP Server
```

This provides:

```text
security
validation
logging
provider abstraction
fallback
observability
```

---

# 73. Future AI Agents

Prepare architecture for:

```text
NewsAgent
EarningsAgent
FundamentalResearchAgent
SectorResearchAgent
MarketRegimeAgent
PortfolioAgent
BacktestAgent
AlertAgent
AnomalyAgent
StrategyDiscoveryAgent
```

Do not implement all of them in V1.

The architecture simply needs to make them easy to add.

---

# 74. Market Regime Agent

Future capability:

```text
Bull
Bear
Sideways
High Volatility
Low Volatility
Risk-On
Risk-Off
```

It can eventually feed strategies.

Example:

```text
Only run mean-reversion strategy
when market regime = SIDEWAYS
```

---

# 75. Alert Agent

Future capability:

```text
RSI crosses below 35
Bollinger squeeze
Breakout
Volume spike
Bullish engulfing
Strategy signal
```

Alerts should be event driven.

---

# 76. Backtesting Rules

When backtesting is implemented:

Do NOT use future data.

For every historical timestamp:

```text
Available data at T
       ↓
Indicators calculated using data <= T
       ↓
Strategy evaluated
       ↓
Signal generated
```

No look-ahead bias.

---

# 77. Documentation Requirements

Claude Code must maintain:

```text
README.md

docs/architecture/overview.md
docs/architecture/agents.md
docs/architecture/mcp.md
docs/architecture/a2a.md
docs/screening-dsl/README.md
docs/indicators/README.md
docs/strategies/README.md
docs/development/setup.md
```

Every major architectural change must update documentation.

---

# 78. Development Workflow

Claude Code MUST NOT generate the entire project in one shot.

Use phases.

## Phase 0 — Inspect

Before coding:

```text
Inspect repository
Inspect package.json
Inspect MCP configuration
Inspect available MCP servers
Inspect actual MCP tools
Inspect existing frontend
Inspect existing backend
Inspect database
Inspect environment
```

Then produce:

```text
Architecture Assessment
```

Do not make large changes yet.

---

# 79. Phase 1 — Foundation

Implement:

```text
Project structure
TypeScript
API
Database
Redis
Environment configuration
Logging
Error handling
MCP registry
MCP adapters
LLM provider abstraction
```

No advanced screener yet.

---

# 80. Phase 2 — Universe

Implement:

```text
Nifty Total Market
Stock master
Index membership
Market cap
Sector
Industry
Basic Industry
```

Build the universe management UI.

---

# 81. Phase 3 — Indicators

Implement:

```text
RSI
Bollinger Bands
```

Create:

```text
IndicatorPlugin
IndicatorRegistry
IndicatorEngine
```

---

# 82. Phase 4 — Screening

Implement:

```text
Screening DSL
DSL validator
Filter engine
Execution planner
Ranking
Results
```

First test:

```text
Nifty Total Market
AND
RSI < 35
AND
Near lower Bollinger Band
```

---

# 83. Phase 5 — Agents

Implement:

```text
OrchestratorAgent
UniverseAgent
MarketDataAgent
IndicatorAgent
ClassificationAgent
FilterAgent
ExplanationAgent
```

Then implement A2A communication.

---

# 84. Phase 6 — GPT-OSS Chat

Implement:

```text
LLMProvider
GPTOSSProvider
LLMChatAgent
structured output
tool calling
chat memory
screen modification
screen execution
```

Test:

```text
Find oversold stocks.
```

through the entire pipeline.

---

# 85. Phase 7 — Advanced Analysis

Implement:

```text
Candlestick Agent
Strategy Agent
Scoring Agent
Risk Agent
Research Agent
```

---

# 86. Phase 8 — Future

Implement:

```text
additional indicators
alerts
backtesting
market regime
news
fundamental research
strategy discovery
```

---

# 87. Critical Development Rules

Claude Code must follow these rules:

1. Inspect before coding.
2. Never invent MCP tool names.
3. Never fabricate financial data.
4. Never fabricate missing indicators.
5. Never expose credentials.
6. Never allow LLM direct SQL.
7. Never allow LLM arbitrary MCP access.
8. Validate all LLM structured output.
9. Keep deterministic calculations outside the LLM.
10. Keep providers behind adapters.
11. Keep agents behind interfaces.
12. Keep filtering separate from scoring.
13. Keep indicators separate from strategies.
14. Keep strategies versioned.
15. Keep provenance for all financial values.
16. Support UNKNOWN values.
17. Support multiple timeframes.
18. Use parallel execution where safe.
19. Cache expensive requests.
20. Do not prematurely introduce microservices.
21. Do not add order execution to V1.
22. Write tests for every important module.
23. Update documentation with architectural changes.
24. Prefer small incremental commits.
25. Do not generate huge untested code dumps.

---

# 88. First Prompt to Claude Code

After placing this document in the repository, give Claude Code the following instruction:

```text
Read STOCK_SCREENER_ARCHITECTURE.md completely.

You are the lead engineer for this project.

Do NOT start by generating the entire application.

First inspect the current repository.

Specifically inspect:

1. Directory structure
2. package.json
3. Existing frontend
4. Existing backend
5. Existing database
6. Redis configuration
7. Environment files
8. MCP configuration
9. Kite MCP configuration
10. TradingView MCP configuration
11. Actual MCP servers available
12. Actual MCP tools available
13. Existing Claude/LLM configuration

Do not assume any MCP tool names.

After inspection, produce:

1. Repository Assessment
2. Current Architecture
3. Gap Analysis
4. MCP Capability Matrix
5. Proposed Architecture
6. Proposed Directory Structure
7. Domain Model
8. Screening DSL
9. A2A Message Protocol
10. LLM Architecture
11. MCP Architecture
12. Database Model
13. Implementation Phases
14. Risks and Technical Decisions

DO NOT make large code changes yet.

Do not replace working infrastructure unnecessarily.

Preserve existing configurations where possible.

If something required by STOCK_SCREENER_ARCHITECTURE.md is unavailable, identify it explicitly.

Wait for approval before implementing Phase 1.
```

---

# 89. Definition of Done for V1

V1 is complete when the user can open the dashboard and do:

```text
Universe:
Nifty Total Market

Market Cap:
Mid Cap

Sector:
IT

RSI:
< 35

Bollinger:
Price within 3% of lower band

Timeframe:
Daily
```

Click:

```text
RUN SCREEN
```

and get:

```text
Matching stocks
↓
Sorted results
↓
Technical values
↓
Market classification
↓
Sector
↓
Index membership
↓
Data timestamps
↓
Data sources
```

Then the user can open AI Chat and type:

```text
Only show stocks with RSI below 30.
```

The AI modifies the existing screen.

Then:

```text
Also remove financial stocks.
```

The AI modifies it again.

Then:

```text
Save this as Oversold Midcap Setup.
```

The screen is saved.

Then:

```text
Explain the top 5 stocks.
```

The ExplanationAgent produces explanations based only on structured data.

---

# 90. Long-Term Vision

The final platform should evolve toward:

```text
                    AI MARKET RESEARCH PLATFORM

                             User
                               │
                               ▼
                         GPT-OSS Chat
                               │
                               ▼
                         Orchestrator
                               │
          ┌────────────────────┼─────────────────────┐
          │                    │                     │
          ▼                    ▼                     ▼
      Screener             Research              Strategy
          │                    │                     │
          ▼                    ▼                     ▼
      Indicators           Fundamentals          Backtest
      Patterns             News                   Signals
      Universe             Sectors                Risk
          │                    │                     │
          └────────────────────┼─────────────────────┘
                               ▼
                         Market Knowledge
                               │
              ┌────────────────┼─────────────────┐
              ▼                ▼                 ▼
           Kite MCP       TradingView MCP    Future MCPs
              │                │                 │
              └────────────────┼─────────────────┘
                               ▼
                        Data / Knowledge
                             Layer
                               │
                               ▼
                         AI + Analytics
```

The objective is not merely:

> "Find stocks where RSI < 35."

The objective is to create a **general-purpose, extensible Indian equity research and screening platform** where natural language, deterministic financial analytics, specialized agents and MCP data providers work together.

---

# 91. Final Architectural Rule

Always preserve this separation:

```text
                    ┌─────────────────────┐
                    │        LLM          │
                    │                     │
                    │ Understand          │
                    │ Plan                │
                    │ Explain             │
                    │ Converse             │
                    └──────────┬──────────┘
                               │
                         Structured Intent
                               │
                               ▼
                    ┌─────────────────────┐
                    │   ORCHESTRATOR      │
                    │                     │
                    │ Plan                │
                    │ Route               │
                    │ Coordinate           │
                    │ Validate             │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ DETERMINISTIC CORE  │
                    │                     │
                    │ Calculate           │
                    │ Filter              │
                    │ Rank                │
                    │ Score               │
                    │ Validate            │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    MCP PROVIDERS    │
                    │                     │
                    │ Kite                │
                    │ TradingView         │
                    │ Future providers    │
                    └─────────────────────┘
```

**LLM = intelligence/interface**

**Orchestrator = coordination**

**Agents = specialized capabilities**

**Engines = deterministic computation**

**MCP = external data/tool connectivity**

**Database/Redis = persistence and performance**

This separation should remain intact as the system grows.
