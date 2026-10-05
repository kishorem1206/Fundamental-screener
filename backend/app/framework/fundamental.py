"""Fundamental Score — "are the financial numbers strong?" (framework section 4).

Hard financial data only. Valuation is deliberately not in it (section 8 comes
after quality and fundamentals), and neither is anything about price.

How it is put together:

  * 80% from the older category scores, which already measure most of what
    section 4 lists, with the sector's own weights and its own formulas for
    banks, NBFCs and insurers (section 19):
        growth          revenue, PAT and EPS growth
        profitability   ROE, ROCE, operating and net margin
        cash_flow       free cash flow, CFO/PAT
        balance_sheet   debt/equity, interest cover, balance-sheet strength
        efficiency      asset turns and working-capital days — not on the
                        framework's list, so it counts at half its sector weight
    The sector weight for valuation is dropped and the rest rescaled.
  * 20% from the four listed inputs the older scores never measured
    (app/framework/inputs.py): earnings consistency 8, working-capital trend 5,
    share dilution 4, dividend sustainability 3.

An input that does not apply or has no data is left out and the remaining
weights are rescaled; `coverage` reports how much of the weight was scored.
A profit-growth figure that is mostly recovery from a depressed base caps the
growth component at 70 ("fast doubling time is not automatically quality").

Long-run growth (section 4 asks for 3Y and 5Y rates together): when Screener's
annual statements give five-year sales, profit and EPS growth, the growth
component is 70% the existing growth score (three-year rates and the recent
quarters) and 30% the five-year rates, scored on the same thresholds.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.calculations.scoring import GROWTH_SCORE_CONFIG, SECTOR_WEIGHTS, UNIVERSAL_WEIGHTS, _score_metric
from app.framework import inputs
from app.framework.screener_series import cagr

LENDER_FRAMEWORKS = {"Banks", "NBFCs", "Housing Finance", "Microfinance", "Gold Loans", "Insurance"}

_CATEGORY_SHARE = 0.80
_ADD_ON_FACTOR = {"efficiency": 0.5}  # counted, but not a framework input
_NEW_INPUTS = {"earnings_consistency": 0.08, "working_capital_trend": 0.05, "share_dilution": 0.04, "dividend_sustainability": 0.03}
_LOW_BASE_GROWTH_CAP = 70.0
_CATEGORIES = ("growth", "profitability", "cash_flow", "balance_sheet", "efficiency")
_LONG_RUN_SHARE = 0.30


def long_run_growth(series: dict | None) -> dict | None:
    """Five-year sales, profit and EPS growth from Screener, scored like the
    three-year rates. None when Screener has under six years for the company."""
    if not series or len(series.get("years") or []) < 6:
        return None
    rates = {name: cagr(series, field, 5) for name, field in (("sales", "sales"), ("profit", "net_profit"), ("eps", "eps"))}
    tables = {"sales": "revenue_cagr_3y", "profit": "pat_cagr_3y", "eps": "eps_cagr_3y"}
    scores = [_score_metric(v, GROWTH_SCORE_CONFIG[tables[k]]) for k, v in rates.items() if v is not None]
    if not scores:
        return None
    return {"score": round(sum(scores) / len(scores), 1), "rates_pct_per_year": {k: round(v, 2) for k, v in rates.items() if v is not None},
            "years": f"{series['years'][-6][:4]}-{series['years'][-1][:4]}", "source": series["source"]}


def weights_for(sector_framework: str) -> dict[str, float]:
    sector = SECTOR_WEIGHTS.get(sector_framework, UNIVERSAL_WEIGHTS)
    raw = {c: sector.get(c, 0.0) * _ADD_ON_FACTOR.get(c, 1.0) for c in _CATEGORIES}
    total = sum(raw.values())
    out = {c: _CATEGORY_SHARE * w / total for c, w in raw.items()}
    out.update(_NEW_INPUTS)
    return out


def classify(score: float | None) -> str | None:
    if score is None:
        return None
    return "STRONG" if score >= 65 else "GOOD" if score >= 50 else "BORDERLINE" if score >= 40 else "WEAK" if score >= 30 else "VERY_WEAK"


def compute_fundamental(category_scores: dict, metrics: dict, financial_data: dict, sector_framework: str,
                        db: Session | None = None, company_id: str | None = None, series: dict | None = None) -> dict:
    """`category_scores` are the app's existing (refined) growth / profitability /
    cash_flow / balance_sheet / efficiency scores for this company."""
    lender = sector_framework in LENDER_FRAMEWORKS
    new = {
        "earnings_consistency": inputs.earnings_consistency(metrics, financial_data, db, company_id),
        "working_capital_trend": inputs.working_capital_trend(metrics, lender),
        "share_dilution": inputs.share_dilution(financial_data),
        "dividend_sustainability": inputs.dividend_sustainability(financial_data, metrics, lender),
    }
    doubling = inputs.double_in(metrics, series)
    long_run = long_run_growth(series)
    weights = weights_for(sector_framework)

    components: dict[str, dict] = {}
    for name in _CATEGORIES:
        value = category_scores.get(name)
        note = None
        if name == "growth" and value is not None and long_run:
            note = f"{(1 - _LONG_RUN_SHARE) * 100:.0f}% existing growth score {value} + {_LONG_RUN_SHARE * 100:.0f}% five-year growth {long_run['score']}"
            value = round((1 - _LONG_RUN_SHARE) * value + _LONG_RUN_SHARE * long_run["score"], 1)
        if name == "growth" and value is not None and doubling["low_base"] and value > _LOW_BASE_GROWTH_CAP:
            note = (note + "; " if note else "") + f"capped at {_LOW_BASE_GROWTH_CAP:.0f} from {value}: {doubling['low_base_reason']}"
            value = _LOW_BASE_GROWTH_CAP
        components[name] = {"score": value, "weight": round(weights[name], 4), "source": "existing category score", **({"note": note} if note else {})}
    for name, detail in new.items():
        components[name] = {"weight": weights[name], "source": "framework input", **detail}

    scored = {n: c for n, c in components.items() if c.get("score") is not None}
    covered = sum(c["weight"] for c in scored.values())
    score = round(sum(c["score"] * c["weight"] for c in scored.values()) / covered, 1) if covered >= 0.5 else None
    return {
        "score": score, "classification": classify(score), "coverage": round(covered, 3),
        "sector_framework": sector_framework, "components": components, "double_in": doubling, "long_run_growth": long_run,
        "metric_sources": metrics.get("_metric_sources") or {},
    }
