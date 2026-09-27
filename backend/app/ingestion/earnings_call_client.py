"""Earnings-call transcript ingestion — sector-agnostic by design, not
IT-only. Any listed company can file one; confirmed live (2026-09-12) that
Infosys files its transcript as a Regulation 30 disclosure on BSE, real
text layer (no OCR needed), right alongside — not part of — the standard
financial-results filing. Reuses bse_client.py's session/download/document-
storage machinery, since it's the same exchange announcements feed, just a
different headline pattern.

Two layers, deliberately separate:
  1. `ingest_earnings_call_transcript()` — find, download, durably store
     (Stage 7's `documents` table + MinIO) the transcript. Runs for ANY
     company, any sector — no extraction happens here.
  2. One targeted LLM call per sector-specific extraction schema, over the
     same located-and-density-ranked text: `extract_it_operational_metrics()`
     (attrition_rate/utilization_rate/deal_wins_tcv, declared in
     app/sectors/it_services.py, built 2026-09-12) and
     `extract_fintech_operational_metrics()` (gtv_growth/take_rate/
     contribution_margin/merchant_count, declared in app/sectors/fintech.py,
     built 2026-09-17 — confirmed live that Pine Labs' own transcript
     discusses GTV growth and take-rate trend by name in exactly this kind
     of prepared-remarks/Q&A text). `_EXTRACTION_JOBS` is the registry of
     these — a new sector adds one entry (keyword terms, extraction
     function, field_map) plus its own `extract_<sector>_metrics` flag on
     `ingest_earnings_call_transcript()`, without touching the fetch/store/
     locate machinery.
"""
from __future__ import annotations

import io
import re
import uuid
from datetime import datetime, timezone

import pdfplumber
from sqlalchemy.orm import Session

from app.ingestion import bse_client
from app.infrastructure.database import metric_store
from app.infrastructure.database.models import Document
from app.infrastructure.storage.minio_client import put_document
from app.llm.client import llm_client as default_llm_client
from app.logger import logger

_TRANSCRIPT_HEADLINE_RE = re.compile(
    r"(earnings call transcript|con\s?call transcript|analyst call transcript|"
    r"investor call transcript|transcript of.*(earnings|con\s?call|investor))",
    re.I,
)

_MAX_TOKENS = 3000
_MAX_CHARS = 16000  # density-selected pages still run longer than a single
                     # disclosure area's worth of text (unlike banking_
                     # ingestion.py's 8000) — confirmed necessary on Infosys's
                     # real transcript, where attrition/utilization landed
                     # past character 12,000 even after density ranking

_IT_OPERATIONAL_PROMPT = (
    "Extract IT-services operational KPIs from this earnings call transcript "
    "(CFO/CEO prepared remarks, usually near the start). If a field isn't "
    "stated, return null. Never invent or estimate a number. Respond with "
    "a single JSON object:\n"
    "{\n"
    '  "period_label": "quarter/period referenced, e.g. \\"Q1 FY27\\", or null",\n'
    '  "attrition_pct": number|null,\n'
    '  "utilization_pct": number|null,\n'
    '  "large_deal_tcv_usd_bn": number|null\n'
    "}"
)

# Fintech schema added 2026-09-17, for the new FintechSector
# (app/sectors/fintech.py) — confirmed live on Pine Labs' own concall
# transcript that management discusses GTV growth and take-rate trend by
# name ("the 4% GTV growth...", "our take rate... in the flow business...
# 28 bps") in exactly this kind of prepared-remarks/Q&A text, the same
# shape the IT prompt above already extracts attrition/utilization from.
_FINTECH_OPERATIONAL_PROMPT = (
    "Extract fintech/payments operational KPIs from this earnings call "
    "transcript (CFO/CEO prepared remarks and Q&A). Companies may call "
    "payment volume \"GTV\" (Gross Transaction/Merchandise Value) or \"TPV\" "
    "(Total Payment Value) — treat them as the same concept. Take rate may "
    "be stated in %, bps, or both (100 bps = 1%; convert % to bps by "
    "multiplying by 100). If a field isn't stated, return null. Never "
    "invent or estimate a number. Respond with a single JSON object:\n"
    "{\n"
    '  "period_label": "quarter/period referenced, e.g. \\"Q1 FY27\\", or null",\n'
    '  "gtv_growth_pct": number|null,\n'
    '  "take_rate_bps": number|null,\n'
    '  "contribution_margin_pct": number|null,\n'
    '  "merchant_count": number|null\n'
    "}"
)


