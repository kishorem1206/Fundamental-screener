"""The steps that let the engine handle a company nobody has tuned it for.

The language model (the one the app is configured with) does two reading
jobs here, and nothing else:

1. it matches a company's reported segments to the exchange's own list of
   basic industries, so each segment gets real peers;
2. it picks operating measures out of the company's presentation or press
   release where no fixed pattern exists for the sector.

It never supplies a number. A segment match is kept only if the industry is
on the exchange's list; a measure is kept only if its quoted words are on the
archived page and the figure is in those words. If the model is unavailable
or answers badly, the step yields nothing and the rule-based paths remain.
"""
from __future__ import annotations

import json
import re

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.bie.evidence import quote_on_page, record_fact
from app.bie.facts import SEGMENT_REVENUE, FactBook
from app.infrastructure.database.models import BieFact, Stock
from app.logger import logger

_SEGMENT_SYSTEM = (
    "You classify the business segments of an Indian listed company. For each segment, choose the ONE entry from the list of "
    "NSE basic industries that best describes the business the segment is in, so that listed companies in that industry would be "
    "its competitors. Use null when the segment is a customer vertical, a geography, a catch-all ('Others', 'Unallocated') or when "
    "nothing on the list fits. Copy the industry name exactly as written in the list. Reply with JSON only: "
    '{"segments": {"<segment label>": "<industry from the list or null>"}}')
_MEASURE_SYSTEM = (
    "You read a page from an Indian listed company's investor presentation or press release and list the OPERATING measures the "
    "company itself states: physical volumes, capacity, utilisation, counts (stores, plants, customers, employees), order book, "
    "average prices or realisations, market share. Do NOT list revenue, profit, EBITDA, margins, EPS, dividends or growth rates of "
    "those. For each measure give the words exactly as printed. Reply with JSON only: "
    '{"measures": [{"label": "<short plain name>", "value": <number as printed, without commas>, "unit": "<unit as printed>", '
    '"period": "<the period or date the figure refers to, as printed, or null>", "quote": "<10 to 120 characters copied exactly '
    'from the text, containing the number>"}]}. At most 8 measures. If there are none, return an empty list.')


UNAVAILABLE = False  # set when the configured model could not be reached (rate limit): the caller can retry later


def _ask(system: str, user: str, max_tokens: int = 2500) -> dict | None:
    """One JSON answer from the configured model, or None. An answer from the small local stand-in model (used when the
    configured one is rate-limited) is not accepted: these are judgement calls it gets wrong, and nothing is better than wrong."""
    global UNAVAILABLE
    try:
        from app.llm.client import LLMClient
        client = LLMClient()
        # Plain mode with room to think: this model's JSON mode returns nothing when its reasoning uses up a small budget.
        raw = client.chat(system, user, max_tokens=max_tokens)
        if client.last_used_fallback:
            UNAVAILABLE = True
            logger.warning("bie: configured language model unavailable (rate limit); step skipped rather than use the stand-in model")
            return None
        match = re.search(r"\{.*\}", raw or "", re.S)
        answer = json.loads(match.group(0)) if match else None
        return answer if isinstance(answer, dict) else None
    except Exception as e:  # noqa: BLE001 — the model is an aid: without it the rule-based paths stand
        if "rate" in str(e).lower() or "429" in str(e):
            UNAVAILABLE = True
        logger.warning("bie: language-model step failed", error=str(e)[:200])
        return None


