"""Weekly bars and every indicator the classifier reads, from stored daily prices.

A week is Monday to Friday and is keyed by its Friday, so a short week and a
week still in progress keep one row. Open, high and low are scaled by each day's
adj_close / close so splits and dividends leave no false gap. Volume is compared
as average daily volume, which keeps a holiday week or an unfinished week fair.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

import numpy as np

from app.technical.macd.engine import _ema_series


@dataclass
class Week:
    end: date
    last_bar: date
    open: float
    high: float
    low: float
    close: float
    volume: float
    adv: float


def to_weeks(rows) -> list[Week]:
    """`rows`: (bar_date, open, high, low, close, adj_close, volume), oldest first."""
    weeks: dict[date, list] = {}
    for d, o, h, l, c, adj, v in rows:
        c, adj = float(c), float(adj)
        k = adj / c if c else 1.0
        bar = (d, float(o or c) * k, float(h or c) * k, float(l or c) * k, adj, float(v or 0))
        weeks.setdefault(d + timedelta(days=4 - d.weekday()), []).append(bar)
    return [Week(end, b[-1][0], b[0][1], max(x[2] for x in b), min(x[3] for x in b), b[-1][4], sum(x[5] for x in b), sum(x[5] for x in b) / len(b))
            for end, b in sorted(weeks.items())]


def _rolling(a: np.ndarray, n: int, fewest: int | None = None, fn=np.mean) -> np.ndarray:
    out = np.full(len(a), np.nan)
    for i in range(len(a)):
        w = a[max(0, i - n + 1):i + 1]
        w = w[~np.isnan(w)]
        if len(w) >= (fewest or n):
            out[i] = fn(w)
    return out


def _change(a: np.ndarray, n: int) -> np.ndarray:
    out = np.full(len(a), np.nan)
    out[n:] = a[n:] - a[:-n]
    return out


def _rsi(close: np.ndarray, period: int) -> np.ndarray:
    """Wilder's RSI, seeded as the technical screener's RSIPlugin is, so the two agree."""
    out = np.full(len(close), np.nan)
    if len(close) <= period:
        return out
    diff = np.diff(close)
    gains, losses = np.clip(diff, 0, None), np.clip(-diff, 0, None)
    gain, loss = gains[:period].mean(), losses[:period].mean()
    for i in range(period, len(diff) + 1):
        if i > period:
            gain, loss = (gain * (period - 1) + gains[i - 1]) / period, (loss * (period - 1) + losses[i - 1]) / period
        out[i] = 100.0 if loss == 0 else 100 - 100 / (1 + gain / loss)
    return out


def _macd(close: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Weekly MACD 12, 26, 9 from the technical screener's EMA."""
    macd, signal = np.full(len(close), np.nan), np.full(len(close), np.nan)
    slow = _ema_series(close.tolist(), 26)
    if not slow:
        return macd, signal
    fast = _ema_series(close.tolist(), 12)[14:]
    line = [f - s for f, s in zip(fast, slow)]
    macd[25:] = line
    sig = _ema_series(line, 9)
    if sig:
        signal[33:] = sig
    return macd, signal


def _pivots(v: np.ndarray, w: int, high: bool) -> list[tuple[int, int, float]]:
    """(week it became known, week it happened, price). A swing point is known only
    `w` weeks after it, so no earlier week can see it."""
    out = []
    for i in range(w, len(v) - w):
        window = v[i - w:i + w + 1]
        if v[i] == (window.max() if high else window.min()):
            out.append((i + w, i, float(v[i])))
    return out


@dataclass
class Series:
    weeks: list[Week]
    close: np.ndarray
    high: np.ndarray
    low: np.ndarray
    adv: np.ndarray
    sma_long: np.ndarray
    sma_short: np.ndarray
    slope: np.ndarray
    rs: np.ndarray            # Mansfield: % above or below RS's own average
    rs_change: np.ndarray
    rsi: np.ndarray
    macd: np.ndarray
    macd_signal: np.ndarray
    volume_ratio: np.ndarray
    updown: np.ndarray
    resistance: np.ndarray    # highest high of the earlier `range_weeks`, this week left out
    support: np.ndarray
    high_52: np.ndarray
    low_52: np.ndarray
    range_pct: np.ndarray
    contraction: np.ndarray
    weeks_above: np.ndarray
    swing_highs: list = field(default_factory=list)
    swing_lows: list = field(default_factory=list)
    failed_highs: list = field(default_factory=list)


