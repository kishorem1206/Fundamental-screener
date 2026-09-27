"""Business segment revenue — Deep Research System, Stage R1. Sourced from
TradingView's financials-segments page (free, no login wall) — confirmed
live (Jyothy Labs, 2026-09-14) to return a genuine multi-segment revenue
table. Nothing in this codebase extracted segment-level revenue before this
— every sector file's segment-related metrics (automobile.py, pharma.py,
chemicals.py, etc.) sat as unfulfilled `na_message` placeholders.

**Why this scrapes rendered text, not a JSON API**: network-intercepted the
page load and found no isolable XHR/WS endpoint carrying the segment
numbers, and the initial HTML only has the page's generic schema.org
description — the numbers are painted into the DOM by TradingView's own
client-side widget. `page.inner_text("body")` is what's actually parsed.

**Why fiscal years are NOT read off TradingView's own axis labels**: the
widget shows a fixed 20-year header (e.g. "2006"..."2025" for Jyothy) but
each segment row only ever renders a short trailing window of tokens
(confirmed: exactly 5 for every segment on Jyothy's page, value-or-"—"),
right-aligned to "last year". TradingView's own axis-year labels don't
reliably correspond to Indian fiscal-year-end dates (confirmed: its "last
year" total revenue matched Jyothy's own FY2026 pnl_sales figure — a fiscal
year TradingView's own axis never labels "2026"). So instead of trusting
that axis text, the last token of every segment's window is anchored to
THIS company's own latest known fiscal-year-end date (from metric_store's
"pnl_sales" history — already ingested by pnl_history_client.py), and
earlier tokens are dated by walking back one fiscal year at a time from
there. A "—" token means "not reported that year" and is skipped, not
stored as zero.
"""
from __future__ import annotations

import re
import uuid
from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.infrastructure.database import metric_store
from app.infrastructure.database.models import BusinessSegment
from app.logger import logger

SOURCE = "TRADINGVIEW"
_TV_BASE = "https://www.tradingview.com/symbols"

_VALUE_RE = re.compile(r"^([\d,]+\.?\d*)\s*(B|M|K|Cr)$")
_DASH_TOKENS = {"—", "-", "–"}
_SECTION_BREAK_PREFIXES = ("By ",)


def _clean(line: str) -> str:
    return line.replace("‪", "").replace("‬", "").strip()


def _parse_value(token: str) -> float | None:
    """"13.46 B" -> 13_460_000_000.0 — always normalized to plain INR."""
    m = _VALUE_RE.match(token)
    if not m:
        return None
    num = float(m.group(1).replace(",", ""))
    mult = {"B": 1e9, "M": 1e6, "K": 1e3, "Cr": 1e7}[m.group(2)]
    return num * mult


def _parse_segment_table(body_text: str) -> dict[str, list[float | None]]:
    """Returns {segment_name: [oldest_in_window, ..., latest]} — `None` at
    a position means that year wasn't reported for that segment (a "—" in
    the source), not a real zero."""
    lines = [_clean(l) for l in body_text.split("\n")]
    lines = [l for l in lines if l]

    try:
        start = next(i for i, l in enumerate(lines) if l == "Metrics")
    except StopIteration:
        return {}
    end = next(
        (i for i, l in enumerate(lines[start + 1:], start + 1)
         if l.startswith(_SECTION_BREAK_PREFIXES)),
        len(lines),
    )
    block = lines[start + 1:end]

    # Skip the leading "Currency: ..." line and the header's bare year
    # digits (e.g. "2006".."2025") — neither is a segment name or value.
    i = 0
    if i < len(block) and block[i].lower().startswith("currency"):
        i += 1
    while i < len(block) and block[i].isdigit():
        i += 1

    segments: dict[str, list[float | None]] = {}
    current: str | None = None
    while i < len(block):
        line = block[i]
        if line in _DASH_TOKENS:
            if current:
                segments[current].append(None)
        else:
            val = _parse_value(line)
            if val is not None and current:
                segments[current].append(val)
            else:
                # Not a value/dash -> this line is a new segment name.
                current = line
                segments[current] = []
        i += 1
    return segments


def _company_latest_fiscal_year_end(db: Session, company_id: str) -> date | None:
    """The company's own most recent confirmed fiscal-year-end date, from
    metric_store's "pnl_sales" history (pnl_history_client.py) — the real
    anchor for dating TradingView's window, not TradingView's own axis.
    statement_type=None (both types) since a fiscal-year-END DATE is the
    same regardless of which statement type reported it — using only
    whichever type happens to be the read-default could miss a more
    recent date if the other type's ingestion ran more recently."""
    rows = metric_store.get_metric_history(db, company_id, "pnl_sales", statement_type=None)
    dates: list[date] = []
    for r in rows:
        if r.period == "TTM":
            continue
        try:
            dates.append(datetime.strptime(r.period, "%Y-%m-%d").date())
        except ValueError:
            continue
    return max(dates) if dates else None


def fetch_segments(symbol: str) -> dict[str, list[float | None]]:
    """Tries NSE first (most India-listed stocks resolve there), falls back
    to BSE. Never raises — returns {} on any failure."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.warning("tradingview_segments_client: playwright not installed")
        return {}

    for exchange in ("NSE", "BSE"):
        url = f"{_TV_BASE}/{exchange}-{symbol.upper()}/financials-segments/"
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                try:
                    page = browser.new_page()
                    page.goto(url, wait_until="networkidle", timeout=45000)
                    page.wait_for_timeout(1500)
                    body_text = page.inner_text("body")
                finally:
                    browser.close()
        except Exception as e:
            logger.warning("tradingview_segments_client: fetch failed", symbol=symbol, exchange=exchange, error=str(e))
            continue

        segments = _parse_segment_table(body_text)
        if segments:
            return segments
    return {}


def ingest_business_segments(db: Session, company_id: str, symbol: str) -> list[BusinessSegment]:
    """Fetches + stores segment revenue history. Never raises — logs and
    returns [] on any failure, matching every other ingestion module here."""
    try:
        raw = fetch_segments(symbol)
        if not raw:
            logger.info("tradingview_segments_client: no segment data found", symbol=symbol)
            return []

        anchor = _company_latest_fiscal_year_end(db, company_id)
        if anchor is None:
            logger.warning("tradingview_segments_client: no known fiscal year to anchor to", symbol=symbol)
            return []

        now = datetime.now(timezone.utc)
        stored: list[BusinessSegment] = []
        for segment_name, values in raw.items():
            for offset_from_latest, value in enumerate(reversed(values)):
                if value is None:
                    continue
                fy_end = date(anchor.year - offset_from_latest, anchor.month, anchor.day)
                fiscal_year = fy_end.isoformat()

                existing = (
                    db.query(BusinessSegment)
                    .filter_by(company_id=company_id, segment_name=segment_name, fiscal_year=fiscal_year)
                    .first()
                )
                if existing:
                    existing.revenue = value
                    existing.retrieved_at = now
                    stored.append(existing)
                else:
                    row = BusinessSegment(
                        id=str(uuid.uuid4()), company_id=company_id,
                        segment_name=segment_name, fiscal_year=fiscal_year,
                        revenue=value, currency="INR", source=SOURCE, retrieved_at=now,
                    )
                    db.add(row)
                    stored.append(row)

        db.flush()
        logger.info("tradingview_segments_client: segments ingested", symbol=symbol,
                    segment_count=len(raw), rows_stored=len(stored))
        return stored
    except Exception as e:
        logger.warning("tradingview_segments_client: ingestion failed", symbol=symbol, error=str(e))
        return []
