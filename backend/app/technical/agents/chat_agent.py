import re
import json
from app.technical.shared.schemas import AgentTask, AgentResult, AgentError
from app.technical.agents.message_bus import agent_message_bus
from app.technical.llm.factory import llm_provider
from app.technical.llm.types import LLMMessage, LLMCompletionOptions
from app.logger import logger

# ─── Keyword sets ─────────────────────────────────────────────────────────────

_FUNDAMENTAL_KW = {
    "pe ratio", "p/e", "book value", "roe", "roa", "earnings",
    "revenue", "dividend", "debt", "fundamentals", "profit margin",
    "price to book", "ev/ebitda", "ebitda", "current ratio",
}

_QUOTE_KW = {
    "price", "quote", "trading at", "current price", "ltp",
    "last traded", "52 week", "52-week", "volume",
}

# Common English words that should never be treated as stock symbols
_SYMBOL_BLOCKLIST = {
    "A", "AN", "THE", "AT", "FOR", "IN", "OF", "TO", "AND", "OR", "BY", "ON",
    "AS", "UP", "DO", "GO", "IS", "IT", "BE", "IF",
    # Pronouns
    "I", "ME", "MY", "WE", "US", "YOU", "HE", "SHE", "THEY", "THEM",
    # Common verbs
    "ARE", "WAS", "HAS", "CAN", "WILL", "GET", "GIVE", "SHOW", "FIND", "HAVE",
    "WITH", "FROM", "WANT", "NEED", "KNOW", "TELL", "LOOK", "MAKE", "TAKE",
    # Interrogatives
    "WHAT", "WHICH", "WHERE", "WHEN", "WHY", "HOW", "WHO",
    # Comparisons / quantity words
    "MORE", "MOST", "LESS", "THAN", "OVER", "UNDER", "ABOVE", "BELOW",
    "HIGH", "HIGHER", "HIGHEST", "LOW", "LOWER", "LOWEST",
    "MANY", "MUCH", "VERY", "ALSO", "JUST", "ONLY", "EVEN",
    # Adjectives
    "LARGE", "LARGER", "MID", "SMALL", "SMALLER", "MICRO",
    "GOOD", "GREAT", "BEST", "BAD", "NEW", "OLD",
    # Time
    "TODAY", "NOW", "CURRENT", "LAST", "NEXT", "RECENT",
    # Quantifiers
    "ALL", "ANY", "SOME", "EACH", "EVERY", "BOTH", "NONE",
    # Market context words (not tickers)
    "NSE", "BSE", "NIFTY", "SENSEX", "MARKET", "STOCK", "STOCKS", "SHARE",
    "SHARES", "INDEX", "INDICES", "SECTOR", "SECTORS", "CAP",
    # This/that/these/those
    "THIS", "THAT", "THESE", "THOSE",
    # Indicator / ratio names
    "RSI", "PE", "PB", "EMA", "SMA", "MACD", "ATR", "BB", "LLM", "AI",
    # Value/price context
    "VALUE", "VALUES", "PRICE", "PRICES", "VOLUME", "RATE", "RATIO",
    # Misc
    "GIVE", "TELL", "LIST", "WITH", "SHOW", "HAVE", "THEIR", "HAVING",
    "CONSTITUENTS", "BETWEEN", "AROUND",
}

# Order matters: more specific patterns first; use word boundaries so "nifty 50" ≠ "nifty 500"
_UNIVERSE_PATTERNS = [
    (re.compile(r'\bnifty\s*total\s*market\b', re.IGNORECASE), "NIFTY_TOTAL_MARKET"),
    (re.compile(r'\btotal\s*market\b', re.IGNORECASE),          "NIFTY_TOTAL_MARKET"),
    (re.compile(r'\bnifty\s*total\b', re.IGNORECASE),           "NIFTY_TOTAL_MARKET"),
    # "Nifty 750" / "750 stocks" = Total Market (752 stocks post-refresh)
    (re.compile(r'\bnifty\s*750\b', re.IGNORECASE),             "NIFTY_TOTAL_MARKET"),
    (re.compile(r'\b750\s*stocks?\b', re.IGNORECASE),           "NIFTY_TOTAL_MARKET"),
    (re.compile(r'\bnifty\s*500\b', re.IGNORECASE),             "NIFTY_500"),
    (re.compile(r'\bnifty\s*50\b', re.IGNORECASE),              "NIFTY_50"),
]

_CAP_MAP = {
    "large cap": "LARGE_CAP", "large-cap": "LARGE_CAP", "largecap": "LARGE_CAP",
    "mid cap": "MID_CAP", "mid-cap": "MID_CAP", "midcap": "MID_CAP",
    "small cap": "SMALL_CAP", "small-cap": "SMALL_CAP", "smallcap": "SMALL_CAP",
    "micro cap": "MICRO_CAP", "micro-cap": "MICRO_CAP", "microcap": "MICRO_CAP",
}

