"""Decision engine — classification, action and position-size guidance from
the framework's separate scores (sections 13, 15, 16, 17, 20, 22).

Fixed rules, never an average: Quality is the first gate, and a strong chart
or a cheap price can never lift a stock across it (sections 1, 7, 8). The
language model only words the explanation afterwards (`explain.py`); it cannot
change any of this.

Order of the checks follows the agent decision flow (section 16): business
quality and fundamentals, then quality momentum, quantitative strength,
relative strength, technical structure, valuation, sector comparison.
Portfolio comparison, sector allocation and total asset allocation come with
the portfolio (phase 10).

Gates (section 17):
  core            Quality 50+, no major governance red flag, no serious
                  balance-sheet weakness (balance-sheet score under 35), no
                  persistent cash-flow deterioration (cash-flow score under 35
                  with free cash flow declining)
  preferred core  Quality 65+, quality not declining, top 40% of its sector,
                  fair or cheap preferred, relative strength 50+ preferred
  recovery        Quality 40-49, quality momentum improving, relative
                  strength 60+, fair or cheap, no governance or balance-sheet flag
  tactical        weak Quality (under 40) with technical 65+ and relative
                  strength 55+: outside the core bucket, small, with an exit rule
"""
from __future__ import annotations

CLASSIFICATIONS = ("Core Quality", "Investable", "Improving / Watch", "Recovery Candidate", "Tactical Only",
                   "Replacement Candidate", "Avoid")
ACTIONS = ("Hold", "Add gradually", "Add on confirmation", "Reduce", "Replace", "Avoid", "Watch")
SIZES = ("High", "Medium", "Small", "Tactical only", "None")

_BALANCE_SHEET_FLOOR = 35.0
_CASH_FLOW_FLOOR = 35.0
_STRONG_TECHNICAL = 65.0
_WEAK_TECHNICAL = 40.0
_STRONG_RS = 60.0
_TOP = 40.0


def _component(detail: dict, score: str, part: str) -> float | None:
    return ((((detail.get(score) or {}).get("components") or {}).get(part)) or {}).get("score")


def direction_of(detail: dict, trend: str | None, quality_direction: str | None) -> str:
    """Quality momentum (section 10) when it could be measured — a measured
    stable Quality stays stable even if some business signals point down; the
    business trend label (section 9) only when momentum is unknown."""
    if quality_direction in ("IMPROVING", "DECLINING", "STABLE"):
        return quality_direction
    if trend in ("IMPROVING", "DECLINING"):
        return trend
    return "STABLE" if trend in ("STABLE", "CYCLICAL") else "UNKNOWN"


def gates(s: dict, detail: dict, rank: dict | None) -> dict:
    q = s.get("quality")
    flags = []
    gov = (detail.get("quality") or {}).get("governance_red_flag")
    if gov:
        flags.append(f"governance: {gov}")
    bs = _component(detail, "fundamental", "balance_sheet")
    if bs is not None and bs < _BALANCE_SHEET_FLOOR:
        flags.append(f"balance sheet weak (score {bs:.0f})")
    cf = _component(detail, "fundamental", "cash_flow")
    fcf_down = any(x.get("signal") == "free cash flow" and x.get("vote", 0) < 0 for x in (detail.get("trend") or {}).get("signals") or [])
    if cf is not None and cf < _CASH_FLOW_FLOOR and fcf_down:
        flags.append(f"cash flow weak and deteriorating (score {cf:.0f})")
    top = rank is not None and rank["top_pct"] <= _TOP
    view = s.get("valuation_view")
    rs = s.get("relative_strength")
    momentum = s.get("quality_direction")
    core = q is not None and q >= 50 and not flags
    return {
        "core": core, "red_flags": flags,
        "preferred": core and q >= 65 and momentum != "DECLINING" and (rank is None or top),
        "recovery": (q is not None and 40 <= q < 50 and momentum == "IMPROVING" and (rs or 0) >= _STRONG_RS
                     and view in ("FAIR", "CHEAP") and not flags),
        "tactical": (q is not None and q < 40 and (s.get("technical") or 0) >= _STRONG_TECHNICAL and (rs or 0) >= 55),
        "top_40_in_sector": top if rank else None,
    }


