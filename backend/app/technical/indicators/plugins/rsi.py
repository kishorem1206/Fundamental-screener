import numpy as np
from app.technical.indicators.plugin import OHLCVBar, IndicatorResult


class RSIPlugin:
    name = "rsi"
    default_params = {"period": 14}

    def calculate(self, bars: list[OHLCVBar], params: dict) -> IndicatorResult:
        period = int(params.get("period", self.default_params["period"]))
        closes = [b.close for b in bars]

        if len(closes) < period + 1:
            return IndicatorResult(
                name=self.name,
                params={"period": period},
                values={"value": None},
                signal="UNKNOWN",
            )

        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0.0)
        losses = np.where(deltas < 0, -deltas, 0.0)

        # Seed with SMA of first `period` values — matches TradingView's RSI exactly
        avg_gain = float(np.mean(gains[:period]))
        avg_loss = float(np.mean(losses[:period]))

        # Then apply Wilder's smoothing (RMA) for the remainder
        for g, l in zip(gains[period:], losses[period:]):
            avg_gain = (avg_gain * (period - 1) + g) / period
            avg_loss = (avg_loss * (period - 1) + l) / period

        if avg_loss == 0:
            rsi = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi = round(100.0 - (100.0 / (1.0 + rs)), 2)

        if rsi < 30:
            signal = "OVERSOLD"
        elif rsi > 70:
            signal = "OVERBOUGHT"
        else:
            signal = "NEUTRAL"

        return IndicatorResult(
            name=self.name,
            params={"period": period},
            values={"value": rsi},
            signal=signal,
        )


rsi_plugin = RSIPlugin()