_SYSTEM_PROMPT = """You are an expert stock market assistant for Indian markets (NSE/BSE).
For every user question, the backend automatically runs the appropriate stock screen or data lookup and injects the results as FRESH MARKET DATA directly in the user's message.

Guidelines:
- ALWAYS answer using the FRESH MARKET DATA block in the current message — that data was just retrieved to answer this specific question.
- Do NOT say "the dataset does not include X" — if you see a FRESH MARKET DATA block, it contains the answer.
- If the user refers to "these stocks" or a previous result, the backend has already re-queried with the correct filter — use the fresh data.
- Be concise but informative. Use bullet points when listing multiple stocks.
- V1 is strictly read-only. Never suggest executing orders, placing trades, or buying/selling.
- Always add a brief disclaimer that this is informational only.
- Format numbers properly: prices in ₹, percentages with %, ratios to 2 decimal places.
- For Bollinger Bands: %B > 1.0 = above upper band, %B ≈ 1.0 = at upper band, %B = 0.5 = at middle band, %B < 0 = below lower band."""


# ─── Intent / entity extraction ───────────────────────────────────────────────

# Detects "RSI <comparison> <number>" in many natural phrasings
_RSI_COMPARISON_RE = re.compile(
    r'rsi\b.{0,30}?'
    r'(?:above|over|greater\s+than|more\s+than|higher\s+than|exceeds?|>|>=|gt)'
    r'\s*(\d+(?:\.\d+)?)',
    re.IGNORECASE,
)
_RSI_BELOW_RE = re.compile(
    r'rsi\b.{0,30}?'
    r'(?:below|under|less\s+than|lower\s+than|<|<=|lt)'
    r'\s*(\d+(?:\.\d+)?)',
    re.IGNORECASE,
)

# Detects any screen-like intent
_SCREEN_PATTERNS = [
    re.compile(r'\brsi\b.{0,40}(?:above|below|over|under|more|less|greater|higher|lower|than|\d)', re.IGNORECASE),
    re.compile(r'(?:find|show|list|give|screen|filter)\b.{0,30}(?:stocks?|shares?|companies)', re.IGNORECASE),
    re.compile(r'(?:stocks?|shares?|companies).{0,30}(?:with|having|where|above|below|rsi|bollinger)', re.IGNORECASE),
    re.compile(r'which\b.{0,30}(?:stocks?|shares?|companies|nifty)', re.IGNORECASE),
    re.compile(r'\b(?:oversold|overbought)\b', re.IGNORECASE),
    re.compile(r'\bbollinger\b', re.IGNORECASE),
    re.compile(r'\b(?:lower|upper)\s+band\b', re.IGNORECASE),
    re.compile(r'\bpercent\s*b\b|%b\b', re.IGNORECASE),
    re.compile(r'\bmacd\b', re.IGNORECASE),
]


def _extract_symbols(text: str) -> list[str]:
    """Extract genuine NSE-style stock tickers (≥2 uppercase alphanumeric chars, not common words)."""
    candidates = re.findall(r'\b([A-Z][A-Z0-9&]{1,13})\b', text.upper())
    return [c for c in candidates if c not in _SYMBOL_BLOCKLIST]


def _extract_universe(text: str) -> str:
    for pattern, universe_id in _UNIVERSE_PATTERNS:
        if pattern.search(text):
            return universe_id
    return "NIFTY_50"


def _extract_market_cap(text: str) -> str | None:
    lower = text.lower()
    for phrase, cap in _CAP_MAP.items():
        if phrase in lower:
            return cap
    return None


def _extract_rsi_threshold(text: str) -> tuple[str, float] | None:
    """
    Handles many natural phrasings:
      "RSI above 60", "RSI more than 70", "RSI greater than 65",
      "RSI below 30", "RSI less than 35", "RSI under 40"
    """
    m = _RSI_COMPARISON_RE.search(text)
    if m:
        return ("gt", float(m.group(1)))
    m = _RSI_BELOW_RE.search(text)
    if m:
        return ("lt", float(m.group(1)))
    lower = text.lower()
    if "oversold" in lower:
        return ("lt", 35.0)
    if "overbought" in lower:
        return ("gt", 65.0)
    return None


_SECTOR_GROUP_RE = re.compile(
    r'categori[sz]e?\s+by\s+sector|group\s+by\s+sector|sector[- ]?wise|by\s+sectors?',
    re.IGNORECASE,
)


def _detect_sector_grouping(text: str) -> bool:
    return bool(_SECTOR_GROUP_RE.search(text))


_FRESH_BREAKOUT_RE = re.compile(
    r'fresh\s*break(?:out)?|rsi\s*break(?:out)?|just\s*cross(?:ed)?\s*above|'
    r'first\s*time\s*above|newly?\s*above|breaking\s*(?:above|out)',
    re.IGNORECASE,
)

_APPROACHING_AGAIN_RE = re.compile(
    r'approach(?:ing)?\s*again|second[- ]chance|pull(?:ed)?\s*back.{0,20}approach|'
    r'was\s*above.{0,20}approach|re[- ]?approach',
    re.IGNORECASE,
)

_UPTREND_RE = re.compile(
    r'\bup\s*trend\b|\bupward\b|\bup\s*ward\s*trend\b|\brising\s*(?:rsi|trend|momentum)?\b|'
    r'\brsi\s*(?:is\s*)?(?:rising|going\s*up|trending\s*up)\b|\bmomentum\s*(?:is\s*)?(?:up|rising)\b',
    re.IGNORECASE,
)

_DOWNTREND_RE = re.compile(
    r'\bdown\s*trend\b|\bdownward\b|\bdown\s*ward\s*trend\b|\bfalling\s*(?:rsi|trend|momentum)?\b|'
    r'\brsi\s*(?:is\s*)?(?:falling|going\s*down|trending\s*down)\b',
    re.IGNORECASE,
)

