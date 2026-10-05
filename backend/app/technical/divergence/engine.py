"""
RSI Divergence Detection Engine

Detects pivot-to-pivot RSI divergences by:
  1. Computing a full RSI time series for all bars.
  2. Finding confirmed swing lows/highs using a left/right pivot rule.
  3. Comparing consecutive pivot pairs for price vs RSI disagreement.
  4. Filtering by recency of the second pivot.

Public entry point:
    detect_rsi_divergence(bars, cfg, div_types) -> list[DivergenceResult]
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

from app.technical.indicators.plugin import OHLCVBar

# ── Types ──────────────────────────────────────────────────────────────────────

DivergenceType   = Literal["REGULAR_BULLISH", "REGULAR_BEARISH", "HIDDEN_BULLISH", "HIDDEN_BEARISH"]
DivergenceStatus = Literal["DEVELOPING", "CONFIRMED", "RECENT_CONFIRMED"]


@dataclass
class DivergenceConfig:
    """All tuneable parameters for divergence detection."""
    rsi_period:              int         = 14
    pivot_left:              int         = 3      # bars to the left that must be higher (for swing low)
    pivot_right:             int         = 3      # bars to the right that must be higher (for swing low)
    max_recency_bars:        int         = 10     # second pivot must be within this many bars of end
    min_bars_between_pivots: int         = 5      # ignore pivot pairs that are too close together
    max_bars_between_pivots: int         = 60     # cap how far back P1 can be (~3 months of daily bars)
    min_rsi_change:          float       = 1.0    # RSI must improve by at least this amount
    min_price_chg_pct:       float       = 0.1    # price must drop at least this % for LL confirmation
    max_pivot_rsi:           float | None = 40.0  # bullish: both P1 and P2 RSI must be ≤ this (None=off)
    min_pivot_rsi:           float | None = None  # bearish: both P1 and P2 RSI must be ≥ this (None=off)


@dataclass
class SwingPivot:
    """One confirmed swing extreme (low for bullish, high for bearish)."""
    bar_idx: int
    date:    str
    price:   float
    rsi:     float


@dataclass
class DivergenceResult:
    """One detected divergence between two swing pivots."""
    div_type:       DivergenceType
    status:         DivergenceStatus
    pivot1:         SwingPivot   # the older pivot
    pivot2:         SwingPivot   # the more recent pivot (within recency window)
    price_chg_pct:  float        # (pivot2.price - pivot1.price) / pivot1.price * 100
    rsi_change:     float        # pivot2.rsi - pivot1.rsi
    bars_between:   int          # pivot2.bar_idx - pivot1.bar_idx
    divergence_age: int          # bars since pivot2 from end of data
    strength_score: float        # 0–10 composite quality score


# ── Internal helpers ───────────────────────────────────────────────────────────

def _rsi_series(closes: list[float], period: int = 14) -> list[float]:
    """
    Compute the full RSI series using Wilder's smoothing — same as rsi_momentum.py.
    series[k] = RSI at bars[period + k].
    Returns an empty list if fewer than period+2 bars are available.
    """
    N = len(closes)
    if N < period + 2:
        return []

    arr = np.array(closes, dtype=float)
    d   = np.diff(arr)
    g   = np.where(d > 0, d, 0.0)
    lo  = np.where(d < 0, -d, 0.0)
    ag  = float(np.mean(g[:period]))
    al  = float(np.mean(lo[:period]))

    def _r(ag: float, al: float) -> float:
        return 100.0 if al == 0 else round(100.0 - 100.0 / (1.0 + ag / al), 2)

    out = [_r(ag, al)]
    for gi, li in zip(g[period:], lo[period:]):
        ag = (ag * (period - 1) + gi) / period
        al = (al * (period - 1) + li) / period
        out.append(_r(ag, al))
    return out


def _bar_rsi(series: list[float], bar_idx: int, period: int) -> float | None:
    """Retrieve the RSI value for a specific bar index (handles the series offset)."""
    k = bar_idx - period
    if k < 0 or k >= len(series):
        return None
    return series[k]


def _swing_lows(lows: list[float], pl: int, pr: int) -> list[tuple[int, float]]:
    """
    Return confirmed swing lows as (bar_index, low_price).
    A bar is a swing low if its low is STRICTLY less than pl bars to the left
    and STRICTLY less than pr bars to the right.
    Only considers bars where both sides can be checked (not at the edges).
    """
    N = len(lows)
    result: list[tuple[int, float]] = []
    for i in range(pl, N - pr):
        v = lows[i]
        if (all(v < lows[i - k] for k in range(1, pl + 1)) and
                all(v < lows[i + k] for k in range(1, pr + 1))):
            result.append((i, v))
    return result


def _swing_highs(highs: list[float], pl: int, pr: int) -> list[tuple[int, float]]:
    """
    Return confirmed swing highs as (bar_index, high_price).
    Strictly greater than pl left and pr right bars.
    """
    N = len(highs)
    result: list[tuple[int, float]] = []
    for i in range(pl, N - pr):
        v = highs[i]
        if (all(v > highs[i - k] for k in range(1, pl + 1)) and
                all(v > highs[i + k] for k in range(1, pr + 1))):
            result.append((i, v))
    return result


def _strength_score(
    price_chg_pct: float,  # negative for bullish div (price LL)
    rsi_change:    float,  # positive for bullish div (RSI HL)
    bars_between:  int,
    rsi_at_p2:    float,   # RSI level at second pivot (lower = more oversold = stronger)
) -> float:
    """
    Composite divergence strength score 0–10.
    Components:
      - RSI change magnitude (0–4 pts): max at 15+ pt improvement
      - Price drop magnitude  (0–3 pts): max at 5%+ lower low
      - Oversold level        (0–2 pts): max at RSI=20, zero at RSI≥40
      - Pivot separation      (0–1 pt):  max at 15+ bars apart
    """
    s  = min(4.0, rsi_change / 15.0 * 4.0)
    s += min(3.0, abs(price_chg_pct) / 5.0 * 3.0)
    s += max(0.0, (40.0 - rsi_at_p2) / 20.0 * 2.0)
    s += min(1.0, bars_between / 15.0)
    return round(min(10.0, s), 2)


def _detect_regular_bullish(
    bars:   list[OHLCVBar],
    rsi:    list[float],
    cfg:    DivergenceConfig,
) -> list[DivergenceResult]:
    """Price Lower Low + RSI Higher Low."""
    N      = len(bars)
    dates  = [b.date for b in bars]
    lows   = [b.low  for b in bars]
    pivots = _swing_lows(lows, cfg.pivot_left, cfg.pivot_right)

    results: list[DivergenceResult] = []
    for idx2, (p2_bar, p2_price) in enumerate(pivots):
        age = (N - 1) - p2_bar
        if age > cfg.max_recency_bars:
            continue

        p2_rsi = _bar_rsi(rsi, p2_bar, cfg.rsi_period)
        if p2_rsi is None:
            continue

        # RSI level gate on P2 (checked once before scanning P1 candidates)
        if cfg.max_pivot_rsi is not None and p2_rsi > cfg.max_pivot_rsi:
            continue

        # Search backwards for the nearest valid pivot1
        for idx1 in range(idx2 - 1, -1, -1):
            p1_bar, p1_price = pivots[idx1]

            sep = p2_bar - p1_bar
            if sep < cfg.min_bars_between_pivots:
                continue
            if sep > cfg.max_bars_between_pivots:
                break  # further candidates are only older — stop searching

            p1_rsi = _bar_rsi(rsi, p1_bar, cfg.rsi_period)
            if p1_rsi is None:
                continue

            # RSI level gate on P1
            if cfg.max_pivot_rsi is not None and p1_rsi > cfg.max_pivot_rsi:
                continue

            price_chg_pct = (p2_price - p1_price) / p1_price * 100.0
            rsi_change    = p2_rsi - p1_rsi

            # Regular bullish: price must make a LOWER low, RSI must make a HIGHER low
            if price_chg_pct >= -cfg.min_price_chg_pct:
                continue
            if rsi_change <= cfg.min_rsi_change:
                continue

            # Reject if any intermediate pivot went even lower than P2 —
            # that would mean P2 is not the true recent extreme
            if any(p < p2_price for _, p in pivots[idx1 + 1:idx2]):
                continue

            score = _strength_score(price_chg_pct, rsi_change, sep, p2_rsi)
            results.append(DivergenceResult(
                div_type="REGULAR_BULLISH",
                status="RECENT_CONFIRMED",
                pivot1=SwingPivot(p1_bar, dates[p1_bar], p1_price, p1_rsi),
                pivot2=SwingPivot(p2_bar, dates[p2_bar], p2_price, p2_rsi),
                price_chg_pct=round(price_chg_pct, 3),
                rsi_change=round(rsi_change, 2),
                bars_between=sep,
                divergence_age=age,
                strength_score=score,
            ))
            break  # take the nearest valid pivot1 for each pivot2

    return results


def _detect_regular_bearish(
    bars:   list[OHLCVBar],
    rsi:    list[float],
    cfg:    DivergenceConfig,
) -> list[DivergenceResult]:
    """Price Higher High + RSI Lower High."""
    N      = len(bars)
    dates  = [b.date for b in bars]
    highs  = [b.high for b in bars]
    pivots = _swing_highs(highs, cfg.pivot_left, cfg.pivot_right)

    results: list[DivergenceResult] = []
    for idx2, (p2_bar, p2_price) in enumerate(pivots):
        age = (N - 1) - p2_bar
        if age > cfg.max_recency_bars:
            continue

        p2_rsi = _bar_rsi(rsi, p2_bar, cfg.rsi_period)
        if p2_rsi is None:
            continue

        # RSI level gate on P2
        if cfg.min_pivot_rsi is not None and p2_rsi < cfg.min_pivot_rsi:
            continue

        for idx1 in range(idx2 - 1, -1, -1):
            p1_bar, p1_price = pivots[idx1]
            sep = p2_bar - p1_bar
            if sep < cfg.min_bars_between_pivots:
                continue
            if sep > cfg.max_bars_between_pivots:
                break
            p1_rsi = _bar_rsi(rsi, p1_bar, cfg.rsi_period)
            if p1_rsi is None:
                continue

            # RSI level gate on P1
            if cfg.min_pivot_rsi is not None and p1_rsi < cfg.min_pivot_rsi:
                continue

            price_chg_pct = (p2_price - p1_price) / p1_price * 100.0
            rsi_change    = p2_rsi - p1_rsi  # negative for bearish div

            if price_chg_pct <= cfg.min_price_chg_pct:
                continue
            if rsi_change >= -cfg.min_rsi_change:
                continue

            # Reject if any intermediate pivot went even higher than P2
            if any(p > p2_price for _, p in pivots[idx1 + 1:idx2]):
                continue

            score = _strength_score(abs(price_chg_pct), abs(rsi_change), sep, 100.0 - p2_rsi)
            results.append(DivergenceResult(
                div_type="REGULAR_BEARISH",
                status="RECENT_CONFIRMED",
                pivot1=SwingPivot(p1_bar, dates[p1_bar], p1_price, p1_rsi),
                pivot2=SwingPivot(p2_bar, dates[p2_bar], p2_price, p2_rsi),
                price_chg_pct=round(price_chg_pct, 3),
                rsi_change=round(rsi_change, 2),
                bars_between=sep,
                divergence_age=age,
                strength_score=score,
            ))
            break

    return results


def _detect_hidden_bullish(
    bars:   list[OHLCVBar],
    rsi:    list[float],
    cfg:    DivergenceConfig,
) -> list[DivergenceResult]:
    """Price Higher Low + RSI Lower Low (trend continuation upward)."""
    N      = len(bars)
    dates  = [b.date for b in bars]
    lows   = [b.low  for b in bars]
    pivots = _swing_lows(lows, cfg.pivot_left, cfg.pivot_right)

    results: list[DivergenceResult] = []
    for idx2, (p2_bar, p2_price) in enumerate(pivots):
        age = (N - 1) - p2_bar
        if age > cfg.max_recency_bars:
            continue
        p2_rsi = _bar_rsi(rsi, p2_bar, cfg.rsi_period)
        if p2_rsi is None:
            continue
        for idx1 in range(idx2 - 1, -1, -1):
            p1_bar, p1_price = pivots[idx1]
            sep = p2_bar - p1_bar
            if sep < cfg.min_bars_between_pivots:
                continue
            if sep > cfg.max_bars_between_pivots:
                break
            p1_rsi = _bar_rsi(rsi, p1_bar, cfg.rsi_period)
            if p1_rsi is None:
                continue
            price_chg_pct = (p2_price - p1_price) / p1_price * 100.0
            rsi_change    = p2_rsi - p1_rsi
            # Hidden bullish: price HL (price_chg_pct > 0), RSI LL (rsi_change < 0)
            if price_chg_pct <= cfg.min_price_chg_pct:
                continue
            if rsi_change >= -cfg.min_rsi_change:
                continue

            # Reject if any intermediate pivot went lower than P1 (breaks the higher-low structure)
            if any(p < p1_price for _, p in pivots[idx1 + 1:idx2]):
                continue

            score = _strength_score(abs(price_chg_pct), abs(rsi_change), sep, p2_rsi)
            results.append(DivergenceResult(
                div_type="HIDDEN_BULLISH",
                status="RECENT_CONFIRMED",
                pivot1=SwingPivot(p1_bar, dates[p1_bar], p1_price, p1_rsi),
                pivot2=SwingPivot(p2_bar, dates[p2_bar], p2_price, p2_rsi),
                price_chg_pct=round(price_chg_pct, 3),
                rsi_change=round(rsi_change, 2),
                bars_between=sep,
                divergence_age=age,
                strength_score=score,
            ))
            break

    return results


# ── Public API ─────────────────────────────────────────────────────────────────

def get_current_rsi(bars: list[OHLCVBar], period: int = 14) -> tuple[float, float] | None:
    """
    Returns (rsi_today, rsi_prev) — the last two RSI values from the series.
    Used for the "RSI rising today" filter without re-running full divergence detection.
    Returns None if there are not enough bars.
    """
    closes = [b.close for b in bars]
    series = _rsi_series(closes, period)
    if len(series) < 2:
        return None
    return series[-1], series[-2]


def detect_rsi_divergence(
    bars:      list[OHLCVBar],
    cfg:       DivergenceConfig | None = None,
    div_types: list[DivergenceType] | None = None,
) -> list[DivergenceResult]:
    """
    Detect RSI divergences in a list of OHLCV bars.

    Args:
        bars:      Daily OHLCV bars. 100–500 bars recommended for reliable pivot detection.
        cfg:       Detection parameters. Uses DivergenceConfig defaults if None.
        div_types: Which patterns to detect. Defaults to ["REGULAR_BULLISH"].

    Returns:
        List of DivergenceResult sorted by recency (most recent first), then strength.
    """
    if cfg is None:
        cfg = DivergenceConfig()
    if div_types is None:
        div_types = ["REGULAR_BULLISH"]

    min_bars = cfg.rsi_period + cfg.pivot_left + cfg.pivot_right + cfg.min_bars_between_pivots + 5
    if len(bars) < min_bars:
        return []

    # Truncate to post-corporate-action bars only. A >30% single-bar drop signals a
    # demerger or large special dividend that yfinance doesn't adjust for. Removing only
    # the drop bar is insufficient — pre-event prices would surround post-event lows,
    # creating artificial pivots that satisfy pivot_left trivially. Keeping only the
    # post-event price series (all bars in the same price scale) eliminates the problem.
    last_ca_idx = -1
    for i in range(1, len(bars)):
        prev_c = bars[i - 1].close
        if prev_c > 0 and (bars[i].close - prev_c) / prev_c < -0.30:
            last_ca_idx = i
    if last_ca_idx >= 0:
        bars = bars[last_ca_idx:]  # start from the first post-event bar

    closes = [b.close for b in bars]
    rsi    = _rsi_series(closes, cfg.rsi_period)
    if not rsi:
        return []

    results: list[DivergenceResult] = []
    if "REGULAR_BULLISH" in div_types:
        results.extend(_detect_regular_bullish(bars, rsi, cfg))
    if "REGULAR_BEARISH" in div_types:
        results.extend(_detect_regular_bearish(bars, rsi, cfg))
    if "HIDDEN_BULLISH" in div_types:
        results.extend(_detect_hidden_bullish(bars, rsi, cfg))

    results.sort(key=lambda r: (r.divergence_age, -r.strength_score))
    return results
