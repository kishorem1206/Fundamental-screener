"""CANSLIM letters (app/canslim/score.py). Offline: fixed inputs only."""
from datetime import date

from app.canslim import score as sc


def _q(rows):
    return {"quarters": sorted(rows), "rows": rows}


def test_c_uses_profit_and_sales_only_nudge():
    q = _q({"2025-06-30": {"net_profit": 100.0, "sales": 1000.0}, "2026-06-30": {"net_profit": 130.0, "sales": 1300.0}})
    c = sc.letter_c(q)
    assert c["score"] == 90.0 and c["growth_pct"] == 30.0  # 25%+ band, sales add 5
    weak = sc.letter_c(_q({"2025-06-30": {"net_profit": 100.0, "sales": 1000.0}, "2026-06-30": {"net_profit": 80.0, "sales": 1500.0}}))
    assert weak["score"] == 15.0  # strong sales never rescue a profit fall
    assert sc.letter_c(_q({"2025-06-30": {"net_profit": -5.0}, "2026-06-30": {"net_profit": 5.0}}))["score"] == 60.0
    assert sc.letter_c(_q({"2026-06-30": {"net_profit": 5.0}}))["score"] is None


def test_a_rewards_roe_with_strong_growth_and_scores_losses():
    series = {"years": ["2023", "2024", "2025", "2026"], "rows": {y: {"net_profit": 10.0} for y in ("2023", "2024", "2025")} | {"2026": {"net_profit": 20.0, "roe": 18.0}}}
    assert sc.letter_a(series, 26.0, None)["score"] == 100.0
    assert sc.letter_a(series, 16.0, None)["score"] == 60.0
    series["rows"]["2026"]["net_profit"] = -1.0
    assert sc.letter_a(series, None, None)["score"] == 15.0
    assert sc.letter_a({"years": [], "rows": {}}, None, None)["score"] is None


def test_n_and_s_bands():
    assert sc.letter_n([100.0] * 100)["score"] == 100.0
    assert sc.letter_n([100.0] * 99 + [90.0])["score"] == 80.0
    assert sc.letter_n([100.0] * 99 + [50.0])["score"] == 10.0
    assert sc.letter_n([100.0] * 10)["score"] is None
    assert sc.letter_s([100.0] * 40 + [200.0] * 10)["score"] == 100.0  # 200 against a 50-day average of 120
    assert sc.letter_s([100.0] * 40 + [140.0] * 10)["score"] == 85.0  # 1.30x
    assert sc.letter_s([100.0] * 50)["score"] == 60.0
    assert sc.letter_s([100.0] * 10)["score"] is None


def test_rs_rating_ranks_the_whole_universe():
    r = {f"S{i}": {"3M": float(i), "6M": float(i), "1Y": float(i)} for i in range(100)}
    r["NEW"] = {"3M": 500.0}
    ratings = sc.rs_ratings(r)
    assert ratings["S99"] == 99 and ratings["S0"] == 1 and "NEW" not in ratings
    assert sc.letter_l(ratings["S99"])["text"].endswith("(a leader)")
    assert sc.letter_l(None)["score"] is None


def test_i_is_a_healthy_range_not_more_is_better():
    assert sc.letter_i(15.0, 15.0)["score"] == 100.0
    assert sc.letter_i(8.0, 4.0)["score"] == 70.0
    assert sc.letter_i(50.0, 30.0)["score"] == 60.0
    assert sc.letter_i(1.0, 1.0)["score"] == 20.0
    assert sc.letter_i(None, None)["score"] is None


def test_m_reads_the_market():
    up = [float(i) for i in range(100, 400)]
    assert sc.market(up, date(2026, 10, 30))["score"] == 100.0
    assert sc.market(list(reversed(up)), date(2026, 10, 30))["score"] == 10.0
    assert sc.market([1.0] * 10, date(2026, 10, 30))["score"] is None


def test_missing_letters_are_left_out_never_zero():
    letters = {k: {"score": 80.0} for k in "cans"} | {"l": {"score": None}, "i": {"score": None}, "m": {"score": 40.0}}
    b = sc.blend(letters, 50.0)
    assert b["letters"] == 5 and b["canslim"] == 72.0 and b["combined"] == 63.2
    assert sc.blend(letters, None)["basis"].startswith("CANSLIM only")
    few = {"c": {"score": 90.0}, "a": {"score": None}}
    assert sc.blend(few, 60.0) == {"letters": 1, "canslim": None, "combined": 60.0, "basis": "peer quality only: too few CANSLIM letters"}
