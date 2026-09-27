"""Blueprint generator — Stage L1. Calls the local-Llama-primary client
(`app/llm/client.py::local_llm_client`) once per modular section
(`app/interpretation/prompts/sections.py`), assembling Summary.md section 9's
Report Blueprint shape: `{report: {company}, sections: [{id, type, title,
content|items}]}`.

Each section call is independently wrapped — matching every other ingestion
path's contract in this app (see e.g. `yfinance_extended_client.py::ingest_all`)
— one section failing (a bad JSON parse, Ollama momentarily down and Groq
also unavailable) never blocks the rest of the blueprint. A failed section
is simply omitted, not filled with placeholder text.
"""
from __future__ import annotations

import json

from app.interpretation.blueprint_validator import validate_blueprint
from app.interpretation.context_builder import build_context
from app.interpretation.prompts.sections import SECTIONS, STRICT_SYSTEM_RULES
from app.llm.client import local_llm_client
from app.logger import logger

# Sections that only make sense with a real sector framework behind them —
# skipped for Generic-sector companies rather than asking the model to
# interpret an empty sector.key_metrics list.
_SECTOR_GATED = {"sector_analysis"}

# Skipped entirely for banks/NBFCs/etc, not just prompted to hedge. Real
# reliability finding, 2026-09-13: even with the supplied data correctly
# showing `interest_coverage.tier: null` and `other_income_dependency.
# flagged: false`, llama3.2:3b still fabricated "weak interest coverage
# tier (WEAK)" and "elevated ... ratio (65.71%, flagged)" for HDFC Bank —
# twice, independently regenerated. The numeric validator can't catch this
# (65.71 is itself a real, grounded number; "WEAK"/"flagged" are words, not
# numbers). Prompt wording alone didn't fix it either. Since the section's
# whole premise (interest coverage as leverage risk, other-income as a
# quality concern) is conceptually inapplicable to a bank/NBFC anyway, not
# just differently thresholded, skipping it outright is more robust than
# continuing to fight the model's hallucination tendency with more prompt
# engineering.
_PNL_FINANCIAL_GATED = {"pnl_earnings_quality"}

# Deep Research System, Stage R3 (2026-09-14) — skipped outright rather than
# asked to interpret an empty list, same discipline as _SECTOR_GATED above.
_SEGMENT_GATED = {"segment_performance"}
_NEWS_GATED = {"recent_developments"}


def _run_section(section_id: str, master: dict) -> dict | None:
    spec = SECTIONS[section_id]
    context = build_context(master, section_id)
    user_prompt = (
        f"{spec['instruction']}\n\n"
        f"Respond with ONLY a JSON object matching this exact shape:\n{spec['schema_hint']}\n\n"
        f"Supplied data:\n{json.dumps(context, indent=2, default=str)}"
    )
    try:
        result = local_llm_client.chat_json(STRICT_SYSTEM_RULES, user_prompt)
    except Exception as e:
        logger.warning("llama_interpreter: section failed", section=section_id, error=str(e))
        return None

    section = {"id": section_id, "type": spec["content_type"], "title": spec["title"]}
    if spec["content_type"] in ("text", "business_model"):
        content = result.get("content")
        if not content:
            return None
        section["content"] = content
        if spec["content_type"] == "business_model" and result.get("key_points"):
            section["key_points"] = result["key_points"]
    else:  # insight_cards / risk_cards
        items = result.get("items")
        if not items:
            return None
        section["items"] = items
    return section


def generate_report_blueprint(master: dict) -> dict:
    """Never raises — a completely empty `sections` list (every call failed)
    is a valid, honest result; callers already fall back to the existing
    `ai_analysis` narrative when this pipeline doesn't produce output."""
    sector_name = (master.get("sector") or {}).get("name")
    pnl_analysis = master.get("pnl_analysis") or {}
    has_pnl_data = bool(pnl_analysis.get("years_of_data"))
    is_financial = bool(pnl_analysis.get("is_financial_sector"))
    has_segments = bool((master.get("business") or {}).get("segments"))
    has_news = bool(master.get("news"))
    sections = []
    for section_id in SECTIONS:
        if section_id in _SECTOR_GATED and (not sector_name or sector_name == "Generic"):
            continue
        if section_id.startswith("pnl_") and not has_pnl_data:
            continue
        if section_id in _PNL_FINANCIAL_GATED and is_financial:
            continue
        if section_id in _SEGMENT_GATED and not has_segments:
            continue
        if section_id in _NEWS_GATED and not has_news:
            continue
        section = _run_section(section_id, master)
        if section is not None:
            sections.append(section)

    raw_blueprint = {
        "report": {"company": (master.get("company") or {}).get("name")},
        "sections": sections,
    }
    validated = validate_blueprint(raw_blueprint, master)

    logger.info("llama_interpreter: blueprint generated",
                company=(master.get("company") or {}).get("name"),
                sections_attempted=len(SECTIONS), sections_generated=len(sections),
                sections_after_validation=len(validated["sections"]))
    return validated
