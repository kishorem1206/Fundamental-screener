"""Deterministic P&L calculation engine — P&L Analysis System, Stage P1.

Reads the 12-year `pnl_*` and balance-sheet ledger rows (`app/ingestion/
pnl_history_client.py`, `screener_client.py::ingest_balance_sheet`, Stage
P0) plus `ValuationHistory` (real historical price/P-E/P-B, also wired up
in Stage P0) and computes every ratio, CAGR, trend, flag and score the P&L
doc's sections 4-32 ask for — pure Python arithmetic, no LLM anywhere in
this file. `app/interpretation/`'s local-Llama pipeline (Stage P2) will
consume this module's output; it never recomputes any of it.

Two things the source doc assumes are genuinely not available and are
returned as explicit `not_available` blocks rather than faked (confirmed
by live-probing Screener.in on 2026-09-13, see `pnl_history_client.py`'s
module docstring): a material/employee/power-fuel expense breakdown, and
Buffett's $1 Test (needs historical market cap, which needs historical
share count across splits/buybacks — a harder problem than this stage
takes on).
"""
from __future__ import annotations

import statistics

from sqlalchemy.orm import Session

from app.calculations.engine import calculate_cagr, safe_div, trend_direction
from app.infrastructure.database import metric_store
from app.infrastructure.database.models import ValuationHistory

# ── Configurable thresholds (doc explicitly asks for these to be
# configurable, not hardcoded inline throughout the module) ────────────────
_INTEREST_COVERAGE_STRONG = 6.0
_INTEREST_COVERAGE_ADEQUATE = 3.0
_INTEREST_COVERAGE_WEAK = 1.0
_OTHER_INCOME_DEPENDENCY_PCT = 25.0  # other_income / PBT past this = flagged
_MARGIN_INFLECTION_PP = 3.0  # percentage-point swing YoY that counts as an inflection
_GROWTH_INFLECTION_PP = 15.0  # percentage-point swing YoY in growth rate
_MARGIN_TOLERANCE_PP = 1.0  # within this of the historical average = "stable"

# Same set orchestrator.py::_run_ai_analysis already uses for the identical
# reason (banking.md's own hierarchy, section 21): "interest" in a bank's
# P&L is the structural cost of deposits/borrowings, not discretionary debt
# service the way it is for an industrial company — (PBT+Interest)/Interest
# naturally comes out low for every bank, always, by the nature of the
# business, not as a leverage-risk signal. Real bug found live-testing HDFC
# Bank (2026-09-13): it was flagged HIGH_INTEREST_BURDEN purely from this
# structural effect. The raw ratio is still computed/shown; only the
# red-flag/quality-score interpretation of it is sector-gated.
_FINANCIAL_SECTORS = {"Banks", "NBFCs", "Housing Finance", "Microfinance", "Gold Loans", "Insurance"}


# ── Series helpers (period-keyed dicts, ISO dates + the literal "TTM") ─────

def _series(db: Session, company_id: str, metric_key: str, statement_type: str = "CONSOLIDATED") -> dict[str, float]:
    """{period: authoritative_value} for every period on record, "TTM"
    included if present. Resolves conflicts the same way every other reader
    in this app does (metric_store.get_authoritative_value).

    Defaults to statement_type="CONSOLIDATED" — `pnl_history_client.py`
    switched to storing consolidated figures under that tag (2026-09-15),
    matching what MetricsCalculator already gets from yfinance elsewhere in
    the app. `compute_pnl_analysis()` resolves the actual statement_type to
    use once (falling back to STANDALONE when CONSOLIDATED has no data —
    see its own docstring) and passes it explicitly on every call; no other
    caller in this file overrides the default."""
    history = metric_store.get_metric_history(db, company_id, metric_key, statement_type=statement_type)
    periods = sorted({row.period for row in history})
    out = {}
    for period in periods:
        winner, _ = metric_store.get_authoritative_value(db, company_id, metric_key, period, statement_type=statement_type)
        if winner is not None and winner.value is not None:
            out[period] = float(winner.value)
    return out


def _fiscal_only(series: dict[str, float]) -> dict[str, float]:
    return {k: v for k, v in series.items() if k != "TTM"}


def _sorted_items(series: dict[str, float]) -> list[tuple[str, float]]:
    return sorted(series.items())


