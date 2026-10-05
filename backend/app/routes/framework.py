"""Stock Quality framework scores (app/framework/)."""
from fastapi import APIRouter, HTTPException, Query

from app.framework import store
from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import Stock

router = APIRouter(prefix="/api/framework")

SCORES = ("quality", "fundamental", "quantitative", "relative_strength", "technical", "valuation")


def _row(score, stock: Stock) -> dict:
    out = {
        "stock_id": stock.id, "symbol": stock.symbol, "company_name": stock.company_name, "sector": stock.sector,
        "market_cap": float(stock.market_cap) if stock.market_cap is not None else None,
        "as_of": score.as_of, "basis": score.basis, "latest_fy": score.latest_fy, "sector_framework": score.sector_framework,
        "trend": score.trend, "classification": score.classification, "action": score.action,
        "valuation_view": score.valuation_view, "reconstructed": score.reconstructed,
    }
    out.update({name: float(v) if (v := getattr(score, name)) is not None else None for name in (*SCORES, "business_quality")})
    return out


@router.get("/scores")
def list_scores(
    q: str | None = None, sector: str | None = None, trend: str | None = None,
    sort: str = Query("quality"), order: str = Query("desc", pattern="^(asc|desc)$"),
    limit: int = Query(100, ge=1, le=5000), offset: int = Query(0, ge=0),
):
    """Latest framework scores for every scored stock, one row each."""
    db = get_db()
    try:
        stocks = {s.id: s for s in db.query(Stock).filter(Stock.is_active.is_(True))}
        rows = [_row(r, stocks[r.stock_id]) for r in store.latest_for_all(db) if r.stock_id in stocks]
        if q:
            needle = q.strip().lower()
            rows = [r for r in rows if needle in r["symbol"].lower() or needle in r["company_name"].lower()]
        if sector:
            rows = [r for r in rows if r["sector"] == sector]
        if trend:
            rows = [r for r in rows if r["trend"] == trend.upper()]
        key = sort if sort in (*SCORES, "market_cap", "symbol") else "quality"
        present = [r for r in rows if r[key] is not None]
        present.sort(key=lambda r: r[key], reverse=order == "desc")
        rows = present + [r for r in rows if r[key] is None]  # unscored rows always last
        return {"total": len(rows), "scores": rows[offset:offset + limit],
                "sectors": sorted({s.sector for s in stocks.values() if s.sector})}
    finally:
        db.close()


@router.get("/{symbol}")
def stock_scores(symbol: str):
    """One stock's latest scores with every input behind them."""
    db = get_db()
    try:
        stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
        if stock is None:
            raise HTTPException(404, f"Unknown symbol '{symbol}'")
        score = store.latest(db, stock.id)
        if score is None:
            raise HTTPException(404, f"No framework scores for '{symbol}' yet")
        return {**_row(score, stock), "detail": score.detail}
    finally:
        db.close()
