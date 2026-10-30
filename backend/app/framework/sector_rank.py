"""Peer-relative quality (framework section 11): where a stock's Quality Score
ranks among stocks in the same line of business — "Pharma stock A: 58, rank #3
of 30" can be the stronger holding than "IT stock B: 65, rank #15 of 25".

Peers are the stock's NSE basic industry when that has at least five scored
stocks, otherwise its industry (user's decision, 2026-10-30: the broad sector
compares a shipbuilder with a steel-tube maker). A stock with too few peers at
both levels is not ranked. NSE's hierarchy is strictly nested, so the fallback
never crosses a sector.

Computed when read, from every stock's latest Quality, so a rank always
reflects the whole group as scored now.
"""
from __future__ import annotations

_MIN_PEERS = 5
BASIC, INDUSTRY = "basic industry", "industry"


def label(top_pct: float) -> str:
    return ("Top 10%" if top_pct <= 10 else "Top 25%" if top_pct <= 25 else "Top 40%" if top_pct <= 40
            else "Top 50%" if top_pct <= 50 else "Bottom 50%")


def ranks(rows: list[tuple[str, str | None, str | None, float | None]]) -> dict[str, dict]:
    """rows: (stock_id, basic_industry, industry, quality). Returns {stock_id:
    {rank, of, top_pct, label, group, level}} for stocks with a Quality and at
    least five scored stocks in the group they are measured in."""
    groups: dict[tuple[str, str], list[tuple[str, float]]] = {}
    scored = [r for r in rows if r[3] is not None]
    for sid, basic, industry, quality in scored:
        if basic:
            groups.setdefault((BASIC, basic), []).append((sid, quality))
        if industry:
            groups.setdefault((INDUSTRY, industry), []).append((sid, quality))
    out = {}
    for sid, basic, industry, quality in scored:
        for level, name in ((BASIC, basic), (INDUSTRY, industry)):
            members = groups.get((level, name)) if name else None
            if not members or len(members) < _MIN_PEERS:
                continue
            rank = 1 + sum(1 for _, other in members if other > quality)  # ties share the better rank
            top = rank / len(members) * 100
            out[sid] = {"rank": rank, "of": len(members), "top_pct": round(top, 1), "label": label(top), "group": name, "level": level}
            break
    return out
