"""Context-builder dispatch tests for the 5 new `pl_*` narrative sections
(P&L Analysis Engine plan, Milestone 4c) — pure dict slicing, no DB/LLM
involved, matching `context_builder.py`'s own architectural contract."""
from __future__ import annotations

import pytest

from app.interpretation.context_builder import build_context

_MASTER = {
    "company": {"name": "Test Co"},
    "pl_intelligence": {
        "period": "2025-03-31",
        "statement_type": "CONSOLIDATED",
        "peer_percentiles": {"pat_margin": {"percentile": 80}},
        "structure": {"csr": 0.97, "csr_band": "PRIMARILY_PARENT_DOMESTIC"},
        "margin_headroom": {"headroom_pct": 12.0, "classification": "MODERATE_HEADROOM"},
        "doubling": {"revenue": {"doubling_years": 6}, "pat": {"doubling_years": 5}, "velocity_comparison": "PAT_FASTER"},
        "diagnostics": {"operating_leverage": {"operating_leverage": "POSITIVE"}},
        "earnings_quality": {"eqi": 0.95, "classification": "HIGH_QUALITY"},
        "non_core_income": {"decomposition": "not_available"},
        "management_commentary": {
            "margin_headroom": [{"chunk_text": "Management expects margin improvement next quarter."}],
            "earnings_quality": [],
        },
    },
}


@pytest.mark.parametrize("section_id", [
    "pl_peer_positioning", "pl_standalone_consolidated", "pl_margin_headroom",
    "pl_doubling_velocity", "pl_earnings_quality_v2",
])
def test_all_five_sections_dispatch_without_error(section_id):
    context = build_context(_MASTER, section_id)
    assert context["company"] == {"name": "Test Co"}
    assert context["period"] == "2025-03-31"


def test_peer_positioning_context_shape():
    context = build_context(_MASTER, "pl_peer_positioning")
    assert context["peer_percentiles"]["pat_margin"]["percentile"] == 80


def test_margin_headroom_context_includes_commentary_excerpts():
    context = build_context(_MASTER, "pl_margin_headroom")
    assert context["management_commentary"] == ["Management expects margin improvement next quarter."]


def test_earnings_quality_v2_context_empty_commentary():
    context = build_context(_MASTER, "pl_earnings_quality_v2")
    assert context["management_commentary"] == []
    assert context["earnings_quality"]["classification"] == "HIGH_QUALITY"


def test_unknown_pl_section_raises():
    with pytest.raises(ValueError):
        build_context(_MASTER, "pl_not_a_real_section")


def test_missing_pl_intelligence_key_degrades_cleanly():
    context = build_context({"company": {}}, "pl_peer_positioning")
    assert context["peer_percentiles"] is None
