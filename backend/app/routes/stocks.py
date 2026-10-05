"""
Read-only stock lookup endpoints — uses the existing stocks table.
No modifications to existing records.
"""
from fastapi import APIRouter, Query
from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import Stock
from app.sectors.registry import get_framework

router = APIRouter(prefix="/api/stocks")


@router.get("/sectors")
def list_sectors():
    """Return distinct sectors from the existing stocks database."""
    db = get_db()
    try:
        rows = (
            db.query(Stock.sector)
            .filter(Stock.is_active == True, Stock.sector.isnot(None))
            .distinct()
            .order_by(Stock.sector)
            .all()
        )
        return {"sectors": [r.sector for r in rows if r.sector]}
    finally:
        db.close()


@router.get("/sector-counts")
def sector_counts():
    """Count of tracked stocks per resolved sector FRAMEWORK (one of the 34
    `app/sectors/*.py` frameworks + Generic) — not the raw `stocks.sector`
    column grouped as-is. The raw column is too coarse to be useful here:
    e.g. every NBFC, bank, and insurer alike carries `sector="Financial
    Services"`, so grouping on it directly would show one inflated bucket
    instead of the real Banks/NBFCs/Insurance/Housing Finance breakdown
    `get_framework()` already resolves correctly (see
    `classification_map.py` — this reuses the exact same resolution the
    Sector Analysis tab uses, so the count here always matches what a user
    would see if they opened any one of those companies).

    Also returns, per sector, the full member stock list (symbol, name,
    market cap, market_cap_category) sorted by market cap descending — the
    KPI-card drill-down needs this, and at ~1610 rows total it's cheap
    enough to send in the same response rather than a second round-trip
    per card click."""
    db = get_db()
    try:
        rows = (
            db.query(Stock.id, Stock.symbol, Stock.company_name, Stock.sector, Stock.industry,
                      Stock.basic_industry, Stock.market_cap, Stock.market_cap_category)
            .filter(Stock.is_active == True)
            .all()
        )
        by_sector: dict[str, list[dict]] = {}
        for stock_id, symbol, company_name, sector, industry, basic_industry, market_cap, category in rows:
            framework = get_framework(sector, industry=industry, basic_industry=basic_industry)
            by_sector.setdefault(framework.sector_name, []).append({
                "stock_id": stock_id,
                "symbol": symbol,
                "company_name": company_name,
                "basic_industry": basic_industry,
                "market_cap_cr": float(market_cap) / 1e7 if market_cap is not None else None,
                "market_cap_category": category,
            })
        for stocks in by_sector.values():
            stocks.sort(key=lambda s: s["market_cap_cr"] or 0, reverse=True)
        ordered = sorted(by_sector.items(), key=lambda kv: len(kv[1]), reverse=True)
        return {
            "sector_counts": [
                {"sector": name, "count": len(stocks), "stocks": stocks} for name, stocks in ordered
            ],
            "total": sum(len(stocks) for stocks in by_sector.values()),
        }
    finally:
        db.close()


@router.get("")
def list_stocks(
    sector: str | None = Query(default=None),
    exchange: str | None = Query(default=None),
    # le=1000 real bug found live 2026-09-17: the frontend's global search
    # box loads the whole stock universe client-side once (App.tsx calls
    # getStocks(undefined, 1000)) and filters/ranks in the browser — with
    # `stocks` grown to 1610 companies (alphabetical order), the old le=1000
    # cap silently truncated the list before "P" (1074 companies sort
    # before "Pine Labs Ltd."), making every company from roughly the back
    # third of the alphabet unsearchable regardless of query. Raised to
    # 2000 to fix it — insufficient headroom, it turned out: by 2026-09-28
    # the IPO-promotion work that same session grew the universe to 2624
    # active stocks, silently recreating the identical bug (both here and
    # in the QuickScreener coverage counter, which used this same capped
    # list's length as its denominator). Raised to 5000 this time, with
    # real headroom rather than "just past today's count" again.
    limit: int = Query(default=200, ge=1, le=5000),
):
    """Return stocks, optionally filtered by sector."""
    db = get_db()
    try:
        q = db.query(Stock).filter(Stock.is_active == True)
        if sector:
            q = q.filter(Stock.sector == sector)
        if exchange:
            q = q.filter(Stock.exchange == exchange.upper())
        stocks = q.order_by(Stock.company_name).limit(limit).all()
        return {
            "stocks": [
                {
                    "id": s.id,
                    "symbol": s.symbol,
                    "exchange": s.exchange,
                    "company_name": s.company_name,
                    "sector": s.sector,
                    "industry": s.industry,
                    "market_cap": float(s.market_cap) if s.market_cap else None,
                    "market_cap_category": s.market_cap_category,
                    "isin": s.isin,
                }
                for s in stocks
            ],
            "count": len(stocks),
        }
    finally:
        db.close()


@router.get("/{stock_id:path}")
def get_stock(stock_id: str):
    db = get_db()
    try:
        stock = db.query(Stock).filter_by(id=stock_id).first()
        if stock is None:
            return {"error": "Stock not found"}, 404
        return {
            "stock": {
                "id": stock.id,
                "symbol": stock.symbol,
                "exchange": stock.exchange,
                "company_name": stock.company_name,
                "sector": stock.sector,
                "industry": stock.industry,
                "market_cap": float(stock.market_cap) if stock.market_cap else None,
                "market_cap_category": stock.market_cap_category,
            }
        }
    finally:
        db.close()
