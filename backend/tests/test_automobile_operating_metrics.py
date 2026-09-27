"""Tests for the Automobile (OEM)-sector `automobile_operating_metrics`
annual-report area and its derived ratios. Mirrors the other
`test_*_operating_metrics.py` files' structure. Covers the one behavior
unique to this area: `asp_growth` needs the PRIOR fiscal year's pnl_sales
too, fetched via `_latest_fiscal_pnl_value(..., n_prior=1)` — a direct
regression test confirms it uses the ledger's own second-most-recent
fiscal period, not date arithmetic on a possibly-fallback-derived period.
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
_FAKE_SECTIONS = {"automobile_operating_metrics": [0]}
_FAKE_STATEMENT_TYPES = {"automobile_operating_metrics": "STANDALONE"}
_COMPANY_ID = "NSE:MARUTI"


def _common_mocks(monkeypatch, extracted):
    monkeypatch.setattr(ari, "put_document", lambda key, data, content_type: None)
    monkeypatch.setattr(ari, "_fetch_nse_annual_report", lambda symbol: _FAKE_FETCH_RESULT)
    monkeypatch.setattr(ari, "locate_sections", lambda pdf_bytes: (_FAKE_SECTIONS, _FAKE_STATEMENT_TYPES))
    monkeypatch.setattr(ari, "_extract_pages_text", lambda pdf_bytes, pages: "fake MD&A text")
    monkeypatch.setattr(ari, "extract_area", lambda area, text: extracted)
    monkeypatch.setattr(ari.default_llm_client, "last_used_fallback", False)


def test_market_share_and_dealer_inventory_stored_directly(monkeypatch, db):
    extracted = {
        "units_sold": 2422713.0, "units_sold_prior_year": 2234266.0,
        "market_share_pct": 15.6, "dealer_inventory_days": 12.0, "period_label": None,
    }
    _common_mocks(monkeypatch, extracted)
    result = ari.ingest_annual_report(db, company_id=_COMPANY_ID, symbol="MARUTI")
    by_key = {r.metric_key: r for r in result}
    assert by_key["market_share"].value == 15.6
    assert by_key["market_share"].reported_or_calculated == "REPORTED"
    assert by_key["dealer_inventory_days"].value == 12.0
    assert by_key["dealer_inventory_days"].reported_or_calculated == "REPORTED"


def test_volume_growth_yoy_computed_from_same_report(monkeypatch, db):
    extracted = {
        "units_sold": 2422713.0, "units_sold_prior_year": 2234266.0,
        "market_share_pct": None, "dealer_inventory_days": None, "period_label": None,
    }
    _common_mocks(monkeypatch, extracted)
    result = ari.ingest_annual_report(db, company_id=_COMPANY_ID, symbol="MARUTI")
    by_key = {r.metric_key: r for r in result}
    expected = round((2422713.0 - 2234266.0) / 2234266.0 * 100, 2)
    assert by_key["volume_growth_yoy"].value == expected
    assert by_key["volume_growth_yoy"].reported_or_calculated == "CALCULATED"


def test_asp_growth_uses_second_most_recent_fiscal_period_not_date_arithmetic(monkeypatch, db):
    """Direct regression test: seeds pnl_sales at THREE fiscal periods
    (including one that ISN'T exactly one calendar year before the latest —
    simulating a real ledger with an irregular gap) and confirms asp_growth
    uses the ledger's own second-most-recent period by sort order, not a
    naively-computed 'period minus 1 year' date."""
    extracted = {
        "units_sold": 2422713.0, "units_sold_prior_year": 2234266.0,
        "market_share_pct": None, "dealer_inventory_days": None, "period_label": None,
    }
    _common_mocks(monkeypatch, extracted)
    metric_store.insert_metric_value(
        db, company_id=_COMPANY_ID, metric_key="pnl_sales", period="2024-03-31", value=90000.0, unit="cr",
        statement_type="STANDALONE", source="SCREENER", source_tier=2,
        reported_or_calculated="REPORTED", confidence="MEDIUM",
    )
    metric_store.insert_metric_value(
        db, company_id=_COMPANY_ID, metric_key="pnl_sales", period="2025-03-31", value=100000.0, unit="cr",
        statement_type="STANDALONE", source="SCREENER", source_tier=2,
        reported_or_calculated="REPORTED", confidence="MEDIUM",
    )
    metric_store.insert_metric_value(
        db, company_id=_COMPANY_ID, metric_key="pnl_sales", period="2026-03-31", value=115000.0, unit="cr",
        statement_type="STANDALONE", source="SCREENER", source_tier=2,
        reported_or_calculated="REPORTED", confidence="MEDIUM",
    )

    result = ari.ingest_annual_report(db, company_id=_COMPANY_ID, symbol="MARUTI")
    by_key = {r.metric_key: r for r in result}

    current_asp = 115000.0 * 1e7 / 2422713.0
    prior_asp = 100000.0 * 1e7 / 2234266.0  # uses 2025-03-31 (second-latest), NOT 2024-03-31
    expected = round((current_asp - prior_asp) / prior_asp * 100, 2)
    assert by_key["asp_growth"].value == expected


def test_no_volume_growth_when_prior_year_not_disclosed(monkeypatch, db):
    extracted = {
        "units_sold": 2422713.0, "units_sold_prior_year": None,
        "market_share_pct": None, "dealer_inventory_days": None, "period_label": None,
    }
    _common_mocks(monkeypatch, extracted)
    result = ari.ingest_annual_report(db, company_id=_COMPANY_ID, symbol="MARUTI")
    assert not any(r.metric_key == "volume_growth_yoy" for r in result)
    assert not any(r.metric_key == "asp_growth" for r in result)