_VOLUME_ABOVE_RE = re.compile(
    r'volume\s*(?:\w+\s*){0,3}(?:greater\s+than|above|more\s+than|higher\s+than|exceeds?|>)\s*'
    r'(?:last\s*)?\d*\s*(?:days?\s*)?(?:average|avg)?|'
    r'(?:above|high|strong)\s+(?:average\s+)?volume|'
    r'above[- ]average\s+volume|volume\s*surge|'
    r"today'?s?\s+volume",
    re.IGNORECASE,
)


_TF_PATTERNS = [
    (re.compile(r'\b(?:monthly|1\s*month|1m\b)', re.IGNORECASE), "1M"),
    (re.compile(r'\b(?:weekly|1\s*week|1w\b)', re.IGNORECASE),  "1W"),
    (re.compile(r'\b(?:4\s*h(?:our)?r?|4h\b)', re.IGNORECASE), "4H"),
    (re.compile(r'\b(?:1\s*h(?:our)?r?|1h\b|hourly|intraday)', re.IGNORECASE), "1H"),
    (re.compile(r'\b(?:daily|1\s*d(?:ay)?|1d\b)', re.IGNORECASE), "1D"),
]


def _extract_timeframe(text: str) -> str:
    """Returns the most specific timeframe keyword found, defaulting to '1D'."""
    for pattern, tf in _TF_PATTERNS:
        if pattern.search(text):
            return tf
    return "1D"


def _detect_fresh_breakout(text: str) -> bool:
    return bool(_FRESH_BREAKOUT_RE.search(text))

def _detect_approaching_again(text: str) -> bool:
    return bool(_APPROACHING_AGAIN_RE.search(text))

def _detect_rsi_trend(text: str) -> float | None:
    """Returns 1.0 (RISING), -1.0 (FALLING), or None (no filter)."""
    if _UPTREND_RE.search(text):
        return 1.0
    if _DOWNTREND_RE.search(text):
        return -1.0
    return None

def _detect_volume_condition(text: str) -> bool:
    return bool(_VOLUME_ABOVE_RE.search(text))


def _extract_bb_condition(lower: str) -> tuple[str, float]:
    """
    Maps natural-language Bollinger Band phrases to (op, percent_b threshold).

    Band position reference:
      percent_b > 1.0  → price above upper band
      percent_b ≈ 1.0  → price touching/at upper band
      percent_b > 0.5  → price above middle band
      percent_b = 0.5  → price at middle band
      percent_b < 0.5  → price below middle band
      percent_b ≈ 0.0  → price touching/at lower band
      percent_b < 0.0  → price below lower band
    """
    # Price above / breaking above upper band (allow "the" between words)
    if re.search(r'above\s+(?:the\s+)?upper|break(?:ing)?\s+(?:out|above)|over\s+(?:the\s+)?upper', lower):
        return ("gt", 1.0)
    # Price touching / at upper band — price must be right at the band
    if re.search(r'(?:touch(?:ing)?|hit(?:ting)?|at|kiss(?:ing)?|reach(?:ing)?)\s+(?:the\s+)?upper', lower):
        return ("gte", 0.95)
    # Near upper band — close but not touching
    if re.search(r'near\s+(?:the\s+)?upper|upper\s+(?:band|bb|bollinger)', lower):
        return ("gte", 0.88)
    # Price below / breaking below lower band
    if re.search(r'below\s+(?:the\s+)?lower|break(?:ing)?\s+(?:down|below)|under\s+(?:the\s+)?lower', lower):
        return ("lt", 0.0)
    # Price touching / near / at lower band
    if re.search(r'(?:touch(?:ing)?|near|at|hit|reach(?:ing)?|kiss(?:ing)?)\s+(?:the\s+)?lower', lower):
        return ("lt", 0.10)
    if re.search(r'lower\s+(?:band|bb|bollinger)', lower):
        return ("lt", 0.15)
    # Price above middle band / midline / SMA
    if re.search(r'above\s+(?:middle|mid(?:line)?|sma|center)|(?:middle|mid(?:line)?|sma)\s+(?:cross(?:ed)?\s+)?(?:above|up)', lower):
        return ("gt", 0.55)
    # Price below middle band
    if re.search(r'below\s+(?:middle|mid(?:line)?|sma|center)|(?:middle|mid(?:line)?|sma)\s+(?:cross(?:ed)?\s+)?(?:below|down)', lower):
        return ("lt", 0.45)
    # Default: near upper band when no specific condition found
    return ("gt", 0.80)


