"""Relative Strength Score — "is the stock doing better than the market, its
sector and its peers?" (framework section 6). Price only; the reasons behind
it belong to Business Quality and are reported separately (section 3's
"special situational logic").

  vs market            return over 1, 3, 6 and 12 months against the Nifty 50
                       (weighted 10/20/30/40), compounded excess return
  vs sector            the same against the stock's NSE sector index, or the
                       median of same-sector stocks when NSE has no index for
                       the sector (app/prices/benchmarks.py says which)
  sector percentile    rank of the 6- and 12-month return among same-sector
                       stocks — the "same-sector alternatives" comparison
  resilience           return during the Nifty 50's worst fall of the year and
                       in the recovery since its low, against the index
  drawdown vs market   the stock's largest fall of the year against the index's
  near 52-week high    last close against the year's high (new-high participation)

Comparison with the user's own holdings is added with the portfolio (phase 10).
"""
from __future__ import annotations

import math
import statistics
from datetime import date

from sqlalchemy.orm import Session

from app.calculations.scoring import _score_metric
from app.framework import price_stats
from app.infrastructure.database.models import Stock
from app.prices import benchmarks

_WEIGHTS = {"vs_market": 0.25, "vs_sector": 0.25, "sector_percentile": 0.15, "resilience": 0.15,
            "drawdown_vs_market": 0.10, "near_52_week_high": 0.10}
_WINDOW_WEIGHTS = {"1M": 0.10, "3M": 0.20, "6M": 0.30, "1Y": 0.40}
_MONTHS = {"1M": 1, "3M": 3, "6M": 6, "1Y": 12}
_EXCESS_1Y = [(-40, 0), (-20, 15), (-10, 30), (0, 50), (10, 70), (20, 85), (40, 100)]
_RESILIENCE = [(-20, 5), (-10, 25), (-3, 45), (0, 55), (5, 75), (10, 90), (20, 100)]
_DD_GAP = [(-30, 5), (-15, 30), (-5, 50), (0, 60), (5, 75), (15, 95), (25, 100)]
_NEAR_HIGH = [(0.5, 5), (0.7, 30), (0.85, 60), (0.95, 85), (1.0, 100)]
_MIN_PEERS = 5
_MIN_MARKET_FALL = 5.0


def _excess_score(excess_by_window: dict[str, float | None]) -> tuple[float | None, dict]:
    """Each window's excess is scaled to a one-year equivalent (by the square
    root of time) before scoring, so a 5% lead over a month counts like a
    17% lead over a year."""
    parts, used = [], {}
    for w, x in excess_by_window.items():
        if x is None:
            continue
        used[w] = round(x, 2)
        parts.append((_score_metric(x * math.sqrt(12 / _MONTHS[w]), _EXCESS_1Y), _WINDOW_WEIGHTS[w]))
    if not parts:
        return None, used
    total = sum(w for _, w in parts)
    return round(sum(s * w for s, w in parts) / total, 1), used


def _peer_ids(db: Session, stock: Stock) -> list[str]:
    return [sid for (sid,) in db.query(Stock.id).filter(Stock.sector == stock.sector, Stock.is_active.is_(True), Stock.id != stock.id)]


def vs_market(own: dict, end: date) -> dict:
    market = price_stats.window_returns(price_stats.index_year(benchmarks.MARKET, end), end)
    score, used = _excess_score({w: price_stats.excess(own.get(w), market.get(w)) for w in _WINDOW_WEIGHTS})
    if score is None:
        return {"score": None, "reason": "no overlapping returns with the Nifty 50"}
    return {"score": score, "benchmark": benchmarks.MARKET, "excess_pct": used,
            "stock_return_pct": {w: round(v, 2) for w, v in own.items() if v is not None},
            "benchmark_return_pct": {w: round(v, 2) for w, v in market.items() if v is not None},
            "source": "NSE daily index file; stored adjusted stock prices"}


