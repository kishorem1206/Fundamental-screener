"""Price store — daily history for every stock and every NSE index.

Where each number comes from:

  * Indices (`index_bars_daily`): NSE's own daily index file, one file per
    trading day covering every Nifty index, with the index's P/E, P/B and
    dividend yield. `app/prices/nse_indices.py`.
  * Stocks (`price_bars_daily`): Yahoo Finance daily history, because returns
    need prices adjusted for splits, bonuses and dividends and the exchange
    publishes only raw prices. `app/prices/yahoo.py`.
  * Check: NSE's daily bhavcopy (the official close of every listed security)
    is compared with the stored close for the same day.
    `app/prices/nse_bhavcopy.py`.

Run:  cd backend && .venv/bin/python -m app.prices.runner            # daily update
      cd backend && .venv/bin/python -m app.prices.runner --years 3  # first fill
"""