def _exit_rule(detail: dict) -> str:
    comps = (detail.get("technical") or {}).get("components") or {}
    swing = (comps.get("trend_structure") or {}).get("last_swing_low")
    sma50 = (comps.get("moving_averages") or {}).get("sma50")
    levels = [f"a close below the last swing low ({swing})" if swing else None, f"the 50-day average ({sma50})" if sma50 else None]
    levels = [x for x in levels if x]
    return "exit on " + " or ".join(levels) if levels else "exit on a close below the 50-day average"


def decide(s: dict, detail: dict, rank: dict | None) -> dict:
    """`s`: the row's scores and labels (quality, fundamental, quantitative, relative_strength,
    technical, valuation, valuation_view, trend, quality_direction)."""
    q, t, rs, view = s.get("quality"), s.get("technical"), s.get("relative_strength"), s.get("valuation_view")
    g = gates(s, detail, rank)
    move = direction_of(detail, s.get("trend"), s.get("quality_direction"))
    why: list[str] = []
    timing_ok = t is not None and t >= 50
    poor_timing = t is not None and t < _WEAK_TECHNICAL

    if q is None:
        return {"classification": None, "action": None, "size": None, "gates": g, "why": ["no Quality Score yet"], "matrix": None}

    if g["red_flags"] and q >= 40:
        cls, action, size, matrix = "Replacement Candidate", "Replace", "None", "fails the core gate"
        why.append("fails the core gate: " + "; ".join(g["red_flags"]))
    elif g["tactical"]:
        cls, action, size, matrix = "Tactical Only", "Add on confirmation", "Tactical only", "Quality <40 + strong technical momentum"
        why.append(f"Quality {q:.0f} is below the gate; technical {t:.0f} and relative strength {rs:.0f} make it a trade, not a holding")
        why.append(_exit_rule(detail))
    elif q >= 65 and g["core"]:
        cls = "Core Quality"
        if move == "DECLINING":
            cls, action, size, matrix = "Investable", "Hold", "None", "Quality 65+ but declining"
            why.append("strong business whose quality is slipping: hold, but do not add until it steadies")
        elif view == "EXPENSIVE":
            action, size, matrix = "Hold", "Small", "Quality 65+ + Expensive"
            why.append("good business, wait for price: limited fresh allocation")
        elif poor_timing:
            action, size, matrix = "Add on confirmation", "Small", "Quality 65+ + weak technical"
            why.append("good business, poor timing: start small or wait for the trend to turn")
        else:
            action = "Add gradually" if timing_ok else "Add on confirmation"
            high = view in ("FAIR", "CHEAP") and (rs or 0) >= _STRONG_RS and (s.get("fundamental") or 0) >= 65 and g["preferred"]
            size = "High" if high else "Medium"
            matrix = ("Strong quality + Cheap + improving trend" if view == "CHEAP" and move == "IMPROVING"
                      else "Quality 65+ + Improving + Fair/Cheap" if move == "IMPROVING" else "Quality 65+ + Fair/Cheap")
            why.append("priority candidate" if matrix.startswith("Strong") else
                       "high-conviction candidate" if move == "IMPROVING" else "core quality at a reasonable price")
        if not g["preferred"] and cls == "Core Quality":
            why.append("not in the top 40% of its sector" if g["top_40_in_sector"] is False else "below the preferred-core bar")
    elif q >= 50 and g["core"]:
        cls = "Investable"
        if move == "IMPROVING":
            matrix = "Quality 50-64 + Improving"
            action = "Add gradually" if timing_ok and view != "EXPENSIVE" else "Add on confirmation"
            size = "Medium" if (rs or 0) >= 55 else "Small"
            why.append("investable, emerging quality")
        elif move == "DECLINING":
            action, size, matrix = "Watch", "None", "Quality 50-64 + Declining"
            why.append("passes the gate but quality is falling: do not add for now")
        else:
            action = "Hold" if view == "EXPENSIVE" or poor_timing else "Add on confirmation"
            size, matrix = "Small", "Quality 50-64 + Stable"
            why.append("investable but not improving")
    elif 40 <= q < 50:
        if g["recovery"]:
            cls, action, size, matrix = "Recovery Candidate", "Add on confirmation", "Small", "Quality 40-49 + Improving + strong relative strength"
            why.append("recovery candidate: small starter position only")
        elif move == "DECLINING":
            cls, action, size, matrix = "Replacement Candidate", "Replace", "None", "Quality 40-49 + Declining"
            why.append("borderline and deteriorating")
        else:
            cls, action, size, matrix = "Improving / Watch", "Watch", "None", "Quality 40-49"
            why.append("borderline: watch for improving momentum and relative strength" if move != "IMPROVING"
                       else "improving but relative strength or valuation not yet supportive")
    else:
        if move == "DECLINING" or q < 30:
            cls, action, size, matrix = "Avoid", "Avoid", "None", "Quality <40 + Declining" if move == "DECLINING" else "Quality <30"
            why.append("weak business" + (" and getting weaker" if move == "DECLINING" else ""))
        else:
            cls, action, size, matrix = "Replacement Candidate", "Replace", "None", "Quality <40"
            why.append("below the quality gate")
    if q < 50 and view == "CHEAP":
        why.append("cheap, but a cheap price does not repair a weak business: possible value trap")
    return {"classification": cls, "action": action, "size": size, "matrix": matrix, "direction_used": move, "gates": g, "why": why}