def vs_sector(db: Session, stock: Stock, own: dict, end: date, universe: dict) -> dict:
    bench = benchmarks.sector_benchmark(stock.sector, stock.industry)
    if bench["index"]:
        ref = price_stats.window_returns(price_stats.index_year(bench["index"], end), end)
        label, kind = bench["index"], bench["kind"]
    else:
        peers = [universe[p] for p in _peer_ids(db, stock) if p in universe]
        ref = {}
        for w in _WINDOW_WEIGHTS:
            vals = [r[w] for r in peers if w in r]
            ref[w] = statistics.median(vals) if len(vals) >= _MIN_PEERS else None
        label, kind = f"median of {len(peers)} {stock.sector or 'same-sector'} stocks", "peers"
    score, used = _excess_score({w: price_stats.excess(own.get(w), ref.get(w)) for w in _WINDOW_WEIGHTS})
    if score is None:
        return {"score": None, "reason": f"no comparable return for {label}", "benchmark_kind": kind}
    return {"score": score, "benchmark": label, "benchmark_kind": kind, "excess_pct": used,
            "benchmark_return_pct": {w: round(v, 2) for w, v in ref.items() if v is not None}}


def sector_percentile(db: Session, stock: Stock, own: dict, universe: dict) -> dict:
    if own.get("6M") is None:
        return {"score": None, "reason": "less than six months of stored prices"}
    peers = [universe[p] for p in _peer_ids(db, stock) if p in universe]
    pcts = {}
    for w in ("6M", "1Y"):
        others = [r[w] for r in peers if w in r]
        if own.get(w) is None or len(others) < _MIN_PEERS:
            continue
        pcts[w] = 100 * (sum(1 for o in others if o < own[w]) + 0.5 * sum(1 for o in others if o == own[w])) / len(others)
    if not pcts:
        return {"score": None, "reason": f"fewer than {_MIN_PEERS} same-sector stocks with prices"}
    pct = sum(pcts.values()) / len(pcts)
    top = 100 - pct
    label = ("Top 10%" if top <= 10 else "Top 25%" if top <= 25 else "Top 40%" if top <= 40
             else "Top 50%" if top <= 50 else "Bottom 50%")
    return {"score": round(pct, 1), "percentile": round(pct, 1), "label": label, "sector": stock.sector,
            "peers_compared": len(peers), "by_window": {w: round(v, 1) for w, v in pcts.items()}}


def resilience(year: list, market_year: list) -> dict:
    """The framework's own example: Nifty -10%, sector -8%, stock -2% is
    resilience. Read on the market's worst fall of the year and its recovery."""
    fall, peak, trough = price_stats.max_drawdown(market_year)
    if fall is None or -fall < _MIN_MARKET_FALL:
        return {"score": None, "reason": f"the Nifty 50 did not fall {_MIN_MARKET_FALL:.0f}% or more this year"}
    own = dict(year)
    mkt = dict(market_year)

    def at(series: dict, day):
        days = [d for d in series if d <= day]
        return series[max(days)] if days else None

    s_peak, s_trough, s_last = at(own, peak), at(own, trough), year[-1][1]
    if not s_peak or not s_trough:
        return {"score": None, "reason": "no prices for the stock across the market's fall"}
    in_fall = price_stats.excess((s_trough / s_peak - 1) * 100, fall)
    m_last = market_year[-1][1]
    since_low = price_stats.excess((s_last / s_trough - 1) * 100, (m_last / mkt[trough] - 1) * 100)
    score = 0.6 * _score_metric(in_fall, _RESILIENCE) + 0.4 * _score_metric(since_low, _RESILIENCE)
    return {"score": round(score, 1), "market_fall_pct": round(fall, 1), "market_peak": peak.isoformat(),
            "market_low": trough.isoformat(), "stock_during_fall_pct": round((s_trough / s_peak - 1) * 100, 1),
            "excess_during_fall_pct": round(in_fall, 1), "excess_since_low_pct": round(since_low, 1)}


def drawdown_vs_market(year: list, market_year: list) -> dict:
    own, mkt = price_stats.max_drawdown(year)[0], price_stats.max_drawdown(market_year)[0]
    if own is None or mkt is None:
        return {"score": None, "reason": "not enough prices"}
    return {"score": round(_score_metric(own - mkt, _DD_GAP), 1), "stock_max_fall_pct": round(own, 1),
            "market_max_fall_pct": round(mkt, 1)}


