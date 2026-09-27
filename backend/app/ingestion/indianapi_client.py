"""IndianAPI.in (stock.indianapi.in) — Free plan. See `Important md files/
indianapi.md` for the full endpoint reference.

Only two endpoint families are used here, deliberately: analyst rating
distribution and market-wide movers. Everything else in that doc
(currentPrice, financials, shareholding, corporate actions, news, a
proprietary "risk meter") substantially duplicates data this codebase
already sources more rigorously — confirmed by comparison, 2026-09-14 —
from yfinance, NSE, and Screener.in directly. Paying-API calls aren't spent
re-fetching what's already covered for free from a more authoritative
source.

`/stock_target_price` is genuinely new: `AnalystConsensus` already existed
(migration 0012) with `buy_pct`/`hold_pct`/`sell_pct` fields, but its only
populated source (IndMoney) requires a Claude session's MCP connector —
there was no autonomous way to fill it. This module gives it one, under
its own `source="INDIANAPI"` tag, never blended with the IndMoney row.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import requests
from sqlalchemy.orm import Session

from app.config import config
from app.infrastructure.database.models import AnalystConsensus
from app.infrastructure.redis.client import cache_get_json, cache_set_json
from app.logger import logger

SOURCE = "INDIANAPI"
_BASE = "https://stock.indianapi.in"
_MARKET_MOVERS_CACHE_KEY = "indianapi:market_movers"
_MARKET_MOVERS_TTL = 60 * 15  # 15min — shared market-wide snapshot, not per-company


def _headers() -> dict:
    return {"X-Api-Key": config.indianapi_key}


def ingest_analyst_recommendations(db: Session, company_id: str, symbol: str) -> AnalystConsensus | None:
    """Never raises — returns None if no key configured, the call fails, or
    the company has no analyst coverage on file."""
    if not config.indianapi_key:
        return None
    try:
        r = requests.get(f"{_BASE}/stock_target_price", params={"stock_id": symbol},
                          headers=_headers(), timeout=15)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        logger.warning("indianapi_client: stock_target_price failed", symbol=symbol, error=str(e))
        return None

    rec = data.get("recommendation") or {}
    stats = {
        s["Recommendation"]: s["NumberOfAnalysts"]
        for s in (rec.get("Statistics") or {}).get("Statistic", [])
    }
    total = sum(stats.values())
    if not total:
        return None

    # IndianAPI's 1-5 scale: 1=Buy, 2=Outperform, 3=Hold, 4=Underperform, 5=Sell.
    buy = stats.get(1, 0) + stats.get(2, 0)
    hold = stats.get(3, 0)
    sell = stats.get(4, 0) + stats.get(5, 0)
    sentiment = "BUY" if buy >= hold and buy >= sell else ("HOLD" if hold >= sell else "SELL")

    price_target = data.get("priceTarget") or {}
    now = datetime.now(timezone.utc)
    fields = dict(
        num_analysts=total, sentiment=sentiment,
        buy_pct=round(buy / total * 100, 1), hold_pct=round(hold / total * 100, 1),
        sell_pct=round(sell / total * 100, 1),
        target_price_mean=price_target.get("Mean"), target_price_low=price_target.get("Low"),
        target_price_high=price_target.get("High"), price_at_capture=None, implied_upside_pct=None,
        source=SOURCE,
    )

    existing = db.query(AnalystConsensus).filter_by(company_id=company_id, source=SOURCE).first()
    if existing:
        for k, v in fields.items():
            setattr(existing, k, v)
        existing.retrieved_at = now
        row = existing
    else:
        row = AnalystConsensus(id=str(uuid.uuid4()), company_id=company_id, retrieved_at=now, **fields)
        db.add(row)
    db.flush()
    logger.info("indianapi_client: analyst recommendations ingested", symbol=symbol, num_analysts=total)
    return row


def fetch_market_movers() -> dict:
    """Market-wide (not per-company) snapshot: top gainers/losers, most
    active on NSE+BSE, price shockers, 52-week highs/lows. Cached in Redis
    (15min TTL) since it's shared across every viewer of the Explore page,
    not fetched once per analysis. Never raises — returns {} on any
    failure; a per-endpoint failure leaves that key None rather than
    dropping the whole snapshot."""
    if not config.indianapi_key:
        return {}
    cached = cache_get_json(_MARKET_MOVERS_CACHE_KEY)
    if cached is not None:
        return cached

    endpoints = {
        "trending": "trending",
        "nse_most_active": "NSE_most_active",
        "bse_most_active": "BSE_most_active",
        "price_shockers": "price_shockers",
        "week_52_high_low": "fetch_52_week_high_low_data",
    }
    result: dict = {}
    for key, path in endpoints.items():
        try:
            r = requests.get(f"{_BASE}/{path}", headers=_headers(), timeout=15)
            r.raise_for_status()
            result[key] = r.json()
        except Exception as e:
            logger.warning("indianapi_client: market movers endpoint failed", endpoint=path, error=str(e))
            result[key] = None

    cache_set_json(_MARKET_MOVERS_CACHE_KEY, result, _MARKET_MOVERS_TTL)
    return result
