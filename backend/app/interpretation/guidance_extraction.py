"""Management guidance extraction — Concall Intelligence System, Stage C3.
Uses `llm_client` (Groq gpt-oss-20b primary, local Llama fallback on rate
limit) rather than `local_llm_client` (the inverse, local-primary) that the
rest of this session's interpretation pipeline uses — a deliberate,
per-module choice, not a change to the P&L/report-narrative pipeline's own
client. Structured extraction from noisy transcript text needs a stronger
model than 3B: the first real run on local Llama alone produced schema-hint
placeholder text leaking verbatim into output fields and self-contradictory
items (see the validator below, and ARCHITECTURE.md's dated entry, for what
was actually found) — gpt-oss-20b as primary here is a direct response to
that, not a preference applied blindly.

A deterministic Python engine computes the UPGRADED/DOWNGRADED/REITERATED/
NEW status by comparing numeric targets — never the LLM, regardless of
which one is primary, same "Llama never does the comparison" principle
already applied twice in the P&L system (profit-vs-sales direction,
EPS-vs-profit direction), both times because leaving a numeric comparison
to a model — even a strong one — produced real, confirmed hallucinations
there too.

Restricted to management-role utterances by construction — the caller
(`extract_guidance_for_transcript`) only ever passes CEO/CFO/Deputy MD/COO/
Chairman/Management utterances to the LLM, never Analyst or Moderator. An
analyst's question becoming "guidance" is structurally impossible here, not
just prompted against.
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.infrastructure.database.models import (
    ConcallTopicSentiment, ConcallTranscript, ConcallUtterance, ManagementGuidance,
)
from app.llm.client import llm_client
from app.logger import logger

_MANAGEMENT_ROLES = {"CEO", "CFO", "Deputy MD", "COO", "Chairman", "Management"}

# Doc section 53's own cost-optimization recommendation: only send chunks
# that look guidance/outlook-relevant to the LLM, not every management
# utterance (most are just answering unrelated procedural questions).
_RELEVANCE_KEYWORDS = (
    "guidance", "outlook", "expect", "anticipate", "confident", "target",
    "margin", "growth", "capex", "order", "demand", "pricing", "expansion",
    "forecast", "aim", "plan to", "going forward", "next year", "full year",
)

# Metrics where a LOWER target is the positive direction — everything else
# defaults to "higher is better". Deliberately small and explicit rather
# than guessed per-metric.
_LOWER_IS_BETTER_METRICS = {"debt", "net_debt", "attrition", "cost", "npa", "credit_cost"}

# Batched (not one call per utterance): the original per-utterance design
# made ~14-15 sequential Groq calls per transcript, each re-sending the full
# system prompt + schema as fixed overhead — live-tested 2026-09-14 and
# confirmed it blows straight through Groq's 8000 TPM limit on gpt-oss-20b,
# so nearly every call fell back to local Llama anyway, defeating the point
# of using the stronger model. Batching amortizes that fixed overhead across
# several utterances per call, cutting call count ~4x.
_BATCH_SIZE = 4

# Real bug found in Stage C4 (2026-09-14): with `metric` left as freeform
# LLM-generated snake_case, the two real HDFC transcripts extracted so far
# have ZERO metric-name overlap — the model invents a fresh phrasing every
# call ("cost_of_funds" vs "borrowing_mix" vs "nominal_rate" for what may be
# the same underlying topic), so `_find_previous_guidance`'s exact-match
# lookup can never find a prior quarter's guidance for the same thing in
# practice, and every row silently stays status="NEW" forever — the entire
# point of Stage C3's UPGRADED/DOWNGRADED/REITERATED engine. A controlled
# vocabulary (doc section 14, adapted — bank-specific metrics added since
# banks don't report EBITDA) fixes this: the model must pick from this list,
# not invent new phrasings, so the same real-world topic gets the same
# `metric` string across quarters and cross-quarter comparison actually has
# a chance to fire.
_CANONICAL_METRICS = (
    "revenue", "revenue_growth", "ebitda", "ebitda_margin", "ebit", "ebit_margin",
    "pat", "pat_margin", "eps", "roe", "roce", "fcf", "fcf_to_pat",
    "nim", "casa_ratio", "credit_growth", "deposit_growth", "gnpa", "nnpa",
    "provision_coverage", "cost_to_income", "capital_adequacy",
    "retail_mix", "borrowing_mix", "cost_of_funds", "asset_quality",
    "volume", "utilization", "capacity", "production", "store_count", "customers",
    "headcount", "attrition", "order_intake", "order_book", "pipeline",
    "capex", "debt", "net_debt", "dividend", "buyback", "ma",
    "demand", "pricing", "market_share", "geography", "segments",
    "product_launch", "expansion", "new_capacity", "other",
)

_GUIDANCE_SYSTEM_RULES = """You are the extraction engine of a management-commentary intelligence system
for Indian equity research, analyzing several utterances from a company's
CEO/CFO/management during one earnings call. Each utterance is numbered and
completely independent — never mix information from one utterance into an
item tagged with a different utterance's number.

