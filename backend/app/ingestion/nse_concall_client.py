"""NSE earnings-call transcript discovery + raw storage — Concall
Intelligence System, Stage C0. Deliberately narrow: find the filing,
download it, store it durably, parse only the cover-page metadata
(quarter/call date/management participants). No speaker/utterance parsing
here — that's Stage C1 — and no guidance extraction — that's Stage C3.

Live-probed 2026-09-13 (HDFCBANK): NSE's `/api/corporate-announcements`
returns real filings tagged `desc: "Analysts/Institutional Investor Meet/
Con. Call Updates"`, and among them, a genuine transcript row distinct from
the "Schedule of meet" and "Link of Recording" filings under the same
category — identified by `attchmntText` containing "Transcript". The PDF
itself has a real text layer (no OCR) and a consistent structure: a
`MANAGEMENT:` block naming each participant and title, then a
"Q_ FY__ Earnings Conference Call" / call-date header line.

Reuses nse_client.py's cookie-bootstrap session (same site, same
requirement) and the documents/MinIO storage pattern already proven by
earnings_call_client.py (there, BSE-sourced; here, NSE — same idempotent
storage-key-based dedup)."""
from __future__ import annotations

import re
import uuid
from datetime import date, datetime, timedelta, timezone

import pdfplumber
import io
import requests
from sqlalchemy.orm import Session

from app.ingestion import nse_client
from app.infrastructure.database.models import ConcallTranscript, Document
from app.infrastructure.storage.minio_client import put_document
from app.logger import logger

API_URL = "https://www.nseindia.com/api/corporate-announcements"
_CONCALL_DESC = "Analysts/Institutional Investor Meet/Con. Call Updates"

_HEADER_RE = re.compile(
    r"(Q\d\s*FY\d{2,4})[^\n]*Earnings\s+(?:Conference\s+)?Call[^\n]*\n+\s*"
    r"([A-Za-z]+\s+\d{1,2},?\s*\d{4})",
    re.I,
)
# Real template variance found live-testing TCS's transcript (2026-09-13):
# no "Q_ FY__ Earnings Conference Call, <date>" header at all — instead
# "Held on <date>...For discussing Financial Results for Q_ FY____ ended
# on...". Different transcription vendor, different phrasing. Tried as a
# fallback, not a replacement — HDFC's format is checked first since it's
# the more common one seen so far.
_HEADER_RE_ALT = re.compile(
    r"Held on\s+([A-Za-z]+\s+\d{1,2},?\s*\d{4}).*?"
    r"Q(\d)\s*FY\s*(\d{4})",
    re.I | re.S,
)
_MGMT_BLOCK_RE = re.compile(r"MANAGEMENT\s*:(.*?)(?=\nModerator\s*:)", re.S | re.I)
_PARTICIPANT_RE = re.compile(
    r"(MR\.|MS\.|MRS\.|DR\.)\s*([A-Z][A-Z.\s]*?)\s*[–\-]\s*(.+?)(?=(?:MR\.|MS\.|MRS\.|DR\.)|$)",
    re.S,
)
# Real bug found live-testing HDFC Bank's transcript, 2026-09-13: a running
# page header ("HDFC Bank Limited" + the call date, right-aligned) sits
# between the last MANAGEMENT entry and "Moderator:", and got absorbed into
# the last participant's title verbatim ("...CHIEF FINANCIAL OFFICER –
# HDFC BANK LIMITED HDFC Bank Limited July 18, 2026"). Strips a trailing
# "<company name> <Month> <Day>, <Year>" tail before parsing participants.
_TRAILING_HEADER_RE = re.compile(
    r"\s+[A-Z][A-Za-z.,&\s]+?\s+(?:January|February|March|April|May|June|July|"
    r"August|September|October|November|December)\s+\d{1,2},?\s*\d{4}\s*$"
)


def _parse_header(full_text: str) -> tuple[str | None, str | None]:
    """(quarter, call_date_iso) from the transcript's own title page. Tries
    the more common vendor template first, then a confirmed alternate
    (see _HEADER_RE_ALT). Never raises — returns (None, None) if neither
    matches; more templates can be added here as they're found, without
    touching call sites."""
    m = _HEADER_RE.search(full_text)
    if m:
        quarter = re.sub(r"\s+", " ", m.group(1)).strip()
        date_str = re.sub(r"\s+", " ", m.group(2)).strip()
        try:
            return quarter, datetime.strptime(date_str, "%B %d, %Y").date().isoformat()
        except ValueError:
            return quarter, None

    m = _HEADER_RE_ALT.search(full_text)
    if m:
        date_str = re.sub(r"\s+", " ", m.group(1)).strip()
        quarter = f"Q{m.group(2)} FY{m.group(3)}"
        try:
            return quarter, datetime.strptime(date_str, "%B %d, %Y").date().isoformat()
        except ValueError:
            return quarter, None

    return None, None


