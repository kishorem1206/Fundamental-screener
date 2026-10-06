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



# ── Phase 6: price statistics, Quantitative, Relative Strength ──────────────

from datetime import date as _date, timedelta as _td

from app.framework import price_stats, quantitative as qn, relative_strength as rs


def _daily(start_value: float, daily_growth: float, days: int = 400, end=_date(2026, 10, 5), shock=None):
    out, v = [], start_value
    for i in range(days, -1, -1):
        d = end - _td(days=i)
        if d.weekday() >= 5:
            continue
        v *= 1 + daily_growth
        if shock and shock[0] <= d <= shock[1]:
            v *= 0.99
        out.append((d, v))
    return out


def test_window_returns_drawdown_and_volatility():
    end = _date(2026, 10, 5)
    flat_then_up = [(end - _td(days=400), 100.0), (end - _td(days=365), 100.0), (end - _td(days=30), 110.0), (end, 121.0)]
    r = price_stats.window_returns(flat_then_up, end)
    assert round(r["1Y"], 2) == 21.0 and round(r["1M"], 2) == 10.0
    assert price_stats.window_returns(flat_then_up[2:], end)["1Y"] is None  # listed within the year
    dd, peak, trough = price_stats.max_drawdown([(end, 100.0), (end + _td(1), 80.0), (end + _td(2), 120.0), (end + _td(3), 90.0)])
    assert dd == -25.0 and peak == end + _td(2)
    assert price_stats.volatility(_daily(100, 0.0)) == 0.0 and price_stats.volatility([(end, 1.0)]) is None
    assert round(price_stats.excess(20.0, 10.0), 2) == 9.09


def _quarters(sales, op, profit):
    qs = [f"{2024 + i // 4}-{('03-31', '06-30', '09-30', '12-31')[i % 4]}" for i in range(len(sales))]
    return {"quarters": qs, "rows": {q: {"sales": s, "operating_profit": o, "net_profit": p} for q, s, o, p in zip(qs, sales, op, profit)},
            "source": "test"}


def test_growth_acceleration_and_margin_change():
    series = _compounder()  # 12% a year for a decade
    fast = _quarters([100] * 4 + [130] * 4, [20] * 4 + [30] * 4, [10] * 4 + [14] * 4)
    ga = qn.growth_acceleration(fast, series)
    assert ga["sales_last_4q_growth_pct"] == 30.0 and ga["sales_3y_growth_pct"] == 12.0 and ga["score"] > 80
    mc = qn.margin_change(fast)
    assert mc["operating_margin_last_4q_pct"] == round(120 / 520 * 100, 2) and mc["change_pts"] > 3 and mc["score"] > 85
    assert qn.growth_acceleration(_quarters([1] * 5, [1] * 5, [1] * 5), series)["score"] is None


def test_return_and_debt_change():
    s = _compounder()
    rc = qn.return_change(s, lender=False)
    assert rc["measure"] == "ROCE" and rc["to"] == "2025" and rc["from"] == "2022"
    assert qn.debt_change(s)["debt_to_equity_now"] < qn.debt_change(s)["debt_to_equity_then"]
    debt_free = _series({2015 + i: {"sales": 1, "equity_capital": 10, "reserves": 90, "borrowings": 0} for i in range(5)})
    assert qn.debt_change(debt_free)["reading"] == "debt-free throughout"


def test_excess_is_scaled_to_a_year_so_short_windows_are_not_overweighted():
    one_month, _ = rs._excess_score({"1M": 5.0})
    one_year, _ = rs._excess_score({"1Y": 5.0})
    assert one_month > one_year  # 5% over a month is worth more than 5% over a year
    assert rs._excess_score({"1M": None})[0] is None


def test_resilience_rewards_holding_up_when_the_market_falls():
    end = _date(2026, 10, 5)
    fall = (end - _td(days=200), end - _td(days=170))
    market = _daily(100, 0.0002, shock=fall)
    steady = _daily(100, 0.0002)
    crashed = _daily(100, 0.0002, shock=(fall[0], fall[1] + _td(days=20)))
    good, bad = rs.resilience(steady, market), rs.resilience(crashed, market)
    assert good["market_fall_pct"] < -5 and good["excess_during_fall_pct"] > 10 and good["score"] > bad["score"]
    calm = rs.resilience(steady, _daily(100, 0.0002))
    assert calm["score"] is None


