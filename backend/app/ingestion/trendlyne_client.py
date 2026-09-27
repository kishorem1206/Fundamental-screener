"""Trendlyne.com — broker research-report history, free table only.

Confirmed live (2026-09-14, Persistent Systems/Jyothy Labs): default
headless-browser requests get a CloudFront 403 (bot-detection on the
default fingerprint, not a real login wall) — a realistic desktop
User-Agent/viewport/locale is enough to get a real 200. The actual PDF
report text sits behind `/visitor/loginmodal/` and is NOT fetched here;
only the free metadata table (date, broker, rating, target price,
price-at-reco) is, which is genuinely new — `AnalystConsensus` is a
current-snapshot aggregate, this is the dated history of individual calls.

`research-reports/stock/{SYMBOL}/` (bare symbol, no internal Trendlyne ID
needed) 302-redirects to the canonical `.../stock/{id}/{SYMBOL}/{slug}/`
URL — confirmed live, so no separate symbol->ID lookup step is needed.
"""
from __future__ import annotations

import html as html_lib
import re
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.infrastructure.database.models import BrokerResearchReport
from app.logger import logger

SOURCE = "TRENDLYNE"
_BASE = "https://trendlyne.com"
_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)
_SKIP_AUTHORS = {"consensus share price target"}  # the table's synthetic aggregate row, not a real dated report


def _parse_date(raw: str) -> str | None:
    """"14 Sep 2026" -> "2026-09-14"."""
    try:
        return datetime.strptime(raw.strip(), "%d %b %Y").date().isoformat()
    except ValueError:
        return None


def _clean_number(raw: str) -> float | None:
    raw = raw.strip()
    if not raw or raw == "-":
        return None
    try:
        return float(raw.replace(",", ""))
    except ValueError:
        return None


def _strip_tags(raw_html: str) -> str:
    # Real bug found 2026-09-14: an unescaped trailing "&nbsp;" (rendered
    # as literal text, not a real space, since this only strips tags) left
    # broker names as "ICICI Securities Limited Reco &nbsp;" — breaking
    # both the display name and the Reco/Target flag-word regex below,
    # which only matches at the true string end. html.unescape() first,
    # then collapse whitespace.
    text = html_lib.unescape(re.sub(r"<[^>]+>", " ", raw_html))
    return re.sub(r"\s+", " ", text).strip()


def fetch_research_reports(symbol: str) -> list[dict]:
    """Never raises — returns [] on any failure (page not found, layout
    changed, blocked despite the realistic fingerprint, etc.)."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.warning("trendlyne_client: playwright not installed")
        return []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                context = browser.new_context(
                    user_agent=_USER_AGENT, viewport={"width": 1440, "height": 900}, locale="en-IN",
                )
                page = context.new_page()
                resp = page.goto(
                    f"{_BASE}/research-reports/stock/{symbol.upper()}/",
                    wait_until="domcontentloaded", timeout=30000,
                )
                if resp is None or resp.status != 200:
                    logger.info("trendlyne_client: no research-reports page", symbol=symbol,
                                status=resp.status if resp else None)
                    return []
                page.wait_for_timeout(2500)
                table = page.query_selector("table")
                if table is None:
                    return []
                table_html = table.inner_html()
            finally:
                browser.close()
    except Exception as e:
        logger.warning("trendlyne_client: fetch failed", symbol=symbol, error=str(e))
        return []

    rows_html = re.findall(r"<tr[^>]*role=\"row\"[^>]*>(.*?)</tr>", table_html, re.S)
    reports = []
    for row_html in rows_html:
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row_html, re.S)
        if len(cells) < 9:
            continue
        author_raw = _strip_tags(cells[3])
        if not author_raw or author_raw.lower() in _SKIP_AUTHORS:
            continue

        report_date = _parse_date(_strip_tags(cells[1]))
        if report_date is None:
            continue

        # The broker name cell has "Reco"/"Target" change-flag words appended
        # at the end (0, 1, or both, in either order — e.g. "Geojit BNP
        # Paribas Reco Target") rather than in a separately parseable
        # element, so they're stripped iteratively rather than assuming a
        # single fixed suffix.
        flag_words = []
        cleaned = author_raw
        while True:
            m = re.search(r"\s*(Reco|Target)\s*$", cleaned)
            if not m:
                break
            flag_words.append(m.group(1))
            cleaned = cleaned[:m.start()]
        broker_name = cleaned.strip()
        if not broker_name:
            continue
        reco_changed = "Reco" in flag_words
        target_changed = "Target" in flag_words

        ltp = _clean_number(_strip_tags(cells[4]))
        target_price = _clean_number(_strip_tags(cells[5]))
        price_at_reco_raw = _strip_tags(cells[6])
        m = re.match(r"([\d,.]+)\s*\(([-\d.]+)%\)", price_at_reco_raw)
        price_at_reco = _clean_number(m.group(1)) if m else None
        change_since_reco_pct = float(m.group(2)) if m else None
        upside_pct = _clean_number(_strip_tags(cells[7]))
        rating = _strip_tags(cells[8]) or None

        report_url_match = re.search(r'href="(https://trendlyne\.com/equity/stock-report/[^"]+)"', cells[9] if len(cells) > 9 else "")
        report_url = report_url_match.group(1) if report_url_match else None

        reports.append({
            "report_date": report_date, "broker_name": broker_name, "rating": rating,
            "target_price": target_price, "ltp_at_capture": ltp, "price_at_reco": price_at_reco,
            "change_since_reco_pct": change_since_reco_pct, "upside_pct": upside_pct,
            "reco_changed": reco_changed, "target_changed": target_changed, "report_url": report_url,
        })
    return reports


def ingest_research_reports(db: Session, company_id: str, symbol: str) -> int:
    """Never raises — logs and returns 0 on any failure. Upserts by
    (company_id, report_date, broker_name) — re-running is idempotent."""
    try:
        reports = fetch_research_reports(symbol)
        if not reports:
            return 0

        now = datetime.now(timezone.utc)
        stored = 0
        for r in reports:
            existing = (
                db.query(BrokerResearchReport)
                .filter_by(company_id=company_id, report_date=r["report_date"], broker_name=r["broker_name"])
                .first()
            )
            if existing:
                for k, v in r.items():
                    setattr(existing, k, v)
                existing.retrieved_at = now
            else:
                db.add(BrokerResearchReport(
                    id=str(uuid.uuid4()), company_id=company_id, source=SOURCE, retrieved_at=now, **r,
                ))
                stored += 1
        db.flush()
        logger.info("trendlyne_client: research reports ingested", symbol=symbol,
                    total_found=len(reports), new_rows=stored)
        return stored
    except Exception as e:
        logger.warning("trendlyne_client: ingestion failed", symbol=symbol, error=str(e))
        return 0
