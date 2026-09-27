"""Orchestrates banking-metric ingestion for the pilot sector, per
sector_frameworks/banking.md sections 20-26 (source hierarchy + provenance).

Two BSE-sourced tiers land in fa_metric_data_points:
  - BSE_RESULTS_API: structured, tagged fields (currently just CAR%) — HIGH confidence.
  - BSE_FILING_OCR: OCR + LLM extraction from the actual SEBI-format results PDF —
    MEDIUM confidence always (OCR misreads digits occasionally; never claim HIGH).

Two metrics (cost_to_income_ratio, credit_cost) are then DERIVED in Python from
the OCR-extracted raw figures using period-end balances as an approximation for
averages — LOW confidence, calculation_formula recorded, source="CALCULATED".

NIM is deliberately NOT derived here: banking.md flags it as one of the most
important banking metrics where a 5-10bps move matters, and a period-end-advances
approximation risks being materially wrong. It stays N/A until a source with
average interest-earning assets (e.g. an investor presentation) is ingested.

CASA, PCR, and slippage ratio are not disclosed in the standard SEBI results
format at all — also stay N/A until investor-presentation ingestion exists.

Two entry points:
  - ingest_bank_filing: latest quarter only — fast, used on every analysis run
    (gated 24h by the caller, see orchestrator.py).
  - backfill_bank_history: walks back ~5 years of quarterly filings — slow
    (one OCR+LLM pass per quarter), used once per company (gated long-TTL by
    the caller) so historical-trend sections of the report have real data.
"""
from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.ingestion import bse_client
from app.ingestion.pdf_ocr import ocr_pdf_pages
from app.infrastructure.database import metric_store
from app.infrastructure.database.models import Document
from app.infrastructure.storage.minio_client import put_document
from app.llm.client import llm_client as default_llm_client
from app.logger import logger

_EXTRACTION_SYSTEM_PROMPT = """You extract figures from OCR'd text of an Indian \
bank's SEBI-format quarterly financial results filing. The text may contain OCR \
noise (misread digits, stray punctuation). Extract ONLY the LATEST quarter column \
(the leftmost "Quarter ended" figures — usually the most recent date, standalone \
results, not "Year ended" and not consolidated if both are present). If a field is \
not present in the text, return null for it. Never invent or estimate a number \
that isn't in the text. Respond with a single JSON object matching this schema:
{
  "period_label": "DD.MM.YYYY or null",
  "unit": "crore",
  "interest_earned": number|null,
  "interest_expended": number|null,
  "other_income": number|null,
  "operating_expenses": number|null,
  "provisions_and_contingencies": number|null,
  "net_profit": number|null,
  "capital_adequacy_ratio_pct": number|null,
  "gross_npa_pct": number|null,
  "net_npa_pct": number|null,
  "return_on_assets_pct": number|null,
  "advances": number|null,
  "deposits": number|null
}"""

_REPORTED_FIELDS = {
    "capital_adequacy_ratio": ("capital_adequacy_ratio_pct", "%"),
    "gross_npa": ("gross_npa_pct", "%"),
    "net_npa": ("net_npa_pct", "%"),
    "roa": ("return_on_assets_pct", "%"),
}


