"""Tests for the Cement-sector `cement_operating_metrics` annual-report area
and its derived ratios (`volume_growth_yoy`, `realisation_per_tonne`,
`ebitda_per_tonne`, `cost_per_tonne`).

Covers a real bug found live 2026-09-20 while building this area: the ratio
computation originally read Screener's `pnl_sales`/`pnl_operating_profit`
via `metric_store.get_latest_period_value()`, which picks the period via
`max()` over plain period strings — but `pnl_history_client.py` stores
trailing-twelve-months figures under the literal string "TTM", which sorts
AFTER every real "YYYY-MM-DD" period, so `get_latest_period_value()` was
silently returning TTM revenue instead of the fiscal-year revenue the
production-volume figure actually corresponds to. Fixed with
`_latest_fiscal_pnl_value()`, which explicitly excludes "TTM" before
picking the latest period.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.infrastructure.database import metric_store
from app.ingestion import annual_report_ingestion as ari

_FAKE_FETCH_RESULT = (
    b"%PDF-fake",
    "some/annual_report_2026.pdf",
    datetime(2026, 3, 31, tzinfo=timezone.utc),
    "https://example.com/report.pdf",
    "Fake Annual Report FY2026",
)
_FAKE_SECTIONS = {"cement_operating_metrics": [0]}
_FAKE_STATEMENT_TYPES = {"cement_operating_metrics": "STANDALONE"}
_FAKE_EXTRACTED = {
    "installed_capacity_mtpa": 191.36,
    "production_mmt": 143.83,
    "production_mmt_prior_year": 127.44,
    "capacity_utilization_pct": 77.0,
    "period_label": None,
}
_COMPANY_ID = "NSE:MARUTI"


def _common_mocks(monkeypatch):
    monkeypatch.setattr(ari, "put_document", lambda key, data, content_type: None)
    monkeypatch.setattr(ari, "_fetch_nse_annual_report", lambda symbol: _FAKE_FETCH_RESULT)
    monkeypatch.setattr(ari, "locate_sections", lambda pdf_bytes: (_FAKE_SECTIONS, _FAKE_STATEMENT_TYPES))
    monkeypatch.setattr(ari, "_extract_pages_text", lambda pdf_bytes, pages: "fake MD&A text")
    monkeypatch.setattr(ari, "extract_area", lambda area, text: _FAKE_EXTRACTED)
    monkeypatch.setattr(ari.default_llm_client, "last_used_fallback", False)


def test_capacity_and_production_fields_stored(monkeypatch, db):
    _common_mocks(monkeypatch)
    result = ari.ingest_annual_report(db, company_id=_COMPANY_ID, symbol="MARUTI")
    by_key = {r.metric_key: r for r in result}
    assert by_key["cement_installed_capacity_mtpa"].value == 191.36
    assert by_key["cement_production_mmt"].value == 143.83
    assert by_key["cement_production_mmt_prior"].value == 127.44
    assert by_key["capacity_utilization"].value == 77.0
    assert by_key["capacity_utilization"].confidence == "HIGH"
    assert by_key["capacity_utilization"].reported_or_calculated == "REPORTED"


def test_per_tonne_cost_components_never_stored(monkeypatch, db):
    """Real, live-caught risk: the per-tonne energy/raw-material/freight
    breakdown was dropped from extraction after two separate live runs of
    the identical source text returned the raw-material and freight figures
    SWAPPED — this area must never store those three fields."""
    _common_mocks(monkeypatch)
    result = ari.ingest_annual_report(db, company_id=_COMPANY_ID, symbol="MARUTI")
    stored_keys = {r.metric_key for r in result}
    assert "cement_energy_cost_per_tonne" not in stored_keys
    assert "cement_raw_material_cost_per_tonne" not in stored_keys
    assert "cement_freight_cost_per_tonne" not in stored_keys


def test_volume_growth_yoy_computed_from_both_years_in_same_table(monkeypatch, db):
    _common_mocks(monkeypatch)
    result = ari.ingest_annual_report(db, company_id=_COMPANY_ID, symbol="MARUTI")
    by_key = {r.metric_key: r for r in result}
    # (143.83 - 127.44) / 127.44 * 100
    assert by_key["volume_growth_yoy"].value == 12.86
    assert by_key["volume_growth_yoy"].reported_or_calculated == "CALCULATED"


def test_realisation_and_ebitda_per_tonne_use_fiscal_year_not_ttm(monkeypatch, db):
    """The direct regression test for the TTM bug: seeds BOTH a "TTM" pnl_sales
    row and the real fiscal-year (2026-03-31) row, at different values, and
    asserts the per-tonne ratio used the fiscal-year figure."""
    _common_mocks(monkeypatch)
    metric_store.insert_metric_value(
        db, company_id=_COMPANY_ID, metric_key="pnl_sales", period="TTM", value=999999.0, unit="cr",
        statement_type="STANDALONE", source="SCREENER", source_tier=2,
        reported_or_calculated="REPORTED", confidence="MEDIUM",
    )
    metric_store.insert_metric_value(
        db, company_id=_COMPANY_ID, metric_key="pnl_sales", period="2026-03-31", value=82169.65, unit="cr",
        statement_type="STANDALONE", source="SCREENER", source_tier=2,
        reported_or_calculated="REPORTED", confidence="MEDIUM",
    )
    metric_store.insert_metric_value(
        db, company_id=_COMPANY_ID, metric_key="pnl_operating_profit", period="2026-03-31", value=15816.0,
        unit="cr", statement_type="STANDALONE", source="SCREENER", source_tier=2,
        reported_or_calculated="REPORTED", confidence="MEDIUM",
    )

    result = ari.ingest_annual_report(db, company_id=_COMPANY_ID, symbol="MARUTI")
    by_key = {r.metric_key: r for r in result}

    # 82169.65 * 10 / 143.83, NOT 999999.0 * 10 / 143.83
    assert by_key["realisation_per_tonne"].value == round(82169.65 * 10 / 143.83, 2)
    assert by_key["ebitda_per_tonne"].value == round(15816.0 * 10 / 143.83, 2)
    assert by_key["cost_per_tonne"].value == round(
        by_key["realisation_per_tonne"].value - by_key["ebitda_per_tonne"].value, 2)