def _cagr_window(series: dict[str, float], n_years: int) -> float | None:
    """CAGR over the most recent `n_years` fiscal years on record (fewer if
    that much history isn't available yet)."""
    items = _sorted_items(_fiscal_only(series))
    if len(items) < 2:
        return None
    window = items[-(n_years + 1):] if len(items) > n_years else items
    values = [v for _, v in window]
    return calculate_cagr(values, len(values) - 1)


def _cagr_windows(series: dict[str, float]) -> dict[str, float | None]:
    return {
        "10y": _cagr_window(series, 10),
        "7y": _cagr_window(series, 7),
        "5y": _cagr_window(series, 5),
        "3y": _cagr_window(series, 3),
    }


def _ttm_growth(series: dict[str, float]) -> float | None:
    """TTM vs. the latest completed fiscal year — never mixed into a
    fixed-year CAGR window (see pnl_history_client.py's module docstring)."""
    ttm = series.get("TTM")
    fiscal = _sorted_items(_fiscal_only(series))
    if ttm is None or not fiscal:
        return None
    latest_fy_value = fiscal[-1][1]
    if not latest_fy_value:
        return None
    return round((ttm - latest_fy_value) / latest_fy_value * 100, 2)


def _yoy_series(series: dict[str, float]) -> dict[str, float | None]:
    """Year-over-year % growth for every fiscal year that has a prior year
    to compare against. Excludes TTM (that's `_ttm_growth`'s job)."""
    items = _sorted_items(_fiscal_only(series))
    out = {}
    for (prev_period, prev_val), (curr_period, curr_val) in zip(items, items[1:]):
        if prev_val:
            out[curr_period] = round((curr_val - prev_val) / prev_val * 100, 2)
    return out


def _avg_recent(series: dict[str, float], n: int) -> float | None:
    items = _sorted_items(_fiscal_only(series))
    if not items:
        return None
    recent = items[-n:] if len(items) >= n else items
    vals = [v for _, v in recent]
    return round(sum(vals) / len(vals), 2) if vals else None


def _margin_stats(series: dict[str, float]) -> dict:
    items = _sorted_items(_fiscal_only(series))
    vals = [v for _, v in items]
    if not vals:
        return {"current": None, "avg_10y": None, "avg_7y": None, "avg_5y": None, "avg_3y": None,
                "peak": None, "trough": None, "vs_10y_avg": None, "vs_5y_avg": None, "trend": "INSUFFICIENT_DATA"}
    current = vals[-1]
    avg_10y, avg_5y = _avg_recent(series, 10), _avg_recent(series, 5)
    return {
        "current": current,
        "avg_10y": avg_10y,
        "avg_7y": _avg_recent(series, 7),
        "avg_5y": avg_5y,
        "avg_3y": _avg_recent(series, 3),
        "peak": round(max(vals), 2),
        "trough": round(min(vals), 2),
        "vs_10y_avg": round(current - avg_10y, 2) if avg_10y is not None else None,
        "vs_5y_avg": round(current - avg_5y, 2) if avg_5y is not None else None,
        "trend": trend_direction(vals),
    }


def _long_vs_short_trend(cagr_windows: dict[str, float | None]) -> str:
    """Doc section 8's specific rule — distinct from engine.py's regression-
    based trend_direction(), which classifies a raw value series rather than
    comparing CAGR windows against each other."""
    c3, c5, c10 = cagr_windows.get("3y"), cagr_windows.get("5y"), cagr_windows.get("10y")
    if c3 is None or c5 is None or c10 is None:
        return "INSUFFICIENT_DATA"
    if c3 > c5 > c10:
        return "IMPROVING"
    if c3 < c5 < c10:
        return "MODERATING"
    if max(c3, c5, c10) - min(c3, c5, c10) <= 3.0:
        return "STABLE"
    return "VOLATILE"


def _direction(a: float | None, b: float | None, tolerance_pp: float = 2.0) -> str:
    """"a" relative to "b" — e.g. profit CAGR vs sales CAGR. Computed here,
    not left to the LLM: real bug found 2026-09-13 testing Maruti — the
    3B model was handed sales_cagr=21.11 and profit_cagr=27.84 (both
    correctly grounded, real numbers) and still wrote "profit growth is
    SLOWER than sales growth," the exact opposite of what the numbers show.
    A direct numeric comparison is exactly the kind of "primary calculation"
    the doc says Llama must never be responsible for — this was already a
    gap in the original design, not a new rule."""
    if a is None or b is None:
        return "INSUFFICIENT_DATA"
    if a > b + tolerance_pp:
        return "FASTER"
    if a < b - tolerance_pp:
        return "SLOWER"
    return "ROUGHLY_IN_LINE"