_FILTER_EXTRACTION_SYSTEM = """You are a stock screening filter extractor for Indian markets (NSE/BSE).
Given a natural language screening request, output ONLY a JSON object with filter conditions. No explanation, no markdown, just raw JSON.

UNIVERSES: NIFTY_50 (50 stocks), NIFTY_500 (500 stocks), NIFTY_TOTAL_MARKET (1750+ stocks)

TIMEFRAMES — every filter condition has a "timeframe" field (default "1D"):
  "1H"  — 1-hour candles  (intraday / short-term)
  "4H"  — 4-hour candles  (medium-term intraday, synthetic from 1H)
  "1D"  — daily candles   (DEFAULT — use when no timeframe specified)
  "1W"  — weekly candles  (swing / long-term)
  "1M"  — monthly candles (macro / very long-term)

  Multi-timeframe example — "RSI > 60 daily AND RSI > 60 weekly":
    [{"indicator": "rsi", "field": "value", "timeframe": "1D", "op": "gt", "value": 60},
     {"indicator": "rsi", "field": "value", "timeframe": "1W", "op": "gt", "value": 60}]

  Rules for timeframe selection:
    user says "1 hour" / "hourly" / "intraday" / "1H"  → timeframe="1H"
    user says "4 hour" / "4H"                           → timeframe="4H"
    user says "daily" / "1D" / no mention               → timeframe="1D"
    user says "weekly" / "1W" / "long term"             → timeframe="1W"
    user says "monthly" / "1M"                          → timeframe="1M"
    user says "short term AND long term" → emit two conditions with "1H" and "1W"

RSI MOMENTUM SIGNALS — use indicator="rsi_momentum", field="signal_rank", timeframe="1D":
  FRESH_BREAKOUT    = 5.0  → RSI just crossed above threshold for the first time in the lookback window
  APPROACHING_AGAIN = 4.5  → was above threshold in lookback, pulled back to within 5pts below — second-chance entry
  APPROACHING       = 4.0  → RSI within 5pts below threshold, rising, never crossed before in lookback
  ALREADY_STRONG    = 3.0  → RSI already above threshold
  EXTENDED          = 2.0  → RSI ≥ 70 (overbought)
  NEUTRAL           = 1.0  → RSI below approaching zone

  Signal range shortcuts:
  "fresh breakout only"          → gte 5.0
  "approaching again only"       → gte 4.5 AND lt 5.0
  "approaching (first time only)"→ gte 4.0 AND lt 4.5
  "approaching or fresh"         → gte 4.0
  "any momentum signal"          → gte 3.0

RSI TREND — use indicator="rsi_momentum", field="rsi_trend", timeframe="1D":
  uptrend / rising RSI  → op="eq", value=1.0
  flat                  → op="eq", value=0.0
  downtrend / falling   → op="eq", value=-1.0

RSI VALUE — use indicator="rsi", field="value", timeframe="1D":
  "RSI above 60" → op="gt", value=60
  "RSI below 30" → op="lt", value=30
  (only use this when no RSI momentum signal is mentioned)

BOLLINGER BANDS — use indicator="bollinger", field="percent_b", timeframe="1D":
  above upper band                        → op="gt",  value=1.0
  touching / at upper band (price at UB)  → op="gte", value=0.95
  near upper band (close to UB)           → op="gte", value=0.88
  above middle band                       → op="gt",  value=0.5
  near lower band                         → op="lte", value=0.15
  at / below lower band                   → op="lte", value=0.0

  IMPORTANT: "touches upper BB" means price is AT or ABOVE the upper band — use value=0.95 minimum.
  "near upper BB" or "close to upper BB" uses value=0.88.
  Never use value=0.85 or lower for "touches" — that only means "above middle".

VOLUME — use indicator="volume_strength", field="volume_ratio", timeframe="1D":
  "volume > 30-day average" / "above average volume" → op="gt", value=100.0
  "volume 2x average"                                → op="gt", value=200.0

MACD — use indicator="macd", timeframe="1D":
  bullish crossover (MACD just crossed above signal today) → field="bullish_crossover", op="eq", value=1.0
  bearish crossover (MACD just crossed below signal today) → field="bearish_crossover", op="eq", value=1.0
  MACD above signal / bullish momentum                     → field="histogram", op="gt", value=0
  MACD below signal / bearish momentum                     → field="histogram", op="lt", value=0
  MACD histogram growing (stronger bullish)                → add field="histogram", op="gt", value=0 (pair with bullish_crossover if crossover wanted)

  Note: "MACD bullish" or "MACD positive" → histogram > 0
        "MACD crossover" or "MACD golden cross" → bullish_crossover eq 1.0

MARKET CAP — use type="classification", field="market_cap_category", op="in":
  large cap → value=["LARGE_CAP"]
  mid cap   → value=["MID_CAP"]
  small cap → value=["SMALL_CAP"]

JSON format:
{
  "universe": "NIFTY_500",
  "conditions": [
    {"type": "indicator", "indicator": "rsi_momentum", "field": "signal_rank", "timeframe": "1D", "op": "gte", "value": 4.5},
    {"type": "indicator", "indicator": "rsi_momentum", "field": "signal_rank", "timeframe": "1D", "op": "lt",  "value": 5.0},
    {"type": "indicator", "indicator": "bollinger",    "field": "percent_b",   "timeframe": "1D", "op": "gte", "value": 0.85},
    {"type": "indicator", "indicator": "volume_strength", "field": "volume_ratio", "timeframe": "1D", "op": "gt", "value": 100.0}
  ],
  "rank_by": {"indicator": "rsi_momentum", "field": "rsi_today", "timeframe": "1D", "order": "desc"}
}

Rules:
- rank_by: use rsi_momentum/rsi_today/desc for momentum screens, rsi/value/desc for plain RSI screens, null if unclear
- If no specific conditions match, use rsi indicator with a sensible default
- Output ONLY the JSON. No text before or after."""


