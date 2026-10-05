"""NSE's official full equity list (`EQUITY_L.csv`, ~2,580 rows, every
listed EQ/BE/BZ symbol) — used to fill gaps in the `stocks` universe, which
was originally built from Screener's "market cap > 1000cr" screen
(`scripts/classify_stocks_screener.py`) and so never had the ~950 smaller-
cap NSE-listed companies below that threshold at all (confirmed live,
2026-09-28: 954 EQ/BE symbols in this CSV had no `stocks` row).

Same two-step shape as `nse_ipo_client.py`: `sync_missing_stocks()` adds a
bare `stocks` row for every NSE-listed EQ/BE symbol not already present
(name + listing date only, no sector yet — that needs Yahoo or Screener,
which this module deliberately doesn't call, to keep this step fast and
network-light), then `classify_and_score_unclassified()` (Yahoo-only, same
approach `nse_ipo_client.py::promote_recent_ipos()` uses for new IPO
listings) fills in sector/industry/market cap and a quick score for
whichever `stocks` rows — from this sync OR from IPO promotion — still
have no sector on record. Re-running `scripts/classify_stocks_screener.py`
afterward upgrades any of these to real NSE `basic_industry` classification
for free (that script already upserts by symbol; it just needs its own
`cache/screener_symbol_name_map.json` regenerated to know about symbols
this module added that Screener's own snapshot didn't have yet).
"""
from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime, timezone

import requests
from sqlalchemy.orm import Session

from app.infrastructure.database.models import Stock
from app.logger import logger

EQUITY_LIST_URL = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.3"
    ),
}
# Same mainboard-only scope as nse_ipo_client.py — BZ (and anything else
# NSE lists that isn't EQ/BE) is a trading-restriction/suspension series
# tag, not a distinct business type, but it's still not a normal tradeable
# mainboard listing, so it's excluded on the same "doesn't fit this app's
# equity-scoring model" grounds.
MAINBOARD_SERIES = frozenset({"EQ", "BE"})


def _parse_date(raw: str | None):
    if not raw or raw.strip() in ("-", ""):
        return None
    try:
        return datetime.strptime(raw.strip(), "%d-%b-%Y").date()
    except ValueError:
        return None


def fetch_equity_list() -> list[dict]:
    """Every row from NSE's own EQUITY_L.csv, raw field names as NSE
    provides them (leading-space column names and all — normalized to
    stripped keys here for the caller's convenience). Never raises —
    returns [] on any failure, same degrade-gracefully contract as every
    other ingestion client here."""
    try:
        r = requests.get(EQUITY_LIST_URL, headers=_HEADERS, timeout=30)
        r.raise_for_status()
        reader = csv.DictReader(io.StringIO(r.text))
        return [{k.strip(): (v.strip() if v else v) for k, v in row.items()} for row in reader]
    except Exception as e:
        logger.warning("nse_equity_list_client: fetch failed", error=str(e))
        return []


def sync_missing_stocks(db: Session) -> dict:
    """Adds a bare `stocks` row (symbol, company_name, listing date; no
    sector/market cap yet) for every mainboard NSE symbol in EQUITY_L.csv
    not already in `stocks`. Commits. Never raises."""
    rows = fetch_equity_list()
    if not rows:
        return {"fetched": 0, "added": 0}

    existing = {r[0] for r in db.query(Stock.symbol).all()}
    now = datetime.now(timezone.utc)
    added = 0
    for row in rows:
        series = (row.get("SERIES") or "").upper()
        symbol = (row.get("SYMBOL") or "").strip().upper()
        if series not in MAINBOARD_SERIES or not symbol or symbol in existing:
            continue
        company_name = row.get("NAME OF COMPANY") or symbol
        db.add(Stock(
            id=f"NSE:{symbol}", symbol=symbol, exchange="NSE", company_name=company_name,
            is_active=True, ipo_listing_date=_parse_date(row.get("DATE OF LISTING")),
            created_at=now, updated_at=now,
        ))
        existing.add(symbol)
        added += 1
    db.commit()
    logger.info("nse_equity_list_client: synced missing stocks", fetched=len(rows), added=added)
    return {"fetched": len(rows), "added": added}


def classify_and_score_unclassified(db: Session, limit: int | None = None) -> dict:
    """Yahoo-only sector/industry/market-cap fill + quick score for every
    `stocks` row with no sector on record yet (whatever the reason — newly
    synced from EQUITY_L.csv, a promoted IPO Yahoo couldn't classify on
    first try, etc.). Same method as `nse_ipo_client.py::promote_recent_ipos()`
    — see that function's docstring for why Yahoo, not Screener, here.
    One bad company never aborts the batch; commits per company."""
    from app.data.yfinance_client import fetch_financial_data
    from app.quick_analysis.runner import _Pacer, _is_throttled
    from app.quick_analysis.scorer import quick_score as run_quick_score
    from app.quick_analysis.store import upsert_quick_score

    query = db.query(Stock).filter(Stock.is_active.is_(True), Stock.sector.is_(None))
    if limit:
        query = query.limit(limit)
    stocks = query.all()

    # Real bug found live (2026-09-28): an earlier version of this function
    # called `fetch_financial_data` back-to-back with no pacing at all —
    # Yahoo started rejecting requests after ~88 of 960 companies, and every
    # one after that silently failed (confirmed: `failed=872` on that run).
    # `_Pacer` is `app/quick_analysis/runner.py`'s own proven fix for this
    # exact problem (spaces requests, exponential backoff 60s->15min on any
    # 429), reused here rather than re-solving the same problem worse.
    pacer = _Pacer(stocks_per_sec=1.5)

    now = datetime.now(timezone.utc)
    classified = quick_scored = failed = 0
    for stock in stocks:
        try:
            data: dict = {}
            for _ in range(3):
                pacer.wait_turn()
                data = fetch_financial_data(stock.exchange, stock.symbol)
                if not _is_throttled(data):
                    pacer.report_ok()
                    break
                pacer.report_throttled()
            if not data or data.get("error"):
                failed += 1
                continue
            info = data.get("company_info") or {}
            mkt = data.get("market") or {}
            if info.get("sector"):
                stock.sector = info["sector"]
                stock.industry = info.get("industry")
            if mkt.get("market_cap"):
                stock.market_cap = mkt["market_cap"]
            stock.updated_at = now
            classified += 1

            result = run_quick_score(stock.symbol, data, stock.sector, stock.industry, stock.basic_industry,
                                     db=db, company_id=stock.id)
            if not result.error:
                upsert_quick_score(db, stock.id, result)  # commits
                quick_scored += 1
            else:
                db.commit()
        except Exception as e:  # noqa: BLE001 — one bad company must never stop the batch
            db.rollback()
            failed += 1
            logger.warning("nse_equity_list_client: classify_and_score failed for one company",
                            symbol=stock.symbol, error=str(e))

    logger.info("nse_equity_list_client: classified + scored", candidates=len(stocks),
                classified=classified, quick_scored=quick_scored, failed=failed)
    return {"candidates": len(stocks), "classified": classified, "quick_scored": quick_scored, "failed": failed}
