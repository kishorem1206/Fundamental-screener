import numpy as np
from app.technical.indicators.plugin import OHLCVBar, IndicatorResult


def _ema_series(values: list[float], period: int) -> list[float]:
    """Full EMA series seeded with SMA of the first `period` values."""
    if len(values) < period:
        return []
    k = 2.0 / (period + 1)
    ema = float(np.mean(values[:period]))
    series = [ema]
    for v in values[period:]:
        ema = v * k + ema * (1.0 - k)
        series.append(ema)
    return series


class MACDPlugin:
    """
    MACD indicator (Gerald Appel, 1970s).

    Formula (Investopedia standard):
      MACD line   = 12-period EMA − 26-period EMA
      Signal line = 9-period EMA of the MACD line
      Histogram   = MACD line − Signal line

    Values returned:
      macd              — MACD line today
      signal_line       — Signal line today
      histogram         — MACD − Signal (positive = bullish, negative = bearish)
      macd_prev         — MACD line yesterday (crossover detection)
      histogram_prev    — Histogram yesterday
      bullish_crossover — 1.0 if MACD crossed above Signal today, else 0.0
      bearish_crossover — 1.0 if MACD crossed below Signal today, else 0.0

    Signals:
      BULLISH_CROSSOVER  — MACD just crossed above Signal line (buy trigger)
      BEARISH_CROSSOVER  — MACD just crossed below Signal line (sell trigger)
      BULLISH            — MACD above Signal (histogram > 0), no crossover today
      BEARISH            — MACD below Signal (histogram < 0), no crossover today
      NEUTRAL            — histogram at zero
    """

    name = "macd"
    default_params = {"fast": 12, "slow": 26, "signal": 9}

    def calculate(self, bars: list[OHLCVBar], params: dict) -> IndicatorResult:
        fast  = int(params.get("fast",   self.default_params["fast"]))
        slow  = int(params.get("slow",   self.default_params["slow"]))
        sig_p = int(params.get("signal", self.default_params["signal"]))

        closes = [b.close for b in bars]

        _unknown_values = {
            "macd": None, "signal_line": None, "histogram": None,
            "macd_prev": None, "histogram_prev": None,
            "bullish_crossover": 0.0, "bearish_crossover": 0.0,
        }

        # Minimum bars: enough to seed the slow EMA and produce at least 2 signal values
        if len(closes) < slow + sig_p:
            return IndicatorResult(
                name=self.name, params=params,
                values=_unknown_values, signal="UNKNOWN",
            )

        fast_ema = _ema_series(closes, fast)
        slow_ema = _ema_series(closes, slow)

        # fast_ema has (len-fast+1) values starting from index fast-1
        # slow_ema has (len-slow+1) values starting from index slow-1
        # Align by trimming the extra fast values at the start
        offset = slow - fast
        macd_line = [f - s for f, s in zip(fast_ema[offset:], slow_ema)]

        if len(macd_line) < sig_p + 1:
            return IndicatorResult(
                name=self.name, params=params,
                values=_unknown_values, signal="UNKNOWN",
            )

        signal_line = _ema_series(macd_line, sig_p)

        # signal_line[i] aligns with macd_line[sig_p - 1 + i]
        macd_aligned = macd_line[sig_p - 1:]

        if len(signal_line) < 2:
            return IndicatorResult(
                name=self.name, params=params,
                values=_unknown_values, signal="UNKNOWN",
            )

        macd_val       = round(macd_aligned[-1],  4)
        signal_val     = round(signal_line[-1],   4)
        histogram      = round(macd_val - signal_val, 4)
        macd_prev      = round(macd_aligned[-2],  4)
        signal_prev    = round(signal_line[-2],   4)
        histogram_prev = round(macd_prev - signal_prev, 4)

        crossed_above = macd_prev < signal_prev and macd_val >= signal_val
        crossed_below = macd_prev > signal_prev and macd_val <= signal_val

        if crossed_above:
            signal = "BULLISH_CROSSOVER"
        elif crossed_below:
            signal = "BEARISH_CROSSOVER"
        elif histogram > 0:
            signal = "BULLISH"
        elif histogram < 0:
            signal = "BEARISH"
        else:
            signal = "NEUTRAL"

        return IndicatorResult(
            name=self.name,
            params={"fast": fast, "slow": slow, "signal": sig_p},
            values={
                "macd":              macd_val,
                "signal_line":       signal_val,
                "histogram":         histogram,
                "macd_prev":         macd_prev,
                "histogram_prev":    histogram_prev,
                "bullish_crossover": 1.0 if crossed_above else 0.0,
                "bearish_crossover": 1.0 if crossed_below else 0.0,
            },
            signal=signal,
        )


macd_plugin = MACDPlugin()
