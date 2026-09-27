"""Client for BSE's public (unofficial, reverse-engineered) JSON API.

Verified reachable from this deployment; nseindia.com is not (Akamai blocks
datacenter IPs outright with a 403 on every request, headers notwithstanding).
BSE's api.bseindia.com host has no such block and requires no cookie/session
bootstrap beyond a browser-like User-Agent.

Two distinct data shapes come out of BSE for a listed bank:
  1. `fetch_results_snapshot` — BSE's own structured "results snapshot" API
     (TabResults_PAR/w). A handful of tagged fields (Revenue, Net Profit, EPS,
     NPM%, and for banks CAR%) — genuinely structured, no OCR involved.
  2. `find_latest_financial_results_filing` + `download_filing_pdf` — locates
     and downloads the bank's actual SEBI-format quarterly results PDF via
     BSE's announcements feed. This is the authoritative regulatory filing,
     but its data pages are scanned images (no text layer) — see
     app/ingestion/pdf_ocr.py for the OCR step needed to read it.
"""
from __future__ import annotations

import base64
import json
import re
import time
from datetime import datetime, timedelta

import requests

from app.infrastructure.redis.client import cache_get, cache_set
from app.logger import logger

API_URL = "https://api.bseindia.com/BseIndiaAPI/api"
BASE_URL = "https://www.bseindia.com/"
ATTACHMENT_URL = "https://www.bseindia.com/xml-data/corpfiling/AttachLive/{name}"
# BSE moves a filing's attachment from "Live" to "His"(torical) once it's no
# longer the most recent filing for that scrip — confirmed empirically: only
# the single latest filing resolves under AttachLive, every older one 404s
# there and is found under AttachHis instead.
ATTACHMENT_HISTORICAL_URL = "https://www.bseindia.com/xml-data/corpfiling/AttachHis/{name}"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.3"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
    "Origin": BASE_URL,
    "Referer": BASE_URL,
}

_PDF_CACHE_TTL = 60 * 60 * 24  # 24h
_SNAPSHOT_CACHE_TTL = 60 * 60 * 6  # 6h


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update(_HEADERS)
    return s


def resolve_scrip_code(symbol: str, session: requests.Session | None = None) -> str | None:
    """NSE/BSE trading symbol (e.g. "HDFCBANK") -> BSE scrip code (e.g. "500180")."""
    s = session or _session()
    r = s.get(f"{API_URL}/PeerSmartSearch/w", params={"Type": "SS", "text": symbol}, timeout=15)
    r.raise_for_status()
    text = r.text
    for entry in re.findall(r"<li[^>]*>.*?</li>", text):
        if re.search(rf"<strong>{re.escape(symbol.upper())}</strong>", entry, re.I):
            m = re.search(r"liclick\('(\d{6})'", entry)
            if m:
                return m.group(1)
    return None


def fetch_results_snapshot(scrip_code: str, session: requests.Session | None = None) -> dict:
    """BSE's structured results-snapshot API. Returns
    {"periods": [...], "fields": {field_title: [v1, v2, v3]}}.
    For banks this reliably includes "CAR %" alongside generic P&L fields.
    """
    cache_key = f"bse:snapshot:{scrip_code}"
    cached = cache_get(cache_key)
    if cached:
        return json.loads(cached)

    s = session or _session()
    r = s.get(
        f"{API_URL}/TabResults_PAR/w",
        params={"scripcode": scrip_code, "tabtype": "RESULTS"},
        timeout=15,
    )
    r.raise_for_status()
    data = r.json()
    if isinstance(data, str):
        data = json.loads(data)

    periods = [data.get(f"col{i}", "") for i in range(2, 5) if data.get(f"col{i}")]
    fields: dict[str, list[str]] = {}
    for item in data.get("resultinCr", []):
        title = item.get("title", "")
        if title:
            fields[title] = [item.get("v1", ""), item.get("v2", ""), item.get("v3", "")]

    result = {"periods": periods, "fields": fields}
    cache_set(cache_key, json.dumps(result), _SNAPSHOT_CACHE_TTL)
    return result