# FMCG schema (2026-09-20). Investor decks often omit numeric volume growth
# (Britannia, Emami, Nestle: chart-only or qualitative), but managements
# state it in prepared remarks/Q&A — confirmed live: Britannia's CFO answers
# "what was the volume growth in 1Q" directly; Godrej Consumer and HUL
# discuss UVG by name. The prompt is deliberately strict because transcripts
# are full of analyst questions, forward guidance and multi-year CAGRs that
# look like the target but are not.
_FMCG_OPERATIONAL_PROMPT = (
    "Extract FMCG operating KPIs from this earnings call transcript. ONLY use a figure that "
    "MANAGEMENT states (prepared remarks or an answer) — never a number that appears only inside an "
    "analyst's question. All fields refer to the company's WHOLE business (or whole India business) for "
    "the CURRENT reported quarter versus the same quarter last year. Rules: (1) volume_growth_pct = "
    "underlying volume growth / UVG / volume growth as an explicit number (a decline is negative; "
    "'flat' = 0). Return null for qualitative bands ('high single digit', 'double digit'), forward "
    "guidance or targets, multi-year CAGRs, full-year figures, or a single category/segment/brand. "
    "(2) premium_share_pct = premium/premiumisation portfolio as an explicit % of company sales or "
    "revenue; null if only described in words or for one category. (3) rural_share_pct = rural as an "
    "explicit % of company sales; null if only growth commentary ('rural growing faster'). Never invent, "
    "infer or average numbers. Respond with a single JSON object:\n"
    "{\n"
    '  "period_label": "quarter referenced, e.g. \\"Q1 FY27\\", or null",\n'
    '  "volume_growth_pct": number|null,\n'
    '  "premium_share_pct": number|null,\n'
    '  "rural_share_pct": number|null\n'
    "}"
)

_FMCG_KPI_TERMS = ["volume growth", "uvg", "underlying volume", "volumes", "premium", "rural"]


def find_latest_earnings_call_transcript(
    scrip_code: str, session=None, lookback_days: int = 150
) -> dict | None:
    """Most recent earnings-call/press-conference transcript filing for a
    BSE scrip code, or None if nothing matches in the window. Searches the
    full announcements feed (not the "Result" category — transcripts are
    filed under the broader "Company Update"/Reg 30 category)."""
    from datetime import timedelta

    s = session or bse_client._session()
    to_date = datetime.now()
    from_date = to_date - timedelta(days=lookback_days)
    params = {
        "pageno": 1, "strCat": -1, "subcategory": "-1",
        "strPrevDate": from_date.strftime("%Y%m%d"), "strToDate": to_date.strftime("%Y%m%d"),
        "strSearch": "P", "strscrip": scrip_code, "strType": "C",
    }
    r = s.get(f"{bse_client.API_URL}/AnnSubCategoryGetData/w", params=params, timeout=20)
    r.raise_for_status()
    rows = [
        row for row in r.json().get("Table", [])
        if row.get("ATTACHMENTNAME") and _TRANSCRIPT_HEADLINE_RE.search(row.get("NEWSSUB") or "")
    ]
    if not rows:
        return None
    rows.sort(key=lambda row: row.get("NEWS_DT", ""), reverse=True)
    return rows[0]


_KPI_TERMS = ["attrition", "utilization", "tcv", "large deal", "headcount", "dso", "net new"]

# Fintech equivalent of _KPI_TERMS — confirmed live against Pine Labs' real
# concall_chunks: "gtv"/"tpv"/"take rate"/"merchant" all appear repeatedly
# in genuine management commentary, not just boilerplate.
_FINTECH_KPI_TERMS = ["gtv", "tpv", "take rate", "merchant", "contribution margin",
                      "payment volume", "active users"]


