"""Tests for `cash_flow_intelligence.coverage` and the package orchestrator
`compute_cash_flow_intelligence()` (Cash Flow Analysis Engine, Milestone 5).
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.calculations.cash_flow_intelligence import compute_cash_flow_intelligence, coverage
from app.infrastructure.database import metric_store
from app.infrastructure.database.models import Stock

_FIXTURE_COMPANY = "TEST:CF_STMT_TYPE_FIXTURE"


def _ensure_fixture_stock(db) -> None:
    """`fa_metric_data_points.company_id` has a FK to `stocks.id` — insert a
    throwaway row inside the same rolled-back transaction the `db` fixture
    already provides."""
    if db.get(Stock, _FIXTURE_COMPANY) is not None:
        return
    now = datetime.now(timezone.utc)
    db.add(Stock(
        id=_FIXTURE_COMPANY, symbol="CF_STMT_TYPE_FIXTURE", exchange="TEST", company_name="CF Fixture Co.",
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

# ── coverage.py ──────────────────────────────────────────────────────────────

def test_full_facts_yields_high_coverage():
    """The whole point of choosing Screener's schedules API over yfinance
    for this engine — coverage should read meaningfully higher than the
    Balance Sheet engine's own ~30-50%, since nearly every tracked metric
    genuinely has a source."""
    facts = {
        "cfo": 19100.0, "cfi": -14734.0, "cff": -4484.0, "net_cash_flow": -118.0,
        "free_cash_flow": 8754.0, "operating_profit": 21802.0, "pat": 15043.0,
        "receivables_change": 1236.0, "inventory_change": -4407.0, "payables_change": 5194.0,
        "taxes_paid": -4337.0, "fixed_assets_purchased": -10398.0, "fixed_assets_sold": 52.0,
        "investments_purchased": -108034.0, "investments_sold": 101969.0, "interest_received": 354.0,
        "borrowings_raised": 0.0, "borrowings_repaid": 0.0, "interest_paid": -102.0,
        "dividends_paid": -4244.0, "opening_cash": 500.0, "closing_cash": 382.0,
    }
    result = coverage.compute_coverage_audit(facts)
    assert result["coverage_pct"] > 60.0
    assert result["metrics"]["cfo"]["status"] == "AVAILABLE"
    assert result["metrics"]["debt_raised"]["status"] == "AVAILABLE"
    assert result["metrics"]["debt_repaid"]["status"] == "AVAILABLE"


def test_empty_facts_still_returns_every_metric():
    result = coverage.compute_coverage_audit({})
    assert result["total_metrics"] == len(coverage._DEPENDENCY_GRAPH)
    assert result["coverage_pct"] == 0.0 or result["coverage_pct"] < 20.0


def test_fx_adjustment_always_missing_input():
    result = coverage.compute_coverage_audit({"cfo": 100.0})
    assert result["metrics"]["fx_adjustment"]["status"] == "MISSING_INPUT"
    assert "FX" in result["metrics"]["fx_adjustment"]["reason"] or "currency" in result["metrics"]["fx_adjustment"]["reason"]


def test_buybacks_always_partial_with_proxy_reason():
    result = coverage.compute_coverage_audit({})
    assert result["metrics"]["buybacks"]["status"] == "PARTIAL"


def test_top_source_gaps_ranks_fx_highest():
    result = coverage.compute_coverage_audit({})
    gaps = coverage.top_source_gaps(result)
    assert gaps[0]["metric"] == "fx_adjustment"
    assert gaps[0]["priority"] == "HIGH"


def test_partial_facts_status():
    facts = {"fixed_assets_purchased": -100.0, "cfo": None}
    result = coverage.compute_coverage_audit(facts)
    assert result["metrics"]["capex_to_cfo"]["status"] == "PARTIAL"


# ── __init__.py orchestrator ────────────────────────────────────────────────

def test_empty_db_returns_graceful_empty_shape(db):
    """A company with zero Screener cash-flow schedule rows must never
    raise — matches every other intelligence-engine package's contract."""
    result = compute_cash_flow_intelligence(db, company_id="NSE:NOPE_NOT_REAL", yfinance_metrics={})
    assert result["period"] is None
    assert result["volatility"]["classification"] == "INSUFFICIENT_DATA"
    assert len(result["risk_flags"]) == 5
    assert len(result["forensic_patterns"]) == 7
    assert result["coverage"]["total_metrics"] == len(coverage._DEPENDENCY_GRAPH)


