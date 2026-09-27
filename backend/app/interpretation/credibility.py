"""Guidance consistency + promise tracking — Concall Intelligence System,
Stage C4. Pure deterministic Python, no LLM anywhere in this file.

`compute_credibility` is a real, honest first layer: it aggregates the
`status` history Stage C3 already computed (NEW/REITERATED/UPGRADED/
DOWNGRADED) per company+metric. It is NOT the source doc's full "hit rate
vs actual reported results" — that needs a metric-name mapping bridge to
real subsequent P&L figures (app/calculations/pnl_engine.py) that doesn't
exist yet, deliberately left as future work rather than approximated with
something that would look more authoritative than it is.

`sync_promises` converts already-extracted qualitative guidance rows into
`ManagementPromise` rows — no new LLM call. Verifying a promise against
what actually happened is also future work (same reason).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.infrastructure.database.models import ManagementCredibility, ManagementGuidance, ManagementPromise


def compute_credibility(db: Session, company_id: str) -> list[ManagementCredibility]:
    """Recomputes the per-metric consistency summary for one company from
    every ManagementGuidance row on record. Upserts — safe to re-run after
    new transcripts are processed."""
    rows = db.query(ManagementGuidance).filter_by(company_id=company_id).order_by(ManagementGuidance.retrieved_at).all()

    by_metric: dict[str, list[ManagementGuidance]] = {}
    for r in rows:
        by_metric.setdefault(r.metric, []).append(r)

    now = datetime.now(timezone.utc)
    results = []
    for metric, items in by_metric.items():
        counts = {"NEW": 0, "REITERATED": 0, "UPGRADED": 0, "DOWNGRADED": 0}
        for item in items:
            counts[item.status] = counts.get(item.status, 0) + 1

        existing = db.query(ManagementCredibility).filter_by(company_id=company_id, metric=metric).first()
        fields = dict(
            guidance_count=len(items), upgraded_count=counts.get("UPGRADED", 0),
            downgraded_count=counts.get("DOWNGRADED", 0), reiterated_count=counts.get("REITERATED", 0),
            new_count=counts.get("NEW", 0), last_status=items[-1].status, last_updated=now,
        )
        if existing:
            for k, v in fields.items():
                setattr(existing, k, v)
            results.append(existing)
        else:
            row = ManagementCredibility(id=str(uuid.uuid4()), company_id=company_id, metric=metric, **fields)
            db.add(row)
            results.append(row)

    db.flush()
    return results


def sync_promises(db: Session, transcript_id: str) -> list[ManagementPromise]:
    """One ManagementPromise per qualitative ManagementGuidance row from
    this transcript that doesn't already have one. Never raises."""
    qualitative = (
        db.query(ManagementGuidance)
        .filter_by(transcript_id=transcript_id, guidance_type="qualitative")
        .all()
    )
    existing_ids = {
        row[0] for row in db.query(ManagementPromise.guidance_id)
        .filter(ManagementPromise.guidance_id.in_([g.id for g in qualitative]))
        .all()
    } if qualitative else set()

    now = datetime.now(timezone.utc)
    stored = []
    for g in qualitative:
        if g.id in existing_ids:
            continue
        row = ManagementPromise(
            id=str(uuid.uuid4()), company_id=g.company_id, guidance_id=g.id,
            promise=g.statement, category=g.category, target_date=g.period,
            status="PENDING", retrieved_at=now,
        )
        db.add(row)
        stored.append(row)

    db.flush()
    return stored
