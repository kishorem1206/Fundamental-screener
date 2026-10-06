"""Business Quality — "is this a good business?" (framework section 3).

The nature of the business, not the share price. What the app can measure
from real data, each scored 0-100 (a part with no data is left out and the
rest rescaled; under half the weight measured gives no score):

  durability of returns   share of the last (up to) ten years with ROCE of 15%+
                          (ROE of 14%+ for a lender) and the median level — a
                          return held for a decade is the visible sign of a
                          competitive advantage
  margin resilience       worst operating margin of the decade against the usual
                          one — pricing power shows as margins that hold up
                          (not for lenders)
  predictability          share of years without a loss or a profit fall of more
                          than 20% — the long-run cyclicality check; the
                          Fundamental Score's earnings consistency looks only at
                          the last three years of quarters
  capital allocation      return earned on the capital added over the last five
                          years (extra operating profit / extra capital employed;
                          extra profit / extra net worth for a lender)
  promoter behaviour      change in promoter holding over three years, less the
                          NSE pledge and promoter-selling penalty where NSE data
                          has been read
  management credibility  how often management's guidance was kept rather than
                          cut, from the concall analysis (where it has run)

Source: Screener annual statements and shareholding (app/framework/
screener_series.py), NSE shareholding for pledges, concall guidance tracking.

Not measured, and listed as such in every result: brand strength, customer
concentration, industry structure and regulatory risk — there is no source
for them across the universe, and they are not guessed.
"""
from __future__ import annotations

import statistics

from sqlalchemy.orm import Session

from app.calculations.scoring import _score_metric
from app.framework.screener_series import annual

_WEIGHTS = {"durability": 0.25, "margin_resilience": 0.20, "predictability": 0.15, "capital_allocation": 0.15,
            "promoter_behaviour": 0.15, "management_credibility": 0.10}
_WEIGHTS_LENDER = {"durability": 0.35, "predictability": 0.20, "capital_allocation": 0.20,
                   "promoter_behaviour": 0.15, "management_credibility": 0.10}
NOT_MEASURED = ["brand strength", "customer concentration", "industry structure", "regulatory risk"]

_YEARS = 10
_MIN_YEARS = 5
_ROCE_LEVEL = [(0, 5), (8, 25), (12, 45), (15, 60), (20, 78), (25, 90), (35, 100)]
_ROE_LEVEL = [(0, 5), (8, 25), (11, 45), (14, 60), (17, 78), (20, 90), (25, 100)]
_RESILIENCE = [(0, 5), (0.4, 30), (0.6, 55), (0.8, 80), (0.9, 95), (1.0, 100)]
_INCREMENTAL = [(-10, 0), (0, 15), (8, 35), (12, 50), (18, 70), (25, 85), (35, 100)]
_PROMOTER_CHANGE = [(-15, 5), (-8, 25), (-4, 50), (-1, 75), (0, 85), (3, 92)]


def _recent(series: dict, field: str) -> list[tuple[str, float]]:
    pts = [(y, series["rows"][y][field]) for y in series["years"] if series["rows"][y].get(field) is not None]
    return pts[-_YEARS:]


def durability(series: dict, lender: bool) -> dict:
    field, hurdle, table = ("roe", 14.0, _ROE_LEVEL) if lender else ("roce", 15.0, _ROCE_LEVEL)
    # a year with negative net worth has no meaningful return and counts as a year below the hurdle, at zero
    pts = [(y, 0.0 if series["rows"][y].get("negative_net_worth") else series["rows"][y].get(field))
           for y in series["years"][1:]]
    pts = [(y, v) for y, v in pts if v is not None][-_YEARS:]
    if len(pts) < _MIN_YEARS:
        return {"score": None, "reason": f"fewer than {_MIN_YEARS} years of {field.upper()}"}
    values = [v for _, v in pts]
    wiped = [y[:4] for y, _ in pts if series["rows"][y].get("negative_net_worth")]
    above = sum(1 for v in values if v >= hurdle) / len(values)
    median = statistics.median(values)
    return {"score": round(0.5 * above * 100 + 0.5 * _score_metric(median, table), 1),
            "measure": field.upper(), "years": len(values), "from": pts[0][0][:4], "to": pts[-1][0][:4],
            f"years_at_or_above_{int(hurdle)}_pct": round(above * 100, 1), "median_pct": round(median, 1),
            **({"negative_net_worth_years": wiped} if wiped else {})}


