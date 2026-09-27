"""EQI + diagnostics formula tests (P&L Analysis Engine plan, Milestone 3).
`test_compute_eqi_uses_revenue_not_ebitda` is a regression test for a real
bug caught while manually verifying Maruti Suzuki's end-to-end pipeline:
an earlier draft divided EBITDA (a post-opex profit figure) by total
income instead of REVENUE, producing a nonsensical ~13% "earnings quality"
for a healthy, core-business-driven company.
"""
from __future__ import annotations

from app.calculations.pl_intelligence.diagnostics import (
    margin_cascade_break,
    margin_stability_score,
    operating_leverage,
)
from app.calculations.pl_intelligence.earnings_quality import compute_eqi


def test_compute_eqi_uses_revenue_not_ebitda():
    # Maruti FY2025-shaped figures: revenue=152913, other_income=5199,
    # ebitda=20224 (~13% margin) — a healthy core-operating business.
    cascade_period = {"revenue": 152913.0, "other_income": 5199.0, "ebitda": 20224.0}
    result = compute_eqi(cascade_period)
    # revenue / (revenue + other_income) = 152913 / 158112 ≈ 0.9671
    assert abs(result["eqi"] - 0.9671) < 0.001
    assert result["classification"] == "HIGH_QUALITY"
    assert result["core_operating_income"] == 152913.0


def test_compute_eqi_jio_financial_style_non_core_dependency():
    # A holding-company-style P&L where other income (e.g. dividends from
    # subsidiaries) dwarfs core operating revenue — the exact scenario the
    # spec's own Jio Financial Services example describes.
    cascade_period = {"revenue": 100.0, "other_income": 900.0, "ebitda": 20.0}
    result = compute_eqi(cascade_period)
    assert result["eqi"] == 0.1
    assert result["classification"] == "LOW_QUALITY_NON_CORE_DEPENDENT"


def test_compute_eqi_missing_data_unavailable():
    assert compute_eqi({"revenue": None, "other_income": 10.0})["confidence"] == "UNAVAILABLE"
    assert compute_eqi({"revenue": 100.0, "other_income": None})["confidence"] == "UNAVAILABLE"


def test_operating_leverage_positive():
    result = operating_leverage(revenue_growth=10.0, ebitda_growth=20.0, pat_growth=25.0)
    assert result["ebitda_vs_revenue"] == "FASTER"
    assert result["operating_leverage"] == "POSITIVE"
    assert result["pat_vs_ebitda"] == "FASTER"


def test_operating_leverage_negative():
    result = operating_leverage(revenue_growth=20.0, ebitda_growth=5.0, pat_growth=2.0)
    assert result["operating_leverage"] == "NEGATIVE"
    assert result["below_ebitda_effect"] == "BELOW_EBITDA_ITEMS_ABSORBING_GAINS"


def test_margin_cascade_break_fires_on_healthy_ebitda_weak_pat():
    result = margin_cascade_break(ebitda_margin=32.5, pat_margin=-1.2, finance_cost_to_revenue_pct=6.0)
    assert result is not None
    assert result["severity"] == "HIGH"
    assert "finance_cost" in result["likely_drivers"]


def test_margin_cascade_break_does_not_fire_when_pat_healthy():
    assert margin_cascade_break(ebitda_margin=32.5, pat_margin=15.0, finance_cost_to_revenue_pct=1.0) is None


def test_margin_stability_score_insufficient_data():
    assert margin_stability_score({})["classification"] == "INSUFFICIENT_DATA"


def test_margin_stability_score_high_stable():
    series = {f"20{y}-03-31": 20.0 for y in range(18, 26)}
    result = margin_stability_score(series)
    assert result["classification"] == "HIGH_STABLE"
    assert result["stdev"] == 0.0
