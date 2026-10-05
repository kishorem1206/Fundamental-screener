from app.technical.indicators.plugin import OHLCVBar, IndicatorResult

LOOKBACK = 30


class VolumeStrengthPlugin:
    name = "volume_strength"
    default_params: dict = {}

    def calculate(self, bars: list[OHLCVBar], params: dict) -> IndicatorResult:
        if len(bars) < LOOKBACK + 1:
            return IndicatorResult(
                name=self.name,
                params={},
                values={
                    "volume_today": None,
                    "avg_volume": None,
                    "volume_ratio": None,
                    "volume_score": None,
                },
                signal="UNKNOWN",
            )

        today_volume = bars[-1].volume
        # Exclude today; take the 30 bars immediately before it
        prev_bars = bars[-(LOOKBACK + 1):-1]
        avg_volume = sum(b.volume for b in prev_bars) / len(prev_bars)

        if avg_volume == 0:
            return IndicatorResult(
                name=self.name,
                params={},
                values={
                    "volume_today": round(today_volume, 0),
                    "avg_volume": 0.0,
                    "volume_ratio": None,
                    "volume_score": 0,
                },
                signal="UNKNOWN",
            )

        volume_ratio = round((today_volume / avg_volume) * 100, 2)

        if volume_ratio >= 200:
            signal = "EXCEPTIONAL"
            volume_score = 5
        elif volume_ratio >= 150:
            signal = "STRONG"
            volume_score = 3
        elif volume_ratio >= 100:
            signal = "ABOVE_AVERAGE"
            volume_score = 2
        else:
            signal = "BELOW_AVERAGE"
            volume_score = 0

        return IndicatorResult(
            name=self.name,
            params={},
            values={
                "volume_today": round(today_volume, 0),
                "avg_volume": round(avg_volume, 0),
                "volume_ratio": volume_ratio,
                "volume_score": float(volume_score),
            },
            signal=signal,
        )


volume_strength_plugin = VolumeStrengthPlugin()
