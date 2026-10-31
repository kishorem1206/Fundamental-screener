"""Investment convergence (app/convergence/): reward/risk, the combined score and the gates. Offline."""
import re
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.convergence import risk_reward, score, settings
from app.routes.framework import _convergence_view
from app.stages import classify as stages

CFG = settings.defaults()
_GATES = {"core": True, "red_flags": []}


def _fw(**over):
    return {"quality": 72.0, "fundamental": 70.0, "technical": 70.0, "relative_strength": 70.0, "valuation": 55.0, "valuation_view": "FAIR", "quality_direction": "STABLE",
            "detail": {"decision": {"gates": _GATES, "interpretation": {"strong": ["growth"], "deteriorating": []}}, "fundamental": {"coverage": 1.0}}, **over}


def _stage(number=2, sub=stages.ESTABLISHED, **over):
    return {"stage": number, "sub_stage": sub, "confidence": 85.0, "reason": None, "rs": 8.0, "rs_improving": True, "next_stage": None, "provisional": False, "weeks_in_stage": 20,
            "sma_distance_pct": 10.0, "detail": {"signal": None}, **over}


def _rr(ratio=2.5):
    return {"ratio": ratio, "score": 75.0, "upside_pct": 25.0, "downside_pct": 10.0, "target": 125.0, "target_basis": "the 52-week high", "invalidation": 90.0, "invalidation_basis": "the last swing low"}


def _class(fw=None, stage=..., rr=None, unread=False):
    return score.build(fw or _fw(), _stage() if stage is ... else stage, rr or _rr(), {"12M": 12.0}, unread, CFG)


def test_default_weights_add_up_to_100():
    assert sum(CFG[k] for k in settings.WEIGHTS) == 100


def test_reward_risk_to_the_52_week_high():
    rr = risk_reward.compute(100, 2, 90, 95, 130, 110, 80, 92, CFG)
    assert rr["target"] == 130 and rr["invalidation"] == 92 and rr["downside_pct"] == 8 and rr["ratio"] == 3.75
    assert (rr["entry_low"], rr["entry_high"], rr["in_zone"]) == (90, 95, False)


def test_reward_risk_under_the_average_aims_only_for_the_average():
    rr = risk_reward.compute(100, 4, 120, 105, 300, 150, 80, None, CFG)
    assert rr["target"] == 120 and rr["target_basis"] == "the 30-week average" and rr["entry_low"] is None


def test_reward_risk_at_the_high_uses_a_measured_move():
    rr = risk_reward.compute(100, 2, 80, 90, 101, 98, 78, 85, CFG)
    assert rr["target_basis"].startswith("a measured move") and rr["target"] == 120


def test_a_tight_level_cannot_make_an_absurd_ratio():
    rr = risk_reward.compute(100, 2, 99, 99.5, 150, 110, 98.5, 99.5, CFG)
    assert rr["invalidation"] == 96.03 and rr["downside_pct"] == pytest.approx(5)
    assert risk_reward.compute(100, 2, 99, 99.5, 150, 110, None, 99.8, {**CFG, "sma_cushion_pct": 0})["downside_pct"] == 5


def test_no_level_under_the_price_gives_no_ratio_not_a_guess():
    rr = risk_reward.compute(100, 4, 120, 110, 200, 150, 105, 102, CFG)
    assert rr["ratio"] is None and rr["score"] is None and "under every" in rr["reason"]


def test_trend_counts_once_in_one_dimension():
    assert score.technical_stage(60, 90, CFG) == 72
    assert score.technical_stage(60, None, CFG) == 60 and score.technical_stage(None, 90, CFG) == 90


def test_combined_reweights_a_missing_dimension_and_stops_under_the_coverage():
    full = {"fundamental_quality": 80, "technical_stage": 60, "relative_strength": 60, "valuation": 60, "risk_reward": 60}
    assert score.combined(full, CFG) == (67.0, 100)
    assert score.combined({**full, "risk_reward": None}, CFG) == (pytest.approx(67.8, abs=0.1), 90)
    assert score.combined({"fundamental_quality": 80, "valuation": 60}, CFG)[0] is None
    assert score.combined({**full, "fundamental_quality": None}, CFG)[0] is None


def test_every_gate_passing_is_high_priority():
    assert _class()["classification"] == score.HIGH


@pytest.mark.parametrize("change", [{"quality": 60.0}, {"valuation_view": "EXPENSIVE"}, {"valuation_view": None, "valuation": None}, {"relative_strength": 50.0}, {"quality_direction": "DECLINING"}])
def test_one_failed_gate_closes_high_priority_however_high_the_number(change):
    out = _class(_fw(**change))
    assert out["classification"] != score.HIGH and out["combined"] is not None


