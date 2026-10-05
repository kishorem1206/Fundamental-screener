"""NSE corporate-filing feeds used by the Business Intelligence Engine. Each
feed takes a symbol (or company name) and was verified live against 45
companies across 22 sectors on 2026-10-04. One paced session per build:
NSE throttles bursts, and every request here is sequential.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import date, datetime, timezone
from urllib.parse import quote

from app.ingestion import nse_client
from app.logger import logger

API = "https://www.nseindia.com/api"
_REFERER = {"Referer": "https://www.nseindia.com/get-quotes/equity"}
_PACE_SECONDS = 0.8


def _parse_date(text: str | None) -> date | None:
    for fmt in ("%d-%b-%Y", "%d-%B-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime((text or "").strip()[:11].title(), fmt).date()
        except ValueError:
            continue
    return None


def _parse_datetime(text: str | None) -> datetime | None:
    for fmt in ("%d-%b-%Y %H:%M:%S", "%d-%b-%Y %H:%M", "%d-%b-%Y"):
        try:
            return datetime.strptime((text or "").strip().title(), fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


@dataclass
class ResultsFiling:
    period_end: date
    basis: str  # STANDALONE | CONSOLIDATED
    audited: bool
    xbrl_url: str
    readable_url: str | None  # NSE's iXBRL rendering, where it exists
    pdf_url: str | None
    published_at: datetime | None
    feed: str  # integrated | legacy


class NseFilings:
    def __init__(self, session=None, pace: float = _PACE_SECONDS):
        self._session = session or nse_client._session()
        self._pace = pace
        self.requests = 0

    def fetch(self, url: str, timeout: int = 120) -> bytes:
        """GET with pacing; one session rebuild and retry on a non-200."""
        for attempt in (1, 2):
            time.sleep(self._pace)
            self.requests += 1
            response = self._session.get(url, timeout=timeout, headers=_REFERER)
            if response.status_code == 200:
                return response.content
            if attempt == 1:
                logger.warning("bie: NSE request failed, rebuilding session", url=url, status=response.status_code)
                time.sleep(4)
                self._session = nse_client._session()
        response.raise_for_status()
        raise RuntimeError(f"NSE returned HTTP {response.status_code} for {url}")

    def _json(self, path: str):
        import json
        return json.loads(self.fetch(f"{API}/{path}", timeout=45))

    def link_status(self, url: str) -> int | None:
        """HTTP status of a cited URL (body not downloaded)."""
        time.sleep(self._pace)
        try:
            response = self._session.get(url, timeout=30, headers=_REFERER, stream=True)
            response.close()
            return response.status_code
        except Exception:  # noqa: BLE001 — unreachable is a result, not an error
            return None

    # ── feeds ────────────────────────────────────────────────────────────

    def symbol_meta_url(self, symbol: str) -> str:
        return f"{API}/NextApi/apiClient/GetQuoteApi?functionName=getMetaData&symbol={quote(symbol)}"

    def symbol_data_url(self, symbol: str, series: str) -> str:
        return (f"{API}/NextApi/apiClient/GetQuoteApi?functionName=getSymbolData&marketType=N"
                f"&series={quote(series)}&symbol={quote(symbol)}")

    def results(self, symbol: str) -> list[ResultsFiling]:
        """Every results filing with a data file, newest first: integrated
        filings (2025 on) then the legacy feed (earlier periods)."""
        out: list[ResultsFiling] = []
        integrated = self._json(
            f"integrated-filing-results?index=equities&symbol={quote(symbol)}&type=Integrated%20Filing-%20Financials"
        ).get("data") or []
        for row in integrated:
            period_end = _parse_date(row.get("qe_Date"))
            if not period_end or not row.get("xbrl"):
                continue
            out.append(ResultsFiling(
                period_end=period_end,
                basis="CONSOLIDATED" if row.get("consolidated") == "Consolidated" else "STANDALONE",
                audited=(row.get("audited") or "").lower().startswith("audited"),
                xbrl_url=row["xbrl"], readable_url=row.get("ixbrl") or None, pdf_url=row.get("pdf_attach") or None,
                published_at=_parse_datetime(row.get("broadcast_Date") or row.get("creation_Date")), feed="integrated",
            ))
        seen = {(f.period_end, f.basis) for f in out}
        legacy = self._json(f"corporates-financial-results?index=equities&symbol={quote(symbol)}&period=Quarterly")
        for row in legacy if isinstance(legacy, list) else []:
            period_end = _parse_date(row.get("toDate"))
            xbrl_url = row.get("xbrl") or ""
            basis = "CONSOLIDATED" if row.get("consolidated") == "Consolidated" else "STANDALONE"
            if not period_end or not xbrl_url or xbrl_url.endswith("/-") or (period_end, basis) in seen:
                continue
            seen.add((period_end, basis))
            out.append(ResultsFiling(
                period_end=period_end, basis=basis,
                audited=(row.get("audited") or "").lower().startswith("audited"),
                xbrl_url=xbrl_url, readable_url=None, pdf_url=None,
                published_at=_parse_datetime(row.get("broadCastDate") or row.get("filingDate")), feed="legacy",
            ))
        out.sort(key=lambda f: (f.period_end, f.basis), reverse=True)
        return out

    def annual_reports(self, symbol: str) -> list[dict]:
        rows = self._json(f"annual-reports?index=equities&symbol={quote(symbol)}").get("data") or []
        rows.sort(key=lambda r: (r.get("toYr") or "", r.get("broadcast_dttm") or ""), reverse=True)
        return rows

    def brsr(self, symbol: str) -> list[dict]:
        rows = self._json(f"corporate-bussiness-sustainabilitiy?index=equities&symbol={quote(symbol)}").get("data") or []
        rows.sort(key=lambda r: r.get("fyTo") or 0, reverse=True)
        return rows

    def announcements_url(self, symbol: str) -> str:
        return f"{API}/corporate-announcements?index=equities&symbol={quote(symbol)}"

    def schemes_url(self, company_name: str) -> str:
        return f"{API}/corporates/offerdocs/arrangementscheme?index=equities&issuer={quote(company_name)}"
