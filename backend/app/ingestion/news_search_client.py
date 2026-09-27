"""Broader news search — Deep Research System, Stage R2. Extends the
existing `company_news` table (already has provider/source/dedup-by-URL,
populated so far only by yfinance_extended_client.py's Yahoo-sourced rows —
a handful of headlines per company) with real, current India-finance
coverage from Google News' RSS search.

**Why Google News RSS, not the 9 named publishers the user's mentor's
report cited**: no API key, free, confirmed live (2026-09-14, Jyothy Labs)
to return real, dated, current articles from real outlets (Value Research,
Univest, etc.) — broader and more current than Yahoo's own aggregation,
and it generalizes to any company by name rather than hand-building N
fragile per-publisher scrapers (several of the mentor's 9 sources are
partially paywalled anyway — a broad search surfaces whichever outlets
currently have free coverage).

Article URLs come back as Google's redirect wrapper
(`news.google.com/rss/articles/...`), not the publisher's own URL — normal
for RSS consumers of this feed; a real browser follows the redirect fine,
so `NewsSection.tsx`'s `<a href>` needs no special handling.

Reuses `yfinance_extended_client.py`'s `_is_relevant_news` filter so a
loosely-matched search result (e.g. a same-named person, a generic
industry piece) gets the same relevance bar as the Yahoo-sourced rows.
"""
from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import requests
from sqlalchemy.orm import Session

from app.infrastructure.database.models import CompanyNews
from app.ingestion.yfinance_extended_client import _is_relevant_news
from app.logger import logger

SOURCE = "GOOGLE_NEWS"
_RSS_URL = "https://news.google.com/rss/search"


def search_news(company_name: str, limit: int = 15) -> list[dict]:
    """Never raises — returns [] on any failure."""
    try:
        resp = requests.get(
            _RSS_URL,
            params={"q": f'"{company_name}" stock India', "hl": "en-IN", "gl": "IN", "ceid": "IN:en"},
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
    except Exception as e:
        logger.warning("news_search_client: RSS fetch failed", company_name=company_name, error=str(e))
        return []

    items: list[dict] = []
    for item in root.findall(".//item")[:limit]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        if not title or not link:
            continue
        source_el = item.find("source")
        publisher = source_el.text.strip() if source_el is not None and source_el.text else None
        published_at = None
        pub_date_raw = item.findtext("pubDate")
        if pub_date_raw:
            try:
                published_at = parsedate_to_datetime(pub_date_raw)
            except (ValueError, TypeError):
                pass
        items.append({"title": title, "url": link, "publisher": publisher, "published_at": published_at})
    return items


def ingest_news_search(db: Session, company_id: str, company_name: str, symbol: str | None = None) -> int:
    """Never raises — logs and returns 0 on any failure, matching every
    other ingestion module's convention here."""
    try:
        items = search_news(company_name)
        if not items:
            return 0

        now = datetime.now(timezone.utc)
        stored = 0
        skipped_irrelevant = 0
        for item in items:
            if not _is_relevant_news(item["title"], None, symbol or "", company_name):
                skipped_irrelevant += 1
                continue
            existing = db.query(CompanyNews).filter_by(company_id=company_id, url=item["url"]).first()
            if existing:
                continue
            db.add(CompanyNews(
                id=str(uuid.uuid4()), company_id=company_id, headline=item["title"],
                summary=None, provider=item["publisher"], url=item["url"],
                published_at=item["published_at"], source=SOURCE, retrieved_at=now,
            ))
            stored += 1
        db.flush()
        if stored or skipped_irrelevant:
            logger.info("news_search_client: news ingested", company_name=company_name,
                        stored=stored, skipped_irrelevant=skipped_irrelevant)
        return stored
    except Exception as e:
        logger.warning("news_search_client: ingestion failed", company_name=company_name, error=str(e))
        return 0
