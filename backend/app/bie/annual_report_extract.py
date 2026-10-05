"""Facts from an annual report PDF that no data file carries reliably: where
the list of group entities sits (and the names and holdings, when the table
can be read), an explicit "no subsidiaries" statement, and the company's own
market-share claims. Everything is located by text search — no LLM — and
cited to the PDF page (the 1-based page of the file, which is not the
printed page number: several reports are laid out as two-page spreads).

Tested on 16 FY2025-26 reports (2026-10-04): the entity list was found in
all 13 that have subsidiaries, through either the statutory statement (Form
AOC-1) or the consolidated-accounts table of entities; ownership percentages
could be read from the table in only some layouts, so those facts are
MEDIUM confidence and absent where the reader fails.
"""
from __future__ import annotations

import io
import re
from datetime import date

import pypdfium2 as pdfium
from sqlalchemy.orm import Session

from app.bie.evidence import clear_document_facts, quote_on_page, record_fact
from app.infrastructure.database.models import Document
from app.logger import logger

_AOC = re.compile(r"\bAOC\s*[-–—]?\s*[1I]\b", re.I)
_AOC_MARKERS = ("share capital", "reserves", "total assets", "turnover", "profit before tax", "% of shareholding",
                "reporting currency", "extent of holding", "provision for tax", "profit after tax")
_NONE = re.compile(
    r"[^.]{0,160}(?:does not|do not|did not) have any (?:subsidiar|associate|joint)[^.]{0,200}\.|"
    r"[^.]{0,160}\b(?:has|have) no subsidiar[^.]{0,200}\.", re.I)
_MARKET_SHARE = re.compile(r"market[\s-]+share", re.I)
_PCT = re.compile(r"(?<![\d.])(\d{1,3}(?:\.\d{1,2})?)\s?%")
_HOLDING_HEADER = re.compile(r"share\s*holding|extent of holding|% of holding", re.I)
_NAME_HEADER = re.compile(r"name of", re.I)
_MAX_CLAIMS = 8


def page_texts(pdf_bytes: bytes) -> list[str]:
    pdf = pdfium.PdfDocument(pdf_bytes)
    try:
        texts = []
        for i in range(len(pdf)):
            textpage = pdf[i].get_textpage()
            texts.append(textpage.get_text_range())
        return texts
    finally:
        pdf.close()


def locate_subsidiary_statement(texts: list[str]) -> list[int]:
    """0-based pages of the statutory subsidiary statement, with its
    continuation pages."""
    lowered = [t.lower() for t in texts]

    def looks_like_statement(i: int) -> bool:
        return sum(m in lowered[i] for m in _AOC_MARKERS) >= 3

    pages: list[int] = []
    for i, text in enumerate(texts):
        if _AOC.search(text) and looks_like_statement(i):
            j = i
            while j < len(texts) and j < i + 60 and (j == i or looks_like_statement(j) or _AOC.search(texts[j])):
                if j not in pages:
                    pages.append(j)
                j += 1
    return sorted(pages)


def locate_entity_table(texts: list[str]) -> list[int]:
    """0-based pages of the consolidated-accounts table that lists every
    entity with its share of net assets and profit."""
    lowered = [t.lower() for t in texts]
    seeds = [i for i, t in enumerate(lowered)
             if "net assets" in t and "share in profit" in t
             and ("consolidated net assets" in t or "schedule iii" in t or "as % of" in t)]
    pages: set[int] = set()
    for i in seeds:
        j = i
        while j < len(texts) and j < i + 40 and (j == i or j in seeds or len(re.findall(r"\(?\d+\.\d{2}\)?", texts[j])) > 60):
            pages.add(j)
            j += 1
    return sorted(pages)


def find_no_subsidiary_statement(texts: list[str]) -> tuple[int, str] | None:
    for i, text in enumerate(texts):
        match = _NONE.search(re.sub(r"\s+", " ", text))
        if match:
            return i, match.group(0).strip()
    return None


def find_market_share_claims(texts: list[str]) -> list[tuple[int, str, list[float]]]:
    """(0-based page, sentence, percentages in it) for sentences that state
    a market share with a number. One entry per distinct sentence."""
    claims: list[tuple[int, str, list[float]]] = []
    seen: set[str] = set()
    for i, text in enumerate(texts):
        if not _MARKET_SHARE.search(text):
            continue
        flat = re.sub(r"\s+", " ", text)
        for sentence in re.split(r"(?<=[.!?])\s+(?=[A-Z“\"(])", flat):
            if len(sentence) > 420 or not _MARKET_SHARE.search(sentence):
                continue
            percentages = [float(p) for p in _PCT.findall(sentence) if float(p) <= 100]
            key = re.sub(r"\W+", "", sentence.lower())[:120]
            if not percentages or key in seen:
                continue
            seen.add(key)
            claims.append((i, sentence.strip(), percentages))
            if len(claims) >= _MAX_CLAIMS:
                return claims
    return claims


