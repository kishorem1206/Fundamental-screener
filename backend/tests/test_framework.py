"""Stock Quality framework — Fundamental Score, its inputs, and the Trend label."""
from app.calculations.scoring import SECTOR_WEIGHTS, UNIVERSAL_WEIGHTS
from app.framework import inputs
from app.framework.fundamental import classify, compute_fundamental, weights_for
from app.framework.trend import classify_trend


def _fd(profit, eps, equity, market=None):
    return {"income": {"net_income": profit, "basic_eps": eps}, "balance": {"total_equity": equity}, "market": market or {}}


# ── share dilution ──────────────────────────────────────────────────────────

def test_flat_share_count_scores_high_and_a_buyback_higher():
    flat = inputs.share_dilution(_fd({"FY2024": 100.0, "FY2025": 120.0}, {"FY2024": 10.0, "FY2025": 12.0}, {"FY2024": 500.0, "FY2025": 600.0}))
    assert flat["share_count_growth_pct_per_year"] == 0.0 and flat["score"] == 92.0
    buyback = inputs.share_dilution(_fd({"FY2024": 100.0, "FY2025": 100.0}, {"FY2024": 10.0, "FY2025": 10.5}, {"FY2024": 500.0, "FY2025": 520.0}))
    assert buyback["share_count_growth_pct_per_year"] < 0 and buyback["score"] > flat["score"]


def test_a_bonus_issue_is_not_dilution_but_a_share_sale_is():
    # shares double, equity only grows by the year's profit: bonus or split
    bonus = inputs.share_dilution(_fd({"FY2024": 100.0, "FY2025": 100.0}, {"FY2024": 10.0, "FY2025": 5.0}, {"FY2024": 500.0, "FY2025": 600.0}))
    assert bonus["score"] is None and bonus["split_or_bonus_years"] == ["FY2025"]
    # shares up 50% and equity up far more than profit: new money raised
    issue = inputs.share_dilution(_fd({"FY2024": 100.0, "FY2025": 150.0}, {"FY2024": 10.0, "FY2025": 10.0}, {"FY2024": 500.0, "FY2025": 1200.0}))
    assert issue["share_count_growth_pct_per_year"] == 50.0 and issue["score"] == 0.0


def test_dilution_needs_two_years():
    assert inputs.share_dilution(_fd({"FY2025": 100.0}, {"FY2025": 10.0}, {}))["score"] is None


# ── dividend sustainability ─────────────────────────────────────────────────

def test_no_dividend_is_not_scored_rather_than_penalised():
    assert inputs.dividend_sustainability(_fd({}, {}, {}), {"fcf_latest": 100.0})["score"] is None


def test_dividend_covered_by_profit_and_cash_beats_one_paid_out_of_borrowing():
    market = {"dividend_rate": 10.0, "shares_outstanding": 10.0, "payout_ratio": 0.4}
    safe = inputs.dividend_sustainability(_fd({}, {}, {}, market), {"fcf_latest": 250.0})
    assert safe["fcf_cover"] == 2.5 and safe["payout_pct"] == 40.0 and safe["score"] > 95
    stretched = inputs.dividend_sustainability(_fd({}, {}, {}, {**market, "payout_ratio": 1.2}), {"fcf_latest": -50.0})
    assert stretched["score"] < 15
    # a lender is judged on payout only: free cash flow means nothing for a bank
    bank = inputs.dividend_sustainability(_fd({}, {}, {}, market), {"fcf_latest": -9999.0}, lender=True)
    assert "fcf_cover" not in bank and bank["score"] == 95.0


# ── earnings consistency ────────────────────────────────────────────────────

def test_annual_fallback_rewards_steady_profit_growth():
    steady = inputs.earnings_consistency({"pat_series": {"FY2023": 10, "FY2024": 12, "FY2025": 15, "FY2026": 18}}, {})
    patchy = inputs.earnings_consistency({"pat_series": {"FY2023": 10, "FY2024": -4, "FY2025": 6, "FY2026": 3}}, {})
    assert steady["score"] == 100.0 and patchy["score"] < 50
    assert inputs.earnings_consistency({"pat_series": {"FY2025": 1, "FY2026": 2}}, {})["score"] is None


