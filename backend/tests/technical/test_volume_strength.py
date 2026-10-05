"""
Tests for VolumeStrengthPlugin.

Volume Ratio = (today_volume / avg_of_prev_30_bars) * 100

Classifications:
  BELOW_AVERAGE  < 100%   → score 0
  ABOVE_AVERAGE  100-149% → score 2
  STRONG         150-199% → score 3
  EXCEPTIONAL    >= 200%  → score 5
"""

import pytest
from app.technical.indicators.plugins.volume_strength import VolumeStrengthPlugin
from app.technical.indicators.plugin import OHLCVBar

plugin = VolumeStrengthPlugin()


def make_bars(prev_volume: float, today_volume: float, n_prev: int = 30) -> list[OHLCVBar]:
    """Build n_prev bars with prev_volume, plus one today bar with today_volume."""
    bars = [
        OHLCVBar(date=f"2024-01-{i:02d}", open=100, high=110, low=90, close=100, volume=prev_volume)
        for i in range(1, n_prev + 1)
    ]
    bars.append(OHLCVBar(date="2024-02-01", open=100, high=110, low=90, close=100, volume=today_volume))
    return bars


class TestInsufficientData:
    def test_fewer_than_31_bars_returns_unknown(self):
        bars = make_bars(prev_volume=1000, today_volume=2000, n_prev=29)
        result = plugin.calculate(bars, {})
        assert result.signal == "UNKNOWN"
        assert result.values["volume_today"] is None
        assert result.values["volume_ratio"] is None

    def test_exactly_0_bars_returns_unknown(self):
        result = plugin.calculate([], {})
        assert result.signal == "UNKNOWN"

    def test_exactly_30_bars_returns_unknown(self):
        bars = make_bars(prev_volume=1000, today_volume=2000, n_prev=29)
        assert len(bars) == 30
        result = plugin.calculate(bars, {})
        assert result.signal == "UNKNOWN"


class TestZeroAvgVolume:
    def test_zero_avg_volume_returns_unknown(self):
        bars = make_bars(prev_volume=0, today_volume=5000)
        result = plugin.calculate(bars, {})
        assert result.signal == "UNKNOWN"
        assert result.values["volume_ratio"] is None
        assert result.values["avg_volume"] == 0.0
        assert result.values["volume_today"] == 5000.0


class TestBelowAverage:
    def test_below_average_80_pct(self):
        bars = make_bars(prev_volume=100, today_volume=80)
        result = plugin.calculate(bars, {})
        assert result.signal == "BELOW_AVERAGE"
        assert result.values["volume_score"] == 0
        assert abs(result.values["volume_ratio"] - 80.0) < 0.01

    def test_below_average_50_pct(self):
        bars = make_bars(prev_volume=100, today_volume=50)
        result = plugin.calculate(bars, {})
        assert result.signal == "BELOW_AVERAGE"
        assert result.values["volume_score"] == 0

    def test_boundary_just_below_100_pct(self):
        bars = make_bars(prev_volume=100, today_volume=99.99)
        result = plugin.calculate(bars, {})
        assert result.signal == "BELOW_AVERAGE"
        assert result.values["volume_score"] == 0


class TestAboveAverage:
    def test_exactly_100_pct(self):
        bars = make_bars(prev_volume=100, today_volume=100)
        result = plugin.calculate(bars, {})
        assert result.signal == "ABOVE_AVERAGE"
        assert result.values["volume_score"] == 2
        assert abs(result.values["volume_ratio"] - 100.0) < 0.01

    def test_125_pct(self):
        bars = make_bars(prev_volume=100, today_volume=125)
        result = plugin.calculate(bars, {})
        assert result.signal == "ABOVE_AVERAGE"
        assert result.values["volume_score"] == 2

    def test_boundary_just_below_150_pct(self):
        bars = make_bars(prev_volume=100, today_volume=149.99)
        result = plugin.calculate(bars, {})
        assert result.signal == "ABOVE_AVERAGE"
        assert result.values["volume_score"] == 2


class TestStrong:
    def test_exactly_150_pct(self):
        bars = make_bars(prev_volume=100, today_volume=150)
        result = plugin.calculate(bars, {})
        assert result.signal == "STRONG"
        assert result.values["volume_score"] == 3

    def test_175_pct(self):
        bars = make_bars(prev_volume=100, today_volume=175)
        result = plugin.calculate(bars, {})
        assert result.signal == "STRONG"
        assert result.values["volume_score"] == 3

    def test_boundary_just_below_200_pct(self):
        bars = make_bars(prev_volume=100, today_volume=199.99)
        result = plugin.calculate(bars, {})
        assert result.signal == "STRONG"
        assert result.values["volume_score"] == 3


class TestExceptional:
    def test_exactly_200_pct(self):
        bars = make_bars(prev_volume=100, today_volume=200)
        result = plugin.calculate(bars, {})
        assert result.signal == "EXCEPTIONAL"
        assert result.values["volume_score"] == 5

    def test_250_pct(self):
        bars = make_bars(prev_volume=100, today_volume=250)
        result = plugin.calculate(bars, {})
        assert result.signal == "EXCEPTIONAL"
        assert result.values["volume_score"] == 5

    def test_500_pct(self):
        bars = make_bars(prev_volume=100, today_volume=500)
        result = plugin.calculate(bars, {})
        assert result.signal == "EXCEPTIONAL"
        assert result.values["volume_score"] == 5


class TestValuesPresent:
    def test_all_values_present_on_valid_data(self):
        bars = make_bars(prev_volume=1_000_000, today_volume=1_500_000)
        result = plugin.calculate(bars, {})
        assert result.values["volume_today"] is not None
        assert result.values["avg_volume"] is not None
        assert result.values["volume_ratio"] is not None
        assert result.values["volume_score"] is not None

    def test_avg_excludes_today(self):
        # 30 prev bars at volume=100, today at 999999 — avg must still be 100
        bars = make_bars(prev_volume=100, today_volume=999_999)
        result = plugin.calculate(bars, {})
        assert abs(result.values["avg_volume"] - 100) < 1

    def test_more_than_31_bars_uses_last_30_prev(self):
        # 50 prev bars: first 20 at 1, last 30 at 100 → avg should be 100
        old_bars = [
            OHLCVBar(date=f"2023-01-{i:02d}", open=100, high=110, low=90, close=100, volume=1)
            for i in range(1, 21)
        ]
        recent_bars = [
            OHLCVBar(date=f"2023-02-{i:02d}", open=100, high=110, low=90, close=100, volume=100)
            for i in range(1, 31)
        ]
        today = OHLCVBar(date="2023-03-01", open=100, high=110, low=90, close=100, volume=200)
        bars = old_bars + recent_bars + [today]
        result = plugin.calculate(bars, {})
        # avg should be 100, ratio = 200%
        assert result.signal == "EXCEPTIONAL"
        assert abs(result.values["volume_ratio"] - 200.0) < 0.01
