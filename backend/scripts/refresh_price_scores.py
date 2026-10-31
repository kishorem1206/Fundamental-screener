"""Refresh the scores that move with price, Relative Strength and Technical, on
every stock's latest row from stored prices (no Screener reads, nothing else
touched), then refresh decisions. Run daily: a stock's other scores change only
when it reports, but these change every day.

    cd backend && .venv/bin/python -m scripts.refresh_price_scores
"""
from __future__ import annotations

from app.framework import price_stats, store
from app.framework.decisions import refresh_all
from app.framework.relative_strength import compute_relative_strength, why_holding_up
from app.framework.technical import compute_technical
from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import Stock


def main() -> None:
    db = get_db()
    try:
        active = {s.id for s in db.query(Stock.id).filter(Stock.is_active.is_(True))}
        rows = [r for r in store.latest_for_all(db) if r.stock_id in active]
        end = price_stats.as_of(db)
        changed = 0
        for i, row in enumerate(rows, 1):
            detail = row.detail or {}
            relative = compute_relative_strength(db, row.stock_id, end)
            holding = why_holding_up(relative, detail.get("fundamental") or {}, detail.get("quantitative") or {}, detail.get("business_quality") or {})
            if holding:
                relative["why_holding_up"] = holding
            before = float(row.relative_strength) if row.relative_strength is not None else None
            row.relative_strength = relative["score"]
            technical = compute_technical(db, row.stock_id, end)
            row.technical = technical["score"]
            row.detail = {**detail, "relative_strength": relative, "technical": technical}
            changed += before != relative["score"]
            if i % 200 == 0:
                db.commit()
                print(f"  ...{i}/{len(rows)} ({changed} changed)", flush=True)
        db.commit()
        print(f"PRICE SCORES: {len(rows)} stocks, {changed} Relative Strength scores changed", flush=True)
        print("DECISIONS:", refresh_all(db), flush=True)
    finally:
        db.close()


if __name__ == "__main__":
    main()