def _locate_kpi_text(pdf_bytes: bytes, terms: list[str] = _KPI_TERMS, max_pages: int = 10) -> str:
    """Scan every page for KPI keyword density, return text from the
    densest pages — ranked by hit count, not document order, then re-sorted
    back into reading order for the selected subset. A naive "first N
    pages" (or even "first N *hit* pages in document order") assumption was
    wrong in practice — confirmed on Infosys's real Q1 FY27 transcript, a
    Q&A-heavy 48-page document where the specific sentences mentioning
    "attrition" and "utilization" each individually fell past character
    12,000-30,000 of the hit-page text even after narrowing to pages that
    merely *mention* a keyword once — sending pages in document order still
    let low-density early pages crowd out the dense summary paragraphs.
    Ranking by density first (a proxy for "the CFO's number-dense recap,"
    not "a page where a journalist happened to use the word once") fixes
    this within a real LLM prompt-size budget. Same keyword-hit-page
    principle as annual_report_locator.py, without that module's windowing
    (unnecessary for a document this short)."""
    scored: list[tuple[int, int]] = []  # (page_idx, hit_count)
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        page_texts = [(p.extract_text() or "") for p in pdf.pages]
        for i, text in enumerate(page_texts):
            low = text.lower()
            count = sum(low.count(term) for term in terms)
            if count:
                scored.append((i, count))
        scored.sort(key=lambda pc: pc[1], reverse=True)
        selected = sorted(p for p, _ in scored[:max_pages])
        return "\n\n".join(page_texts[i] for i in selected)


def extract_it_operational_metrics(text: str, llm_client=None) -> dict:
    client = llm_client or default_llm_client
    return client.chat_json(_IT_OPERATIONAL_PROMPT, text[:_MAX_CHARS], max_tokens=_MAX_TOKENS)


def extract_fintech_operational_metrics(text: str, llm_client=None) -> dict:
    client = llm_client or default_llm_client
    return client.chat_json(_FINTECH_OPERATIONAL_PROMPT, text[:_MAX_CHARS], max_tokens=_MAX_TOKENS)


def extract_fmcg_operational_metrics(text: str, llm_client=None) -> dict:
    client = llm_client or default_llm_client
    return client.chat_json(_FMCG_OPERATIONAL_PROMPT, text[:_MAX_CHARS], max_tokens=_MAX_TOKENS)


# One entry per sector-specific extraction schema — (keyword terms for
# page-density ranking, extraction function, {metric_key: (llm_field, unit)}).
# Adding a new sector's schema means adding one entry here plus a new
# `extract_<sector>_metrics=True` flag on `ingest_earnings_call_transcript()`
# below, not touching the fetch/store/locate machinery.
_EXTRACTION_JOBS = {
    "it": (_KPI_TERMS, extract_it_operational_metrics, {
        "attrition_rate": ("attrition_pct", "%"),
        "utilization_rate": ("utilization_pct", "%"),
        "deal_wins_tcv": ("large_deal_tcv_usd_bn", "USD Bn"),
    }),
    "fintech": (_FINTECH_KPI_TERMS, extract_fintech_operational_metrics, {
        "gtv_growth": ("gtv_growth_pct", "%"),
        "take_rate": ("take_rate_bps", "bps"),
        "contribution_margin": ("contribution_margin_pct", "%"),
        "merchant_count": ("merchant_count", "count"),
    }),
    "fmcg": (_FMCG_KPI_TERMS, extract_fmcg_operational_metrics, {
        "volume_growth_yoy": ("volume_growth_pct", "%"),
        "premiumization_pct": ("premium_share_pct", "%"),
        "rural_revenue_pct": ("rural_share_pct", "%"),
    }),
}


