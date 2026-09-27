"""Tests for `app/calculations/quarterly_sector_kpis.py` — the read-side
compute function surfacing the Quarterly Sector KPI Extraction Engine's
data. Mirrors the real end-to-end shape confirmed live on Maruti Suzuki
(`qtr_automobile_units_sold`/`qtr_volume_growth_yoy` for FY2026-27 Q1).
"""
from __future__ import annotations

from app.calculations.quarterly_sector_kpis import compute_quarterly_sector_kpis
from app.infrastructure.database import metric_store

_COMPANY_ID = "NSE:MARUTI"


def test_unconfigured_sector_returns_unavailable(db):
    result = compute_quarterly_sector_kpis(db, _COMPANY_ID, "IT Services")
    assert result == {"available": False, "sector_name": "IT Services"}


def test_no_sector_name_returns_unavailable(db):
    result = compute_quarterly_sector_kpis(db, _COMPANY_ID, None)
    assert result["available"] is False


def test_configured_sector_with_no_data_yet_returns_unavailable(db):
    """A company that hasn't had this engine run for it yet (or whose
    presentation resolved to nothing extractable) is a clean `available:
    false`, not an error or an all-null metrics list."""
    result = compute_quarterly_sector_kpis(db, "NSE:A-COMPANY-WITH-NO-QTR-DATA", "Automobile")
    assert result == {"available": False, "sector_name": "Automobile"}


def test_real_shape_with_synthetic_automobile_data(db):
    metric_store.insert_metric_value(
        db, company_id=_COMPANY_ID, metric_key="qtr_automobile_units_sold", period="2026-06-30",
        value=682724.0, unit="units", statement_type="STANDALONE", source="NSE_INVESTOR_PRESENTATION",
        source_tier=1, reported_or_calculated="REPORTED", confidence="HIGH",
    )
    metric_store.insert_metric_value(
        db, company_id=_COMPANY_ID, metric_key="qtr_volume_growth_yoy", period="2026-06-30",
        value=29.34, unit="%", statement_type="STANDALONE", source="NSE_INVESTOR_PRESENTATION",
        source_tier=1, reported_or_calculated="CALCULATED", confidence="MEDIUM",
    )

    result = compute_quarterly_sector_kpis(db, _COMPANY_ID, "Automobile")
    assert result["available"] is True
    assert result["statement_type"] == "STANDALONE"
    assert result["single_statement_source"] is True
    assert result["latest_quarter"] == "2026-06-30"
    by_key = {m["metric_key"]: m for m in result["metrics"]}
    assert by_key["qtr_automobile_units_sold"]["latest_value"] == 682724.0
    assert by_key["qtr_volume_growth_yoy"]["label"] == "Volume Growth (YoY)"
    # market_share was never inserted — must not appear as a null entry
    assert "qtr_automobile_market_share" not in by_key


def test_prefers_consolidated_when_both_exist(db):
    metric_store.insert_metric_value(
        db, company_id=_COMPANY_ID, metric_key="qtr_cement_sales_mnt", period="2026-06-30",
        value=17.1, unit="MT", statement_type="CONSOLIDATED", source="NSE_INVESTOR_PRESENTATION",
        source_tier=1, reported_or_calculated="REPORTED", confidence="HIGH",
    )
    metric_store.insert_metric_value(
        db, company_id=_COMPANY_ID, metric_key="qtr_cement_sales_mnt", period="2026-06-30",
        value=11.7, unit="MT", statement_type="STANDALONE", source="NSE_INVESTOR_PRESENTATION",
        source_tier=1, reported_or_calculated="REPORTED", confidence="HIGH",
    )

    result = compute_quarterly_sector_kpis(db, _COMPANY_ID, "Cement")
    assert result["statement_type"] == "CONSOLIDATED"
    assert result["single_statement_source"] is False
    by_key = {m["metric_key"]: m for m in result["metrics"]}
    assert by_key["qtr_cement_sales_mnt"]["latest_value"] == 17.1


