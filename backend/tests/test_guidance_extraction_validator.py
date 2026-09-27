"""Tests for `guidance_extraction._validate_item()` — pure-function
structural/numeric-grounding checks (no DB/LLM), plus the question-mark
guard added 2026-09-22.
"""
from __future__ import annotations

from app.interpretation.guidance_extraction import _validate_item

_VALID_ITEM = {
    "metric": "capex", "category": "Capital Allocation", "period": "FY27",
    "guidance_type": "quantitative", "target_low": 1200.0, "target_high": 1500.0,
}


def test_valid_item_passes():
    source = "Targeted for the full year is another INR1,200 crores to INR1,500 crores."
    assert _validate_item(_VALID_ITEM, source) is True


def test_rejects_item_sourced_from_a_question():
    """Real bug found live on GNFC (2026-09-22): an analyst's question
    ("So totally INR1,800 crores -- INR1,500 crores to INR1,800 crores for
    the full year?") got mislabeled "Management" upstream by the
    speaker-role heuristic and extracted as if it were the company's own
    capex guidance. Genuine guidance is a statement, never a question."""
    item = {**_VALID_ITEM, "target_low": 1500.0, "target_high": 1800.0}
    source = "So totally INR1,800 crores -- INR1,500 crores to INR1,800 crores for the full year?"
    assert _validate_item(item, source) is False


def test_rejects_question_with_trailing_quote_or_whitespace():
    item = {**_VALID_ITEM}
    assert _validate_item(item, 'Are we targeting 1,200 crores to 1,500 crores?  ') is False
    assert _validate_item(item, 'Are we targeting 1,200 crores to 1,500 crores?"') is False


def test_off_vocabulary_metric_rejected():
    item = {**_VALID_ITEM, "metric": "made_up_metric"}
    assert _validate_item(item, "Targeted for the full year is another INR1,200 crores.") is False


def test_invalid_category_rejected():
    item = {**_VALID_ITEM, "category": "Not A Real Category"}
    assert _validate_item(item, "Targeted for the full year is another INR1,200 crores.") is False


def test_leaked_placeholder_period_rejected():
    item = {**_VALID_ITEM, "period": "FY27, Q2 FY27, or null if not stated"}
    assert _validate_item(item, "Targeted for the full year is another INR1,200 crores.") is False


def test_quantitative_with_no_target_rejected():
    item = {**_VALID_ITEM, "target_low": None, "target_high": None, "target_value": None}
    assert _validate_item(item, "We remain confident about capex plans.") is False


def test_ungrounded_number_rejected():
    item = {**_VALID_ITEM, "target_low": 9999.0, "target_high": 9999.0}
    assert _validate_item(item, "Targeted for the full year is another INR1,200 crores to INR1,500 crores.") is False
