"""Quantitative Score — "are the measurable numbers getting better or worse?"
(framework section 5).

Measured changes and statistical behaviour only (section 18). Levels of growth,
margins and returns belong to the Fundamental Score and are not counted again
here; returns against the market and the sector belong to Relative Strength.

  growth acceleration   last four quarters' sales and profit growth against
                        the three-year rate (Screener)
  margin change         operating margin of the last four quarters against the
                        four before (net margin for a lender) (Screener)
  return change         ROCE now against three years ago (ROE for a lender)
  debt change           borrowings to net worth now against three years ago
                        (not for a lender)
  volatility            annualised daily volatility over a year (stored prices)
  drawdown              largest fall from a high over a year
  risk-adjusted return  one-year return per unit of volatility

Earnings revisions (also on the framework's list) are left out: analyst
estimates are stored for only about 56 companies. Quality Score change over
time comes with Quality Momentum (phase 8).
"""
from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.calculations.scoring import _score_metric
from app.framework import price_stats
from app.framework.screener_series import cagr, quarterly

_WEIGHTS = {"growth_acceleration": 0.20, "margin_change": 0.15, "return_change": 0.15, "debt_change": 0.10,
            "volatility": 0.15, "drawdown": 0.10, "risk_adjusted_return": 0.15}
_WEIGHTS_LENDER = {"growth_acceleration": 0.25, "margin_change": 0.10, "return_change": 0.20,
                   "volatility": 0.15, "drawdown": 0.10, "risk_adjusted_return": 0.20}
_ACCEL = [(-25, 5), (-12, 25), (-4, 45), (0, 55), (5, 70), (12, 85), (25, 100)]
_MARGIN = [(-5, 5), (-2, 30), (-0.5, 50), (0.5, 60), (2, 80), (5, 100)]
_RETURN = [(-10, 5), (-4, 30), (-1, 50), (1, 62), (4, 80), (8, 100)]
_DEBT = [(-0.5, 100), (-0.2, 85), (-0.05, 70), (0.05, 60), (0.2, 40), (0.5, 20), (1.0, 5)]
_VOL = [(15, 100), (25, 80), (35, 60), (50, 35), (70, 10), (100, 0)]
_DD = [(-60, 5), (-45, 25), (-30, 50), (-20, 70), (-10, 90), (-5, 100)]
_SHARPE = [(-1.0, 5), (0.0, 30), (0.5, 55), (1.0, 75), (1.5, 90), (2.0, 100)]
_RISK_FREE = 6.5  # % a year, roughly the Indian 1-year government bond yield


def _ttm(q: dict, field: str, offset: int) -> float | None:
    """Sum of four quarters ending `offset` quarters before the latest."""
    qs = q["quarters"]
    window = qs[len(qs) - 4 - offset: len(qs) - offset] if len(qs) >= 4 + offset else []
    vals = [q["rows"][p].get(field) for p in window]
    return sum(vals) if len(window) == 4 and all(v is not None for v in vals) else None


def growth_acceleration(q: dict, series: dict) -> dict:
    parts, out = [], {}
    for name, field in (("sales", "sales"), ("profit", "net_profit")):
        now, before = _ttm(q, field, 0), _ttm(q, field, 4)
        long_run = cagr(series, field, 3) if series.get("years") else None
        if now is None or before is None or before <= 0 or now <= 0 or long_run is None:
            continue
        recent = (now / before - 1) * 100
        out[f"{name}_last_4q_growth_pct"] = round(recent, 1)
        out[f"{name}_3y_growth_pct"] = round(long_run, 1)
        parts.append(_score_metric(recent - long_run, _ACCEL))
    if not parts:
        return {"score": None, "reason": "need eight quarters and three years of positive sales or profit"}
    out["latest_quarter"] = q["quarters"][-1]
    return {"score": round(sum(parts) / len(parts), 1), **out, "source": q["source"]}


def margin_change(q: dict, lender: bool = False) -> dict:
    """Operating margin; net margin for a lender, whose Screener "financing
    margin" nets off provisions and swings for reasons unrelated to pricing."""
    field, label = ("net_profit", "net_margin") if lender else ("operating_profit", "operating_margin")
    latest = (_ttm(q, field, 0), _ttm(q, "sales", 0))
    prior = (_ttm(q, field, 4), _ttm(q, "sales", 4))
    if None in latest or None in prior or not latest[1] or not prior[1]:
        return {"score": None, "reason": f"need eight quarters of sales and {field.replace('_', ' ')}"}
    now, before = latest[0] / latest[1] * 100, prior[0] / prior[1] * 100
    return {"score": round(_score_metric(now - before, _MARGIN), 1), f"{label}_last_4q_pct": round(now, 2),
            f"{label}_prior_4q_pct": round(before, 2), "change_pts": round(now - before, 2), "source": q["source"]}


