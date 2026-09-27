"""Telecom quarterly KPIs: storage, derived metrics, results-filing layer, bridge."""
from __future__ import annotations

from app.calculations.quarterly_sector_kpis import compute_quarterly_sector_kpis
from app.ingestion import quarterly_operating_metrics_ingestion as q
from app.sectors.classification_map import BASIC_INDUSTRY_TO_FRAMEWORK as M
from app.sectors.ledger_bridge import inject_ledger_bridge

_CO = "NSE:SUNTV"
_P = "2026-06-30"


def _store(db, extracted):
    inserted: list = []
    token = q._source_ctx.set("NSE_RESULTS_FILING")
    try:
        q._store_extracted(db, _CO, "Telecom", q._SECTOR_CONFIG["Telecom"], extracted, _P, "CONSOLIDATED", "u", "d", inserted)
    finally:
        q._source_ctx.reset(token)
    return {r.metric_key: float(r.value) for r in inserted}


def test_config_prompt_and_routing():
    assert q._SECTOR_CONFIG["Telecom"]["prefix"] == "tel"
    for f in ("arpu_inr", "churn_pct", "subscribers_mn", "towers", "order_backlog_cr"):
        assert f in q._AREA_PROMPTS["telecom"]
    assert M["telecom - infrastructure"] == "Telecom"  # tower companies are telecom, not roads/ports infrastructure


def test_results_filing_layer_is_registered_for_telecom_only():
    assert q._KIND_META["outcome"]["source"] == "NSE_RESULTS_FILING"
    from app.infrastructure.database import metric_store
    assert "NSE_RESULTS_FILING" in metric_store.VALID_SOURCES


def test_derived_growth_tenancy_and_service_fcf(db):
    got = _store(db, {"arpu_inr": 264, "subscribers_mn": 376.508, "subscribers_yoy_prior_mn": 362.796, "towers": 267611,
                      "colocations": 432250, "revenue_cr": 8431, "ebitda_cr": 4521, "capex_cr": 1500})
    assert round(got["qtr_tel_subscriber_growth_yoy"], 2) == 3.78
    assert round(got["qtr_tel_tenancy"], 2) == round(432250 / 267611, 2)
    assert round(got["qtr_tel_ebitda_minus_capex_margin"], 2) == round((4521 - 1500) / 8431 * 100, 2)


def test_stated_tenancy_wins_and_nothing_is_derived_without_inputs(db):
    got = _store(db, {"towers": 100, "colocations": 200, "tenancy_ratio": 1.62})
    assert got["qtr_tel_tenancy"] == 1.62
    got2 = _store(db, {"arpu_inr": 200})
    assert "qtr_tel_subscriber_growth_yoy" not in got2 and "qtr_tel_ebitda_minus_capex_margin" not in got2


def test_read_side_and_bridge(db):
    _store(db, {"arpu_inr": 264, "subscribers_mn": 376.5, "subscribers_yoy_prior_mn": 362.8, "churn_pct": 2.6})
    assert compute_quarterly_sector_kpis(db, _CO, "Telecom")["available"] is True
    bridged = inject_ledger_bridge({}, db, _CO, ["arpu", "subscriber_growth_yoy", "churn_pct"])["_ledger_metrics"]
    assert bridged["arpu"] == 264.0 and bridged["churn_pct"] == 2.6 and "subscriber_growth_yoy" in bridged


def test_locator_accepts_a_text_tolerance_for_letter_spaced_filings():
    import inspect
    from app.ingestion.annual_report_locator import locate_sections
    assert "x_tolerance" in inspect.signature(locate_sections).parameters


def test_overseas_segment_data_share_and_revenue_per_gb(db):
    got = _store(db, {"africa_subscribers_mn": 188.999, "africa_subscribers_yoy_prior_mn": 169.389, "africa_arpu_usd": 2.7,
                      "group_customers_mn": 681, "data_revenue_cr": 5703.58, "revenue_cr": 6582.82,
                      "mobile_revenue_cr": 29928.9, "data_traffic_bn_gb": 31.062,
                      "spectrum_liability_cr": 130299, "agr_liability_cr": 25759})
    assert round(got["qtr_tel_africa_subscriber_growth_yoy"], 1) == 11.6      # company states 11.6%
    assert round(got["qtr_tel_data_revenue_pct"], 1) == 86.6
    assert round(got["qtr_tel_revenue_per_gb"], 2) == 9.64
    assert got["qtr_tel_group_customers_mn"] == 681 and got["qtr_tel_agr_liability"] == 25759


def test_trai_parser_computes_shares_and_rejects_a_table_that_does_not_reconcile():
    from app.ingestion.trai_client import parse_report
    good = ("Highlights of Telecom Subscription Data at the end of June 2026\n"
            "Access Service Provider-wise Market Shares BSNL, 7.25% MTNL, 0.01%\n"
            "  total   483,809,981   486,799,957   198,659,341   198,823,098   92,914,988   93,008,994   "
            "177,761   166,477   501,436,636   503,583,616   1,276,998,869   1,282,382,284   5,383,415\n").replace("\\\n", "\n")
    out = parse_report(good)
    assert out["month_end"] == "2026-06-30"
    assert out["shares"]["airtel"] == 37.96 and out["shares"]["vi"] == 15.5
    bad = good.replace("1,282,382,284", "1,182,382,284")     # operator columns no longer add up to the total
    assert parse_report(bad) is None
    assert parse_report(good.replace("7.25%", "9.90%")) is None  # disagrees with TRAI's printed BSNL share


def test_trai_source_is_registered_and_labelled():
    from app.infrastructure.database import metric_store
    from app.calculations.quarterly_sector_kpis import SOURCE_LABELS
    assert "TRAI_REPORT" in metric_store.VALID_SOURCES and "TRAI_REPORT" in SOURCE_LABELS