def test_why_holding_up_only_when_the_sector_is_weak_and_the_stock_is_ahead():
    relative = {"components": {"vs_sector": {"benchmark_return_pct": {"6M": -8.0, "1Y": -12.0}, "excess_pct": {"6M": 3.0, "1Y": 15.0}}}}
    fundamental = {"components": {"cash_flow": {"score": 80}}}
    out = rs.why_holding_up(relative, fundamental, {"components": {"debt_change": {"change": -0.2}}}, {"components": {}})
    assert out["stock_ahead_of_sector_over"] == ["1Y"] and out["reasons"] == ["debt falling against equity", "strong cash flow"]
    nothing = rs.why_holding_up(relative, {"components": {}}, {"components": {}}, {"components": {}})
    assert "price alone" in nothing["reasons"][0]
    rising = {"components": {"vs_sector": {"benchmark_return_pct": {"1Y": 10.0}, "excess_pct": {"1Y": 30.0}}}}
    assert rs.why_holding_up(rising, fundamental, {"components": {}}, {"components": {}}) is None



# ── Phase 7: Technical and Valuation ────────────────────────────────────────

from app.framework import technical as tech, valuation as val
from app.technical.indicators.plugin import OHLCVBar


def _bars(closes, volumes=None):
    start = _date(2025, 1, 1)
    return [OHLCVBar(date=(start + _td(days=i)).isoformat(), open=c, high=c * 1.01, low=c * 0.99, close=c,
                     volume=(volumes[i] if volumes else 1000.0)) for i, c in enumerate(closes)]


def _zigzag(n, drift):
    import math
    return [100 * (1 + drift) ** i * (1 + 0.04 * math.sin(i / 6)) for i in range(n)]


def test_uptrend_and_downtrend_read_from_swing_points_and_averages():
    up, down = _bars(_zigzag(300, 0.003)), _bars(_zigzag(300, -0.003))
    t_up, t_down = tech.trend_structure(up), tech.trend_structure(down)
    assert "uptrend" in t_up["reading"] and t_up["score"] >= 75
    assert "downtrend" in t_down["reading"] and t_down["score"] <= 25
    ma = tech.moving_averages(up)
    assert ma["above_200"] and ma["golden_cross"] and ma["score"] >= 80
    assert tech.moving_averages(down)["score"] <= 20
    assert tech.moving_averages(up[:100])["score"] is None


def test_rsi_and_macd_come_from_the_technical_screener_engines():
    up = _bars(_zigzag(300, 0.003))
    r, m = tech.rsi(up), tech.macd(up)
    assert 0 <= r["rsi_14"] <= 100 and isinstance(r["score"], float)
    assert set(m) >= {"macd", "signal_line", "histogram", "histogram_rising"}


def test_volume_and_breakout():
    closes = [100.0] * 80 + [100 + i for i in range(1, 6)]
    vols = [1000.0] * 80 + [3000.0] * 5
    b = tech.breakout(_bars(closes, vols))
    assert b["score"] == 100.0 and "broke above" in b["reading"]
    rising = [100 + (i % 2) * 2 + i * 0.1 for i in range(60)]
    vol = [2000.0 if i % 2 else 1000.0 for i in range(60)]
    assert tech.volume(_bars(rising, vol))["up_day_to_down_day_volume"] > 1.5


def test_one_off_quarter_is_left_out_of_trailing_profit():
    assert val.core_ttm([10.0, 12.0, 11.0, 13.0]) == (46.0, None)
    ttm, note = val.core_ttm([-6608.0, -5524.0, -5286.0, 51970.0])  # Vodafone Idea, March 2026
    assert round(ttm) == round((-6608 - 5524 - 5286) * 4 / 3) and "one-off" in note


def test_valuation_view_and_interpretation_follow_section_8():
    assert [val.view(s) for s in (70, 50, 30, None)] == ["CHEAP", "FAIR", "EXPENSIVE", None]
    assert val.INTERPRETATION[(False, "CHEAP")] == "possible value trap"
    assert val.INTERPRETATION[(True, "EXPENSIVE")] == "good business, poor entry price"


