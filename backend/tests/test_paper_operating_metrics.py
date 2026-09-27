"""Tests for the Forest Materials (Paper)-sector `paper_operating_metrics`
annual-report area and its derived ratios. Mirrors
`test_cement_operating_metrics.py`'s structure — same shared final
metric_key names (`capacity_utilization`, `realisation_per_tonne`,
`ebitda_per_tonne`, `cost_per_tonne`) as CementSector, since a company can
only ever be classified into one sector (no collision risk), and both
sectors share the same per-tonne-commodity-economics vocabulary.
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
_FAKE_SECTIONS = {"paper_operating_metrics": [0]}
_FAKE_STATEMENT_TYPES = {"paper_operating_metrics": "STANDALONE"}
_FAKE_EXTRACTED = {
    "production_tonnes": 434000.0,
    "sales_tonnes": 448000.0,
    "installed_capacity_tonnes": None,
    "capacity_utilization_pct": None,
    "period_label": None,
}
_COMPANY_ID = "NSE:MARUTI"


def _common_mocks(monkeypatch, extracted=None):
    monkeypatch.setattr(ari, "put_document", lambda key, data, content_type: None)
    monkeypatch.setattr(ari, "_fetch_nse_annual_report", lambda symbol: _FAKE_FETCH_RESULT)
    monkeypatch.setattr(ari, "locate_sections", lambda pdf_bytes: (_FAKE_SECTIONS, _FAKE_STATEMENT_TYPES))
    monkeypatch.setattr(ari, "_extract_pages_text", lambda pdf_bytes, pages: "fake MD&A text")
    monkeypatch.setattr(ari, "extract_area", lambda area, text: extracted or _FAKE_EXTRACTED)
    monkeypatch.setattr(ari.default_llm_client, "last_used_fallback", False)


def test_production_and_sales_volume_stored(monkeypatch, db):
    _common_mocks(monkeypatch)
    result = ari.ingest_annual_report(db, company_id=_COMPANY_ID, symbol="MARUTI")
    by_key = {r.metric_key: r for r in result}
    assert by_key["paper_production_tonnes"].value == 434000.0
    assert by_key["paper_sales_tonnes"].value == 448000.0


def test_realisation_ebitda_cost_per_tonne_computed(monkeypatch, db):
    _common_mocks(monkeypatch)
    metric_store.insert_metric_value(
        db, company_id=_COMPANY_ID, metric_key="pnl_sales", period="2026-03-31", value=1500.0, unit="cr",
        statement_type="STANDALONE", source="SCREENER", source_tier=2,
        reported_or_calculated="REPORTED", confidence="MEDIUM",
    )
    metric_store.insert_metric_value(
        db, company_id=_COMPANY_ID, metric_key="pnl_operating_profit", period="2026-03-31", value=225.0,
        unit="cr", statement_type="STANDALONE", source="SCREENER", source_tier=2,
        reported_or_calculated="REPORTED", confidence="MEDIUM",
    )

    result = ari.ingest_annual_report(db, company_id=_COMPANY_ID, symbol="MARUTI")
    by_key = {r.metric_key: r for r in result}

    # 1500 * 1e7 / 448000 (uses SALES volume, not production)
    expected_realisation = round(1500.0 * 1e7 / 448000.0, 2)
    expected_ebitda = round(225.0 * 1e7 / 448000.0, 2)
    assert by_key["realisation_per_tonne"].value == expected_realisation
    assert by_key["ebitda_per_tonne"].value == expected_ebitda
    assert by_key["cost_per_tonne"].value == round(expected_realisation - expected_ebitda, 2)


def test_falls_back_to_production_volume_when_sales_not_disclosed(monkeypatch, db):
    extracted = {
        "production_tonnes": 434000.0, "sales_tonnes": None,
        "installed_capacity_tonnes": None, "capacity_utilization_pct": None,
        "period_label": None,
    }
    _common_mocks(monkeypatch, extracted=extracted)
    metric_store.insert_metric_value(
        db, company_id=_COMPANY_ID, metric_key="pnl_sales", period="2026-03-31", value=1500.0, unit="cr",
        statement_type="STANDALONE", source="SCREENER", source_tier=2,
        reported_or_calculated="REPORTED", confidence="MEDIUM",
    )
    result = ari.ingest_annual_report(db, company_id=_COMPANY_ID, symbol="MARUTI")
    by_key = {r.metric_key: r for r in result}
    assert by_key["realisation_per_tonne"].value == round(1500.0 * 1e7 / 434000.0, 2)


def test_capacity_utilization_computed_when_not_directly_reported(monkeypatch, db):
    """When the LLM doesn't find a direct capacity_utilization_pct but does
    find both production and installed capacity, compute it as a fallback
    (production / capacity * 100) — mirrors the Cement area having no
    equivalent gap (its capacity_utilization_pct is always extracted
    directly from the same clean table as production/capacity)."""
    extracted = {
        "production_tonnes": 434000.0, "sales_tonnes": None,
        "installed_capacity_tonnes": 620000.0, "capacity_utilization_pct": None,
        "period_label": None,
    }
    _common_mocks(monkeypatch, extracted=extracted)
    result = ari.ingest_annual_report(db, company_id=_COMPANY_ID, symbol="MARUTI")
    by_key = {r.metric_key: r for r in result}
    assert by_key["capacity_utilization"].value == round(434000.0 / 620000.0 * 100, 2)
    assert by_key["capacity_utilization"].reported_or_calculated == "CALCULATED"


def test_capacity_utilization_not_double_computed_when_directly_reported(monkeypatch, db):
    """When capacity_utilization_pct IS directly extracted, the fallback
    computation must not also fire and overwrite/duplicate it."""
    extracted = {
        "production_tonnes": 434000.0, "sales_tonnes": None,
        "installed_capacity_tonnes": 620000.0, "capacity_utilization_pct": 70.0,
        "period_label": None,
    }
    _common_mocks(monkeypatch, extracted=extracted)
    result = ari.ingest_annual_report(db, company_id=_COMPANY_ID, symbol="MARUTI")
    cu_rows = [r for r in result if r.metric_key == "capacity_utilization"]
    assert len(cu_rows) == 1
    assert cu_rows[0].value == 70.0
    assert cu_rows[0].reported_or_calculated == "REPORTED"