def _updown(close: np.ndarray, adv: np.ndarray, n: int) -> np.ndarray:
    out = np.full(len(close), np.nan)
    move = np.sign(np.diff(close, prepend=np.nan))
    for i in range(n, len(close)):
        m, v = move[i - n + 1:i + 1], adv[i - n + 1:i + 1]
        if (m > 0).any() and (m < 0).any() and v[m < 0].mean() > 0:
            out[i] = v[m > 0].mean() / v[m < 0].mean()
    return out


def _failed_highs(close: np.ndarray, high: np.ndarray, resistance: np.ndarray) -> list[tuple[int, int]]:
    """(week known, week it happened): a new high that closed back under the old high within two weeks."""
    out = []
    for i in range(len(close) - 2):
        level = resistance[i]
        if not np.isnan(level) and high[i] > level and close[i + 1:i + 3].min() < level:
            out.append((i + 2, i))
    return out


def build(weeks: list[Week], bench: dict[date, float], cfg: dict[str, float]) -> Series:
    close = np.array([w.close for w in weeks], float)
    high = np.array([w.high for w in weeks], float)
    low = np.array([w.low for w in weeks], float)
    adv = np.array([w.adv for w in weeks], float)
    long_n, slope_n = int(cfg["sma_long_weeks"]), int(cfg["slope_weeks"])
    sma_long = _rolling(close, long_n)
    with np.errstate(invalid="ignore", divide="ignore"):
        slope = np.full(len(close), np.nan)
        slope[slope_n:] = (sma_long[slope_n:] / sma_long[:-slope_n] - 1) * 100
        ratio = np.array([w.close / bench[w.end] if bench.get(w.end) else np.nan for w in weeks], float)
        rs = (ratio / _rolling(ratio, int(cfg["rs_sma_weeks"]), int(cfg["rs_min_weeks"])) - 1) * 100
        avg_n = int(cfg["volume_avg_weeks"])
        volume_ratio = adv / np.concatenate(([np.nan], _rolling(adv, avg_n)[:-1])) if len(adv) else adv
    range_n = int(cfg["range_weeks"])
    resistance = np.concatenate(([np.nan], _rolling(high, range_n, fn=np.max)[:-1]))
    support = np.concatenate(([np.nan], _rolling(low, range_n, fn=np.min)[:-1]))
    base_n = int(cfg["base_weeks"])
    base_high, base_low = _rolling(high, base_n, fn=np.max), _rolling(low, base_n, fn=np.min)
    swing = (high - low) / close * 100
    with np.errstate(invalid="ignore", divide="ignore"):
        contraction = _rolling(swing, 10) / np.concatenate((np.full(10, np.nan), _rolling(swing, 20)))[:len(close)]
    above = close > sma_long
    weeks_above = np.zeros(len(close), int)
    for i in range(1, len(close)):
        weeks_above[i] = weeks_above[i - 1] + 1 if above[i] else 0
    macd, macd_signal = _macd(close)
    w = int(cfg["pivot_weeks"])
    return Series(weeks, close, high, low, adv, sma_long, _rolling(close, int(cfg["sma_short_weeks"])), slope, rs,
                  _change(rs, int(cfg["rs_slope_weeks"])), _rsi(close, int(cfg["rsi_weeks"])), macd, macd_signal, volume_ratio,
                  _updown(close, adv, int(cfg["updown_weeks"])), resistance, support, _rolling(high, 52, 26, np.max), _rolling(low, 52, 26, np.min),
                  (base_high - base_low) / ((base_high + base_low) / 2) * 100,
                  contraction, weeks_above, _pivots(high, w, True), _pivots(low, w, False), _failed_highs(close, high, resistance))
