"""Single DB-reading entry point for this package (mirrors
`balance_sheet_intelligence/snapshot.py`'s role) — every other module here
is a pure function operating on the dicts this module returns, no DB
access of its own.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.calculations.cash_flow_intelligence.canonical_fields import (
    CFF_SCHEDULE_FIELDS,
    CFI_SCHEDULE_FIELDS,
    CFO_SCHEDULE_FIELDS,
    TOP_LEVEL_FIELDS,
)
from app.infrastructure.database import metric_store

_VALID_STATEMENT_TYPES = {"STANDALONE", "CONSOLIDATED"}


def _require_statement_type(statement_type: str) -> None:
    if statement_type not in _VALID_STATEMENT_TYPES:
        raise ValueError(f"statement_type must be one of {_VALID_STATEMENT_TYPES}, got {statement_type!r}")


def _series(db: Session, company_id: str, metric_key: str, statement_type: str) -> dict[str, float]:
    """{period: authoritative_value} — same tier/confidence/recency
    resolution every other ledger reader in this codebase uses."""
    history = metric_store.get_metric_history(db, company_id, metric_key, statement_type=statement_type)
    periods = sorted({row.period for row in history if row.period != "TTM"})
    out: dict[str, float] = {}
    for period in periods:
        winner, _ = metric_store.get_authoritative_value(db, company_id, metric_key, period, statement_type=statement_type)
        if winner is not None and winner.value is not None:
            out[period] = float(winner.value)
    return out


def build_top_level_series(db: Session, company_id: str, statement_type: str) -> dict[str, dict[str, float]]:
    """{canonical_field: {period: value}} for CFO/CFI/CFF/Net/FCF totals.
    `TOP_LEVEL_FIELDS` values are the bare `ingest_cash_flow()` field names
    (e.g. "operating_cash_flow") — that ingestor writes them under a `cf_`
    prefix (`f"cf_{field}"`), so the lookup here must add it back."""
    _require_statement_type(statement_type)
    return {field: _series(db, company_id, f"cf_{key}", statement_type) for field, key in TOP_LEVEL_FIELDS.items()}


def build_cfo_schedule_series(db: Session, company_id: str, statement_type: str) -> dict[str, dict[str, float]]:
    """{canonical_field: {period: value}} for the CFO reconciliation
    schedule (working capital + taxes)."""
    _require_statement_type(statement_type)
    return {
        field: _series(db, company_id, f"cf_sched_op_{suffix}", statement_type)
        for field, suffix in CFO_SCHEDULE_FIELDS.items()
    }


def build_cfi_schedule_series(db: Session, company_id: str, statement_type: str) -> dict[str, dict[str, float]]:
    """{canonical_field: {period: value}} for the CFI breakdown schedule."""
    _require_statement_type(statement_type)
    return {
        field: _series(db, company_id, f"cf_sched_inv_{suffix}", statement_type)
        for field, suffix in CFI_SCHEDULE_FIELDS.items()
    }


def build_cff_schedule_series(db: Session, company_id: str, statement_type: str) -> dict[str, dict[str, float]]:
    """{canonical_field: {period: value}} for the CFF breakdown schedule."""
    _require_statement_type(statement_type)
    return {
        field: _series(db, company_id, f"cf_sched_fin_{suffix}", statement_type)
        for field, suffix in CFF_SCHEDULE_FIELDS.items()
    }


def latest_period(series_by_field: dict[str, dict[str, float]]) -> str | None:
    """Most recent period any field in the group has a value for — used
    when no single "anchor" field (like Balance Sheet's `total_assets`) is
    guaranteed present for every company."""
    all_periods = {p for series in series_by_field.values() for p in series}
    return max(all_periods) if all_periods else None


def period_snapshot(series_by_field: dict[str, dict[str, float]], period: str) -> dict[str, float | None]:
    """{canonical_field: value_at_period} — a flat single-period slice."""
    return {field: values.get(period) for field, values in series_by_field.items()}


def yfinance_cross_check(metrics: dict, screener_value: float | None, yfinance_key: str, period: str | None) -> dict:
    """Compares a Screener-sourced figure against the equivalent
    yfinance-sourced series already exposed by
    `engine.py::MetricsCalculator` (via the persisted `metrics` dict) —
    same "never silently prefer one over the other" discipline as
    `balance_sheet_intelligence/working_capital.py`'s cross-check, just
    inverted here (Screener primary, yfinance the cross-check).

    Uses `yfinance_value_in_crores()`, not `value_at_fiscal_year()` — every
    yfinance-sourced series this package cross-checks against (FCF, cash)
    is an absolute Rupee figure, and `engine.py::MetricsCalculator`'s series
    are raw Rupees while every Screener-sourced figure here is already in
    Crores. Real bug found live-testing Maruti: without the conversion, FCF
    cross-check divergence read as 994,094,028% (comparing 8754 Cr against
    87,023,000,000 raw Rupees) — see
    `balance_sheet_intelligence/snapshot.py::yfinance_value_in_crores()`'s
    own docstring for the first time this exact bug was found and fixed."""
    from app.calculations.balance_sheet_intelligence.snapshot import yfinance_value_in_crores

    series = (metrics or {}).get(yfinance_key) or {}
    yfinance_value = yfinance_value_in_crores(series, period) if period else None
    divergence_pct = None
    if screener_value is not None and yfinance_value is not None and screener_value:
        divergence_pct = round(abs(screener_value - yfinance_value) / abs(screener_value) * 100, 2)
    return {"screener": screener_value, "yfinance": yfinance_value, "divergence_pct": divergence_pct}
