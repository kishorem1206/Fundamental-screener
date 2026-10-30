"""Credit ratings from the letters companies file with NSE.

Source: NSE corporate announcements (`/api/corporate-announcements`), subject
"Credit Rating". The announcement itself says only that a rating letter was
filed; the PDF attached is read (first four pages) by `rating_text.parse`.
One NSE query covers every company for a month (about 150 rating letters a
month market-wide), so the whole universe is read month by month rather than
symbol by symbol.

Shown in the full analysis report only: credit ratings feed no score, gate or
classification (user's decision, 2026-10-30).
"""
from __future__ import annotations

import io
from datetime import date, datetime, timedelta, timezone
from urllib.parse import quote

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.infrastructure.database.models import CreditRating, Stock
from app.logger import logger
from app.risk.rating_text import parse

_FIELDS = ("agency", "instrument", "rating", "short_term", "outlook", "action", "previous_rating",
           "previous_outlook", "rationale_url", "excerpt", "parsed")


def letter_text(pdf_bytes: bytes, pages: int = 4) -> str:
    import pdfplumber

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        return "\n".join((p.extract_text() or "") for p in pdf.pages[:pages])


def _store(db: Session, nse, stock_id: str, item: dict) -> bool:
    url = item["attchmntFile"]
    try:
        text = letter_text(nse.fetch(url))
    except Exception as exc:  # noqa: BLE001 — a scanned or broken PDF is stored unparsed
        logger.warning("credit_ratings: letter not read", url=url, error=str(exc)[:120])
        text = ""
    p = parse(text) if text else {"parsed": False}
    try:
        when = datetime.strptime(item["an_dt"], "%d-%b-%Y %H:%M:%S").date()
    except (KeyError, ValueError):
        when = date.today()
    row = {"filing_url": url, "stock_id": stock_id, "announced_on": when, "retrieved_at": datetime.now(timezone.utc),
           **{k: p.get(k) for k in _FIELDS}}
    row["parsed"] = bool(row["parsed"])
    stmt = insert(CreditRating).values(**row)
    db.execute(stmt.on_conflict_do_update(index_elements=["filing_url"], set_={k: stmt.excluded[k] for k in _FIELDS}))
    return row["parsed"]


def _is_rating(item: dict) -> bool:
    return (item.get("desc") or "").strip().lower() == "credit rating" and bool(item.get("attchmntFile"))


def ingest(db: Session, start: date, end: date | None = None, log=print) -> dict:
    """Every rating letter filed by an active stock between `start` and `end`,
    month by month. Letters already stored are skipped. Never raises."""
    from app.bie.nse_filings import NseFilings

    end = end or date.today()
    nse = NseFilings(pace=1.0)
    ids = {s.symbol: s.id for s in db.query(Stock).filter(Stock.is_active.is_(True), Stock.exchange == "NSE")}
    known = {u for (u,) in db.query(CreditRating.filing_url)}
    stored = parsed = 0
    lo = start
    while lo <= end:
        hi = min(end, (lo.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1))
        try:
            rows = nse._json(f"corporate-announcements?index=equities&from_date={lo:%d-%m-%Y}&to_date={hi:%d-%m-%Y}") or []
        except Exception as exc:  # noqa: BLE001
            log(f"  {lo:%b %Y}: NSE did not answer ({str(exc)[:80]})")
            rows = []
        todo = [r for r in rows if _is_rating(r) and r.get("symbol") in ids and r["attchmntFile"] not in known]
        for r in todo:
            parsed += _store(db, nse, ids[r["symbol"]], r)
            known.add(r["attchmntFile"])
            stored += 1
            if stored % 10 == 0:
                db.commit()
        db.commit()
        log(f"  {lo:%b %Y}: {len(todo)} letters ({stored} stored so far, {parsed} with a rating read)")
        lo = hi + timedelta(days=1)
    return {"letters": stored, "parsed": parsed}


def reparse(db: Session, workers: int = 4, log=print) -> dict:
    """Read every stored letter again (after the parser changes). NSE's
    archive is a plain file host, so this needs no session and no pacing."""
    from concurrent.futures import ThreadPoolExecutor

    import httpx

    rows = db.query(CreditRating).all()
    client = httpx.Client(headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36"},
                          timeout=60, follow_redirects=True)

    def read(url: str) -> dict | None:
        for attempt in range(3):
            try:
                r = client.get(url)
                if r.status_code == 200:
                    return parse(letter_text(r.content))
            except Exception:  # noqa: BLE001
                pass
        return None

    failed = changed = 0
    with ThreadPoolExecutor(workers) as pool:
        for i, (row, p) in enumerate(zip(rows, pool.map(read, [r.filing_url for r in rows])), 1):
            if p is None:
                failed += 1
                continue
            before = (row.rating, row.action, row.outlook)
            for k in _FIELDS:
                setattr(row, k, bool(p.get(k)) if k == "parsed" else p.get(k))
            changed += before != (row.rating, row.action, row.outlook)
            if i % 200 == 0:
                db.commit()
                log(f"  ...{i}/{len(rows)} letters, {changed} changed, {failed} not fetched")
    db.commit()
    return {"letters": len(rows), "changed": changed, "not_fetched": failed}


def ingest_symbol(db: Session, stock: Stock, months: int = 24) -> dict:
    """One company's letters (used by tests and on demand). Never raises."""
    from app.bie.nse_filings import NseFilings

    nse = NseFilings()
    today = date.today()
    since = today - timedelta(days=int(months * 30.5))
    try:
        rows = nse._json(f"corporate-announcements?index=equities&symbol={quote(stock.symbol)}"
                         f"&from_date={since:%d-%m-%Y}&to_date={today:%d-%m-%Y}") or []
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)[:120]}
    known = {u for (u,) in db.query(CreditRating.filing_url).filter(CreditRating.stock_id == stock.id)}
    stored = parsed = 0
    for r in rows:
        if _is_rating(r) and r["attchmntFile"] not in known:
            parsed += _store(db, nse, stock.id, r)
            stored += 1
    db.commit()
    return {"letters": stored, "parsed": parsed}
