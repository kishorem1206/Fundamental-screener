"""SEBI enforcement orders: read the listing, match titles to listed
companies, and read the operative part of the orders that name one.

Source: sebi.gov.in → Enforcement → Orders (every order SEBI publishes:
whole-time member and quasi-judicial orders, adjudication orders, settlement
orders, exemption and revocation orders, RTI appeals). The listing is the
page's own AJAX call, `/sebiweb/ajax/home/getnewslistinfo.jsp`, 25 orders a
page, newest first; it answers only inside the listing page's session, with
that page as Referer. SEBI's RSS feed (`sebirss.xml`) holds only the last
thirty items of every kind, so it is not used.

Reading an order: the order page embeds the PDF (`/web/?file=<pdf>`). Long
orders end in annexures, so the pages are read backwards with pdfplumber to
the last one that decides something, and the six pages ending there (and any
after) are kept. Two things are removed first, or the reading is wrong: the running footer (every page repeats the title, so the
company's name is always "present"), and the recital before the operative
part (which quotes earlier orders and other authorities' penalties). The
operative part starts at the first "in exercise of the powers…", "following
directions" or "hereby impose/direct/…". The outcome is then classified:

  DIRECTIONS  restrained / debarred / prohibited — kept out of the market
              or of an activity
  DISGORGEMENT money to be given up or refunded, or impounded
  COMPLIANCE  directions to do something (test related-party deals, appoint a
              valuer), no restraint
  PENALTY     a monetary penalty imposed; `penalty_rs` is the largest amount
  DISPOSED    closed: charges not established, no directions, no penalty
  UNKNOWN     none of these found (scanned order, unusual wording)

Only orders that name a listed company (not as a traded scrip) and are of a
kind that can be adverse are read; the rest keep `outcome` empty.
"""
from __future__ import annotations

import io
import re
import time
from datetime import date, datetime, timedelta, timezone

import httpx
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.infrastructure.database.models import SebiOrder, SebiOrderMatch
from app.logger import logger
from app.risk.names import Matcher, alias, normalise

_BASE = "https://www.sebi.gov.in"
_LISTING = f"{_BASE}/sebiweb/home/HomeAction.do?doListing=yes&sid=2&ssid=9&smid=0"
_AJAX = f"{_BASE}/sebiweb/ajax/home/getnewslistinfo.jsp"
_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
_ROW = re.compile(r"<td>([A-Z][a-z]{2} \d{1,2}, \d{4})</td>\s*<td>\s*<a href='([^']+)'[^>]*?title=\"([^\"]*)\"", re.S)
_PACE = 1.5
READ_KINDS = {"FINAL", "INTERIM", "ORDER", "ADJUDICATION"}

_CLOSED = re.compile(r"without\s+(?:any\s+)?directions?|dispos(?:e|ed)\s+of\s+(?:the\s+)?(?:scn|show\s+cause\s+notice|proceedings)[^.]{0,80}"
                     r"without|no\s+(?:further\s+)?directions?\s+(?:are|is)\s+(?:called|required|warranted|necessary)", re.I)
_DIRECTIONS = re.compile(r"\brestrain|\bdebarr|prohibited\s+from|shall\s+not\s+(?:buy|sell|deal|access|associate|"
                         r"take\s+up|undertake|act\s+as|issue|raise)|"
                         r"cease\s+and\s+desist", re.I)
_DISGORGE = re.compile(r"\bimpound|disgorge|refund\s+(?:the|to)", re.I)
_COMPLIANCE = re.compile(r"hereby\s+direct|following\s+directions|direct\s+as\s+under", re.I)
_PENALTY = re.compile(r"penalt(?:y|ies)\s+of\s+(?:rs|₹|inr)|following\s+(?:monetary\s+)?penalt|hereby\s+impose|"
                      r"imposed?\s+(?:a\s+|with\s+)?(?:monetary\s+)?penalty\s+of|penalty\s+amount", re.I)
