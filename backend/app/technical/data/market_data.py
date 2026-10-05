import yfinance as yf
from app.technical.indicators.plugin import OHLCVBar
from app.logger import logger
from app.technical.shared.errors import DataUnavailableError


_TF_MAP = {
    "1D": ("1d",  "2y"),    # 2y ≈ 500 bars — Wilder's RSI needs many bars to converge after a big crash
    "1W": ("1wk", "5y"),
    "1M": ("1mo", "10y"),   # 10y = 120 monthly bars
    "1H": ("1h",  "730d"),  # max yfinance allows — deeper history = better RSI convergence
    "4H": None,             # synthetic — resampled from 1H (see get_ohlcv)
    "15M": ("15m", "60d"),  # yfinance caps 15m at 60d
    "5M": ("5m",  "5d"),
}

def _resample_bars(bars: list[OHLCVBar], n: int) -> list[OHLCVBar]:
    """Combine n consecutive bars into one (OHLCV aggregation)."""
    out: list[OHLCVBar] = []
    for i in range(0, len(bars), n):
        chunk = bars[i: i + n]
        if not chunk:
            break
        out.append(OHLCVBar(
            date=chunk[0].date,
            open=chunk[0].open,
            high=max(b.high for b in chunk),
            low=min(b.low for b in chunk),
            close=chunk[-1].close,
            volume=sum(b.volume for b in chunk),
        ))
    return out


def _yf_symbol(exchange: str, symbol: str) -> str:
    exchange = exchange.upper()
    if exchange == "NSE":
        return f"{symbol.upper()}.NS"
    if exchange == "BSE":
        return f"{symbol.upper()}.BO"
    return symbol.upper()


def get_ohlcv(exchange: str, symbol: str, timeframe: str = "1D") -> list[OHLCVBar]:
    tf_upper = timeframe.upper()

    # 4H is synthetic: fetch 1H bars and group every 4 consecutive 1H bars
    if tf_upper == "4H":
        bars_1h = get_ohlcv(exchange, symbol, "1H")
        return _resample_bars(bars_1h, 4)

    tf_config = _TF_MAP.get(tf_upper)
    if tf_config is None:
        raise DataUnavailableError(timeframe, f"Unsupported timeframe. Supported: {list(_TF_MAP.keys())}")

    interval, period = tf_config  # type: ignore[misc]
    yf_sym = _yf_symbol(exchange, symbol)

    logger.debug("Fetching OHLCV", symbol=yf_sym, interval=interval, period=period)

    try:
        ticker = yf.Ticker(yf_sym)
        df = ticker.history(period=period, interval=interval, auto_adjust=True)
    except Exception as e:
        raise DataUnavailableError(yf_sym, f"yfinance fetch failed: {e}")

    if df.empty:
        raise DataUnavailableError(yf_sym, f"No data returned for interval={interval} period={period}")

    bars: list[OHLCVBar] = []
    for ts, row in df.iterrows():
        try:
            date_str = ts.strftime("%Y-%m-%d") if hasattr(ts, "strftime") else str(ts)[:10]
            bars.append(OHLCVBar(
                date=date_str,
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                volume=float(row.get("Volume", 0)),
            ))
        except Exception:
            continue

    if not bars:
        raise DataUnavailableError(yf_sym, "Could not parse OHLCV data")

    return bars
