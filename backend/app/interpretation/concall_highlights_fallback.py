"""Deterministic "Results & Concall Highlights" fallback — used only when
`arthneeti_client.ingest_concall_highlights` finds no matching page for a
company+quarter (2026-09-15). Pure Python over rows our own extraction
pipeline already produced and validated (`ConcallTopicSentiment`,
`ManagementGuidance`) — no new LLM call, same "never fabricate, only
restate what's already grounded" discipline as `concall_report_data.py`'s
`_what_changed`.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.infrastructure.database.models import ConcallTopicSentiment, ManagementGuidance
from app.interpretation.concall_report_data import _TOPIC_LABELS

_SENTIMENT_LABEL = {"POSITIVE": "Positive", "NEGATIVE": "Negative", "NEUTRAL": "Neutral", "MIXED": "Mixed"}


def _fmt_guidance_target(g: ManagementGuidance) -> str | None:
    unit = g.unit or ""
    if g.target_low is not None and g.target_high is not None:
        return f"{float(g.target_low):g}-{float(g.target_high):g}{unit}"
    if g.target_value is not None:
        return f"{float(g.target_value):g}{unit}"
    return None


def generate_highlights_fallback(db: Session, transcript_id: str) -> list[dict]:
    """[{"heading": str, "bullets": [str, ...]}, ...] built from whatever
    topic-sentiment/guidance rows already exist for this transcript. Never
    raises; returns [] if neither extraction pass has produced anything yet
    (caller should skip storing an empty ConcallHighlight rather than
    persist a section-less row)."""
    topics = db.query(ConcallTopicSentiment).filter_by(transcript_id=transcript_id).all()
    guidance_rows = db.query(ManagementGuidance).filter_by(transcript_id=transcript_id).all()

    sections = []

    if topics:
        bullets = [
            f"{_TOPIC_LABELS.get(t.topic, t.topic.replace('_', ' ').title())}: "
            f"{_SENTIMENT_LABEL.get(t.sentiment, t.sentiment.title())} management tone."
            for t in topics
        ]
        sections.append({"heading": "Management Commentary by Topic", "bullets": bullets})

    if guidance_rows:
        bullets = []
        for g in guidance_rows:
            target = _fmt_guidance_target(g)
            metric_label = g.metric.replace("_", " ").title()
            if target:
                bullets.append(f"{metric_label} guidance: {target} ({g.period or 'period not specified'}).")
            else:
                bullets.append(f"{metric_label} guidance reiterated for {g.period or 'the guided period'}.")
        sections.append({"heading": "Management Guidance", "bullets": bullets})

    return sections
