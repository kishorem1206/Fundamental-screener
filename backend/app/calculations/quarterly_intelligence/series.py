"""Reads `qtr_*` ledger rows into {period: value} series — same pattern as
`pl_intelligence/cascade.py::_series()`, pointed at the quarterly namespace.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.infrastructure.database import metric_store

_VALID_STATEMENT_TYPES = {"STANDALONE", "CONSOLIDATED"}


def quarter_series(db: Session, company_id: str, metric_key: str, statement_type: str) -> dict[str, float]:
    """{period: authoritative_value}, sorted-friendly (dict keys are ISO
    dates, `sorted()` on them is chronological). `statement_type` has no
    default, same enforcement as `pl_intelligence/cascade.py::_series()`."""
    if statement_type not in _VALID_STATEMENT_TYPES:
        raise ValueError(f"statement_type must be one of {_VALID_STATEMENT_TYPES}, got {statement_type!r}")
    history = metric_store.get_metric_history(db, company_id, metric_key, statement_type=statement_type)
    periods = sorted({row.period for row in history if row.period != "TTM"})
    out: dict[str, float] = {}
    for period in periods:
        winner, _ = metric_store.get_authoritative_value(db, company_id, metric_key, period, statement_type=statement_type)
        if winner is not None and winner.value is not None:
            out[period] = float(winner.value)
    return out