def _to_pct(cell) -> float | None:
    match = re.search(r"\d{1,3}(?:\.\d+)?", str(cell or "").replace(",", ""))
    if not match:
        return None
    value = float(match.group(0))
    return value if 0 < value <= 100 else None


def read_holdings(pdf_bytes: bytes, pages: list[int]) -> list[tuple[str, float, int]]:
    """(entity name, % held, 0-based page) rows read from the statement's
    tables. Handles entities laid out down rows or across columns; returns
    nothing for layouts the table reader cannot segment."""
    import pdfplumber

    found: list[tuple[str, float, int]] = []
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for p in pages:
                for table in pdf.pages[p].extract_tables():
                    rows = [[re.sub(r"\s+", " ", str(c or "")).strip() for c in row] for row in table]
                    name_row = next((i for i, r in enumerate(rows) if any(_NAME_HEADER.search(c) for c in r)), None)
                    if name_row is None:
                        continue
                    hold_row = next((i for i, r in enumerate(rows) if any(_HOLDING_HEADER.search(c) for c in r)), None)
                    pairs: list[tuple[str, float | None]] = []
                    if hold_row is not None and hold_row != name_row:  # entities across columns
                        pairs = [(n, _to_pct(h)) for n, h in zip(rows[name_row][1:], rows[hold_row][1:])]
                    else:  # entities down rows
                        header = rows[name_row]
                        name_col = next((j for j, c in enumerate(header) if _NAME_HEADER.search(c)), None)
                        hold_col = next((j for j, c in enumerate(header) if _HOLDING_HEADER.search(c)), None)
                        if name_col is not None and hold_col is not None:
                            pairs = [(r[name_col], _to_pct(r[hold_col])) for r in rows[name_row + 1:] if len(r) > max(name_col, hold_col)]
                    for name, pct in pairs:
                        if pct is not None and len(name) > 3 and re.search(r"[A-Za-z]{3}", name) and not _NAME_HEADER.search(name):
                            found.append((name, pct, p))
    except Exception as e:  # noqa: BLE001 — an unreadable table is an absent fact, not a failed build
        logger.warning("bie: annual-report table read failed", error=str(e))
    return found


_ASSOCIATE_PAGE = re.compile(r"associates?(\s+compan(y|ies))?\s*(and|/|&)\s*joint\s+ventures?", re.I)
_RELATIONSHIP = re.compile(r"^(associate|joint\s+venture)", re.I)


def locate_associate_statement(texts: list[str], statement: list[int]) -> list[int]:
    """0-based pages carrying the associates-and-joint-ventures part of the statement: it follows the
    subsidiaries part, often on a page of its own that does not repeat the form's name."""
    if not statement:
        return []
    candidates = list(range(statement[0], min(statement[-1] + 4, len(texts))))
    return [i for i in candidates if _ASSOCIATE_PAGE.search(texts[i]) and re.search(r"extent of holding|% of holding|shareholding", texts[i], re.I)]