def classify_segments(db: Session, stock: Stock) -> dict:
    """Store, for each reported business segment, the basic industry the model matched it to (or that it matched none)."""
    book = FactBook(db, stock.id)
    basis = next(iter(book.bases()), None)
    ends = book.period_ends("FY", basis) if basis else []
    if not ends or stock.sector in ("Financial Services", "Information Technology"):
        return {"skipped": "segments are not separate industries for this kind of company"}
    segments = [label for label, facts in book.segments("FY", ends[0], basis).items()
                if SEGMENT_REVENUE in facts and (facts[SEGMENT_REVENUE].attributes or {}).get("is_business_segment", True)
                and float(facts[SEGMENT_REVENUE].value_num or 0) > 0]
    if len(segments) < 2:
        return {"skipped": "fewer than two segments"}
    industries = sorted(name for (name,) in db.query(Stock.basic_industry).filter(
        Stock.is_active.is_(True), Stock.basic_industry.isnot(None)).group_by(Stock.basic_industry).having(func.count() >= 2))
    activities = [f.dimension for f in book.of_type("business_activity")][:8]
    global UNAVAILABLE
    UNAVAILABLE = False
    answer = _ask(_SEGMENT_SYSTEM, json.dumps({"company": stock.company_name, "own_classification": stock.basic_industry,
                                                "what_the_company_says_it_does": activities, "segments": segments,
                                                "nse_basic_industries": industries}, ensure_ascii=False))
    chosen = (answer or {}).get("segments")
    if not isinstance(chosen, dict):
        return {"skipped": "no usable answer from the model; any earlier classification is kept", "model_unavailable": UNAVAILABLE}
    db.query(BieFact).filter(BieFact.company_id == stock.id, BieFact.fact_type == "segment_industry").delete(synchronize_session=False)
    known, kept = set(industries), {}
    for label in segments:
        industry = chosen.get(label)
        industry = industry if isinstance(industry, str) and industry in known else None  # anything not on the exchange's list is dropped
        fact = record_fact(
            db, scope="COMPANY", company_id=stock.id, fact_type="segment_industry", key="matched_basic_industry", dimension=label[:300],
            value_text=industry or "none", nature="ANALYST_ASSUMPTION", extraction_method="LLM_CLASSIFICATION", source_tier=3, confidence="LOW",
            formula="Chosen by the language model from the exchange's list of basic industries, as the industry whose listed companies "
                    "compete with this segment; an answer not on that list is discarded. Peers and multiples for the segment follow from it.",
            replace=False)
        fact.verification_status = "ASSUMPTION"
        kept[label] = industry
    return {"segments": len(segments), "matched": sum(1 for v in kept.values() if v), "mapping": kept}


def stored_segment_industries(db: Session, company_id: str) -> dict[str, str | None] | None:
    """{segment label: industry or None} from the stored classification, or None when none has been made."""
    facts = db.query(BieFact).filter(BieFact.company_id == company_id, BieFact.fact_type == "segment_industry").all()
    return {f.dimension: (None if f.value_text == "none" else f.value_text) for f in facts} if facts else None


def _number_in(value, quote: str) -> bool:
    try:
        target = float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return False
    return any(abs(float(n.replace(",", "")) - target) < 1e-9 for n in re.findall(r"\d[\d,]*(?:\.\d+)?", quote) if n.replace(",", "").replace(".", "").isdigit())


def pick_pages(pages: list[str], limit: int = 2) -> list[int]:
    """The pages most likely to carry operating measures: many figures alongside words like 'highlights' or 'volume'."""
    cue = re.compile(r"highlights?|key\s+(?:metrics|figures|performance)|operational|operating|volumes?|capacity|utili[sz]ation|"
                     r"stores?|customers?|subscribers?|order\s+book|production|market\s+share|realisation", re.I)
    scored = sorted(((len(cue.findall(t)) * min(len(re.findall(r"\d[\d,.]*", t)), 60), i) for i, t in enumerate(pages) if 200 < len(t) < 9000), reverse=True)
    return sorted(i for score, i in scored[:limit] if score > 0)


def read_measures(pages: list[str], company_name: str) -> list[dict]:
    """Operating measures the model found on the best pages, each checked against the page: {label, value, unit, period, quote, page}."""
    out, seen = [], set()
    for page in pick_pages(pages):
        answer = _ask(_MEASURE_SYSTEM, f"Company: {company_name}\n\nPage text:\n{pages[page][:7000]}")
        for item in (answer or {}).get("measures") or []:
            if not isinstance(item, dict):
                continue
            label, quote = str(item.get("label") or "").strip()[:80], str(item.get("quote") or "").strip()
            try:
                value = float(str(item.get("value")).replace(",", ""))
            except (TypeError, ValueError):
                continue
            # Kept only if the quoted words are on the page and the figure is in them.
            if not label or not 10 <= len(quote) <= 160 or not quote_on_page(quote, pages[page]) or not _number_in(value, quote):
                continue
            key = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")[:40]
            if key in seen:
                continue
            seen.add(key)
            out.append({"key": key, "label": label, "value": value, "unit": str(item.get("unit") or "").strip()[:30] or "as stated",
                        "period": (str(item["period"]).strip()[:60] if item.get("period") else None), "quote": quote, "page": page})
    return out
