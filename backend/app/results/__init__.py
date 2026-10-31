"""Results calendar: re-read a stock the day after its results, not the whole market.

NSE's event calendar says when each board meets to consider results. The day
after, that stock's Screener pages are read and it is re-scored. Screener can
take a few days to show a new quarter, so a stock stays pending until it does.
Run daily by the scheduled job: `python -m app.results.runner`.
"""