def _consistency_stats(yoy: dict[str, float | None], level_series: dict[str, float]) -> dict:
    growth_vals = [v for v in yoy.values() if v is not None]
    levels = [v for _, v in _sorted_items(_fiscal_only(level_series))]
    negative_years = sum(1 for v in growth_vals if v < 0)
    stdev = round(statistics.stdev(growth_vals), 2) if len(growth_vals) >= 2 else None
    max_drawdown = None
    if levels:
        peak = levels[0]
        worst = 0.0
        for v in levels:
            peak = max(peak, v)
            if peak > 0:
                worst = min(worst, (v - peak) / peak * 100)
        max_drawdown = round(worst, 2)
    return {
        "negative_growth_years": negative_years,
        "total_years": len(growth_vals),
        "growth_stdev": stdev,
        "max_drawdown_pct": max_drawdown,
    }


def _interest_coverage(pbt_series: dict, interest_series: dict, is_financial: bool = False) -> dict:
    items = []
    for period, pbt in _fiscal_only(pbt_series).items():
        interest = interest_series.get(period)
        if interest and interest > 0:
            items.append((period, round((pbt + interest) / interest, 2)))
    items.sort()
    latest = items[-1][1] if items else None
    # `tier` (STRONG/ADEQUATE/WEAK/NEGATIVE_UNSAFE) is a leverage-risk
    # judgment call that's structurally meaningless for a bank/NBFC — see
    # _FINANCIAL_SECTORS's comment. Real bug found 2026-09-13: an earlier
    # fix gated the tier out of red-flag/quality-score logic but left it
    # computed here regardless, so the pnl_earnings_quality prompt (told
    # "a null tier means don't discuss interest burden") still received a
    # real WEAK/STRONG tier for every bank and discussed it anyway. `tier`
    # is genuinely None for a financial-sector company now — `latest`/
    # `by_year` (the raw ratio) stay populated, only the qualitative label
    # is suppressed.
    tier = None
    if latest is not None and not is_financial:
        if latest >= _INTEREST_COVERAGE_STRONG:
            tier = "STRONG"
        elif latest >= _INTEREST_COVERAGE_ADEQUATE:
            tier = "ADEQUATE"
        elif latest >= _INTEREST_COVERAGE_WEAK:
            tier = "WEAK"
        else:
            tier = "NEGATIVE_UNSAFE"
    return {"by_year": dict(items), "latest": latest, "tier": tier}


def _other_income_dependency(other_income_series: dict, pbt_series: dict, is_financial: bool = False) -> dict:
    """The ratio is always computed/shown; `flagged` is sector-gated — a
    bank's "other income" (fee income, treasury gains) is normally a large,
    structural share of PBT since Screener's bank-specific "financing
    profit" (this module's operating_profit equivalent) excludes it by
    definition, not because the bank is unusually reliant on one-off items
    the way an industrial company flagged here would be. Same sector-
    mismatch class of issue as interest coverage above."""
    fiscal_oi, fiscal_pbt = _fiscal_only(other_income_series), _fiscal_only(pbt_series)
    latest_period = max(fiscal_pbt) if fiscal_pbt else None
    if latest_period is None or latest_period not in fiscal_oi:
        return {"latest_ratio_pct": None, "flagged": False}
    pbt = fiscal_pbt[latest_period]
    ratio = round(fiscal_oi[latest_period] / pbt * 100, 2) if pbt else None
    flagged = bool(ratio and ratio >= _OTHER_INCOME_DEPENDENCY_PCT) and not is_financial
    return {"latest_ratio_pct": ratio, "flagged": flagged}