def test_own_history_and_sector_comparisons_score_cheaper_higher():
    hist = [(f"2024-0{i}-30", pe) for i, pe in enumerate([20, 22, 25, 28, 30, 32], 1)]
    cheap, dear = val._vs_history("PE", 19.0, hist), val._vs_history("PE", 40.0, hist)
    assert cheap["score"] == 100.0 and dear["score"] == 0.0 and cheap["median_pe"] == 26.5
    assert val._vs_history("PE", 20.0, hist[:3])["score"] is None
    assert val._vs_history("PE", None, hist)["score"] is None
    assert val._vs_sector("PE", 10.0, [12, 14, 16, 18, 20], "Banks")["score"] == 100.0


# ── Phase 8: Quality Momentum and sector rank ───────────────────────────────

from app.framework import momentum as mo, sector_rank
from app.framework.screener_series import _published_by


def test_results_count_only_once_published():
    assert not _published_by("2026-03-31", _date(2026, 5, 29), 60)  # annual results not yet due
    assert _published_by("2026-03-31", _date(2026, 5, 30), 60)
    assert _published_by("2026-06-30", _date(2026, 8, 14), 45) and not _published_by("2026-06-30", _date(2026, 8, 13), 45)
    assert _published_by("2026-06-30", None, 45)


def test_direction_follows_the_framework_examples():
    assert mo.direction(7.0, 15.0) == "IMPROVING"   # 39 -> 46 -> 54
    assert mo.direction(-11.0, -18.0) == "DECLINING"  # 72 -> 65 -> 54
    assert mo.direction(1.0, -2.0) == "STABLE"
    assert mo.direction(3.5, None) == "IMPROVING" and mo.direction(None, None) == "INSUFFICIENT_DATA"
    assert mo.direction(4.0, -6.0) == "DECLINING"  # a recent bounce does not hide a year-long fall


def test_point_in_time_metrics_use_published_statements_and_skip_one_off_quarters():
    s = _compounder()
    q = _quarters([100, 100, 100, 100], [20, 20, 20, 20], [10, 10, 10, 500])  # one-off gain in the last quarter
    m = mo.point_in_time_metrics(s, q)
    assert m["ebitda_margin"] == 20.0 and m["pat_margin"] == 10.0  # the 500 quarter is left out
    assert m["revenue_cagr_3y"] > 11 and m["latest_fy"] == "FY2025" and "roce" in m


def test_sector_rank_and_labels():
    rows = [(f"S{i}", "Pharma", float(q)) for i, q in enumerate([58, 70, 40, 65, 30, 52, 47, 61, 35, 44])]
    rows += [("X1", "Tiny", 90.0), ("N1", "Pharma", None)]
    r = sector_rank.ranks(rows)
    assert r["S1"]["rank"] == 1 and r["S1"]["of"] == 10 and r["S1"]["label"] == "Top 10%"
    assert r["S0"]["rank"] == 4 and r["S0"]["label"] == "Top 40%"
    assert "X1" not in r and "N1" not in r  # too few peers; no score


# ── Phase 9: decision engine ────────────────────────────────────────────────

from app.framework import decision as dec, explain as ex


def _s(q, **kw):
    base = {"quality": q, "fundamental": q, "technical": 55.0, "relative_strength": 55.0, "valuation_view": "FAIR",
            "trend": "STABLE", "quality_direction": "STABLE"}
    return {**base, **kw}


_TOP_RANK = {"rank": 2, "of": 30, "top_pct": 6.7, "label": "Top 10%", "sector": "X"}