_DISPOSED = re.compile(r"dispos(?:e|ed)\s+of|no\s+(?:monetary\s+)?penalty|not\s+a\s+fit\s+case|(?:allegations?|charges?)\s+(?:are|is|have|has)\s+not\s+"
                       r"(?:been\s+)?(?:established|proved|proven|substantiated)|no\s+(?:further\s+)?directions?", re.I)


def kind_of(title: str) -> str:
    t = " ".join(title.lower().split()).strip(" .")
    if re.match(r"appeal\s+no", t):
        return "RTI_APPEAL"
    if re.search(r"notice\s+of\s+demand|recovery\s+certificate|attachment|release\s+order|\brc\s+no", t):
        return "RECOVERY"
    if re.search(r"writ\s+petition|civil\s+appeal|\bsat\b|\bcourt\b|\bvs\.?\s|(?:ltd|limited|ors|others|anr)\.?\s+v\.?\s", t):
        return "COURT"
    if re.search(r"regulation\s+11\b.{0,40}(?:sast|takeover)|(?:sast|takeover).{0,60}regulation\s+11\b", t):
        return "EXEMPTION"
    for word, kind in (("corrigendum", "CORRIGENDUM"), ("addendum", "CORRIGENDUM"), ("settlement", "SETTLEMENT"),
                       ("exemption", "EXEMPTION"), ("revocation", "REVOCATION"), ("adjudication", "ADJUDICATION")):
        if word in t:
            return kind
    if any(w in t for w in ("interim", "ex-parte", "ex parte", "confirmatory")):
        return "INTERIM"
    if "final order" in t:
        return "FINAL"
    if t.startswith("order") or " order " in t or "in the matter of" in t:
        return "ORDER"
    return "OTHER"


class _Sebi:
    def __init__(self):
        self.c = httpx.Client(headers={"User-Agent": _UA}, timeout=60, follow_redirects=True)
        self.c.get(_LISTING)
        self._last = 0.0

    def _wait(self):
        gap = time.monotonic() - self._last
        if gap < _PACE:
            time.sleep(_PACE - gap)
        self._last = time.monotonic()

    def page(self, n: int) -> list[tuple[date, str, str]]:
        body = (f"nextValue={n}&next=n&search=&fromDate=&toDate=&fromYear=&toYear=&deptId=-1&sid=2&ssid=9&smid=0"
                f"&ssidhidden=9&intmid=-1&sText=Enforcement&ssText=Orders&smText=&doDirect={n}")
        headers = {"Referer": _LISTING, "Origin": _BASE, "X-Requested-With": "XMLHttpRequest",
                   "Content-Type": "application/x-www-form-urlencoded"}
        for attempt in range(3):
            self._wait()
            try:
                r = self.c.post(_AJAX, content=body, headers=headers)
                rows = _ROW.findall(r.text)
                if rows or "records" in r.text:
                    return [(datetime.strptime(d, "%b %d, %Y").date(), u.strip(), " ".join(t.split())) for d, u, t in rows]
            except httpx.HTTPError:
                pass
            time.sleep(5 * (attempt + 1))
            self.c.get(_LISTING)  # a fresh session cookie
        raise RuntimeError(f"SEBI listing page {n} did not answer")

    def get(self, url: str) -> httpx.Response:
        self._wait()
        return self.c.get(url)


