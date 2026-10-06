"""Quality Momentum — how the Quality Score is changing (framework section 10).

Two stocks at 54 today, one up from 39 and one down from 72, are not the same
stock. Momentum compares today's Quality with 6 and 12 months ago.

Where the earlier score comes from:

  recorded        a Quality row actually stored in `fw_scores` within 20 days
                  of the target date. Rows are kept per day from 2026-10-05, so
                  this takes over on its own as history builds up.
  reconstructed   until then: Quality is rebuilt three times — as at today, 6
                  months ago and 12 months ago — from the Screener statements
                  that had been published by each date (annual results 60 days
                  after the year end, quarterly results 45 days after the
                  quarter end, shareholding as filed). The same method is used
                  for all three, so the change between them is like for like.
                  The earlier score shown is today's actual Quality less that
                  change.

The reconstruction leaves out what has no history to replay: Yahoo-only
inputs (share dilution, dividend sustainability, working-capital trend),
NSE pledge events and concall guidance tracking. They are left out of all
three dates alike.

Direction: improving when the 12-month change is +5 or more (or the 6-month
change +3 or more without a 12-month fall); declining when the 12-month change
is -5 or less (or the 6-month change -3 or less without a 12-month rise);
otherwise stable.
"""
from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.calculations.quarterly_growth import (
    _MARGIN_TREND_SCORE_CONFIG, _METRIC_WEIGHTS, _block_avg_delta_pp, _block_growth_pct, _weighted_growth_pct,
)
from app.calculations.scoring import GROWTH_SCORE_CONFIG, _score_metric, compute_scores
from app.framework.business_quality import compute_business_quality
from app.framework.fundamental import compute_fundamental
from app.framework.quality import compute_quality
from app.framework.screener_series import annual, cagr, quarterly
from app.framework.valuation import core_ttm

HORIZONS = {"6m": 182, "12m": 365}
_RECORDED_WINDOW_DAYS = 20
_MIN_YEARS = 4


def _quarterly_growth(q: dict) -> dict | None:
    """The existing quarterly growth score (calculations/quarterly_growth.py),
    fed with the quarters published by the date in question."""
    periods = q["quarters"][-12:]
    if len(periods) < 8:
        return None
    scores, growth = {}, {}
    for name, field, config in (("revenue", "sales", "revenue_cagr_3y"), ("pat", "net_profit", "pat_cagr_3y"),
                                ("eps", "eps", "eps_cagr_3y")):
        values = [q["rows"][p].get(field) for p in periods]
        if any(v is None for v in values):
            continue
        g = _weighted_growth_pct(_block_growth_pct(values))
        if g is not None:
            growth[name], scores[name] = g, _score_metric(g, GROWTH_SCORE_CONFIG[config])
    margins = [q["rows"][p].get("opm") for p in periods]
    if all(m is not None for m in margins):
        d = _weighted_growth_pct(_block_avg_delta_pp(margins))
        if d is not None:
            growth["margin"], scores["margin"] = d, _score_metric(d, _MARGIN_TREND_SCORE_CONFIG)
    if not scores:
        return None
    total = sum(_METRIC_WEIGHTS[k] for k in scores)
    return {"score": sum(scores[k] * _METRIC_WEIGHTS[k] for k in scores) / total, "growth_pct": growth}


def point_in_time_metrics(series: dict, q: dict) -> dict:
    """The metric keys scoring.py reads, from Screener statements alone:
    growth from the annual years, margins from the last four published
    quarters, returns, leverage and cash conversion from the latest year."""
    years = series["years"]
    r = series["rows"][years[-1]]
    m: dict = {"latest_fy": f"FY{years[-1][:4]}",
               "revenue_cagr_3y": cagr(series, "sales", 3), "pat_cagr_3y": cagr(series, "net_profit", 3),
               "eps_cagr_3y": cagr(series, "eps", 3), "fcf_cagr_3y": cagr(series, "fcf", 3),
               "pat_series": {y: series["rows"][y]["net_profit"] for y in years if series["rows"][y].get("net_profit") is not None},
               "revenue_series": {y: series["rows"][y]["sales"] for y in years}}
    qs = q["quarters"][-4:]
    if len(qs) == 4 and all(q["rows"][p].get(f) is not None for p in qs for f in ("sales", "operating_profit", "net_profit")):
        sales = sum(q["rows"][p]["sales"] for p in qs)
        if sales > 0:
            m["ebitda_margin"] = sum(q["rows"][p]["operating_profit"] for p in qs) / sales * 100
            # a quarter that dwarfs the other three is a one-off (same rule as the Valuation Score)
            profit, _ = core_ttm([q["rows"][p]["net_profit"] for p in qs])
            m["pat_margin"] = profit / sales * 100
    elif r.get("sales"):
        m["ebitda_margin"] = r.get("opm")
        if r.get("net_profit") is not None:
            m["pat_margin"] = r["net_profit"] / r["sales"] * 100
    m["roe"], m["roce"] = r.get("roe"), r.get("roce")
    np_ = r.get("net_profit")
    if np_ and np_ > 0:
        if r.get("cfo") is not None:
            m["cfo_to_pat"] = r["cfo"] / np_ * 100
        if r.get("fcf") is not None:
            m["fcf_to_pat"] = r["fcf"] / np_ * 100
    if r.get("fcf") is not None and r.get("sales"):
        m["fcf_margin"] = r["fcf"] / r["sales"] * 100
    if (r.get("net_worth") or 0) > 0:
        m["debt_to_equity"] = (r.get("borrowings") or 0) / r["net_worth"]
    if r.get("interest"):
        m["interest_coverage"] = (r.get("pbt", 0) + r["interest"]) / r["interest"]
    if r.get("total_assets"):
        m["asset_turnover"] = r["sales"] / r["total_assets"]
        if np_ is not None:
            m["roa"] = np_ / r["total_assets"] * 100
    qg = _quarterly_growth(q)
    if qg:
        m["quarterly_growth_score"], m["quarterly_growth_pct"] = qg["score"], qg["growth_pct"]
    return {k: v for k, v in m.items() if v is not None}


