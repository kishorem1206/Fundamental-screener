"""M1-M5 scoring tests (P&L Analysis Engine plan, Milestone 3) — boundary
values, weighted-sum arithmetic, `components`/`algorithm_version` always
present."""
from __future__ import annotations

from app.calculations.pl_intelligence.scoring import (
    ALGORITHM_VERSION,
    compute_master_score,
    score_m1_sector_margin_percentile,
    score_m3_doubling_velocity,
    score_m4_eqi,
)


def test_m1_boundaries():
    assert score_m1_sector_margin_percentile(81) == 100.0
    assert score_m1_sector_margin_percentile(80) == 70.0
    assert score_m1_sector_margin_percentile(50) == 70.0
    assert score_m1_sector_margin_percentile(49) == 30.0
    assert score_m1_sector_margin_percentile(None) is None


def test_m3_boundaries_and_gap_interpolation():
    assert score_m3_doubling_velocity(4.9) == 100.0
    assert score_m3_doubling_velocity(5.0) == 80.0
    assert score_m3_doubling_velocity(8.0) == 80.0
    assert score_m3_doubling_velocity(10.0) == 40.0
    assert score_m3_doubling_velocity(15.0) == 40.0
    # midpoint of the spec-flagged 8-10y gap -> halfway between 80 and 40
    assert score_m3_doubling_velocity(9.0) == 60.0


def test_m4_boundaries():
    assert score_m4_eqi(0.95) == 100.0
    assert score_m4_eqi(0.90) == 100.0
    assert score_m4_eqi(0.89) == 60.0
    assert score_m4_eqi(0.70) == 60.0
    assert score_m4_eqi(0.69) == 20.0
    assert score_m4_eqi(None) is None


def test_compute_master_score_full_weighted_sum():
    result = compute_master_score(m1=100.0, m2=80.0, m3=100.0, m4=100.0, m5=100.0)
    # 0.25*100 + 0.20*80 + 0.20*100 + 0.20*100 + 0.15*100 = 25+16+20+20+15 = 96
    assert result["master_pl_score"] == 96.0
    assert result["classification"] == "PREMIUM_QUALITY_GROWTH_EFFICIENCY_LEADER"
    assert result["components"] == {"M1": 100.0, "M2": 80.0, "M3": 100.0, "M4": 100.0, "M5": 100.0}
    assert result["algorithm_version"] == ALGORITHM_VERSION


def test_compute_master_score_never_omits_components_key():
    result = compute_master_score(None, None, None, None, None)
    assert result["master_pl_score"] is None
    assert result["classification"] is None
    assert "components" in result
    assert result["components"] == {"M1": None, "M2": None, "M3": None, "M4": None, "M5": None}


def test_compute_master_score_renormalizes_over_missing_components():
    # Only M1 and M4 available; weights renormalized over 0.25+0.20=0.45
    result = compute_master_score(m1=100.0, m2=None, m3=None, m4=100.0, m5=None)
    assert result["master_pl_score"] == 100.0
    result2 = compute_master_score(m1=100.0, m2=None, m3=None, m4=0.0, m5=None)
    # (0.25*100 + 0.20*0) / 0.45 = 25/0.45 ≈ 55.56
    assert abs(result2["master_pl_score"] - 55.56) < 0.01


def test_classification_bands():
    assert compute_master_score(80, 80, 80, 80, 80)["classification"] == "PREMIUM_QUALITY_GROWTH_EFFICIENCY_LEADER"
    assert compute_master_score(60, 60, 60, 60, 60)["classification"] == "STABLE_COMPOUNDER_MARGIN_EXPANSION_CANDIDATE"
    assert compute_master_score(40, 40, 40, 40, 40)["classification"] == "HIGH_OVERHEAD_NON_CORE_TRAP_STAGNANT_PERFORMER"