def test_the_decision_matrix_rows():
    hc = dec.decide(_s(70, quality_direction="IMPROVING", relative_strength=65.0), {}, _TOP_RANK)
    assert (hc["classification"], hc["action"], hc["size"]) == ("Core Quality", "Add gradually", "High")
    assert hc["matrix"] == "Quality 65+ + Improving + Fair/Cheap"
    priority = dec.decide(_s(70, quality_direction="IMPROVING", valuation_view="CHEAP"), {}, _TOP_RANK)
    assert priority["matrix"] == "Strong quality + Cheap + improving trend"
    wait = dec.decide(_s(70, valuation_view="EXPENSIVE"), {}, _TOP_RANK)
    assert (wait["action"], wait["matrix"]) == ("Hold", "Quality 65+ + Expensive")
    timing = dec.decide(_s(70, technical=30.0), {}, _TOP_RANK)
    assert timing["matrix"] == "Quality 65+ + weak technical" and timing["action"] == "Add on confirmation"
    emerging = dec.decide(_s(55, quality_direction="IMPROVING"), {}, None)
    assert (emerging["classification"], emerging["action"]) == ("Investable", "Add gradually")
    recovery = dec.decide(_s(45, quality_direction="IMPROVING", relative_strength=65.0), {}, None)
    assert recovery["classification"] == "Recovery Candidate" and recovery["size"] == "Small"
    watch = dec.decide(_s(45, quality_direction="IMPROVING", relative_strength=40.0), {}, None)
    assert watch["classification"] == "Improving / Watch"
    replace = dec.decide(_s(45, quality_direction="DECLINING"), {}, None)
    assert (replace["classification"], replace["action"]) == ("Replacement Candidate", "Replace")
    avoid = dec.decide(_s(35, quality_direction="DECLINING"), {}, None)
    assert avoid["classification"] == "Avoid"


def test_strong_technicals_never_lift_a_weak_business_above_tactical():
    t = dec.decide(_s(30, technical=90.0, relative_strength=80.0), {"technical": {"components": {"moving_averages": {"sma50": 101.5}}}}, None)
    assert (t["classification"], t["size"]) == ("Tactical Only", "Tactical only")
    assert any("exit on" in w and "101.5" in w for w in t["why"])


def test_a_cheap_weak_business_is_flagged_as_a_possible_value_trap():
    d = dec.decide(_s(38, valuation_view="CHEAP"), {}, None)
    assert d["classification"] == "Replacement Candidate" and any("value trap" in w for w in d["why"])


def test_core_gate_red_flags():
    detail = {"quality": {"governance_red_flag": "promoter pledge (medium, 2026-06-30)"}}
    d = dec.decide(_s(80), detail, _TOP_RANK)
    assert d["classification"] == "Replacement Candidate" and "governance" in d["why"][0]
    weak_bs = {"fundamental": {"components": {"balance_sheet": {"score": 20.0}}}}
    assert dec.decide(_s(70), weak_bs, _TOP_RANK)["gates"]["red_flags"] == ["balance sheet weak (score 20)"]


def test_measured_quality_momentum_outranks_the_business_trend_label():
    assert dec.direction_of({}, "DECLINING", "STABLE") == "STABLE"
    assert dec.direction_of({}, "DECLINING", None) == "DECLINING"
    assert dec.direction_of({}, "IMPROVING", "INSUFFICIENT_DATA") == "IMPROVING"


def test_the_model_cannot_contradict_the_decision():
    d = {"classification": "Investable", "action": "Watch"}
    ok = {"summary": "Investable: the business passes the quality gate at 51.6 but quality fell 12.8 points, so watch."}
    assert ex._consistent(ok, d)
    assert not ex._consistent({"summary": "It is non-investable at present because its quality is falling fast."}, d)
    assert not ex._consistent({"summary": "Investable today, and it could be upgraded to investable later on."}, d)
    assert not ex._consistent({"summary": "This is really a Replacement Candidate rather than investable stock."}, d)
    assert not ex._consistent({"summary": "Quality is falling and the valuation is expensive at present."}, d)  # does not name it


def test_fallback_explanation_states_the_decision():
    p = {"decision": {"classification": "Core Quality", "action": "Hold", "size": "Small", "why": ["good business, wait for price"]},
         "interpretation": {"strong": ["profitability"], "weak": [], "performance": "behind the Nifty 50 by 5.0% over a year"},
         "red_flags": []}
    f = ex.fallback(p)
    assert f["summary"].startswith("Core Quality: hold, position size small.") and f["author"] == "rules"