def test_mining_and_specialty_chemicals_alias_to_shared_metric_sets():
    from app.calculations.quarterly_sector_kpis import _SECTOR_METRICS
    assert _SECTOR_METRICS["Mining"] is _SECTOR_METRICS["Metals"]
    assert _SECTOR_METRICS["Specialty Chemicals"] is _SECTOR_METRICS["Chemicals"]


def test_hotels_shape_with_synthetic_data(db):
    """Mirrors the real end-to-end shape confirmed live on Chalet Hotels
    (ADR/Occupancy/RevPAR for FY2026-27 Q1, Combined Portfolio)."""
    for key, value, unit in [
        ("qtr_hotels_arr", 13247.0, "INR"), ("qtr_hotels_occupancy", 64.8, "%"),
        ("qtr_hotels_revpar", 8582.0, "INR"),
    ]:
        metric_store.insert_metric_value(
            db, company_id="NSE:CHALET", metric_key=key, period="2026-06-30",
            value=value, unit=unit, statement_type="CONSOLIDATED", source="NSE_INVESTOR_PRESENTATION",
            source_tier=1, reported_or_calculated="REPORTED", confidence="HIGH",
        )
    result = compute_quarterly_sector_kpis(db, "NSE:CHALET", "Hotels & Restaurants")
    assert result["available"] is True
    by_key = {m["metric_key"]: m for m in result["metrics"]}
    assert by_key["qtr_hotels_revpar"]["latest_value"] == 8582.0
    assert by_key["qtr_hotels_occupancy"]["label"] == "Occupancy"


def test_retail_shape_with_synthetic_data(db):
    """Mirrors the real end-to-end shape confirmed live on Trent (store
    count/revenue-per-sqft for FY2026-27 Q1)."""
    metric_store.insert_metric_value(
        db, company_id="NSE:TRENT", metric_key="qtr_retail_store_count", period="2026-06-30",
        value=1312.0, unit="units", statement_type="CONSOLIDATED", source="NSE_INVESTOR_PRESENTATION",
        source_tier=1, reported_or_calculated="REPORTED", confidence="HIGH",
    )
    result = compute_quarterly_sector_kpis(db, "NSE:TRENT", "Retail")
    assert result["available"] is True
    by_key = {m["metric_key"]: m for m in result["metrics"]}
    assert by_key["qtr_retail_store_count"]["latest_value"] == 1312.0
    # sssg/growth/revenue-per-sqft were never inserted — must not appear as null entries
    assert "qtr_retail_sssg" not in by_key


def test_realty_shape_with_synthetic_data(db):
    """Mirrors the real end-to-end shape confirmed live on Godrej
    Properties (booking value/collections growth for FY2026-27 Q1)."""
    metric_store.insert_metric_value(
        db, company_id="NSE:GODREJPROP", metric_key="qtr_realty_pre_sales_value", period="2026-06-30",
        value=8651.0, unit="INR Cr", statement_type="CONSOLIDATED", source="NSE_INVESTOR_PRESENTATION",
        source_tier=1, reported_or_calculated="REPORTED", confidence="HIGH",
    )
    metric_store.insert_metric_value(
        db, company_id="NSE:GODREJPROP", metric_key="qtr_realty_collections_growth_yoy", period="2026-06-30",
        value=18.47, unit="%", statement_type="CONSOLIDATED", source="NSE_INVESTOR_PRESENTATION",
        source_tier=1, reported_or_calculated="CALCULATED", confidence="MEDIUM",
    )
    result = compute_quarterly_sector_kpis(db, "NSE:GODREJPROP", "Real Estate")
    assert result["available"] is True
    by_key = {m["metric_key"]: m for m in result["metrics"]}
    assert by_key["qtr_realty_pre_sales_value"]["latest_value"] == 8651.0
    # collections (the absolute figure) was never inserted — must not appear as a null entry
    assert "qtr_realty_collections" not in by_key