Your job is to identify GENUINELY FORWARD-LOOKING guidance or outlook
statements — nothing else.

STRICT RULES:
1. Use ONLY the text of the utterance an item is tagged with. Do not use outside knowledge of this company, and do not borrow facts from a different numbered utterance.
2. Never invent a number, period, or target not explicitly stated in that utterance's text. Every number you output must be copied verbatim from it, never estimated or rounded from something else.
3. A CURRENT or HISTORICAL figure mentioned for context ("our coverage ratio is currently 66%", "last year we grew 5%") is NOT guidance — it describes the past or present, not a forward commitment. Do not extract it.
4. A conditional statement ("if demand improves, margins could recover") is NOT firm guidance — mark it conditional=true, certainty="conditional".
5. A qualitative statement ("demand remains strong") with no number is guidance_type="qualitative" and target_low/target_high/target_value must all be null — never invent a number to make it "quantitative".
6. Do not equate positive-sounding words with high certainty — "we believe"/"could"/"may" is lower certainty than "we expect"/"we will"/"we are committed to", regardless of tone.
7. Extract AT MOST 2 items PER UTTERANCE — the most genuinely significant forward-looking statements only. Prioritize quality over completeness.
8. Most utterances contain NO genuine forward-looking statement at all (they're just answering a question with current facts) — for those, contribute nothing to the output. Do not force an extraction to fill a quota.
9. `metric` MUST be exactly one value from this fixed list — never invent a new word, never combine two, never use a synonym or a more specific phrase: {metric_list}. Pick the closest match; if truly nothing fits, use "other".
10. `period` must be null or a short token like "FY27" or "Q2 FY27" — never a sentence, never a list, never placeholder text.
11. `category` must be exactly one of: Financial, Operating, Capital Allocation, Business — never anything else.
12. `utterance_index` must be the exact number of the utterance the item was drawn from.
13. Return ONLY a JSON object matching the exact schema. Never copy any instruction or example text from this prompt into your output — every field must be a real value drawn from the utterance, or null."""

_GUIDANCE_SYSTEM_RULES = _GUIDANCE_SYSTEM_RULES.format(metric_list=", ".join(_CANONICAL_METRICS))

_SCHEMA_HINT = """{"guidance_items": [<0 or more items, at most 2 per utterance>]}

Each item has this exact shape — this is a REAL FILLED EXAMPLE, not a template to copy:
{
  "utterance_index": 1,
  "metric": "ebitda_margin",
  "category": "Financial",
  "period": "FY27",
  "guidance_type": "quantitative",
  "target_low": 20.5,
  "target_high": 21.0,
  "target_value": null,
  "unit": "percent",
  "tone": "positive",
  "confidence": "high",
  "certainty": "explicit",
  "conditional": false
}"""


def _is_relevant(text: str) -> bool:
    low = text.lower()
    return any(kw in low for kw in _RELEVANCE_KEYWORDS)


_VALID_CATEGORIES = {"Financial", "Operating", "Capital Allocation", "Business"}
_VALID_GUIDANCE_TYPES = {"quantitative", "qualitative"}
_LEAKAGE_MARKERS = ("e.g.", " or ", "|", "null", "not stated", "template")
_NUMBER_RE_LOCAL = re.compile(r"-?\d[\d,]*\.?\d*")


def _text_numbers(text: str) -> set[float]:
    out = set()
    for m in _NUMBER_RE_LOCAL.finditer(text or ""):
        try:
            out.add(round(float(m.group().replace(",", "")), 2))
        except ValueError:
            continue
    return out


def _validate_item(item: dict, source_text: str) -> bool:
    """Best-effort structural + numeric-grounding check — same discipline
    as the P&L system's blueprint_validator.py, applied here after finding
    the same class of problem: schema-hint placeholder text ("period: FY27,
    Q2 FY27, or null if not stated", "category:
    Financial|Operating|Capital Allocation|Business") leaking verbatim into
    real extracted rows on the first real run against HDFC Bank's
    transcript, plus "quantitative" items with no actual target number at
    all. Rejects the item outright rather than trying to repair it.

    Real bug found live on GNFC (2026-09-22, user's own report — duplicate
    Capex guidance rows with no explanation): the module docstring's
    "an analyst's question becoming guidance is structurally impossible" -
    guarantee rests entirely on `_assign_roles_and_sections()`'s speaker-
    role heuristic in concall_parser.py — which learns anyone speaking
    before the detected Q&A transition as "Management" (a deliberate fix
    for TCS's no-upfront-block transcript format). Confirmed live: GNFC's
    transcript mislabeled analyst Jigar Shah as "Management" this way, so
    his question — "So totally INR1,800 crores... for the full year?" —
    reached this function tagged as a management utterance and got
    extracted as if it were the company's own capex guidance, sitting
    right next to the real answer (management's actual "1,200-1,500
    crores" figure) with no way to tell them apart. A second, independent
    check here — reject any item whose SOURCE utterance is itself phrased
    as a question — doesn't require fixing the speaker-role heuristic
    (which stays useful for its original TCS case) to close this gap:
    genuine guidance is a statement, never a question, regardless of who
    the transcript parser thinks said it."""
    if source_text and source_text.strip().rstrip('"\'”’').endswith("?"):
        return False

    metric = item.get("metric")
    if not isinstance(metric, str) or metric.lower() not in _CANONICAL_METRICS:
        return False  # off-vocabulary — see _CANONICAL_METRICS's comment on why this is enforced

    category = item.get("category")
    if category is not None and category not in _VALID_CATEGORIES:
        return False

    period = item.get("period")
    if period is not None:
        if not isinstance(period, str) or len(period) > 20:
            return False
        if any(marker in period.lower() for marker in _LEAKAGE_MARKERS):
            return False

    guidance_type = item.get("guidance_type")
    if guidance_type not in _VALID_GUIDANCE_TYPES:
        return False

    targets = [item.get("target_low"), item.get("target_high"), item.get("target_value")]
    if guidance_type == "quantitative" and all(t is None for t in targets):
        return False  # self-contradictory: claims quantitative, supplies no number

    source_numbers = _text_numbers(source_text)
    for t in targets:
        if t is None:
            continue
        try:
            t_rounded = round(float(t), 2)
        except (TypeError, ValueError):
            return False
        if not any(abs(t_rounded - n) <= 0.05 for n in source_numbers):
            return False  # ungrounded — not a real number from the source text

    return True


def _extract_from_batch(utterances: list[ConcallUtterance]) -> dict[str, list[dict]]:
    """One LLM call covering several utterances — {utterance_id: [items]}.
    Never raises — logs and returns {} on failure, same contract as every
    other ingestion path."""
    numbered = "\n\n".join(f"Utterance {i}:\n{u.text}" for i, u in enumerate(utterances, start=1))
    user_prompt = f"{numbered}\n\nRespond with ONLY a JSON object matching this schema:\n{_SCHEMA_HINT}"
    try:
        result = llm_client.chat_json(_GUIDANCE_SYSTEM_RULES, user_prompt)
    except Exception as e:
        logger.warning("guidance_extraction: batch extraction call failed", batch_size=len(utterances), error=str(e))
        return {}

    items = result.get("guidance_items")
    if not isinstance(items, list):
        return {}

    by_utterance: dict[str, list[dict]] = {}
    dropped = 0
    for item in items:
        if not isinstance(item, dict):
            dropped += 1
            continue
        idx = item.get("utterance_index")
        if not isinstance(idx, int) or not (1 <= idx <= len(utterances)):
            dropped += 1
            continue
        source_utterance = utterances[idx - 1]
        if not _validate_item(item, source_utterance.text):
            dropped += 1
            continue
        by_utterance.setdefault(source_utterance.id, []).append(item)

    if dropped:
        logger.info("guidance_extraction: validator dropped item(s)", total=len(items), dropped=dropped)
    return by_utterance


def _midpoint(item: dict | ManagementGuidance) -> float | None:
    if isinstance(item, dict):
        low, high, value = item.get("target_low"), item.get("target_high"), item.get("target_value")
    else:
        low, high, value = item.target_low, item.target_high, item.target_value
    if low is not None and high is not None:
        return (float(low) + float(high)) / 2
    if value is not None:
        return float(value)
    return None


def _compute_status_and_change(new_item: dict, previous: ManagementGuidance | None) -> tuple[str, float | None]:
    """Deterministic — never the LLM. Only compares numeric midpoints; a
    qualitative-only statement (no prior comparable number, or no prior
    guidance at all) gets NEW rather than a guessed status."""
    if previous is None:
        return "NEW", None

    new_mid = _midpoint(new_item)
    prev_mid = _midpoint(previous)
    if new_mid is None or prev_mid is None:
        return "NEW", None

    delta = new_mid - prev_mid
    metric = (new_item.get("metric") or "").lower()
    lower_is_better = any(kw in metric for kw in _LOWER_IS_BETTER_METRICS)

    tolerance = abs(prev_mid) * 0.01 if prev_mid else 0.01
    if abs(delta) <= tolerance:
        return "REITERATED", round(delta, 4)

    improved = (delta < 0) if lower_is_better else (delta > 0)
    return ("UPGRADED" if improved else "DOWNGRADED"), round(delta, 4)


_PERIOD_RE = re.compile(r"(?:Q(\d)\s*)?FY\s*'?(\d{2,4})", re.I)


def _normalize_period(period: str | None) -> str | None:
    """"FY 2027" / "fy27" / "Q1 FY2027" -> a consistent "FY27" / "Q1FY27" —
    applied both at storage time and lookup time so cross-quarter matching
    on `period` isn't broken by the same formatting-consistency problem
    `_CANONICAL_METRICS` fixes for `metric`. Falls back to a plain
    strip+upper for anything that doesn't match the FY pattern at all."""
    if not period:
        return None
    m = _PERIOD_RE.search(period)
    if not m:
        return period.strip().upper() or None
    q, yr = m.groups()
    yr2 = yr[-2:]
    return f"Q{q}FY{yr2}" if q else f"FY{yr2}"


def _find_previous_guidance(db: Session, company_id: str, metric: str, period: str | None,
                             exclude_transcript_id: str) -> ManagementGuidance | None:
    """None for the generic "other" bucket, always — two "other" items
    aren't necessarily about the same underlying topic just because
    neither fit the controlled vocabulary, so treating one as "previous
    guidance" for the other would produce a real but meaningless UPGRADED/
    DOWNGRADED comparison. Found live-testing real cross-quarter HDFC data
    2026-09-14: "other" was the single most common metric value, and a
    same-topic match there is coincidence, not identity."""
    if metric == "other":
        return None
    query = (
        db.query(ManagementGuidance)
        .filter(
            ManagementGuidance.company_id == company_id,
            ManagementGuidance.metric == metric,
            ManagementGuidance.transcript_id != exclude_transcript_id,
        )
    )
    if period is not None:
        query = query.filter(ManagementGuidance.period == period)
    return query.order_by(ManagementGuidance.retrieved_at.desc()).first()


def extract_guidance_for_transcript(db: Session, transcript_id: str) -> list[ManagementGuidance]:
    """Runs guidance extraction for every relevant management utterance in
    one transcript. Never raises — logs and returns whatever succeeded on
    partial failure, same contract as every other ingestion path."""
    transcript = db.query(ConcallTranscript).filter_by(id=transcript_id).first()
    if transcript is None:
        return []

    utterances = (
        db.query(ConcallUtterance)
        .filter(
            ConcallUtterance.transcript_id == transcript_id,
            ConcallUtterance.speaker_role.in_(_MANAGEMENT_ROLES),
        )
        .order_by(ConcallUtterance.sequence)
        .all()
    )
    relevant = [u for u in utterances if _is_relevant(u.text)]
    utterance_by_id = {u.id: u for u in relevant}

    now = datetime.now(timezone.utc)
    stored = []
    for batch_start in range(0, len(relevant), _BATCH_SIZE):
        batch = relevant[batch_start:batch_start + _BATCH_SIZE]
        items_by_utterance = _extract_from_batch(batch)

        for utterance_id, items in items_by_utterance.items():
            u = utterance_by_id[utterance_id]
            for item in items:
                metric = (item.get("metric") or "").lower()
                if not metric:
                    continue
                period = _normalize_period(item.get("period"))
                previous = _find_previous_guidance(db, transcript.company_id, metric, period, transcript_id)
                status, change_midpoint = _compute_status_and_change(item, previous)

                row = ManagementGuidance(
                    id=str(uuid.uuid4()), company_id=transcript.company_id, transcript_id=transcript_id,
                    utterance_id=u.id, quarter=transcript.quarter, speaker_role=u.speaker_role,
                    metric=metric, category=item.get("category"), period=period,
                    guidance_type=item.get("guidance_type") or "qualitative",
                    target_low=item.get("target_low"), target_high=item.get("target_high"),
                    target_value=item.get("target_value"), unit=item.get("unit"),
                    statement=u.text, tone=item.get("tone"), confidence=item.get("confidence"),
                    certainty=item.get("certainty"), conditional=bool(item.get("conditional", False)),
                    status=status, previous_guidance_id=previous.id if previous else None,
                    change_midpoint=change_midpoint, retrieved_at=now,
                )
                db.add(row)
                stored.append(row)

    transcript.extraction_status = "EXTRACTED"
    db.flush()

    logger.info("guidance_extraction: transcript processed", transcript_id=transcript_id,
                management_utterances=len(utterances), relevant_utterances=len(relevant),
                batches=-(-len(relevant) // _BATCH_SIZE) if relevant else 0,
                guidance_items_extracted=len(stored))
    return stored


# ── Concall Topic-Sentiment Grid — Premium PDF System, Stage B2 ────────────
# A controlled vocabulary distinct from _CANONICAL_METRICS above: this
# tracks management TONE per broad discussion topic (the doc's own example
# format: "Demand ↑ Positive, Margins ↓ Negative"), not specific numeric
# guidance targets. Trimmed from pdf generation.md's 19-topic list to the
# ones realistically discussed on a real earnings call, per that doc's own
# §20 list, still a fixed vocabulary for the same anti-drift reason
# _CANONICAL_METRICS exists — a model free to invent topic names would
# produce a different label every quarter and cross-quarter comparison
# (Stage B3) could never match them up.
_TOPIC_SENTIMENT_TOPICS = (
    "demand", "volume", "pricing", "margins", "costs", "capacity_capex",
    "new_products", "market_share", "competition", "guidance",
)
_VALID_SENTIMENTS = {"POSITIVE", "NEUTRAL", "NEGATIVE", "MIXED"}
_TOPIC_BATCH_SIZE = 6  # lighter task per utterance than guidance extraction, so a larger batch is fine

_TOPIC_SENTIMENT_SYSTEM_RULES = """You are the tone-analysis engine of a management-commentary intelligence
system for Indian equity research, analyzing several utterances from a
company's CEO/CFO/management during one earnings call. Each utterance is
numbered and independent.

Your job is to identify which of a FIXED list of topics each utterance
discusses, and management's tone on that topic in THAT utterance only.

STRICT RULES:
1. `topic` MUST be exactly one value from this fixed list — never invent a new word, never combine two: {topic_list}.
2. Only tag a topic if the utterance actually discusses it substantively — most utterances don't touch any of these topics at all; for those, contribute nothing.
3. `sentiment` must be exactly one of: POSITIVE, NEUTRAL, NEGATIVE, MIXED — based ONLY on management's own tone in that utterance's text, never your own view of whether the underlying fact is good or bad news.
4. A single utterance may cover more than one topic (e.g. both demand and pricing) — output one item per topic it substantively covers.
5. `utterance_index` must be the exact number of the utterance the item was drawn from.
6. Return ONLY a JSON object matching the exact schema. Never copy instruction or example text into your output."""

_TOPIC_SENTIMENT_SYSTEM_RULES = _TOPIC_SENTIMENT_SYSTEM_RULES.format(topic_list=", ".join(_TOPIC_SENTIMENT_TOPICS))

_TOPIC_SCHEMA_HINT = """{"topic_items": [<0 or more items>]}

Each item has this exact shape — this is a REAL FILLED EXAMPLE, not a template to copy:
{
  "utterance_index": 1,
  "topic": "margins",
  "sentiment": "NEGATIVE"
}"""


def _extract_topics_from_batch(utterances: list[ConcallUtterance]) -> dict[str, list[dict]]:
    """One LLM call covering several utterances — {utterance_id: [items]}.
    Never raises — logs and returns {} on failure."""
    numbered = "\n\n".join(f"Utterance {i}:\n{u.text}" for i, u in enumerate(utterances, start=1))
    user_prompt = f"{numbered}\n\nRespond with ONLY a JSON object matching this schema:\n{_TOPIC_SCHEMA_HINT}"
    try:
        result = llm_client.chat_json(_TOPIC_SENTIMENT_SYSTEM_RULES, user_prompt)
    except Exception as e:
        logger.warning("guidance_extraction: topic-sentiment batch call failed", batch_size=len(utterances), error=str(e))
        return {}

    items = result.get("topic_items")
    if not isinstance(items, list):
        return {}

    by_utterance: dict[str, list[dict]] = {}
    dropped = 0
    for item in items:
        if not isinstance(item, dict):
            dropped += 1
            continue
        idx = item.get("utterance_index")
        topic = item.get("topic")
        sentiment = item.get("sentiment")
        if not isinstance(idx, int) or not (1 <= idx <= len(utterances)):
            dropped += 1
            continue
        if not isinstance(topic, str) or topic.lower() not in _TOPIC_SENTIMENT_TOPICS:
            dropped += 1
            continue
        if not isinstance(sentiment, str) or sentiment.upper() not in _VALID_SENTIMENTS:
            dropped += 1
            continue
        source_utterance = utterances[idx - 1]
        by_utterance.setdefault(source_utterance.id, []).append(
            {"topic": topic.lower(), "sentiment": sentiment.upper()}
        )
    if dropped:
        logger.info("guidance_extraction: topic validator dropped item(s)", total=len(items), dropped=dropped)
    return by_utterance


def extract_topic_sentiment_for_transcript(db: Session, transcript_id: str) -> list[ConcallTopicSentiment]:
    """Never raises — logs and returns whatever succeeded on partial
    failure. Reuses the same management-role + relevance-keyword filtered
    utterance set extract_guidance_for_transcript already computes, rather
    than a second full pass over every utterance — a topic not touched by
    any of those already-relevant utterances simply gets no row, not a
    fabricated 'Neutral'."""
    transcript = db.query(ConcallTranscript).filter_by(id=transcript_id).first()
    if transcript is None:
        return []

    utterances = (
        db.query(ConcallUtterance)
        .filter(
            ConcallUtterance.transcript_id == transcript_id,
            ConcallUtterance.speaker_role.in_(_MANAGEMENT_ROLES),
        )
        .order_by(ConcallUtterance.sequence)
        .all()
    )
    relevant = [u for u in utterances if _is_relevant(u.text)]
    utterance_by_id = {u.id: u for u in relevant}

    now = datetime.now(timezone.utc)
    # One row per (transcript, topic) — first sentiment found for a topic
    # wins rather than being overwritten by a later, possibly-duplicate
    # utterance on the same topic (the DB's own uniqueness constraint).
    seen_topics: set[str] = set()
    stored = []
    for batch_start in range(0, len(relevant), _TOPIC_BATCH_SIZE):
        batch = relevant[batch_start:batch_start + _TOPIC_BATCH_SIZE]
        items_by_utterance = _extract_topics_from_batch(batch)

        for utterance_id, items in items_by_utterance.items():
            u = utterance_by_id[utterance_id]
            for item in items:
                topic = item["topic"]
                if topic in seen_topics:
                    continue
                seen_topics.add(topic)
                row = ConcallTopicSentiment(
                    id=str(uuid.uuid4()), transcript_id=transcript_id, company_id=transcript.company_id,
                    topic=topic, sentiment=item["sentiment"], evidence_utterance_id=u.id, retrieved_at=now,
                )
                db.add(row)
                stored.append(row)

    db.flush()
    logger.info("guidance_extraction: topic sentiment processed", transcript_id=transcript_id,
                relevant_utterances=len(relevant), topics_found=len(stored))
    return stored