def test_stored_quarters_are_used_and_shrinking_losses_do_not_count_as_consistency(db):
    from datetime import datetime, timezone
    from app.infrastructure.database.metric_store import insert_metric_value
    from app.infrastructure.database.models import Stock

    now = datetime.now(timezone.utc)
    quarters = [f"{y}-{md}" for y in (2024, 2025, 2026) for md in ("03-31", "06-30", "09-30", "12-31")]

    def company(symbol, values):
        s = Stock(id=f"TEST:{symbol}", symbol=symbol, exchange="TEST", company_name=symbol, is_active=False, created_at=now, updated_at=now)
        db.add(s); db.flush()
        for period, value in zip(quarters, values):
            insert_metric_value(db, company_id=s.id, metric_key="qtr_net_profit", period=period, value=value, unit="cr",
                                source="SCREENER", source_tier=2, confidence="MEDIUM", statement_type="CONSOLIDATED",
                                reported_or_calculated="REPORTED")
        return s.id

    grower = inputs.earnings_consistency({}, {}, db, company("FWGROW", [10 + i for i in range(12)]))
    assert grower["quarters"] == 12 and grower["quarters_in_profit_pct"] == 100.0
    assert grower["quarters_ahead_of_last_year_pct"] == 100.0 and grower["score"] == 100.0
    # always in loss, each loss smaller than the year before
    loss_maker = inputs.earnings_consistency({}, {}, db, company("FWLOSS", [-100 + 5 * i for i in range(12)]))
    assert loss_maker["quarters_in_profit_pct"] == 0.0 and loss_maker["quarters_ahead_of_last_year_pct"] == 100.0
    assert loss_maker["score"] == 15.0


# ── working capital and "double in" ─────────────────────────────────────────

def test_working_capital_trend_is_skipped_for_lenders_and_when_unknown():
    assert inputs.working_capital_trend({"ccc_trend": "IMPROVING", "wc_to_revenue_trend": "DETERIORATING"})["score"] == 55.0
    assert inputs.working_capital_trend({"ccc_trend": "IMPROVING"}, lender=True)["score"] is None
    assert inputs.working_capital_trend({})["score"] is None


def test_double_in_flags_a_recovery_from_a_depressed_base():
    base = {"revenue_series": {"FY2023": 1, "FY2024": 1, "FY2025": 1, "FY2026": 1}}
    voltas_like = inputs.double_in({**base, "revenue_cagr_3y": 14.5, "pat_cagr_3y": 40.7,
                                    "pat_margin_series": {"FY2023": 1.44, "FY2024": 2.03, "FY2025": 5.49, "FY2026": 2.66}})
    assert voltas_like["profit_doubles_in_years"] == 2.0 and voltas_like["low_base"] is True
    compounder = inputs.double_in({**base, "revenue_cagr_3y": 20.0, "pat_cagr_3y": 24.0,
                                   "pat_margin_series": {"FY2023": 14.0, "FY2024": 15.0, "FY2025": 15.5, "FY2026": 16.0}})
    assert compounder["low_base"] is False and compounder["revenue_doubles_in_years"] == 3.8
    assert inputs.double_in({**base, "revenue_cagr_3y": -3.0, "pat_cagr_3y": None})["revenue_doubles_in_years"] is None


# ── Fundamental Score ───────────────────────────────────────────────────────

def test_weights_sum_to_one_drop_valuation_and_keep_efficiency_as_an_add_on():
    for sector in (None, *SECTOR_WEIGHTS):
        w = weights_for(sector)
        assert abs(sum(w.values()) - 1.0) < 1e-9 and "valuation" not in w
        src = SECTOR_WEIGHTS.get(sector, UNIVERSAL_WEIGHTS)
        if src["efficiency"] and src["growth"]:  # efficiency counts at half its sector weight relative to a framework input
            assert abs(w["efficiency"] / w["growth"] - 0.5 * src["efficiency"] / src["growth"]) < 1e-9