def _llm_extract_filters(message: str) -> dict | None:
    """Ask the LLM to convert natural language into structured filter JSON."""
    if not llm_provider.is_configured():
        return None
    try:
        result = llm_provider.complete(LLMCompletionOptions(
            messages=[LLMMessage(role="user", content=message)],
            system_prompt=_FILTER_EXTRACTION_SYSTEM,
            temperature=0.0,
            max_tokens=600,
        ))
        text = result.content.strip()
        # Strip markdown fences if the LLM wrapped the JSON
        text = re.sub(r'^```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        m = re.search(r'\{.*\}', text, re.DOTALL)
        if m:
            return json.loads(m.group())
    except Exception as e:
        logger.debug("LLM filter extraction failed", error=str(e))
    return None


def _detect_intent(message: str) -> str:
    # Screen: RSI/Bollinger filter or stock listing request
    if any(p.search(message) for p in _SCREEN_PATTERNS):
        return "SCREEN"
    lower = message.lower()
    # Fundamentals: ratio / metric keywords
    if any(kw in lower for kw in _FUNDAMENTAL_KW):
        return "FUNDAMENTALS"
    # Quote: price lookup for a specific symbol
    symbols = _extract_symbols(message)
    if symbols and any(kw in lower for kw in _QUOTE_KW):
        return "QUOTE"
    if symbols:
        return "QUOTE"
    return "GENERAL"


# ─── Context builders ─────────────────────────────────────────────────────────

def _fmt_quote(data: dict) -> str:
    sym = data.get("symbol", "?")
    name = data.get("company_name", sym)
    price = data.get("price")
    chg = data.get("change")
    chg_pct = data.get("change_pct")
    high52 = data.get("week52_high")
    low52 = data.get("week52_low")
    vol = data.get("volume")

    price_str = f"₹{price:,.2f}" if price else "N/A"
    chg_str = ""
    if chg is not None and chg_pct is not None:
        sign = "+" if chg >= 0 else ""
        chg_str = f" ({sign}{chg:.2f}, {sign}{chg_pct:.2f}%)"

    lines = [f"**{sym}** ({name})", f"Price: {price_str}{chg_str}"]
    if high52 and low52:
        lines.append(f"52-week: ₹{low52:,.2f} – ₹{high52:,.2f}")
    if vol:
        lines.append(f"Volume: {vol:,}")
    return "\n".join(lines)


def _fmt_fundamentals(data: dict) -> str:
    sym = data.get("symbol", "?")
    lines = [f"**{sym}** — Fundamentals"]
    fields = [
        ("trailing_pe", "Trailing P/E"),
        ("forward_pe", "Forward P/E"),
        ("price_to_book", "P/B"),
        ("price_to_sales", "P/S"),
        ("ev_to_ebitda", "EV/EBITDA"),
        ("roe", "ROE"),
        ("roa", "ROA"),
        ("profit_margin", "Profit Margin"),
        ("revenue_growth", "Revenue Growth"),
        ("earnings_growth", "Earnings Growth"),
        ("debt_to_equity", "Debt/Equity"),
        ("current_ratio", "Current Ratio"),
        ("dividend_yield", "Dividend Yield"),
        ("beta", "Beta"),
    ]
    for key, label in fields:
        v = data.get(key)
        if v is not None:
            if key in ("roe", "roa", "profit_margin", "revenue_growth", "earnings_growth", "dividend_yield"):
                lines.append(f"  {label}: {v*100:.2f}%")
            else:
                lines.append(f"  {label}: {v:.2f}")
    return "\n".join(lines)


def _bb_signal_label(pct_b: float) -> str:
    if pct_b > 1.05:
        return "ABOVE UPPER BAND"
    if pct_b >= 0.95:
        return "TOUCHING UPPER BAND"
    if pct_b >= 0.88:
        return "NEAR UPPER BAND"
    if pct_b > 0.55:
        return "ABOVE MIDDLE (not near upper band)"
    if pct_b >= 0.45:
        return "AT MIDDLE BAND"
    if pct_b > 0.10:
        return "BELOW MIDDLE"
    if pct_b >= 0.0:
        return "NEAR/AT LOWER BAND"
    return "BELOW LOWER BAND"


def _fmt_stock_indicators(s: dict) -> list[str]:
    """Return list of formatted indicator strings for a single stock result."""
    parts = []
    for k, v in (s.get("indicators") or {}).items():
        if not isinstance(v, dict):
            continue
        tf_upper = k.upper()
        if   "_1H" in tf_upper: tf_label = "(1H)"
        elif "_4H" in tf_upper: tf_label = "(4H)"
        elif "_1D" in tf_upper: tf_label = "(1D)"
        elif "_1W" in tf_upper: tf_label = "(1W)"
        elif "_1M" in tf_upper: tf_label = "(1M)"
        else:                   tf_label = ""
        k_lower = k.lower()
        if k_lower.startswith("rsi_momentum"):
            rsi_today = v.get("rsi_today")
            sig = v.get("signal", "")
            days = v.get("days_since_above_60")
            if rsi_today is not None:
                days_str = f", {int(days)}d ago" if days else ""
                parts.append(f"RSI Momentum {tf_label}={rsi_today:.1f} [{sig}{days_str}]")
        elif k_lower.startswith("volume_strength"):
            ratio = v.get("volume_ratio")
            sig = v.get("signal", "")
            if ratio is not None:
                parts.append(f"Vol Ratio {tf_label}={ratio:.0f}% [{sig}]")
        elif k_lower.startswith("bollinger"):
            pct_b = v.get("percent_b")
            upper = v.get("upper")
            middle = v.get("middle")
            lower_val = v.get("lower")
            if pct_b is not None:
                bb_label = _bb_signal_label(pct_b)
                bb_parts = [f"BB {tf_label} %B={pct_b:.3f} [{bb_label}]"]
                if upper and middle and lower_val:
                    bb_parts.append(f"upper=₹{upper:,.2f} mid=₹{middle:,.2f} lower=₹{lower_val:,.2f}")
                parts.append(" | ".join(bb_parts))
        elif k_lower.startswith("macd"):
            macd_val = v.get("macd")
            sig_line = v.get("signal_line")
            hist     = v.get("histogram")
            signal   = v.get("signal", "")
            bc       = v.get("bullish_crossover", 0.0)
            brc      = v.get("bearish_crossover", 0.0)
            if macd_val is not None:
                cross_tag = " ⚡CROSSOVER" if bc or brc else ""
                parts.append(
                    f"MACD {tf_label}={macd_val:.4f} Signal={sig_line:.4f} "
                    f"Hist={hist:+.4f} [{signal}{cross_tag}]"
                )
        elif k_lower.startswith("rsi"):
            val = v.get("value")
            sig = v.get("signal", "")
            if val is not None:
                parts.append(f"RSI {tf_label}={val:.2f} [{sig}]")
        else:
            val = v.get("value")
            if val is not None:
                parts.append(f"{k.split('_')[0].upper()} {tf_label}={val:.2f}")
    return parts


_SIGNAL_RANK_NAMES = {
    5.0: "FRESH_BREAKOUT (RSI just crossed above threshold for first time)",
    4.5: "APPROACHING_AGAIN (RSI pulled back to within 5pts below threshold — second-chance entry)",
    4.0: "APPROACHING (RSI within 5pts below threshold, rising, never crossed before)",
    3.0: "ALREADY_STRONG (RSI above threshold)",
    2.0: "EXTENDED (RSI ≥ 70, overbought)",
    1.0: "NEUTRAL",
}
_TREND_NAMES = {1.0: "RISING", 0.0: "FLAT", -1.0: "FALLING"}


def _describe_conditions(conditions: list[dict]) -> str:
    """Produce a human-readable summary of the filter conditions actually executed."""
    parts: list[str] = []
    # Collect signal_rank bounds to describe them together
    sig_gte: float | None = None
    sig_lt:  float | None = None

    for c in conditions:
        if c.get("type") != "indicator":
            field = c.get("field", "")
            if field == "market_cap_category":
                parts.append(f"Cap: {c.get('value')}")
            continue
        ind   = c.get("indicator", "")
        field = c.get("field", "")
        op    = c.get("op", "")
        val   = c.get("value")

        tf = c.get("timeframe", "1D").upper()
        tf_tag = f"[{tf}]" if tf != "1D" else ""

        if ind == "rsi_momentum" and field == "signal_rank":
            if op in ("gte", "gt"):
                sig_gte = float(val)
            elif op in ("lt", "lte"):
                sig_lt = float(val)
        elif ind == "rsi_momentum" and field == "rsi_trend":
            parts.append(f"RSI Trend{tf_tag} = {_TREND_NAMES.get(float(val), val)}")
        elif ind == "bollinger" and field == "percent_b":
            parts.append(f"Bollinger %B{tf_tag} {op} {val}")
        elif ind == "volume_strength" and field == "volume_ratio":
            parts.append(f"Volume{tf_tag} > {val}% of 30-day average")
        elif ind == "rsi" and field == "value":
            parts.append(f"RSI{tf_tag} {op} {val}")
        elif ind == "macd":
            if field == "bullish_crossover" and float(val) == 1.0:
                parts.append(f"MACD{tf_tag}: Bullish crossover today (MACD crossed above Signal)")
            elif field == "bearish_crossover" and float(val) == 1.0:
                parts.append(f"MACD{tf_tag}: Bearish crossover today (MACD crossed below Signal)")
            elif field == "histogram":
                direction = "bullish (above signal)" if op == "gt" else "bearish (below signal)"
                parts.append(f"MACD{tf_tag} histogram {op} {val} → {direction}")
            else:
                parts.append(f"MACD{tf_tag} {field} {op} {val}")

    if sig_gte is not None:
        label = _SIGNAL_RANK_NAMES.get(sig_gte, f"signal_rank ≥ {sig_gte}")
        if sig_lt == 5.0 and sig_gte == 4.5:
            label = "APPROACHING_AGAIN — RSI was above threshold in lookback window, pulled back to within 5pts below (second-chance entry, threshold = 60 by default)"
        elif sig_lt is None and sig_gte == 5.0:
            label = "FRESH_BREAKOUT — RSI just crossed above threshold (60) for first time in lookback window"
        parts.insert(0, f"Signal: {label}")

    return " | ".join(parts) if parts else "all stocks"


def _fmt_screen_results(data: dict, group_by_sector: bool = False,
                        filter_summary: str = "") -> str:
    universe = data.get("universe", "")
    matched = data.get("total_matched", 0)
    screened = data.get("stocks_screened", 0)
    stocks = data.get("stocks", [])

    if matched == 0:
        return (
            f"**Screen Results — {universe}**\n"
            f"Active filters: {filter_summary}\n"
            f"No stocks matched the filter conditions out of {screened} screened."
        )

    header = [
        f"**Screen Results — {universe}**",
        f"Active filters: {filter_summary}",
        f"{matched} stocks matched out of {screened} screened\n",
    ]

    display = stocks[:20]

    if group_by_sector:
        # Group stocks by sector, preserving existing rank order within each sector
        from collections import defaultdict
        sector_map: dict[str, list[dict]] = defaultdict(list)
        for s in display:
            sector_map[s.get("sector") or "Other"].append(s)

        lines = list(header)
        global_i = 1
        for sector_name in sorted(sector_map.keys()):
            lines.append(f"## {sector_name} ({len(sector_map[sector_name])})")
            for s in sector_map[sector_name]:
                sym = s.get("symbol", "?")
                name = s.get("company_name", "")
                cap = s.get("market_cap_category", "")
                score = s.get("score")
                lines.append(f"{global_i}. **{sym}** ({name}) [{cap}]")
                for part in _fmt_stock_indicators(s):
                    lines.append(f"   {part}")
                if score is not None:
                    lines.append(f"   Score: {score:.1f}")
                global_i += 1
    else:
        lines = list(header)
        for i, s in enumerate(display, 1):
            sym = s.get("symbol", "?")
            name = s.get("company_name", "")
            sector = s.get("sector", "")
            cap = s.get("market_cap_category", "")
            score = s.get("score")
            lines.append(f"{i}. **{sym}** ({name}) [{cap}] {sector}")
            for part in _fmt_stock_indicators(s):
                lines.append(f"   {part}")
            if score is not None:
                lines.append(f"   Score: {score:.1f}")

    return "\n".join(lines)


# ─── Agent ────────────────────────────────────────────────────────────────────

class LLMChatAgent:
    agent_id = "chat_agent"
    task_types = ["CHAT_TURN"]

    def handle(self, task: AgentTask) -> AgentResult:
        try:
            payload = task.payload or {}
            user_message: str = payload.get("user_message", "")
            history: list[dict] = payload.get("history", [])

            intent = _detect_intent(user_message)
            context_blocks: list[str] = []

            if intent == "SCREEN":
                context_blocks.append(self._do_screen(task, user_message))
            elif intent == "QUOTE":
                for sym in _extract_symbols(user_message)[:3]:
                    block = self._do_quote(task, sym)
                    if block:
                        context_blocks.append(block)
            elif intent == "FUNDAMENTALS":
                for sym in _extract_symbols(user_message)[:3]:
                    block = self._do_fundamentals(task, sym)
                    if block:
                        context_blocks.append(block)

            context = "\n\n".join(context_blocks)
            reply = self._llm_respond(user_message, context, history)

            return AgentResult(
                task_id=task.task_id,
                correlation_id=task.correlation_id,
                agent=self.agent_id,
                status="SUCCESS",
                data={"reply": reply, "intent": intent, "has_context": bool(context)},
            )
        except Exception as e:
            logger.error("LLMChatAgent: failed", error=str(e))
            return AgentResult(
                task_id=task.task_id,
                correlation_id=task.correlation_id,
                agent=self.agent_id,
                status="FAILED",
                data=None,
                errors=[AgentError(code="CHAT_FAILED", message=str(e))],
            )

    # ─── Tool dispatchers ─────────────────────────────────────────────────────

    def _do_screen(self, task: AgentTask, message: str) -> str:
        group_by_sector = _detect_sector_grouping(message)

        # ── Phase 1: LLM extracts structured filter conditions ────────────────
        extracted = _llm_extract_filters(message)

        if extracted and "conditions" in extracted:
            universe   = extracted.get("universe", _extract_universe(message))
            conditions = extracted.get("conditions", [])
            rank_by    = extracted.get("rank_by")

            # Append market cap classification filter if regex detects one
            # (LLM may miss informal phrases like "large cap stocks")
            cap_filter = _extract_market_cap(message)
            if cap_filter and not any(
                c.get("field") == "market_cap_category" for c in conditions
            ):
                conditions.append({
                    "type": "classification",
                    "field": "market_cap_category",
                    "op": "in",
                    "value": [cap_filter],
                })

            if not conditions:
                conditions.append({
                    "type": "indicator", "indicator": "rsi",
                    "field": "value", "timeframe": "1D",
                    "op": "lt", "value": 100.0,
                })

            logger.info("Screen via LLM extraction", universe=universe,
                        n_conditions=len(conditions))
        else:
            # ── Phase 2: Fallback — regex-based extraction ────────────────────
            logger.info("Screen via regex fallback (LLM extraction failed)")
            universe   = _extract_universe(message)
            cap_filter = _extract_market_cap(message)
            rsi_cond   = _extract_rsi_threshold(message)
            lower      = message.lower()
            conditions = []
            rank_by    = None

            # Detect the primary timeframe mentioned (default 1D)
            tf = _extract_timeframe(message)

            is_fresh_breakout    = _detect_fresh_breakout(message)
            is_approaching_again = _detect_approaching_again(message)
            rsi_trend_val        = _detect_rsi_trend(message)

            # RSI momentum signals always use 1D (they are daily calculations)
            if is_approaching_again:
                conditions += [
                    {"type": "indicator", "indicator": "rsi_momentum", "field": "signal_rank",
                     "timeframe": "1D", "op": "gte", "value": 4.5},
                    {"type": "indicator", "indicator": "rsi_momentum", "field": "signal_rank",
                     "timeframe": "1D", "op": "lt",  "value": 5.0},
                ]
                rank_by = {"indicator": "rsi_momentum", "field": "rsi_today", "timeframe": "1D", "order": "desc"}
            elif is_fresh_breakout:
                conditions.append({
                    "type": "indicator", "indicator": "rsi_momentum", "field": "signal_rank",
                    "timeframe": "1D", "op": "gte", "value": 5.0,
                })
                rank_by = {"indicator": "rsi_momentum", "field": "rsi_today", "timeframe": "1D", "order": "desc"}
            elif rsi_cond:
                op, val = rsi_cond
                conditions.append({
                    "type": "indicator", "indicator": "rsi",
                    "field": "value", "timeframe": tf, "op": op, "value": val,
                })

            if rsi_trend_val is not None:
                conditions.append({
                    "type": "indicator", "indicator": "rsi_momentum",
                    "field": "rsi_trend", "timeframe": "1D", "op": "eq", "value": rsi_trend_val,
                })

            if re.search(r'\bbollinger\b|\b(?:lower|upper)\s+band\b|%b\b|percent\s*b\b|\bbb\b', lower):
                op, val = _extract_bb_condition(lower)
                conditions.append({
                    "type": "indicator", "indicator": "bollinger",
                    "field": "percent_b", "timeframe": tf, "op": op, "value": val,
                })

            if _detect_volume_condition(message):
                conditions.append({
                    "type": "indicator", "indicator": "volume_strength",
                    "field": "volume_ratio", "timeframe": tf, "op": "gt", "value": 100.0,
                })

            # MACD regex fallback
            if re.search(r'\bmacd\b', lower):
                if re.search(r'cross(?:over)?|golden\s+cross|bullish\s+cross', lower):
                    conditions.append({
                        "type": "indicator", "indicator": "macd",
                        "field": "bullish_crossover", "timeframe": tf, "op": "eq", "value": 1.0,
                    })
                elif re.search(r'bearish\s+cross|death\s+cross', lower):
                    conditions.append({
                        "type": "indicator", "indicator": "macd",
                        "field": "bearish_crossover", "timeframe": tf, "op": "eq", "value": 1.0,
                    })
                elif re.search(r'bearish|below\s+signal|negative', lower):
                    conditions.append({
                        "type": "indicator", "indicator": "macd",
                        "field": "histogram", "timeframe": tf, "op": "lt", "value": 0,
                    })
                else:
                    # Default: MACD bullish (histogram > 0)
                    conditions.append({
                        "type": "indicator", "indicator": "macd",
                        "field": "histogram", "timeframe": tf, "op": "gt", "value": 0,
                    })

            if not conditions:
                conditions.append({
                    "type": "indicator", "indicator": "rsi",
                    "field": "value", "timeframe": "1D", "op": "lt", "value": 100.0,
                })

            if cap_filter:
                conditions.append({
                    "type": "classification", "field": "market_cap_category",
                    "op": "in", "value": [cap_filter],
                })

        filters = {"and": conditions} if conditions else None
        payload = {"universe": universe, "filters": filters, "limit": 20}
        if rank_by:
            payload["rank_by"] = rank_by

        result = agent_message_bus.dispatch(AgentTask(
            from_agent=self.agent_id,
            to_agent="filter_agent",
            task_type="RUN_SCREEN",
            payload=payload,
            correlation_id=task.correlation_id,
        ))

        if result.status == "SUCCESS" and result.data:
            return _fmt_screen_results(
                result.data,
                group_by_sector=group_by_sector,
                filter_summary=_describe_conditions(conditions),
            )
        err = result.errors[0].message if result.errors else "unknown error"
        return f"Screen failed: {err}"

    def _do_quote(self, task: AgentTask, symbol: str) -> str | None:
        result = agent_message_bus.dispatch(AgentTask(
            from_agent=self.agent_id,
            to_agent="market_data_agent",
            task_type="GET_QUOTE",
            payload={"exchange": "NSE", "symbol": symbol},
            correlation_id=task.correlation_id,
        ))
        if result.status == "SUCCESS" and result.data:
            return _fmt_quote(result.data)
        return None

    def _do_fundamentals(self, task: AgentTask, symbol: str) -> str | None:
        result = agent_message_bus.dispatch(AgentTask(
            from_agent=self.agent_id,
            to_agent="fundamental_agent",
            task_type="GET_FUNDAMENTALS",
            payload={"exchange": "NSE", "symbol": symbol},
            correlation_id=task.correlation_id,
        ))
        if result.status == "SUCCESS" and result.data:
            return _fmt_fundamentals(result.data)
        return None

    # ─── LLM synthesis ────────────────────────────────────────────────────────

    def _llm_respond(self, user_message: str, context: str, history: list[dict]) -> str:
        if not llm_provider.is_configured():
            return (
                "LLM is not configured. Set LLM_API_KEY and LLM_API_BASE_URL "
                "(e.g., https://api.groq.com/openai/v1) in your .env file."
            )

        messages: list[LLMMessage] = []

        for m in history[-10:]:
            role = m.get("role", "user")
            if role in ("user", "assistant"):
                messages.append(LLMMessage(role=role, content=m["content"]))

        if context:
            user_content = (
                f"{user_message}\n\n"
                f"═══ FRESH MARKET DATA (just retrieved for this question) ═══\n"
                f"{context}\n"
                f"═══ END OF FRESH DATA ═══\n\n"
                f"Answer using the fresh data above."
            )
        else:
            user_content = user_message

        messages.append(LLMMessage(role="user", content=user_content))

        result = llm_provider.complete(LLMCompletionOptions(
            messages=messages,
            system_prompt=_SYSTEM_PROMPT,
            temperature=0.3,
            max_tokens=1024,
        ))
        return result.content


chat_agent = LLMChatAgent()
