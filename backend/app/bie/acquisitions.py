"""Acquisition disclosures filed since the last balance sheet: what was
bought, what it cost, whether it was paid in cash, and whether it has closed.

Listed companies disclose an acquisition to the exchange in a fixed format
(SEBI listing regulation 30): a covering letter and a numbered table with
"Indicative time period for completion", "Consideration - whether cash
consideration or share swap" and "Cost of acquisition". Those three rows are
read from the archived filing; nothing is inferred from the headline.
"""
from __future__ import annotations

import re
from datetime import date

from sqlalchemy.orm import Session

from app.bie.annual_report_extract import page_texts
from app.bie.documents import archive
from app.bie.evidence import clear_document_facts, quote_on_page, record_fact
from app.infrastructure.database.models import BieFact, Stock

_AMOUNT = re.compile(r"(?:₹|`|Rs\.?|INR)\s*([\d,]+(?:\.\d+)?)\s*(crores?|cr\b|lakhs?|lacs?|millions?|billions?)", re.I)
_UNITS = {"cr": 1e7, "la": 1e5, "mi": 1e6, "bi": 1e9}
_NEXT_ITEM = re.compile(r"\n\s*(?:\d{1,2}\.\s|Sl\.\s)")
_DONE = re.compile(r"\b(?:has|have)\s+(?:today\s+)?(?:further\s+)?(?:completed|acquired)\b|\btoday\s+has\s+(?:further\s+)?acquired\b|"
                   r"\bcompleted\s+(?:the\s+)?acquisition\b", re.I)
_NOT_YET = re.compile(r"subject to|within\s+(?:~\s*)?\d|expected to|proposed to|by\s+\w+\s+\d{4}", re.I)
MAX_FILINGS = 10


def target_key(headline: str) -> str:
    """What a filing is about, so an agreement and its later completion can be matched."""
    text = re.sub(r"^.*?informed the exchange (?:about|regarding|that)\s*", "", headline or "", flags=re.I)
    text = re.sub(r"\b(entering into agreements? for|acquisition of|shares of|equity|update[sd]?)\b|[^a-z0-9 ]", " ", text.lower())
    return " ".join(text.split())


def _subject(headline: str | None) -> str:
    return re.sub(r"^.*?informed the exchange (?:about|regarding|that)\s*", "", headline or "", flags=re.I).strip().rstrip(".")


def _row(text: str, starts: str, header_ends: str) -> str | None:
    """The disclosure against one numbered row of the regulation-30 table."""
    head = re.search(starts + r"[\s\S]{0,160}?" + header_ends + r"[ \t]*\n", text, re.I)
    if head is None:
        return None
    body = text[head.end():head.end() + 900]
    cut = _NEXT_ITEM.search(body)
    return (body[:cut.start()] if cut else body).strip()


def read_filing(pages: list[str]) -> dict:
    """{status, consideration, cost (₹), quote, page (0-based)} from one disclosure's text."""
    pages = [p.replace("\r\n", "\n").replace("\r", "\n") for p in pages]
    text = "\n".join(pages)
    timing = _row(text, r"Indicative time period", r"acquisition")
    paid_in = _row(text, r"Consideration\s*[-–—]\s*whether cash", r"details\s+of\s+the\s+same")
    cost_text = _row(text, r"Cost of acquisition", r"(?:are\s+)?acquired")
    letter = pages[0] if pages else ""
    if timing and _NOT_YET.search(timing) and not _DONE.search(timing):
        status = "pending"
    elif _DONE.search(timing or "") or _DONE.search(letter):
        status = "completed"
    else:
        status = "other"
    consideration = None
    if paid_in and not re.match(r"not applicable", paid_in, re.I):
        consideration = "shares" if re.search(r"swap|issue of|allot", paid_in, re.I) and not re.match(r"cash", paid_in, re.I) else "cash"
    # `priced_elsewhere`: the filing has no cost row at all (a bare completion notice), so the agreement it completes holds the price.
    out = {"status": status, "consideration": consideration, "cost": None, "quote": None, "page": 0, "priced_elsewhere": cost_text is None}
    amount = _AMOUNT.search(cost_text or "")
    if amount:
        out["cost"] = float(amount.group(1).replace(",", "")) * _UNITS[amount.group(2)[:2].lower()]
        out["quote"] = amount.group(0)
        out["page"] = next((i for i, p in enumerate(pages) if quote_on_page(amount.group(0), p)), 0)
    else:
        done = _DONE.search(letter) or _DONE.search(text)
        out["quote"] = done.group(0) if done else (timing or "")[:80] or None
        # Cite the page the quoted words are actually on; if none carries them, there is nothing to cite.
        out["page"] = next((i for i, p in enumerate(pages) if out["quote"] and quote_on_page(out["quote"], p)), None)
        if out["page"] is None:
            out["quote"], out["page"] = None, 0
    return out


