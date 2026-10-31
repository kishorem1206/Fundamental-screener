"""Reward/risk from stored prices. A rule of thumb from chart levels, not a forecast.

  invalidation   the nearest structural level at least `min_stop_pct` under the
                 price: the last daily swing low, `sma_cushion_pct` under the
                 30-week average, or the 20-week low. With none that far, the
                 deepest level under the price, and the downside counts as
                 `min_stop_pct` so a tight level cannot produce an absurd ratio
  target         the 30-week average when the price is under it (first overhead
                 resistance); else the 52-week high when `target_gap_pct` above;
                 else a measured move, the 20-week range on top of resistance
  ratio          upside ÷ downside from the current price
"""
from __future__ import annotations

from app.calculations.scoring import _score_metric

_SCORE = [(0.5, 10), (1.0, 30), (1.5, 50), (2.0, 65), (3.0, 85), (4.0, 100)]


def _entry(stage: int | None, close: float, sma30, sma10, resistance, cfg: dict) -> dict:
    if stage == 2 and sma30 and sma10 and sma10 > sma30:
        return {"entry_low": sma30, "entry_high": sma10, "in_zone": sma30 <= close <= sma10, "entry_note": "A pullback between the 30- and 10-week averages"}
    if stage == 1 and resistance:
        high = round(resistance * (1 + cfg["entry_band_pct"] / 100), 2)
        return {"entry_low": resistance, "entry_high": high, "in_zone": resistance <= close <= high, "entry_note": "Just above resistance, on a breakout"}
    note = f"No entry zone in Stage {stage}" if stage in (3, 4) else "No entry zone until the stage is clear"
    return {"entry_low": None, "entry_high": None, "in_zone": False, "entry_note": note}


def compute(close, stage, sma30, sma10, high_52w, resistance, support, swing_low, cfg: dict) -> dict:
    empty = {"ratio": None, "score": None, "upside_pct": None, "downside_pct": None, "invalidation": None, "invalidation_basis": None, "target": None, "target_basis": None}
    if not close:
        return {**empty, "entry_low": None, "entry_high": None, "in_zone": False, "entry_note": "No price", "reason": "No price on record"}
    entry = _entry(stage, close, sma30, sma10, resistance, cfg)
    levels = [(swing_low, "the last swing low"), (sma30 * (1 - cfg["sma_cushion_pct"] / 100) if sma30 else None, "under the 30-week average"), (support, "the 20-week low")]
    under = [(v, name) for v, name in levels if v and v < close]
    far = [x for x in under if x[0] <= close * (1 - cfg["min_stop_pct"] / 100)]
    if sma30 and close < sma30:
        target, target_basis = sma30, "the 30-week average"
    elif high_52w and high_52w >= close * (1 + cfg["target_gap_pct"] / 100):
        target, target_basis = high_52w, "the 52-week high"
    elif resistance and support and resistance > support:
        target, target_basis = max(resistance, close) + (resistance - support), "a measured move from the 20-week range"
    else:
        target, target_basis = None, None
    if not under or not target:
        return {**empty, **entry, "reason": "The price is under every structural level" if not under else "No level to aim for above the price"}
    invalidation, basis = max(far) if far else min(under)
    upside, downside = (target / close - 1) * 100, max((1 - invalidation / close) * 100, cfg["min_stop_pct"])
    ratio = upside / downside
    return {"ratio": round(ratio, 2), "score": round(_score_metric(ratio, _SCORE), 1), "upside_pct": round(upside, 1), "downside_pct": round(downside, 1),
            "invalidation": round(invalidation, 2), "invalidation_basis": basis, "target": round(target, 2), "target_basis": target_basis, **entry}
