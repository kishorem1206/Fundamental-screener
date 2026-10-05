"""Other-income-dependency signal for quick analysis (2026-09-28, explicit
user request — surfaced by I S T Limited: Other Income was 78-88% of PBT
across its last 3 reported quarters, meaning reported profit was
overwhelmingly non-core, something Yahoo-derived pat_margin/ROE/ROCE never
distinguish from real operating profit at all — `approx.py`'s own docstring
already flagged profitability as "NOT derivable" from Yahoo for exactly
this reason).

"Find what this other income is": Screener's P&L (quarterly OR annual)
reports Other Income as ONE aggregate line — the same structural limit
`pl_intelligence/earnings_quality.py`'s own docstring documents for the
full pipeline ("dividend/interest/investment-gains/capital-gains/
exceptional sub-buckets cannot be separated from what this app ingests").
That's a real, honest ceiling on "what it is" — this module answers "how
much of it" instead (the ratio to PBT), which is what's actually
computable and what drives the flag/score adjustment.

DB-first, ingest-on-miss — its OWN trigger, independent of whether
`screener_quarterly_fallback.py`'s quarterly-growth fallback ran this same
call. Real gap found live: I S T Limited's Yahoo quarterly data is
perfectly sufficient for growth scoring (5 real quarters, no gap), so that
fallback never fires and `qtr_other_income`/`qtr_pbt` never land in the
ledger as a side effect — yet ISTLTD is exactly the company this feature
exists for. So this reads the ledger first (quarterly `qtr_other_income`/
`qtr_pbt` preferred, else the latest annual `pnl_other_income`/`pnl_pbt`
from a prior full analysis), and on a genuine miss calls the same
`quarterly_results_client.py::ingest_quarterly_results()` the growth
fallback uses, then re-reads. A repeat scan of the same company finds the
ledger already populated (by either this check or the growth fallback,
whichever ran first) and never re-fetches. Still returns None (no ingest
retried a third time) if Screener has nothing either.

Reuses `quarterly_intelligence/flags.py`'s own threshold
(`_OTHER_INCOME_DEPENDENCY_RATIO`, other_income/PBT >= 25%) for consistency
with the full pipeline's identical concept.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.calculations.quarterly_intelligence.flags import _OTHER_INCOME_DEPENDENCY_RATIO
from app.infrastructure.database import metric_store
from app.logger import logger

# Ratio -> profitability proxy score (0-100), same spirit as
# `pl_intelligence/scoring.py::score_m4_eqi()`'s EQI bands, but keyed off
# this module's other_income/PBT ratio directly (not EQI's revenue-basis
# ratio — a different, PBT-facing question: "how much of REPORTED PROFIT,
# not income, is non-core").
_RATIO_SCORE_BANDS = ((0.10, 90.0), (0.25, 70.0), (0.50, 40.0), (0.75, 20.0))
_SEVERE_SCORE = 10.0


def _score_for_ratio(ratio: float) -> float:
    for threshold, score in _RATIO_SCORE_BANDS:
        if ratio < threshold:
            return score
    return _SEVERE_SCORE


def _read_from_ledger(db: Session, company_id: str) -> dict | None:
    for prefix, period_type in (("qtr_", "quarterly"), ("pnl_", "annual")):
        oi_hist = metric_store.get_metric_history(db, company_id, f"{prefix}other_income", statement_type="CONSOLIDATED")
        pbt_hist = metric_store.get_metric_history(db, company_id, f"{prefix}pbt", statement_type="CONSOLIDATED")
        periods = sorted({r.period for r in oi_hist if r.period != "TTM"} & {r.period for r in pbt_hist if r.period != "TTM"})
        if not periods:
            continue
        latest = periods[-1]
        oi_winner, _ = metric_store.get_authoritative_value(db, company_id, f"{prefix}other_income", latest, statement_type="CONSOLIDATED")
        pbt_winner, _ = metric_store.get_authoritative_value(db, company_id, f"{prefix}pbt", latest, statement_type="CONSOLIDATED")
        if oi_winner is None or pbt_winner is None or not pbt_winner.value or not oi_winner.value:
            continue
        oi_val, pbt_val = float(oi_winner.value), float(pbt_winner.value)
        if oi_val <= 0 or pbt_val <= 0:
            continue  # a loss quarter or negative/zero other-income makes this ratio meaningless as a dependency measure
        ratio = oi_val / pbt_val
        return {
            "ratio": round(ratio, 3),
            "period": latest,
            "period_type": period_type,
            "flagged": ratio >= _OTHER_INCOME_DEPENDENCY_RATIO,
            "proxy_score": _score_for_ratio(ratio),
        }
    return None


def compute_other_income_dependency(db: Session, company_id: str, symbol: str, screener_pacer=None) -> dict | None:
    """Public entry point — see module docstring for the ledger-first,
    ingest-on-miss, own-trigger contract. Never raises.

    `screener_pacer` (optional — see `screener_quarterly_fallback.py`'s
    identical parameter, same shared `_Pacer` instance) — this check
    triggers its OWN Screener ingest independently of that other fallback
    (see module docstring), so it needs the same pacing across concurrent
    worker threads."""
    result = _read_from_ledger(db, company_id)
    if result is not None:
        return result

    if screener_pacer is not None:
        screener_pacer.wait_turn()
    try:
        from app.ingestion.quarterly_results_client import ingest_quarterly_results
        ingest_quarterly_results(db, company_id=company_id, symbol=symbol)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning("quick_analysis: other-income ingest failed", symbol=symbol, error=str(e))
        return None

    return _read_from_ledger(db, company_id)
