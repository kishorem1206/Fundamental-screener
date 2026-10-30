"""Headlines from publishers' RSS feeds, matched to listed companies.

Sits next to the per-company Google News search (`news_search_client.py`), which
runs only when a company is analysed: this reads the whole market. A headline
that names a listed company also gets a `company_news` row, so it reaches the
stock's News tab and the report with no other change. Feeds hold about the last
day, so run this at least daily.

Moneycontrol's RSS feeds stopped in April 2024 and PIB's serve Hindi titles, so
neither is read.
"""
from __future__ import annotations

import html
import re
import uuid
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import httpx
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.infrastructure.database.models import CompanyNews, MarketNews, Stock
from app.logger import logger
from app.risk.names import Matcher

FEEDS = [
    ("Economic Times", "https://economictimes.indiatimes.com/markets/stocks/news/rssfeeds/2146842.cms"),
    ("Economic Times", "https://economictimes.indiatimes.com/news/company/corporate-trends/rssfeeds/13357270.cms"),
    ("Mint", "https://www.livemint.com/rss/markets"),
    ("Mint", "https://www.livemint.com/rss/companies"),
]
_UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126 Safari/537.36"}
_SOURCE = "PUBLISHER_RSS"


def _field(item: str, tag: str) -> str | None:
    m = re.search(rf"<{tag}\b[^>]*>(.*?)</{tag}>", item, re.S)
    if not m:
        return None
    text = re.sub(r"^\s*<!\[CDATA\[|\]\]>\s*$", "", m.group(1).strip())
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", text)).split()) or None


def parse_rss(xml: str) -> list[dict]:
    out = []
    for item in re.findall(r"<item\b.*?</item>", xml, re.S):
        title, link = _field(item, "title"), _field(item, "link")
        if not title or not link:
            continue
        when = None
        try:
            when = parsedate_to_datetime(_field(item, "pubDate") or "")
        except (TypeError, ValueError):
            pass
        out.append({"headline": title, "url": link, "summary": (_field(item, "description") or "")[:500] or None, "published_at": when})
    return out


def ingest(db: Session) -> dict:
    """Never raises: one feed down does not stop the others."""
    matcher = Matcher.from_db(db)
    symbols = {s.id: s.symbol for s in db.query(Stock).filter(Stock.is_active.is_(True))}
    now = datetime.now(timezone.utc)
    new = matched = failed = 0
    for publisher, url in FEEDS:
        try:
            r = httpx.get(url, headers=_UA, timeout=30, follow_redirects=True)
            r.raise_for_status()
            items = parse_rss(r.text)
        except Exception as exc:  # noqa: BLE001
            logger.warning("news_feeds: feed not read", url=url, error=str(exc)[:120])
            failed += 1
            continue
        for item in items:
            found = matcher.find_news(item["headline"])
            done = db.execute(insert(MarketNews).values(
                **item, publisher=publisher, symbols=[symbols[m.stock_id] for m in found if m.stock_id in symbols], retrieved_at=now
            ).on_conflict_do_nothing()).rowcount
            new += done
            if not done:
                continue
            for m in found:
                db.execute(insert(CompanyNews).values(
                    id=str(uuid.uuid4()), company_id=m.stock_id, headline=item["headline"], summary=item["summary"], provider=publisher,
                    url=item["url"], published_at=item["published_at"], source=_SOURCE, retrieved_at=now,
                ).on_conflict_do_nothing())
                matched += 1
        db.commit()
    return {"new_headlines": new, "company_matches": matched, "feeds_failed": failed}


def latest(db: Session, limit: int = 15) -> list[dict]:
    rows = db.query(MarketNews).order_by(MarketNews.published_at.desc().nullslast()).limit(limit).all()
    return [{"headline": r.headline, "url": r.url, "publisher": r.publisher, "symbols": r.symbols or [],
             "published_at": r.published_at.isoformat() if r.published_at else None} for r in rows]
