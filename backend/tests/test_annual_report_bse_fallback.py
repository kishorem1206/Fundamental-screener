"""Tests for `annual_report_ingestion.py`'s NSE-primary/BSE-secondary
fallback (real gap found live 2026-09-16 on Pine Labs, a very recently
listed company with zero NSE annual-report coverage but a real FY2025-26
report on BSE — confirmed live, scrip 544606). Mocks
`_fetch_nse_annual_report`/`_fetch_bse_annual_report` directly (rather than
the raw HTTP clients) to isolate the fallback DECISION logic under test
from the PDF-locate-extract pipeline, which has its own test coverage
needs (LLM calls, pdfplumber) out of scope here.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.ingestion import annual_report_ingestion as ari

_FAKE_FETCH_RESULT = (
    b"%PDF-fake",  # pdf_bytes
    "some/annual_report_2026.pdf",  # storage_key_suffix
    datetime(2026, 3, 31, tzinfo=timezone.utc),  # fallback_date
    "https://example.com/report.pdf",  # source_url
    "Fake Annual Report FY2026",  # source_document
)


def test_uses_nse_when_nse_has_data(monkeypatch, db):
    calls = {"bse": 0}
    monkeypatch.setattr(ari, "put_document", lambda key, data, content_type: None)
    monkeypatch.setattr(ari, "_fetch_nse_annual_report", lambda symbol: _FAKE_FETCH_RESULT)

    def _bse_should_not_be_called(symbol):
        calls["bse"] += 1
        return _FAKE_FETCH_RESULT
    monkeypatch.setattr(ari, "_fetch_bse_annual_report", _bse_should_not_be_called)
    monkeypatch.setattr(ari, "locate_sections", lambda pdf_bytes: ({}, {}))

    ari.ingest_annual_report(db, company_id="NSE:MARUTI", symbol="MARUTI")
    assert calls["bse"] == 0


def test_falls_back_to_bse_when_nse_has_nothing(monkeypatch, db):
    monkeypatch.setattr(ari, "put_document", lambda key, data, content_type: None)
    monkeypatch.setattr(ari, "_fetch_nse_annual_report", lambda symbol: None)
    calls = {"bse": 0}

    def _bse(symbol):
        calls["bse"] += 1
        return _FAKE_FETCH_RESULT
    monkeypatch.setattr(ari, "_fetch_bse_annual_report", _bse)
    monkeypatch.setattr(ari, "locate_sections", lambda pdf_bytes: ({}, {}))

    ari.ingest_annual_report(db, company_id="NSE:PINELABS", symbol="PINELABS")
    assert calls["bse"] == 1


def test_falls_back_to_bse_when_nse_raises(monkeypatch, db):
    monkeypatch.setattr(ari, "put_document", lambda key, data, content_type: None)

    def _nse_boom(symbol):
        raise RuntimeError("NSE unreachable")
    monkeypatch.setattr(ari, "_fetch_nse_annual_report", _nse_boom)
    calls = {"bse": 0}

    def _bse(symbol):
        calls["bse"] += 1
        return _FAKE_FETCH_RESULT
    monkeypatch.setattr(ari, "_fetch_bse_annual_report", _bse)
    monkeypatch.setattr(ari, "locate_sections", lambda pdf_bytes: ({}, {}))

    ari.ingest_annual_report(db, company_id="NSE:TEST", symbol="TEST")
    assert calls["bse"] == 1


def test_document_tagged_with_correct_source_when_bse_used(monkeypatch, db):
    from app.infrastructure.database.models import Document, Stock

    company_id = "TEST:ARI_BSE_FIXTURE"
    if db.get(Stock, company_id) is None:
        now = datetime.now(timezone.utc)
        db.add(Stock(id=company_id, symbol="ARI_BSE_FIXTURE", exchange="TEST",
                      company_name="ARI BSE Fixture Co.", is_active=True, created_at=now, updated_at=now))
        db.flush()

    monkeypatch.setattr(ari, "_fetch_nse_annual_report", lambda symbol: None)
    monkeypatch.setattr(ari, "_fetch_bse_annual_report", lambda symbol: _FAKE_FETCH_RESULT)
    monkeypatch.setattr(ari, "locate_sections", lambda pdf_bytes: ({}, {}))
    monkeypatch.setattr(ari, "put_document", lambda key, data, content_type: "fake_sha256")

    ari.ingest_annual_report(db, company_id=company_id, symbol="ARI_BSE_FIXTURE")
    doc = db.query(Document).filter_by(company_id=company_id, document_type="ANNUAL_REPORT").first()
    assert doc is not None
    assert doc.source == "BSE_ANNUAL_REPORT"
    assert doc.storage_key == f"{company_id}/some/annual_report_2026.pdf"


def test_returns_empty_gracefully_when_both_sources_have_nothing(monkeypatch, db):
    monkeypatch.setattr(ari, "_fetch_nse_annual_report", lambda symbol: None)
    monkeypatch.setattr(ari, "_fetch_bse_annual_report", lambda symbol: None)

    result = ari.ingest_annual_report(db, company_id="NSE:NOPE", symbol="NOPE")
    assert result == []


def test_returns_empty_gracefully_when_both_sources_raise(monkeypatch, db):
    def _boom(symbol):
        raise RuntimeError("network down")
    monkeypatch.setattr(ari, "_fetch_nse_annual_report", _boom)
    monkeypatch.setattr(ari, "_fetch_bse_annual_report", _boom)

    result = ari.ingest_annual_report(db, company_id="NSE:NOPE2", symbol="NOPE2")
    assert result == []
