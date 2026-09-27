"""Regression test for `compute_pl_intelligence()`'s statement-type
fallback — a real bug found live-testing Tata Technologies (and confirmed
to affect several other companies too, per `test_pnl_engine_existing.py`'s
own fixture-choice docstring): `pnl_*` ledger rows had only ever been
ingested under STANDALONE for these companies, but the function's
CONSOLIDATED default had no fallback, so it silently returned an entirely
empty result despite real STANDALONE data existing.

Superseded (not just extended) by a later, real-world finding on Netweb
Technologies / Bandhan Bank: a company that has data under ONLY ONE
statement type at all (confirmed live — Screener.in genuinely has no
consolidated statements for these two, not an ingestion gap) has no actual
standalone-vs-consolidated distinction to preserve, so the single dataset
is now always labeled "CONSOLIDATED" in the output (`single_statement_source:
True`) rather than surfaced as "STANDALONE" — see `compute_pl_intelligence`'s
own docstring.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.calculations.pl_intelligence import compute_pl_intelligence
from app.infrastructure.database import metric_store
from app.infrastructure.database.models import Stock

_FIXTURE_COMPANY = "TEST:PLI_STMT_TYPE_FIXTURE"


def _ensure_fixture_stock(db) -> None:
    """`fa_metric_data_points.company_id` has a FK to `stocks.id` — insert a
    throwaway row inside the same rolled-back transaction the `db` fixture
    already provides."""
    if db.get(Stock, _FIXTURE_COMPANY) is not None:
        return
    now = datetime.now(timezone.utc)
    db.add(Stock(
        id=_FIXTURE_COMPANY, symbol="PLI_STMT_TYPE_FIXTURE", exchange="TEST", company_name="PLI Fixture Co.",
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


def test_uses_standalone_data_labeled_consolidated_when_only_one_type_exists(db):
    period = "2026-03-31"
    for metric_key, value in (
        ("pnl_sales", 1000.0), ("pnl_expenses", 800.0), ("pnl_operating_profit", 200.0),
        ("pnl_other_income", 10.0), ("pnl_interest", 5.0), ("pnl_depreciation", 20.0),
        ("pnl_pbt", 185.0), ("pnl_tax_pct", 25.0), ("pnl_net_profit", 139.0),
    ):
        _insert(db, metric_key, period, value, "STANDALONE")
    db.flush()

    result = compute_pl_intelligence(db, company_id=_FIXTURE_COMPANY)
    assert result["period"] == period
    assert result["statement_type"] == "CONSOLIDATED"
    assert result["single_statement_source"] is True

    # An explicit request for either type converges on the same single
    # dataset — there's nothing genuinely different to toggle to.
    explicit_consolidated = compute_pl_intelligence(
        db, company_id=_FIXTURE_COMPANY, statement_type="CONSOLIDATED", allow_fallback=False)
    explicit_standalone = compute_pl_intelligence(
        db, company_id=_FIXTURE_COMPANY, statement_type="STANDALONE", allow_fallback=False)
    assert explicit_consolidated["period"] == period
    assert explicit_standalone["period"] == period
    assert explicit_consolidated["statement_type"] == "CONSOLIDATED"
    assert explicit_standalone["statement_type"] == "CONSOLIDATED"


def test_stays_empty_when_neither_statement_type_has_data(db):
    result = compute_pl_intelligence(db, company_id="NSE:NOPE_NOT_REAL_PLI")
    assert result["period"] is None
    assert result["score"]["master_pl_score"] is None
    assert result["single_statement_source"] is False


def test_distinguishes_genuine_consolidated_and_standalone_data(db):
    """Companies with real, distinct data on both sides keep their exact
    existing behavior — no relabeling, no forced convergence."""
    period = "2026-03-31"
    for metric_key, value in (
        ("pnl_sales", 1000.0), ("pnl_expenses", 800.0), ("pnl_operating_profit", 200.0),
        ("pnl_other_income", 10.0), ("pnl_interest", 5.0), ("pnl_depreciation", 20.0),
        ("pnl_pbt", 185.0), ("pnl_tax_pct", 25.0), ("pnl_net_profit", 139.0),
    ):
        _insert(db, metric_key, period, value, "STANDALONE")
        _insert(db, metric_key, period, value * 1.5, "CONSOLIDATED")
    db.flush()

    result = compute_pl_intelligence(db, company_id=_FIXTURE_COMPANY)
    assert result["single_statement_source"] is False
    assert result["statement_type"] == "CONSOLIDATED"

    explicit_standalone = compute_pl_intelligence(
        db, company_id=_FIXTURE_COMPANY, statement_type="STANDALONE", allow_fallback=False)
    assert explicit_standalone["statement_type"] == "STANDALONE"
    assert explicit_standalone["single_statement_source"] is False


def test_prefers_current_standalone_over_stale_consolidated(db):
    """Regression test for a real bug found live on GPT Healthcare
    (2026-09-20): its Screener CONSOLIDATED data stops at FY2022 (it
    deconsolidated a subsidiary) while STANDALONE runs current through
    FY2026 — both sides genuinely have SOME data, so `single_statement_source`
    is False, but the old auto-detect default always picked CONSOLIDATED
    purely because it was nonempty, silently showing a 4-year-stale P&L as
    the default view. The fix must prefer whichever side is more CURRENT."""
    for metric_key, value in (
        ("pnl_sales", 500.0), ("pnl_expenses", 400.0), ("pnl_operating_profit", 100.0),
        ("pnl_other_income", 5.0), ("pnl_interest", 2.0), ("pnl_depreciation", 10.0),
        ("pnl_pbt", 93.0), ("pnl_tax_pct", 25.0), ("pnl_net_profit", 70.0),
    ):
        _insert(db, metric_key, "2022-03-31", value, "CONSOLIDATED")  # stale
        _insert(db, metric_key, "2026-03-31", value * 2, "STANDALONE")  # current
    db.flush()

    result = compute_pl_intelligence(db, company_id=_FIXTURE_COMPANY)
    assert result["single_statement_source"] is False
    assert result["statement_type"] == "STANDALONE"
    assert result["period"] == "2026-03-31"

    # An explicit toggle still gets exactly what it asked for, unaffected.
    explicit_consolidated = compute_pl_intelligence(
        db, company_id=_FIXTURE_COMPANY, statement_type="CONSOLIDATED", allow_fallback=False)
    assert explicit_consolidated["statement_type"] == "CONSOLIDATED"
    assert explicit_consolidated["period"] == "2022-03-31"
