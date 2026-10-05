"""Read-only browse of the raw NSE IPO issue archive (`fa_ipo_issues`) —
company name, price band, issue dates, listing date, and (once promoted)
the linked `stock_id`. Mainboard-only by default since that's the only
subset this app actually analyses (see nse_ipo_client.py's module
docstring); pass `all_types=true` to see SME/debt/InvIT/REIT rows too.

    GET /api/ipo-issues?since=2025-01-01&limit=50
"""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, Request

from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import IPOIssue
from app.ingestion.nse_ipo_client import MAINBOARD_SECURITY_TYPES

router = APIRouter(prefix="/api/ipo-issues")


def _row(issue: IPOIssue) -> dict:
    return {
        "id": issue.id,
        "company_name": issue.company_name,
        "symbol": issue.symbol,
        "security_type": issue.security_type,
        "issue_price": float(issue.issue_price) if issue.issue_price is not None else None,
        "price_range_low": float(issue.price_range_low) if issue.price_range_low is not None else None,
        "price_range_high": float(issue.price_range_high) if issue.price_range_high is not None else None,
        "issue_start_date": issue.issue_start_date.isoformat() if issue.issue_start_date else None,
        "issue_end_date": issue.issue_end_date.isoformat() if issue.issue_end_date else None,
        "listing_date": issue.listing_date.isoformat() if issue.listing_date else None,
        "status": issue.status,
        "stock_id": issue.stock_id,
    }


@router.get("")
def list_ipo_issues(request: Request):
    params = dict(request.query_params)
    unknown = set(params) - {"q", "since", "all_types", "listed_only", "limit", "offset"}
    if unknown:
        raise HTTPException(status_code=400, detail=f"Unknown parameter(s): {sorted(unknown)}")

    try:
        limit = min(max(int(params.get("limit", 100)), 1), 500)
        offset = max(int(params.get("offset", 0)), 0)
    except ValueError:
        raise HTTPException(status_code=400, detail="limit/offset must be integers")

    db = get_db()
    try:
        query = db.query(IPOIssue)
        if params.get("all_types", "").lower() not in ("1", "true"):
            query = query.filter(IPOIssue.security_type.in_(MAINBOARD_SECURITY_TYPES))
        if params.get("since"):
            try:
                since = date.fromisoformat(params["since"])
            except ValueError:
                raise HTTPException(status_code=400, detail="since must be YYYY-MM-DD")
            query = query.filter(IPOIssue.issue_start_date >= since)
        if params.get("listed_only", "").lower() in ("1", "true"):
            query = query.filter(IPOIssue.listing_date.isnot(None))
        if params.get("q"):
            like = f"%{params['q'].strip()}%"
            query = query.filter(IPOIssue.company_name.ilike(like) | IPOIssue.symbol.ilike(like))

        total = query.count()
        rows = (
            query.order_by(IPOIssue.issue_start_date.desc().nulls_last())
            .offset(offset).limit(limit).all()
        )
        return {"total": total, "limit": limit, "offset": offset, "results": [_row(r) for r in rows]}
    finally:
        db.close()
