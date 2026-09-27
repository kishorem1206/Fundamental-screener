"""Keeps `fa_company_scores` (one latest-score row per company) in sync with
completed analyses — see `CompanyScore`'s docstring for why the table exists.
Called from the pipeline right after the final (refined) scores are saved,
and from `scripts/backfill_company_scores.py` for analyses that predate it.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.infrastructure.database import metric_store
from app.infrastructure.database.models import CompanyScore, FundamentalAnalysis

SCORE_FIELDS = ("overall", "growth", "profitability", "cash_flow", "balance_sheet", "efficiency", "valuation")


def _latest_quarter_end(db: Session, stock_id: str) -> date | None:
    """Newest reported quarter in the ledger (`qtr_sales`, either statement
    type; TTM excluded) — the freshness marker stored beside the scores."""
    rows = metric_store.get_metric_history(db, stock_id, "qtr_sales", statement_type=None)
    latest: date | None = None
    for r in rows:
        try:
            d = date.fromisoformat(r.period)
        except ValueError:
            continue
        if latest is None or d > latest:
            latest = d
    return latest


def upsert_company_score(
    db: Session, analysis: FundamentalAnalysis, scored_at: datetime | None = None,
) -> CompanyScore | None:
    """Writes `analysis.scores` into the company's row, creating it if
    needed. Returns None (and writes nothing) when the analysis has no
    scores, or when the stored row was scored LATER than this analysis —
    a stale analysis must never overwrite fresher numbers. Does not commit."""
    scores = analysis.scores or {}
    if scores.get("overall") is None:
        return None

    scored_at = scored_at or datetime.now(timezone.utc)
    row = db.query(CompanyScore).filter_by(stock_id=analysis.stock_id).first()
    if row is not None and row.scored_at is not None and row.scored_at > scored_at:
        return None

    now = datetime.now(timezone.utc)
    if row is None:
        row = CompanyScore(id=str(uuid.uuid4()), stock_id=analysis.stock_id, created_at=now)
        db.add(row)

    for field in SCORE_FIELDS:
        setattr(row, field, scores.get(field))
    row.analysis_id = analysis.id
    row.overall_rating = scores.get("overall_rating")
    row.valuation_view = scores.get("valuation_view")
    row.weights = scores.get("weights")
    row.red_flags = scores.get("red_flags")
    row.confidence_score = analysis.confidence_score
    row.scored_at = scored_at
    row.latest_quarter_end = _latest_quarter_end(db, analysis.stock_id)
    row.updated_at = now
    db.flush()
    return row
