"""Technical Score — "is price behaviour confirming strength or reversal?"
(framework section 7). Price and volume structure and timing only; returns
against benchmarks belong to Relative Strength (section 18).

Computed on the stored daily bars (app/prices/, split-adjusted closes, so a
bonus issue is not read as a crash), with the technical screener's own
engines where one exists: Wilder RSI (indicators/plugins/rsi.py), MACD
12/26/9 (indicators/plugins/macd.py) and RSI divergence (divergence/engine.py).

  trend structure         the last two swing highs and swing lows: higher
                          highs and higher lows, or lower ones
  moving averages         close against the 50- and 200-day averages, 50 against
                          200, and the 200-day's slope over a month
  RSI                     14-day RSI: 55-70 is momentum without excess
  MACD                    line against signal and zero, histogram rising or falling
  volume confirmation     volume on up days against down days over 50 days
  breakout / breakdown    close against the prior 60-day range, and a break of it
                          in the last 10 days on volume 1.5x the average
  base / contraction      the last 20 days' range against the 60 before it,
                          rewarded when tight and near the high
  reversal structure      a recent RSI divergence (bullish adds, bearish takes away)

A strong technical score never makes up for weak fundamentals: with Quality
below the gate the decision engine (phase 9) can only call the stock tactical.
"""
from __future__ import annotations

import statistics
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.calculations.scoring import _score_metric
from app.prices import store
from app.technical.divergence.engine import DivergenceConfig, detect_rsi_divergence
from app.technical.indicators.plugin import OHLCVBar
from app.technical.indicators.plugins.macd import MACDPlugin
from app.technical.indicators.plugins.rsi import RSIPlugin

_WEIGHTS = {"trend_structure": 0.20, "moving_averages": 0.20, "rsi": 0.10, "macd": 0.10, "volume": 0.10,
            "breakout": 0.15, "base": 0.10, "reversal": 0.05}
_MIN_BARS = 220
_PIVOT = 5


def ohlcv(db: Session, stock_id: str, end: date, days: int = 420) -> list[OHLCVBar]:
    rows = store.bars(db, stock_id, since=end - timedelta(days=days))
    out = []
    for b in rows:
        if b.bar_date > end:
            continue
        close = float(b.close)
        out.append(OHLCVBar(date=b.bar_date.isoformat(), open=float(b.open or close), high=float(b.high or close),
                            low=float(b.low or close), close=close, volume=float(b.volume or 0)))
    return out


def _pivots(values: list[float], high: bool) -> list[tuple[int, float]]:
    out = []
    for i in range(_PIVOT, len(values) - _PIVOT):
        window = values[i - _PIVOT:i + _PIVOT + 1]
        if values[i] == (max(window) if high else min(window)):
            out.append((i, values[i]))
    return out


def trend_structure(bars: list[OHLCVBar]) -> dict:
    recent = bars[-130:]
    highs, lows = _pivots([b.high for b in recent], True), _pivots([b.low for b in recent], False)
    if len(highs) < 2 or len(lows) < 2:
        return {"score": None, "reason": "too few swing points in six months"}
    hh, hl = highs[-1][1] > highs[-2][1], lows[-1][1] > lows[-2][1]
    reading = {(True, True): "higher highs and higher lows (uptrend)", (False, False): "lower highs and lower lows (downtrend)",
               (True, False): "higher highs but lower lows (widening)", (False, True): "higher lows but lower highs (tightening)"}[(hh, hl)]
    score = {(True, True): 95.0, (False, True): 60.0, (True, False): 40.0, (False, False): 10.0}[(hh, hl)]
    # a close under the last swing low breaks an uptrend; above the last swing high breaks a downtrend
    last = recent[-1].close
    if last < lows[-1][1]:
        score, reading = min(score, 25.0), reading + "; close below the last swing low"
    elif last > highs[-1][1]:
        score, reading = max(score, 75.0), reading + "; close above the last swing high"
    return {"score": score, "reading": reading, "last_swing_high": round(highs[-1][1], 2), "last_swing_low": round(lows[-1][1], 2)}


def moving_averages(bars: list[OHLCVBar]) -> dict:
    closes = [b.close for b in bars]
    if len(closes) < 221:
        return {"score": None, "reason": "fewer than 221 days of prices"}
    sma50, sma200 = statistics.fmean(closes[-50:]), statistics.fmean(closes[-200:])
    sma200_month_ago = statistics.fmean(closes[-221:-21])
    slope = (sma200 / sma200_month_ago - 1) * 100
    last = closes[-1]
    points = (30 if last > sma200 else 0) + (25 if last > sma50 else 0) + (25 if sma50 > sma200 else 0) + \
             (20 if slope > 0.5 else 10 if slope > -0.5 else 0)
    return {"score": float(points), "close": round(last, 2), "sma50": round(sma50, 2), "sma200": round(sma200, 2),
            "sma200_slope_1m_pct": round(slope, 2), "above_200": last > sma200, "golden_cross": sma50 > sma200}


def rsi(bars: list[OHLCVBar]) -> dict:
    value = RSIPlugin().calculate(bars, {"period": 14}).values.get("value")
    if value is None:
        return {"score": None, "reason": "not enough prices"}
    score = _score_metric(value, [(20, 10), (35, 25), (45, 45), (55, 75), (62, 95), (70, 90), (78, 65), (88, 40)])
    return {"score": round(float(score), 1), "rsi_14": float(value)}


