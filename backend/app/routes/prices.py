"""Price store: stored daily history and what it covers."""
from datetime import date, timedelta

from fastapi import APIRouter, HTTPException

from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import IndexBar, Stock
from app.infrastructure.redis.client import cache_get_json, cache_set_json
from app.prices import benchmarks, nse_bhavcopy, store

router = APIRouter(prefix="/api/prices")


@router.get("/status")
def status():
    db = get_db()
    try:
        return store.coverage(db)
    finally:
        db.close()


@router.get("/check")
def check():
    """Stored closes against NSE's official bhavcopy for the latest published day."""
    cached = cache_get_json("prices:check")
    if cached:
        return cached
    db = get_db()
    try:
        result = nse_bhavcopy.compare(db)
    finally:
        db.close()
    result["day"] = str(result["day"])
    cache_set_json("prices:check", result, 6 * 3600)
    return result


@router.get("/indices")
def indices():
    db = get_db()
    try:
        latest = db.query(IndexBar.bar_date).order_by(IndexBar.bar_date.desc()).limit(1).scalar()
        rows = db.query(IndexBar).filter(IndexBar.bar_date == latest).order_by(IndexBar.index_name).all() if latest else []
        return {"as_of": latest, "indices": [
            {"name": r.index_name, "close": float(r.close), "pe": r.pe and float(r.pe), "pb": r.pb and float(r.pb),
             "div_yield": r.div_yield and float(r.div_yield), "source_url": r.source_url} for r in rows]}
    finally:
        db.close()


@router.get("/index/{index_name}")
def index_history(index_name: str, days: int = 400):
    db = get_db()
    try:
        series = store.index_closes(db, index_name, date.today() - timedelta(days=days))
        if not series:
            raise HTTPException(404, f"No stored history for index '{index_name}'")
        return {"index": index_name, "bars": [{"date": d, "close": c} for d, c in series]}
    finally:
        db.close()


@router.get("/stock/{symbol}")
def stock_history(symbol: str, days: int = 400):
    db = get_db()
    try:
        stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
        if stock is None:
            raise HTTPException(404, f"Unknown symbol '{symbol}'")
        rows = store.bars(db, stock.id, date.today() - timedelta(days=days))
        return {
            "symbol": stock.symbol, "source": "Yahoo Finance daily history",
            "benchmarks": {"market": benchmarks.MARKET, "broad_market": benchmarks.BROAD_MARKET,
                           "sector": benchmarks.sector_benchmark(stock.sector, stock.industry)},
            "bars": [{"date": b.bar_date, "open": b.open and float(b.open), "high": b.high and float(b.high),
                      "low": b.low and float(b.low), "close": float(b.close), "adj_close": float(b.adj_close),
                      "volume": b.volume} for b in rows],
        }
    finally:
        db.close()