def _parse_management_block(full_text: str) -> list[dict]:
    m = _MGMT_BLOCK_RE.search(full_text)
    if not m:
        return []
    block = _TRAILING_HEADER_RE.sub("", m.group(1)).strip()
    block = re.sub(r"\s+", " ", block).strip()
    participants = []
    for pm in _PARTICIPANT_RE.finditer(block):
        prefix, name, title = pm.groups()
        clean_name = re.sub(r"\s+", " ", f"{prefix} {name}").strip()
        clean_title = re.sub(r"\s+", " ", title).strip(" –-")
        if clean_name and clean_title:
            participants.append({"name": clean_name, "title": clean_title})
    return participants


def find_transcript_filings(symbol: str, session: requests.Session | None = None,
                             lookback_days: int = 120) -> list[dict]:
    """Genuine transcript filings only — excludes the "Schedule of meet"
    and "Link of Recording" filings NSE files under the same category.
    Never raises — returns [] on any failure."""
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
        logger.warning("nse_concall_client: filing search failed", symbol=symbol, error=str(e))
        return []

    return [
        row for row in rows
        if row.get("desc") == _CONCALL_DESC
        and "transcript" in (row.get("attchmntText") or "").lower()
        and row.get("attchmntFile")
    ]


def ingest_transcript(db: Session, company_id: str, symbol: str, filing: dict,
                       session: requests.Session | None = None) -> ConcallTranscript | None:
    """Download, durably store, and record metadata for one transcript
    filing. Idempotent on the PDF's storage key — re-running for a filing
    already ingested returns the existing row rather than duplicating it.
    Never raises — logs and returns None on failure."""
    url = filing.get("attchmntFile")
    if not url:
        return None

    storage_key = f"nse_concall/{company_id}/{url.rsplit('/', 1)[-1]}"
    existing_doc = db.query(Document).filter_by(storage_key=storage_key).first()
    if existing_doc:
        existing_transcript = db.query(ConcallTranscript).filter_by(document_id=existing_doc.id).first()
        if existing_transcript:
            return existing_transcript

    s = session or nse_client._session()
    try:
        r = s.get(url, timeout=30, headers={"Referer": nse_client.BOOTSTRAP_URL})
        r.raise_for_status()
        pdf_bytes = r.content
    except Exception as e:
        logger.warning("nse_concall_client: transcript download failed", symbol=symbol, url=url, error=str(e))
        return None

    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            full_text = "\n".join((p.extract_text() or "") for p in pdf.pages)
    except Exception as e:
        logger.warning("nse_concall_client: PDF text extraction failed", symbol=symbol, error=str(e))
        return None

    quarter, call_date = _parse_header(full_text)
    management_participants = _parse_management_block(full_text)

    now = datetime.now(timezone.utc)
    if existing_doc:
        document = existing_doc
    else:
        sha256 = put_document(storage_key, pdf_bytes, content_type="application/pdf")
        if sha256 is None:
            logger.warning("nse_concall_client: MinIO storage failed", symbol=symbol)
            return None
        document = Document(
            id=str(uuid.uuid4()), company_id=company_id, source="NSE",
            document_type="CONCALL_TRANSCRIPT", url=url, sha256=sha256,
            storage_key=storage_key, file_size=len(pdf_bytes), retrieved_at=now,
        )
        db.add(document)
        db.flush()

    filing_date = None
    an_dt = filing.get("an_dt")
    if an_dt:
        try:
            filing_date = datetime.strptime(an_dt.split(" ")[0], "%d-%b-%Y").date().isoformat()
        except ValueError:
            filing_date = None

    transcript = ConcallTranscript(
        id=str(uuid.uuid4()), company_id=company_id, document_id=document.id,
        quarter=quarter, call_date=call_date, filing_date=filing_date,
        management_participants=management_participants or None,
        source="NSE", source_url=url, extraction_status="PENDING", retrieved_at=now,
    )
    db.add(transcript)
    db.flush()

    logger.info("nse_concall_client: transcript ingested", symbol=symbol, quarter=quarter,
                call_date=call_date, participants=len(management_participants))
    return transcript


def ingest_recent_transcripts(db: Session, company_id: str, symbol: str,
                               lookback_days: int = 120) -> list[ConcallTranscript]:
    """Find and ingest every genuine transcript filed in the lookback
    window. Never raises — logs and returns whatever succeeded on partial
    failure."""
    session = nse_client._session()
    filings = find_transcript_filings(symbol, session=session, lookback_days=lookback_days)
    results = []
    for filing in filings:
        transcript = ingest_transcript(db, company_id, symbol, filing, session=session)
        if transcript is not None:
            results.append(transcript)
    return results
