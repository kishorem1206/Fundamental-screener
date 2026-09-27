"""Services framework routing + services quarterly KPIs."""
from __future__ import annotations

from app.calculations.quarterly_sector_kpis import compute_quarterly_sector_kpis
from app.ingestion import quarterly_operating_metrics_ingestion as q
from app.sectors.classification_map import BASIC_INDUSTRY_TO_FRAMEWORK as M
from app.sectors.ledger_bridge import inject_ledger_bridge
from app.sectors.registry import get_framework

_CO = "NSE:SUNTV"
_P = "2026-06-30"


def _store(db, sector, extracted):
    inserted: list = []
    token = q._source_ctx.set("NSE_PRESS_RELEASE")
    try:
        q._store_extracted(db, _CO, sector, q._SECTOR_CONFIG[sector], extracted, _P, "CONSOLIDATED", "u", "d", inserted)
    finally:
        q._source_ctx.reset(token)
    return {r.metric_key: float(r.value) for r in inserted}


def test_service_basic_industries_no_longer_fall_to_generic():
    for k in ("diversified commercial services", "trading & distributors", "transport related services",
              "business process outsourcing (bpo)/ knowledge process outsourcing (kpo)"):
        assert M[k] == "Services"
    assert get_framework("Services", "Commercial Services & Supplies", "Diversified Commercial Services").sector_name == "Services"


def test_services_family_shares_one_prompt_and_prefix():
    for name in ("Services", "Logistics", "Aviation", "Infrastructure"):
        assert q._SECTOR_CONFIG[name]["prefix"] == "svc"


def test_aviation_storage_and_shared_volume_key(db):
    got = _store(db, "Aviation", {"load_factor_pct": 83.3, "ask_bn": 43.5, "cask_inr": 5.71, "volume_growth_yoy_pct": 6.0})
    assert got["qtr_svc_load_factor"] == 83.3 and got["qtr_volume_growth_yoy"] == 6.0
    assert compute_quarterly_sector_kpis(db, _CO, "Aviation")["available"] is True


def test_services_orders_and_bridge(db):
    got = _store(db, "Services", {"headcount": 482214, "attrition_pct": 30, "order_inflow_cr": 100, "revenue_cr": 80,
                                   "capacity_utilization_pct": 76})
    assert got["qtr_svc_book_to_bill"] == 1.25
    bridged = inject_ledger_bridge({}, db, _CO, ["headcount", "attrition_rate", "asset_utilization"])["_ledger_metrics"]
    assert bridged == {"headcount": 482214.0, "attrition_rate": 30.0, "asset_utilization": 76.0}


def test_toll_disclosure_parse_uses_the_group_total_and_converts_million_to_crore():
    from app.ingestion.nse_toll_disclosure_client import parse_toll_disclosure
    text = ("Subject: Toll Revenue for the month of August 2026\n(Rs. in millions)\n1 IRB MP 1,721 1,447\n"
            "Total: 8,074 6,462\n")
    assert parse_toll_disclosure(text) == {"month_end": "2026-08-31", "current_cr": 807.4, "prior_cr": 646.2}
    assert parse_toll_disclosure("Toll Revenue for the month of May 2026\nTotal 8,427 6,725") is None  # no unit -> rejected


def test_toll_quarter_rollup_needs_all_three_months(db):
    from app.infrastructure.database import metric_store
    from app.ingestion import nse_toll_disclosure_client as t
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    for end, cur, pri in (("2026-04-30", 793.5, 641.8), ("2026-05-31", 842.7, 672.5)):
        for key, v in (("mth_svc_toll_revenue", cur), ("mth_svc_toll_revenue_yoy_prior", pri)):
            metric_store.insert_metric_value(db, company_id=_CO, metric_key=key, period=end, value=v, unit="INR Cr",
                statement_type="CONSOLIDATED", source="NSE_COMPANY_DISCLOSURE", source_tier=1,
                reported_or_calculated="REPORTED", confidence="HIGH")
    assert t._quarter_rollups(db, _CO, "u", now) == []
    for key, v in (("mth_svc_toll_revenue", 807.8), ("mth_svc_toll_revenue_yoy_prior", 630.8)):
        metric_store.insert_metric_value(db, company_id=_CO, metric_key=key, period="2026-06-30", value=v, unit="INR Cr",
            statement_type="CONSOLIDATED", source="NSE_COMPANY_DISCLOSURE", source_tier=1,
            reported_or_calculated="REPORTED", confidence="HIGH")
    rows = {r.metric_key: float(r.value) for r in t._quarter_rollups(db, _CO, "u", now)}
    assert rows["qtr_svc_toll_revenue"] == round(793.5 + 842.7 + 807.8, 2)
    assert rows["qtr_svc_toll_growth_yoy"] == round((2444.0 - 1945.1) / 1945.1 * 100, 2)


def test_employee_cost_pct_is_derived_from_the_same_document(db):
    got = _store(db, "Services", {"employee_cost_cr": 39.1, "revenue_cr": 200.0})
    assert got["qtr_svc_employee_cost_pct"] == 19.55
    assert "qtr_svc_employee_cost_pct" not in _store(db, "Services", {"employee_cost_cr": 39.1})