def _depreciation_trend(dep_series: dict, sales_series: dict, opex_profit_series: dict) -> dict:
    fiscal_dep = _fiscal_only(dep_series)
    latest_period = max(fiscal_dep) if fiscal_dep else None
    if latest_period is None:
        return {"dep_to_sales_pct": None, "dep_to_opex_profit_pct": None, "yoy_growth_pct": None, "trend": "INSUFFICIENT_DATA"}
    dep_to_sales = safe_div(fiscal_dep[latest_period], _fiscal_only(sales_series).get(latest_period))
    dep_to_op = safe_div(fiscal_dep[latest_period], _fiscal_only(opex_profit_series).get(latest_period))
    yoy = _yoy_series(dep_series)
    return {
        "dep_to_sales_pct": round(dep_to_sales * 100, 2) if dep_to_sales is not None else None,
        "dep_to_opex_profit_pct": round(dep_to_op * 100, 2) if dep_to_op is not None else None,
        "yoy_growth_pct": yoy.get(latest_period),
        "trend": trend_direction([v for _, v in _sorted_items(fiscal_dep)]),
    }


def _roe_series(net_profit_series: dict, equity_capital_series: dict, reserves_series: dict) -> dict:
    """ROE = Net Profit / Average Shareholders' Equity (doc section 20).
    Shareholders' equity = equity_capital + reserves, from Screener's
    balance sheet (already ingested for every sector, Stage P0)."""
    equity_by_period = {}
    for period, ec in _fiscal_only(equity_capital_series).items():
        reserves = reserves_series.get(period)
        if reserves is not None:
            equity_by_period[period] = ec + reserves

    items = sorted(equity_by_period.items())
    roe_by_year = {}
    for (prev_p, prev_e), (curr_p, curr_e) in zip(items, items[1:]):
        net_profit = _fiscal_only(net_profit_series).get(curr_p)
        avg_equity = (prev_e + curr_e) / 2
        if net_profit is not None and avg_equity:
            roe_by_year[curr_p] = round(net_profit / avg_equity * 100, 2)

    vals_sorted = [v for _, v in sorted(roe_by_year.items())]
    return {
        "by_year": roe_by_year,
        "latest": vals_sorted[-1] if vals_sorted else None,
        "avg_10y": round(sum(vals_sorted[-10:]) / len(vals_sorted[-10:]), 2) if vals_sorted else None,
        "avg_5y": round(sum(vals_sorted[-5:]) / len(vals_sorted[-5:]), 2) if vals_sorted else None,
        "avg_3y": round(sum(vals_sorted[-3:]) / len(vals_sorted[-3:]), 2) if vals_sorted else None,
        "trend": trend_direction(vals_sorted),
    }


def _dividend_and_retention(net_profit_series: dict, payout_series: dict) -> dict:
    fiscal_np, fiscal_payout = _fiscal_only(net_profit_series), _fiscal_only(payout_series)
    cumulative_retained = 0.0
    have_data = False
    for period, net_profit in fiscal_np.items():
        payout_pct = fiscal_payout.get(period)
        if payout_pct is None:
            continue
        have_data = True
        retention_pct = max(0.0, 100.0 - payout_pct)
        cumulative_retained += net_profit * (retention_pct / 100.0)
    payout_vals = list(fiscal_payout.values())
    latest_period = max(fiscal_payout) if fiscal_payout else None
    return {
        "latest_payout_pct": fiscal_payout.get(latest_period) if latest_period else None,
        "avg_3y_payout_pct": _avg_recent(payout_series, 3),
        "avg_5y_payout_pct": _avg_recent(payout_series, 5),
        "avg_10y_payout_pct": _avg_recent(payout_series, 10),
        "payout_volatility": round(statistics.stdev(payout_vals), 2) if len(payout_vals) >= 2 else None,
        "cumulative_retained_earnings": round(cumulative_retained, 2) if have_data else None,
    }


