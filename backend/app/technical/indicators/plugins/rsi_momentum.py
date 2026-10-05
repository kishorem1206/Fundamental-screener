import numpy as np
from app.technical.indicators.plugin import OHLCVBar, IndicatorResult

_FLAT_THRESHOLD = 0.5  # RSI change smaller than this counts as sideways


def _compute_rsi_series(closes: list[float], period: int = 14) -> list[float]:
    """Full RSI series using Wilder's smoothing (same algorithm as rsi.py)."""
    if len(closes) < period + 2:
        return []

    arr = np.array(closes, dtype=float)
    deltas = np.diff(arr)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)

    avg_gain = float(np.mean(gains[:period]))
    avg_loss = float(np.mean(losses[:period]))

    def _rsi(ag: float, al: float) -> float:
        return 100.0 if al == 0 else round(100.0 - 100.0 / (1.0 + ag / al), 2)

    series = [_rsi(avg_gain, avg_loss)]
    for g, l in zip(gains[period:], losses[period:]):
        avg_gain = (avg_gain * (period - 1) + g) / period
        avg_loss = (avg_loss * (period - 1) + l) / period
        series.append(_rsi(avg_gain, avg_loss))

    return series


class RSIMomentumPlugin:
    """
    Detects fresh RSI breakouts and stocks approaching the threshold.

    Values returned (all floats for filter-engine compatibility):
      rsi_today         — current RSI
      rsi_prev          — yesterday's RSI
      rsi_change        — today minus yesterday
      distance_to_60    — threshold minus rsi_today (negative = already above)
      rsi_trend         — 1=RISING, 0=FLAT, -1=FALLING (3-period direction)
      above_60_in_20d   — 1.0 if any of prev lookback_days RSI >= threshold else 0.0
      days_since_above_60 — days ago RSI was last >= threshold (999 = never in history)
      signal_rank       — FRESH_BREAKOUT=5, APPROACHING=4, ALREADY_STRONG=3,
                          EXTENDED=2, NEUTRAL=1
    """

    name = "rsi_momentum"
    default_params = {"period": 14, "lookback_days": 50, "threshold": 60.0}

    def calculate(self, bars: list[OHLCVBar], params: dict) -> IndicatorResult:
        period = int(params.get("period", 14))
        lookback = int(params.get("lookback_days", 20))
        threshold = float(params.get("threshold", 60.0))
        approaching_zone = threshold - 5.0

        closes = [b.close for b in bars]
        rsi_series = _compute_rsi_series(closes, period)

        if len(rsi_series) < 2:
            return IndicatorResult(
                name=self.name,
                params=params,
                values={
                    "rsi_today": None, "rsi_prev": None, "rsi_change": None,
                    "distance_to_60": None, "rsi_trend": 0.0,
                    "above_60_in_20d": 0.0, "days_since_above_60": 999.0,
                    "signal_rank": 0.0,
                },
                signal="UNKNOWN",
            )

        rsi_today = rsi_series[-1]
        rsi_prev = rsi_series[-2]
        rsi_change = round(rsi_today - rsi_prev, 2)
        distance_to_60 = round(threshold - rsi_today, 2)

        # Trend: today vs yesterday RSI
        if rsi_change > _FLAT_THRESHOLD:
            rsi_trend = 1.0   # RISING
        elif rsi_change < -_FLAT_THRESHOLD:
            rsi_trend = -1.0  # FALLING
        else:
            rsi_trend = 0.0   # FLAT (sideways)

        # Previous `lookback` RSI values (exclude today)
        if len(rsi_series) >= lookback + 1:
            prev_vals = rsi_series[-(lookback + 1):-1]
        else:
            prev_vals = rsi_series[:-1]

        above_in_lookback = any(r >= threshold for r in prev_vals)

        # Days since last above threshold (1 = yesterday)
        days_since = 999.0
        for i, r in enumerate(reversed(prev_vals)):
            if r >= threshold:
                days_since = float(i + 1)
                break

        # Signal priority: FRESH_BREAKOUT > APPROACHING_AGAIN > APPROACHING > EXTENDED > ALREADY_STRONG > NEUTRAL
        if rsi_prev < threshold and rsi_today >= threshold and not above_in_lookback:
            # RSI just crossed threshold for first time in lookback window
            signal = "FRESH_BREAKOUT"
            signal_rank = 5.0
        elif approaching_zone <= rsi_today < threshold and above_in_lookback:
            # Was above threshold in lookback, has pulled back into approaching zone — second-chance entry
            signal = "APPROACHING_AGAIN"
            signal_rank = 4.5
        elif approaching_zone <= rsi_today < threshold and rsi_change > 0 and not above_in_lookback:
            # Approaching threshold for the first time, rising
            signal = "APPROACHING"
            signal_rank = 4.0
        elif rsi_today >= 70:
            # Extended regardless of history — RSI >= 70 is always extended
            signal = "EXTENDED"
            signal_rank = 2.0
        elif rsi_today >= threshold:
            signal = "ALREADY_STRONG"
            signal_rank = 3.0
        else:
            signal = "NEUTRAL"
            signal_rank = 1.0

        return IndicatorResult(
            name=self.name,
            params={"period": period, "lookback_days": lookback, "threshold": threshold},
            values={
                "rsi_today": rsi_today,
                "rsi_prev": rsi_prev,
                "rsi_change": rsi_change,
                "distance_to_60": distance_to_60,
                "rsi_trend": rsi_trend,
                "above_60_in_20d": 1.0 if above_in_lookback else 0.0,
                "days_since_above_60": days_since,
                "signal_rank": signal_rank,
            },
            signal=signal,
        )


rsi_momentum_plugin = RSIMomentumPlugin()
