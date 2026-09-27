"""FMCG extraction job in `earnings_call_client._EXTRACTION_JOBS` — fills the
FMCG NA fields that quarterly decks usually can't (Britannia/Nestle: no
numeric volume growth in the deck, but management states it on the call).

Reference statements, each verified by string search in the real Q1 FY27
transcripts: Britannia CFO "the volume growth that we had for the quarter
was close to 9%"; Nestle "premium portfolio, the contribution has grown
rapidly from 11% to 14%".
"""
from __future__ import annotations

from datetime import datetime

from app.infrastructure.database import metric_store
from app.ingestion import earnings_call_client as ecc
from app.sectors.fmcg import FMCGSector


class _FakeLLM:
    def __init__(self, out):
        self.out, self.seen = out, None

    def chat_json(self, prompt, text, max_tokens=0):
        self.seen = (prompt, text)
        return self.out


def test_job_fields_are_real_fmcg_sector_metrics():
    """Guards drift: every metric_key the job writes must be a declared,
    non-yfinance FMCGSector metric — otherwise the ledger bridge would
    never surface it."""
    fw = {m.name: m for m in FMCGSector().key_metrics()}
    _, _, field_map = ecc._EXTRACTION_JOBS["fmcg"]
    for metric_key in field_map:
        assert metric_key in fw and fw[metric_key].available_from_yfinance is False


def test_prompt_rejects_the_lookalikes_transcripts_are_full_of():
    p = ecc._FMCG_OPERATIONAL_PROMPT.lower()
    for guard in ("analyst's question", "guidance", "cagr", "qualitative", "never invent"):
        assert guard in p


def test_extract_passes_transcript_text_to_the_llm():
    llm = _FakeLLM({"volume_growth_pct": 9})
    out = ecc.extract_fmcg_operational_metrics("volume growth ... close to 9%", llm_client=llm)
    assert out == {"volume_growth_pct": 9}
    assert "close to 9%" in llm.seen[1]


def test_ingest_stores_only_stated_values(monkeypatch, db):
    """Britannia-shaped: volume stated, premium/rural not -> exactly one row."""
    monkeypatch.setattr(ecc.bse_client, "_session", lambda: object())
    monkeypatch.setattr(ecc.bse_client, "resolve_scrip_code", lambda symbol, session=None: "500825")
    monkeypatch.setattr(ecc, "find_latest_earnings_call_transcript", lambda code, session=None: {
        "ATTACHMENTNAME": "x.pdf", "NEWS_DT": "2026-08-12T19:22:18", "NEWSSUB": "Transcript of Q1 FY27 call"})
    monkeypatch.setattr(ecc.bse_client, "download_filing_pdf", lambda name, session=None: b"%PDF")
    monkeypatch.setattr(ecc, "_store_transcript_document", lambda *a, **k: None)
    monkeypatch.setattr(ecc, "_locate_kpi_text", lambda pdf, terms=None: "some transcript text")
    job = ecc._EXTRACTION_JOBS["fmcg"]
    monkeypatch.setitem(ecc._EXTRACTION_JOBS, "fmcg", (job[0], lambda text: {
        "volume_growth_pct": 9, "premium_share_pct": None, "rural_share_pct": None}, job[2]))

    res = ecc.ingest_earnings_call_transcript(db, "NSE:BRITANNIA", "BRITANNIA", extract_fmcg_metrics=True)
    assert res == {"stored": True, "metrics_inserted": 1}
    row = metric_store.get_latest_period_value(db, "NSE:BRITANNIA", "volume_growth_yoy")
    assert float(row.value) == 9.0
    assert row.source == "BSE_EARNINGS_CALL"
    assert metric_store.get_latest_period_value(db, "NSE:BRITANNIA", "premiumization_pct") is None
