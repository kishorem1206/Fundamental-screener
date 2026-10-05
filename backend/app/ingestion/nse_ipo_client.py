"""NSE IPO issue tracking — fetches the full public-issue archive
(`/api/public-past-issues`, confirmed live: 1,452 rows across every security
type back to 2016 — this is the same data NSE's own "IPO-PastIssue" CSV
export on https://www.nseindia.com/market-data/all-upcoming-issues-ipo comes
from) plus currently-open/upcoming issues (`/api/all-upcoming-issues?category=ipo`),
and stores every row in `fa_ipo_issues` regardless of security type.

Only mainboard equity (EQ/BE) issues get promoted into the `stocks`
universe (`promote_recent_ipos`) — SME-board, debt/NCDs, InvITs (IV) and
REITs (RR) don't fit this app's equity-scoring model at all, and SME-board
disclosure is too thin for Screener/Yahoo to usefully cover (2026-09-28
scope decision).

Weekly refresh entry point: `scripts/update_ipo_universe.py`.
"""
from __future__ import annotations

import re
import uuid
from datetime import date, datetime, timezone

import requests
from sqlalchemy.orm import Session

from app.infrastructure.database.models import IPOIssue
from app.logger import logger

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.3"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
}
_BOOTSTRAP_URL = "https://www.nseindia.com/market-data/all-upcoming-issues-ipo"
_PAST_ISSUES_URL = "https://www.nseindia.com/api/public-past-issues"
_UPCOMING_ISSUES_URL = "https://www.nseindia.com/api/all-upcoming-issues?category=ipo"

# Mainboard equity only — see module docstring for why SME/DEBT/N0/IV/RR/etc
# are stored (in `fa_ipo_issues`) but never promoted into `stocks`.
MAINBOARD_SECURITY_TYPES = frozenset({"EQ", "BE"})


def _session() -> requests.Session:
    """Same cookie-bootstrap pattern as `nse_client.py` — NSE's API rejects
    requests with no cookies acquired from an actual page visit first."""
    s = requests.Session()
    s.headers.update(_HEADERS)
    r = s.get(_BOOTSTRAP_URL, timeout=15)
    r.raise_for_status()
    return s


def _parse_date(raw: str | None) -> date | None:
    if not raw or raw.strip() in ("-", ""):
        return None
    for fmt in ("%d-%b-%Y", "%d-%B-%Y"):
        try:
            return datetime.strptime(raw.strip(), fmt).date()
        except ValueError:
            continue
    return None


_PRICE_RE = re.compile(r"(\d[\d,]*(?:\.\d+)?)")


def _parse_price_range(raw: str | None) -> tuple[float | None, float | None]:
    """"Rs.140 to Rs.148" -> (140, 148); "Rs.94" / "RS.41" -> (94, 94); a
    single-number range means a fixed-price issue, not a book-built band.
    Real formatting variance found live: some rows use "Rs 180 to Rs 186"
    (no dot), some drop "to" entirely ("Rs.130 Rs.140"), some have a
    trailing space. `_PRICE_RE` finds all embedded numbers regardless."""
    if not raw:
        return None, None
    nums = [float(n.replace(",", "")) for n in _PRICE_RE.findall(raw)]
    if not nums:
        return None, None
    if len(nums) == 1:
        return nums[0], nums[0]
    return nums[0], nums[-1]


def _parse_issue_price(raw: str | None) -> float | None:
    """A bare numeric issue price ("   186") or "-"/"######" (Excel-overflow
    junk from the CSV export path, or a book-built issue with no single
    fixed price) — never a real number in the second case."""
    if not raw:
        return None
    raw = raw.strip()
    if not raw or raw in ("-",) or "#" in raw:
        return None
    try:
        return float(raw.replace(",", ""))
    except ValueError:
        return None


def fetch_past_issues(session: requests.Session | None = None) -> list[dict]:
    """Every issue NSE has on record, every security type. Never raises —
    returns [] on any failure, same degrade-gracefully contract as every
    other ingestion client here."""
    try:
        s = session or _session()
        r = s.get(_PAST_ISSUES_URL, timeout=20, headers={"Referer": _BOOTSTRAP_URL})
        r.raise_for_status()
        return r.json() or []
    except Exception as e:
        logger.warning("nse_ipo_client: fetch_past_issues failed", error=str(e))
        return []


