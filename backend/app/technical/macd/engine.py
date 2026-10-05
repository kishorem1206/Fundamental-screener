"""
MACD Analysis Engine

Computes MACD with configurable source, MA types (EMA/SMA), and periods.
Classifies each bar into histogram states and detects crossovers with
zero-line context. No look-ahead: all classifications use only data
available at the current bar.
"""
from dataclasses import dataclass
from app.technical.indicators.plugin import OHLCVBar


# ─── MA helpers ──────────────────────────────────────────────────────────────

def _sma_series(values: list[float], period: int) -> list[float]:
    n = len(values)
    if n < period:
        return []
    return [sum(values[i: i + period]) / period for i in range(n - period + 1)]


def _ema_series(values: list[float], period: int) -> list[float]:
    if len(values) < period:
        return []
    k = 2.0 / (period + 1)
    ema = sum(values[:period]) / period
    series = [ema]
    for v in values[period:]:
        ema = v * k + ema * (1.0 - k)
        series.append(ema)
    return series


def _ma_series(values: list[float], period: int, ma_type: str) -> list[float]:
    return _sma_series(values, period) if ma_type.upper() == "SMA" else _ema_series(values, period)


# ─── Source extraction ────────────────────────────────────────────────────────

def _source_value(bar: OHLCVBar, source: str) -> float:
    s = source.upper()
    if s == "OPEN":   return bar.open
    if s == "HIGH":   return bar.high
    if s == "LOW":    return bar.low
    if s == "HL2":    return (bar.high + bar.low) / 2
    if s == "HLC3":   return (bar.high + bar.low + bar.close) / 3
    if s == "OHLC4":  return (bar.open + bar.high + bar.low + bar.close) / 4
    return bar.close  # default: Close


# ─── Output dataclasses ───────────────────────────────────────────────────────

@dataclass
class MACDAnalysis:
    macd: float
    signal_line: float
    histogram: float
    histogram_prev: float
    # histogram direction vs previous bar
    histogram_direction: str       # INCREASING | DECREASING | FLAT
    # 4-state histogram classification
    histogram_state: str           # STRONG_BULLISH | BULLISH_FADING | STRONG_BEARISH | BEARISH_FADING | NEUTRAL
    # MACD vs zero line
    zero_line_status: str          # ABOVE | BELOW | AT
    # today's crossover (NONE if no crossover today)
    crossover: str                 # BULLISH | BEARISH | NONE
    crossover_location: str        # ABOVE_ZERO | BELOW_ZERO | NONE
    # most recent crossover within lookback window
    last_crossover_type: str | None    # BULLISH_BELOW_ZERO | BULLISH_ABOVE_ZERO | BEARISH_ABOVE_ZERO | BEARISH_BELOW_ZERO
    last_crossover_bars_ago: int | None
    # composite classification
    macd_state: str


@dataclass
class MACDBar:
    date: str
    close: float
    macd: float
    signal: float
    histogram: float
    histogram_state: str


@dataclass
class MACDSeries:
    bars: list[MACDBar]


# ─── Core computation ─────────────────────────────────────────────────────────

def _build_aligned_series(
    bars: list[OHLCVBar],
    source: str,
    fast: int,
    slow: int,
    signal: int,
    osc_ma: str,
    sig_ma: str,
) -> tuple[list[str], list[float], list[float], list[float], list[float]] | None:
    """
    Returns (dates, closes, macd_vals, signal_vals, histogram_vals) aligned arrays,
    or None if there are insufficient bars.
    """
    src = [_source_value(b, source) for b in bars]

    fast_ma = _ma_series(src, fast, osc_ma)
    slow_ma = _ma_series(src, slow, osc_ma)

    if not fast_ma or not slow_ma:
        return None

    # Align fast_ma to match slow_ma length (both referenced from the end)
    offset = len(fast_ma) - len(slow_ma)
    if offset < 0:
        return None
    macd_line = [f - s for f, s in zip(fast_ma[offset:], slow_ma)]

    sig_line = _ma_series(macd_line, signal, sig_ma)
    if len(sig_line) < 2:
        return None

    # Align macd_line to sig_line
    macd_offset = len(macd_line) - len(sig_line)
    macd_aligned = macd_line[macd_offset:]

    # Align corresponding bars
    total_offset = len(bars) - len(sig_line)
    aligned_bars = bars[total_offset:]

    dates      = [b.date  for b in aligned_bars]
    closes     = [b.close for b in aligned_bars]
    macd_vals  = [round(m, 4) for m in macd_aligned]
    sig_vals   = [round(s, 4) for s in sig_line]
    hist_vals  = [round(m - s, 4) for m, s in zip(macd_aligned, sig_line)]

    return dates, closes, macd_vals, sig_vals, hist_vals


def _hist_state(hist: float, hist_prev: float) -> str:
    if hist > 0:
        return "STRONG_BULLISH" if hist >= hist_prev else "BULLISH_FADING"
    if hist < 0:
        return "STRONG_BEARISH" if hist <= hist_prev else "BEARISH_FADING"
    return "NEUTRAL"