def _store_transcript_document(db: Session, company_id: str, filing: dict, pdf_bytes: bytes) -> None:
    attachment = filing.get("ATTACHMENTNAME", "unknown")
    storage_key = f"bse_earnings_call/{company_id}/{attachment}"
    try:
        if db.query(Document).filter_by(storage_key=storage_key).first():
            return
        sha256 = put_document(storage_key, pdf_bytes, content_type="application/pdf")
        if sha256 is None:
            return
        db.add(Document(
            id=str(uuid.uuid4()), company_id=company_id, source="BSE_EARNINGS_CALL",
            document_type="EARNINGS_CALL_TRANSCRIPT",
            url=filing.get("NSURL") or bse_client.ATTACHMENT_URL.format(name=attachment),
            sha256=sha256, storage_key=storage_key, file_size=len(pdf_bytes),
            retrieved_at=datetime.now(timezone.utc),
        ))
        db.flush()
    except Exception as e:
        logger.warning("earnings_call_client: document storage failed", company_id=company_id, error=str(e))


def ingest_earnings_call_transcript(
    db: Session, company_id: str, symbol: str, *,
    extract_it_metrics: bool = False, extract_fintech_metrics: bool = False,
    extract_fmcg_metrics: bool = False,
) -> dict:
    """Find, durably store, and (only for flagged sectors) extract
    operational KPIs from the latest earnings-call transcript. Storage
    always happens regardless of the flags — the document itself is useful
    even without a sector-specific extraction schema. Multiple flags can be
    true at once (harmless — a company's own classification should only
    ever match one sector, so in practice at most one fires per call), each
    running its own `_EXTRACTION_JOBS` entry against the same downloaded
    PDF. Never raises — logs and returns zero counts on failure, matching
    every other ingestion path's contract."""
    try:
        session = bse_client._session()
        scrip_code = bse_client.resolve_scrip_code(symbol, session=session)
        if not scrip_code:
            logger.warning("earnings_call_client: could not resolve BSE scrip code", symbol=symbol)
            return {"stored": False, "metrics_inserted": 0}
        filing = find_latest_earnings_call_transcript(scrip_code, session=session)
        if not filing:
            logger.info("earnings_call_client: no transcript found", symbol=symbol)
            return {"stored": False, "metrics_inserted": 0}
        pdf_bytes = bse_client.download_filing_pdf(filing["ATTACHMENTNAME"], session=session)
    except Exception as e:
        logger.warning("earnings_call_client: fetch/download failed", symbol=symbol, error=str(e))
        return {"stored": False, "metrics_inserted": 0}

    _store_transcript_document(db, company_id, filing, pdf_bytes)

    jobs = []
    if extract_it_metrics:
        jobs.append(_EXTRACTION_JOBS["it"])
    if extract_fintech_metrics:
        jobs.append(_EXTRACTION_JOBS["fintech"])
    if extract_fmcg_metrics:
        jobs.append(_EXTRACTION_JOBS["fmcg"])
    if not jobs:
        return {"stored": True, "metrics_inserted": 0}

    news_dt = filing.get("NEWS_DT", "")
    try:
        fallback_date = datetime.fromisoformat(news_dt) if news_dt else datetime.now()
    except ValueError:
        fallback_date = datetime.now()
    period = fallback_date.date().isoformat()
    source_url = filing.get("NSURL") or bse_client.ATTACHMENT_URL.format(name=filing["ATTACHMENTNAME"])
    source_document = filing.get("NEWSSUB", "BSE earnings call transcript")

    inserted = 0
    for terms, extract_fn, field_map in jobs:
        try:
            text = _locate_kpi_text(pdf_bytes, terms=terms)
            if not text:
                continue
            extracted = extract_fn(text)
        except Exception as e:
            logger.warning("earnings_call_client: extraction failed", symbol=symbol, error=str(e))
            continue

        for metric_key, (field, unit) in field_map.items():
            value = extracted.get(field)
            if value is None:
                continue
            try:
                value = float(value)
            except (TypeError, ValueError):
                continue
            row = metric_store.insert_metric_value(
                db, company_id=company_id, metric_key=metric_key, period=period,
                value=value, unit=unit, source="BSE_EARNINGS_CALL", source_tier=1,
                reported_or_calculated="REPORTED", confidence="HIGH",
                source_url=source_url, source_document=source_document,
                source_date=fallback_date, raw_reported_value=str(extracted.get(field)),
            )
            if row is not None:
                inserted += 1

    logger.info("earnings_call_client: ingested", symbol=symbol, metrics_inserted=inserted)
    return {"stored": True, "metrics_inserted": inserted}
