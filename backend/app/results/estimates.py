"""Expected earnings for stocks about to report, from Yahoo Finance.

Yahoo's "0q" row is the quarter not yet reported: its year-ago EPS matches Screener's
figure for the same quarter last year (checked on Divi's, Apollo Hospitals, Astral,
Bosch and Afcons, October 2026). Yahoo writes 0 for a value it does not have, and its
figures are analysts' consensus, so this is shown and never scored. An estimate
stops changing once the meeting has passed, so it stays what was expected beforehand.

    cd backend && .venv/bin/python -m app.results.estimates [--days 14]
"""
from __future__ import annotations

import argparse
import time
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import ResultsCalendar, Stock

_PACE = 0.7
_CRORE = 1e7
HORIZON_DAYS = 14


def _positive(v) -> float | None:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if x == x and x != 0 else None


def _count(v) -> int | None:
    x = _positive(v)
    return int(x) if x else None


def _crore(v) -> float | None:
    x = _positive(v)
    return round(x / _CRORE, 2) if x else None


def parse(eps: dict | None, revenue: dict | None) -> dict:
    """`eps`, `revenue`: Yahoo's "0q" rows."""
    e, r = eps or {}, revenue or {}
    return {"eps_estimate": _positive(e.get("avg")), "eps_low": _positive(e.get("low")), "eps_high": _positive(e.get("high")),
            "eps_year_ago": _positive(e.get("yearAgoEps")), "eps_analysts": _count(e.get("numberOfAnalysts")),
            "revenue_estimate_cr": _crore(r.get("avg")), "revenue_year_ago_cr": _crore(r.get("yearAgoRevenue")), "revenue_analysts": _count(r.get("numberOfAnalysts"))}


def _row(df) -> dict | None:
    return df.loc["0q"].to_dict() if df is not None and not getattr(df, "empty", True) and "0q" in df.index else None


def read_one(symbol: str) -> dict:
    import yfinance as yf

    t = yf.Ticker(f"{symbol}.NS")
    return parse(_row(t.earnings_estimate), _row(t.revenue_estimate))


def refresh(db: Session, days: int = HORIZON_DAYS, log=print) -> dict:
    """Every stock reporting from today to `days` ahead. Never raises."""
    today = date.today()
    rows = (db.query(ResultsCalendar, Stock.symbol).join(Stock, Stock.id == ResultsCalendar.stock_id)
            .filter(ResultsCalendar.board_date >= today, ResultsCalendar.board_date <= today + timedelta(days=days)).all())
    found = failed = 0
    for i, (row, symbol) in enumerate(rows, 1):
        if row.estimate_on == today:
            continue
        time.sleep(_PACE)
        try:
            values = read_one(symbol)
        except Exception as exc:  # noqa: BLE001
            failed += 1
            if "too many" in str(exc).lower():
                time.sleep(90)
            continue
        for k, v in values.items():
            setattr(row, k, v)
        row.estimate_on = today
        db.commit()
        found += values["eps_estimate"] is not None or values["revenue_estimate_cr"] is not None
        if i % 100 == 0:
            log(f"  ...{i}/{len(rows)}, {found} with estimates")
    return {"meetings": len(rows), "with_estimates": found, "failed": failed}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--days", type=int, default=HORIZON_DAYS)
    a = ap.parse_args()
    db = get_db()
    try:
        print("ESTIMATES:", refresh(db, a.days, log=lambda m: print(m, flush=True)), flush=True)
    finally:
        db.close()


if __name__ == "__main__":
    main()
