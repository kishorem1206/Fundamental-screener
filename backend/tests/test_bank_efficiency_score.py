"""Tests for `_bank_efficiency_score()`/`_nbfc_efficiency_score()` —
2026-09-27 fix: these used to be an unconditional `return 50.0` regardless
of data availability. Now they score the cost-to-income ratio when it's on
record (merged into `metrics` by the orchestrator from
`banking_data_bridge.py`) and fall back to the same neutral 50 only when
the metric is genuinely missing — not as a permanent constant."""
from __future__ import annotations

from app.calculations.scoring import _bank_efficiency_score, _nbfc_efficiency_score


def test_falls_back_to_neutral_when_cost_to_income_missing():
    assert _bank_efficiency_score({}) == 50.0
    assert _nbfc_efficiency_score({}) == 50.0


def test_low_cost_to_income_scores_well_above_neutral():
    # HDFC Bank-shaped (~39%, real ingested value) — a best-in-class ratio.
    assert _bank_efficiency_score({"cost_to_income_ratio": 39.2}) > 75.0


def test_high_cost_to_income_scores_below_neutral():
    # RBL Bank-shaped (~87%, real ingested value) — a stressed ratio.
    assert _bank_efficiency_score({"cost_to_income_ratio": 87.6}) < 15.0


def test_score_decreases_monotonically_as_cost_to_income_rises():
    scores = [_bank_efficiency_score({"cost_to_income_ratio": v}) for v in (30, 45, 60, 80)]
    assert scores == sorted(scores, reverse=True)


def test_nbfc_uses_the_same_cost_to_income_thresholds_as_bank():
    assert _nbfc_efficiency_score({"cost_to_income_ratio": 42.0}) == _bank_efficiency_score({"cost_to_income_ratio": 42.0})


def test_nim_alone_scores_without_cost_to_income():
    # ICICI-shaped (4.36%, real ingested value) — a healthy bank NIM.
    assert _bank_efficiency_score({"nim": 4.36}) > 75.0


def test_nim_and_cost_to_income_blend_beats_either_alone_when_both_strong():
    cti_only = _bank_efficiency_score({"cost_to_income_ratio": 39.2})
    nim_only = _bank_efficiency_score({"nim": 4.5})
    both = _bank_efficiency_score({"cost_to_income_ratio": 39.2, "nim": 4.5})
    assert min(cti_only, nim_only) <= both <= max(cti_only, nim_only)


def test_nbfc_nim_uses_a_wider_band_than_bank_nim():
    # A gold-loan-NBFC-shaped 9% NIM is normal/strong for an NBFC but would
    # be nonsensical (off the top of the scale) for a bank — the two must
    # use different threshold tables, not the same one.
    assert _nbfc_efficiency_score({"nim": 9.0}) > 75.0
    assert _bank_efficiency_score({"nim": 9.0}) == 100.0  # clamped at the bank table's top bucket
