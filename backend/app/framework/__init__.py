"""Stock Quality & Portfolio Replacement framework.

Implements `Important md files/stock_quality_portfolio_replacement_agent_framework.md`.
The framework's scores are the headline; the app's older six category scores
(app/calculations/scoring.py) are inputs to them, never replaced.

Each score answers one question and is stored separately — they are never
averaged into one number (framework section 1):

    fundamental.py   Fundamental Score — are the financial numbers strong?  (section 4)
    trend.py         business trend label, not price                        (section 9)
    inputs.py        the measures section 4 lists that the older scores lacked
    store.py         one row per stock per day in `fw_scores`
"""
