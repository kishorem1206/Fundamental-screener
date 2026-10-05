"""`fw_scores`: one row per stock, per day, per basis. A re-run on the same day
updates that day's row; an earlier day's row is never touched, so the history
Quality Momentum needs builds up on its own."""
from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.infrastructure.database.models import FrameworkScore

QUICK, FULL = "QUICK", "FULL"


def save(db: Session, stock_id: str, basis: str, columns: dict, detail: dict, as_of: date | None = None) -> FrameworkScore:
    """Sets the given score columns and merges `detail` (keyed by score name)
    into the row for this stock, day and basis. Does not commit."""
    as_of = as_of or date.today()
    row = db.get(FrameworkScore, (stock_id, as_of, basis))
    if row is None:
        row = FrameworkScore(stock_id=stock_id, as_of=as_of, basis=basis, detail={}, reconstructed=False,
                             computed_at=datetime.now(timezone.utc))
        db.add(row)
    for name, value in columns.items():
        setattr(row, name, value)
    row.detail = {**(row.detail or {}), **detail}
    row.computed_at = datetime.now(timezone.utc)
    db.flush()
    return row


def latest(db: Session, stock_id: str) -> FrameworkScore | None:
    """Newest row for a stock; on the same day a FULL row is preferred to QUICK.
    The same rule as latest_for_all(), so the table and the detail view agree."""
    rows = (db.query(FrameworkScore).filter(FrameworkScore.stock_id == stock_id)
            .order_by(FrameworkScore.as_of.desc()).limit(2).all())
    if not rows:
        return None
    same_day = [r for r in rows if r.as_of == rows[0].as_of]
    return next((r for r in same_day if r.basis == FULL), same_day[0])


def latest_for_all(db: Session) -> list[FrameworkScore]:
    newest = (db.query(FrameworkScore.stock_id, func.max(FrameworkScore.as_of).label("as_of"))
              .group_by(FrameworkScore.stock_id).subquery())
    rows = (db.query(FrameworkScore)
            .join(newest, (FrameworkScore.stock_id == newest.c.stock_id) & (FrameworkScore.as_of == newest.c.as_of)).all())
    best: dict[str, FrameworkScore] = {}
    for r in rows:
        if r.stock_id not in best or r.basis == FULL:
            best[r.stock_id] = r
    return list(best.values())
