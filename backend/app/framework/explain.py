"""Plain-language reasoning for a stock's decision (framework section 21's
agent prompt), written by the configured model (gpt-oss) from the stored
numbers only.

The model explains; it does not decide. Its answer is rejected if it names a
different classification or action than the rules produced, and the fixed
text below is used instead — so the page always has an explanation, and never
one that disagrees with the decision. Answers are cached on the stock's row by
a hash of what the model was shown.
"""
from __future__ import annotations

import hashlib
import json

from sqlalchemy.orm import Session

from app.framework.decision import ACTIONS, CLASSIFICATIONS

SYSTEM = (
    "You are an equity analyst writing for a long-term quality portfolio. You explain a decision already made by fixed "
    "rules; you never change it. Use only the numbers given. Do not judge a stock on one score: business quality and "
    "fundamentals first, then momentum, relative strength, technicals and valuation. A strong chart does not repair "
    "weak fundamentals and a cheap price does not repair a weak business. Separate the business reason for any "
    "out-performance from the price strength itself. State the classification and the action exactly as given, in "
    "those words, and do not contradict them. Score changes are points, not percent. Plain English, no jargon, no "
    "investment advice disclaimers. "
    'Answer as JSON: {"summary": "3-5 sentences", "major_risks": ["..."], "what_would_change_it": "1 sentence"}'
)


def pack(row_values: dict, detail: dict, alternative: dict | None) -> dict:
    d = detail.get("decision") or {}
    return {
        "scores": {k: row_values.get(k) for k in ("quality", "fundamental", "business_quality", "quantitative",
                                                    "relative_strength", "technical", "valuation")},
        "valuation_view": row_values.get("valuation_view"), "business_trend": row_values.get("trend"),
        "quality_momentum": {"direction": row_values.get("quality_direction"), "change_12m": row_values.get("quality_change_12m")},
        "sector_rank": d.get("sector_rank"), "decision": {k: d.get(k) for k in ("classification", "action", "size", "matrix", "why")},
        "red_flags": (d.get("gates") or {}).get("red_flags"), "interpretation": d.get("interpretation"),
        "best_same_sector_alternative": alternative and {k: alternative.get(k) for k in ("symbol", "classification", "action", "quality")},
    }


def fallback(p: dict) -> dict:
    d, i = p["decision"], p.get("interpretation") or {}
    parts = [f"{d['classification']}: {d['action'].lower()}" + (f", position size {d['size'].lower()}" if d.get("size") not in (None, "None") else "") + "."]
    parts += [w[0].upper() + w[1:] + "." for w in d.get("why") or []]
    if i.get("strong"):
        parts.append("Strong: " + ", ".join(i["strong"]) + ".")
    if i.get("weak"):
        parts.append("Weak: " + ", ".join(i["weak"]) + ".")
    if i.get("performance"):
        parts.append("The stock is " + i["performance"] + ".")
    return {"summary": " ".join(parts), "major_risks": (p.get("red_flags") or []) + [f"weak {w}" for w in i.get("weak") or []][:3],
            "what_would_change_it": None, "author": "rules"}


_NEGATIONS = ("non-", "non ", "not ", "no longer ", "upgraded to ", "upgrade to ", "become ", "becomes ")


def _consistent(answer: dict, d: dict) -> bool:
    """The summary must name the decision's own classification, and the answer
    must not name another classification, negate this one ("non-investable") or
    talk of moving into the class the stock is already in ("upgraded to investable")."""
    summary = answer.get("summary")
    if not isinstance(summary, str) or len(summary) < 40:
        return False
    text = " ".join([summary, *map(str, answer.get("major_risks") or []), str(answer.get("what_would_change_it") or "")]).lower()
    own = d["classification"].lower()
    if own not in summary.lower():
        return False
    if any(c.lower() in text for c in CLASSIFICATIONS if c != d["classification"]):
        return False
    stems = [own] + [w for w in own.replace("/", " ").split() if len(w) > 4]
    return not any(f"{neg}{w}" in text for w in stems for neg in _NEGATIONS)


def explain(db: Session, row, row_values: dict, alternative: dict | None, use_model: bool = True) -> dict:
    p = pack(row_values, row.detail or {}, alternative)
    if not p["decision"].get("classification"):
        return {"summary": "No decision yet: this stock has no Quality Score.", "author": "rules"}
    key = hashlib.sha256(json.dumps(p, sort_keys=True, default=str).encode()).hexdigest()[:16]
    cached = (row.detail or {}).get("explanation")
    if cached and cached.get("key") == key and (cached.get("author") == "rules" or _consistent(cached, p["decision"])):
        return cached
    answer = None
    if use_model:
        from app.bie.llm_assist import _ask  # validated wrapper: refuses the stand-in model's answers

        raw = _ask(SYSTEM, json.dumps(p, default=str), max_tokens=2500)
        if raw and _consistent(raw, p["decision"]):
            answer = {"summary": raw["summary"], "major_risks": raw.get("major_risks") or [],
                      "what_would_change_it": raw.get("what_would_change_it"), "author": "gpt-oss"}
    answer = answer or fallback(p)
    answer["key"] = key
    row.detail = {**(row.detail or {}), "explanation": answer}
    db.commit()
    return answer
