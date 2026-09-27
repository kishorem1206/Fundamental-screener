"""Tests for `app/calculations/bank_roe_engine.py` — the port of the
mentor's IDFC FIRST ROE simulator. The reference numbers below were
produced by running his own JavaScript `simulate()` (extracted verbatim
from idfc-first-roe-simulator.html) in Node with the same starting state,
so any drift from his method fails here.
"""
from __future__ import annotations

import pytest

from app.calculations import bank_roe_engine as eng

MENTOR_START = {"px0": 85.90, "bv0": 56.10, "sh0": 862.0, "roe0": 0.09}


@pytest.mark.parametrize("name,params,price,multiple,total_ret,raised,dilution", [
    ("mgmt", dict(roe=15, yrs=5, g=18, pay=12, pb=2.2, disc=5), 491.8170, 5.7255, 5.9459, 60709.04, 0.3134),
    ("bear", dict(roe=7, yrs=5, g=15, pay=12, pb=1.0, disc=10), 103.2888, 1.2024, 1.2816, 84818.39, 1.1973),
    ("bull", dict(roe=17, yrs=4, g=20, pay=10, pb=3.0, disc=5), 848.3307, 9.8758, 10.1171, 64953.67, 0.2284),
])
def test_simulate_matches_mentors_javascript(name, params, price, multiple, total_ret, raised, dilution):
    out = eng.simulate(MENTOR_START, params)
    last = out["rows"][-1]
    assert last["price"] == pytest.approx(price, abs=1e-3)
    assert last["multiple"] == pytest.approx(multiple, abs=1e-4)
    assert last["total_return_multiple"] == pytest.approx(total_ret, abs=1e-4)
    assert out["raised"] == pytest.approx(raised, abs=0.01)
    assert out["dilution"] == pytest.approx(dilution, abs=1e-4)


def test_mentors_crossover_arithmetic():
    """His page: 9% ROE / 12% payout funds ~7.9% growth; 15% ROE funds 13.2%."""
    assert eng.sustainable_growth(9, 12) == pytest.approx(7.92)
    assert eng.sustainable_growth(15, 12) == pytest.approx(13.2)
    assert eng.crossover_roe(13, 13) == pytest.approx(14.94, abs=0.01)


def test_no_fresh_equity_when_growth_is_self_funded():
    out = eng.simulate(MENTOR_START, dict(roe=15, yrs=1, g=5, pay=10, pb=2.0, disc=5))
    assert out["raised"] == 0.0
    assert out["dilution"] == 0.0


def test_verdict_bands():
    assert eng.verdict_of(1.0) == "Dead money"
    assert eng.verdict_of(2.5) == "Modest compounder"
    assert eng.verdict_of(5.7) == "Multibagger territory"
    assert eng.verdict_of(12).startswith("Rare outcome")


def test_pb_anchor_curve_hits_mentors_cases():
    assert eng.pb_for_roe(7) == 1.0 and eng.pb_for_roe(9) == 1.1
    assert eng.pb_for_roe(15) == 2.2 and eng.pb_for_roe(17) == 3.0
    assert eng.pb_for_roe(2) == 1.0 and eng.pb_for_roe(30) == 3.0  # flat outside anchors
    assert eng.pb_for_roe(12) == pytest.approx(1.65)


def test_justified_pb_and_implied_roe_are_inverses():
    pb = eng.justified_pb(15, coe_pct=12, g_pct=7)
    assert eng.implied_roe(pb, coe_pct=12, g_pct=7) == pytest.approx(15)
    assert eng.justified_pb(15, coe_pct=6, g_pct=7) is None


_INPUTS = {
    "price": 85.92, "bvps": 56.518, "shares": 8_622_196_236.0, "payout_ratio": 0.0965, "trailing_eps": 2.59,
    "equity": {"FY2024": 3.2e11, "FY2025": 3.8e11, "FY2026": 4.7e11},
    "assets": {"FY2024": 3.0e12, "FY2025": 3.44e12, "FY2026": 4.0e12},
    "net_income": {"FY2024": 2.9e10, "FY2025": 1.5e10, "FY2026": 1.6e10},
    "quarterly_pat_cr": [("2026-03-31", 319.0), ("2026-06-30", 1075.0)],
}


