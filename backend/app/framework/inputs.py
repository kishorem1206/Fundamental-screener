"""The four Fundamental Score inputs the older category scores did not cover
(share dilution, dividend sustainability, earnings consistency, working-capital
trend) and the "double in" measure. Framework section 4.

Every function returns a dict with `score` (0-100, or None when the measure
does not apply or cannot be computed — a missing input is left out of the
weighted score, never counted as 50) and the figures behind it.
"""
from __future__ import annotations

import math

from sqlalchemy.orm import Session

from app.calculations.scoring import _score_metric

_TREND_SCORE = {
    "STRONGLY_IMPROVING": 95.0, "IMPROVING": 80.0, "STABLE": 65.0, "VOLATILE": 45.0,
    "DETERIORATING": 30.0, "STRONGLY_DETERIORATING": 10.0,
}
# share count growth per year, % — a shrinking count (buyback) scores best
_DILUTION = [(-2, 100), (0, 92), (1, 78), (3, 55), (5, 35), (10, 12), (20, 0)]
_PAYOUT = [(0, 70), (20, 95), (50, 95), (70, 75), (90, 45), (100, 25), (150, 5)]
_FCF_COVER = [(0, 5), (0.7, 30), (1.0, 55), (1.5, 80), (2.5, 100)]


def _years(series: dict | None) -> list[str]:
    return sorted(k for k, v in (series or {}).items() if v is not None)


def share_dilution(financial_data: dict) -> dict:
    """Yearly growth in the share count, derived as net profit / basic EPS for
    each reported year. A jump that came with no matching rise in equity is a
    split or bonus issue, not dilution, and that year is left out."""
    income, balance = financial_data.get("income") or {}, financial_data.get("balance") or {}
    profit, eps, equity = income.get("net_income") or {}, income.get("basic_eps") or {}, balance.get("total_equity") or {}
    shares = {}
    for fy in _years(profit):
        if eps.get(fy) and profit[fy] / eps[fy] > 0:
            shares[fy] = profit[fy] / eps[fy]
    years = sorted(shares)
    if len(years) < 2:
        return {"score": None, "reason": "fewer than two years of profit and EPS"}
    steps, skipped = [], []
    for prev, cur in zip(years, years[1:]):
        change = shares[cur] / shares[prev] - 1
        if abs(change) > 0.25 and equity.get(prev) and equity.get(cur):
            raised = (equity[cur] - equity[prev] - profit[cur]) / equity[prev]
            if raised < 0.10 and change > 0 or change < 0:
                skipped.append(cur)  # share count moved without capital moving: split, bonus or consolidation
                continue
        steps.append(change)
    if not steps:
        return {"score": None, "reason": "only split or bonus years on record", "split_or_bonus_years": skipped}
    yearly = (math.prod(1 + s for s in steps) ** (1 / len(steps)) - 1) * 100
    return {
        "score": round(_score_metric(yearly, _DILUTION), 1), "share_count_growth_pct_per_year": round(yearly, 2),
        "years": [years[0], years[-1]], "split_or_bonus_years": skipped,
        "basis": "derived: net profit / basic EPS (Yahoo annual statements)",
    }


def dividend_sustainability(financial_data: dict, metrics: dict, lender: bool = False) -> dict:
    """Payout against profit and, outside lenders, against free cash flow. A
    company that pays no dividend is not scored on this."""
    market = financial_data.get("market") or {}
    rate, shares, payout = market.get("dividend_rate"), market.get("shares_outstanding"), market.get("payout_ratio")
    if not rate or not shares:
        return {"score": None, "reason": "no dividend on record"}
    paid = rate * shares
    parts, out = [], {"dividend_per_share": rate, "dividends_paid": paid}
    if payout is not None:
        out["payout_pct"] = round(payout * 100, 1)
        parts.append(_score_metric(payout * 100, _PAYOUT))
    fcf = metrics.get("fcf_latest")
    if not lender and fcf is not None:
        out["fcf_cover"] = round(fcf / paid, 2)
        parts.append(_score_metric(fcf / paid, _FCF_COVER))
    if not parts:
        return {"score": None, "reason": "no payout ratio or free cash flow to judge it against", **out}
    return {"score": round(sum(parts) / len(parts), 1), **out, "basis": "Yahoo: dividend rate, payout ratio; free cash flow from annual cash flow"}


def _stored_quarterly_profit(db: Session, company_id: str) -> tuple[dict[str, float], str | None]:
    from app.infrastructure.database.metric_store import get_metric_history

    for basis in ("CONSOLIDATED", "STANDALONE"):
        rows = get_metric_history(db, company_id, "qtr_net_profit", statement_type=basis)
        series: dict[str, float] = {}
        for r in rows:  # newest retrieval first: the first value seen for a period wins
            if r.value is not None and r.period not in series and r.period != "TTM":
                series[r.period] = float(r.value)
        if len(series) >= 5:
            return series, f"Screener quarterly results ({basis.title()})"
    return {}, None


