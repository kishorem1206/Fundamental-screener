"""Price statistics from the stored daily history (app/prices/).

Every return is computed from the dividend- and split-adjusted close; every
index figure from NSE's own daily index file. Windows are calendar based: the
last bar on or before 30, 91, 182 and 365 days before the as-of date.
"""
from __future__ import annotations

import math
import statistics
from datetime import date, timedelta
from functools import lru_cache

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.prices import store

WINDOWS = {"1M": 30, "3M": 91, "6M": 182, "1Y": 365}
TRADING_DAYS = 252


def as_of(db: Session) -> date | None:
    return db.execute(text("select max(bar_date) from index_bars_daily where index_name = 'Nifty 50'")).scalar()


def _window_return(series: list[tuple[date, float]], end: date, days: int) -> float | None:
    """None when the series does not reach back to the window start (listed later)."""
    start_day = end - timedelta(days=days)
    if not series or series[0][0] > start_day:
        return None
    last = [v for d, v in series if d <= end]
    start = [v for d, v in series if d <= start_day]
    if not last or not start or start[-1] <= 0:
        return None
    return (last[-1] / start[-1] - 1) * 100


def window_returns(series: list[tuple[date, float]], end: date) -> dict[str, float | None]:
    return {k: _window_return(series, end, d) for k, d in WINDOWS.items()}


def max_drawdown(series: list[tuple[date, float]]) -> tuple[float | None, date | None, date | None]:
    """Largest peak-to-trough fall in %, with its peak and trough dates."""
    if len(series) < 2:
        return None, None, None
    peak_v, peak_d = series[0][1], series[0][0]
    worst, worst_peak, worst_trough = 0.0, None, None
    for d, v in series:
        if v > peak_v:
            peak_v, peak_d = v, d
        fall = (v / peak_v - 1) * 100
        if fall < worst:
            worst, worst_peak, worst_trough = fall, peak_d, d
    return worst, worst_peak, worst_trough


def volatility(series: list[tuple[date, float]]) -> float | None:
    """Annualised standard deviation of daily returns, in %."""
    if len(series) < 60:
        return None
    rets = [b / a - 1 for (_, a), (_, b) in zip(series, series[1:]) if a > 0]
    return statistics.pstdev(rets) * math.sqrt(TRADING_DAYS) * 100


def stock_year(db: Session, stock_id: str, end: date) -> list[tuple[date, float]]:
    return [(d, v) for d, v in store.closes(db, stock_id, since=end - timedelta(days=372)) if d <= end]


@lru_cache(maxsize=64)
def _index_year_cached(index_name: str, end: date) -> tuple:
    from app.infrastructure.database.client import get_db

    db = get_db()
    try:
        return tuple((d, v) for d, v in store.index_closes(db, index_name, since=end - timedelta(days=372)) if d <= end)
    finally:
        db.close()


def index_year(index_name: str, end: date) -> list[tuple[date, float]]:
    return list(_index_year_cached(index_name, end))


@lru_cache(maxsize=4)
def _universe_returns(end: date) -> dict[str, dict[str, float]]:
    """{stock_id: {window: return %}} for every stored stock — one query per
    window, cached for the as-of date, so sector medians and percentiles cost
    nothing per stock."""
    from app.infrastructure.database.client import get_db

    db = get_db()
    try:
        def closes_at(day: date) -> dict[str, tuple[date, float]]:
            rows = db.execute(text(
                "select distinct on (stock_id) stock_id, bar_date, adj_close from price_bars_daily "
                "where bar_date <= :d and bar_date > :floor order by stock_id, bar_date desc"),
                {"d": day, "floor": day - timedelta(days=10)})
            return {sid: (d, float(v)) for sid, d, v in rows}

        first = dict(db.execute(text("select stock_id, min(bar_date) from price_bars_daily group by stock_id")).all())
        latest = closes_at(end)
        out: dict[str, dict[str, float]] = {sid: {} for sid in latest}
        for name, days in WINDOWS.items():
            start_day = end - timedelta(days=days)
            for sid, (_, v0) in closes_at(start_day).items():
                if sid in latest and first.get(sid) and first[sid] <= start_day and v0 > 0:
                    out[sid][name] = (latest[sid][1] / v0 - 1) * 100
        return out
    finally:
        db.close()


def universe_returns(end: date) -> dict[str, dict[str, float]]:
    return _universe_returns(end)


def excess(stock_ret: float | None, bench_ret: float | None) -> float | None:
    """Return over the benchmark, compounded: +10 means 10% better than the benchmark."""
    if stock_ret is None or bench_ret is None:
        return None
    return ((1 + stock_ret / 100) / (1 + bench_ret / 100) - 1) * 100
