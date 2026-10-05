import pandas as pd
from app.technical.indicators.plugin import OHLCVBar, IndicatorResult


class BollingerBandsPlugin:
    name = "bollinger"
    default_params = {"period": 20, "std_dev": 2.0}

    def calculate(self, bars: list[OHLCVBar], params: dict) -> IndicatorResult:
        period = int(params.get("period", self.default_params["period"]))
        std_dev_mult = float(params.get("std_dev", self.default_params["std_dev"]))
        closes = [b.close for b in bars]

        if len(closes) < period:
            return IndicatorResult(
                name=self.name,
                params={"period": period, "std_dev": std_dev_mult},
                values={"upper": None, "middle": None, "lower": None, "percent_b": None, "bandwidth": None},
                signal="UNKNOWN",
            )

        series = pd.Series(closes)
        sma = series.rolling(period).mean().iloc[-1]
        std = series.rolling(period).std(ddof=0).iloc[-1]  # ddof=0 matches TradingView

        upper = round(float(sma + std_dev_mult * std), 4)
        middle = round(float(sma), 4)
        lower = round(float(sma - std_dev_mult * std), 4)
        last_price = closes[-1]

        band_width = upper - lower
        percent_b = round((last_price - lower) / band_width, 4) if band_width != 0 else 0.5
        bandwidth = round(band_width / middle, 4) if middle != 0 else 0.0

        if percent_b < 0.05:
            signal = "NEAR_LOWER"
        elif percent_b > 0.95:
            signal = "NEAR_UPPER"
        else:
            signal = "NEUTRAL"

        return IndicatorResult(
            name=self.name,
            params={"period": period, "std_dev": std_dev_mult},
            values={
                "upper": upper,
                "middle": middle,
                "lower": lower,
                "percent_b": percent_b,
                "bandwidth": bandwidth,
            },
            signal=signal,
        )


bollinger_plugin = BollingerBandsPlugin()