def fetch_upcoming_issues(session: requests.Session | None = None) -> list[dict]:
    """Currently open or announced-but-not-yet-open issues — a separate NSE
    endpoint from `fetch_past_issues`, shaped differently (camelCase
    "companyName"/"symbol"/"issuePrice"/"issueStartDate"/"issueEndDate",
    "series" instead of "securityType", a "status" field ("Active",
    "Forthcoming", ...) `fetch_past_issues` doesn't have). Never raises."""
    try:
        s = session or _session()
        r = s.get(_UPCOMING_ISSUES_URL, timeout=20, headers={"Referer": _BOOTSTRAP_URL})
        r.raise_for_status()
        return r.json() or []
    except Exception as e:
        logger.warning("nse_ipo_client: fetch_upcoming_issues failed", error=str(e))
        return []


def _upsert_past_issue(db: Session, row: dict, now: datetime, cache: dict) -> IPOIssue | None:
    symbol = (row.get("symbol") or "").strip().upper()
    company = (row.get("company") or "").strip()
    start = _parse_date(row.get("ipoStartDate"))
    if not symbol or not company or start is None:
        return None
    low, high = _parse_price_range(row.get("priceRange"))
    key = (symbol, start)
    existing = cache.get(key)
    issue = existing or IPOIssue(id=str(uuid.uuid4()), symbol=symbol, issue_start_date=start, created_at=now)
    cache[key] = issue
    issue.company_name = company
    issue.security_type = (row.get("securityType") or "UNKNOWN").strip()
    issue.issue_price = _parse_issue_price(row.get("issuePrice"))
    issue.price_range_low = low
    issue.price_range_high = high
    issue.issue_end_date = _parse_date(row.get("ipoEndDate"))
    issue.listing_date = _parse_date(row.get("listingDate"))
    issue.status = "Listed" if issue.listing_date else None
    issue.source = "NSE_PUBLIC_PAST_ISSUES"
    issue.fetched_at = now
    issue.updated_at = now
    if existing is None:
        db.add(issue)
    return issue


def _upsert_upcoming_issue(db: Session, row: dict, now: datetime, cache: dict) -> IPOIssue | None:
    symbol = (row.get("symbol") or "").strip().upper()
    company = (row.get("companyName") or "").strip()
    start = _parse_date(row.get("issueStartDate"))
    if not symbol or not company or start is None:
        return None
    low, high = _parse_price_range(row.get("issuePrice"))
    key = (symbol, start)
    existing = cache.get(key)
    issue = existing or IPOIssue(id=str(uuid.uuid4()), symbol=symbol, issue_start_date=start, created_at=now)
    cache[key] = issue
    issue.company_name = company
    issue.security_type = (row.get("series") or "UNKNOWN").strip()
    issue.issue_price = None  # this endpoint only ever gives a range, no fixed price field
    issue.price_range_low = low
    issue.price_range_high = high
    issue.issue_end_date = _parse_date(row.get("issueEndDate"))
    if existing is None:
        issue.listing_date = None  # by definition not listed yet, for a genuinely new row
    # else: leave whatever listing_date `_upsert_past_issue` (or an earlier
    # run) already established — this endpoint has no listing_date field at
    # all, "not listed yet" is an inference for a NEW row, not a fact this
    # endpoint reports; blindly nulling it here would erase a real value if
    # the same (symbol, issue_start_date) also came back from
    # `fetch_past_issues` in the same run (checked live: shouldn't normally
    # happen since a listed issue drops off "upcoming," but NSE's two
    # endpoints have shown drift before, and a defensive fix here is free).
    issue.status = row.get("status")
    issue.source = "NSE_ALL_UPCOMING_ISSUES"
    issue.fetched_at = now
    issue.updated_at = now
    if existing is None:
        db.add(issue)
    return issue