def ingest(db: Session, since: date, matcher: Matcher | None = None, stop_at_known: bool = True, log=print) -> dict:
    """Read the listing newest first until orders are older than `since` (or,
    with `stop_at_known`, until a whole page is already stored), store them,
    and match each new title to listed companies. Never raises."""
    s = _Sebi()
    matcher = matcher or Matcher.from_db(db)
    known = {u for (u,) in db.query(SebiOrder.url)}
    now = datetime.now(timezone.utc)
    new = matched = pages = 0
    n = 0
    try:
        while True:
            rows = s.page(n)
            pages += 1
            if not rows:
                break
            fresh = [r for r in rows if r[1] not in known and r[0] >= since]
            for d, url, title in fresh:
                db.execute(insert(SebiOrder).values(url=url, order_date=d, title=title, kind=kind_of(title),
                                                    retrieved_at=now).on_conflict_do_nothing())
                known.add(url)
                new += 1
                for m in matcher.find(title):
                    db.execute(insert(SebiOrderMatch).values(order_url=url, stock_id=m.stock_id, role=m.role,
                                                             matched_name=m.name).on_conflict_do_nothing())
                    matched += 1
            db.commit()
            if rows[-1][0] < since or (stop_at_known and not fresh and n > 0):
                break
            n += 1
            if n % 20 == 0:
                log(f"  ...page {n}, back to {rows[-1][0]}, {new} new orders, {matched} company matches")
    except Exception as exc:  # noqa: BLE001 — what was read is kept
        db.rollback()
        logger.warning("sebi_orders: listing stopped", error=str(exc)[:200], page=n)
        return {"pages": pages, "new_orders": new, "matches": matched, "stopped": str(exc)[:200]}
    return {"pages": pages, "new_orders": new, "matches": matched}


def rematch(db: Session, matcher: Matcher | None = None) -> dict:
    """Classify and match every stored title again (after the matcher or the
    universe changes). Keeps what was read from orders already opened."""
    matcher = matcher or Matcher.from_db(db)
    read = {(m.order_url, m.stock_id): m.company_in_operative for m in db.query(SebiOrderMatch)}
    db.query(SebiOrderMatch).delete()
    count = 0
    for o in db.query(SebiOrder):
        o.kind = kind_of(o.title)
        for m in matcher.find(o.title):
            db.add(SebiOrderMatch(order_url=o.url, stock_id=m.stock_id, role=m.role, matched_name=m.name,
                                  company_in_operative=read.get((o.url, m.stock_id))))
            count += 1
    db.commit()
    return {"matches": count}


def operative_text(pdf_bytes: bytes, pages: int = 6) -> str:
    """The six pages ending at the last page that decides something (and what
    follows). Falls back to the last six pages."""
    import pdfplumber

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        n = len(pdf.pages)
        texts: dict[int, str] = {}
        last = n - 1
        for i in range(n - 1, -1, -1):
            texts[i] = pdf.pages[i].extract_text() or ""
            if _ANCHOR.search(" ".join(texts[i].split())):
                last = i
                break
        for i in range(max(0, last - pages + 1), last):
            texts.setdefault(i, pdf.pages[i].extract_text() or "")
        return " ".join(" ".join(texts[i] for i in sorted(texts)).split())


_FOOTER = re.compile(r"(?:order|in\s+the\s+matter)[^.]{0,160}?\s(?:page\s+)?\d+\s+of\s+\d+\b", re.I)
_ANCHOR = re.compile(r"exercise\s+of\s+(?:the\s+)?(?:my\s+)?powers?|following\s+directions|direct\s+as\s+under|"
                     r"hereby\s+(?:impose|direct|order|dispose)|I\s+impose", re.I)
_AMOUNT = re.compile(r"(?:(?:rs\.?|₹|inr)\s*)?([0-9][0-9,]*(?:\.[0-9]+)?)\s*(crores?|cr\.?|lakhs?|lacs?)\b|(?:rs\.?|₹|inr)\s*([0-9][0-9,]*(?:\.[0-9]+)?)", re.I)


def operative_part(text: str, title: str = "") -> str:
    """What the order decides: the footer and the recital removed."""
    t = text
    if title:
        t = re.sub(re.escape(" ".join(title.split())), " ", t, flags=re.I)
    t = _FOOTER.sub(" ", t)
    t = re.sub(r"\bpage\s+\d+\s+of\s+\d+\b|_{3,}", " ", t, flags=re.I)
    m = _ANCHOR.search(t)
    if not m:
        return t[-3000:]
    start = t.rfind(". ", max(0, m.start() - 200), m.start())  # from the start of that sentence
    return t[start + 2 if start >= 0 else m.start():]