# ── Phase 11: integrated report helpers ─────────────────────────────────────

def test_integrated_report_bands_and_figures():
    from app.reporting.integrated.build import band, facts
    assert [band(x) for x in (70, 55, 45, 35, 20, None)] == ["strong", "good", "borderline", "weak", "very weak", "—"]
    assert facts({"score": None, "reason": "no stored prices"}) == "no stored prices"
    line = facts({"score": 80.0, "weight": 0.1, "source": "x", "median_pct": 19.04, "years": 10, "by_window": {"6M": 85.2}})
    assert line == "median pct: 19.04 · years: 10 · by window: 6M 85.2"  # score, weight and source are shown in their own columns


# ── NSE MCP: corporate actions and price adjustment ─────────────────────────

def _nse_stock(db, symbol):
    from datetime import datetime, timezone
    from app.infrastructure.database.models import Stock
    now = datetime.now(timezone.utc)
    s = Stock(id=f"TEST:{symbol}", symbol=symbol, exchange="TEST", company_name=symbol, is_active=False, created_at=now, updated_at=now)
    db.add(s); db.flush()
    return s


def _action(db, stock, ex, purpose, kind, factor=1.0):
    from datetime import datetime, timezone
    from app.infrastructure.database.models import NseCorporateAction
    from app.nse_mcp.corporate_actions import dividend_in
    db.add(NseCorporateAction(stock_id=stock.id, ex_date=ex, purpose=purpose, action_type=kind, adjustment_factor=factor,
                              dividend_per_share=dividend_in(purpose), retrieved_at=datetime.now(timezone.utc)))
    db.flush()


def test_dividend_amount_is_read_from_nse_purpose_text():
    from app.nse_mcp.corporate_actions import dividend_in
    assert dividend_in("Annual General Meeting/Dividend - Rs 20 Per Share") == 20.0
    assert dividend_in("Interim Dividend - Rs 3 Per Share & Special Dividend - Re 1.50 Per Share") == 4.5
    assert dividend_in("Bonus 1:1") is None and dividend_in("Annual General Meeting") is None


def test_dividends_before_a_bonus_are_restated_and_bonus_years_found(db):
    from app.nse_mcp import corporate_actions as ca
    s = _nse_stock(db, "NSECA")
    today = _date(2026, 10, 6)
    _action(db, s, _date(2025, 11, 10), "Interim Dividend - Rs 10 Per Share", "DIVIDEND")
    _action(db, s, _date(2026, 1, 15), "Bonus 1:1", "BONUS", 0.5)
    _action(db, s, _date(2026, 7, 20), "Dividend - Rs 6 Per Share", "DIVIDEND")
    _action(db, s, _date(2024, 7, 20), "Dividend - Rs 9 Per Share", "DIVIDEND")  # more than a year ago
    actions = ca.for_stock(db, s.id)
    assert ca.split_or_bonus_financial_years(actions) == {"FY2026": "Bonus 1:1 (2026-01-15)"}
    d = ca.dividends_last_12_months(actions, today)
    assert d["per_share"] == 11.0  # 10 before a 1:1 bonus counts as 5, plus 6
    assert len(d["payments"]) == 2


def test_nse_confirms_a_bonus_year_and_supplies_the_dividend(db):
    s = _nse_stock(db, "NSEDIV")
    _action(db, s, _date(2025, 9, 23), "Bonus 1:1", "BONUS", 0.5)
    _action(db, s, _date.today() - _td(days=60), "Dividend - Rs 8 Per Share", "DIVIDEND")
    # share count doubles in FY2026 AND equity jumps: the heuristic alone would call this a share sale
    fd = _fd({"FY2025": 100.0, "FY2026": 110.0}, {"FY2025": 10.0, "FY2026": 5.5}, {"FY2025": 500.0, "FY2026": 1500.0},
             {"dividend_rate": 99.0, "shares_outstanding": 20.0, "trailing_eps": 20.0})
    dil = inputs.share_dilution(fd, db, s.id)
    assert dil["split_or_bonus_years"] == ["FY2026"] and "NSE: Bonus 1:1" in dil["confirmed_by"]["FY2026"]
    div = inputs.dividend_sustainability(fd, {"fcf_latest": 400.0}, False, db, s.id)
    assert div["dividend_per_share"] == 8.0 and div["payout_pct"] == 40.0 and "NSE" in div["basis"]
    # NSE read, nothing paid in a year: not scored, whatever Yahoo's stale rate says
    quiet = _nse_stock(db, "NSEQUIET")
    _action(db, quiet, _date(2023, 7, 1), "Dividend - Rs 2 Per Share", "DIVIDEND")
    assert inputs.dividend_sustainability(fd, {}, False, db, quiet.id)["score"] is None


