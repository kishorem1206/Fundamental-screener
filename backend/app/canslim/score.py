"""The seven CANSLIM letters, each scored 0-100 from stored data.

  C  latest quarter's net profit against the same quarter a year earlier:
     50%+ 100, 25%+ 85, 15%+ 60, growth 35, a fall 15. Sales growth of 20%+ adds 5
     to a score already at "ok", a sales fall takes off 5; sales never rescue
     weak profit
  A  three-year net profit CAGR (five if three cannot be read), same bands;
     strong growth with ROE of 17%+ scores 100
  N  distance below the 52-week closing high: within 5% 100, 15% 80, 25% 50,
     40% 25, further 10. The "new product or management" half has no data feed
  S  10-day average volume against the 50-day: 1.5x 100, 1.25x 85, 1.0x 60, else 30
  L  RS Rating, 1-99: the stock's weighted return (latest quarter counted twice,
     then six and twelve months) ranked against every stock. 80+ is a leader
  I  FII + DII holding: 20-70% 100, 10-20% 70, 70-90% 60 (crowded), 5-10% 40,
     under 5% or over 90% 20
  M  Nifty 50 against its 50- and 200-day averages: above both and the 50 above
     the 200 100, above the 200 60, above the 50 only 40, below both 10. The
     same for every stock

Thresholds follow the user's CANSLIM notes, tightened with InCred Money's India
guide (RS 80+, FII + DII above 10%, ROE 17%, volume 40-50% above average).

A letter with no data is left out, never scored as zero. CANSLIM is the average of
the letters available, and needs at least four. Combined is 60% CANSLIM + 40% peer
quality (the stock's Quality percentile among its peers); if one is missing the
other stands alone and `basis` says so.
"""
from __future__ import annotations

import statistics
from datetime import date

MIN_LETTERS = 4
CANSLIM_SHARE, PEER_SHARE = 0.60, 0.40
LEADER_RS = 80


def _band(value: float, bands: list[tuple[float, float]], floor: float) -> float:
    return next((score for limit, score in bands if value >= limit), floor)


_GROWTH = [(50, 100.0), (25, 85.0), (15, 60.0), (0, 35.0)]


def _year_ago(period: str, quarters: list[str]) -> str | None:
    target = f"{int(period[:4]) - 1}{period[4:7]}"
    return next((q for q in quarters if q[:7] == target), None)


def letter_c(q: dict) -> dict:
    usable = [p for p in q.get("quarters", []) if q["rows"][p].get("net_profit") is not None]
    if not usable:
        return {"score": None, "text": "no quarterly results stored"}
    latest = usable[-1]
    before = _year_ago(latest, usable)
    if before is None:
        return {"score": None, "text": f"no quarter a year before {latest}"}
    now, then = q["rows"][latest]["net_profit"], q["rows"][before]["net_profit"]
    if then <= 0:
        score, text = (60.0, f"turned profitable: ₹{now:,.1f} cr against a ₹{then:,.1f} cr loss") if now > 0 else (15.0, "loss-making in both quarters")
        growth = None
    else:
        growth = (now / then - 1) * 100
        score, text = _band(growth, _GROWTH, 15.0), f"net profit {growth:+.1f}% year on year"
    sales_now, sales_then = q["rows"][latest].get("sales"), q["rows"][before].get("sales")
    sales = (sales_now / sales_then - 1) * 100 if sales_now and sales_then and sales_then > 0 else None
    if sales is not None:
        text += f", sales {sales:+.1f}%"
        if sales >= 20 and score >= 60:
            score = min(100.0, score + 5)
        elif sales < 0:
            score = max(0.0, score - 5)
    return {"score": score, "text": f"{text} ({latest})", "growth_pct": growth and round(growth, 1), "sales_growth_pct": sales and round(sales, 1), "quarter": latest}


def letter_a(series: dict, three: float | None, five: float | None) -> dict:
    """`three`, `five`: net profit CAGRs, None where a year was a loss or too few years exist."""
    usable = [y for y in series.get("years", []) if series["rows"][y].get("net_profit") is not None]
    if len(usable) < 4:
        return {"score": None, "text": "fewer than four years of annual results"}
    latest = series["rows"][usable[-1]]
    growth, span = (three, 3) if three is not None else (five, 5)
    roe = latest.get("roe")
    roe_text = f", ROE {roe:.1f}%" if roe is not None else ""
    if growth is None:
        if latest["net_profit"] <= 0:
            return {"score": 15.0, "text": f"latest year was a loss{roe_text}"}
        return {"score": 50.0, "text": f"profitable now after a loss, so no growth rate{roe_text}"}
    score = _band(min(growth, 49.9), _GROWTH, 15.0)
    if score >= 85 and roe is not None and roe >= 17:
        score = 100.0
    return {"score": score, "text": f"{span}-year profit CAGR {growth:.1f}%{roe_text}", "cagr_pct": round(growth, 1), "roe_pct": roe if roe is None else round(roe, 1)}


