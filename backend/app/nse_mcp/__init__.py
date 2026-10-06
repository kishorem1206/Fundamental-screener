"""NSE's own MCP servers (https://www.nseindia.com/nse-mcp), used as an
official data source by this backend:

  bhavcopy   https://mcp.nseindia.in/bhavcopy/cm/mcp — daily OHLCV for every
             NSE security (five years, unadjusted, including SME listings),
             corporate actions with exact ex-dates and adjustment factors,
             market breadth, latest quotes
  market     https://mcp.nseindia.in/cmmkt/mcp — live quotes (one-minute
             refresh in market hours), gainers and losers

What this app uses them for:
  * corporate actions (`corporate_actions.py`): official splits, bonuses and
    dividends for the Fundamental Score's share-dilution and dividend inputs
  * price history for stocks Yahoo does not carry (`history.py`), adjusted
    here with NSE's own factors
  * live price on the Combined Score and Portfolio pages; market breadth

    cd backend && .venv/bin/python -m app.nse_mcp.runner --actions       # corporate actions, every stock
    cd backend && .venv/bin/python -m app.nse_mcp.runner --fill-prices   # history for stocks with none stored
"""
