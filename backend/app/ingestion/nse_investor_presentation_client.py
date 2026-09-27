"""NSE quarterly Investor Presentation discovery + download — the fetch
half of the Quarterly Sector KPI Extraction Engine (2026-09-20).

Same NSE `/api/corporate-announcements` endpoint `nse_concall_client.py`
already uses for earnings-call transcripts, filtered to
`desc == "Investor Presentation"` instead of the concall category. Live-
probed on 4 real companies before writing any extraction logic:

- **Maruti Suzuki**: the attached PDF IS the real deck — 14 pages, clean
  text layer, a "Highlights of Q1 FY'27 w.r.t. Q1 FY'26"/"...w.r.t. Q4
  FY'26" table with sales volume + growth %, plus a domestic/export/
  segment breakdown. The best case.
- **Ambuja Cements**: also the real deck directly attached — 39 pages,
  34K+ chars, a "Consolidated Highlights" page giving Sales Volume (MnT),
  Cement Cost (Rs/t) AND EBITDA (Rs PMT) for 3 quarters side by side —
  even richer than the annual report case, no ratio derivation needed.
- **JSW Steel**: the NSE-attached PDF is NOT the deck — it's a one-page
  cover letter linking to the real presentation on the company's OWN
  website (an S3-hosted URL). `_resolve_real_pdf()` below follows that
  link when the attached PDF is too sparse to be the real thing; JSW's
  real deck (60 pages, 55K chars) has a genuine "Q1 FY27 Production &
  Sales" table once fetched this way.
- **UltraTech Cement**: a documented miss — the attached PDF is a 39-page
  pure-graphic/infographic deck with almost no extractable text (~30
  chars/page), and no fallback external link is present either. Same
  "return nothing rather than guess" conservatism as every other area in
  this engine — `find_investor_presentation_filings` still returns the
  filing, but the caller's own sparse-text check (in
  `quarterly_operating_metrics_ingestion.py`) skips extraction for it.
- **TNPL / JK Paper**: neither files under this category at all in a
  180-day lookback — smaller-cap companies often don't run an investor-
  relations deck program. A real, structural sector gap, not a fetch bug.
"""
from __future__ import annotations

import io
import re
import uuid
from datetime import datetime, timedelta, timezone

import pdfplumber
import requests
from sqlalchemy.orm import Session

from app.ingestion import nse_client
from app.infrastructure.database.models import Document
from app.infrastructure.storage.minio_client import put_document
from app.logger import logger

API_URL = "https://www.nseindia.com/api/corporate-announcements"
_INVESTOR_PRESENTATION_DESC = "Investor Presentation"
_MISFILED_DECK_TEXT_RE = re.compile(r"about (an? )?(investor|analyst)s?\s+(/\s*analyst\s+)?presentation\b", re.I)

# Below this, a PDF is almost certainly either a bare cover-letter (JSW
# Steel's pattern) or a pure-graphic deck (UltraTech's pattern) rather than
# a real extractable presentation — confirmed live: Maruti's genuine 14-page
# deck has 4,607 chars (thin but real), UltraTech's 39-page graphic deck has
# 1,210 chars, JSW's 1-page cover letter has 996 chars. 2,000 sits cleanly
# between "thinnest real deck seen" and "cover letter/graphics seen" without
# being tuned to exactly one example.
_MIN_REAL_TEXT_CHARS = 2000
# Tolerates a line break mid-URL — real bug found live on JSW Steel's cover
# letter: pdfplumber's text extraction preserves the PDF's own word-wrap,
# which splits the URL mid-word ("...uploads/2025/12/JSW-\nSteel_Investor-
# Presentation_Aug26_vf.pdf"), so a plain `\S+` search matched nothing.
_EXTERNAL_PDF_URL_RE = re.compile(r"https?://[^\s]+(?:\n[^\s]+)*?\.pdf", re.I)


def _find_external_pdf_url(text: str) -> str | None:
    m = _EXTERNAL_PDF_URL_RE.search(text)
    if not m:
        return None
    return m.group(0).replace("\n", "")


def find_investor_presentation_filings(symbol: str, session: requests.Session | None = None,
                                        lookback_days: int = 120) -> list[dict]:
    """Investor Presentation filings in the lookback window. Never raises —
    returns [] on any failure, matching `find_transcript_filings`'s
    contract. Does not itself validate the PDF's content — `ingest_*` below
    does that (sparse-text / cover-letter detection)."""
    s = session or nse_client._session()
    to_date = datetime.now()
    from_date = to_date - timedelta(days=lookback_days)
    params = {
        "index": "equities", "symbol": symbol,
        "from_date": from_date.strftime("%d-%m-%Y"), "to_date": to_date.strftime("%d-%m-%Y"),
    }
    try:
        r = s.get(API_URL, params=params, timeout=20)
        r.raise_for_status()
        rows = r.json() or []
    except Exception as e:
        logger.warning("nse_investor_presentation_client: filing search failed", symbol=symbol, error=str(e))
        return []

    return [
        row for row in rows
        if row.get("attchmntFile") and (
            row.get("desc") == _INVESTOR_PRESENTATION_DESC
            # Some issuers file the deck under a different category — found live
            # on Bank of Baroda ("General Updates": "...informed the Exchange
            # about Investor Presentation"), which the exact-desc match missed.
            or _MISFILED_DECK_TEXT_RE.search(row.get("attchmntText") or "")
        )
    ]