def earnings_consistency(metrics: dict, financial_data: dict, db: Session | None = None, company_id: str | None = None) -> dict:
    """How dependable profit has been: the share of quarters in profit and the
    share of quarters ahead of the same quarter a year earlier. Uses the stored
    Screener quarters (about 13) when present, otherwise Yahoo's annual profit."""
    series, basis = _stored_quarterly_profit(db, company_id) if db is not None and company_id else ({}, None)
    if series:
        periods = sorted(series)
        in_profit = sum(1 for p in periods if series[p] > 0) / len(periods)
        pairs = [(series[p], series[f"{int(p[:4]) - 1}{p[4:]}"]) for p in periods if f"{int(p[:4]) - 1}{p[4:]}" in series]
        out = {"quarters": len(periods), "quarters_in_profit_pct": round(in_profit * 100, 1), "basis": basis}
        parts = [_score_metric(in_profit * 100, [(50, 0), (75, 40), (90, 75), (100, 100)])]
        if len(pairs) >= 4:
            ahead = sum(1 for now, before in pairs if now > before) / len(pairs)
            out["quarters_ahead_of_last_year_pct"] = round(ahead * 100, 1)
            out["quarters_compared"] = len(pairs)
            parts.append(_score_metric(ahead * 100, [(20, 10), (50, 55), (80, 100)]))
        score = sum(parts) / len(parts)
        if in_profit < 0.75:
            # smaller losses than last year are not consistency: a company mostly in loss stays near its profit reading
            score = min(score, parts[0] + 15)
        return {"score": round(score, 1), **out}
    annual = metrics.get("pat_series") or {}
    years = _years(annual)
    if len(years) < 3:
        return {"score": None, "reason": "fewer than three years of profit on record"}
    in_profit = sum(1 for y in years if annual[y] > 0) / len(years)
    ups = sum(1 for a, b in zip(years, years[1:]) if annual[b] > annual[a]) / (len(years) - 1)
    score = 0.5 * _score_metric(in_profit * 100, [(50, 0), (75, 40), (100, 100)]) + 0.5 * _score_metric(ups * 100, [(0, 10), (50, 55), (100, 100)])
    return {"score": round(score, 1), "years": len(years), "years_in_profit_pct": round(in_profit * 100, 1),
            "years_of_growth_pct": round(ups * 100, 1), "basis": "Yahoo annual net profit"}


def working_capital_trend(metrics: dict, lender: bool = False) -> dict:
    if lender:
        return {"score": None, "reason": "not meaningful for a lender or insurer"}
    labels = {k: metrics.get(k) for k in ("ccc_trend", "wc_to_revenue_trend")}
    scores = [_TREND_SCORE[v] for v in labels.values() if v in _TREND_SCORE]
    if not scores:
        return {"score": None, "reason": "too little history for a trend"}
    return {"score": round(sum(scores) / len(scores), 1), "cash_conversion_cycle_trend": labels["ccc_trend"],
            "working_capital_to_revenue_trend": labels["wc_to_revenue_trend"],
            "cash_conversion_cycle_days": metrics.get("cash_conversion_cycle")}


def double_in(metrics: dict, series: dict | None = None) -> dict:
    """Years for revenue and profit to double at the measured growth rate, with
    a flag when the profit figure is a recovery from a depressed base — the
    framework's warning that fast doubling is not the same as quality.

    Screener's annual statements (up to about 12 years) are used first, giving
    3-, 5- and 10-year rates; Yahoo's four years (a 3-year rate at most) only
    when Screener has no history for the company."""
    from app.framework.screener_series import cagr

    def doubling(rate):
        return round(math.log(2) / math.log(1 + rate / 100), 1) if rate and rate > 0 else None

    if series and len(series.get("years") or []) >= 4:
        rates = {f"{field}_{n}y": cagr(series, src, n) for field, src in (("revenue", "sales"), ("profit", "net_profit"))
                 for n in (3, 5, 10)}
        rates = {k: round(v, 2) for k, v in rates.items() if v is not None}
        margins = {y: r["net_profit"] / r["sales"] * 100 for y, r in series["rows"].items()
                   if r.get("sales") and r.get("net_profit") is not None}
        source = series["source"]
    else:
        rates = {k: v for k, v in (("revenue_3y", metrics.get("revenue_cagr_3y")), ("profit_3y", metrics.get("pat_cagr_3y")))
                 if v is not None}
        margins = metrics.get("pat_margin_series") or {}
        source = "Yahoo annual statements (four years at most)"
    window = 5 if "revenue_5y" in rates or "profit_5y" in rates else 3
    rev, pat = rates.get(f"revenue_{window}y"), rates.get(f"profit_{window}y")
    out = {"source": source, "growth_pct_per_year": rates, "measured_over_years": window,
           "revenue_doubles_in_years": doubling(rev), "profit_doubles_in_years": doubling(pat), "low_base": False}

    span = 3
    ys = _years(margins)[-(span + 1):]
    if len(ys) == span + 1 and rates.get("profit_3y") is not None:
        first, later = margins[ys[0]], sorted(margins[y] for y in ys[1:])
        usual = later[len(later) // 2]
        rev3, pat3 = rates.get("revenue_3y") or 0, rates["profit_3y"]
        # profit compounding far faster than sales, off a starting margin well below what the company has earned since
        if usual > 0 and first < 0.6 * usual and pat3 > 2 * max(rev3, 0) + 10:
            out["low_base"] = True
            out["low_base_reason"] = (f"net margin was {first:.1f}% in {ys[0][:4] if len(ys[0]) == 10 else ys[0]} against a usual "
                                      f"{usual:.1f}% since: profit growth is mostly margin recovery, not sales growth")
    return out
