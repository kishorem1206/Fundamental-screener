"""Structured brand extraction — Premium PDF System, Stage B1. Uses
`local_llm_client` (local Llama primary, same client the report-blueprint
narrative pipeline uses — see llama_interpreter.py) rather than `llm_client`
(the concall system's Groq-primary client): this is a single, bounded
extraction pass over one company-description text, not the noisy
multi-utterance transcript work that justified a stronger model there.

Source is CompanySummary.key_points — specifically the FULL, logged-in
version (see screener_client.py's _fetch_full_key_points module docstring)
that actually names individual brands with market share. The free/
anonymous preview is usually too short to mention any brand by name, so
extraction is gated on key_points being reasonably long (see
ingest_company_brands's length check) rather than wasting an LLM call on a
one-sentence stub.

Same numeric-grounding discipline as blueprint_validator.py and
guidance_extraction.py's _validate_item: every market-share % the model
outputs must be a number that literally appears in the source text, or the
whole brand entry is dropped rather than trusted.
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.infrastructure.database.models import CompanyBrand, CompanySummary
from app.llm.client import local_llm_client
from app.logger import logger

_MIN_KEY_POINTS_LEN = 400  # below this, it's almost certainly just the free-preview stub — see module docstring

_BRAND_SYSTEM_RULES = """You are the brand-extraction engine of an equity research system for
Indian public companies. You receive one company's "Key Points" description
(sourced from Screener.in) and must extract ONLY the individual product/
service BRANDS it explicitly names.

STRICT RULES:
1. Extract a brand only if it is named explicitly in the text (a proper noun the company sells under) — never infer a brand from a generic product category.
2. `category` is the product category the brand competes in (e.g. "Fabric Care", "Dishwashing") if the text states or clearly implies it — otherwise null.
3. `ownership` is "owned" or "licensed" ONLY if the text explicitly says so (e.g. "licensed from Henkel", "its own brand") — otherwise null. Never guess.
4. `market_share_pct` must be a number copied verbatim from the text — never estimated, never rounded from a different figure, never invented. If no percentage is given for that specific brand, it is null.
5. `market_share_context` is the short qualifier that number applies to, copied from the text (e.g. "in Kerala", "of liquid dishwash", "in the coil category") — null if the share is stated with no qualifier.
6. `license_expiry` is a date/period ONLY if the text explicitly states when a license ends — otherwise null.
7. Do not list the same brand twice. Do not list the company's own name as a brand.
8. Return ONLY a JSON object matching the exact schema. Never copy instruction or example text into your output — every field is a real value drawn from the text, or null."""

_SCHEMA_HINT = """{"brands": [<0 or more brand objects>]}

Each brand has this exact shape — this is a REAL FILLED EXAMPLE, not a template to copy:
{
  "brand_name": "Ujala",
  "category": "Fabric Care",
  "ownership": "owned",
  "market_share_pct": 84.0,
  "market_share_context": "in fabric whiteners",
  "license_expiry": null
}"""

_NUMBER_RE = re.compile(r"-?\d[\d,]*\.?\d*")


def _text_numbers(text: str) -> set[float]:
    out = set()
    for m in _NUMBER_RE.finditer(text or ""):
        try:
            out.add(round(float(m.group().replace(",", "")), 2))
        except ValueError:
            continue
    return out


def _validate_brand(item: dict, source_numbers: set[float]) -> bool:
    name = item.get("brand_name")
    if not isinstance(name, str) or not name.strip() or len(name) > 60:
        return False

    share = item.get("market_share_pct")
    if share is not None:
        try:
            share_rounded = round(float(share), 2)
        except (TypeError, ValueError):
            return False
        if not any(abs(share_rounded - n) <= 0.05 for n in source_numbers):
            return False  # ungrounded — not a real number from the source text

    ownership = item.get("ownership")
    if ownership is not None and ownership not in ("owned", "licensed"):
        return False

    return True


def extract_brands(key_points: str) -> list[dict]:
    """Never raises — returns [] on any failure."""
    if not key_points or len(key_points) < _MIN_KEY_POINTS_LEN:
        return []

    user_prompt = f"{key_points}\n\nRespond with ONLY a JSON object matching this schema:\n{_SCHEMA_HINT}"
    try:
        result = local_llm_client.chat_json(_BRAND_SYSTEM_RULES, user_prompt)
    except Exception as e:
        logger.warning("brand_extraction: extraction call failed", error=str(e))
        return []

    items = result.get("brands")
    if not isinstance(items, list):
        return []

    source_numbers = _text_numbers(key_points)
    valid = []
    dropped = 0
    for item in items:
        if not isinstance(item, dict) or not _validate_brand(item, source_numbers):
            dropped += 1
            continue
        valid.append(item)
    if dropped:
        logger.info("brand_extraction: validator dropped item(s)", total=len(items), dropped=dropped)
    return valid


def ingest_company_brands(db: Session, company_id: str) -> list[CompanyBrand]:
    """Never raises — logs and returns [] on any failure. Upserts by
    (company_id, brand_name) — re-running is idempotent."""
    try:
        summary = db.query(CompanySummary).filter_by(company_id=company_id).first()
        if summary is None or not summary.key_points:
            return []

        brands = extract_brands(summary.key_points)
        if not brands:
            return []

        now = datetime.now(timezone.utc)
        stored = []
        for b in brands:
            existing = db.query(CompanyBrand).filter_by(company_id=company_id, brand_name=b["brand_name"]).first()
            fields = dict(
                category=b.get("category"), ownership=b.get("ownership"),
                market_share_pct=b.get("market_share_pct"), market_share_context=b.get("market_share_context"),
                license_expiry=b.get("license_expiry"), source_excerpt=summary.key_points[:2000],
            )
            if existing:
                for k, v in fields.items():
                    setattr(existing, k, v)
                existing.retrieved_at = now
                stored.append(existing)
            else:
                row = CompanyBrand(id=str(uuid.uuid4()), company_id=company_id, brand_name=b["brand_name"],
                                    source="SCREENER", retrieved_at=now, **fields)
                db.add(row)
                stored.append(row)
        db.flush()
        logger.info("brand_extraction: brands ingested", company_id=company_id, count=len(stored))
        return stored
    except Exception as e:
        logger.warning("brand_extraction: ingestion failed", company_id=company_id, error=str(e))
        return []