def near_high(year: list) -> dict:
    high = max(v for _, v in year)
    ratio = year[-1][1] / high
    return {"score": round(_score_metric(ratio, _NEAR_HIGH), 1), "close_to_52_week_high": round(ratio, 3)}


def compute_relative_strength(db: Session, stock_id: str, end: date | None) -> dict:
    stock = db.get(Stock, stock_id)
    if end is None or stock is None:
        return {"score": None, "reason": "no stored prices", "components": {}}
    year = price_stats.stock_year(db, stock_id, end)
    if len(year) < 20:
        return {"score": None, "reason": "no stored prices for this stock", "components": {}}
    market_year = price_stats.index_year(benchmarks.MARKET, end)
    universe = price_stats.universe_returns(end)
    own = price_stats.window_returns(year, end)
    if own.get("3M") is None:
        return {"score": None, "reason": "less than three months of stored prices", "components": {}}
    listed_a_year = year[0][0] <= end.replace(year=end.year - 1)
    parts = {
        "vs_market": vs_market(own, end),
        "vs_sector": vs_sector(db, stock, own, end, universe),
        "sector_percentile": sector_percentile(db, stock, own, universe),
        "resilience": resilience(year, market_year) if listed_a_year else {"score": None, "reason": "listed less than a year"},
        "drawdown_vs_market": drawdown_vs_market(year, market_year) if listed_a_year else {"score": None, "reason": "listed less than a year"},
        "near_52_week_high": near_high(year),
    }
    for name, part in parts.items():
        part["weight"] = _WEIGHTS[name]
    scored = {n: p for n, p in parts.items() if p.get("score") is not None}
    covered = sum(p["weight"] for p in scored.values())
    score = round(sum(p["score"] * p["weight"] for p in scored.values()) / covered, 1) if covered >= 0.5 else None
    return {"score": score, "coverage": round(covered, 3), "components": parts, "as_of": end.isoformat(),
            "not_measured": ["vs the user's existing holdings (added with the portfolio)"]}


def why_holding_up(relative: dict, fundamental: dict, quantitative: dict, business: dict) -> dict | None:
    """Section 3: when the sector is weak but the stock is holding up, say why —
    from the business data, kept apart from the price strength itself."""
    sector = (relative.get("components") or {}).get("vs_sector") or {}
    ref = sector.get("benchmark_return_pct") or {}
    excess = sector.get("excess_pct") or {}
    weak = [w for w in ("6M", "1Y") if ref.get(w) is not None and ref[w] < 0]
    ahead = [w for w in weak if (excess.get(w) or 0) >= 10]
    if not ahead:
        return None
    q, f, b = quantitative.get("components") or {}, fundamental.get("components") or {}, business.get("components") or {}
    reasons = []
    if ((q.get("growth_acceleration") or {}).get("score") or 0) >= 70:
        reasons.append("earnings growing faster than their usual rate")
    if ((q.get("margin_change") or {}).get("change_pts") or 0) > 0.5:
        reasons.append(f"operating margin up {q['margin_change']['change_pts']} points on a year earlier")
    if ((q.get("debt_change") or {}).get("change") or 0) < -0.05:
        reasons.append("debt falling against equity")
    if ((f.get("cash_flow") or {}).get("score") or 0) >= 70:
        reasons.append("strong cash flow")
    if ((f.get("balance_sheet") or {}).get("score") or 0) >= 75:
        reasons.append("strong balance sheet")
    if ((b.get("durability") or {}).get("score") or 0) >= 75:
        reasons.append("returns on capital of 15% or more held for most of the last decade")
    if ((b.get("margin_resilience") or {}).get("score") or 0) >= 75:
        reasons.append("margins that have held up through past downturns")
    return {"sector_weak_over": weak, "stock_ahead_of_sector_over": ahead,
            "reasons": reasons or ["no business reason found in the data: the strength is price alone"]}
