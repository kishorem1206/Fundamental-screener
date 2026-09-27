"""Shared query layer for rendering Concall Intelligence data into both PDF
report paths — Stage C5, extended by the Premium PDF System's Stages B2/B3/
B5 (2026-09-14: topic-sentiment grid, quarter-over-quarter change detection,
guidance consistency score). Mirrors app/calculations/pnl_engine.py's role
for the P&L section: one function both renderers call, computed fresh at
render time — the B3 diff and B5 score are pure Python over already-stored
rows, no new LLM call here, same discipline as "render what's real, don't
fabricate a summary that doesn't exist".
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.infrastructure.database.models import (
    ConcallTopicSentiment, ConcallTranscript, ManagementCredibility, ManagementGuidance, ManagementPromise,
)

_TOPIC_LABELS = {
    "demand": "Demand", "volume": "Volume", "pricing": "Pricing", "margins": "Margins",
    "costs": "Costs", "capacity_capex": "Capacity/Capex", "new_products": "New Products",
    "market_share": "Market Share", "competition": "Competition", "guidance": "Guidance",
}
_SENTIMENT_ARROW = {"POSITIVE": "↑", "NEGATIVE": "↓", "NEUTRAL": "→", "MIXED": "↕"}


def _dedupe_guidance(rows: list[ManagementGuidance]) -> list[ManagementGuidance]:
    """Collapses exact-duplicate guidance rows — same metric, same target
    figures, same underlying quote — to one. Real gap found live on GNFC
    (2026-09-22, user's own report — "why so many Capex numbers... some
    duplicate TARGET / WHAT WAS SAID"): `ManagementGuidance` rows are never
    overwritten, only appended (same "never overwrite, only append" ledger
    discipline every other ingestion path in this codebase already uses),
    so a transcript whose guidance extraction ran more than once (e.g. an
    analysis re-run) accumulates the SAME quote as separate rows — GNFC had
    its "1,200-1,500 crores" capex guidance and its "Thank you to
    moderator..." opening remark each stored twice, byte-for-byte
    identical statement text and target figures both times. `unit` is
    deliberately excluded from the key (confirmed live: the same number
    landed once as unit="crores" and once as unit="INR crores" across the
    two runs — a formatting difference, not a different figure) and so is
    `category` (the same quote occasionally got a different category tag
    run to run — still the same guidance, not two). `metric` IS kept in
    the key: if the same quote was genuinely classified under two
    different metrics, that's a real classification disagreement worth
    keeping visible, not silently merged away. Keeps whichever duplicate
    was retrieved most recently (rows already arrive sorted newest-first)."""
    seen: set[tuple] = set()
    out = []
    for g in rows:
        key = (g.metric, g.target_low, g.target_high, g.target_value,
               (g.statement or "").strip()[:120])
        if key in seen:
            continue
        seen.add(key)
        out.append(g)
    return out


def _guidance_consistency_score(credibility_rows: list[ManagementCredibility]) -> dict | None:
    """Premium PDF System, Stage B5 — deliberately named "consistency", not
    "accuracy": this measures whether management's guidance holds up
    (REITERATED) or improves (UPGRADED) quarter to quarter, vs. gets walked
    back (DOWNGRADED) — NOT whether a guided number was later hit, which
    would need guidance-to-actual-outcome matching that doesn't exist yet
    (see credibility.py's own module docstring). Formula: 100 * (reiterated
    + upgraded) / comparable — a downgrade is the only thing that reduces
    this score; an upgrade counts the same as a reiteration (both mean
    management didn't walk back a prior commitment).

    Real bug found live: the denominator used to be `guidance_count`
    (every guidance item ever extracted, NEW included), but a NEW item —
    by definition, guidance with no prior quarter's figure on record to
    compare against (`_find_previous_guidance` in guidance_extraction.py,
    including every item in the "other" bucket, which that function never
    even attempts to match) — can structurally never become REITERATED or
    UPGRADED. With most real transcripts only 1-2 quarters deep and "other"
    routinely the single largest metric bucket, NEW dominates the
    denominator for nearly every company, so the score reads near 0 for
    everyone regardless of whether management has actually walked anything
    back — indistinguishable from "not enough repeat history to judge yet".
    Restricting the denominator to `comparable` (REITERATED+UPGRADED+
    DOWNGRADED — updates that had a real prior figure to be judged against)
    makes the score measure what its name says, and returns None (renders
    nothing) rather than a misleading 0 when there's no comparable history
    yet, same as every other "not enough data" case in this app."""
    comparable = sum(c.reiterated_count + c.upgraded_count + c.downgraded_count for c in credibility_rows)
    if comparable == 0:
        return None
    held_or_improved = sum(c.reiterated_count + c.upgraded_count for c in credibility_rows)
    metrics_with_comparison = sum(1 for c in credibility_rows if c.reiterated_count + c.upgraded_count + c.downgraded_count > 0)
    return {
        "score": round(held_or_improved / comparable * 100, 1),
        "metrics_tracked": metrics_with_comparison,
        "total_updates": comparable,
    }


def _topic_sentiment_rows(db: Session, transcript_id: str) -> list[ConcallTopicSentiment]:
    return db.query(ConcallTopicSentiment).filter_by(transcript_id=transcript_id).all()


def _what_changed(
    latest_topics: list[ConcallTopicSentiment], previous_topics: list[ConcallTopicSentiment],
    latest_guidance: list[ManagementGuidance],
) -> list[str]:
    """Premium PDF System, Stage B3 — pure Python diff, no new LLM call:
    reuses Stage B2's topic-sentiment rows and the guidance status
    Stage C3's deterministic engine already computed. Never invents a
    change that isn't backed by two real stored rows."""
    changes: list[str] = []
    prev_by_topic = {t.topic: t.sentiment for t in previous_topics}
    for t in latest_topics:
        label = _TOPIC_LABELS.get(t.topic, t.topic)
        prev_sentiment = prev_by_topic.get(t.topic)
        if prev_sentiment is None:
            changes.append(f"{label}: newly discussed this quarter ({t.sentiment.title()})")
        elif prev_sentiment != t.sentiment:
            changes.append(f"{label}: {prev_sentiment.title()} → {t.sentiment.title()}")
    for g in latest_guidance:
        if g.status in ("UPGRADED", "DOWNGRADED"):
            changes.append(f"{g.metric.replace('_', ' ').title()} guidance {g.status.lower()} since last call")
    return changes


def build_concall_report_data(db: Session, company_id: str) -> dict:
    """Empty/absent fields mean "no concall data ingested yet for this
    company" — callers check `latest_transcript` before rendering
    anything, same as `pnl_engine`'s `years_of_data` gate."""
    transcripts = (
        db.query(ConcallTranscript)
        .filter_by(company_id=company_id)
        .order_by(ConcallTranscript.filing_date.desc())
        .limit(2)
        .all()
    )
    if not transcripts:
        return {"latest_transcript": None}
    latest_transcript = transcripts[0]
    previous_transcript = transcripts[1] if len(transcripts) > 1 else None

    guidance_rows = _dedupe_guidance(
        db.query(ManagementGuidance)
        .filter_by(company_id=company_id, transcript_id=latest_transcript.id)
        .order_by(ManagementGuidance.retrieved_at.desc())
        .all()
    )
    credibility_rows = (
        db.query(ManagementCredibility)
        .filter_by(company_id=company_id)
        .filter(ManagementCredibility.guidance_count > 1)  # only metrics with real cross-quarter history
        .order_by(ManagementCredibility.guidance_count.desc())
        .all()
    )
    promise_rows = (
        db.query(ManagementPromise)
        .filter_by(company_id=company_id, status="PENDING")
        .order_by(ManagementPromise.retrieved_at.desc())
        .limit(8)
        .all()
    )

    latest_topics = _topic_sentiment_rows(db, latest_transcript.id)
    previous_topics = _topic_sentiment_rows(db, previous_transcript.id) if previous_transcript else []
    what_changed = _what_changed(latest_topics, previous_topics, guidance_rows) if previous_transcript else []

    return {
        "topic_sentiment": [
            {"topic": _TOPIC_LABELS.get(t.topic, t.topic), "sentiment": t.sentiment,
             "arrow": _SENTIMENT_ARROW.get(t.sentiment, "→")}
            for t in latest_topics
        ],
        "what_changed": what_changed,
        "has_previous_call": previous_transcript is not None,
        "guidance_consistency": _guidance_consistency_score(credibility_rows),
        "latest_transcript": {
            "quarter": latest_transcript.quarter,
            "call_date": latest_transcript.call_date,
            "filing_date": latest_transcript.filing_date,
            "management_participants": latest_transcript.management_participants or [],
        },
        "guidance": [
            {
                "metric": g.metric, "category": g.category, "period": g.period,
                "guidance_type": g.guidance_type,
                "target_low": float(g.target_low) if g.target_low is not None else None,
                "target_high": float(g.target_high) if g.target_high is not None else None,
                "target_value": float(g.target_value) if g.target_value is not None else None,
                "unit": g.unit, "tone": g.tone, "confidence": g.confidence,
                "certainty": g.certainty, "conditional": g.conditional, "status": g.status,
                # The verbatim (lightly transcribed) management quote this
                # row was extracted from — added 2026-09-21 so a generic
                # "other"/qualitative row (no clean target figure) still
                # shows real context instead of just the word "qualitative"
                # with nothing to distinguish one row from another.
                "statement": g.statement,
            }
            for g in guidance_rows
        ],
        "credibility": [
            {
                "metric": c.metric, "guidance_count": c.guidance_count,
                "upgraded_count": c.upgraded_count, "downgraded_count": c.downgraded_count,
                "reiterated_count": c.reiterated_count, "last_status": c.last_status,
            }
            for c in credibility_rows
        ],
        # Deduped by text, not just id: two different ManagementGuidance
        # rows (different metrics) can legitimately come from the same
        # utterance — found rendering real HDFC data, 2026-09-14 — and
        # since `promise` is the full source utterance, not the specific
        # sub-claim, that shows as an apparent duplicate to a reader.
        "promises": list({p.promise: {"promise": p.promise, "category": p.category} for p in promise_rows}.values()),
    }