def test_prefers_statement_type_with_schedule_data_over_top_level_only(db):
    """Regression test for a real bug found live-testing Tata Technologies:
    CONSOLIDATED had all 8 top-level cf_* periods but ZERO cf_sched_* rows
    (the schedule fetch failed for that statement_type on the original
    ingestion run), while STANDALONE had both. The old selection logic
    picked CONSOLIDATED purely because its top-level series existed, then
    produced an almost-entirely-empty result (CFO bridge, working capital,
    investing/financing breakdown, conversion all blank) despite real
    schedule data existing under STANDALONE. The fix must prefer the
    statement_type where schedule data actually exists."""
    period = "2026-03-31"
    # CONSOLIDATED: top-level only, no schedule.
    _insert(db, "cf_operating_cash_flow", period, 100.0, "CONSOLIDATED")
    _insert(db, "cf_investing_cash_flow", period, -20.0, "CONSOLIDATED")
    _insert(db, "cf_financing_cash_flow", period, -10.0, "CONSOLIDATED")
    # STANDALONE: both top-level AND schedule.
    _insert(db, "cf_operating_cash_flow", period, 90.0, "STANDALONE")
    _insert(db, "cf_investing_cash_flow", period, -15.0, "STANDALONE")
    _insert(db, "cf_financing_cash_flow", period, -8.0, "STANDALONE")
    _insert(db, "cf_sched_op_profit_from_operations", period, 110.0, "STANDALONE")
    _insert(db, "cf_sched_op_working_capital_changes", period, -5.0, "STANDALONE")
    _insert(db, "cf_sched_op_direct_taxes", period, -15.0, "STANDALONE")
    db.flush()

    result = compute_cash_flow_intelligence(db, company_id=_FIXTURE_COMPANY, yfinance_metrics={})
    assert result["statement_type"] == "STANDALONE"
    assert result["reconciliation"]["cfo_bridge"]["operating_profit"] == 110.0


def test_falls_back_to_top_level_only_when_no_statement_type_has_schedule(db):
    """When NEITHER statement_type has schedule data, the engine must still
    return the top-level-only result (FCF/cash-bridge still useful) rather
    than an empty shape — the old, still-valid fallback behavior."""
    period = "2026-03-31"
    _insert(db, "cf_operating_cash_flow", period, 100.0, "CONSOLIDATED")
    _insert(db, "cf_free_cash_flow", period, 50.0, "CONSOLIDATED")
    db.flush()

    result = compute_cash_flow_intelligence(db, company_id=_FIXTURE_COMPANY, yfinance_metrics={})
    assert result["statement_type"] == "CONSOLIDATED"
    assert result["period"] == period


def test_prefers_current_standalone_over_stale_consolidated(db):
    """Same bug class as `test_prefers_statement_type_with_schedule_data_
    over_top_level_only` above, found the same day on GPT Healthcare:
    CONSOLIDATED data stops at FY2022 while STANDALONE runs current through
    FY2026 — both sides have real top-level AND schedule data, so the old
    "CONSOLIDATED always tried first" order silently picked the stale one."""
    for period, mult, stmt in (("2022-03-31", 1.0, "CONSOLIDATED"), ("2026-03-31", 2.0, "STANDALONE")):
        _insert(db, "cf_operating_cash_flow", period, 100.0 * mult, stmt)
        _insert(db, "cf_investing_cash_flow", period, -20.0 * mult, stmt)
        _insert(db, "cf_financing_cash_flow", period, -10.0 * mult, stmt)
        _insert(db, "cf_sched_op_profit_from_operations", period, 110.0 * mult, stmt)
        _insert(db, "cf_sched_op_working_capital_changes", period, -5.0 * mult, stmt)
        _insert(db, "cf_sched_op_direct_taxes", period, -15.0 * mult, stmt)
    db.flush()

    result = compute_cash_flow_intelligence(db, company_id=_FIXTURE_COMPANY, yfinance_metrics={})
    assert result["statement_type"] == "STANDALONE"
    assert result["period"] == "2026-03-31"
    assert result["reconciliation"]["cfo_bridge"]["operating_profit"] == 220.0

    explicit_consolidated = compute_cash_flow_intelligence(
        db, company_id=_FIXTURE_COMPANY, statement_type="CONSOLIDATED", yfinance_metrics={})
    assert explicit_consolidated["statement_type"] == "CONSOLIDATED"
    assert explicit_consolidated["period"] == "2022-03-31"