def macd(bars: list[OHLCVBar]) -> dict:
    v = MACDPlugin().calculate(bars, {"fast": 12, "slow": 26, "signal": 9}).values
    if v.get("macd") is None:
        return {"score": None, "reason": "not enough prices"}
    above_signal, above_zero = v["histogram"] > 0, v["macd"] > 0
    rising = v["histogram"] > v["histogram_prev"]
    score = (40 if above_signal else 0) + (30 if above_zero else 0) + (30 if rising else 0)
    return {"score": float(score), "macd": v["macd"], "signal_line": v["signal_line"], "histogram": v["histogram"],
            "histogram_rising": rising}


def volume(bars: list[OHLCVBar]) -> dict:
    recent = bars[-51:]
    up = [b.volume for a, b in zip(recent, recent[1:]) if b.close > a.close]
    down = [b.volume for a, b in zip(recent, recent[1:]) if b.close < a.close]
    if len(up) < 5 or len(down) < 5 or not sum(down) or not any(b.volume for b in recent):
        return {"score": None, "reason": "no usable volume"}
    ratio = statistics.fmean(up) / statistics.fmean(down)
    return {"score": round(_score_metric(ratio, [(0.6, 5), (0.8, 30), (1.0, 50), (1.2, 70), (1.5, 90), (2.0, 100)]), 1),
            "up_day_to_down_day_volume": round(ratio, 2)}


def breakout(bars: list[OHLCVBar]) -> dict:
    if len(bars) < 75:
        return {"score": None, "reason": "fewer than 75 days of prices"}
    prior = bars[-70:-10]
    hi, lo = max(b.high for b in prior), min(b.low for b in prior)
    avg_vol = statistics.fmean(b.volume for b in bars[-60:-10]) or 0
    last10 = bars[-10:]
    broke_up = [b for b in last10 if b.close > hi and avg_vol and b.volume >= 1.5 * avg_vol]
    broke_down = [b for b in last10 if b.close < lo]
    position = (bars[-1].close - lo) / (hi - lo) if hi > lo else 0.5
    if broke_up and bars[-1].close > hi:
        return {"score": 100.0, "reading": f"broke above the 60-day high {hi:.2f} on volume on {broke_up[0].date}"}
    if broke_down and bars[-1].close < lo:
        return {"score": 5.0, "reading": f"broke below the 60-day low {lo:.2f} on {broke_down[0].date}"}
    score = _score_metric(position, [(0, 15), (0.25, 30), (0.5, 50), (0.75, 70), (1.0, 85), (1.2, 90)])
    return {"score": round(score, 1), "position_in_60_day_range": round(position, 2), "range_high": round(hi, 2),
            "range_low": round(lo, 2), "reading": "inside the range" if 0 <= position <= 1 else
            ("above the range without volume confirmation" if position > 1 else "below the range")}


def base(bars: list[OHLCVBar]) -> dict:
    if len(bars) < 252:
        return {"score": None, "reason": "less than a year of prices"}
    def span(chunk):
        return (max(b.high for b in chunk) / min(b.low for b in chunk) - 1) * 100
    tight, before = span(bars[-20:]), span(bars[-80:-20])
    contraction = tight / before if before else 1.0
    near_high = bars[-1].close / max(b.high for b in bars[-252:])
    score = _score_metric(contraction, [(0.2, 95), (0.35, 80), (0.5, 60), (0.75, 40), (1.0, 25), (1.5, 10)])
    score *= _score_metric(near_high, [(0.6, 0.4), (0.75, 0.7), (0.9, 1.0), (1.0, 1.0)])
    return {"score": round(score, 1), "range_20d_pct": round(tight, 1), "range_prior_60d_pct": round(before, 1),
            "close_to_52_week_high": round(near_high, 3)}


def reversal(bars: list[OHLCVBar]) -> dict:
    found = detect_rsi_divergence(bars, DivergenceConfig(max_pivot_rsi=45.0, min_pivot_rsi=55.0),
                                  div_types=["REGULAR_BULLISH", "REGULAR_BEARISH", "HIDDEN_BULLISH"])
    if not found:
        return {"score": 50.0, "reading": "no recent RSI divergence"}
    d = found[0]
    bullish = "BULLISH" in d.div_type
    return {"score": 85.0 if bullish else 15.0, "reading": f"{d.div_type.replace('_', ' ').lower()} RSI divergence",
            "pivot_dates": [d.pivot1.date, d.pivot2.date], "strength": round(d.strength_score, 1)}


def compute_technical(db: Session, stock_id: str, end: date | None) -> dict:
    if end is None:
        return {"score": None, "reason": "no stored prices", "components": {}}
    bars = ohlcv(db, stock_id, end)
    if len(bars) < 60:
        return {"score": None, "reason": "fewer than 60 days of stored prices", "components": {}}
    parts = {"trend_structure": trend_structure(bars), "moving_averages": moving_averages(bars), "rsi": rsi(bars),
             "macd": macd(bars), "volume": volume(bars), "breakout": breakout(bars), "base": base(bars),
             "reversal": reversal(bars)}
    for name, part in parts.items():
        part["weight"] = _WEIGHTS[name]
    scored = {n: p for n, p in parts.items() if p.get("score") is not None}
    covered = sum(p["weight"] for p in scored.values())
    score = round(sum(p["score"] * p["weight"] for p in scored.values()) / covered, 1) if covered >= 0.5 else None
    return {"score": score, "coverage": round(covered, 3), "components": parts, "as_of": end.isoformat(),
            "bars_used": len(bars), "source": "stored daily prices (split-adjusted), technical screener engines",
            "not_measured": ["price recovery after drawdown (in Relative Strength's resilience)"]}
