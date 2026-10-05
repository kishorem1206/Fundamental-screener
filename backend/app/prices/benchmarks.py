"""Which index a stock is measured against.

Market: Nifty 50 (headline) and Nifty 500 (broad).

Sector: the official NSE sector index where one exists for the stock's sector
or industry. NSE publishes no index for several of the sector labels on the
`stocks` table (capital goods, textiles, services …); those get no official
benchmark here, and the relative-strength engine compares them with the other
stocks carrying the same sector label instead. `kind` says which case applies
so a report never presents a stand-in as an official sector index:

    official   the NSE index for exactly this sector
    closest    an NSE index that covers this sector together with others
    peers      no NSE index: compare with same-sector stocks
"""
from __future__ import annotations

MARKET = "Nifty 50"
BROAD_MARKET = "Nifty 500"

# industry is checked first, then sector
_BY_INDUSTRY = {
    "Banks": ("Nifty Bank", "official"),
    "Pharmaceuticals & Biotechnology": ("Nifty Pharma", "official"),
    "Capital Markets": ("Nifty Capital Markets", "official"),
    "Transport Services": ("Nifty Transportation & Logistics", "closest"),
    "Transport Infrastructure": ("Nifty Transportation & Logistics", "closest"),
}

_BY_SECTOR = {
    "Financial Services": ("Nifty Financial Services", "official"),
    "Healthcare": ("Nifty Healthcare Index", "official"),
    "Chemicals": ("Nifty Chemicals", "official"),
    "Fast Moving Consumer Goods": ("Nifty FMCG", "official"),
    "Consumer Durables": ("Nifty Consumer Durables", "official"),
    "Information Technology": ("Nifty IT", "official"),
    "Automobile and Auto Components": ("Nifty Auto", "official"),
    "Realty": ("Nifty Realty", "official"),
    "Metals & Mining": ("Nifty Metal", "official"),
    "Media, Entertainment & Publication": ("Nifty Media", "official"),
    "Oil, Gas & Consumable Fuels": ("Nifty Oil & Gas", "official"),
    "Power": ("Nifty Energy", "closest"),
    "Construction": ("Nifty Infrastructure", "closest"),
    "Capital Goods": ("Nifty India Manufacturing", "closest"),
    "Consumer Services": ("Nifty India Consumption", "closest"),
}


def sector_benchmark(sector: str | None, industry: str | None = None) -> dict:
    name, kind = _BY_INDUSTRY.get(industry or "") or _BY_SECTOR.get(sector or "") or (None, "peers")
    return {"index": name, "kind": kind, "sector": sector}


def all_index_names() -> set[str]:
    return {MARKET, BROAD_MARKET} | {n for n, _ in _BY_INDUSTRY.values()} | {n for n, _ in _BY_SECTOR.values()}
