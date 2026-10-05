"""Daily stock history from Yahoo Finance.

`close` is Yahoo's Close (adjusted for splits and bonus issues), `adj_close`
its Adj Close (also adjusted for dividends). Both are restated backwards every
time a company splits or pays, which `update()` detects and handles by
re-reading that stock's whole history.
"""
from __future__ import annotations

import time
from datetime import date, timedelta

import pandas as pd
import yfinance as yf
from sqlalchemy.orm import Session

from app.infrastructure.database.models import PriceBar, Stock
from app.logger import logger
from app.prices import store

SOURCE = "YAHOO"
_BATCH = 60
_PAUSE = 2.0
_RESTATED = 0.005  # a stored adjusted close differing by more than 0.5% means history was restated


def ticker(stock: Stock) -> str:
    return f"{stock.symbol}{'.BO' if (stock.exchange or 'NSE').upper() == 'BSE' else '.NS'}"


def _rows(stock_id: str, frame: pd.DataFrame) -> list[dict]:
    if frame is None or frame.empty or "Close" not in frame:
        return []
    frame = frame.dropna(subset=["Close"])
    out = []
    for ts, r in frame.iterrows():
        close = float(r["Close"])
        if close <= 0:
            continue
        adj = r.get("Adj Close")
        vol = r.get("Volume")
        out.append({
            "stock_id": stock_id,
            "bar_date": ts.date(),
            "open": None if pd.isna(r.get("Open")) else float(r["Open"]),
            "high": None if pd.isna(r.get("High")) else float(r["High"]),
            "low": None if pd.isna(r.get("Low")) else float(r["Low"]),
            "close": close,
            "adj_close": close if adj is None or pd.isna(adj) else float(adj),
            "volume": None if vol is None or pd.isna(vol) else int(vol),
            "source": SOURCE,
        })
    return out


def download(stocks: list[Stock], **window) -> dict[str, list[dict]]:
    """{stock_id: rows} for one batch. A ticker Yahoo cannot serve maps to []."""
    tickers = {ticker(s): s.id for s in stocks}
    for attempt in range(4):
        try:
            data = yf.download(list(tickers), interval="1d", auto_adjust=False, group_by="ticker",
                               threads=True, progress=False, **window)
            break
        except Exception as exc:  # rate limit or network: wait and retry the batch
            logger.warning("yahoo batch failed", attempt=attempt, error=str(exc))
            time.sleep(15 * (attempt + 1))
    else:
        return {sid: [] for sid in tickers.values()}
    out = {}
    for tk, sid in tickers.items():
        try:
            frame = data[tk] if isinstance(data.columns, pd.MultiIndex) else data
        except KeyError:
            frame = None
        out[sid] = _rows(sid, frame)
    return out


def _batches(items: list, size: int = _BATCH):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def backfill(db: Session, stocks: list[Stock], years: int = 3, on_batch=None) -> dict:
    """Whole history for the given stocks, replacing anything stored."""
    start = date.today() - timedelta(days=365 * years + 10)
    done = empty = bars = 0
    for batch in _batches(stocks):
        for sid, rows in download(batch, start=start.isoformat()).items():
            if rows:
                bars += store.replace_price_history(db, sid, rows)
                done += 1
            else:
                empty += 1
        db.commit()
        if on_batch:
            on_batch(done, empty)
        time.sleep(_PAUSE)
    return {"stocks_stored": done, "no_data": empty, "bars": bars}


def update(db: Session, stocks: list[Stock], years: int = 3) -> dict:
    """Adds the days since each stock's last stored bar. Stocks with no history
    yet, and stocks whose earlier prices Yahoo has since restated, get a full
    re-read instead."""
    last = store.last_price_dates(db)
    fresh = [s for s in stocks if s.id not in last]
    known = [s for s in stocks if s.id in last]
    restated: list[Stock] = []
    added = 0
    by_id = {s.id: s for s in known}
    for batch in _batches(known):
        oldest = min(last[s.id] for s in batch)
        start = oldest - timedelta(days=7)
        got = download(batch, start=start.isoformat())
        for sid, rows in got.items():
            if not rows:
                continue
            stored = {b.bar_date: float(b.adj_close) for b in
                      db.query(PriceBar).filter(PriceBar.stock_id == sid, PriceBar.bar_date >= start)}
            overlap = [(r["adj_close"], stored[r["bar_date"]]) for r in rows if r["bar_date"] in stored]
            if any(abs(new - old) > _RESTATED * old for new, old in overlap):
                restated.append(by_id[sid])
                continue
            added += store.upsert_price_bars(db, [r for r in rows if r["bar_date"] >= last[sid]])
        db.commit()
        time.sleep(_PAUSE)
    refill = backfill(db, fresh + restated, years=years) if fresh or restated else {"stocks_stored": 0, "no_data": 0, "bars": 0}
    return {"bars_added": added, "new_stocks": len(fresh), "restated": [s.symbol for s in restated], "refilled": refill}