def _extract_full_text(pdf_bytes: bytes) -> str:
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        return "\n\n".join((p.extract_text() or "") for p in pdf.pages)


def _resolve_real_pdf(pdf_bytes: bytes, attached_url: str, symbol: str) -> tuple[bytes, str] | None:
    """(pdf_bytes, source_url) for the real deck if the attached PDF
    already has enough text; otherwise tries following an external `.pdf`
    link found in its (sparse) text — JSW Steel's real-world pattern,
    where the NSE-attached file is just a cover letter pointing at the
    company's own website. Returns None if neither the attached PDF nor a
    linked one turns out to have enough text (UltraTech's pattern:
    pure-graphic deck, no useful link either)."""
    text = _extract_full_text(pdf_bytes)
    if len(text) >= _MIN_REAL_TEXT_CHARS:
        return pdf_bytes, attached_url

    external_url = _find_external_pdf_url(text)
    if external_url is None:
        logger.info("nse_investor_presentation_client: attached PDF too sparse, no external link found",
                    symbol=symbol, chars=len(text))
        return None

    try:
        r = requests.get(external_url, timeout=30)
        r.raise_for_status()
        external_bytes = r.content
        if not external_bytes.startswith(b"%PDF"):
            return None
    except Exception as e:
        logger.warning("nse_investor_presentation_client: external link fetch failed",
                        symbol=symbol, url=external_url, error=str(e))
        return None

    external_text = _extract_full_text(external_bytes)
    if len(external_text) >= _MIN_REAL_TEXT_CHARS:
        logger.info("nse_investor_presentation_client: resolved real deck via external link",
                    symbol=symbol, url=external_url, chars=len(external_text))
        return external_bytes, external_url

    logger.info("nse_investor_presentation_client: external link also too sparse — giving up",
                symbol=symbol, url=external_url, chars=len(external_text))
    return None


def fetch_investor_presentation(filing: dict, symbol: str,
                                 session: requests.Session | None = None) -> tuple[bytes, str] | None:
    """Downloads the NSE-attached PDF and resolves it to the real deck
    (following an external link if needed, see `_resolve_real_pdf`).
    Returns (pdf_bytes, source_url) — `source_url` may be the external URL,
    not the NSE one, when the fallback path was used (kept for provenance).
    Never raises — returns None on any failure."""
    url = filing.get("attchmntFile")
    if not url:
        return None

    s = session or nse_client._session()
    try:
        r = s.get(url, timeout=30, headers={"Referer": nse_client.BOOTSTRAP_URL})
        r.raise_for_status()
        pdf_bytes = r.content
        if not pdf_bytes.startswith(b"%PDF"):
            return None
    except Exception as e:
        logger.warning("nse_investor_presentation_client: download failed", symbol=symbol, url=url, error=str(e))
        return None

    return _resolve_real_pdf(pdf_bytes, url, symbol)


def store_investor_presentation(db: Session, company_id: str, symbol: str, filing: dict,
                                 pdf_bytes: bytes, source_url: str) -> Document | None:
    """Durably store the resolved PDF (same idempotent storage-key-based
    dedup as `annual_report_ingestion.py::_store_annual_report_document`).
    Never raises — returns None (and logs) if storage fails."""
    an_dt = filing.get("an_dt", "")
    date_part = an_dt.split(" ")[0] if an_dt else "unknown"
    storage_key = f"nse_investor_presentation/{company_id}/{date_part}_{source_url.rsplit('/', 1)[-1]}"

    existing = db.query(Document).filter_by(storage_key=storage_key).first()
    if existing:
        return existing

    sha256 = put_document(storage_key, pdf_bytes, content_type="application/pdf")
    if sha256 is None:
        logger.warning("nse_investor_presentation_client: MinIO storage failed", symbol=symbol)
        return None

    document = Document(
        id=str(uuid.uuid4()), company_id=company_id, source="NSE",
        document_type="INVESTOR_PRESENTATION", url=source_url, sha256=sha256,
        storage_key=storage_key, file_size=len(pdf_bytes), retrieved_at=datetime.now(timezone.utc),
    )
    db.add(document)
    db.flush()
    return document


def fetch_latest_investor_presentation(symbol: str, session: requests.Session | None = None,
                                        lookback_days: int = 120) -> tuple[bytes, str, dict] | None:
    """Convenience wrapper: finds and resolves the MOST RECENT Investor
    Presentation for `symbol`. Returns (pdf_bytes, source_url, filing) or
    None if there's no filing in the lookback window, or the one found
    doesn't resolve to real, extractable text. Never raises."""
    s = session or nse_client._session()
    filings = find_investor_presentation_filings(symbol, session=s, lookback_days=lookback_days)
    if not filings:
        return None

    def _an_dt_key(f):
        try:
            return datetime.strptime(f.get("an_dt", "").split(" ")[0], "%d-%b-%Y")
        except ValueError:
            return datetime.min

    filings = sorted(filings, key=_an_dt_key, reverse=True)
    latest = filings[0]
    resolved = fetch_investor_presentation(latest, symbol, session=s)
    if resolved is None:
        return None
    pdf_bytes, source_url = resolved
    return pdf_bytes, source_url, latest