def read_associate_holdings(pdf_bytes: bytes, pages: list[int]) -> list[tuple[str, float, str, float | None, int]]:
    """(entity, % held, 'Associate' or 'Joint Venture', carrying amount in ₹ crore or None, 0-based page) from a
    statement laid out with one entity a column. The row labels are often merged away by the table reader, so
    the rows are recognised by their content: the relationship row, the holding row above it, the amount above that."""
    import pdfplumber

    found = []
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for p in pages:
                for table in pdf.pages[p].extract_tables():
                    rows = [[re.sub(r"\s+", " ", str(c or "")).strip() for c in row] for row in table]
                    name_row = next((i for i, r in enumerate(rows) if r and _NAME_HEADER.search(r[0])), None)
                    rel_row = next((i for i, r in enumerate(rows) if len(r) > 1 and all(_RELATIONSHIP.match(c) for c in r[1:] if c)
                                    and any(r[1:])), None)
                    if name_row is None or rel_row is None or rel_row < name_row + 2:
                        continue
                    holdings = [_to_pct(c) for c in rows[rel_row - 1][1:]]
                    if any(h is None for h in holdings):
                        continue

                    def amount(cell: str) -> float | None:
                        m = re.fullmatch(r"\(?([\d,]+(?:\.\d+)?)\)?", cell)
                        return float(m.group(1).replace(",", "")) if m else None

                    amounts = [amount(c) for c in rows[rel_row - 2][1:]] if rel_row - 2 > name_row else []
                    for k, (name, pct, rel) in enumerate(zip(rows[name_row][1:], holdings, rows[rel_row][1:])):
                        name = re.sub(r"[#*@&^]+$", "", name).strip()
                        if len(name) > 3 and re.search(r"[A-Za-z]{3}", name):
                            found.append((name, pct, "Joint Venture" if rel.lower().startswith("joint") else "Associate",
                                          amounts[k] if k < len(amounts) else None, p))
    except Exception as e:  # noqa: BLE001 — an unreadable table is an absent fact, not a failed build
        logger.warning("bie: associate table read failed", error=str(e))
    return found


def extract_annual_report(db: Session, *, company_id: str, document: Document, content: bytes,
                          fy_end: date | None) -> dict:
    texts = page_texts(content)
    clear_document_facts(db, document)
    summary = {"pages": len(texts), "statement_pages": [], "entities": 0, "no_subsidiaries": False, "market_share_claims": 0}

    def write(**kw):
        return record_fact(db, scope="COMPANY", company_id=company_id, period_type="FY" if fy_end else "NA",
                           period_end=fy_end, document=document, locator_type="PAGE", source_tier=1, replace=False, **kw)

    statement = locate_subsidiary_statement(texts)
    kind = "Subsidiary statement (Form AOC-1)"
    if not statement:
        statement, kind = locate_entity_table(texts), "Table of consolidated entities"
    if statement:
        first = statement[0]
        header = _AOC.search(texts[first])
        quote = header.group(0) if header else "share in profit"
        span = f"{statement[0] + 1}" if len(statement) == 1 else f"{statement[0] + 1}–{statement[-1] + 1}"
        write(fact_type="group_structure", key="entity_list_location", value_text=f"{kind}, PDF pages {span}",
              attributes={"pages": [p + 1 for p in statement], "kind": kind}, nature="REPORTED",
              page=first + 1, quote=quote, extraction_method="PDF_TEXT", confidence="HIGH")
        summary["statement_pages"] = [p + 1 for p in statement]
        for name, pct, page in read_holdings(content, statement):
            if not quote_on_page(name, texts[page]):
                continue  # the table reader's cell text is not on the page as read: do not cite it
            write(fact_type="group_entity", key="relationship", dimension=name[:300],
                  value_text="Listed in the annual report's subsidiary statement",
                  attributes={"shares_held_ratio": round(pct / 100, 6)}, nature="REPORTED",
                  page=page + 1, quote=name, extraction_method="PDF_TABLE", confidence="MEDIUM")
            summary["entities"] += 1
        for name, pct, relationship, carrying, page in read_associate_holdings(content, locate_associate_statement(texts, statement)):
            if not quote_on_page(name, texts[page]):
                continue
            write(fact_type="group_entity", key="relationship", dimension=name[:300], value_text=relationship,
                  attributes={"shares_held_ratio": round(pct / 100, 6), **({"carrying_amount": carrying * 1e7} if carrying is not None else {})},
                  nature="REPORTED", page=page + 1, quote=name, extraction_method="PDF_TABLE", confidence="MEDIUM")
            summary["entities"] += 1
            summary["associates"] = summary.get("associates", 0) + 1
    else:
        none = find_no_subsidiary_statement(texts)
        if none is not None:
            page, quote = none
            write(fact_type="group_structure", key="no_subsidiaries_statement", value_text=quote, nature="REPORTED",
                  page=page + 1, quote=quote, extraction_method="PDF_TEXT", confidence="HIGH")
            summary["no_subsidiaries"] = True

    for page, sentence, percentages in find_market_share_claims(texts):
        write(fact_type="market_share", key="company_claim", dimension=f"p{page + 1}:{sentence[:60]}",
              value_text=sentence, attributes={"percentages": percentages}, nature="COMPANY_CLAIM",
              page=page + 1, quote=sentence, extraction_method="PDF_TEXT", confidence="MEDIUM")
        summary["market_share_claims"] += 1
    return summary
