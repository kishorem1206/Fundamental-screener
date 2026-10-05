"""
Refreshes Nifty index universe data from the official NSE CSV files.

Run via:  POST /admin/universes/refresh
          make refresh-universes

Sources (all public, no auth required):
  Nifty 50           → LARGE_CAP, in NIFTY_50 + NIFTY_500 + NIFTY_TOTAL_MARKET
  Nifty Next 50      → LARGE_CAP, in NIFTY_500 + NIFTY_TOTAL_MARKET
  Nifty Midcap 150   → MID_CAP,   in NIFTY_500 + NIFTY_TOTAL_MARKET
  Nifty Smallcap 250 → SMALL_CAP, in NIFTY_500 + NIFTY_TOTAL_MARKET
  Nifty Total Market → MICRO_CAP (for remainder not in above), in NIFTY_TOTAL_MARKET

Market cap categories follow SEBI classification:
  Large Cap  = rank 1–100  (Nifty 50 + Next 50)
  Mid Cap    = rank 101–250 (Nifty Midcap 150)
  Small Cap  = rank 251–500 (Nifty Smallcap 250)
  Micro Cap  = rank 500+   (Total Market remainder)
"""

import csv
import io
from dataclasses import dataclass, field
from datetime import datetime, timezone

import httpx
from sqlalchemy import text

from app.infrastructure.database.client import get_db
from app.infrastructure.database.models import Stock, Universe, UniverseMembership
from app.logger import logger

_STALE_DAYS = 90  # warn if data is older than this

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.niftyindices.com/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Processed in order — first assignment of cap_category wins (MICRO_CAP is fallback)
_INDEX_SOURCES = [
    {
        "label": "Nifty 50",
        "url": "https://www.niftyindices.com/IndexConstituent/ind_nifty50list.csv",
        "cap_category": "LARGE_CAP",
        "universe_ids": ["NIFTY_50", "NIFTY_500", "NIFTY_TOTAL_MARKET"],
    },
    {
        "label": "Nifty Next 50",
        "url": "https://www.niftyindices.com/IndexConstituent/ind_niftynext50list.csv",
        "cap_category": "LARGE_CAP",
        "universe_ids": ["NIFTY_500", "NIFTY_TOTAL_MARKET"],
    },
    {
        "label": "Nifty Midcap 150",
        "url": "https://www.niftyindices.com/IndexConstituent/ind_niftymidcap150list.csv",
        "cap_category": "MID_CAP",
        "universe_ids": ["NIFTY_500", "NIFTY_TOTAL_MARKET"],
    },
    {
        "label": "Nifty Smallcap 250",
        "url": "https://www.niftyindices.com/IndexConstituent/ind_niftysmallcap250list.csv",
        "cap_category": "SMALL_CAP",
        "universe_ids": ["NIFTY_500", "NIFTY_TOTAL_MARKET"],
    },
    {
        "label": "Nifty Total Market",
        "url": "https://www.niftyindices.com/IndexConstituent/ind_niftytotalmarket_list.csv",
        "cap_category": "MICRO_CAP",   # only applied to stocks not yet classified above
        "universe_ids": ["NIFTY_TOTAL_MARKET"],
    },
]

_UNIVERSE_DEFS = {
    "NIFTY_50":           {"name": "Nifty 50",           "description": "NSE Nifty 50 large-cap index"},
    "NIFTY_500":          {"name": "Nifty 500",           "description": "NSE Nifty 500 index (large, mid and small cap)"},
    "NIFTY_TOTAL_MARKET": {"name": "Nifty Total Market",  "description": "NSE Nifty Total Market index — all exchange-eligible NSE stocks"},
}

_MANAGED_UNIVERSE_IDS = list(_UNIVERSE_DEFS.keys())


@dataclass
class StockRecord:
    symbol: str
    isin: str
    company_name: str
    sector: str
    cap_category: str
    universe_ids: set[str] = field(default_factory=set)


def _fetch_csv(url: str, label: str) -> list[dict]:
    """Download and parse one index CSV from niftyindices.com."""
    logger.info("Fetching index CSV", label=label, url=url)
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        r = client.get(url, headers=_HEADERS)
    r.raise_for_status()
    rows = list(csv.DictReader(io.StringIO(r.text.strip())))
    logger.info("Fetched index CSV", label=label, rows=len(rows))
    return rows


def _parse_symbol(row: dict) -> str:
    return (row.get("Symbol") or row.get("symbol") or "").strip().upper()


def _parse_isin(row: dict) -> str:
    return (row.get("ISIN Code") or row.get("ISIN") or row.get("isin") or "").strip()


def _parse_company(row: dict) -> str:
    return (row.get("Company Name") or row.get("company_name") or "").strip()


def _parse_sector(row: dict) -> str:
    return (row.get("Industry") or row.get("industry") or row.get("Sector") or "").strip()


