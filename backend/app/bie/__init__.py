"""Business Intelligence Engine — a deep company-understanding layer beside
the quantitative screener (spec: `Important md files/Deep business
analysis.md`; target output: the ITC initiation report in the repo root).

Phase 1 (this package today) is document intelligence: fetch each company's
primary filings from NSE, archive them, extract facts deterministically (no
LLM), and store every fact with the document, direct URL and locator it came
from. Later phases add the universal business model, sector intelligence,
forecasting/valuation and the editorial narrative.

Rules that hold across phases:
  * a fact is written only through `evidence.record_fact`, which refuses one
    without a usable source;
  * what a company reported, what it claims, what management guides to and
    what this app assumes are different `nature`s and never merged;
  * arithmetic is done in Python and stored as CALCULATED facts that name
    their inputs — an LLM never produces a number.
"""