def ingest_acquisitions(db: Session, nse, stock: Stock, fy_end: date, touch=lambda d: d) -> dict:
    """Archive and read the acquisition disclosures dated after `fy_end`, plus the earlier filing for any deal
    whose completion notice does not restate the price."""
    events = db.query(BieFact).filter(BieFact.company_id == stock.id, BieFact.fact_type == "corporate_event",
                                      BieFact.key == "ACQUISITION").order_by(BieFact.period_end.desc()).all()
    db.query(BieFact).filter(BieFact.company_id == stock.id, BieFact.fact_type == "acquisition").delete(synchronize_session=False)
    queue = [e for e in events if e.period_end and e.period_end > fy_end][:MAX_FILINGS]
    seen, summary = set(), {"filings": 0, "with_cost": 0, "completed": 0, "pending": 0}
    while queue:
        event = queue.pop(0)
        url = (event.attributes or {}).get("filing_url")
        if not url or url in seen:
            continue
        seen.add(url)
        content = nse.fetch(url, timeout=120)
        document = touch(archive(db, company_id=stock.id, source="NSE", document_type="ACQUISITION_FILING", url=url, content=content,
                                 content_type="application/pdf", title=(event.value_text or "Acquisition disclosure")[:300],
                                 period_end=event.period_end, published_at=None))
        if document is None:
            continue
        clear_document_facts(db, document)
        pages = page_texts(content)
        read = read_filing(pages)
        key = target_key(event.value_text or "")
        if not read["quote"] or not key:
            continue  # nothing on the page to cite: the filing stays in the event list only
        record_fact(
            db, scope="COMPANY", company_id=stock.id, fact_type="acquisition", key="disclosure", dimension=event.dimension,
            period_type="INSTANT", period_end=event.period_end, value_num=read["cost"], value_text=(event.value_text or "")[:600],
            unit="INR" if read["cost"] is not None else None,
            attributes={"target": key, "status": read["status"], "consideration": read["consideration"], "filing_url": url,
                        "priced_elsewhere": read["priced_elsewhere"]},
            nature="REPORTED", document=document, locator_type="PAGE", page=read["page"] + 1, quote=read["quote"],
            extraction_method="PDF_TEXT", source_tier=1, confidence="MEDIUM", replace=False)
        summary["filings"] += 1
        summary["with_cost"] += read["cost"] is not None
        summary[read["status"]] = summary.get(read["status"], 0) + 1
        if read["status"] == "completed" and read["priced_elsewhere"] and event.period_end > fy_end:
            # The completion notice does not restate the price: read the agreement it completes.
            queue += [e for e in events if e.period_end < event.period_end and target_key(e.value_text or "") == key][:2]
    return summary


def since_balance_sheet(db: Session, company_id: str, fy_end: date) -> dict:
    """{'paid': [...], 'pending': [...]} for deals disclosed after `fy_end`. A completed cash deal is 'paid' at the
    cost its own filing states, or failing that the cost in the latest earlier filing for the same target."""
    facts = db.query(BieFact).filter(BieFact.company_id == company_id, BieFact.fact_type == "acquisition").order_by(BieFact.period_end).all()
    paid, pending = [], []
    for f in facts:
        a = f.attributes or {}
        if f.period_end <= fy_end:
            continue
        if a.get("status") == "completed" and a.get("consideration") != "shares":
            priced = f if f.value_num is not None else None if not a.get("priced_elsewhere") else next(
                (e for e in reversed(facts) if e.period_end < f.period_end and (e.attributes or {}).get("target") == a.get("target")
                 and e.value_num is not None and (e.attributes or {}).get("consideration") != "shares"), None)
            if priced is not None:
                paid.append({"what": _subject(f.value_text), "date": f.period_end, "cost": float(priced.value_num), "facts": [f] + ([priced] if priced is not f else []),
                             "priced_on": priced.period_end if priced is not f else None})
        elif a.get("status") == "pending":
            closed = any(e.period_end > f.period_end and (e.attributes or {}).get("target") == a.get("target")
                         and (e.attributes or {}).get("status") == "completed" for e in facts)
            if not closed:
                pending.append({"what": _subject(f.value_text), "date": f.period_end, "cost": float(f.value_num) if f.value_num is not None else None,
                                "consideration": a.get("consideration"), "facts": [f]})
    return {"paid": paid, "pending": pending}
