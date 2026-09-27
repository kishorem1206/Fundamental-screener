"""Tests for `ingest_annual_report()`'s LLM-fallback guard (real bug found
live 2026-09-20 while building the Chemicals-sector note-extraction areas):
`default_llm_client.last_used_fallback` was never checked after
`extract_area()`, so a Groq rate-limit mid-run could silently fall back to
the much weaker local Ollama model — whose documented failure mode is
silent digit transposition, not an honest null — and the wrong value would
still get persisted tagged confidence="HIGH"/REPORTED. Reproduced exactly
this live on Pidilite Industries' real annual report: a fallback-served
call returned domestic_revenue=12349.33 instead of the correct 12539.33.

Uses `other_liabilities` (an existing, already-wired area) as the test
vehicle rather than one of the new Chemicals areas — the guard lives in the
shared per-area loop in `ingest_annual_report()`, so it protects every area
in `_AREA_METRIC_FIELDS` identically; which area's fields are used here is
incidental to what's under test.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.ingestion import annual_report_ingestion as ari

_FAKE_FETCH_RESULT = (
    b"%PDF-fake",
    "some/annual_report_2026.pdf",
    datetime(2026, 3, 31, tzinfo=timezone.utc),
    "https://example.com/report.pdf",
    "Fake Annual Report FY2026",
)
_FAKE_SECTIONS = {"other_liabilities": [0]}
_FAKE_STATEMENT_TYPES = {"other_liabilities": "STANDALONE"}
_FAKE_EXTRACTED = {"deferred_revenue": 694.0, "accrued_expenses": None, "period_label": None}


def _common_mocks(monkeypatch, *, used_fallback: bool):
    monkeypatch.setattr(ari, "put_document", lambda key, data, content_type: None)
    monkeypatch.setattr(ari, "_fetch_nse_annual_report", lambda symbol: _FAKE_FETCH_RESULT)
    monkeypatch.setattr(ari, "locate_sections", lambda pdf_bytes: (_FAKE_SECTIONS, _FAKE_STATEMENT_TYPES))
    monkeypatch.setattr(ari, "_extract_pages_text", lambda pdf_bytes, pages: "fake note text")
    monkeypatch.setattr(ari, "extract_area", lambda area, text: _FAKE_EXTRACTED)
    monkeypatch.setattr(ari.default_llm_client, "last_used_fallback", used_fallback)


def test_skips_storage_when_fallback_llm_served_the_extraction(monkeypatch, db):
    _common_mocks(monkeypatch, used_fallback=True)
    result = ari.ingest_annual_report(db, company_id="NSE:MARUTI", symbol="MARUTI")
    assert result == []


def test_stores_normally_when_primary_llm_served_the_extraction(monkeypatch, db):
    _common_mocks(monkeypatch, used_fallback=False)
    result = ari.ingest_annual_report(db, company_id="NSE:MARUTI", symbol="MARUTI")
    assert len(result) == 1
    assert result[0].metric_key == "deferred_revenue"
    assert result[0].value == 694.0


def test_single_input_ratio_recovers_numerator_from_an_earlier_run_when_this_run_finds_nothing(monkeypatch, db):
    """Real gap found live on GNFC (2026-09-22, user's own report — "can't
    you find chemical specific metrics anywhere?"): `raw_material_cost`
    (an absolute Cr figure) was captured on an earlier run and sat in the
    ledger, but a LATER run's re-extraction of that same area got Groq
    rate-limited and fell back to Ollama — discarded per the guard tested
    above — leaving nothing fresh for `raw_material_cost` that run. The
    ratio computation (`raw_material_cost_pct`) used to only ever look at
    THIS run's own fresh inserts (`_inserted_by_key`), so it silently never
    got computed even though every ingredient it needs was already on
    file. It must fall back to the ledger's existing value instead of
    requiring both halves to land in the exact same run."""
    from datetime import datetime, timezone

    from app.infrastructure.database import metric_store

    company_id = "NSE:MARUTI"
    period = "2099-03-31"  # a period no real fixture data could collide with
    metric_store.insert_metric_value(
        db, company_id=company_id, metric_key="raw_material_cost", period=period,
        value=3915.25, unit="cr", statement_type="STANDALONE",
        source="NSE_ANNUAL_REPORT", source_tier=1, reported_or_calculated="REPORTED",
        confidence="HIGH", source_date=datetime(2026, 8, 1, tzinfo=timezone.utc),
    )
    metric_store.insert_metric_value(
        db, company_id=company_id, metric_key="pnl_sales", period=period,
        value=7773.0, unit="cr", statement_type="STANDALONE",
        source="SCREENER", source_tier=2, reported_or_calculated="REPORTED", confidence="MEDIUM",
    )
    db.flush()

    # This run locates no sections at all — simulates every area being
    # rate-limited/skipped, so the main per-area loop contributes nothing
    # fresh, and `raw_material_cost_pct` must come from the ledger fallback.
    monkeypatch.setattr(ari, "put_document", lambda key, data, content_type: None)
    monkeypatch.setattr(ari, "_fetch_nse_annual_report", lambda symbol: _FAKE_FETCH_RESULT)
    monkeypatch.setattr(ari, "locate_sections", lambda pdf_bytes: ({}, {}))

    result = ari.ingest_annual_report(db, company_id=company_id, symbol="MARUTI")
    pct_rows = [r for r in result if r.metric_key == "raw_material_cost_pct"]
    assert len(pct_rows) == 1
    assert pct_rows[0].period == period
    assert float(pct_rows[0].value) == round(3915.25 / 7773.0 * 100, 2)
