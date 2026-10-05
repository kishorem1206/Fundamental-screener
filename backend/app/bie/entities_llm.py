"""Phase 2 — group entities read by the LLM from the located annual-report
pages, for layouts the table reader cannot segment. The model only
transcribes: a name is kept only if it appears on the cited page, and a
holding only if that number is printed on the same page.
"""
from __future__ import annotations

import re

from sqlalchemy.orm import Session

from app.bie.annual_report_extract import page_texts
from app.bie.documents import content_of
from app.bie.evidence import quote_on_page, record_fact
from app.infrastructure.database.models import BieFact, Document
from app.logger import logger

_SYSTEM = ("You transcribe tables from Indian annual reports. Return JSON only: "
           '{"entities":[{"name":"<legal entity name exactly as printed>","relationship":"Subsidiary|Associate|Joint venture",'
           '"held_pct":<number or null>}]}. List only subsidiaries, associates and joint ventures of the reporting company '
           "that appear in the text. Never invent a name or a percentage; use null when the holding is not printed.")
_MAX_PAGES = 8


def read_entities(db: Session, company_id: str) -> dict:
    if db.query(BieFact.id).filter(BieFact.company_id == company_id, BieFact.fact_type == "group_entity").first():
        return {"skipped": "entities already on file"}
    location = db.query(BieFact).filter(BieFact.company_id == company_id, BieFact.key == "entity_list_location").first()
    if location is None:
        return {"skipped": "no entity list located"}
    document = db.get(Document, location.document_id)
    content = content_of(document) if document else None
    if content is None:
        return {"skipped": "archived report unavailable"}
    from app.llm.client import LLMClient
    client, texts = LLMClient(), page_texts(content)
    written, seen = 0, set()
    # Only the statutory subsidiary statement prints ownership; the consolidated entity table's
    # percentages are shares of net assets and profit, so no holding is taken from it.
    has_holdings = "AOC" in ((location.attributes or {}).get("kind") or "")
    for page in (location.attributes or {}).get("pages", [])[:_MAX_PAGES]:
        text = texts[page - 1]
        try:
            result = client.chat_json(_SYSTEM, text[:14000])
        except Exception as e:  # noqa: BLE001
            logger.warning("bie: entity read failed", page=page, error=str(e))
            continue
        for item in (result or {}).get("entities") or []:
            name = re.sub(r"\s+", " ", str(item.get("name") or "")).strip()
            if len(name) < 5 or name.lower() in seen or not quote_on_page(name, text):
                continue
            held = item.get("held_pct")
            if not has_holdings or not isinstance(held, (int, float)) or not 0 < held <= 100 or not re.search(rf"(?<![\d.]){re.escape(f'{held:g}')}(?:\.0+)?(?![\d])", text):
                held = None
            seen.add(name.lower())
            record_fact(
                db, scope="COMPANY", company_id=company_id, fact_type="group_entity", key="relationship", dimension=name[:300],
                value_text=str(item.get("relationship") or "Listed in the annual report's entity table"),
                attributes={"shares_held_ratio": round(held / 100, 6) if held is not None else None},
                period_type=location.period_type, period_end=location.period_end, nature="REPORTED", document=document,
                locator_type="PAGE", page=page, quote=name, extraction_method="LLM_READ_QUOTE_CHECKED", source_tier=1,
                confidence="MEDIUM", replace=False,
            )
            written += 1
    return {"facts": written, "document": document}