def margin_resilience(series: dict) -> dict:
    pts = _recent(series, "opm")
    if len(pts) < _MIN_YEARS:
        return {"score": None, "reason": f"fewer than {_MIN_YEARS} years of operating margin"}
    values = [v for _, v in pts]
    usual = statistics.median(values)
    if usual <= 0:
        return {"score": 5.0, "usual_operating_margin_pct": round(usual, 1), "years": len(values),
                "reading": "operating margin usually zero or negative"}
    worst = min(values)
    worst_year = next(y for y, v in pts if v == worst)
    ratio = max(worst, 0) / usual
    return {"score": round(_score_metric(ratio, _RESILIENCE), 1), "years": len(values),
            "usual_operating_margin_pct": round(usual, 1), "worst_operating_margin_pct": round(worst, 1),
            "worst_year": worst_year[:4]}


def predictability(series: dict) -> dict:
    pts = _recent(series, "net_profit")
    if len(pts) < _MIN_YEARS + 1:
        return {"score": None, "reason": f"fewer than {_MIN_YEARS + 1} years of profit"}
    bad = []
    for (_, before), (year, now) in zip(pts, pts[1:]):
        if now <= 0 or (before > 0 and now < 0.8 * before):
            bad.append(year[:4])
    steady = 1 - len(bad) / (len(pts) - 1)
    return {"score": round(_score_metric(steady * 100, [(30, 5), (50, 30), (70, 60), (85, 85), (100, 100)]), 1),
            "years_compared": len(pts) - 1, "loss_or_sharp_fall_years": bad, "cyclical": len(bad) >= 3}


def capital_allocation(series: dict, lender: bool) -> dict:
    gain_field, base_field = ("net_profit", "net_worth") if lender else (None, "capital_employed")
    years = [y for y in series["years"] if series["rows"][y].get(base_field) is not None
             and (series["rows"][y].get("pbt") is not None if not lender else series["rows"][y].get("net_profit") is not None)]
    if len(years) < 4:
        return {"score": None, "reason": "fewer than four years of capital and profit"}
    start, end = years[-6] if len(years) >= 6 else years[0], years[-1]
    a, b = series["rows"][start], series["rows"][end]

    def gain(r):
        return r["net_profit"] if lender else r["pbt"] + (r.get("interest") or 0)

    added_profit, added_capital = gain(b) - gain(a), b[base_field] - a[base_field]
    out = {"from": start[:4], "to": end[:4], "added_profit_cr": round(added_profit, 1), "added_capital_cr": round(added_capital, 1)}
    if gain(b) <= 0:
        return {"score": 5.0, "reading": "still loss-making at the end of the period", **out}
    if a[base_field] <= 0:
        return {"score": 20.0, "reading": "began the period with negative net worth", **out}
    if added_capital <= 0.05 * a[base_field]:
        # little or no capital added: judged on whether profit still grew
        out["reading"] = "profit grew without adding capital" if added_profit > 0 else "no capital added and profit did not grow"
        return {"score": 90.0 if added_profit > 0 else 25.0, **out}
    incremental = added_profit / added_capital * 100
    return {"score": round(_score_metric(incremental, _INCREMENTAL), 1), "incremental_return_pct": round(incremental, 1), **out}