def _inflection_points(sales_yoy: dict, opm_series: dict) -> list[dict]:
    points = []
    sales_items = sorted(sales_yoy.items())
    for (prev_p, prev_g), (curr_p, curr_g) in zip(sales_items, sales_items[1:]):
        if prev_g is None or curr_g is None:
            continue
        delta = curr_g - prev_g
        if abs(delta) >= _GROWTH_INFLECTION_PP:
            points.append({
                "year": curr_p,
                "type": "revenue_growth_acceleration" if delta > 0 else "revenue_growth_deceleration",
                "metric": "sales_growth",
                "observation": f"YoY sales growth moved from {prev_g}% to {curr_g}% ({delta:+.1f}pp)",
                "severity": "high" if abs(delta) >= _GROWTH_INFLECTION_PP * 1.5 else "medium",
            })
    opm_items = sorted(_fiscal_only(opm_series).items())
    for (prev_p, prev_m), (curr_p, curr_m) in zip(opm_items, opm_items[1:]):
        delta = curr_m - prev_m
        if abs(delta) >= _MARGIN_INFLECTION_PP:
            points.append({
                "year": curr_p,
                "type": "margin_expansion" if delta > 0 else "margin_compression",
                "metric": "OPM",
                "observation": f"OPM moved from {prev_m}% to {curr_m}% ({delta:+.1f}pp)",
                "severity": "high" if abs(delta) >= _MARGIN_INFLECTION_PP * 2 else "medium",
            })
    return sorted(points, key=lambda p: p["year"])


def _red_flags_and_signals(
    sales_cagr: dict, profit_cagr: dict, opm_stats: dict, consistency: dict,
    interest_cov: dict, other_income: dict, dep_trend: dict, roe: dict,
    is_financial: bool = False,
) -> tuple[list[str], list[str]]:
    red_flags, signals = [], []

    if sales_cagr.get("3y") is not None and sales_cagr.get("10y") is not None:
        if sales_cagr["3y"] < sales_cagr["10y"] - 3:
            red_flags.append("DECLINING_SALES_GROWTH")
        elif sales_cagr["3y"] > sales_cagr["10y"] + 3:
            signals.append("ACCELERATING_SALES_GROWTH")
    if sales_cagr.get("3y") is not None and sales_cagr["3y"] < 0:
        red_flags.append("NEGATIVE_SALES_GROWTH")
    if consistency.get("growth_stdev") is not None and consistency["growth_stdev"] > 20:
        red_flags.append("HIGH_GROWTH_VOLATILITY")
    if profit_cagr.get("5y") is not None and sales_cagr.get("5y") is not None:
        if profit_cagr["5y"] < sales_cagr["5y"]:
            red_flags.append("PROFIT_GROWTH_BELOW_SALES_GROWTH")
        else:
            signals.append("PROFIT_GROWTH_ABOVE_SALES_GROWTH")

    if opm_stats.get("vs_5y_avg") is not None:
        if opm_stats["vs_5y_avg"] < -2:
            red_flags.append("MARGIN_COMPRESSION")
        elif opm_stats["vs_5y_avg"] > 2:
            signals.append("EXPANDING_OPM")
    if opm_stats.get("current") is not None and opm_stats.get("trough") is not None:
        if opm_stats["current"] <= opm_stats["trough"] + 0.5:
            red_flags.append("LOWEST_HISTORICAL_MARGIN")
    if opm_stats.get("trend") == "STABLE":
        signals.append("STABLE_MARGINS")

    # Interest coverage isn't a leverage-risk signal for a bank/NBFC —
    # "interest" there is the structural cost of deposits/borrowings, not
    # discretionary debt service, so it's naturally low for every company
    # in this sector group, always. See _FINANCIAL_SECTORS's comment.
    if not is_financial:
        if interest_cov.get("tier") in ("STRONG",):
            signals.append("HIGH_INTEREST_COVERAGE")
        elif interest_cov.get("tier") in ("WEAK", "NEGATIVE_UNSAFE"):
            red_flags.append("HIGH_INTEREST_BURDEN")

    if other_income.get("flagged"):
        red_flags.append("HIGH_OTHER_INCOME_DEPENDENCY")

    if dep_trend.get("trend") == "DETERIORATING":
        red_flags.append("RISING_DEPRECIATION_BURDEN")

    if roe.get("latest") is not None and roe["latest"] >= 18:
        signals.append("HIGH_ROE")

    if consistency.get("negative_growth_years", 0) == 0 and consistency.get("total_years", 0) >= 5:
        signals.append("CONSISTENT_SALES_GROWTH")
        signals.append("POSITIVE_EARNINGS_CONSISTENCY")

    return red_flags, signals