def interpretation(detail: dict) -> dict:
    """Section 20 "business interpretation": what is strong, weak, improving and
    deteriorating, and why the stock is out- or under-performing — read from the
    stored inputs, nothing invented."""
    labels = {"growth": "growth", "profitability": "profitability", "cash_flow": "cash flow", "balance_sheet": "balance sheet",
              "earnings_consistency": "earnings consistency", "durability": "durable returns on capital",
              "margin_resilience": "margin resilience", "predictability": "predictable profits",
              "capital_allocation": "capital allocation", "promoter_behaviour": "promoter behaviour",
              "management_credibility": "management credibility"}
    strong, weak = [], []
    for score in ("fundamental", "business_quality"):
        for name, part in ((detail.get(score) or {}).get("components") or {}).items():
            if name in labels and part.get("score") is not None:
                (strong if part["score"] >= 75 else weak if part["score"] <= 35 else []).append(labels[name])
    improving = [f"{x['signal']} ({x['reading']})" for x in (detail.get("trend") or {}).get("signals") or [] if x.get("vote", 0) > 0]
    worsening = [f"{x['signal']} ({x['reading']})" for x in (detail.get("trend") or {}).get("signals") or [] if x.get("vote", 0) < 0]
    qn = (detail.get("quantitative") or {}).get("components") or {}
    for name, label in (("margin_change", "operating margin"), ("return_change", "return on capital"), ("debt_change", "debt")):
        p = qn.get(name) or {}
        if p.get("score") is None:
            continue
        change = p.get("change_pts", p.get("change"))
        if p.get("reading"):
            (improving if p["score"] >= 75 else worsening if p["score"] <= 30 else []).append(f"{label}: {p['reading']}")
        elif p["score"] >= 75:
            improving.append(f"{label} (change {change:+})" if change is not None else label)
        elif p["score"] <= 30:
            worsening.append(f"{label} (change {change:+})" if change is not None else label)
    rs = detail.get("relative_strength") or {}
    vs_m = ((rs.get("components") or {}).get("vs_market") or {}).get("excess_pct") or {}
    perf = None
    if vs_m.get("1Y") is not None:
        perf = f"{'ahead of' if vs_m['1Y'] >= 0 else 'behind'} the Nifty 50 by {abs(vs_m['1Y']):.1f}% over a year"
    reasons = (rs.get("why_holding_up") or {}).get("reasons")
    return {"strong": strong, "weak": weak, "improving": improving, "deteriorating": worsening,
            "performance": perf, "why": reasons}
