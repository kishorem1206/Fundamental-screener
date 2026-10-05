"""Capital Goods order-book KPIs: storage/derivation in the quarterly engine and
the bridge into sector scoring."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.calculations.quarterly_sector_kpis import compute_quarterly_sector_kpis
from app.infrastructure.database import metric_store
from app.infrastructure.database.models import Stock
from app.ingestion import quarterly_operating_metrics_ingestion as q
from app.sectors.ledger_bridge import QUARTERLY_FALLBACKS, inject_ledger_bridge

_CO = "TEST:CAPGOODS"  # a company that exists only inside each test's transaction, so no real data can leak into the checks
_P = "2026-06-30"


@pytest.fixture(autouse=True)
def _blank_company(request):
    """Create the test's own company where the test uses the database (the tests assume it starts with no figures on file)."""
    if "db" not in request.fixturenames:
        return
    session = request.getfixturevalue("db")
    now = datetime.now(timezone.utc)
    session.add(Stock(id=_CO, symbol="CAPGOODS", exchange="TEST", company_name="Capital Goods Test Ltd", is_active=True, created_at=now, updated_at=now))
    session.flush()


def _store(db, extracted, **kw):
    inserted: list = []
    token = q._source_ctx.set("NSE_PRESS_RELEASE")
    try:
        q._store_extracted(db, _CO, "Capital Goods", q._SECTOR_CONFIG["Capital Goods"], extracted, _P,
                           "CONSOLIDATED", "http://x", "doc", inserted)
    finally:
        q._source_ctx.reset(token)
    return {r.metric_key: float(r.value) for r in inserted}


def test_all_three_sector_names_share_one_config():
    for name in ("Capital Goods", "Industrials", "Defence"):
        assert q._SECTOR_CONFIG[name]["prefix"] == "capgoods"


def test_growth_derived_and_book_to_bill(db):
    got = _store(db, {"order_inflow_cr": 4363, "order_inflow_yoy_prior_cr": 2917, "order_backlog_cr": 11898,
                      "order_backlog_yoy_prior_cr": 9733, "revenue_cr": 3559})
    assert round(got["qtr_capgoods_order_inflow_growth_yoy"], 1) == 49.6
    assert round(got["qtr_capgoods_order_backlog_growth_yoy"], 1) == 22.2
    assert got["qtr_capgoods_book_to_bill"] == round(4363 / 3559, 2)


def test_stated_growth_wins_over_derived(db):
    got = _store(db, {"order_inflow_cr": 568, "order_inflow_yoy_prior_cr": 536, "order_inflow_growth_pct": 6.1})
    assert got["qtr_capgoods_order_inflow_growth_yoy"] == 6.1


def test_no_growth_without_a_base_and_no_book_to_bill_without_revenue(db):
    got = _store(db, {"order_inflow_cr": 5096.5, "order_backlog_cr": 32222.1})
    assert "qtr_capgoods_order_inflow_growth_yoy" not in got
    assert "qtr_capgoods_book_to_bill" not in got
    assert "qtr_capgoods_order_backlog_to_ttm_revenue" not in got


def test_backlog_to_ttm_revenue_needs_four_consecutive_quarters(db):
    for p, v in [("2025-09-30", 100.0), ("2025-12-31", 110.0), ("2026-03-31", 120.0), ("2026-06-30", 130.0)]:
        metric_store.insert_metric_value(
            db, company_id=_CO, metric_key="qtr_sales", period=p, value=v, unit="cr", statement_type="CONSOLIDATED",
            source="SCREENER", source_tier=2, reported_or_calculated="REPORTED", confidence="MEDIUM")
    got = _store(db, {"order_backlog_cr": 920})
    assert got["qtr_capgoods_order_backlog_to_ttm_revenue"] == 920 / 460


def test_backlog_to_ttm_skipped_when_a_quarter_is_missing(db):
    for p, v in [("2025-06-30", 100.0), ("2026-03-31", 120.0), ("2026-06-30", 130.0), ("2025-12-31", 110.0)]:
        metric_store.insert_metric_value(
            db, company_id=_CO, metric_key="qtr_sales", period=p, value=v, unit="cr", statement_type="CONSOLIDATED",
            source="SCREENER", source_tier=2, reported_or_calculated="REPORTED", confidence="MEDIUM")
    assert "qtr_capgoods_order_backlog_to_ttm_revenue" not in _store(db, {"order_backlog_cr": 920})


def test_kpi_read_side_and_scoring_bridge(db):
    _store(db, {"order_inflow_cr": 100, "order_inflow_yoy_prior_cr": 80, "order_backlog_cr": 300, "revenue_cr": 90})
    for name in ("Capital Goods", "Industrials", "Defence"):
        r = compute_quarterly_sector_kpis(db, _CO, name)
        assert r["available"] and {m["metric_key"] for m in r["metrics"]} >= {
            "qtr_capgoods_order_inflow", "qtr_capgoods_book_to_bill"}
    data = inject_ledger_bridge({}, db, _CO, ["order_inflow_growth", "book_to_bill", "order_book_to_revenue"])
    bridged = data["_ledger_metrics"]
    assert bridged["order_inflow_growth"] == 25.0 and "book_to_bill" in bridged


def test_fallbacks_only_reference_rates_not_absolute_flows():
    for metric in ("order_inflow_growth", "order_book_to_revenue", "book_to_bill"):
        keys = QUARTERLY_FALLBACKS[metric]
        assert (keys if isinstance(keys, str) else keys[0]).startswith("qtr_capgoods_")


def test_aftermarket_and_utilization_stored_and_bridged(db):
    got = _store(db, {"order_backlog_cr": 100, "aftermarket_order_pct": 39, "capacity_utilization_pct": 72})
    assert got["qtr_capgoods_aftermarket_order_pct"] == 39
    assert got["qtr_capgoods_capacity_utilization"] == 72
    bridged = inject_ledger_bridge({}, db, _CO, ["aftermarket_order_pct", "capacity_utilization"])["_ledger_metrics"]
    assert bridged == {"aftermarket_order_pct": 39.0, "capacity_utilization": 72.0}


def test_construction_shares_the_order_book_engine(db):
    assert q._SECTOR_CONFIG["Construction"]["prefix"] == "capgoods"
    got = {}
    inserted: list = []
    token = q._source_ctx.set("NSE_PRESS_RELEASE")
    try:
        q._store_extracted(db, _CO, "Construction", q._SECTOR_CONFIG["Construction"],
                           {"order_backlog_cr": 100, "international_backlog_pct": 52}, _P, "CONSOLIDATED", "u", "d", inserted)
    finally:
        q._source_ctx.reset(token)
    assert {r.metric_key for r in inserted} >= {"qtr_capgoods_order_backlog", "qtr_capgoods_international_backlog_pct"}
    assert compute_quarterly_sector_kpis(db, _CO, "Construction")["available"] is True


def test_vehicle_industries_route_to_capital_goods_not_construction():
    from app.sectors.classification_map import BASIC_INDUSTRY_TO_FRAMEWORK as m
    assert m["tractors"] == "Capital Goods" and m["construction vehicles"] == "Capital Goods"
