"""Tests for metric_store's 2026-09-23 fix: `get_authoritative_value()`/
`get_latest_period_value()` now default to a CONSOLIDATED-preferred,
STANDALONE-fallback resolution when the caller omits `statement_type`,
instead of silently always meaning STANDALONE. This was a real, recurring
bug — found independently on Apollo Hospitals (P/E), GNFC (revenue,
ratios), GROWW (ROCE) and TANLA (quarterly results) across this session,
each time in a different ingestion/read path, before the user asked for a
single systemic fix instead of patching call sites one at a time.

Uses a synthetic fixture company (insert_metric_value directly) rather than
real ledger data, so these tests are fast and don't depend on what's been
ingested for any real symbol.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.infrastructure.database import metric_store
from app.infrastructure.database.models import Stock

_FIXTURE_COMPANY = "TEST:METRIC_STORE_STMT_TYPE_FIXTURE"


def _ensure_fixture_stock(db) -> None:
    if db.get(Stock, _FIXTURE_COMPANY) is not None:
        return
    now = datetime.now(timezone.utc)
    db.add(Stock(
        id=_FIXTURE_COMPANY, symbol="METRIC_STORE_STMT_TYPE_FIXTURE", exchange="TEST",
        company_name="Metric Store Fixture Co.", sector="Chemicals",
        is_active=True, created_at=now, updated_at=now,
    ))
    db.flush()


def _insert(db, metric_key: str, period: str, value: float, statement_type: str) -> None:
    _ensure_fixture_stock(db)
    metric_store.insert_metric_value(
        db, company_id=_FIXTURE_COMPANY, metric_key=metric_key, period=period, value=value,
        unit="cr", statement_type=statement_type, source="SCREENER", source_tier=2,
        reported_or_calculated="REPORTED", confidence="MEDIUM", source_date=datetime.now(timezone.utc),
    )


def test_authoritative_value_prefers_consolidated_when_both_exist(db):
    _insert(db, "pnl_sales", "2026-03-31", 744.0, "STANDALONE")
    _insert(db, "pnl_sales", "2026-03-31", 4418.0, "CONSOLIDATED")
    winner, _ = metric_store.get_authoritative_value(db, _FIXTURE_COMPANY, "pnl_sales", "2026-03-31")
    assert winner is not None
    assert winner.statement_type == "CONSOLIDATED"
    assert float(winner.value) == 4418.0


def test_authoritative_value_falls_back_to_standalone_when_consolidated_absent(db):
    _insert(db, "pnl_sales", "2027-03-31", 100.0, "STANDALONE")
    winner, _ = metric_store.get_authoritative_value(db, _FIXTURE_COMPANY, "pnl_sales", "2027-03-31")
    assert winner is not None
    assert winner.statement_type == "STANDALONE"
    assert float(winner.value) == 100.0


def test_authoritative_value_explicit_standalone_still_respected_with_both_present(db):
    """An explicit request for one type must never silently redirect to the
    other — this is what pl_intelligence/balance_sheet_intelligence/
    cash_flow_intelligence's own side-by-side comparisons depend on."""
    _insert(db, "pnl_sales", "2028-03-31", 55.0, "STANDALONE")
    _insert(db, "pnl_sales", "2028-03-31", 900.0, "CONSOLIDATED")
    winner, _ = metric_store.get_authoritative_value(db, _FIXTURE_COMPANY, "pnl_sales", "2028-03-31", statement_type="STANDALONE")
    assert winner is not None
    assert winner.statement_type == "STANDALONE"
    assert float(winner.value) == 55.0


def test_latest_period_value_prefers_consolidated_when_both_exist(db):
    _insert(db, "qtr_sales", "2026-06-30", 214.0, "STANDALONE")
    _insert(db, "qtr_sales", "2026-06-30", 1226.0, "CONSOLIDATED")
    row = metric_store.get_latest_period_value(db, _FIXTURE_COMPANY, "qtr_sales")
    assert row is not None
    assert row.statement_type == "CONSOLIDATED"
    assert float(row.value) == 1226.0


def test_latest_period_value_falls_back_to_standalone_when_consolidated_absent(db):
    _insert(db, "bs_ratio_roce_percent", "2026-03-31", 16.0, "STANDALONE")
    row = metric_store.get_latest_period_value(db, _FIXTURE_COMPANY, "bs_ratio_roce_percent")
    assert row is not None
    assert row.statement_type == "STANDALONE"
    assert float(row.value) == 16.0


def test_latest_period_value_explicit_type_still_respected(db):
    _insert(db, "bs_ratio_debtor_days", "2026-03-31", 12.0, "STANDALONE")
    _insert(db, "bs_ratio_debtor_days", "2026-03-31", 22.0, "CONSOLIDATED")
    row = metric_store.get_latest_period_value(db, _FIXTURE_COMPANY, "bs_ratio_debtor_days", statement_type="STANDALONE")
    assert row is not None
    assert row.statement_type == "STANDALONE"
    assert float(row.value) == 12.0


def test_get_metric_history_none_still_returns_both_types_unchanged():
    """get_metric_history()'s own "statement_type=None means both types"
    contract predates this fix and must be completely unaffected by it —
    only get_authoritative_value()/get_latest_period_value() gained the
    new smart-fallback default."""
    import inspect
    sig = inspect.signature(metric_store.get_metric_history)
    assert sig.parameters["statement_type"].default == metric_store.DEFAULT_STATEMENT_TYPE
