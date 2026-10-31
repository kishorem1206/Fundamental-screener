"""The five dimensions, the combined score, the gates and the written assessment.
Pure functions over stored values. `fw` is a stock's framework row, `stage` its
Stage Screener row or None. Nothing is estimated: a missing input drops out and
lowers confidence.

Trend counts once: Technical and the stage share one dimension, and that dimension
uses only the stage label, so the stage's relative-strength conditions are not
counted again. Quality already contains Fundamental, so only Quality is weighted.
"""
from __future__ import annotations

from app.stages import classify as stages

HIGH, STRONG, EARLY, WATCH, CAUTION, LOW, NOT_RATED = "High Priority", "Strong Candidate", "Early Opportunity", "Watchlist", "Caution", "Low Priority", "Not Rated"
CLASSES = (HIGH, STRONG, EARLY, WATCH, CAUTION, LOW, NOT_RATED)
_SUB_FIT = {stages.ESTABLISHED: "fit_established", stages.EARLY: "fit_early", stages.LATE: "fit_late", stages.WEAKENING: "fit_weakening"}
_DIMENSIONS = (("fundamental_quality", "weight_quality"), ("technical_stage", "weight_technical"), ("relative_strength", "weight_rs"),
               ("valuation", "weight_valuation"), ("risk_reward", "weight_risk_reward"))


def stage_fit(stage: dict | None, cfg: dict) -> float | None:
    if not stage or stage.get("stage") is None:
        return None
    if stage["stage"] == 2:
        return cfg[_SUB_FIT.get(stage.get("sub_stage"), "fit_established")]
    return cfg[f"fit_stage_{stage['stage']}"]


def technical_stage(technical: float | None, fit: float | None, cfg: dict) -> float | None:
    if technical is None or fit is None:
        return technical if fit is None else fit
    share = cfg["stage_share"] / 100
    return round(technical * (1 - share) + fit * share, 1)


def combined(scores: dict[str, float | None], cfg: dict) -> tuple[float | None, float]:
    """Weighted average of the dimensions that have data, and the share of weight they carry."""
    have = [(scores[name], cfg[weight]) for name, weight in _DIMENSIONS if scores.get(name) is not None]
    carried = sum(w for _, w in have)
    if not carried or carried < cfg["min_coverage"] or scores.get("fundamental_quality") is None:
        return None, round(carried, 1)
    return round(sum(s * w for s, w in have) / carried, 1), round(carried, 1)


def confidence(fw: dict, stage: dict | None, scores: dict, unread_result: bool, cfg: dict) -> tuple[float, str, list[str]]:
    points, notes = 100.0, []

    def lose(amount: float, note: str) -> None:
        nonlocal points
        points -= amount
        notes.append(note)
    for name, weight in _DIMENSIONS:
        if scores.get(name) is None:
            lose(20, f"no {name.replace('_', ' ')} reading")
    coverage = ((fw.get("detail") or {}).get("fundamental") or {}).get("coverage")
    if coverage is not None and coverage < 0.7:
        lose(15, f"fundamental data covers {coverage:.0%}")
    if unread_result:
        lose(15, "a new result is not read yet")
    if stage and stage.get("provisional"):
        lose(10, "the week is still open")
    if stage and stage.get("confidence") is not None and stage["confidence"] < 60:
        lose(10, f"stage confidence is only {stage['confidence']:.0f}")
    points = max(points, 0.0)
    return points, ("High" if points >= cfg["high_confidence"] else "Low" if points < cfg["low_confidence"] else "Medium"), notes


