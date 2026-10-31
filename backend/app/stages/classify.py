"""Weinstein stage classifier. Rules only, no model.

Each week is read in order, seeing only that week and earlier. A stage first has
to be possible (`_possible`: the moving average's direction, which side of it the
price is on, and what came before: a base follows a decline, a top an advance).
Its confidence is then the weight of its conditions that are met, out of those
that could be read. Missing data drops a condition; it never counts as failed.
A stock with no possible stage, or none reaching `min_confidence`, stays Unclassified.

A stage is slow by nature, so a running stage is held unless a rival beats it by
`switch_margin`, and a change must hold `confirm_weeks` in a row. Only a breakout
on volume into Stage 2 counts at once. Until then the stock keeps its stage and
`pending` names the change that is waiting.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from app.stages.indicators import Series

NAMES = {1: "Stage 1", 2: "Stage 2", 3: "Stage 3", 4: "Stage 4"}
EARLY, ESTABLISHED, LATE, WEAKENING = "Early Stage 2", "Established Stage 2", "Late Stage 2", "Stage 2 Weakening"


def _v(x) -> float | None:
    return None if x is None or not math.isfinite(x) else float(x)


def _cond(key: str, label: str, met, weight: int, value: str = "") -> dict:
    return {"key": key, "label": label, "met": None if met is None else bool(met), "weight": weight, "value": value}


def _gt(a, b) -> bool | None:
    return None if a is None or b is None else a > b


def _pct(x, signed: bool = True) -> str:
    return "" if x is None else f"{x:+.1f}%" if signed else f"{x:.1f}%"


def structure(s: Series, t: int, cfg: dict) -> tuple[bool | None, bool | None]:
    """(higher highs, higher lows) from the last two swing points known at week t."""
    since = t - int(cfg["structure_weeks"])
    highs = [p for known, i, p in s.swing_highs if known <= t and i >= since][-2:]
    lows = [p for known, i, p in s.swing_lows if known <= t and i >= since][-2:]
    return (highs[1] > highs[0] if len(highs) == 2 else None, lows[1] > lows[0] if len(lows) == 2 else None)


def facts(s: Series, t: int, cfg: dict) -> dict:
    c, sma = float(s.close[t]), _v(s.sma_long[t])
    hh, hl = structure(s, t, cfg)
    flat, no_low = cfg["flat_slope_pct"], int(cfg["no_new_low_weeks"])
    slope = _v(s.slope[t])
    earlier = s.low[max(0, t - 26):max(0, t - no_low + 1)]
    return {"close": c, "sma": sma, "sma10": _v(s.sma_short[t]), "slope": slope, "rising": slope is not None and slope > flat,
            "falling": slope is not None and slope < -flat, "flat": slope is not None and abs(slope) <= flat, "above": sma is not None and c > sma,
            "distance": (c / sma - 1) * 100 if sma else None, "hh": hh, "hl": hl, "rs": _v(s.rs[t]), "rs_change": _v(s.rs_change[t]), "rsi": _v(s.rsi[t]),
            "rsi_prior": _v(s.rsi[t - 4]) if t >= 4 else None, "macd": _v(s.macd[t]), "macd_signal": _v(s.macd_signal[t]),
            "volume_ratio": _v(s.volume_ratio[t]), "updown": _v(s.updown[t]), "resistance": _v(s.resistance[t]), "support": _v(s.support[t]),
            "high_52": _v(s.high_52[t]), "low_52": _v(s.low_52[t]), "range_pct": _v(s.range_pct[t]), "contraction": _v(s.contraction[t]),
            "weeks_above": int(s.weeks_above[t]), "no_new_low": bool(earlier.size) and float(s.low[max(0, t - no_low + 1):t + 1].min()) > float(earlier.min()),
            "failed_highs": sum(1 for known, i in s.failed_highs if known <= t and i >= t - 12),
            "high_distance": (c / float(s.high_52[t]) - 1) * 100 if _v(s.high_52[t]) else None,
            "sma_up_20w": _gt(sma, _v(s.sma_long[t - 20])) if t >= 20 else None}


def _evidence(f: dict, prior_up: bool | None, prior_down: bool | None, cfg: dict) -> dict[int, list[dict]]:
    """Weights in each stage add up to 100."""
    near = None if f["distance"] is None else abs(f["distance"]) <= cfg["near_sma_pct"]
    based = None if f["range_pct"] is None else f["range_pct"] <= cfg["base_range_pct"]
    contracting = None if f["contraction"] is None else f["contraction"] <= cfg["contraction_ratio"]
    bull = None if f["updown"] is None else f["updown"] >= cfg["updown_bull"]
    bear = None if f["updown"] is None else f["updown"] <= cfg["updown_bear"]
    rs_up = _gt(f["rs_change"], 0)
    near_high = None if f["high_distance"] is None else f["high_distance"] >= -cfg["near_high_pct"]
    short_over = _gt(f["sma10"], f["sma"])
    macd_over = _gt(f["macd"], f["macd_signal"])
    both_up = None if f["hh"] is None or f["hl"] is None else f["hh"] and f["hl"]
    both_down = None if f["hh"] is None or f["hl"] is None else not f["hh"] and not f["hl"]
    slope, dist, rs = _pct(f["slope"]), _pct(f["distance"]), "" if f["rs"] is None else f"{f['rs']:+.1f}"
    ud = "" if f["updown"] is None else f"{f['updown']:.2f}x"
    return {
        1: [_cond("sma_flat", "30-week average is flat", f["flat"], 25, slope),
            _cond("after_decline", "Follows a decline", prior_down, 20),
            _cond("consolidating", "Price is in a defined range", based, 20, _pct(f["range_pct"], False)),
            _cond("no_new_low", "Selling pressure easing: no new low lately", f["no_new_low"], 15),
            _cond("contracting", "Volatility has contracted", contracting, 10, "" if f["contraction"] is None else f"{f['contraction']:.2f}x"),
            _cond("near_sma", "Close near the 30-week average", near, 10, dist)],
        2: [_cond("above_sma", "Close above the 30-week average", f["above"], 20, dist),
            _cond("sma_rising", "30-week average is rising", f["rising"], 20, slope),
            _cond("short_over_long", "10-week average above the 30-week", short_over, 10),
            _cond("higher_highs_lows", "Higher highs and higher lows", both_up, 15),
            _cond("rs_positive", "Stronger than the Nifty 500", None if f["rs"] is None else f["rs"] > 0, 10, rs),
            _cond("rs_improving", "Relative strength improving", rs_up, 10),
            _cond("volume_up", "Up weeks carry more volume", bull, 10, ud),
            _cond("macd_up", "Weekly MACD above its signal", macd_over, 5)],
        3: [_cond("sma_flat", "30-week average has flattened", f["flat"], 20, slope),
            _cond("after_advance", "Follows an advance", prior_up, 20),
            _cond("range_near_highs", "Holding a range near the highs", None if based is None or near_high is None else based and near_high, 15, _pct(f["high_distance"])),
            _cond("rs_weakening", "Relative strength weakening", None if rs_up is None else not rs_up, 15, rs),
            _cond("failed_highs", "Recent new highs failed", f["failed_highs"] > 0, 10, str(f["failed_highs"])),
            _cond("distribution", "Down weeks carry more volume", bear, 10, ud),
            _cond("near_sma", "Close near the 30-week average", near, 10, dist)],
        4: [_cond("below_sma", "Close below the 30-week average", not f["above"], 20, dist),
            _cond("sma_falling", "30-week average is falling", f["falling"], 20, slope),
            _cond("short_under_long", "10-week average below the 30-week", None if short_over is None else not short_over, 10),
            _cond("lower_highs_lows", "Lower highs and lower lows", both_down, 15),
            _cond("rs_negative", "Weaker than the Nifty 500", None if f["rs"] is None else f["rs"] < 0, 10, rs),
            _cond("rs_falling", "Relative strength falling", None if rs_up is None else not rs_up, 10),
            _cond("volume_down", "Down weeks carry more volume", bear, 10, ud),
            _cond("macd_down", "Weekly MACD below its signal", None if macd_over is None else not macd_over, 5)],
    }


def _score(conds: list[dict]) -> float | None:
    read = [c for c in conds if c["met"] is not None]
    weight = sum(c["weight"] for c in read)
    return round(sum(c["weight"] for c in read if c["met"]) / weight * 100, 1) if weight >= 60 else None


def _possible(f: dict, prev: int | None, up_context: bool, down_context: bool, breakout_on_volume: bool, cfg: dict) -> set[int]:
    slope, tol = f["slope"], cfg["pullback_pct"] / 100
    out: set[int] = set()
    above, c, sma = f["above"], f["close"], f["sma"]
    # a running trend holds until its average actually turns; entering one needs a clear slope
    if (f["rising"] and (above or (prev == 2 and c >= sma * (1 - tol)))) or (prev == 2 and above and slope > 0):
        out.add(2)
    if prev == 1 and breakout_on_volume and above and slope >= -cfg["flat_slope_pct"]:
        out.add(2)
    if (f["falling"] and (not above or (prev == 4 and c <= sma * (1 + tol)))) or (prev == 4 and not above and slope < 0):
        out.add(4)
    if down_context and not (above and f["rising"]) and not (not above and f["falling"]):
        out.add(1)
    if up_context and not (above and f["rising"]) and not (not above and f["falling"]):
        out.add(3)
    return out


def sub_stage(f: dict, age: int, came_from: int | None, cfg: dict) -> str:
    """Stage 2 only. Trouble is checked first, so a stock is never Early and failing at once."""
    rs_falling = f["rs_change"] is not None and f["rs_change"] < 0
    if rs_falling and ((f["sma10"] is not None and f["close"] < f["sma10"]) or (f["rs"] is not None and f["rs"] < 0)):
        return WEAKENING
    extended = f["distance"] is not None and f["distance"] >= cfg["late_distance_pct"]
    fading = (age > cfg["early_weeks"] and f["macd"] is not None and f["macd_signal"] is not None and f["macd"] < f["macd_signal"]
              and f["rsi"] is not None and f["rsi_prior"] is not None and f["rsi"] < f["rsi_prior"])
    if extended or fading:
        return LATE
    return EARLY if came_from in (1, 4) and age <= cfg["early_weeks"] else ESTABLISHED


@dataclass
class Reading:
    t: int
    stage: int | None = None
    sub_stage: str | None = None
    confidence: float | None = None
    reason: str | None = None
    scores: dict = field(default_factory=dict)
    conditions: dict = field(default_factory=dict)
    event: str | None = None
    came_from: int | None = None
    age: int = 0
    since: int = 0
    pending: int | None = None
    facts: dict = field(default_factory=dict)


def _event(s: Series, t: int, cfg: dict) -> str | None:
    """A close through the range, first time in `event_gap_weeks`. "breakout_volume" when volume confirms."""
    def through(i):
        c, res, sup = s.close[i], s.resistance[i], s.support[i]
        return 1 if c > res else -1 if c < sup else 0     # nan compares False: no range yet
    side = through(t)
    if not side or any(through(i) == side for i in range(max(0, t - int(cfg["event_gap_weeks"])), t)):
        return None
    if side < 0:
        return "breakdown"
    ratio = _v(s.volume_ratio[t])
    return "breakout_volume" if ratio is not None and ratio >= cfg["breakout_volume"] else "breakout"


def replay(s: Series, cfg: dict) -> list[Reading]:
    """Classify every week in order. The stage carried forward is the only memory."""
    first = int(cfg["sma_long_weeks"] + cfg["slope_weeks"])
    out: list[Reading] = []
    prev, came_from, age, since = None, None, 0, 0
    pending, waited = None, 0
    for t in range(len(s.weeks)):
        r = Reading(t=t, event=_event(s, t, cfg))
        if t < first:
            r.reason = f"{t + 1} weeks of prices, {first + 1} needed"
            out.append(r)
            continue
        f = facts(s, t, cfg)
        r.facts = f
        prior_up = prev in (2, 3) if prev is not None else f["sma_up_20w"]
        prior_down = prev in (4, 1) if prev is not None else (None if f["sma_up_20w"] is None else not f["sma_up_20w"])
        evidence = _evidence(f, prior_up, prior_down, cfg)
        r.conditions = evidence
        r.scores = {k: _score(v) for k, v in evidence.items()}
        ratio = f["volume_ratio"]
        breakout = f["resistance"] is not None and f["close"] > f["resistance"] and ratio is not None and ratio >= cfg["breakout_volume"]
        possible = _possible(f, prev, bool(prior_up), bool(prior_down), breakout, cfg)
        ranked = sorted(((r.scores[k], k == prev, k) for k in possible if r.scores.get(k) is not None), reverse=True)
        best = ranked[0] if ranked else None
        held = r.scores.get(prev) if prev in possible else None
        if best and held is not None and held >= cfg["min_confidence"] and best[0] < held + cfg["switch_margin"]:
            best = (held, True, prev)
        if not best:
            r.reason, pending, waited = "The moving average, price and prior trend do not fit any stage", None, 0
        elif best[0] < cfg["min_confidence"]:
            r.reason, pending, waited = f"Best fit is {NAMES[best[2]]} at {best[0]:.0f}, below the {cfg['min_confidence']:.0f} needed", None, 0
        else:
            stage = best[2]
            if stage == prev or prev is None:
                pending, waited = None, 0
            else:
                pending, waited = stage, waited + 1 if stage == pending else 1
                if waited < cfg["confirm_weeks"] and not (stage == 2 and breakout):
                    stage = prev
                else:
                    pending, waited = None, 0
            r.stage, r.confidence, r.pending = stage, r.scores.get(stage), pending
            if stage != prev:
                came_from, age, since = prev, 0, t
            prev, age = stage, age + 1
            if stage == 2:
                r.sub_stage = sub_stage(f, age, came_from, cfg)
        r.came_from, r.age, r.since = came_from, age, since
        out.append(r)
    return out


def next_signal(r: Reading, cfg: dict) -> dict | None:
    """The move a stock's stage leads to, with five plain checks."""
    f = r.facts
    if r.stage is None:
        return None
    near, slope = cfg["near_level_pct"], f["slope"]
    rs_up = _gt(f["rs_change"], 0)
    bear = None if f["updown"] is None else f["updown"] <= cfg["updown_bear"]
    if r.stage == 1:
        to, checks = 2, [("Close above the 30-week average", f["above"]), ("30-week average has stopped falling", slope is not None and slope > -cfg["flat_slope_pct"]),
                         ("Close at or above resistance", f["resistance"] is not None and f["close"] >= f["resistance"] * (1 - near / 100)),
                         ("Volume expanding", f["volume_ratio"] is not None and f["volume_ratio"] >= cfg["breakout_volume"]), ("Relative strength improving", rs_up)]
    elif r.stage == 2:
        to, checks = 3, [("30-week average flattening", slope is not None and slope <= cfg["flat_slope_pct"]), ("Relative strength falling", None if rs_up is None else not rs_up),
                         ("Close under the 10-week average", f["sma10"] is not None and f["close"] < f["sma10"]), ("A recent new high failed", f["failed_highs"] > 0), ("Down weeks carry more volume", bear)]
    elif r.stage == 3:
        to, checks = 4, [("Close below the 30-week average", not f["above"]), ("30-week average turning down", slope is not None and slope < 0),
                         ("Close at or below support", f["support"] is not None and f["close"] <= f["support"] * (1 + near / 100)),
                         ("Weaker than the Nifty 500", None if f["rs"] is None else f["rs"] < 0), ("Down weeks carry more volume", bear)]
    else:
        to, checks = 1, [("30-week average flattening", slope is not None and slope >= -cfg["flat_slope_pct"]), ("No new low lately", f["no_new_low"]),
                         ("Close above the 10-week average", f["sma10"] is not None and f["close"] > f["sma10"]), ("Relative strength improving", rs_up),
                         ("Volatility contracting", f["contraction"] is not None and f["contraction"] <= cfg["contraction_ratio"])]
    met = sum(1 for _, m in checks if m)
    return {"from": r.stage, "to": to, "met": met, "of": len(checks), "watch": met >= cfg["signal_min_checks"], "checks": [{"label": a, "met": None if b is None else bool(b)} for a, b in checks]}


def explain(stage: int | None, sub: str | None, weeks: int | None, since: str | None, confidence: float | None, reason: str | None, conditions: list[dict]) -> str:
    """The stage in plain words, built only from the conditions that were read."""
    if stage is None:
        return f"Unclassified. {reason or 'Not enough evidence for any stage.'}"
    met = [c["label"][0].lower() + c["label"][1:] for c in conditions if c["met"]]
    lead = f"{sub or NAMES[stage]}, confidence {confidence:.0f}" if confidence is not None else (sub or NAMES[stage])
    return f"{lead}, for {weeks} week{'s' if weeks != 1 else ''} since {since}. Reads this way because: {'; '.join(met) or 'the stage is being held while a change confirms'}."
