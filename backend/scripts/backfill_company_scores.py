"""One-off/idempotent backfill of `fa_company_scores` from every company's
latest COMPLETED analysis (the pipeline maintains the table itself from now
on). Safe to re-run: a row is only overwritten by a newer analysis.

    cd backend && .venv/bin/python scripts/backfill_company_scores.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.infrastructure.database.client import get_db  # noqa: E402
from app.infrastructure.database.models import FundamentalAnalysis  # noqa: E402
from app.services.company_scores import upsert_company_score  # noqa: E402


def main() -> None:
    db = get_db()
    try:
        analyses = (
            db.query(FundamentalAnalysis)
            .filter(FundamentalAnalysis.status == "COMPLETED")
            .order_by(FundamentalAnalysis.stock_id, FundamentalAnalysis.created_at.desc())
            .all()
        )
        seen: set[str] = set()
        written = skipped = 0
        for a in analyses:
            if a.stock_id in seen:
                continue
            seen.add(a.stock_id)
            row = upsert_company_score(db, a, scored_at=a.completed_at or a.created_at)
            if row is None:
                skipped += 1
            else:
                written += 1
        db.commit()
        print(f"companies: {len(seen)} | written: {written} | skipped (no scores / stale): {skipped}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