def find_latest_financial_results_filing(
    scrip_code: str, session: requests.Session | None = None, lookback_days: int = 150
) -> dict | None:
    """Find the most recent "Financial Results" announcement for a scrip via
    BSE's announcements feed. Returns the raw announcement row (NEWSSUB,
    NEWS_DT, ATTACHMENTNAME, ...) or None if nothing was filed in the window.
    """
    s = session or _session()
    to_date = datetime.now()
    from_date = to_date - timedelta(days=lookback_days)
    params = {
        "pageno": 1,
        "strCat": "Result",
        "subcategory": "-1",
        "strPrevDate": from_date.strftime("%Y%m%d"),
        "strToDate": to_date.strftime("%Y%m%d"),
        "strSearch": "P",
        "strscrip": scrip_code,
        "strType": "C",
    }
    r = s.get(f"{API_URL}/AnnSubCategoryGetData/w", params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    rows = [row for row in data.get("Table", []) if row.get("PDFFLAG") == 1 and row.get("ATTACHMENTNAME")]
    if not rows:
        return None
    rows.sort(key=lambda row: row.get("NEWS_DT", ""), reverse=True)
    return rows[0]


def _is_genuine_results_filing(row: dict) -> bool:
    """The "Result" category also carries same-day board-outcome and related-
    party-transaction disclosures with no numbers table attached. Verified
    against 5 years of real HDFC Bank filings: every genuine quarterly results
    filing's headline contains "financial results"; board-outcome/RPT noise
    never does, even though it shares PDFFLAG=1 and CATEGORYNAME="Result"."""
    if row.get("PDFFLAG") != 1 or not row.get("ATTACHMENTNAME"):
        return False
    return "financial results" in (row.get("NEWSSUB") or "").lower()


def find_financial_results_filings(
    scrip_code: str,
    session: requests.Session | None = None,
    years: int = 5,
    window_days: int = 360,
    request_delay: float = 0.4,
) -> list[dict]:
    """Walk backward in <=365-day windows collecting every genuine quarterly
    results filing over `years` years. A single wide-range query silently
    returns zero rows from this endpoint — confirmed empirically: BSE's
    AnnSubCategoryGetData/w returns data for spans up to ~360 days and nothing
    for spans of a year or more, even though older filings clearly exist and
    are reachable through a sequence of narrower windows.
    """
    s = session or _session()
    filings: list[dict] = []
    seen_ids = set()
    cur_to = datetime.now()
    window = timedelta(days=window_days)
    num_windows = max(1, (years * 365) // window_days + 1)

    for _ in range(num_windows):
        cur_from = cur_to - window
        params = {
            "pageno": 1,
            "strCat": "Result",
            "subcategory": "-1",
            "strPrevDate": cur_from.strftime("%Y%m%d"),
            "strToDate": cur_to.strftime("%Y%m%d"),
            "strSearch": "P",
            "strscrip": scrip_code,
            "strType": "C",
        }
        try:
            r = s.get(f"{API_URL}/AnnSubCategoryGetData/w", params=params, timeout=20)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            logger.warning("find_financial_results_filings: window failed",
                           scrip_code=scrip_code, window_from=cur_from.date().isoformat(), error=str(e))
            cur_to = cur_from
            time.sleep(request_delay)
            continue

        for row in data.get("Table", []):
            if not _is_genuine_results_filing(row):
                continue
            row_id = row.get("NEWSID") or row.get("ATTACHMENTNAME")
            if row_id in seen_ids:
                continue
            seen_ids.add(row_id)
            filings.append(row)

        cur_to = cur_from
        time.sleep(request_delay)

    filings.sort(key=lambda row: row.get("NEWS_DT", ""), reverse=True)
    return filings


def download_filing_pdf(attachment_name: str, session: requests.Session | None = None) -> bytes:
    """Download a filing PDF by its BSE attachment filename, cached 24h.
    Tries the "live" path first (the current/most-recent filing), then falls
    back to the "historical" path (every older filing)."""
    cache_key = f"bse:pdf:{attachment_name}"
    cached = cache_get(cache_key)
    if cached:
        return base64.b64decode(cached)

    s = session or _session()
    content = None
    last_error = None
    for url in (ATTACHMENT_URL.format(name=attachment_name), ATTACHMENT_HISTORICAL_URL.format(name=attachment_name)):
        try:
            r = s.get(url, timeout=30)
            r.raise_for_status()
            # A 404 for a stale AttachLive link is not the only failure mode —
            # confirmed empirically: some stale links 200 with an HTML error
            # page (Content-Type: text/html) instead. Only real PDF bytes count.
            if not r.content.startswith(b"%PDF"):
                raise ValueError(f"Response from {url} is not a PDF (got {r.headers.get('Content-Type')})")
            content = r.content
            break
        except Exception as e:
            last_error = e
            continue
    if content is None:
        raise last_error

    try:
        cache_set(cache_key, base64.b64encode(content).decode("ascii"), _PDF_CACHE_TTL)
    except Exception as e:
        logger.warning("Failed to cache filing PDF", error=str(e))
    return content


# ── Annual report (secondary source, NSE primary) ───────────────────────────
# Found 2026-09-16 investigating why Pine Labs (a recently-listed company)
# had zero NSE annual-report coverage: NSE's `/api/annual-reports` genuinely
# has nothing on file for it, but BSE's listing requirements evidently moved
# faster for this IPO — its FY2025-26 annual report IS on BSE, confirmed
# live (scrip 544606, a real 7MB PDF, same text-layer format as NSE's — no
# OCR needed here either). `annual_report_ingestion.py` tries NSE first
# (unchanged) and only falls back to this when NSE has nothing, so a company
# with real NSE coverage is completely unaffected.
_ANNUAL_REPORT_CACHE_DIR = None  # set lazily below to avoid a module-load-time import cycle


def _annual_report_cache_dir():
    global _ANNUAL_REPORT_CACHE_DIR
    if _ANNUAL_REPORT_CACHE_DIR is None:
        from pathlib import Path
        from app.config import config
        _ANNUAL_REPORT_CACHE_DIR = Path(config.reports_dir).parent / "cache" / "annual_reports"
    return _ANNUAL_REPORT_CACHE_DIR


def find_latest_annual_report(scrip_code: str, session: requests.Session | None = None) -> dict | None:
    """BSE's own Annual Report API (undocumented, found by probing the same
    `api.bseindia.com/BseIndiaAPI/api/` host the rest of this module already
    uses) — `AnnualReport_New/w?scripcode=...` returns every fiscal year BSE
    has a report on file for, each row carrying a direct PDF URL
    (`PDFDownload`) with no further filing lookup needed. Returns the most
    recent year's row, or None if BSE has nothing either."""
    s = session or _session()
    r = s.get(f"{API_URL}/AnnualReport_New/w", params={"scripcode": scrip_code}, timeout=20)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, str):
        data = json.loads(data)
    rows = [row for row in (data.get("Table") or []) if row.get("PDFDownload")]
    if not rows:
        return None
    rows.sort(key=lambda row: row.get("Year", ""), reverse=True)
    return rows[0]


def download_annual_report(filing: dict, symbol: str, session: requests.Session | None = None) -> bytes:
    """Download a BSE annual-report PDF located via `find_latest_annual_report()`.
    Cached to local disk, not Redis — mirrors `nse_client.py::download_annual_report()`'s
    own reasoning (these run several MB+, too large for base64-in-Redis)."""
    file_url = filing["PDFDownload"]
    year = filing.get("Year", "unknown")
    cache_path = _annual_report_cache_dir() / f"{symbol}_BSE_{year}.pdf"
    if cache_path.exists():
        return cache_path.read_bytes()

    s = session or _session()
    r = s.get(file_url, timeout=90, headers={"Referer": BASE_URL})
    r.raise_for_status()
    if not r.content.startswith(b"%PDF"):
        raise ValueError(f"Response from {file_url} is not a PDF (got {r.headers.get('Content-Type')})")

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(r.content)
    logger.info("BSE annual report downloaded", symbol=symbol, size=len(r.content), path=str(cache_path))
    return r.content
