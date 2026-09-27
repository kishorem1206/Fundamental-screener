"""IT services quarterly KPIs: storage, derived revenue/employee, bridge into scoring."""
from __future__ import annotations

from app.calculations.quarterly_sector_kpis import compute_quarterly_sector_kpis
from app.ingestion import quarterly_operating_metrics_ingestion as q
from app.sectors.ledger_bridge import inject_ledger_bridge

_CO = "NSE:SUNTV"  # blank company
_P = "2026-06-30"


def _store(db, extracted):
    inserted: list = []
    token = q._source_ctx.set("NSE_PRESS_RELEASE")
    try:
        q._store_extracted(db, _CO, "Information Technology", q._SECTOR_CONFIG["Information Technology"],
                           extracted, _P, "CONSOLIDATED", "u", "d", inserted)
    finally:
        q._source_ctx.reset(token)
    return {r.metric_key: float(r.value) for r in inserted}


def test_it_config_and_prompt_fields_match_storage():
    cfg = q._SECTOR_CONFIG["Information Technology"]
    assert cfg["prefix"] == "it" and cfg["prompt"] in q._AREA_PROMPTS
    prompt = q._AREA_PROMPTS[cfg["prompt"]]
    for field in ("cc_growth_yoy_pct", "attrition_pct", "utilization_pct", "deal_tcv_usd_bn", "top10_client_pct"):
        assert field in prompt


def test_storage_and_revenue_per_employee(db):
    got = _store(db, {"revenue_usd_mn": 3650, "headcount": 223889, "attrition_pct": 12.7, "cc_growth_yoy_pct": 2.6,
                      "deal_tcv_usd_bn": 2.407})
    assert got["qtr_it_attrition"] == 12.7
    assert round(got["qtr_it_revenue_per_employee"], 1) == round(3650 * 4 / 223889 * 1000, 1)


def test_no_revenue_per_employee_without_headcount(db):
    assert "qtr_it_revenue_per_employee" not in _store(db, {"revenue_usd_mn": 3650})


def test_read_side_and_scoring_bridge(db):
    _store(db, {"attrition_pct": 13.0, "utilization_pct": 82.1, "cc_growth_yoy_pct": 2.4, "deal_tcv_usd_bn": 3.6,
                "top10_client_pct": 19.9})
    assert compute_quarterly_sector_kpis(db, _CO, "Information Technology")["available"] is True
    bridged = inject_ledger_bridge({}, db, _CO, ["attrition_rate", "utilization_rate", "cc_revenue_growth",
                                                   "deal_wins_tcv", "client_concentration_top10"])["_ledger_metrics"]
    assert bridged == {"attrition_rate": 13.0, "utilization_rate": 82.1, "cc_revenue_growth": 2.4,
                       "deal_wins_tcv": 3.6, "client_concentration_top10": 19.9}
