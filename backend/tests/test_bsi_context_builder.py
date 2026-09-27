"""Context-builder dispatch tests for the 5 new `bs_*` narrative sections
(Balance Sheet Analysis Engine, Milestone 6) — pure dict slicing, no DB/LLM
involved, matching `context_builder.py`'s own architectural contract
(mirrors `test_pl_intelligence_context_builder.py`)."""
from __future__ import annotations

import pytest

from app.interpretation.context_builder import build_context

_MASTER = {
    "company": {"name": "Test Co"},
    "balance_sheet_intelligence": {
        "period": "2026-03-31",
        "statement_type": "CONSOLIDATED",
        "balance_sheet_integrity": {"status": "VALID"},
        "house": {"sources": [], "applications": [], "sources_total": 1000.0, "applications_total": 1000.0},
        "common_size": {"fixed_assets": 30.0},
        "working_capital": {"dso_series": {"FY2026": 11.0}, "methodology": "CLOSING_BALANCE_OVER_TOTAL_REVENUE"},
        "derived_metrics": {"debt_to_equity": 0.1, "liabilities_to_equity": 0.4, "roce": 15.0},
        "archetype": {"classification": "STRONG", "evidence": ["Low D/E"]},
        "risk_flags": [
            {"flag_id": "HIGH_LEVERAGE", "status": "NOT_TRIGGERED"},
            {"flag_id": "WORKING_CAPITAL_DRAG", "status": "TRIGGERED"},
            {"flag_id": "RELATED_PARTY_EXPOSURE", "status": "SOURCE_REQUIRED"},
        ],
        "coverage": {
            "coverage_pct": 54.8,
            "metrics": {"ar_aging": {"status": "SOURCE_REQUIRED", "reason": "no source", "dependencies": []}},
        },
    },
}


@pytest.mark.parametrize("section_id", [
    "bs_structure_and_liquidity", "bs_working_capital", "bs_leverage_and_roce",
    "bs_archetype_and_risk", "bs_coverage_summary",
])
def test_all_five_sections_dispatch_without_error(section_id):
    context = build_context(_MASTER, section_id)
    assert context["company"] == {"name": "Test Co"}
    assert context["period"] == "2026-03-31"


def test_structure_and_liquidity_context_shape():
    context = build_context(_MASTER, "bs_structure_and_liquidity")
    assert context["balance_sheet_integrity"]["status"] == "VALID"
    assert context["house"]["sources_total"] == 1000.0


def test_archetype_and_risk_only_includes_triggered_flags():
    context = build_context(_MASTER, "bs_archetype_and_risk")
    flag_ids = [f["flag_id"] for f in context["triggered_risk_flags"]]
    assert flag_ids == ["WORKING_CAPITAL_DRAG"]
    assert "HIGH_LEVERAGE" not in flag_ids
    assert "RELATED_PARTY_EXPOSURE" not in flag_ids


def test_coverage_summary_context_includes_top_gaps():
    context = build_context(_MASTER, "bs_coverage_summary")
    assert context["coverage_pct"] == 54.8
    assert any(g["metric"] == "ar_aging" for g in context["top_source_gaps"])


def test_unknown_bs_section_raises():
    with pytest.raises(ValueError):
        build_context(_MASTER, "bs_not_a_real_section")


def test_missing_balance_sheet_intelligence_key_degrades_cleanly():
    context = build_context({"company": {}}, "bs_leverage_and_roce")
    assert context["derived_metrics"] is None