def test_analysis_uses_latest_quarter_annualised_like_the_mentor():
    out = eng.compute_bank_roe_analysis(_INPUTS)
    assert out["available"] is True
    # 1075 x 4 / (56.518 x 862.2 cr) ~ 8.8% — his "~9% run-rate"
    assert out["start"]["run_rate_roe"] == pytest.approx(8.82, abs=0.05)
    assert "PAT x4" in out["start"]["run_rate_source"]
    assert out["sustainability"]["gap"] > 0  # growth outruns retained profit
    assert {p["key"] for p in out["presets"]} == {"asis", "mature", "self", "bull", "bear"}


def test_dupont_identity_holds():
    for row in eng.compute_bank_roe_analysis(_INPUTS)["dupont"]:
        assert row["roe"] == pytest.approx(row["roa"] * row["leverage"], rel=1e-9)


def test_falls_back_to_trailing_eps_then_degrades_without_zeros():
    no_q = dict(_INPUTS, quarterly_pat_cr=[])
    out = eng.compute_bank_roe_analysis(no_q)
    assert "trailing EPS" in out["start"]["run_rate_source"]
    bare = eng.compute_bank_roe_analysis({"price": 100, "bvps": 50, "shares": 1e9})
    assert bare["available"] is False
    assert eng.compute_bank_roe_analysis({})["available"] is False


def test_missing_checklist_values_are_null_not_zero():
    out = eng.compute_bank_roe_analysis(_INPUTS)
    by = {c["key"]: c for c in out["checklist"]}
    assert by["credit_cost"]["value"] is None
    assert by["cost_to_income"]["value"] is None


# ── scoring hooks ─────────────────────────────────────────────────────────

_FD = {
    "market": {"current_price": 85.92, "book_value": 56.518, "shares_outstanding": 8_622_196_236.0, "payout_ratio": 0.0965},
    "balance": {"total_assets": {"FY2025": 3.44e12, "FY2026": 4.0e12}},
    "_banking_authoritative_metrics": {"bank_latest_qtr_pat_cr": 1075.0},
}


def test_scoring_metrics_use_run_rate_roe_when_quarter_available():
    out = eng.scoring_metrics({"roe": 3.8}, _FD)
    # run-rate ~8.8%, self-funded ~7.97%, asset growth ~16.3% -> gap ~8.3pp
    assert out["sustainable_growth_gap"] == pytest.approx(8.3, abs=0.2)
    # P/B 1.52 vs anchor(8.8%)~1.09 -> ~ +39%
    assert out["pb_roe_premium_pct"] == pytest.approx(39, abs=3)


def test_scoring_metrics_fall_back_to_engine_roe_and_never_zero_fill():
    fd = {k: v for k, v in _FD.items() if k != "_banking_authoritative_metrics"}
    out = eng.scoring_metrics({"roe": 15.0}, fd)
    assert out["sustainable_growth_gap"] == pytest.approx(16.3 - 15 * (1 - 0.0965), abs=0.2)
    none = eng.scoring_metrics({}, _FD | {"_banking_authoritative_metrics": {}})
    assert none == {"sustainable_growth_gap": None, "pb_roe_premium_pct": None}


def test_banking_and_nbfc_frameworks_expose_and_compute_the_new_metrics():
    from app.sectors.banking import BankingSector
    from app.sectors.nbfc import NBFCSector
    for fw in (BankingSector(), NBFCSector()):
        names = {m.name for m in fw.key_metrics()}
        assert {"sustainable_growth_gap", "pb_roe_premium_pct"} <= names
        got = fw.extract_sector_metrics({"roe": 3.8}, _FD)
        assert got["sustainable_growth_gap"] == pytest.approx(8.3, abs=0.2)