def _quality_score(sales_cagr, profit_cagr, consistency, opm_stats, roe, interest_cov, is_financial: bool = False) -> dict:
    """Deterministic weighted sub-scores, 0-10 each (doc section 32) — Llama
    explains this score, it never assigns it."""
    def _scale(value, lo, hi):
        if value is None:
            return 5.0  # neutral, not zero — absence of data isn't a penalty
        return max(0.0, min(10.0, (value - lo) / (hi - lo) * 10))

    sales_growth = _scale(sales_cagr.get("5y"), 0, 20)
    profit_growth = _scale(profit_cagr.get("5y"), 0, 20)
    growth_consistency = _scale(
        10 - (consistency.get("negative_growth_years", 0) * 2), 0, 10
    ) if consistency.get("total_years") else 5.0
    operating_margins = _scale(opm_stats.get("current"), 0, 30)
    profit_conversion = _scale(
        (profit_cagr.get("5y") - sales_cagr.get("5y")) if profit_cagr.get("5y") is not None and sales_cagr.get("5y") is not None else None,
        -5, 10,
    )
    earnings_quality = 10.0
    if not is_financial:
        if interest_cov.get("tier") == "WEAK":
            earnings_quality -= 3
        elif interest_cov.get("tier") == "NEGATIVE_UNSAFE":
            earnings_quality -= 6
    earnings_quality = max(0.0, earnings_quality)

    sub_scores = {
        "sales_growth": round(sales_growth, 1),
        "profit_growth": round(profit_growth, 1),
        "growth_consistency": round(growth_consistency, 1),
        "operating_margins": round(operating_margins, 1),
        "profit_conversion": round(profit_conversion, 1),
        "earnings_quality": round(earnings_quality, 1),
    }
    overall = round(sum(sub_scores.values()) / len(sub_scores), 1)
    return {"sub_scores": sub_scores, "overall": overall}


def _stock_price_cagr(db: Session, company_id: str) -> dict:
    rows = (
        db.query(ValuationHistory)
        .filter_by(company_id=company_id)
        .order_by(ValuationHistory.period_end)
        .all()
    )
    priced = [(r.period_end, float(r.price)) for r in rows if r.price is not None]
    if len(priced) < 2:
        return {"10y": None, "5y": None, "3y": None, "1y": None, "years_of_data": len(priced)}

    def _window(n):
        w = priced[-(n + 1):] if len(priced) > n else priced
        vals = [v for _, v in w]
        return calculate_cagr(vals, len(vals) - 1)

    return {"10y": _window(10), "5y": _window(5), "3y": _window(3), "1y": _window(1), "years_of_data": len(priced)}


# ── Public entry point ──────────────────────────────────────────────────────

