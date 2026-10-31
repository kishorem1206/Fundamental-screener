"""Weinstein stage classifier (app/stages/) on synthetic weekly prices. Offline."""
from datetime import date, timedelta

import numpy as np
import pytest

from app.stages import classify as cl
from app.stages import indicators as ind
from app.stages import settings
from app.technical.indicators.plugin import OHLCVBar
from app.technical.indicators.plugins.rsi import RSIPlugin

CFG = settings.defaults()
_START = date(2023, 10, 6)


def _weeks(closes, volumes=None, wiggle=0.02):
    volumes = volumes if volumes is not None else [1000.0] * len(closes)
    out, prev = [], closes[0]
    for i, c in enumerate(closes):
        high, low = max(prev, c) * (1 + wiggle), min(prev, c) * (1 - wiggle)
        end = _START + timedelta(weeks=i)
        out.append(ind.Week(end, end, prev, high, low, float(c), volumes[i] * 5, volumes[i]))
        prev = c
    return out


def _bench(n, drift=0.0):
    return {_START + timedelta(weeks=i): 100.0 * (1 + drift) ** i for i in range(n)}


def _read(closes, volumes=None, cfg=CFG, bench=None):
    weeks = _weeks(closes, volumes)
    series = ind.build(weeks, bench or _bench(len(closes)), cfg)
    return series, cl.replay(series, cfg)


def _wave(n, start, step, swing=0.04):
    """A trend that advances in waves, so it has swing points."""
    return [start * (1 + step) ** i * (1 + swing * np.sin(i / 2.2)) for i in range(n)]


def test_daily_bars_roll_up_into_friday_weeks_with_adjustment():
    # a 2:1 split between the weeks: adjusted prices leave no false gap
    rows = [(date(2026, 1, 5), 200, 210, 190, 200, 100, 10), (date(2026, 1, 6), 200, 220, 200, 210, 105, 30), (date(2026, 1, 12), 110, 115, 100, 110, 110, 20)]
    a, b = ind.to_weeks(rows)
    assert (a.end, a.last_bar) == (date(2026, 1, 9), date(2026, 1, 6))
    assert a.open == 100 and a.high == 110 and a.low == 95 and a.close == 105 and a.volume == 40 and a.adv == 20
    assert b.end == date(2026, 1, 16) and b.close == 110


def test_rsi_agrees_with_the_technical_screener():
    closes = list(np.cumsum(np.sin(np.arange(60) / 3.0) + 0.2) + 100)
    bars = [OHLCVBar(date=date(2026, 1, 1), open=c, high=c, low=c, close=c, volume=1) for c in closes]
    assert ind._rsi(np.array(closes), 14)[-1] == pytest.approx(RSIPlugin().calculate(bars, {"period": 14}).values["value"], abs=0.01)


def test_short_history_is_unclassified_not_guessed():
    _, readings = _read(_wave(20, 100, 0.01))
    assert all(r.stage is None for r in readings)
    assert readings[-1].reason == "20 weeks of prices, 35 needed"


def test_any_length_of_history_builds_without_a_stage():
    for n in (1, 2, 12, 34):
        _, readings = _read(_wave(n, 100, 0.01))
        assert len(readings) == n and all(r.stage is None for r in readings)


def test_a_stock_that_stopped_trading_has_no_infinite_volume_ratio():
    closes, volumes = _wave(60, 100, 0.01), [0.0] * 59 + [500.0]
    series, readings = _read(closes, volumes)
    assert np.isinf(series.volume_ratio[-1]) and readings[-1].facts["volume_ratio"] is None


def test_steady_advance_is_stage_2():
    _, readings = _read(_wave(90, 100, 0.012), bench=_bench(90, 0.002))
    recent = readings[-30:]
    assert all(r.stage == 2 for r in recent) and sum(r.confidence for r in recent) / 30 >= 60
    assert recent[-1].sub_stage in (cl.ESTABLISHED, cl.LATE)


def test_steady_decline_is_stage_4():
    _, readings = _read(_wave(90, 500, -0.012), bench=_bench(90, 0.002))
    assert readings[-1].stage == 4 and readings[-1].confidence >= 70


def test_flat_after_a_decline_is_stage_1_and_after_an_advance_is_stage_3():
    down = [400 * 0.985 ** i for i in range(45)]
    base = [down[-1] * (1 + 0.03 * np.sin(i / 1.5)) for i in range(40)]
    assert _read(down + base)[1][-1].stage == 1
    up = [100 * 1.02 ** i for i in range(45)]
    top = [up[-1] * (1 + 0.03 * np.sin(i / 1.5)) for i in range(40)]
    assert _read(up + top)[1][-1].stage == 3


def test_base_breakout_goes_1_to_2_and_is_early():
    down = [400 * 0.985 ** i for i in range(45)]
    base = [down[-1] * (1 + 0.03 * np.sin(i / 1.5)) for i in range(40)]
    rise = [base[-1] * 1.025 ** i for i in range(1, 10)]
    volumes = [1000.0] * 85 + [2500.0] * 9
    _, readings = _read(down + base + rise, volumes)
    last = readings[-1]
    assert last.stage == 2 and last.came_from == 1 and last.sub_stage == cl.EARLY
    assert any(r.event == "breakout_volume" for r in readings[85:])


def test_extended_advance_is_late_stage_2():
    _, readings = _read(_wave(60, 100, 0.005) + [100 * 1.3 * 1.05 ** i for i in range(16)], bench=_bench(76))
    assert readings[-1].stage == 2 and readings[-1].sub_stage == cl.LATE


def test_one_bad_week_does_not_change_the_stage():
    closes = _wave(80, 100, 0.012)
    closes[-1] = closes[-2] * 0.8
    r = _read(closes)[1][-1]
    assert r.stage == 2 and r.pending is not None


def test_a_week_sees_nothing_after_it():
    closes = _wave(100, 100, 0.01)
    _, full = _read(closes)
    _, cut = _read(closes[:70])
    assert (full[69].stage, full[69].confidence) == (cut[69].stage, cut[69].confidence)
    assert (full[69].sub_stage, full[69].facts["failed_highs"]) == (cut[69].sub_stage, cut[69].facts["failed_highs"])


def test_missing_benchmark_drops_rs_conditions_rather_than_failing_them():
    weeks = _weeks(_wave(90, 100, 0.012))
    series = ind.build(weeks, {}, CFG)
    last = cl.replay(series, CFG)[-1]
    rs = [c for c in last.conditions[2] if c["key"] in ("rs_positive", "rs_improving")]
    assert all(c["met"] is None for c in rs) and last.stage == 2


def test_impossible_confidence_stays_unclassified():
    cfg = {**CFG, "min_confidence": 101}
    assert all(r.stage is None for r in _read(_wave(90, 100, 0.012), cfg=cfg)[1])


def test_stage_weights_add_up_to_100():
    series, readings = _read(_wave(90, 100, 0.012))
    assert {k: sum(c["weight"] for c in v) for k, v in readings[-1].conditions.items()} == {1: 100, 2: 100, 3: 100, 4: 100}


def test_transition_watch_needs_enough_checks():
    _, readings = _read(_wave(90, 100, 0.012))
    signal = cl.next_signal(readings[-1], CFG)
    assert signal["from"] == 2 and signal["to"] == 3 and signal["of"] == 5 and signal["watch"] == (signal["met"] >= 4)


def test_threshold_limits_are_enforced():
    with pytest.raises(ValueError, match="between"):
        settings.save(None, {"min_confidence": 5})
    with pytest.raises(ValueError, match="Unknown"):
        settings.save(None, {"nope": 1})
