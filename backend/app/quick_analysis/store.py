"""Persistence for quick-analysis scores -> `fa_quick_scores` (never
`fa_company_scores`, which holds full-pipeline scores; the two are kept apart
on purpose)."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.infrastructure.database.models import QuickScore as QuickScoreRow
from app.quick_analysis.scorer import QuickScore

METHOD_VERSION = "quick-v1"
SCORE_FIELDS = ("overall", "growth", "profitability", "cash_flow", "balance_sheet", "efficiency", "valuation")


def upsert_quick_score(db: Session, stock_id: str, result: QuickScore, scored_at: datetime | None = None) -> QuickScoreRow | None:
    """Writes the approximated-refinement scores (the recommended quick score)
    for one company, updating its single row in place with the new date.
    Returns None and writes nothing for a failed/empty result. Commits."""
    if result.error or not result.refined:
        return None
    now = datetime.now(timezone.utc)
    row = db.query(QuickScoreRow).filter_by(stock_id=stock_id).first()
    if row is None:
        row = QuickScoreRow(id=str(uuid.uuid4()), stock_id=stock_id, created_at=now)
        db.add(row)
    scores = result.refined
    for field in SCORE_FIELDS:
        setattr(row, field, scores.get(field))
    # The two components blended into `growth` (see scoring.py's
    # `_growth_score()`) — `growth_quarterly` is None when too few Yahoo
    # quarters were on record, same fallback contract as the field itself.
    row.growth_annual = scores.get("growth_annual")
    row.growth_quarterly = scores.get("growth_quarterly")
    row.sector_framework = result.sector_framework
    row.overall_rating = scores.get("overall_rating")
    row.valuation_view = scores.get("valuation_view")
    row.weights = scores.get("weights")
    row.red_flags = scores.get("red_flags")
    row.refinement = scores.get("refinement")
    row.latest_fy = result.metrics.get("latest_fy")
    row.method_version = METHOD_VERSION
    row.scored_at = scored_at or now
    row.updated_at = now
    db.commit()
    return row


def recently_scored_ids(db: Session, max_age_days: float) -> set[str]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    return {sid for (sid,) in db.query(QuickScoreRow.stock_id).filter(QuickScoreRow.scored_at >= cutoff)}
