"""Quick analysis — Yahoo Finance-only scoring for the whole stock universe.

A self-contained package that sits BESIDE the full 20-stage pipeline
(`app/pipeline/orchestrator.py`) and changes nothing in it. The full pipeline
takes minutes per company (Screener ingestion, LLM stages, PDF) and is
rate-limited; this path produces the same six category scores + overall from
Yahoo Finance data alone, in seconds per company, so every stock can be
screened and the interesting ones sent through the full pipeline afterwards.

How it stays faithful to the full pipeline
------------------------------------------
* Reuses the SAME code, imported not copied: `compute_metrics()` (engine.py),
  `get_framework()` (sector routing), `compute_scores()` (scoring.py, incl. the
  bank / NBFC-insurance / fintech scorers and the per-sector weight tables).
  Any score difference therefore comes from INPUTS, never from formula drift.
* Yahoo's Indian statements are CONSOLIDATED (verified 2026-09-24 against the
  Screener ledger for 18 analysed companies — Yahoo matches consolidated, not
  standalone, wherever the two differ, e.g. Tanla 5.9x). Nothing here reads
  standalone figures.

What the quick path cannot see (see fidelity.py for measured impact)
--------------------------------------------------------------------
1. Screener-primary metric overrides (screener_metrics_override.py) — the full
   pipeline replaces several Yahoo-derived metrics with Screener's.
2. Score refinement (score_refinement.py) — bounded +/-10 point nudges to
   profitability / balance sheet / cash flow from the P&L, balance-sheet and
   cash-flow intelligence engines, which need the Screener ledger.
3. Sector `key_metrics` frameworks feed `sector_analysis.sector_score`, which
   is displayed separately and is NOT part of the six scores — so sector
   coverage for scoring is exactly the routing done by `get_framework()`.

Run:  cd backend && .venv/bin/python -m app.quick_analysis.fidelity
"""
