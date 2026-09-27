"""Regression test for `pnl_engine.py::compute_pnl_analysis()`'s STANDALONE
fallback — a real gap found live on two separate companies (Tata
Technologies, then Coforge): Screener's CONSOLIDATED P&L schedule
ingestion occasionally doesn't complete, leaving `pnl_*` ledger rows
STANDALONE-only. `compute_pnl_analysis()` had NO fallback at all before —
hardcoded `statement_type="CONSOLIDATED"` — unlike `pl_intelligence/
__init__.py::compute_pl_intelligence()`'s own `allow_fallback`, which this
mirrors. `screener_metrics_override.py::_apply_pnl_overrides()` depends on
this function, so a company hitting this gap previously had its CAGR/PAT
margin/ROE/interest-coverage overrides all silently skip (falling back to
the untouched yfinance value) rather than using real STANDALONE Screener
data that was actually available.

Kept separate from `test_pnl_engine_existing.py` (that file is a
"Stage 0 boundary" tripwire explicitly documented to never need touching as
new P&L Intelligence code is added — this test exercises a real change to
`pnl_engine.py` itself, not new code layered on top of it).
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.calculations.pnl_engine import compute_pnl_analysis
from app.infrastructure.database import metric_store
from app.infrastructure.database.models import Stock

_FIXTURE_COMPANY = "TEST:PNL_ENGINE_STMT_TYPE_FIXTURE"


def _ensure_fixture_stock(db) -> None:
    if db.get(Stock, _FIXTURE_COMPANY) is not None:
        return
    now = datetime.now(timezone.utc)
    db.add(Stock(
        id=_FIXTURE_COMPANY, symbol="PNL_ENGINE_STMT_TYPE_FIXTURE", exchange="TEST",
        company_name="PNL Engine Fixture Co.", is_active=True, created_at=now, updated_at=now,
    ))
    db.flush()


def _insert(db, metric_key: str, period: str, value: float, statement_type: str) -> None:
    _ensure_fixture_stock(db)
    metric_store.insert_metric_value(
        db, company_id=_FIXTURE_COMPANY, metric_key=metric_key, period=period, value=value,
        unit="cr", statement_type=statement_type, source="SCREENER", source_tier=2,
        reported_or_calculated="REPORTED", confidence="MEDIUM", source_date=datetime.now(timezone.utc),
    )


def test_falls_back_to_standalone_when_consolidated_has_no_pnl_sales(db):
    for period, sales in (("2025-03-31", 900.0), ("2026-03-31", 1000.0)):
        _insert(db, "pnl_sales", period, sales, "STANDALONE")
        _insert(db, "pnl_net_profit", period, sales * 0.1, "STANDALONE")
    db.flush()

    result = compute_pnl_analysis(db, company_id=_FIXTURE_COMPANY)
    assert result["statement_type"] == "STANDALONE"
    assert result["years_of_data"] == 2
    assert result["table"]["sales"] == {"2025-03-31": 900.0, "2026-03-31": 1000.0}


def test_prefers_consolidated_when_both_available(db):
    for period, sales in (("2025-03-31", 900.0), ("2026-03-31", 1000.0)):
        _insert(db, "pnl_sales", period, sales, "STANDALONE")
        _insert(db, "pnl_sales", period, sales * 1.5, "CONSOLIDATED")
    db.flush()

    result = compute_pnl_analysis(db, company_id=_FIXTURE_COMPANY)
    assert result["statement_type"] == "CONSOLIDATED"
    assert result["table"]["sales"]["2026-03-31"] == 1500.0


def test_empty_both_statement_types_never_raises(db):
    """When neither statement type has data, the function still returns a
    mostly-empty, `years_of_data=0` structure rather than raising — which
    statement_type label it reports in that case is cosmetic (both are
    equally empty), so this only asserts the no-crash contract."""
    result = compute_pnl_analysis(db, company_id=_FIXTURE_COMPANY)
    assert result["years_of_data"] == 0
    assert result["statement_type"] in ("CONSOLIDATED", "STANDALONE")
