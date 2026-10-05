"""Promoter-governance signal folded into score refinement (2026-09-28,
explicit user request — the app ingested promoter holding %, pledge %, and
even ran a deterministic event detector for it (`PROMOTER_HOLDING_DECLINE`,
`PLEDGE_PRESENT`, `PLEDGE_INCREASE` — see `app/ingestion/
shareholding_client.py::_detect_events()`), but none of it ever touched a
score; it only ever reached a report/dashboard read-only view
(`app/routes/governance.py`)).

This module reads what that ingestion already wrote — it never scrapes
NSE itself. `ingest_shareholding()` already runs unconditionally for every
company, every sector, in the full pipeline's orchestrator, so by the time
score_refinement's stage runs, `governance_events` is already populated
(or empty, if NSE genuinely had nothing).

Unlike the P&L/balance-sheet/cash-flow intelligence proxies (each of which
replaces/refines one existing `scoring.py` category by design — see
`score_refinement.py`'s own docstring), promoter governance isn't a
dimension `compute_scores()` measures at all. There's no natural "base
score" for it to blend toward, so this is applied as a direct, bounded
PENALTY on `overall` after the category-level blends, not another
bounded-blend category refinement — see `apply_score_refinement()`.

"Current state", not "any flag ever raised": `_detect_events()` re-emits a
PLEDGE_PRESENT event for every quarter pledge remains > 0 (one row per
quarter, deduped by event_date), so the MOST RECENT event of each type
reflects the CURRENT governance state. `_LOOKBACK_DAYS` additionally
excludes events that have aged out — a pledge released or a promoter-
holding decline from years ago shouldn't permanently tax a company's score
just because the row is still in the table.
"""
from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.infrastructure.database.models import GovernanceEvent, Shareholding

# Roughly 15 months — covers one missed/delayed quarterly filing without
# falsely clearing a still-live pledge or decline.
_LOOKBACK_DAYS = 460

# Points subtracted from `overall`, keyed by event_type then severity (the
# severities `_detect_events()` already assigns — reused as-is, not
# re-derived, so this module never disagrees with the detector about how
# bad a given pledge %/decline is). PLEDGE_INCREASE stacks on top of
# PLEDGE_PRESENT (a worsening trend is worse than a static pledge at the
# same level), PROMOTER_HOLDING_DECLINE stacks on top of both (an
# orthogonal signal — a promoter can be both pledging and selling down).
_SEVERITY_PENALTY = {
    "PROMOTER_HOLDING_DECLINE": {"HIGH": 6.0, "MEDIUM": 3.0},
    "PLEDGE_PRESENT": {"HIGH": 8.0, "MEDIUM": 4.0, "LOW": 1.5},
    "PLEDGE_INCREASE": {"HIGH": 4.0, "MEDIUM": 2.0, "LOW": 1.0},
}
_MAX_PENALTY = 20.0


def clamp_score(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def compute_governance_penalty(db: Session, company_id: str) -> dict | None:
    """`None` when this company has no shareholding data ingested at all
    yet (ingestion hasn't run, or NSE had nothing) — absence of data is
    never treated as a clean 0-penalty result. Once shareholding data
    exists, a genuinely clean record (no adverse events in the lookback
    window) correctly returns `penalty=0.0`, `flags=[]`."""
    has_data = db.query(Shareholding.id).filter_by(company_id=company_id).first() is not None
    if not has_data:
        return None

    cutoff = (date.today() - timedelta(days=_LOOKBACK_DAYS)).isoformat()
    rows = (
        db.query(GovernanceEvent)
        .filter(GovernanceEvent.company_id == company_id, GovernanceEvent.event_date >= cutoff)
        .order_by(GovernanceEvent.event_date.desc())
        .all()
    )
    latest_by_type: dict[str, GovernanceEvent] = {}
    for row in rows:
        latest_by_type.setdefault(row.event_type, row)  # rows are DESC -> first seen per type is the most recent

    penalty = 0.0
    flags: list[dict] = []
    for event_type, row in latest_by_type.items():
        pts = _SEVERITY_PENALTY.get(event_type, {}).get(row.severity, 0.0)
        if pts:
            penalty += pts
            flags.append({
                "event_type": event_type, "severity": row.severity,
                "event_date": row.event_date, "description": row.description,
            })

    return {"penalty": round(min(_MAX_PENALTY, penalty), 2), "flags": flags}