def quality_at(db: Session, stock_id: str, sector_framework: str, lender: bool, as_of: date) -> dict | None:
    series = annual(db, stock_id, as_of)
    if len(series["years"]) < _MIN_YEARS:
        return None
    q = quarterly(db, stock_id, as_of)
    metrics = point_in_time_metrics(series, q)
    categories = compute_scores(metrics, sector=sector_framework)
    fundamental = compute_fundamental(categories, metrics, {}, sector_framework, series=series)
    business = compute_business_quality(db, stock_id, lender, series, as_of=as_of)
    quality = compute_quality(fundamental, business)
    if quality["score"] is None:
        return None
    return {"as_of": as_of.isoformat(), "quality": quality["score"], "fundamental": fundamental["score"],
            "business_quality": business["score"], "latest_year": series["years"][-1][:4],
            "latest_quarter": q["quarters"][-1] if q["quarters"] else None}


def _recorded(db: Session, stock_id: str, target: date):
    from app.infrastructure.database.models import FrameworkScore

    rows = (db.query(FrameworkScore).filter(
        FrameworkScore.stock_id == stock_id, FrameworkScore.quality.isnot(None), FrameworkScore.reconstructed.is_(False),
        FrameworkScore.as_of.between(target - timedelta(days=_RECORDED_WINDOW_DAYS), target + timedelta(days=_RECORDED_WINDOW_DAYS)))
        .all())
    return min(rows, key=lambda r: (abs((r.as_of - target).days), r.basis != "FULL")) if rows else None


def direction(change_6m: float | None, change_12m: float | None) -> str:
    if change_6m is None and change_12m is None:
        return "INSUFFICIENT_DATA"
    c6, c12 = change_6m or 0.0, change_12m
    if (c12 is not None and c12 >= 5) or (c6 >= 3 and (c12 is None or c12 >= 0)):
        return "IMPROVING"
    if (c12 is not None and c12 <= -5) or (c6 <= -3 and (c12 is None or c12 <= 0)):
        return "DECLINING"
    return "STABLE"


def compute_momentum(db: Session, stock_id: str, sector_framework: str, lender: bool, current: float | None,
                     today: date | None = None) -> dict:
    today = today or date.today()
    if current is None:
        return {"direction": "INSUFFICIENT_DATA", "reason": "no current Quality Score"}
    out: dict = {"current": current}
    rebuilt_now = None
    for name, days in HORIZONS.items():
        target = today - timedelta(days=days)
        row = _recorded(db, stock_id, target)
        if row is not None:
            out[name] = {"quality": float(row.quality), "change": round(current - float(row.quality), 1),
                         "method": "recorded", "as_of": row.as_of.isoformat(), "basis": row.basis}
            continue
        if rebuilt_now is None:
            rebuilt_now = quality_at(db, stock_id, sector_framework, lender, today) or {}
        then = quality_at(db, stock_id, sector_framework, lender, target)
        if not rebuilt_now or not then:
            out[name] = {"quality": None, "change": None, "method": "reconstructed",
                         "reason": f"fewer than {_MIN_YEARS} years of Screener results published by {target.isoformat()}"}
            continue
        change = round(rebuilt_now["quality"] - then["quality"], 1)
        out[name] = {"quality": round(current - change, 1), "change": change, "method": "reconstructed",
                     "as_of": target.isoformat(), "rebuilt_then": then, "rebuilt_now": rebuilt_now["quality"]}
    out["direction"] = direction(out["6m"].get("change"), out["12m"].get("change"))
    return out