_STRONG = {"growth": 80, "profitability": 85, "cash_flow": 80, "balance_sheet": 90, "efficiency": 70}


def test_valuation_cannot_move_the_fundamental_score():
    metrics = {"pat_series": {"FY2023": 10, "FY2024": 12, "FY2025": 15, "FY2026": 18}}
    a = compute_fundamental({**_STRONG, "valuation": 5}, metrics, {}, "FMCG")
    b = compute_fundamental({**_STRONG, "valuation": 95}, metrics, {}, "FMCG")
    assert a["score"] == b["score"] and a["classification"] == "STRONG"


def test_missing_inputs_are_left_out_not_scored_as_average():
    out = compute_fundamental(_STRONG, {}, {}, "Banks")
    assert out["components"]["working_capital_trend"]["score"] is None
    assert out["components"]["dividend_sustainability"]["score"] is None
    assert out["coverage"] == 0.8  # only the five category scores had data
    assert 80 <= out["score"] <= 90  # the weighted average of those five, untouched by the absent inputs


def test_low_base_recovery_caps_growth():
    metrics = {"revenue_series": {"FY2023": 1, "FY2024": 1, "FY2025": 1, "FY2026": 1}, "revenue_cagr_3y": 14.5, "pat_cagr_3y": 40.7,
               "pat_margin_series": {"FY2023": 1.44, "FY2024": 2.03, "FY2025": 5.49, "FY2026": 2.66}}
    out = compute_fundamental({**_STRONG, "growth": 89}, metrics, {}, "Consumer Durables")
    assert out["components"]["growth"]["score"] == 70.0 and "capped" in out["components"]["growth"]["note"]


def test_too_little_data_gives_no_score():
    assert compute_fundamental({"growth": 60}, {}, {}, "FMCG")["score"] is None
    assert [classify(s) for s in (70, 55, 45, 35, 20, None)] == ["STRONG", "GOOD", "BORDERLINE", "WEAK", "VERY_WEAK", None]


# ── Trend ───────────────────────────────────────────────────────────────────

def test_trend_labels():
    up = {"roce_trend": "IMPROVING", "pat_margin_trend": "IMPROVING", "ebitda_margin_trend": "STRONGLY_IMPROVING",
          "debt_trend": "STABLE", "fcf_trend": "IMPROVING"}
    assert classify_trend(up)["trend"] == "IMPROVING"
    down = {k: "DETERIORATING" for k in up}
    assert classify_trend(down)["trend"] == "DECLINING"
    assert classify_trend({k: "STABLE" for k in up})["trend"] == "STABLE"
    mixed = {**up, "roce_trend": "DETERIORATING", "fcf_trend": "DETERIORATING", "is_cyclical": True}
    assert classify_trend(mixed)["trend"] == "CYCLICAL"
    assert classify_trend({"roce_trend": "IMPROVING"})["trend"] == "INSUFFICIENT_DATA"


def test_trend_for_a_lender_ignores_debt_and_free_cash_flow():
    m = {"roe_trend": "IMPROVING", "pat_margin_trend": "IMPROVING", "debt_trend": "STRONGLY_DETERIORATING",
         "fcf_trend": "STRONGLY_DETERIORATING", "quarterly_growth_pct": {"revenue": 22.0}, "revenue_cagr_3y": 12.0}
    out = classify_trend(m, lender=True)
    assert out["trend"] == "IMPROVING" and {s["signal"] for s in out["signals"]} == {"returns", "net margin", "growth"}


def test_a_lender_can_be_read_from_two_signals_but_other_companies_need_three():
    m = {"roe_trend": "DETERIORATING", "roce_trend": "DETERIORATING", "pat_margin_trend": "DETERIORATING"}
    assert classify_trend(m, lender=True)["trend"] == "DECLINING"
    assert classify_trend(m)["trend"] == "INSUFFICIENT_DATA"


