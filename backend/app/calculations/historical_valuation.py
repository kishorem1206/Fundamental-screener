"""Historical valuation position — Architecture v2 Stage 4.

Answers "is the current P/E expensive relative to THIS COMPANY's own
history," not just an absolute cutoff — the gap Architecture v2
chatgpt.md's source doc emphasizes most heavily (section 13). Pure
deterministic statistics over app/ingestion/valuation_history_client.py's
stored rows; the LLM layer explains this, it doesn't compute it, per the
doc's System A/B/C separation (section 20).
"""
from __future__ import annotations

import statistics

from sqlalchemy.orm import Session

from app.infrastructure.database.models import ValuationHistory

# Premium/discount beyond this many percentage points from the historical
# median is labeled EXPENSIVE/CHEAP rather than FAIR. Symmetric, deliberately
# simple — a company-specific band would need more history than most stocks
# here have yet.
_BAND_PCT = 15.0


def _percentile_rank(value: float, population: list[float]) -> float:
    """% of `population` at or below `value` — 100 means the current value
    is the highest ever seen, 0 means the lowest."""
    if not population:
        return 50.0
    below_or_equal = sum(1 for v in population if v <= value)
    return round(below_or_equal / len(population) * 100, 1)


def _position(current: float, median: float) -> tuple[float, str]:
    premium_pct = round((current - median) / median * 100, 1) if median else 0.0
    if premium_pct > _BAND_PCT:
        label = "EXPENSIVE"
    elif premium_pct < -_BAND_PCT:
        label = "CHEAP"
    else:
        label = "FAIR"
    return premium_pct, label


def compute_valuation_position(
    db: Session, company_id: str, current_pe: float | None, current_pb: float | None = None
) -> dict:
    """Historical P/E and (if available) P/B context for the given current
    values. `years_of_data` tells the caller how much history this is
    actually based on — this is rarely a true "10 years" (see
    valuation_history_client.py's module docstring on yfinance's shallow
    EPS depth for Indian stocks), so every result states its own depth
    rather than implying a fixed window."""
    rows = (
        db.query(ValuationHistory)
        .filter_by(company_id=company_id)
        .order_by(ValuationHistory.period_end)
        .all()
    )

    pe_history = [float(r.pe) for r in rows if r.pe is not None]
    pb_history = [float(r.pb) for r in rows if r.pb is not None]

    result: dict = {
        "years_of_data": len({r.period_end for r in rows}),
        "pe": None,
        "pb": None,
    }

    if current_pe is not None and pe_history:
        median_pe = round(statistics.median(pe_history), 2)
        premium_pct, position = _position(current_pe, median_pe)
        result["pe"] = {
            "current": round(current_pe, 2),
            "median": median_pe,
            "min": round(min(pe_history), 2),
            "max": round(max(pe_history), 2),
            "percentile": _percentile_rank(current_pe, pe_history),
            "premium_to_median_pct": premium_pct,
            "position": position,
            "sample_size": len(pe_history),
        }

    if current_pb is not None and pb_history:
        median_pb = round(statistics.median(pb_history), 2)
        premium_pct, position = _position(current_pb, median_pb)
        result["pb"] = {
            "current": round(current_pb, 2),
            "median": median_pb,
            "min": round(min(pb_history), 2),
            "max": round(max(pb_history), 2),
            "percentile": _percentile_rank(current_pb, pb_history),
            "premium_to_median_pct": premium_pct,
            "position": position,
            "sample_size": len(pb_history),
        }

    return result
