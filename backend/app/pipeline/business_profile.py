"""Fetch + store Yahoo's business description/industry for a stock."""
from __future__ import annotations

from datetime import datetime, timezone

import yfinance as yf
from sqlalchemy.orm import Session

from app.data.yfinance_client import _yf_symbol
from app.infrastructure.database.models import Stock, StockBusinessProfile


def fetch_profile(stock: Stock) -> dict | None:
    info = yf.Ticker(_yf_symbol(stock.exchange, stock.symbol)).info or {}
    if not (info.get("longBusinessSummary") or info.get("industry")):
        return None
    return {
        "yahoo_industry": info.get("industry"),
        "yahoo_sector": info.get("sector"),
        "description": info.get("longBusinessSummary"),
    }


def store_profile(db: Session, stock_id: str, data: dict) -> None:
    row = db.get(StockBusinessProfile, stock_id)
    if row is None:
        row = StockBusinessProfile(stock_id=stock_id)
        db.add(row)
    row.yahoo_industry = data["yahoo_industry"]
    row.yahoo_sector = data["yahoo_sector"]
    row.description = data["description"]
    row.fetched_at = datetime.now(timezone.utc)
    db.commit()
