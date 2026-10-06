"""Portfolio — framework sections 12 (comparison with what is owned), 13
(position sizing in portfolio context) and 14 (asset allocation).

Holdings come from Zerodha Kite through Kite's own MCP server (read-only:
`kite_link.py`), from a holdings CSV (Dhan, Zerodha console, or any broker
with symbol/ISIN, quantity and price columns), or are entered by hand (gold,
debt, cash, international, property — anything not in a broker account).
"""