def test_a_cyclical_business_with_a_clear_direction_is_reported_by_direction():
    m = {"roce_trend": "IMPROVING", "pat_margin_trend": "IMPROVING", "ebitda_margin_trend": "IMPROVING",
         "debt_trend": "IMPROVING", "fcf_trend": "DETERIORATING", "is_cyclical": True}
    assert classify_trend(m)["trend"] == "IMPROVING"


# ── Phase 5: Screener series, Business Quality, Quality ─────────────────────

from app.framework import business_quality as bq
from app.framework.quality import band, compute_quality
from app.framework.screener_series import cagr


def _series(rows: dict) -> dict:
    """rows: {year: {field: value}} with year as an int; capital fields optional."""
    table = {f"{y}-03-31": dict(r) for y, r in rows.items()}
    years = sorted(table)
    for prev, cur in zip(years, years[1:]):
        a, b = table[prev], table[cur]
        for x in (a, b):
            if "reserves" in x:
                x["capital_employed"] = x.get("equity_capital", 0) + x["reserves"] + x.get("borrowings", 0)
                x["net_worth"] = x.get("equity_capital", 0) + x["reserves"]
        if any(x.get("net_worth", 1) <= 0 for x in (a, b)):
            b["negative_net_worth"] = True
        elif "pbt" in b:
            b["roce"] = (b["pbt"] + b.get("interest", 0)) / ((a["capital_employed"] + b["capital_employed"]) / 2) * 100
            b["roe"] = b["net_profit"] / ((a["net_worth"] + b["net_worth"]) / 2) * 100
    return {"basis": "CONSOLIDATED", "years": years, "rows": table, "source": "test"}


def _compounder(years=11):
    return _series({2015 + i: {"sales": 100 * 1.12 ** i, "opm": 22 + (i % 3), "pbt": 20 * 1.12 ** i, "interest": 1,
                               "net_profit": 15 * 1.12 ** i, "eps": 10 * 1.12 ** i, "equity_capital": 10,
                               "reserves": 60 * 1.10 ** i, "borrowings": 5} for i in range(years)})


def test_cagr_and_series_need_positive_ends():
    s = _compounder()
    assert round(cagr(s, "sales", 5), 1) == 12.0 and round(cagr(s, "sales", 10), 1) == 12.0
    assert cagr(s, "sales", 11) is None
    assert cagr(_series({2020: {"sales": -5}, 2025: {"sales": 10}}), "sales", 1) is None


def test_a_decade_of_high_returns_and_steady_margins_scores_as_durable():
    s = _compounder()
    d, m, p, c = bq.durability(s, False), bq.margin_resilience(s), bq.predictability(s), bq.capital_allocation(s, False)
    assert d["years"] == 10 and d["years_at_or_above_15_pct"] == 100.0 and d["score"] > 80
    assert m["score"] > 85 and p["score"] == 100.0 and p["cyclical"] is False and c["score"] > 50


def test_negative_net_worth_years_count_against_durability():
    rows = {2015 + i: {"sales": 100, "opm": 10, "pbt": 10, "interest": 5, "net_profit": 8, "equity_capital": 10,
                       "reserves": (-50 if i < 5 else 40), "borrowings": 60} for i in range(11)}
    d = bq.durability(_series(rows), False)
    assert len(d["negative_net_worth_years"]) >= 5 and d["years_at_or_above_15_pct"] <= 50


def test_a_cyclical_record_and_a_loss_maker_are_marked_down():
    swings = _series({2015 + i: {"sales": 100, "opm": (25 if i % 2 else 3), "net_profit": (20 if i % 2 else -5)} for i in range(11)})
    assert bq.margin_resilience(swings)["score"] < 30
    pred = bq.predictability(swings)
    assert pred["cyclical"] is True and pred["score"] < 40
    loss = _series({2015 + i: {"sales": 100, "pbt": -20 + i, "interest": 2, "net_profit": -20 + i, "equity_capital": 10,
                               "reserves": 100 - 5 * i, "borrowings": 50} for i in range(11)})
    assert bq.capital_allocation(loss, False)["score"] == 5.0