def _bar_hist_state(hist: float, hist_prev: float) -> str:
    """Per-bar histogram state for chart coloring."""
    if hist > 0:
        return "STRONG_BULLISH" if hist >= hist_prev else "BULLISH_FADING"
    if hist < 0:
        return "STRONG_BEARISH" if hist <= hist_prev else "BEARISH_FADING"
    return "NEUTRAL"


def analyze_macd(
    bars: list[OHLCVBar],
    source: str = "Close",
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
    osc_ma: str = "EMA",
    sig_ma: str = "EMA",
    crossover_lookback: int = 20,
) -> MACDAnalysis | None:
    """Compute MACD analysis for the latest bar. Returns None if insufficient data."""
    result = _build_aligned_series(bars, source, fast, slow, signal, osc_ma, sig_ma)
    if result is None or len(result[2]) < 2:
        return None

    _, _, macd_vals, sig_vals, hist_vals = result

    macd_val       = macd_vals[-1]
    signal_val     = sig_vals[-1]
    histogram      = hist_vals[-1]
    macd_prev      = macd_vals[-2]
    signal_prev    = sig_vals[-2]
    histogram_prev = hist_vals[-2]

    # Histogram direction
    if histogram > histogram_prev:
        hist_dir = "INCREASING"
    elif histogram < histogram_prev:
        hist_dir = "DECREASING"
    else:
        hist_dir = "FLAT"

    hist_state = _hist_state(histogram, histogram_prev)

    # Zero line status
    if abs(macd_val) < 1e-8:
        zero_status = "AT"
    elif macd_val > 0:
        zero_status = "ABOVE"
    else:
        zero_status = "BELOW"

    # Today's crossover
    bull_today = macd_prev <= signal_prev and macd_val > signal_val
    bear_today = macd_prev >= signal_prev and macd_val < signal_val
    if bull_today:
        crossover      = "BULLISH"
        cross_location = "ABOVE_ZERO" if macd_val >= 0 else "BELOW_ZERO"
    elif bear_today:
        crossover      = "BEARISH"
        cross_location = "ABOVE_ZERO" if macd_val > 0 else "BELOW_ZERO"
    else:
        crossover      = "NONE"
        cross_location = "NONE"

    # Scan back for most recent crossover within lookback
    last_cross_type: str | None = None
    last_cross_bars: int | None = None
    lookback = min(crossover_lookback, len(macd_vals) - 1)
    for i in range(lookback):
        idx = -(i + 1)
        m_cur  = macd_vals[idx]
        s_cur  = sig_vals[idx]
        m_prev = macd_vals[idx - 1]
        s_prev = sig_vals[idx - 1]
        is_bull = m_prev <= s_prev and m_cur > s_cur
        is_bear = m_prev >= s_prev and m_cur < s_cur
        if is_bull or is_bear:
            loc = "ABOVE_ZERO" if m_cur >= 0 else "BELOW_ZERO"
            if is_bull:
                last_cross_type = f"BULLISH_{loc}"
            else:
                last_cross_type = f"BEARISH_{loc}"
            last_cross_bars = i  # 0 = today
            break

    # Composite MACD state
    if crossover == "BULLISH":
        macd_state = f"BULLISH_CROSSOVER_{cross_location}"
    elif crossover == "BEARISH":
        macd_state = f"BEARISH_CROSSOVER_{cross_location}"
    elif histogram > 0:
        macd_state = "STRONG_BULLISH" if hist_dir != "DECREASING" else "BULLISH_FADING"
    elif histogram < 0:
        macd_state = "STRONG_BEARISH" if hist_dir != "INCREASING" else "BEARISH_FADING"
    else:
        macd_state = "NEUTRAL"

    return MACDAnalysis(
        macd=macd_val,
        signal_line=signal_val,
        histogram=histogram,
        histogram_prev=histogram_prev,
        histogram_direction=hist_dir,
        histogram_state=hist_state,
        zero_line_status=zero_status,
        crossover=crossover,
        crossover_location=cross_location,
        last_crossover_type=last_cross_type,
        last_crossover_bars_ago=last_cross_bars,
        macd_state=macd_state,
    )


def compute_macd_series(
    bars: list[OHLCVBar],
    source: str = "Close",
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
    osc_ma: str = "EMA",
    sig_ma: str = "EMA",
    num_bars: int = 80,
) -> MACDSeries | None:
    """Compute full MACD series for charting. Returns the last `num_bars` bars."""
    result = _build_aligned_series(bars, source, fast, slow, signal, osc_ma, sig_ma)
    if result is None or len(result[2]) < 2:
        return None

    dates, closes, macd_vals, sig_vals, hist_vals = result

    # Trim to last num_bars
    n = min(num_bars, len(dates))
    dates      = dates[-n:]
    closes     = closes[-n:]
    macd_vals  = macd_vals[-n:]
    sig_vals   = sig_vals[-n:]
    hist_vals  = hist_vals[-n:]

    out: list[MACDBar] = []
    for i, (d, c, m, s, h) in enumerate(zip(dates, closes, macd_vals, sig_vals, hist_vals)):
        h_prev = hist_vals[i - 1] if i > 0 else h
        state  = _bar_hist_state(h, h_prev)
        out.append(MACDBar(date=d, close=c, macd=m, signal=s, histogram=h, histogram_state=state))

    return MACDSeries(bars=out)
