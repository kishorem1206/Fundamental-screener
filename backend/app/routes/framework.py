"""Stock Quality framework scores (app/framework/)."""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app.framework import sector_rank, store
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
        "quality_direction": score.quality_direction,
        "quality_change_6m": float(score.quality_change_6m) if score.quality_change_6m is not None else None,
        "quality_change_12m": float(score.quality_change_12m) if score.quality_change_12m is not None else None,
    }
    out.update({name: float(v) if (v := getattr(score, name)) is not None else None for name in (*SCORES, "business_quality")})
    return out


@router.get("/scores")
def list_scores(
    q: str | None = None, sector: str | None = None, trend: str | None = None, direction: str | None = None,
    classification: str | None = None, action: str | None = None,
    sort: str = Query("quality"), order: str = Query("desc", pattern="^(asc|desc)$"),
    limit: int = Query(100, ge=1, le=5000), offset: int = Query(0, ge=0),
):
    """Latest framework scores for every scored stock, one row each."""
    db = get_db()
    try:
        stocks = {s.id: s for s in db.query(Stock).filter(Stock.is_active.is_(True))}
        latest = [r for r in store.latest_for_all(db) if r.stock_id in stocks]
        rows = [_row(r, stocks[r.stock_id]) for r in latest]
        ranked = sector_rank.ranks([(r["stock_id"], r["sector"], r["quality"]) for r in rows])
        for r in rows:
            r["sector_rank"] = ranked.get(r["stock_id"])
        if q:
            needle = q.strip().lower()
            rows = [r for r in rows if needle in r["symbol"].lower() or needle in r["company_name"].lower()]
        if sector:
            rows = [r for r in rows if r["sector"] == sector]
        if trend:
            rows = [r for r in rows if r["trend"] == trend.upper()]
        if direction:
            rows = [r for r in rows if r["quality_direction"] == direction.upper()]
        if classification:
            rows = [r for r in rows if r["classification"] == classification]
        if action:
            rows = [r for r in rows if r["action"] == action]
        key = sort if sort in (*SCORES, "market_cap", "symbol", "quality_change_6m", "quality_change_12m") else "quality"
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
        peers = [(r.stock_id, s.sector, float(r.quality) if r.quality is not None else None)
                 for r in store.latest_for_all(db) if (s := db.get(Stock, r.stock_id)) is not None and s.sector == stock.sector]
        from app.framework.decisions import best_alternative, replacement, values

        alt = best_alternative(db, stock, stock.id)
        out = {**_row(score, stock), "sector_rank": sector_rank.ranks(peers).get(stock.id), "detail": score.detail,
               "best_alternative": alt}
        if alt and score.classification in ("Replacement Candidate", "Improving / Watch", "Avoid"):
            out["replacement"] = replacement({**values(score), "symbol": stock.symbol, "valuation_view": score.valuation_view},
                                             alt, score.detail, store.latest(db, alt["stock_id"]))
        return out
    finally:
        db.close()


@router.post("/{symbol}/explain")
def explain_stock(symbol: str, model: bool = True):
    """Plain-language reasoning for the stock's decision (gpt-oss, checked
    against the decision; fixed text when the model is unavailable)."""
    from app.framework.decisions import best_alternative, values
    from app.framework.explain import explain

    db = get_db()
    try:
        stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
        row = store.latest(db, stock.id) if stock else None
        if row is None:
            raise HTTPException(404, f"No framework scores for '{symbol}' yet")
        return explain(db, row, values(row), best_alternative(db, stock, stock.id), use_model=model)
    finally:
        db.close()


@router.get("/{symbol}/integrated-report.pdf")
def integrated_report(symbol: str):
    """One PDF: the Stock Quality framework section, the editorial report (when a
    full analysis exists) and the deep report (when built)."""
    from app.reporting.integrated.build import build

    db = get_db()
    try:
        path = build(db, symbol)
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    finally:
        db.close()
    return FileResponse(path, media_type="application/pdf", filename=path.rsplit("/", 1)[-1])
