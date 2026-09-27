"""Market-wide movers (IndianAPI.in) — top gainers/losers, most active on
NSE/BSE, price shockers, 52-week highs/lows. Not tied to any one company —
see app/ingestion/indianapi_client.py's module docstring for the full
rationale and its Redis caching.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.ingestion.indianapi_client import fetch_market_movers

router = APIRouter(prefix="/api/market-movers")


@router.get("")
def get_market_movers():
    return fetch_market_movers()