def test_too_little_history_is_not_scored():
    short = _series({2023: {"sales": 1, "opm": 1, "net_profit": 1}, 2024: {"sales": 1, "opm": 1, "net_profit": 1}})
    assert bq.durability(short, False)["score"] is None and bq.margin_resilience(short)["score"] is None
    assert bq.predictability(short)["score"] is None and bq.capital_allocation(short, False)["score"] is None


def test_business_quality_for_a_lender_skips_margins_and_reads_roe(db):
    out = bq.compute_business_quality(db, "TEST:NOBODY", lender=True, series=_compounder())
    assert "margin_resilience" not in out["components"] and out["components"]["durability"]["measure"] == "ROE"
    assert out["score"] is not None and out["not_measured"] == bq.NOT_MEASURED


def test_quality_is_seventy_thirty_and_a_pledge_caps_it():
    assert compute_quality({"score": 80.0}, {"score": 60.0})["score"] == 74.0
    only = compute_quality({"score": 70.0}, {"score": None})
    assert only["score"] == 70.0 and "only" in only["formula"]
    pledged = {"score": 90.0, "components": {"promoter_behaviour": {"governance_flags": [
        {"event_type": "PLEDGE_PRESENT", "severity": "MEDIUM", "event_date": "2026-06-30"}]}}}
    capped = compute_quality({"score": 85.0}, pledged)
    assert capped["score"] == 49.0 and "pledge" in capped["capped"] and capped["band"] == "BORDERLINE"
    assert compute_quality({"score": None}, {"score": 80.0})["score"] is None
    assert [band(s) for s in (65, 50, 40, 30, 29.9)] == ["STRONG", "GOOD", "BORDERLINE", "WEAK", "VERY_WEAK"]


def test_prefetched_pages_are_shared_by_every_ingest_and_errors_resurface(monkeypatch):
    import pytest
    from app.ingestion import screener_pages

    calls = []

    def fake_fetch(symbol, consolidated):
        calls.append(consolidated)
        if consolidated:
            raise RuntimeError("HTTP 404")
        return '<div id="top"></div>'

    monkeypatch.setattr(screener_pages, "fetch_html", fake_fetch)
    with screener_pages.prefetched("abc"), screener_pages.prefetched("ABC"):  # nested: still one read
        for _ in range(3):
            assert screener_pages.screener_stock("ABC", False).page_html == '<div id="top"></div>'
        with pytest.raises(RuntimeError):
            screener_pages.screener_stock("ABC", True)
    assert calls == [False, True]  # each page read once, however many ingests use it
    assert screener_pages.screener_stock("ABC", False).page_html is None  # outside the block: a normal live Stock


def test_the_newest_day_wins_and_full_beats_quick_on_the_same_day(db):
    from datetime import date, datetime, timezone
    from app.framework import store
    from app.infrastructure.database.models import Stock

    now = datetime.now(timezone.utc)
    db.add(Stock(id="TEST:FWSTORE", symbol="FWSTORE", exchange="TEST", company_name="x", is_active=False, created_at=now, updated_at=now))
    db.flush()
    store.save(db, "TEST:FWSTORE", store.FULL, {"fundamental": 70}, {}, as_of=date(2026, 10, 5))
    store.save(db, "TEST:FWSTORE", store.QUICK, {"fundamental": 60}, {}, as_of=date(2026, 10, 6))
    assert store.latest(db, "TEST:FWSTORE").basis == store.QUICK
    store.save(db, "TEST:FWSTORE", store.FULL, {"fundamental": 72}, {}, as_of=date(2026, 10, 6))
    assert store.latest(db, "TEST:FWSTORE").basis == store.FULL
    assert [r.basis for r in store.latest_for_all(db) if r.stock_id == "TEST:FWSTORE"] == [store.FULL]
