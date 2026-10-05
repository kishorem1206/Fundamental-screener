"""Everything the technical screener serves, under one prefix.

As a separate app these routes sat at the root (`/screens/run`, `/macd/scan`,
`/tv/scan` …). Inside the merged app they live under `/api/technical`, so none
of them can collide with a fundamental route of the same name (`/health`,
`/stocks`).
"""
from fastapi import APIRouter

from app.technical.agents.registry import agent_registry
from app.technical.routes import (
    admin, chat, explain, fundamentals, health, indicators, macd, nifty_index, quotes,
    rsi_divergence, rsi_momentum, screens, stocks, tv_screener, universes,
)

router = APIRouter(prefix="/api/technical")
for _module in (health, universes, stocks, indicators, screens, quotes, fundamentals, explain, chat,
                rsi_momentum, admin, nifty_index, rsi_divergence, macd, tv_screener):
    router.include_router(_module.router)


def register_agents() -> None:
    """Same agents, same order, as the old app's startup."""
    from app.technical.agents.chat_agent import chat_agent
    from app.technical.agents.classification_agent import classification_agent
    from app.technical.agents.explanation_agent import explanation_agent
    from app.technical.agents.filter_agent import filter_agent
    from app.technical.agents.fundamental_agent import fundamental_agent
    from app.technical.agents.indicator_agent import indicator_agent
    from app.technical.agents.market_data_agent import market_data_agent
    from app.technical.agents.nifty_index_agent import nifty_index_agent
    from app.technical.agents.research_agent import research_agent
    from app.technical.agents.scoring_agent import scoring_agent
    from app.technical.agents.universe_agent import universe_agent

    for agent in (universe_agent, classification_agent, indicator_agent, filter_agent, scoring_agent,
                  market_data_agent, fundamental_agent, explanation_agent, research_agent, chat_agent,
                  nifty_index_agent):
        agent_registry.register(agent)
