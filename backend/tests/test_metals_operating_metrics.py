"""Tests for the Metals & Mining-sector `metals_operating_metrics`
annual-report area and its derived ratios. Mirrors
`test_cement_operating_metrics.py`/`test_paper_operating_metrics.py`'s
structure. Covers the one behavior unique to this area: preferring a
company's DIRECTLY-reported EBITDA/tonne (common in steel MD&A narrative)
over the derived pnl_operating_profit/volume figure — and never
overwriting that REPORTED value with a lower-confidence CALCULATED one.
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
_FAKE_SECTIONS = {"metals_operating_metrics": [0]}
_FAKE_STATEMENT_TYPES = {"metals_operating_metrics": "STANDALONE"}
_COMPANY_ID = "NSE:MARUTI"


def _common_mocks(monkeypatch, extracted):
    monkeypatch.setattr(ari, "put_document", lambda key, data, content_type: None)
    monkeypatch.setattr(ari, "_fetch_nse_annual_report", lambda symbol: _FAKE_FETCH_RESULT)
    monkeypatch.setattr(ari, "locate_sections", lambda pdf_bytes: (_FAKE_SECTIONS, _FAKE_STATEMENT_TYPES))
    monkeypatch.setattr(ari, "_extract_pages_text", lambda pdf_bytes, pages: "fake MD&A text")
    monkeypatch.setattr(ari, "extract_area", lambda area, text: extracted)
    monkeypatch.setattr(ari.default_llm_client, "last_used_fallback", False)


def test_production_volume_growth_computed_from_same_report(monkeypatch, db):
    extracted = {
        "production_million_tonnes": 21.30, "production_million_tonnes_prior_year": 22.47,
        "sales_million_tonnes": None, "ebitda_per_tonne_reported": None, "period_label": None,
    }
    _common_mocks(monkeypatch, extracted)
    result = ari.ingest_annual_report(db, company_id=_COMPANY_ID, symbol="MARUTI")
    by_key = {r.metric_key: r for r in result}
    assert by_key["production_volume_growth"].value == round((21.30 - 22.47) / 22.47 * 100, 2)
    assert by_key["production_volume_growth"].reported_or_calculated == "CALCULATED"


def test_directly_reported_ebitda_per_tonne_used_as_is(monkeypatch, db):
    extracted = {
        "production_million_tonnes": 21.30, "production_million_tonnes_prior_year": None,
        "sales_million_tonnes": 22.40, "ebitda_per_tonne_reported": 9015.0, "period_label": None,
    }
    _common_mocks(monkeypatch, extracted)
    result = ari.ingest_annual_report(db, company_id=_COMPANY_ID, symbol="MARUTI")
    by_key = {r.metric_key: r for r in result}
    ebitda_rows = [r for r in result if r.metric_key == "ebitda_per_tonne"]
    assert len(ebitda_rows) == 1
    assert ebitda_rows[0].value == 9015.0
    assert ebitda_rows[0].reported_or_calculated == "REPORTED"
    assert ebitda_rows[0].confidence == "HIGH"


def test_reported_ebitda_per_tonne_never_overwritten_by_derived_calculation(monkeypatch, db):
    """The direct regression test for the preference rule: even when
    pnl_sales/pnl_operating_profit ARE available (which would let the
    derivation branch also fire), the directly-reported figure must win,
    not get silently replaced by a second, lower-confidence CALCULATED row."""
    extracted = {
        "production_million_tonnes": 21.30, "production_million_tonnes_prior_year": None,
        "sales_million_tonnes": 22.40, "ebitda_per_tonne_reported": 9015.0, "period_label": None,
    }
    _common_mocks(monkeypatch, extracted)
    metric_store.insert_metric_value(
        db, company_id=_COMPANY_ID, metric_key="pnl_sales", period="2026-03-31", value=132847.0, unit="cr",
        statement_type="STANDALONE", source="SCREENER", source_tier=2,
        reported_or_calculated="REPORTED", confidence="MEDIUM",
    )
    metric_store.insert_metric_value(
        db, company_id=_COMPANY_ID, metric_key="pnl_operating_profit", period="2026-03-31", value=20191.0,
        unit="cr", statement_type="STANDALONE", source="SCREENER", source_tier=2,
        reported_or_calculated="REPORTED", confidence="MEDIUM",
    )
    result = ari.ingest_annual_report(db, company_id=_COMPANY_ID, symbol="MARUTI")
    ebitda_rows = [r for r in result if r.metric_key == "ebitda_per_tonne"]
    assert len(ebitda_rows) == 1, "must not insert a second, derived ebitda_per_tonne row"
    assert ebitda_rows[0].value == 9015.0
    assert ebitda_rows[0].reported_or_calculated == "REPORTED"

    # cost_per_tonne must use the REPORTED ebitda_per_tonne in its bridge,
    # not silently recompute a derived one.
    cost_rows = [r for r in result if r.metric_key == "cost_per_tonne"]
    assert len(cost_rows) == 1
    expected_realisation = round(132847.0 * 10 / 22.40, 2)
    assert cost_rows[0].value == round(expected_realisation - 9015.0, 2)


def test_ebitda_per_tonne_derived_when_no_direct_figure_given(monkeypatch, db):
    extracted = {
        "production_million_tonnes": 21.30, "production_million_tonnes_prior_year": None,
        "sales_million_tonnes": 22.40, "ebitda_per_tonne_reported": None, "period_label": None,
    }
    _common_mocks(monkeypatch, extracted)
    metric_store.insert_metric_value(
        db, company_id=_COMPANY_ID, metric_key="pnl_operating_profit", period="2026-03-31", value=20191.0,
        unit="cr", statement_type="STANDALONE", source="SCREENER", source_tier=2,
        reported_or_calculated="REPORTED", confidence="MEDIUM",
    )
    result = ari.ingest_annual_report(db, company_id=_COMPANY_ID, symbol="MARUTI")
    by_key = {r.metric_key: r for r in result}
    assert by_key["ebitda_per_tonne"].value == round(20191.0 * 10 / 22.40, 2)
    assert by_key["ebitda_per_tonne"].reported_or_calculated == "CALCULATED"


def test_volume_prefers_sales_over_production_for_per_tonne_ratios(monkeypatch, db):
    extracted = {
        "production_million_tonnes": 21.30, "production_million_tonnes_prior_year": None,
        "sales_million_tonnes": 22.40, "ebitda_per_tonne_reported": None, "period_label": None,
    }
    _common_mocks(monkeypatch, extracted)
    metric_store.insert_metric_value(
        db, company_id=_COMPANY_ID, metric_key="pnl_sales", period="2026-03-31", value=132847.0, unit="cr",
        statement_type="STANDALONE", source="SCREENER", source_tier=2,
        reported_or_calculated="REPORTED", confidence="MEDIUM",
    )
    result = ari.ingest_annual_report(db, company_id=_COMPANY_ID, symbol="MARUTI")
    by_key = {r.metric_key: r for r in result}
    # 132847 * 10 / 22.40 (sales), NOT / 21.30 (production)
    assert by_key["realisation_per_tonne"].value == round(132847.0 * 10 / 22.40, 2)
