"""Sector-relative quality (framework section 11): where a stock's Quality
Score ranks among same-sector stocks — "Pharma stock A: 58, rank #3 of 30"
can be the stronger holding than "IT stock B: 65, rank #15 of 25".

Computed when read, from every stock's latest Quality, so a rank always
reflects the whole sector as scored now. Sector is the NSE sector label on
the stocks table.
"""
from __future__ import annotations

_MIN_PEERS = 5


def label(top_pct: float) -> str:
    return ("Top 10%" if top_pct <= 10 else "Top 25%" if top_pct <= 25 else "Top 40%" if top_pct <= 40
            else "Top 50%" if top_pct <= 50 else "Bottom 50%")


def ranks(rows: list[tuple[str, str | None, float | None]]) -> dict[str, dict]:
    """rows: (stock_id, sector, quality). Returns {stock_id: {rank, of, top_pct, label, sector}}
    for stocks with a Quality in a sector of at least five scored stocks."""
    by_sector: dict[str, list[tuple[str, float]]] = {}
    for sid, sector, quality in rows:
        if sector and quality is not None:
            by_sector.setdefault(sector, []).append((sid, quality))
    out = {}
    for sector, members in by_sector.items():
        if len(members) < _MIN_PEERS:
            continue
        members.sort(key=lambda m: -m[1])
        n = len(members)
        for i, (sid, q) in enumerate(members):
            rank = 1 + sum(1 for _, other in members if other > q)  # ties share the better rank
            top = rank / n * 100
            out[sid] = {"rank": rank, "of": n, "top_pct": round(top, 1), "label": label(top), "sector": sector}
    return out