def test_nse_prices_are_adjusted_backwards_for_bonus_and_dividend(db):
    from app.nse_mcp import corporate_actions as ca, history
    s = _nse_stock(db, "NSEADJ")
    _action(db, s, _date(2026, 1, 5), "Bonus 1:1", "BONUS", 0.5)
    _action(db, s, _date(2026, 1, 7), "Dividend - Rs 5 Per Share", "DIVIDEND")
    raw = [{"date": "2026-01-02", "open": 200, "high": 200, "low": 200, "close": 200.0, "volume": 1000},
           {"date": "2026-01-05", "open": 100, "high": 100, "low": 100, "close": 100.0, "volume": 2000},   # ex-bonus
           {"date": "2026-01-06", "open": 100, "high": 100, "low": 100, "close": 100.0, "volume": 2000},
           {"date": "2026-01-07", "open": 95, "high": 95, "low": 95, "close": 95.0, "volume": 2000}]       # ex-dividend
    rows = history.adjust(s.id, raw, ca.for_stock(db, s.id))
    assert [r["close"] for r in rows] == [100.0, 100.0, 100.0, 95.0]          # the bonus is not a 50% crash
    assert [round(r["adj_close"], 2) for r in rows] == [95.0, 95.0, 95.0, 95.0]  # nor is the dividend a 5% fall
    assert rows[0]["volume"] == 2000  # pre-bonus volume restated to today's share count


def test_adjustment_factor_is_read_from_nse_wording():
    from app.nse_mcp.corporate_actions import classify
    assert classify("Bonus 1:1") == ("BONUS", 0.5)
    assert classify("Bonus 2:1") == ("BONUS", 1 / 3)       # two new for each held
    assert classify("Bonus issue 1:5")[1] == 5 / 6
    assert classify("Face Value Split (Sub-Division) - From Rs 10/- Per Share To Rs 2/- Per Share") == ("SPLIT", 0.2)
    assert classify("Face Value Split (Sub-Division) - From Re 1/- Per Share To Re 0.50/- Per Share")[1] == 0.5
    assert classify("Interim Dividend - Rs 7 Per Share") == ("DIVIDEND", 1.0)
    assert classify("Annual General Meeting") == ("OTHER", 1.0)
    assert classify("Bonus Debentures 1:1")[0] != "BONUS"  # not a change in the share count



def test_falling_returns_and_margins_pull_profitability_down():
    from app.calculations.scoring import _profitability_score, compute_scores, profitability_direction, _PROFITABILITY_WEIGHTS
    level = {"ebitda_margin": 34.0, "pat_margin": 25.0, "roe": 31.0, "roce": 48.0}
    base = _profitability_score(level)
    falling = {**level, "ebitda_margin_trend": "DETERIORATING", "pat_margin_trend": "STABLE",
               "roe_trend": "STRONGLY_DETERIORATING", "roce_trend": "STRONGLY_DETERIORATING"}  # Sigma Solve's labels
    d = profitability_direction(falling, _PROFITABILITY_WEIGHTS)
    assert d["adjustment"] == -12.0 and d["signals"]["roce"] == "STRONGLY_DETERIORATING"
    assert _profitability_score(falling) == base - 12.0
    rising = {**level, **{f"{k}_trend": "IMPROVING" for k in level}}
    assert _profitability_score(rising) == min(100.0, base + 4.0)
    assert _profitability_score(level) == base  # no labels, no change
    out = compute_scores({**falling, "revenue_cagr_3y": 20.0}, sector="IT Services")
    assert out["profitability_direction"]["adjustment"] == -12.0