def promoter_behaviour(db: Session, company_id: str, as_of=None) -> dict:
    from datetime import date

    from app.calculations.governance_scoring import compute_governance_penalty
    from app.infrastructure.database.models import ShareholdingScreener

    all_rows = (db.query(ShareholdingScreener).filter(ShareholdingScreener.company_id == company_id,
                                                      ShareholdingScreener.frequency == "quarterly")
                .order_by(ShareholdingScreener.period_end).all())
    if as_of is not None:  # point in time: holdings published by then; no pledge history is kept to replay
        all_rows = [r for r in all_rows if date.fromisoformat(r.period_end) <= as_of]
    rows = [r for r in all_rows if r.promoter_pct is not None]
    governance = compute_governance_penalty(db, company_id) if as_of is None else None
    out: dict = {"nse_pledge_data": governance is not None}
    if governance:
        out["governance_penalty"] = governance["penalty"]
        out["governance_flags"] = [{k: f[k] for k in ("event_type", "severity", "event_date")} for f in governance["flags"]]
    if len(all_rows) >= 4 and not rows:
        out.update(score=None, reason="no promoter group (widely held company)")
        return out
    if len(rows) < 4:
        out.update(score=None, reason="fewer than four quarters of shareholding")
        return out
    latest = rows[-1]
    cutoff = date.fromisoformat(latest.period_end).replace(year=date.fromisoformat(latest.period_end).year - 3).isoformat()
    base = next((r for r in rows if r.period_end >= cutoff), rows[0])
    now, before = float(latest.promoter_pct), float(base.promoter_pct)
    out.update(promoter_pct=now, promoter_pct_then=before, since=base.period_end, latest=latest.period_end)
    if now < 1 and before < 1:
        out.update(score=None, reason="no promoter group (widely held company)")
        return out
    score = _score_metric(now - before, _PROMOTER_CHANGE) - (governance or {}).get("penalty", 0) * 2
    out.update(score=round(max(0.0, score), 1), change_pts=round(now - before, 2))
    return out


def management_credibility(db: Session, company_id: str, as_of=None) -> dict:
    from app.infrastructure.database.models import ManagementCredibility

    if as_of is not None:
        return {"score": None, "reason": "guidance tracking keeps no history to replay at an earlier date"}
    rows = db.query(ManagementCredibility).filter(ManagementCredibility.company_id == company_id).all()
    kept = sum(r.upgraded_count + r.reiterated_count for r in rows)
    cut = sum(r.downgraded_count for r in rows)
    if kept + cut < 3:
        return {"score": None, "reason": "fewer than three tracked guidance updates (concall analysis not run)"}
    share = kept / (kept + cut)
    return {"score": round(_score_metric(share * 100, [(30, 10), (50, 40), (70, 70), (85, 90), (100, 100)]), 1),
            "guidance_kept_or_raised": kept, "guidance_cut": cut, "metrics_tracked": len(rows)}


def compute_business_quality(db: Session, company_id: str, lender: bool, series: dict | None = None, as_of=None) -> dict:
    series = series or annual(db, company_id, as_of)
    parts = {
        "durability": durability(series, lender),
        "predictability": predictability(series),
        "capital_allocation": capital_allocation(series, lender),
        "promoter_behaviour": promoter_behaviour(db, company_id, as_of),
        "management_credibility": management_credibility(db, company_id, as_of),
    }
    if not lender:
        parts["margin_resilience"] = margin_resilience(series)
    weights = _WEIGHTS_LENDER if lender else _WEIGHTS
    for name, part in parts.items():
        part["weight"] = weights[name]
    scored = {n: p for n, p in parts.items() if p.get("score") is not None}
    covered = sum(p["weight"] for p in scored.values())
    score = round(sum(p["score"] * p["weight"] for p in scored.values()) / covered, 1) if covered >= 0.5 else None
    return {"score": score, "coverage": round(covered, 3), "components": parts, "not_measured": NOT_MEASURED,
            "source": series.get("source"), "years_on_record": len(series["years"])}