def classify(fw: dict, stage: dict | None, total: float | None, rr: dict, confidence_label: str, cfg: dict) -> dict:
    """Gates in order. `high_gates` lists what High Priority needs, passed or not."""
    quality, view, rs = fw.get("quality"), fw.get("valuation_view"), fw.get("relative_strength")
    gates = ((fw.get("detail") or {}).get("decision") or {}).get("gates") or {}
    flags = list(gates.get("red_flags") or [])
    number = (stage or {}).get("stage")
    sub = (stage or {}).get("sub_stage")
    ratio = rr.get("ratio")
    poor = ratio is not None and ratio < cfg["poor_reward_risk"]
    warnings = []
    if view == "EXPENSIVE":
        warnings.append("valuation is Expensive")
    if fw.get("quality_direction") == "DECLINING":
        warnings.append("Quality is declining")
    if sub == stages.LATE:
        warnings.append("Late Stage 2: extended or losing momentum")
    if sub == stages.WEAKENING:
        warnings.append("Stage 2 is weakening")
    if poor:
        warnings.append(f"reward/risk is poor at {ratio:.1f}")
    if number == 3:
        warnings.append("Stage 3: the advance may be topping")
    if number == 4:
        warnings.append("Stage 4: price is in a downtrend")
    high_gates = [
        {"gate": "Established Stage 2", "passed": sub == stages.ESTABLISHED},
        {"gate": f"Quality {cfg['high_quality']:.0f}+", "passed": (quality or 0) >= cfg["high_quality"]},
        {"gate": f"Combined {cfg['high_combined']:.0f}+", "passed": (total or 0) >= cfg["high_combined"]},
        {"gate": f"Reward/risk {cfg['high_reward_risk']:g}+", "passed": (ratio or 0) >= cfg["high_reward_risk"]},
        {"gate": f"Relative Strength {cfg['high_rs']:.0f}+", "passed": (rs or 0) >= cfg["high_rs"]},
        {"gate": "Relative strength improving", "passed": (stage or {}).get("rs_improving") is True},
        {"gate": "Valuation Fair or Cheap", "passed": view in ("FAIR", "CHEAP")},
        {"gate": "Quality not declining", "passed": fw.get("quality_direction") != "DECLINING"},
        {"gate": "Confidence not Low", "passed": confidence_label != "Low"},
        {"gate": "No red flag", "passed": not flags},
    ]

    def result(name: str, why: str) -> dict:
        return {"classification": name, "why": why, "warnings": warnings, "high_gates": high_gates}

    if quality is None or total is None:
        return result(NOT_RATED, "Not enough data to rate this stock")
    if (stage or {}).get("reason", "") and str(stage["reason"]).startswith("No trade"):
        return result(NOT_RATED, stage["reason"])
    if flags:
        return result(LOW, "Fails the core gate: " + "; ".join(flags))
    if quality < cfg["floor_quality"]:
        return result(LOW, f"Quality {quality:.0f} is under {cfg['floor_quality']:.0f}")
    if quality < 50:
        healthy = number == 2 and sub != stages.WEAKENING
        return result(WATCH if healthy else LOW, f"Quality {quality:.0f} is below the gate of 50" + (", but the stock is in a healthy Stage 2" if healthy else ""))
    if number in (3, 4):
        return result(CAUTION, f"Quality passes, but Stage {number} restricts it")
    if number == 2 and sub == stages.EARLY or number == 1 and (stage or {}).get("next_stage") == 2:
        if poor:
            return result(WATCH, "A possible early move, but reward/risk is poor")
        return result(EARLY, "Early Stage 2" if number == 2 else "Stage 1 showing most of the checks for Stage 2")
    if number == 2 and sub != stages.WEAKENING:
        if all(g["passed"] for g in high_gates):
            return result(HIGH, "Every gate passes")
        if total >= cfg["strong_combined"] and (ratio or 0) >= cfg["strong_reward_risk"]:
            return result(STRONG, f"Stage 2 with combined {total:.0f} and reward/risk {ratio:.1f}")
    return result(WATCH, "Passes the quality gate, but stage, reward/risk or the combined score is not there yet")


def _join(items: list[str]) -> str:
    return ", ".join(items)


