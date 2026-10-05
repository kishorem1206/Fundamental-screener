"""Filter/sort companies by their six category scores (+ overall), one at a
time or combined. Backed by `fa_company_scores` (full-pipeline scores,
refreshed after every analysis — app/services/company_scores.py). The same
listing logic serves `fa_quick_scores` via `list_scores()` (routes/
quick_scores.py) — two separate tables, one shared implementation.

    GET /api/company-scores?min_growth=70&min_profitability=60&max_valuation=40&sort_by=overall

Every score is 0-100. Filters AND together; unknown query keys are a 400 so
a typo never silently returns unfiltered results.
"""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import asc, case, desc, func

from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import CompanyScore, Stock
from app.services.company_scores import SCORE_FIELDS

router = APIRouter(prefix="/api/company-scores")

_TEXT_FILTERS = {"q", "sector", "macro_sector", "rating", "valuation_view", "ipo_only", "ipo_since"}
_CONTROL_PARAMS = {"sort_by", "order", "limit", "offset"}
_SORTABLE = set(SCORE_FIELDS) | {"scored_at", "latest_quarter_end", "company_name", "market_cap", "ipo_listing_date"}
_RANGE_PARAMS = {f"{bound}_{field}" for field in SCORE_FIELDS for bound in ("min", "max")}


def _num(v):
    return float(v) if v is not None else None


def _row_dict(score, stock: Stock) -> dict:
    return {
        "stock_id": stock.id, "symbol": stock.symbol, "company_name": stock.company_name,
        "sector": stock.sector, "macro_sector": stock.macro_sector,
        "market_cap": _num(stock.market_cap),
        "ipo_listing_date": stock.ipo_listing_date.isoformat() if stock.ipo_listing_date else None,
        **{f: _num(getattr(score, f)) for f in SCORE_FIELDS},
        "overall_rating": score.overall_rating, "valuation_view": score.valuation_view,
        "red_flags": score.red_flags or [],
        # Present on one table or the other, never both:
        "analysis_id": getattr(score, "analysis_id", None),
        "sector_framework": getattr(score, "sector_framework", None),
        "latest_fy": getattr(score, "latest_fy", None),
        # The two components blended into `growth` (scoring.py's
        # `_growth_score()`) — only on QuickScore today (see that model's
        # docstring), None here for a CompanyScore row.
        "growth_annual": _num(getattr(score, "growth_annual", None)),
        "growth_quarterly": _num(getattr(score, "growth_quarterly", None)),
        "scored_at": score.scored_at.isoformat() if score.scored_at else None,
        "latest_quarter_end": (
            score.latest_quarter_end.isoformat() if getattr(score, "latest_quarter_end", None) else None
        ),
    }


@router.get("")
def list_company_scores(request: Request):
    return list_scores(request, CompanyScore)


def list_scores(request: Request, model, extra_numeric_fields: frozenset[str] = frozenset()):
    """`model` is CompanyScore (full pipeline) or QuickScore (Yahoo-only).
    `extra_numeric_fields` widens filtering/sorting to columns that only
    exist on `model` (not shared via `SCORE_FIELDS`) — e.g. QuickScore's
    `growth_annual`/`growth_quarterly` (see quick_scores.py's call site).
    Callers must only pass field names that are real columns on `model`."""
    range_params = _RANGE_PARAMS | {f"{bound}_{field}" for field in extra_numeric_fields for bound in ("min", "max")}
    sortable = _SORTABLE | extra_numeric_fields

    params = dict(request.query_params)
    unknown = set(params) - range_params - _TEXT_FILTERS - _CONTROL_PARAMS
    if unknown:
        raise HTTPException(status_code=400, detail=f"Unknown parameter(s): {sorted(unknown)}")

    try:
        limit = min(max(int(params.get("limit", 50)), 1), 500)
        offset = max(int(params.get("offset", 0)), 0)
    except ValueError:
        raise HTTPException(status_code=400, detail="limit/offset must be integers")
    sort_by = params.get("sort_by", "overall")
    if sort_by not in sortable:
        raise HTTPException(status_code=400, detail=f"sort_by must be one of {sorted(sortable)}")
    order = params.get("order", "desc").lower()
    if order not in ("asc", "desc"):
        raise HTTPException(status_code=400, detail="order must be asc or desc")

    db = get_db()
    try:
        query = db.query(model, Stock).join(Stock, Stock.id == model.stock_id).filter(Stock.is_active.is_(True))

        for key in range_params & set(params):
            bound, field = key.split("_", 1)
            try:
                value = float(params[key])
            except ValueError:
                raise HTTPException(status_code=400, detail=f"{key} must be a number")
            column = getattr(model, field)
            query = query.filter(column >= value if bound == "min" else column <= value)

        if params.get("sector"):
            query = query.filter(Stock.sector == params["sector"])
        if params.get("macro_sector"):
            query = query.filter(Stock.macro_sector == params["macro_sector"])
        if params.get("rating"):
            query = query.filter(model.overall_rating == params["rating"].upper())
        if params.get("valuation_view"):
            query = query.filter(model.valuation_view == params["valuation_view"].upper())
        if params.get("q"):
            like = f"%{params['q'].strip()}%"
            query = query.filter(Stock.company_name.ilike(like) | Stock.symbol.ilike(like))
        if params.get("ipo_only", "").lower() in ("1", "true"):
            query = query.filter(Stock.ipo_listing_date.isnot(None))
        if params.get("ipo_since"):
            # Implies ipo_only — a listing-date cutoff only makes sense
            # among IPO stocks, and "entered after this date" is exactly
            # what the frontend's date filter means (same column, just a
            # user-chosen cutoff instead of "any listing date at all").
            try:
                since = date.fromisoformat(params["ipo_since"])
            except ValueError:
                raise HTTPException(status_code=400, detail="ipo_since must be YYYY-MM-DD")
            query = query.filter(Stock.ipo_listing_date >= since)

        total = query.count()
        sort_column = {
            "company_name": Stock.company_name, "market_cap": Stock.market_cap,
            "ipo_listing_date": Stock.ipo_listing_date,
        }.get(sort_by) or getattr(model, sort_by)
        direction = asc if order == "asc" else desc
        ordering = [direction(sort_column).nulls_last(), Stock.symbol]
        if params.get("q"):
            # A search puts the stock whose symbol was typed first, then symbols and names
            # starting with it, then looser matches; the chosen sort applies within each group.
            term = params["q"].strip()
            ordering.insert(0, case(
                (func.lower(Stock.symbol) == term.lower(), 0),
                (Stock.symbol.ilike(f"{term}%"), 1),
                (Stock.company_name.ilike(f"{term}%"), 2),
                else_=3,
            ))
        rows = query.order_by(*ordering).offset(offset).limit(limit).all()

        return {"total": total, "limit": limit, "offset": offset, "results": [_row_dict(s, st) for s, st in rows]}
    finally:
        db.close()