def _build_stock_map(fetch_errors: list[str]) -> dict[str, StockRecord]:
    """
    Fetch all CSVs and build a unified {isin: StockRecord} dict.
    First CSV that classifies a stock wins (so MICRO_CAP is only for Total Market leftovers).
    """
    stock_map: dict[str, StockRecord] = {}

    for src in _INDEX_SOURCES:
        try:
            rows = _fetch_csv(src["url"], src["label"])
        except Exception as e:
            msg = f"{src['label']}: {e}"
            fetch_errors.append(msg)
            logger.error("CSV fetch failed", label=src["label"], error=str(e))
            continue

        for row in rows:
            symbol = _parse_symbol(row)
            isin = _parse_isin(row)
            if not symbol or not isin:
                continue

            if isin not in stock_map:
                stock_map[isin] = StockRecord(
                    symbol=symbol,
                    isin=isin,
                    company_name=_parse_company(row),
                    sector=_parse_sector(row),
                    cap_category=src["cap_category"],
                )

            stock_map[isin].universe_ids.update(src["universe_ids"])

    return stock_map


class NiftyRefreshService:
    def refresh(self, force: bool = False) -> dict:
        """
        Download NSE index CSVs and synchronise the database.

        Returns a summary dict with counts and any fetch errors.
        Raises RuntimeError if no data could be fetched at all.
        """
        db = get_db()
        now = datetime.now(timezone.utc)

        # Optional staleness check
        if not force:
            row = db.execute(
                text("SELECT MIN(last_synced_at) FROM universes WHERE id = ANY(:ids)"),
                {"ids": _MANAGED_UNIVERSE_IDS},
            ).fetchone()
            if row and row[0]:
                age_days = (now - row[0]).days
                if age_days < _STALE_DAYS:
                    db.close()
                    return {
                        "skipped": True,
                        "reason": f"Data is {age_days}d old — less than {_STALE_DAYS}d threshold. Pass force=true to override.",
                        "last_synced_at": row[0].isoformat(),
                    }

        fetch_errors: list[str] = []
        stock_map = _build_stock_map(fetch_errors)

        if not stock_map:
            db.close()
            raise RuntimeError(
                "All CSV fetches failed — no data to load. Check network or niftyindices.com availability.\n"
                + "\n".join(fetch_errors)
            )

        try:
            # 1. Ensure managed universes exist
            for uid, udef in _UNIVERSE_DEFS.items():
                existing = db.get(Universe, uid)
                if existing:
                    existing.name = udef["name"]
                    existing.description = udef["description"]
                    existing.updated_at = now
                else:
                    db.add(Universe(
                        id=uid,
                        name=udef["name"],
                        description=udef["description"],
                        is_built_in=True,
                        stock_count=0,
                        created_at=now,
                        updated_at=now,
                    ))
            db.flush()

            # 2. Upsert stocks (NSE exchange, EQ series only)
            for rec in stock_map.values():
                stock_id = f"NSE:{rec.symbol}"
                existing = db.get(Stock, stock_id)
                if existing:
                    existing.company_name = rec.company_name
                    existing.isin = rec.isin
                    existing.sector = rec.sector or existing.sector
                    existing.market_cap_category = rec.cap_category
                    existing.is_active = True
                    existing.updated_at = now
                else:
                    db.add(Stock(
                        id=stock_id,
                        symbol=rec.symbol,
                        exchange="NSE",
                        company_name=rec.company_name,
                        isin=rec.isin,
                        sector=rec.sector or None,
                        industry=rec.sector or None,
                        market_cap_category=rec.cap_category,
                        is_active=True,
                        created_at=now,
                        updated_at=now,
                    ))
            db.flush()

            # 3. Replace memberships for managed universes
            db.execute(
                text("DELETE FROM universe_memberships WHERE universe_id = ANY(:ids)"),
                {"ids": _MANAGED_UNIVERSE_IDS},
            )
            db.flush()

            for rec in stock_map.values():
                stock_id = f"NSE:{rec.symbol}"
                for uid in rec.universe_ids:
                    db.add(UniverseMembership(universe_id=uid, stock_id=stock_id, added_at=now))
            db.flush()

            # 4. Refresh stock_count + last_synced_at
            for uid in _MANAGED_UNIVERSE_IDS:
                db.execute(text("""
                    UPDATE universes
                    SET stock_count    = (SELECT COUNT(*) FROM universe_memberships WHERE universe_id = :uid),
                        last_synced_at = :now,
                        updated_at     = :now
                    WHERE id = :uid
                """), {"uid": uid, "now": now})

            db.commit()

        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

        # Build summary
        summary: dict[str, int] = {}
        from collections import Counter
        cap_counts: Counter = Counter(r.cap_category for r in stock_map.values())
        universe_counts: Counter = Counter()
        for r in stock_map.values():
            for uid in r.universe_ids:
                universe_counts[uid] += 1

        return {
            "refreshed_at": now.isoformat(),
            "total_stocks": len(stock_map),
            "by_cap_category": dict(cap_counts),
            "universe_counts": dict(universe_counts),
            "fetch_errors": fetch_errors,
        }

    def is_stale(self) -> tuple[bool, int]:
        """Returns (is_stale, age_in_days). age=-1 if never synced."""
        db = get_db()
        try:
            row = db.execute(
                text("SELECT MIN(last_synced_at) FROM universes WHERE id = ANY(:ids)"),
                {"ids": _MANAGED_UNIVERSE_IDS},
            ).fetchone()
            if not row or not row[0]:
                return True, -1
            age = (datetime.now(timezone.utc) - row[0]).days
            return age >= _STALE_DAYS, age
        finally:
            db.close()


nifty_refresh_service = NiftyRefreshService()