def dimensions(fw: dict, stage: dict | None, rr: dict, rs_windows: dict, scores: dict, fit: float | None) -> list[dict]:
    detail = fw.get("detail") or {}
    components = (detail.get("fundamental") or {}).get("components") or {}
    parts = [f"{n.replace('_', ' ')} {components[n]['score']:.0f}" for n in ("growth", "profitability", "cash_flow", "balance_sheet") if (components.get(n) or {}).get("score") is not None]
    number, sub = (stage or {}).get("stage"), (stage or {}).get("sub_stage")
    stage_label = sub or (f"Stage {number}" if number else "Unclassified")
    windows = [f"{k} {v:+.1f}%" for k, v in rs_windows.items() if v is not None]
    direction = None if not stage or stage.get("rs_improving") is None else "Improving" if stage["rs_improving"] else "Deteriorating"
    val = detail.get("valuation") or {}
    vc = val.get("components") or {}
    hist, peer, deep = vc.get("pe_vs_history") or vc.get("pb_vs_history") or {}, vc.get("pe_vs_sector") or vc.get("pb_vs_sector") or {}, vc.get("deep_report") or {}
    bits = []
    if hist.get("current_pe") is not None:
        bits.append(f"P/E {hist['current_pe']} against its own median {hist.get('median_pe')}")
    elif hist.get("current_pb") is not None:
        bits.append(f"P/B {hist['current_pb']} against its own median {hist.get('median_pb')}")
    if peer.get("sector_median_pe") is not None:
        bits.append(f"peers' median P/E {peer['sector_median_pe']}")
    if deep.get("upside_pct") is not None:
        bits.append(f"margin of safety {deep['upside_pct']:+.0f}% to the deep report's value")
    technical = fw.get("technical")
    return [
        {"key": "fundamental_quality", "name": "Fundamental Quality", "score": scores["fundamental_quality"], "label": ((detail.get("quality") or {}).get("band") or "—").replace("_", " ").title(), "status": "Existing",
         "text": f"Quality = 70% Fundamental + 30% Business Quality. {_join(parts).capitalize()}." if parts else "Quality = 70% Fundamental + 30% Business Quality."},
        {"key": "technical_stage", "name": "Technical Stage", "score": scores["technical_stage"], "label": stage_label, "status": "Enhanced",
         "text": f"Technical {technical:.0f}" if technical is not None else "No Technical score", "fit": fit},
        {"key": "relative_strength", "name": "Relative Strength", "score": scores["relative_strength"], "label": direction or "—", "status": "Existing, Nifty 500 view new",
         "text": f"Against the Nifty 500: {_join(windows)}." if windows else "No Nifty 500 comparison yet."},
        {"key": "valuation", "name": "Valuation", "score": scores["valuation"], "label": (fw.get("valuation_view") or "—").title(), "status": "Existing",
         "text": (_join(bits).capitalize() + ".") if bits else (val.get("reason") or "No valuation measures.")},
        {"key": "risk_reward", "name": "Risk/Reward", "score": scores["risk_reward"], "label": f"{rr['ratio']:.1f} to 1" if rr.get("ratio") is not None else "—", "status": "New",
         "text": f"{rr['upside_pct']:+.0f}% to {rr['target_basis']}, -{rr['downside_pct']:.0f}% to {rr['invalidation_basis']}." if rr.get("ratio") is not None else rr.get("reason", "Not available.")},
    ]