def test_falling_relative_strength_closes_high_priority():
    assert _class(stage=_stage(rs_improving=False))["classification"] != score.HIGH


def test_a_high_number_never_lifts_stage_4_or_stage_3():
    best = _fw(quality=95.0, technical=95.0, relative_strength=95.0, valuation=95.0)
    for number in (3, 4):
        assert _class(best, _stage(number, None))["classification"] == score.CAUTION


def test_poor_reward_risk_restricts_eligibility():
    assert _class(rr=_rr(0.8))["classification"] == score.WATCH
    assert _class(stage=_stage(2, stages.EARLY), rr=_rr(0.8))["classification"] == score.WATCH


def test_early_moves_are_identified_separately():
    assert _class(stage=_stage(2, stages.EARLY))["classification"] == score.EARLY
    assert _class(stage=_stage(1, None, next_stage=2))["classification"] == score.EARLY
    assert _class(stage=_stage(1, None))["classification"] == score.WATCH


def test_weak_fundamentals_and_red_flags_restrict_eligibility():
    assert _class(_fw(quality=35.0))["classification"] == score.LOW
    assert _class(_fw(quality=45.0))["classification"] == score.WATCH
    assert _class(_fw(quality=45.0), _stage(2, stages.WEAKENING))["classification"] == score.LOW
    flagged = _fw(detail={"decision": {"gates": {"core": False, "red_flags": ["governance: SEBI order"]}, "interpretation": {}}})
    assert _class(flagged)["classification"] == score.LOW


def test_missing_or_stale_data_lowers_confidence_or_stops_the_rating():
    assert _class()["confidence_label"] == "High"
    assert _class(unread=True)["confidence"] == 85
    assert _class(_fw(valuation=None, valuation_view=None), rr={"ratio": None, "score": None, "reason": "x"}, unread=True)["confidence_label"] == "Low"
    assert _class(stage=_stage(None, None, reason="No trade since 2026-10-01"))["classification"] == score.NOT_RATED
    assert _class(_fw(quality=None))["classification"] == score.NOT_RATED


def test_the_assessment_states_levels_and_never_mentions_kept_out_inputs():
    out = _class()
    text = " ".join(x["text"] for x in out["qualifies"] + out["invalidates"]).lower()
    assert "under 90" in text and "2.5 to 1" in text
    assert not any(word in text for word in ("credit", "rating agency", "analyst", "fpi", "revision"))
    assert {d["status"].split(",")[0] for d in out["dimensions"]} == {"Existing", "Enhanced", "New"}


def test_settings_reject_weights_that_do_not_add_up():
    with pytest.raises(ValueError, match="add up to 100"):
        settings.check(CFG, {"weight_quality": 50})
    settings.check(CFG, {"weight_quality": 40, "weight_risk_reward": 5})
    with pytest.raises(ValueError, match="between"):
        settings.check(CFG, {"high_combined": 10})


def test_any_override_shows_in_the_version():
    assert settings.version(CFG) == "1.0"
    assert settings.version({**CFG, "high_combined": 75}).startswith("1.0-")


def test_the_stock_view_carries_every_field_the_page_reads():
    """The runner keeps some fields in columns and the rest in `detail`; the view must join them again."""
    read = {**_class(), "rr": _rr(), "windows": {"1M": 1.0}}
    columns = ("combined", "classification", "confidence", "confidence_label")
    row = SimpleNamespace(detail={k: v for k, v in read.items() if k not in columns}, combined=read["combined"], classification=read["classification"], confidence=read["confidence"],
                          confidence_label=read["confidence_label"], as_of=date(2026, 10, 30), method_version="1.0")
    view = _convergence_view(row, [], [], 70.0)
    panel = Path(__file__).parents[2] / "frontend/src/components/ConvergencePanel.tsx"
    block = re.search(r"export interface Convergence \{(.*?)\n  windows.*?\}\n", panel.read_text(), re.S).group(0)
    fields = set(re.findall(r"(?:^|[{;,\s])(\w+):", re.sub(r"rr: \{.*?\};", "rr: x;", block, flags=re.S)))
    assert {"combined", "classification", "confidence", "confidence_label", "rr", "windows", "dimensions", "high_gates"} <= fields
    assert fields - {"area", "text", "gate", "passed", "on", "from", "to", "direction"} <= set(view)
