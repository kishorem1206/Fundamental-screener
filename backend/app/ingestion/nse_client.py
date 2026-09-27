"""Client for NSE's annual-reports API.

nseindia.com was Akamai-blocked (403 on everything) earlier in this project's
life — that turned out to be transient/IP-reputation-based, not a permanent
wall: re-tested 2026-09-06 and found fully reachable, including
`/api/annual-reports`, after a one-time cookie bootstrap. Given that history,
every call here degrades gracefully (raises a catchable error, callers log +
skip) rather than assuming permanent access — if NSE blocks this environment
again, annual-report ingestion should fail closed, not break the pipeline.

Unlike BSE's SEBI-format quarterly results (scanned images, see pdf_ocr.py),
NSE's annual report PDFs carry a genuine text layer — confirmed on HDFC
Bank's real FY2025-26 report (678 pages). No OCR needed here.
"""
from __future__ import annotations

from pathlib import Path

import requests

from app.config import config
from app.logger import logger

API_URL = "https://www.nseindia.com/api"
BOOTSTRAP_URL = "https://www.nseindia.com/companies-listing/corporate-filings-annual-reports"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.3"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
}

_CACHE_DIR = Path(config.reports_dir).parent / "cache" / "annual_reports"


def _session() -> requests.Session:
    """A fresh session with the required cookies bootstrapped. NSE's API
    rejects requests without cookies acquired from an actual page visit."""
    s = requests.Session()
    s.headers.update(_HEADERS)
    r = s.get(BOOTSTRAP_URL, timeout=15)
    r.raise_for_status()
    return s


def find_latest_annual_report(symbol: str, session: requests.Session | None = None) -> dict | None:
    """Latest annual report filing for a symbol, or None if NSE has nothing
    on file. Prefers a "New" submission over a "Revised" one filed for the
    same year unless only a Revised exists."""
    s = session or _session()
    r = s.get(f"{API_URL}/annual-reports", params={"index": "equities", "symbol": symbol}, timeout=20)
    r.raise_for_status()
    data = r.json()
    rows = data.get("data") or []
    if not rows:
        return None

    def sort_key(row):
        return (row.get("toYr", ""), row.get("broadcast_dttm", ""))

    rows = sorted(rows, key=sort_key, reverse=True)
    latest_year_rows = [r for r in rows if r.get("toYr") == rows[0].get("toYr")]
    new_rows = [r for r in latest_year_rows if r.get("submission_type") == "New"]
    return new_rows[0] if new_rows else latest_year_rows[0]


def download_annual_report(filing: dict, symbol: str, session: requests.Session | None = None) -> bytes:
    """Download the annual report PDF, cached to local disk (these run
    10-15MB+ — base64-in-Redis, the pattern bse_client.py uses for ~1MB
    quarterly PDFs, doesn't make sense at this size)."""
    file_url = filing["fileName"]
    from_yr, to_yr = filing.get("fromYr", "?"), filing.get("toYr", "?")
    cache_path = _CACHE_DIR / f"{symbol}_{from_yr}_{to_yr}.pdf"
    if cache_path.exists():
        return cache_path.read_bytes()

    s = session or _session()
    r = s.get(file_url, timeout=90, headers={"Referer": BOOTSTRAP_URL})
    r.raise_for_status()
    if not r.content.startswith(b"%PDF"):
        raise ValueError(f"Response from {file_url} is not a PDF (got {r.headers.get('Content-Type')})")

    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(r.content)
    logger.info("Annual report downloaded", symbol=symbol, size=len(r.content), path=str(cache_path))
    return r.content