def test_oil_gas_shape_with_synthetic_data(db):
    """Mirrors the real end-to-end shape confirmed live on BPCL (GRM for
    FY2026-27 Q1)."""
    metric_store.insert_metric_value(
        db, company_id="NSE:BPCL", metric_key="qtr_oilgas_grm", period="2026-06-30",
        value=41.41, unit="USD/bbl", statement_type="CONSOLIDATED", source="NSE_INVESTOR_PRESENTATION",
        source_tier=1, reported_or_calculated="REPORTED", confidence="HIGH",
    )
    result = compute_quarterly_sector_kpis(db, "NSE:BPCL", "Oil & Gas")
    assert result["available"] is True
    by_key = {m["metric_key"]: m for m in result["metrics"]}
    assert by_key["qtr_oilgas_grm"]["latest_value"] == 41.41


def test_fmcg_shape_with_synthetic_data(db):
    # NSE:SUNTV, not HINDUNILVR: real hand-verified HUL rows now live in the ledger,
    # which would make the "USG never inserted" assertion below false.
    for key, val in [("qtr_volume_growth_yoy", 5.0), ("qtr_fmcg_price_mix_growth", 4.76)]:
        metric_store.insert_metric_value(
            db, company_id="NSE:SUNTV", metric_key=key, period="2026-06-30", value=val, unit="%",
            statement_type="CONSOLIDATED", source="NSE_INVESTOR_PRESENTATION", source_tier=1,
            reported_or_calculated="REPORTED", confidence="HIGH",
        )
    result = compute_quarterly_sector_kpis(db, "NSE:SUNTV", "Fast Moving Consumer Goods")
    assert result["available"] is True
    by_key = {m["metric_key"]: m for m in result["metrics"]}
    assert by_key["qtr_volume_growth_yoy"]["latest_value"] == 5.0
    assert "qtr_fmcg_underlying_sales_growth" not in by_key


def test_healthcare_shape_with_synthetic_data(db):
    metric_store.insert_metric_value(
        db, company_id="NSE:ALKEM", metric_key="qtr_healthcare_us_revenue_pct", period="2026-06-30", value=21.7,
        unit="%", statement_type="CONSOLIDATED", source="NSE_INVESTOR_PRESENTATION", source_tier=1,
        reported_or_calculated="REPORTED", confidence="HIGH",
    )
    result = compute_quarterly_sector_kpis(db, "NSE:ALKEM", "Healthcare")
    assert result["available"] is True
    assert [m["metric_key"] for m in result["metrics"]] == ["qtr_healthcare_us_revenue_pct"]


def test_consumer_durables_shape_with_synthetic_data(db):
    """Mirrors the real end-to-end shape confirmed live on Voltas
    (`qtr_volume_growth_yoy`/`qtr_consumer_durables_market_share` for
    FY2026-27 Q1, Room Air Conditioner segment)."""
    metric_store.insert_metric_value(
        db, company_id="NSE:VOLTAS", metric_key="qtr_volume_growth_yoy", period="2026-06-30",
        value=45.0, unit="%", statement_type="CONSOLIDATED", source="NSE_INVESTOR_PRESENTATION",
        source_tier=1, reported_or_calculated="REPORTED", confidence="HIGH",
    )
    metric_store.insert_metric_value(
        db, company_id="NSE:VOLTAS", metric_key="qtr_consumer_durables_market_share", period="2026-06-30",
        value=17.3, unit="%", statement_type="CONSOLIDATED", source="NSE_INVESTOR_PRESENTATION",
        source_tier=1, reported_or_calculated="REPORTED", confidence="HIGH",
    )
    result = compute_quarterly_sector_kpis(db, "NSE:VOLTAS", "Consumer Durables")
    assert result["available"] is True
    assert result["statement_type"] == "CONSOLIDATED"
    by_key = {m["metric_key"]: m for m in result["metrics"]}
    assert by_key["qtr_volume_growth_yoy"]["latest_value"] == 45.0
    assert by_key["qtr_consumer_durables_market_share"]["latest_value"] == 17.3