def letter_n(closes: list[float]) -> dict:
    if len(closes) < 60:
        return {"score": None, "text": "under three months of prices"}
    high = max(closes)
    below = (high - closes[-1]) / high * 100
    score = _band(-below, [(-5, 100.0), (-15, 80.0), (-25, 50.0), (-40, 25.0)], 10.0)
    return {"score": score, "text": "at a new 52-week high" if below == 0 else f"{below:.1f}% below the 52-week high of ₹{high:,.2f}", "below_high_pct": round(below, 1)}


def letter_s(volumes: list[float]) -> dict:
    if len(volumes) < 50:
        return {"score": None, "text": "under 50 days of volume"}
    long_run = statistics.fmean(volumes[-50:])
    if long_run <= 0:
        return {"score": None, "text": "no traded volume"}
    ratio = statistics.fmean(volumes[-10:]) / long_run
    return {"score": _band(ratio, [(1.5, 100.0), (1.25, 85.0), (1.0, 60.0)], 30.0), "text": f"10-day volume {ratio:.2f}x the 50-day average", "volume_ratio": round(ratio, 2)}


def rs_ratings(returns: dict[str, dict[str, float]]) -> dict[str, int]:
    """{stock_id: RS Rating 1-99} over every stock with a full year of returns."""
    weighted = {sid: (2 * r["3M"] + r["6M"] + r["1Y"]) / 4 for sid, r in returns.items() if all(w in r for w in ("3M", "6M", "1Y"))}
    ordered = sorted(weighted.values())
    n = len(ordered)
    if n < 2:
        return {}
    from bisect import bisect_left

    return {sid: 1 + round(98 * bisect_left(ordered, v) / (n - 1)) for sid, v in weighted.items()}


def letter_l(rating: int | None) -> dict:
    if rating is None:
        return {"score": None, "text": "under a year of prices"}
    return {"score": float(rating), "text": f"RS Rating {rating}" + (" (a leader)" if rating >= LEADER_RS else ""), "rs_rating": rating}


def letter_i(fii: float | None, dii: float | None) -> dict:
    if fii is None and dii is None:
        return {"score": None, "text": "no FII or DII holding stored"}
    held = (fii or 0) + (dii or 0)
    if held > 90 or held < 5:
        score = 20.0
    else:
        score = 100.0 if 20 <= held <= 70 else 70.0 if 10 <= held < 20 else 60.0 if held > 70 else 40.0
    return {"score": score, "text": f"FII + DII hold {held:.1f}% (FII {fii or 0:.1f}%, DII {dii or 0:.1f}%)", "held_pct": round(held, 1)}


def market(closes: list[float], on: date) -> dict:
    """Letter M, from the Nifty 50's closes."""
    if len(closes) < 200:
        return {"score": None, "text": "under 200 days of Nifty 50 closes"}
    last, sma50, sma200 = closes[-1], statistics.fmean(closes[-50:]), statistics.fmean(closes[-200:])
    if last > sma200 and last > sma50 and sma50 > sma200:
        score, view = 100.0, "uptrend"
    elif last > sma200:
        score, view = 60.0, "uptrend under pressure"
    elif last > sma50:
        score, view = 40.0, "rally attempt below the 200-day average"
    else:
        score, view = 10.0, "correction: below its 50- and 200-day averages"
    return {"score": score, "text": f"Nifty 50 {last:,.0f}, 50-day {sma50:,.0f}, 200-day {sma200:,.0f}: {view}", "view": view, "as_of": on.isoformat()}


def blend(letters: dict[str, dict], peer_quality: float | None) -> dict:
    available = [p["score"] for p in letters.values() if p.get("score") is not None]
    canslim = round(statistics.fmean(available), 1) if len(available) >= MIN_LETTERS else None
    if canslim is not None and peer_quality is not None:
        combined, basis = round(CANSLIM_SHARE * canslim + PEER_SHARE * peer_quality, 1), "60% CANSLIM + 40% peer quality"
    elif canslim is not None:
        combined, basis = canslim, "CANSLIM only: no peer quality"
    elif peer_quality is not None:
        combined, basis = round(peer_quality, 1), "peer quality only: too few CANSLIM letters"
    else:
        combined, basis = None, None
    return {"letters": len(available), "canslim": canslim, "combined": combined, "basis": basis}