def compute_pnl_analysis(db: Session, company_id: str, sector_name: str | None = None) -> dict:
    """Full deterministic P&L analysis object for one company. Never raises
    — a company with no pnl_* ledger data yet (ingestion hasn't run, or
    failed) gets back a mostly-None/insufficient-data structure rather than
    an exception, matching every other calculation path's contract.
    `sector_name` gates the interest-coverage flag/score interpretation for
    banks/NBFCs/etc — see _FINANCIAL_SECTORS's comment.

    Resolves CONSOLIDATED vs STANDALONE once, up front, falling back to
    STANDALONE when CONSOLIDATED has no `pnl_sales` data — real gap found
    live on both Tata Technologies and Coforge (Screener's CONSOLIDATED
    P&L schedule ingestion occasionally doesn't complete for a company,
    same class of transient scrape-target gap as the cash-flow-schedules
    case), and this function had NO fallback at all before, unlike
    `pl_intelligence/__init__.py::compute_pl_intelligence()`'s own
    `allow_fallback` — mirrors that fix here since
    `screener_metrics_override.py` depends on this function too."""
    is_financial = sector_name in _FINANCIAL_SECTORS
    statement_type = "CONSOLIDATED"
    if not _series(db, company_id, "pnl_sales", statement_type):
        statement_type = "STANDALONE"

    sales = _series(db, company_id, "pnl_sales", statement_type)
    expenses = _series(db, company_id, "pnl_expenses", statement_type)
    operating_profit = _series(db, company_id, "pnl_operating_profit", statement_type)
    opm = _series(db, company_id, "pnl_opm", statement_type)
    other_income = _series(db, company_id, "pnl_other_income", statement_type)
    interest = _series(db, company_id, "pnl_interest", statement_type)
    depreciation = _series(db, company_id, "pnl_depreciation", statement_type)
    pbt = _series(db, company_id, "pnl_pbt", statement_type)
    net_profit = _series(db, company_id, "pnl_net_profit", statement_type)
    eps = _series(db, company_id, "pnl_eps", statement_type)
    dividend_payout = _series(db, company_id, "pnl_dividend_payout", statement_type)
    equity_capital = _series(db, company_id, "equity_capital", statement_type)
    reserves = _series(db, company_id, "reserves", statement_type)

    sales_cagr = _cagr_windows(sales)
    profit_cagr = _cagr_windows(net_profit)
    pbt_cagr = _cagr_windows(pbt)
    eps_cagr = _cagr_windows(eps)

    sales_yoy = _yoy_series(sales)
    pbt_yoy = _yoy_series(pbt)
    net_profit_yoy = _yoy_series(net_profit)
    eps_yoy = _yoy_series(eps)

    opm_stats = _margin_stats(opm)
    pbt_margin = calc_margin_series(pbt, sales)
    npm = calc_margin_series(net_profit, sales)
    pbt_margin_stats = _margin_stats(pbt_margin)
    npm_stats = _margin_stats(npm)

    consistency = _consistency_stats(sales_yoy, sales)
    interest_cov = _interest_coverage(pbt, interest, is_financial=is_financial)
    oi_dependency = _other_income_dependency(other_income, pbt, is_financial=is_financial)
    dep_trend = _depreciation_trend(depreciation, sales, operating_profit)
    roe = _roe_series(net_profit, equity_capital, reserves)
    dividend = _dividend_and_retention(net_profit, dividend_payout)
    inflections = _inflection_points(sales_yoy, opm)
    red_flags, signals = _red_flags_and_signals(
        sales_cagr, profit_cagr, opm_stats, consistency, interest_cov, oi_dependency, dep_trend, roe,
        is_financial=is_financial,
    )
    quality = _quality_score(sales_cagr, profit_cagr, consistency, opm_stats, roe, interest_cov, is_financial=is_financial)
    stock_price_cagr = _stock_price_cagr(db, company_id)

    fiscal_years = sorted(_fiscal_only(sales).keys())

    return {
        "years_of_data": len(fiscal_years),
        "is_financial_sector": is_financial,
        "statement_type": statement_type,
        "fiscal_years": fiscal_years,
        "table": {
            "sales": sales, "expenses": expenses, "operating_profit": operating_profit,
            "opm": opm, "other_income": other_income, "interest": interest,
            "depreciation": depreciation, "pbt": pbt, "net_profit": net_profit,
            "eps": eps, "dividend_payout": dividend_payout,
        },
        "growth": {
            "sales_cagr": sales_cagr, "sales_ttm_growth": _ttm_growth(sales), "sales_yoy": sales_yoy,
            "pbt_cagr": pbt_cagr, "pbt_yoy": pbt_yoy,
            "profit_cagr": profit_cagr, "profit_ttm_growth": _ttm_growth(net_profit), "profit_yoy": net_profit_yoy,
            "eps_cagr": eps_cagr, "eps_yoy": eps_yoy,
            "long_vs_short_trend": _long_vs_short_trend(sales_cagr),
            "profit_vs_sales_direction_5y": _direction(profit_cagr.get("5y"), sales_cagr.get("5y")),
            "eps_vs_profit_direction_5y": _direction(eps_cagr.get("5y"), profit_cagr.get("5y")),
        },
        "margins": {"opm": opm_stats, "pbt_margin": pbt_margin_stats, "npm": npm_stats},
        "consistency": consistency,
        "interest_coverage": interest_cov,
        "other_income_dependency": oi_dependency,
        "depreciation": dep_trend,
        "roe": roe,
        "dividend": dividend,
        "stock_price_cagr": stock_price_cagr,
        "inflection_points": inflections,
        "red_flags": red_flags,
        "positive_signals": signals,
        "quality_score": quality,
        "expense_structure": {"not_available": True, "reason": "Screener.in's standard P&L view has no material/employee/power-fuel breakdown for any sector checked"},
        "buffetts_dollar_test": {"not_available": True, "reason": "requires historical market cap across share-count changes — not built this rollout"},
    }


def calc_margin_series(numerator: dict, denominator: dict) -> dict[str, float]:
    out = {}
    for period, num in numerator.items():
        den = denominator.get(period)
        if den:
            out[period] = round(num / den * 100, 2)
    return out
