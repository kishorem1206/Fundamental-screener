"""The write gate for `bie_facts`, and verification of what was written.

A fact that came from a document must name the archived document, a direct
http(s) URL and where in the document it sits (a PDF page plus the quoted
text, or a data-file element). A calculated fact must name the facts it was
computed from. Anything else raises `EvidenceError` — callers are expected
to skip the fact, not to weaken the citation.
"""
from __future__ import annotations

import re
import uuid
from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.infrastructure.database.models import BieFact, Document

SCOPES = {"COMPANY", "SECTOR", "MACRO"}
DOCUMENT_NATURES = {"REPORTED", "COMPANY_CLAIM", "MANAGEMENT_GUIDANCE", "THIRD_PARTY"}
NATURES = DOCUMENT_NATURES | {"CALCULATED", "ANALYST_ASSUMPTION"}
LOCATOR_TYPES = {"PAGE", "XBRL", "JSON", "TABLE"}
CONFIDENCES = {"HIGH", "MEDIUM", "LOW"}


class EvidenceError(ValueError):
    """The fact lacks a usable source and was not written."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise EvidenceError(message)


def record_fact(
    db: Session,
    *,
    scope: str,
    fact_type: str,
    key: str,
    nature: str,
    extraction_method: str,
    source_tier: int,
    confidence: str,
    company_id: str | None = None,
    sector: str | None = None,
    dimension: str = "",
    period_type: str = "NA",
    period_start: date | None = None,
    period_end: date | None = None,
    statement_type: str = "NA",
    value_num: float | None = None,
    value_text: str | None = None,
    unit: str | None = None,
    attributes: dict | None = None,
    document: Document | None = None,
    locator_type: str = "NONE",
    page: int | None = None,
    locator: str | None = None,
    quote: str | None = None,
    inputs: list[str] | None = None,
    formula: str | None = None,
    replace: bool = True,
) -> BieFact:
    """Insert one fact, replacing any earlier fact with the same identity
    from the same document (so a re-run is idempotent). An extractor that
    has already cleared a document's facts with `clear_document_facts`
    passes `replace=False` to skip the per-fact lookup. Raises
    `EvidenceError` if the source requirements are not met."""
    _require(scope in SCOPES, f"unknown scope {scope!r}")
    _require(nature in NATURES, f"unknown nature {nature!r}")
    _require(confidence in CONFIDENCES, f"unknown confidence {confidence!r}")
    _require(scope != "COMPANY" or bool(company_id), "a COMPANY fact needs company_id")
    _require(scope != "SECTOR" or bool(sector), "a SECTOR fact needs sector")
    _require(value_num is not None or bool(value_text), "a fact needs a value")

    source_url = None
    if nature in DOCUMENT_NATURES:
        _require(document is not None, "a document-sourced fact needs an archived document")
        _require(bool(document.sha256) and bool(document.storage_key), "the document is not archived")
        _require(bool(document.url) and re.match(r"https?://", document.url) is not None,
                 "the document has no direct http(s) URL")
        _require(locator_type in LOCATOR_TYPES, f"a document-sourced fact needs a locator, got {locator_type!r}")
        if locator_type == "PAGE":
            _require(page is not None and page >= 1, "a PAGE locator needs a 1-based page number")
            _require(bool(quote), "a PAGE locator needs the quoted source text")
        else:
            _require(bool(locator), f"a {locator_type} locator needs the element or path it points to")
        source_url = document.url
    elif nature == "CALCULATED":
        _require(bool(inputs), "a CALCULATED fact needs the ids of its input facts")
        _require(bool(formula), "a CALCULATED fact needs its formula")
        found = db.query(BieFact.id).filter(BieFact.id.in_(inputs)).count()
        _require(found == len(set(inputs)), "a CALCULATED fact names input facts that do not exist")
        locator_type = "NONE"
    else:  # ANALYST_ASSUMPTION
        _require(bool(formula), "an ANALYST_ASSUMPTION needs its rationale in `formula`")
        locator_type = "NONE"

    document_id = document.id if document is not None else None
    if replace:
        same = db.query(BieFact).filter(
            BieFact.scope == scope, BieFact.company_id == company_id, BieFact.sector == sector,
            BieFact.fact_type == fact_type, BieFact.key == key, BieFact.dimension == dimension,
            BieFact.period_type == period_type, BieFact.period_end == period_end,
            BieFact.statement_type == statement_type, BieFact.nature == nature,
        )
        if document_id is not None:
            same = same.filter(BieFact.document_id == document_id)
        same.delete(synchronize_session=False)

    fact = BieFact(
        id=str(uuid.uuid4()), scope=scope, company_id=company_id, sector=sector,
        fact_type=fact_type, key=key, dimension=dimension, period_type=period_type,
        period_start=period_start, period_end=period_end, statement_type=statement_type,
        value_num=value_num, value_text=value_text, unit=unit, attributes=attributes,
        nature=nature, document_id=document_id, source_url=source_url,
        locator_type=locator_type, page=page, locator=locator, quote=quote,
        extraction_method=extraction_method, source_tier=source_tier, confidence=confidence,
        inputs=list(inputs) if inputs else None, formula=formula,
        verification_status="UNVERIFIED", created_at=datetime.now(timezone.utc),
    )
    db.add(fact)
    db.flush()
    return fact


def clear_document_facts(db: Session, document: Document) -> None:
    """Drop every fact read from `document`, ahead of re-extracting it."""
    db.query(BieFact).filter(BieFact.document_id == document.id).delete(synchronize_session=False)


def _squash(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def quote_on_page(quote: str, page_text: str) -> bool:
    """True if `quote` appears in `page_text`, ignoring whitespace and case."""
    return bool(quote) and _squash(quote) in _squash(page_text)


def verify_fact(db: Session, fact: BieFact, *, xbrl_lookup=None, page_text=None, raw_text=None) -> str:
    """Re-check one fact against its archived source and store the outcome.

    The caller supplies whichever view of the archived document the locator
    needs: `xbrl_lookup(element, context_id) -> str | None`, `page_text(page)
    -> str`, or `raw_text` (the whole decoded file) for JSON/TABLE locators.
    Returns the new status: VERIFIED, FAILED or UNVERIFIED (nothing to check
    against)."""
    status = "UNVERIFIED"
    if fact.nature == "CALCULATED":
        inputs = db.query(BieFact).filter(BieFact.id.in_(fact.inputs or [])).all()
        ok = len(inputs) == len(set(fact.inputs or [])) and all(i.verification_status in ("VERIFIED", "ASSUMPTION") for i in inputs)
        status = "VERIFIED" if ok else "FAILED"
    elif fact.locator_type == "XBRL" and xbrl_lookup is not None:
        element, _, context_id = (fact.locator or "").partition("@")
        found = xbrl_lookup(element, context_id)
        status = "VERIFIED" if found is not None and found.strip() == (fact.quote or "").strip() else "FAILED"
    elif fact.locator_type == "PAGE" and page_text is not None:
        status = "VERIFIED" if quote_on_page(fact.quote or "", page_text(fact.page)) else "FAILED"
    elif fact.locator_type in ("JSON", "TABLE") and raw_text is not None:
        status = "VERIFIED" if quote_on_page(fact.quote or "", raw_text) else "FAILED"
    if fact.nature == "ANALYST_ASSUMPTION":
        status = "ASSUMPTION"  # nothing to verify against: it is this app's stated choice
    fact.verification_status = status
    fact.verified_at = datetime.now(timezone.utc)
    return status