def largest_amount(text: str) -> float | None:
    """Largest rupee amount named, in rupees. "15 Crore", "₹2,00,000/-", "25 Lacs"."""
    best = None
    for m in _AMOUNT.finditer(text):
        raw = m.group(1) or m.group(3)
        unit = (m.group(2) or "").lower()
        try:
            v = float(raw.replace(",", ""))
        except ValueError:
            continue
        v *= 1e7 if unit.startswith("cr") else 1e5 if unit.startswith("la") else 1
        best = max(best or 0, v)
    return best


def classify_outcome(text: str) -> tuple[str, str | None]:
    """An order closed "without any directions" is DISPOSED even when its
    recital quotes the earlier interim directions."""
    for label, pattern in (("DISPOSED", _CLOSED), ("DIRECTIONS", _DIRECTIONS), ("DISGORGEMENT", _DISGORGE), ("PENALTY", _PENALTY),
                           ("DISPOSED", _DISPOSED),
                           ("COMPLIANCE", _COMPLIANCE)):
        m = pattern.search(text)
        if m:
            return label, text[max(0, m.start() - 250):m.end() + 250]
    return "UNKNOWN", None


def _pdf_url(s: _Sebi, url: str) -> str | None:
    if url.lower().endswith(".pdf"):
        return url
    page = s.get(url)
    m = re.search(r"file=(https?://[^'\"&]+\.pdf)", page.text, re.I) or re.search(r"['\"](https?://[^'\"]+\.pdf)['\"]", page.text, re.I)
    return m.group(1) if m else None


def read_outcomes(db: Session, months: int = 48, log=print) -> dict:
    """Open the orders that name a listed company and could be adverse; record
    the outcome and whether each matched company is named in the operative
    part. Never raises. An order whose PDF has no readable text is marked
    UNKNOWN; one that could not be downloaded is left for the next run."""
    since = date.today() - timedelta(days=int(months * 30.5))
    todo = (db.query(SebiOrder).join(SebiOrderMatch, SebiOrderMatch.order_url == SebiOrder.url)
            .filter(SebiOrder.read_at.is_(None), SebiOrder.kind.in_(READ_KINDS), SebiOrder.order_date >= since,
                    SebiOrderMatch.role != "SCRIP")
            .distinct().all())
    if not todo:
        return {"read": 0}
    s = _Sebi()
    counts: dict[str, int] = {}
    for i, o in enumerate(todo, 1):
        text = ""
        try:
            o.pdf_url = _pdf_url(s, o.url)
            if o.pdf_url:
                text = operative_text(s.get(o.pdf_url).content)
        except Exception as exc:  # noqa: BLE001 — a network failure is retried on the next run
            logger.warning("sebi_orders: order not read", url=o.url, error=str(exc)[:120])
            db.rollback()
            continue
        part = operative_part(text, o.title) if text else ""
        o.outcome, o.outcome_excerpt = classify_outcome(part) if part else ("UNKNOWN", None)
        o.penalty_rs = largest_amount(part) if o.outcome == "PENALTY" else None
        o.read_at = datetime.now(timezone.utc)
        low = normalise(part)
        for m in db.query(SebiOrderMatch).filter(SebiOrderMatch.order_url == o.url):
            m.company_in_operative = bool(text) and re.search(rf"\b{re.escape(alias(m.matched_name))}\b", low) is not None
        db.commit()
        counts[o.outcome] = counts.get(o.outcome, 0) + 1
        if i % 20 == 0:
            log(f"  ...{i}/{len(todo)} orders read {counts}")
    return {"read": len(todo), **counts}