def _three_years_apart(series: dict, field: str) -> tuple[str, float, str, float] | None:
    years = [y for y in series.get("years") or [] if series["rows"][y].get(field) is not None]
    if len(years) < 4:
        return None
    return years[-4], series["rows"][years[-4]][field], years[-1], series["rows"][years[-1]][field]


def return_change(series: dict, lender: bool) -> dict:
    field = "roe" if lender else "roce"
    pair = _three_years_apart(series, field)
    if pair is None:
        return {"score": None, "reason": f"need four years of {field.upper()}"}
    y0, v0, y1, v1 = pair
    return {"score": round(_score_metric(v1 - v0, _RETURN), 1), "measure": field.upper(), "from": y0[:4], "to": y1[:4],
            "then_pct": round(v0, 1), "now_pct": round(v1, 1), "change_pts": round(v1 - v0, 1), "source": series.get("source")}


def debt_change(series: dict) -> dict:
    years = [y for y in series.get("years") or [] if (series["rows"][y].get("net_worth") or 0) > 0]
    if len(years) < 4:
        return {"score": None, "reason": "need four years of positive net worth"}
    a, b = series["rows"][years[-4]], series["rows"][years[-1]]
    de0, de1 = a.get("borrowings", 0) / a["net_worth"], b.get("borrowings", 0) / b["net_worth"]
    out = {"from": years[-4][:4], "to": years[-1][:4], "debt_to_equity_then": round(de0, 2), "debt_to_equity_now": round(de1, 2),
           "source": series.get("source")}
    if de0 < 0.05 and de1 < 0.05:
        return {"score": 85.0, "reading": "debt-free throughout", **out}
    return {"score": round(_score_metric(de1 - de0, _DEBT), 1), "change": round(de1 - de0, 2), **out}


def price_behaviour(db: Session, stock_id: str, end: date | None) -> dict[str, dict]:
    none = {"score": None, "reason": "no stored price history"}
    if end is None:
        return {"volatility": none, "drawdown": none, "risk_adjusted_return": none}
    year = price_stats.stock_year(db, stock_id, end)
    if len(year) < 200 or year[0][0] > end.replace(year=end.year - 1):
        reason = {"score": None, "reason": "less than a year of stored prices"}
        return {"volatility": reason, "drawdown": reason, "risk_adjusted_return": reason}
    vol = price_stats.volatility(year)
    dd, peak, trough = price_stats.max_drawdown(year)
    ret = price_stats.window_returns(year, end)["1Y"]
    sharpe = (ret - _RISK_FREE) / vol if ret is not None and vol else None
    src = "stored daily prices (Yahoo, adjusted), one year to " + end.isoformat()
    return {
        "volatility": {"score": round(_score_metric(vol, _VOL), 1), "annualised_pct": round(vol, 1), "source": src},
        "drawdown": {"score": round(_score_metric(dd, _DD), 1), "max_fall_pct": round(dd, 1),
                     "peak": peak and peak.isoformat(), "trough": trough and trough.isoformat(), "source": src},
        "risk_adjusted_return": ({"score": round(_score_metric(sharpe, _SHARPE), 1), "return_1y_pct": round(ret, 1),
                                  "return_per_unit_of_volatility": round(sharpe, 2), "risk_free_pct": _RISK_FREE, "source": src}
                                 if sharpe is not None else {"score": None, "reason": "no one-year return"}),
    }


def compute_quantitative(db: Session, stock_id: str, series: dict, lender: bool, end: date | None) -> dict:
    q = quarterly(db, stock_id)
    parts = {"growth_acceleration": growth_acceleration(q, series), "margin_change": margin_change(q, lender),
             "return_change": return_change(series, lender), **price_behaviour(db, stock_id, end)}
    if not lender:
        parts["debt_change"] = debt_change(series)
    weights = _WEIGHTS_LENDER if lender else _WEIGHTS
    for name, part in parts.items():
        part["weight"] = weights[name]
    scored = {n: p for n, p in parts.items() if p.get("score") is not None}
    covered = sum(p["weight"] for p in scored.values())
    score = round(sum(p["score"] * p["weight"] for p in scored.values()) / covered, 1) if covered >= 0.5 else None
    return {"score": score, "coverage": round(covered, 3), "components": parts,
            "not_measured": ["earnings revisions"], "as_of": end and end.isoformat()}