def assess(fw: dict, stage: dict | None, rr: dict, rs_windows: dict, cfg: dict) -> tuple[list[dict], list[dict]]:
    """(why it qualifies, what could invalidate it). Every line comes from stored values."""
    detail = fw.get("detail") or {}
    interp = (detail.get("decision") or {}).get("interpretation") or {}
    quality, view, rs = fw.get("quality"), fw.get("valuation_view"), fw.get("relative_strength")
    number, sub = (stage or {}).get("stage"), (stage or {}).get("sub_stage")
    ratio = rr.get("ratio")
    year = rs_windows.get("12M")
    good, bad = [], []
    if quality is not None and quality >= 50:
        strong = interp.get("strong") or []
        good.append({"area": "Fundamental", "text": f"Quality {quality:.0f}" + (f": {_join(strong[:4])}" if strong else "")})
    if number == 2:
        good.append({"area": "Technical", "text": f"{sub or 'Stage 2'} for {stage.get('weeks_in_stage')} weeks, close {stage.get('sma_distance_pct') or 0:+.1f}% from the 30-week average"})
    elif number == 1:
        good.append({"area": "Technical", "text": "Stage 1: building a base after a decline"})
    if (fw.get("technical") or 0) >= 65:
        good.append({"area": "Technical", "text": f"Technical score {fw['technical']:.0f}"})
    if (rs or 0) >= cfg["high_rs"] or (stage or {}).get("rs_improving"):
        text = f"Relative Strength {rs:.0f}" if rs is not None else "Relative strength"
        if year is not None:
            text += f", {year:+.1f}% against the Nifty 500 over 12 months"
        good.append({"area": "Relative strength", "text": text + (", improving" if (stage or {}).get("rs_improving") else "")})
    if view in ("CHEAP", "FAIR"):
        good.append({"area": "Valuation", "text": f"Valuation reads {view.title()}"})
    if ratio is not None and ratio >= cfg["strong_reward_risk"]:
        good.append({"area": "Reward/risk", "text": f"{ratio:.1f} to 1: target {rr['target']:,.0f}, invalidation {rr['invalidation']:,.0f}"})

    if quality is not None and quality >= 50:
        bad.append({"area": "Fundamental", "text": f"Quality falling under the gate of 50, from {quality:.0f}"})
    if fw.get("quality_direction") == "DECLINING":
        bad.append({"area": "Fundamental", "text": "Quality is already declining"})
    for item in (interp.get("deteriorating") or [])[:2]:
        bad.append({"area": "Fundamental", "text": f"Deteriorating: {item}"})
    if rr.get("invalidation") is not None:
        bad.append({"area": "Technical", "text": f"A weekly close under {rr['invalidation']:,.0f} ({rr['invalidation_basis']})"})
    if number == 2:
        bad.append({"area": "Technical", "text": "The 30-week average turning flat or down, which would point to Stage 3"})
    signal = ((stage or {}).get("detail") or {}).get("signal")
    if signal and signal["met"]:
        bad.append({"area": "Technical", "text": f"Stage {signal['from']} to {signal['to']} checks: {signal['met']} of {signal['of']} met"})
    if (stage or {}).get("rs_improving") is False:
        bad.append({"area": "Relative strength", "text": "Relative strength is already falling against the Nifty 500"})
    elif (stage or {}).get("rs") is not None and stage["rs"] > 0:
        bad.append({"area": "Relative strength", "text": "Relative strength against the Nifty 500 turning negative"})
    if view == "EXPENSIVE":
        bad.append({"area": "Valuation", "text": "Valuation reads Expensive, so a good result may already be priced in"})
    if ratio is not None and ratio < cfg["strong_reward_risk"]:
        bad.append({"area": "Reward/risk", "text": f"Only {ratio:.1f} to 1 from here"})
    return good, bad


def build(fw: dict, stage: dict | None, rr: dict, rs_windows: dict, unread_result: bool, cfg: dict) -> dict:
    fit = stage_fit(stage, cfg)
    scores = {"fundamental_quality": fw.get("quality"), "technical_stage": technical_stage(fw.get("technical"), fit, cfg),
              "relative_strength": fw.get("relative_strength"), "valuation": fw.get("valuation"), "risk_reward": rr.get("score")}
    total, carried = combined(scores, cfg)
    points, label, notes = confidence(fw, stage, scores, unread_result, cfg)
    verdict = classify(fw, stage, total, rr, label, cfg)
    good, bad = assess(fw, stage, rr, rs_windows, cfg)
    return {"combined": total, "coverage": carried, "confidence": points, "confidence_label": label, "confidence_notes": notes, **verdict, "scores": scores,
            "dimensions": dimensions(fw, stage, rr, rs_windows, scores, fit), "qualifies": good, "invalidates": bad}