def _parse_period(period_label: str | None, fallback: datetime) -> str:
    if period_label:
        for fmt in ("%d.%m.%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(period_label.strip(), fmt).date().isoformat()
            except ValueError:
                continue
    return fallback.date().isoformat()


def extract_metrics_from_ocr_text(ocr_text: str, llm_client=None) -> dict:
    client = llm_client or default_llm_client
    # This account's Groq tier has an 8000 tokens/minute ceiling and the API
    # reserves the full requested max_tokens against that budget upfront
    # (not just what's actually generated) — confirmed empirically: the
    # default config.llm_max_tokens=4096 pushed every single extraction call
    # over the limit (~4100 input + 4096 reserved output ≈ 8200 > 8000).
    # gpt-oss-20b spends real "reasoning" tokens even in JSON mode — a normal
    # filing measured ~600 reasoning + ~140 JSON tokens (742 completion total
    # on 3308 prompt tokens) — so anything much below ~1500 truncates the
    # reasoning pass and fails Groq's own JSON validation with an opaque,
    # empty-body 400. 3000 leaves comfortable headroom while keeping
    # input+output safely under the 8000 TPM ceiling. A handful of unusually
    # dense filings (e.g. annual results bundling standalone + consolidated
    # tables) can still fail extraction regardless of budget — that's fine,
    # _ingest_one_filing already skips a failed filing gracefully.
    return client.chat_json(_EXTRACTION_SYSTEM_PROMPT, ocr_text[:8000], max_tokens=3000)


def _to_float(val) -> float | None:
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _ingest_snapshot_car(db: Session, company_id: str, scrip_code: str, session, all_periods: bool) -> list:
    """Tier 1, structured, HIGH confidence: BSE's own tagged results snapshot.
    `all_periods=True` (backfill) stores all 3 periods the snapshot API returns
    for free in one call; `all_periods=False` (incremental) stores only the
    latest, matching the single-quarter fast path."""
    inserted = []
    try:
        snapshot = bse_client.fetch_results_snapshot(scrip_code, session=session)
        car_values = snapshot["fields"].get("CAR %") or []
        periods = snapshot.get("periods") or []
        pairs = list(zip(periods, car_values)) if all_periods else list(zip(periods[:1], car_values[:1]))
        for period_label, raw_value in pairs:
            if raw_value in ("", "--", None):
                continue
            row = metric_store.insert_metric_value(
                db,
                company_id=company_id,
                metric_key="capital_adequacy_ratio",
                period=period_label or datetime.now().date().isoformat(),
                value=float(str(raw_value).replace(",", "")),
                unit="%",
                source="BSE_RESULTS_API",
                source_tier=1,
                reported_or_calculated="REPORTED",
                confidence="HIGH",
                source_url=f"{bse_client.API_URL}/TabResults_PAR/w?scripcode={scrip_code}",
                source_document="BSE results snapshot (TabResults_PAR)",
            )
            if row is not None:
                inserted.append(row)
    except Exception as e:
        logger.warning("banking_ingestion: results snapshot failed", scrip_code=scrip_code, error=str(e))
    return inserted


def _store_filing_document(db: Session, company_id: str, filing: dict, pdf_bytes: bytes) -> None:
    """Durably store the raw filing PDF in MinIO — Architecture v2 Stage 7.
    Closes a real gap: this PDF previously only lived in bse_client.py's
    24h Redis cache and was unrecoverable after that, so an extracted
    GNPA/NNPA/CAR value could never be re-verified against its source past
    a day. Never raises — a storage failure shouldn't break ingestion, the
    value still gets extracted and stored either way."""
    attachment = filing.get("ATTACHMENTNAME", "unknown")
    storage_key = f"bse/{company_id}/{attachment}"
    try:
        if db.query(Document).filter_by(storage_key=storage_key).first():
            return  # already stored, same attachment name is stable per filing
        sha256 = put_document(storage_key, pdf_bytes, content_type="application/pdf")
        if sha256 is None:
            return
        db.add(Document(
            id=str(uuid.uuid4()), company_id=company_id, source="BSE_FILING_OCR",
            document_type="QUARTERLY_FILING",
            url=filing.get("NSURL") or bse_client.ATTACHMENT_URL.format(name=attachment),
            sha256=sha256, storage_key=storage_key, file_size=len(pdf_bytes),
            retrieved_at=datetime.now(timezone.utc),
        ))
        db.flush()
    except Exception as e:
        logger.warning("banking_ingestion: document storage failed", company_id=company_id, error=str(e))


def _ingest_one_filing(db: Session, company_id: str, filing: dict, session) -> list:
    """OCR one filing PDF, LLM-extract, derive, and store every value with
    provenance. Never raises — logs and returns an empty list on failure, since
    one bad filing (a malformed scan, an OCR/LLM hiccup) shouldn't abort a
    multi-quarter backfill."""
    inserted = []
    try:
        pdf_bytes = bse_client.download_filing_pdf(filing["ATTACHMENTNAME"], session=session)
        _store_filing_document(db, company_id, filing, pdf_bytes)
        # Page 1 (0-idx): the results table (CAR/GNPA/NNPA/ROA/P&L). Page 3 (0-idx):
        # the "Statement of Assets and Liabilities" note (Deposits, Advances).
        # Position varies a little by bank/quarter, so OCR a small window around
        # each and let the LLM pick out what's actually present.
        ocr_text = ocr_pdf_pages(pdf_bytes, page_indices=[1, 2, 3, 4])
        extracted = extract_metrics_from_ocr_text(ocr_text)
    except Exception as e:
        logger.warning("banking_ingestion: OCR/extraction failed",
                        attachment=filing.get("ATTACHMENTNAME"), error=str(e))
        return inserted

    news_dt = filing.get("NEWS_DT", "")
    fallback_date = datetime.now()
    try:
        fallback_date = datetime.fromisoformat(news_dt) if news_dt else fallback_date
    except ValueError:
        pass
    period = _parse_period(extracted.get("period_label"), fallback_date)
    source_url = filing.get("NSURL") or bse_client.ATTACHMENT_URL.format(name=filing["ATTACHMENTNAME"])
    source_document = filing.get("NEWSSUB", "BSE financial results filing")

    for metric_key, (field, unit) in _REPORTED_FIELDS.items():
        value = _to_float(extracted.get(field))
        if value is None:
            continue
        row = metric_store.insert_metric_value(
            db,
            company_id=company_id,
            metric_key=metric_key,
            period=period,
            value=value,
            unit=unit,
            source="BSE_FILING_OCR",
            source_tier=1,
            reported_or_calculated="REPORTED",
            confidence="MEDIUM",
            source_url=source_url,
            source_document=source_document,
            source_date=fallback_date,
            raw_reported_value=str(extracted.get(field)),
        )
        if row is not None:
            inserted.append(row)

    # DERIVED, LOW confidence: period-end-balance approximations.
    opex = _to_float(extracted.get("operating_expenses"))
    interest_earned = _to_float(extracted.get("interest_earned"))
    interest_expended = _to_float(extracted.get("interest_expended"))
    other_income = _to_float(extracted.get("other_income"))
    provisions = _to_float(extracted.get("provisions_and_contingencies"))
    advances = _to_float(extracted.get("advances"))

    if opex is not None and interest_earned is not None and interest_expended is not None and other_income is not None:
        nii = interest_earned - interest_expended
        denom = nii + other_income
        if denom:
            row = metric_store.insert_metric_value(
                db,
                company_id=company_id,
                metric_key="cost_to_income_ratio",
                period=period,
                value=round(opex / denom * 100, 2),
                unit="%",
                source="CALCULATED",
                source_tier=2,
                reported_or_calculated="CALCULATED",
                confidence="LOW",
                calculation_formula="operating_expenses / (interest_earned - interest_expended + other_income) * 100, "
                                     "from single-quarter OCR-extracted figures",
                source_url=source_url,
                source_document=source_document,
                source_date=fallback_date,
            )
            if row is not None:
                inserted.append(row)

    if provisions is not None and advances:
        row = metric_store.insert_metric_value(
            db,
            company_id=company_id,
            metric_key="credit_cost",
            period=period,
            value=round(provisions / advances * 100, 2),
            unit="%",
            source="CALCULATED",
            source_tier=2,
            reported_or_calculated="ESTIMATED",
            confidence="LOW",
            calculation_formula="provisions_and_contingencies / period-end advances * 100 (single quarter, "
                                 "not annualized; approximates average advances with period-end balance)",
            source_url=source_url,
            source_document=source_document,
            source_date=fallback_date,
        )
        if row is not None:
            inserted.append(row)

    return inserted


def ingest_bank_filing(db: Session, company_id: str, symbol: str) -> list:
    """Fetch the latest BSE results snapshot + filing PDF for a bank, extract
    what's extractable, store every value with provenance. Returns the list of
    MetricDataPoint rows inserted. Never raises for "nothing found" — logs and
    returns an empty list instead, since a missing filing is a legitimate,
    poll-again-later state, not a pipeline error.
    """
    session = bse_client._session()
    scrip_code = bse_client.resolve_scrip_code(symbol, session=session)
    if not scrip_code:
        logger.warning("banking_ingestion: could not resolve BSE scrip code", symbol=symbol)
        return []

    inserted = _ingest_snapshot_car(db, company_id, scrip_code, session, all_periods=False)

    filing = bse_client.find_latest_financial_results_filing(scrip_code, session=session)
    if not filing:
        logger.info("banking_ingestion: no financial-results filing found", symbol=symbol)
        return inserted

    inserted.extend(_ingest_one_filing(db, company_id, filing, session))
    return inserted


def backfill_bank_history(db: Session, company_id: str, symbol: str, years: int = 5) -> list:
    """Walk back `years` of quarterly BSE filings and ingest each one. Slow —
    one OCR+LLM pass per quarter (~15-20 quarters for 5 years) — intended to
    run once per company, not on every analysis (see the long-TTL gate in
    orchestrator.py).
    """
    session = bse_client._session()
    scrip_code = bse_client.resolve_scrip_code(symbol, session=session)
    if not scrip_code:
        logger.warning("banking_ingestion: could not resolve BSE scrip code", symbol=symbol)
        return []

    inserted = _ingest_snapshot_car(db, company_id, scrip_code, session, all_periods=True)

    filings = bse_client.find_financial_results_filings(scrip_code, session=session, years=years)
    logger.info("banking_ingestion: backfill starting", symbol=symbol, filings_found=len(filings))
    for filing in filings:
        inserted.extend(_ingest_one_filing(db, company_id, filing, session))
        db.flush()
        time.sleep(1.0)  # stay under the LLM provider's per-minute token/request budget

    logger.info("banking_ingestion: backfill complete", symbol=symbol,
                filings_processed=len(filings), values_inserted=len(inserted))
    return inserted


def backfill_all_banks(db: Session, max_companies_per_run: int = 3, years: int = 5) -> dict:
    """Batch driver for the 5-year OCR backfill — deliberately NOT called
    inline during a live analysis (removed from orchestrator.py 2026-09-10).
    ~15-20 sequential Groq calls per company reliably collided with the
    provider's per-minute rate limit, stalling a brand-new bank's very first
    analysis on the sector_analysis stage for many minutes (escalating 429
    retry-after backoff, observed up to 30s between attempts). The single
    latest-quarter call (`ingest_bank_filing`) stays inline — it's one Groq
    call, not twenty — so a first-time analysis still gets current CAR/ROA/
    gross_npa/net_npa/credit_cost promptly; the 5-year trend history now
    fills in via this batch job instead, same bounded/resumable pattern as
    `annual_report_ingestion.ingest_all_banks_annual_reports` (uses the same
    `banking_backfill:{company_id}` Redis gate orchestrator.py used to set
    inline, so a company already backfilled — by either path — is skipped).
    Meant to be invoked repeatedly (daily cron, or manually) until the whole
    banking universe is covered.
    """
    from app.ingestion.annual_report_ingestion import _bank_stocks
    from app.infrastructure.redis.client import cache_get, cache_set

    _BACKFILL_GATE_TTL = 60 * 60 * 24 * 30  # 30d — mirrors orchestrator.py's former inline gate

    processed, skipped, failed = [], [], []
    for stock in _bank_stocks(db):
        if len(processed) >= max_companies_per_run:
            break
        gate_key = f"banking_backfill:{stock.id}"
        if cache_get(gate_key):
            skipped.append(stock.id)
            continue
        try:
            rows = backfill_bank_history(db, company_id=stock.id, symbol=stock.symbol, years=years)
            db.commit()
            processed.append({"company_id": stock.id, "values_inserted": len(rows)})
        except Exception as e:
            db.rollback()
            logger.warning("backfill_all_banks: company failed", stock_id=stock.id, error=str(e))
            failed.append(stock.id)
        cache_set(gate_key, "1", _BACKFILL_GATE_TTL)

    logger.info("backfill_all_banks: run complete",
                processed=len(processed), skipped=len(skipped), failed=len(failed))
    return {"processed": processed, "skipped": skipped, "failed": failed}
