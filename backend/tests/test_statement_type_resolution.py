"""Tests for `statement_type_resolution.prefer_current_statement_type()` —
the shared "pick whichever side is actually current" helper used by
pl_intelligence, balance_sheet_intelligence and cash_flow_intelligence's
auto-detect (no explicit toggle) path. See each package's own orchestrator
test for the real GPT-Healthcare-shaped integration scenario.
"""
from __future__ import annotations

from app.calculations.statement_type_resolution import prefer_current_statement_type


def test_prefers_the_more_recent_period():
    assert prefer_current_statement_type({"CONSOLIDATED": "2022-03-31", "STANDALONE": "2026-03-31"}) == "STANDALONE"
    assert prefer_current_statement_type({"CONSOLIDATED": "2026-03-31", "STANDALONE": "2022-03-31"}) == "CONSOLIDATED"


def test_ties_prefer_consolidated():
    assert prefer_current_statement_type({"CONSOLIDATED": "2026-03-31", "STANDALONE": "2026-03-31"}) == "CONSOLIDATED"


def test_missing_side_never_wins():
    assert prefer_current_statement_type({"CONSOLIDATED": None, "STANDALONE": "2026-03-31"}) == "STANDALONE"
    assert prefer_current_statement_type({"CONSOLIDATED": "2026-03-31", "STANDALONE": None}) == "CONSOLIDATED"


def test_both_missing_defaults_consolidated():
    assert prefer_current_statement_type({"CONSOLIDATED": None, "STANDALONE": None}) == "CONSOLIDATED"
    assert prefer_current_statement_type({}) == "CONSOLIDATED"
