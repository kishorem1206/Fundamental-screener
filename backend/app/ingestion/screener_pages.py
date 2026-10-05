"""One read of a company's Screener page, shared by every Screener ingest.

Each `ingest_*` function in screener_client.py, pnl_history_client.py,
quarterly_results_client.py and screener_shareholding_client.py builds its own
`openscreener.Stock`, and each of those opens a browser and loads the page
again — about ten page loads per company for sections that all sit on the same
two pages (standalone and consolidated). Inside `prefetched(symbol)` the two
pages are read once over plain HTTP and every ingest parses that copy instead.
Outside it, `screener_stock()` behaves exactly as before.

Requests are paced across threads (Screener answers HTTP 429 when hit quickly)
and a 429 is retried with a growing wait.
"""
from __future__ import annotations

import threading
import time
from contextlib import contextmanager
from contextvars import ContextVar

import httpx

URL = "https://www.screener.in/company/{symbol}/{suffix}"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}
MIN_INTERVAL = 1.2  # seconds between requests, across all threads

_pages: ContextVar[dict | None] = ContextVar("screener_pages", default=None)
_lock = threading.Lock()
_next_slot = 0.0


def _wait_turn() -> None:
    global _next_slot
    with _lock:
        now = time.monotonic()
        slot = max(now, _next_slot)
        _next_slot = slot + MIN_INTERVAL
    time.sleep(max(0.0, slot - now))


def fetch_html(symbol: str, consolidated: bool) -> str:
    from openscreener.exceptions import OpenScreenerError

    url = URL.format(symbol=symbol.upper(), suffix="consolidated/" if consolidated else "")
    for attempt in range(5):
        _wait_turn()
        try:
            r = httpx.get(url, headers=HEADERS, follow_redirects=True, timeout=30)
        except httpx.HTTPError as exc:
            if attempt == 4:
                raise OpenScreenerError(f"Could not load Screener page for symbol '{symbol.upper()}': {exc}") from exc
            time.sleep(5 * (attempt + 1))
            continue
        if r.status_code == 429:
            time.sleep(20 * (attempt + 1))
            continue
        if r.status_code >= 400:
            raise OpenScreenerError(f"Screener.in returned HTTP {r.status_code} for symbol '{symbol.upper()}'.")
        if 'id="top"' not in r.text:
            raise OpenScreenerError(f"Could not find Screener page content for symbol '{symbol.upper()}'.")
        return r.text
    raise OpenScreenerError(f"Screener.in kept answering HTTP 429 for symbol '{symbol.upper()}'.")


@contextmanager
def prefetched(symbol: str):
    """Reads the standalone and consolidated pages once; every `screener_stock()`
    call for this symbol inside the block uses them. A page that failed to load
    raises the same error inside the block that a live load would have."""
    current = _pages.get() or {}
    if (symbol.upper(), False) in current:  # already read by an enclosing block: never read twice
        yield current
        return
    pages: dict = {}
    for consolidated in (False, True):
        try:
            pages[(symbol.upper(), consolidated)] = fetch_html(symbol, consolidated)
        except Exception as exc:  # kept and re-raised where the page is used
            pages[(symbol.upper(), consolidated)] = exc
    token = _pages.set(pages)
    try:
        yield pages
    finally:
        _pages.reset(token)


def screener_stock(symbol: str, consolidated: bool):
    from openscreener import Stock

    cached = (_pages.get() or {}).get((symbol.upper(), consolidated))
    if cached is None:
        return Stock(symbol, consolidated=consolidated)
    if isinstance(cached, Exception):
        raise cached
    return Stock(symbol, consolidated=consolidated, page_html=cached)
