"""CANSLIM screen for every stock (app/canslim/). Nothing here feeds another score."""
from fastapi import APIRouter, Query
from sqlalchemy import or_

from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import CanslimScore, Stock

router = APIRouter(prefix="/api/canslim")

_LETTERS = ("c", "a", "n", "s", "l", "i", "m")
_SORT = (*_LETTERS, "canslim", "peer_quality", "combined")


def _num(v) -> float | None:
    return float(v) if v is not None else None


@router.get("/scores")
def scores(q: str | None = None, sector: str | None = None, sort_by: str = "canslim", order: str = "desc", min_canslim: float = 0,
           strong: str = "", limit: int = Query(100, ge=1, le=500), offset: int = 0):
    """`strong`: letters that must score 70 or more, e.g. "ca"."""
    db = get_db()
    try:
        query = db.query(CanslimScore, Stock).join(Stock, Stock.id == CanslimScore.stock_id).filter(Stock.is_active.is_(True))
        if q and q.strip():
            needle = f"%{q.strip()}%"
            query = query.filter(or_(Stock.symbol.ilike(needle), Stock.company_name.ilike(needle)))
        if sector:
            query = query.filter(Stock.sector == sector)
        if min_canslim:
            query = query.filter(CanslimScore.canslim >= min_canslim)
        for letter in strong.lower():
            if letter in _LETTERS:
                query = query.filter(getattr(CanslimScore, letter) >= 70)
        total = query.count()
        column = getattr(CanslimScore, sort_by if sort_by in _SORT else "canslim")
        rows = query.order_by((column.asc() if order == "asc" else column.desc()).nullslast(), Stock.symbol).offset(offset).limit(limit).all()
        first = db.query(CanslimScore).filter(CanslimScore.m.isnot(None)).first()
        return {"total": total, "as_of": first.as_of.isoformat() if first else None, "market": (first.detail or {}).get("m") if first else None,
                "results": [{"stock_id": s.id, "symbol": s.symbol, "company_name": s.company_name, "sector": s.sector, "basic_industry": s.basic_industry,
                             **{k: _num(getattr(c, k)) for k in _SORT}, "letters": c.letters, "basis": c.basis, "detail": c.detail} for c, s in rows]}
    finally:
        db.close()