def ingest_ipo_issues(db: Session) -> dict:
    """Fetches both NSE endpoints and upserts every row into
    `fa_ipo_issues`. Never raises — logs and returns whatever it managed,
    same contract as every other ingestion module. Does NOT commit (caller's
    responsibility, matching every other ingestion function's convention)."""
    now = datetime.now(timezone.utc)
    try:
        s = _session()
    except Exception as e:
        logger.warning("nse_ipo_client: session bootstrap failed", error=str(e))
        return {"past_fetched": 0, "past_written": 0, "upcoming_fetched": 0, "upcoming_written": 0}
    past = fetch_past_issues(s)
    upcoming = fetch_upcoming_issues(s)

    # In-memory (symbol, issue_start_date) -> IPOIssue cache, seeded from
    # the DB, so a duplicate key WITHIN one fetch (confirmed live: NSE's own
    # past-issues endpoint repeats several rows verbatim, e.g. every InvIT/
    # REIT/NCD entry with two allotment tranches — "PKH" on 2023-06-30
    # appears twice) updates the same in-memory row instead of a second
    # INSERT racing the unique constraint before either is flushed.
    cache: dict[tuple[str, date], IPOIssue] = {
        (i.symbol, i.issue_start_date): i for i in db.query(IPOIssue).all()
    }

    past_written = upcoming_written = 0
    for row in past:
        if _upsert_past_issue(db, row, now, cache) is not None:
            past_written += 1
    for row in upcoming:
        if _upsert_upcoming_issue(db, row, now, cache) is not None:
            upcoming_written += 1

    logger.info("nse_ipo_client: ingested", past_fetched=len(past), past_written=past_written,
                upcoming_fetched=len(upcoming), upcoming_written=upcoming_written)
    return {"past_fetched": len(past), "past_written": past_written,
            "upcoming_fetched": len(upcoming), "upcoming_written": upcoming_written}


def promote_recent_ipos(db: Session, since: date) -> dict:
    """For every mainboard (EQ/BE) `fa_ipo_issues` row listed on/after
    `since`: ensure a matching `stocks` row exists (creating one from
    Yahoo's own sector/industry/market-cap when there isn't one yet — these
    are too newly listed to be in the Screener-scraped classification
    snapshot `classify_stocks_screener.py` builds; re-running that script
    later will upgrade a promoted IPO stock to real NSE `basic_industry`
    classification for free, same upsert-by-symbol convention it already
    has), then Yahoo-only quick-score it (2026-09-28 scope decision — full
    analysis stays a manual per-stock action, same as every other quick-
    scored stock). One bad company never aborts the batch. Commits per
    company (via `upsert_quick_score`), so a mid-run failure keeps whatever
    already succeeded."""
    from app.data.yfinance_client import fetch_financial_data
    from app.infrastructure.database.models import Stock
    from app.quick_analysis.scorer import quick_score as run_quick_score
    from app.quick_analysis.store import upsert_quick_score

    issues = (
        db.query(IPOIssue)
        .filter(IPOIssue.security_type.in_(MAINBOARD_SECURITY_TYPES))
        .filter(IPOIssue.listing_date.isnot(None), IPOIssue.listing_date >= since)
        .all()
    )

    now = datetime.now(timezone.utc)
    created = linked = quick_scored = failed = 0
    for issue in issues:
        try:
            stock_id = f"NSE:{issue.symbol}"
            stock = db.get(Stock, stock_id)
            data = fetch_financial_data("NSE", issue.symbol)

            if stock is None:
                if not data or data.get("error"):
                    # No Yahoo coverage yet (very common the first few days
                    # after listing) and no existing stocks row to fall
                    # back on — nothing usable to create it from, skip for
                    # this run; the next weekly pass retries it.
                    failed += 1
                    continue
                info = data.get("company_info") or {}
                mkt = data.get("market") or {}
                stock = Stock(
                    id=stock_id, symbol=issue.symbol, exchange="NSE",
                    company_name=info.get("long_name") or issue.company_name,
                    sector=info.get("sector"), industry=info.get("industry"), basic_industry=None,
                    macro_sector=None, market_cap=mkt.get("market_cap"),
                    is_active=True, ipo_listing_date=issue.listing_date,
                    created_at=now, updated_at=now,
                )
                db.add(stock)
                db.flush()
                created += 1
            else:
                if stock.ipo_listing_date is None:
                    stock.ipo_listing_date = issue.listing_date
                stock.updated_at = now
                linked += 1

            issue.stock_id = stock.id
            issue.updated_at = now

            if data and not data.get("error"):
                result = run_quick_score(stock.symbol, data, stock.sector, stock.industry, stock.basic_industry,
                                         db=db, company_id=stock.id)
                if not result.error:
                    upsert_quick_score(db, stock.id, result)
                    quick_scored += 1
        except Exception as e:  # noqa: BLE001 — one bad company must never stop the batch
            db.rollback()
            failed += 1
            logger.warning("nse_ipo_client: promote_recent_ipos failed for one company",
                            symbol=issue.symbol, error=str(e))

    db.commit()
    logger.info("nse_ipo_client: promoted recent IPOs", candidates=len(issues), created=created,
                linked=linked, quick_scored=quick_scored, failed=failed)
    return {"candidates": len(issues), "created": created, "linked": linked,
            "quick_scored": quick_scored, "failed": failed}
