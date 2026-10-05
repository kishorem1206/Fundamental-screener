"""NSE's daily index file — every Nifty index's open, high, low, close, volume,
turnover, P/E, P/B and dividend yield for one trading day.

    https://nsearchives.nseindia.com/content/indices/ind_close_all_DDMMYYYY.csv

One file per trading day; a weekend or exchange holiday has no file (HTTP 404).
"""
from __future__ import annotations

import csv
import io
import time
from datetime import date, datetime, timedelta

import httpx
from sqlalchemy.orm import Session

from app.logger import logger
from app.prices import store

URL = "https://nsearchives.nseindia.com/content/indices/ind_close_all_{:%d%m%Y}.csv"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept": "text/csv,*/*",
}
_PAUSE = 0.3


def _number(raw: str | None) -> float | None:
    raw = (raw or "").strip().replace(",", "")
    if raw in ("", "-", "NA"):
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def parse(text: str, url: str) -> list[dict]:
    """Rows of one day's file. An index with no closing value that day is skipped."""
    rows = []
    for r in csv.DictReader(io.StringIO(text)):
        r = {(k or "").strip(): v for k, v in r.items()}
        close = _number(r.get("Closing Index Value"))
        name = (r.get("Index Name") or "").strip()
        if not name or close is None:
            continue
        volume = _number(r.get("Volume"))
        rows.append({
            "index_name": name,
            "bar_date": datetime.strptime(r["Index Date"].strip(), "%d-%m-%Y").date(),
            "open": _number(r.get("Open Index Value")),
            "high": _number(r.get("High Index Value")),
            "low": _number(r.get("Low Index Value")),
            "close": close,
            "volume": int(volume) if volume is not None else None,
            "turnover_cr": _number(r.get("Turnover (Rs. Cr.)")),
            "pe": _number(r.get("P/E")),
            "pb": _number(r.get("P/B")),
            "div_yield": _number(r.get("Div Yield")),
            "source_url": url,
        })
    return rows


def fetch(day: date, client: httpx.Client) -> list[dict] | None:
    """None when NSE has no file for that day (holiday). Raises on any other failure."""
    url = URL.format(day)
    for attempt in range(3):
        r = client.get(url)
        if r.status_code == 404:
            return None
        if r.status_code == 200 and r.text.startswith("Index Name"):
            return parse(r.text, url)
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"NSE index file for {day}: HTTP {r.status_code}")


def ingest(db: Session, since: date, until: date | None = None) -> dict:
    """Fetches every weekday in the range that is not stored yet."""
    until = until or date.today()
    have = store.index_dates(db)
    days = [since + timedelta(n) for n in range((until - since).days + 1)]
    days = [d for d in days if d.weekday() < 5 and d not in have]
    stored = holidays = failed = 0
    with httpx.Client(headers=HEADERS, timeout=30, follow_redirects=True) as client:
        for day in days:
            try:
                rows = fetch(day, client)
            except Exception as exc:
                failed += 1
                logger.warning("index file failed", day=str(day), error=str(exc))
                continue
            if rows is None:
                holidays += 1
            else:
                store.upsert_index_bars(db, rows)
                db.commit()
                stored += 1
            time.sleep(_PAUSE)
    return {"days_stored": stored, "no_file": holidays, "failed": failed}
