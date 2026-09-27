"""
Before adding sector-specific annual-report or quarterly-report note
extraction for this sector, check the two dedicated extraction engines'
Area Registries first — app/ingestion/annual_report_ingestion.py and
app/ingestion/quarterly_results_client.py (see also "Important md
files/Annual_Report_Fetching_Extraction_Engine.md" and
".../Quarterly_Report_Fetching_Extraction_Engine.md") — an existing
area may already cover what this sector needs.

Diversified sector framework — Diversified_Diversified_Analysis.md.
Conglomerates and holding companies spanning multiple, often unrelated,
businesses (Bajaj Finserv, Bajaj Holdings, Godrej Industries, 3M India,
DCM Shriram, Balmer Lawrie, Rane Holdings, ...).

Built 2026-09-20 — previously every diversified/holding company fell
through to GenericSector, since `classification_map.py` mapped
`'diversified'`/`'holding company'` straight to `'Generic'` with no
dedicated framework (an undocumented gap, unlike Textiles' — that one had
an explicit "coming later" note in this file's own docstring; this one
didn't, but is the same class of gap).

IMPORTANT SCOPE NOTE: the MD spec's primary analytical framework for this
sector is genuinely different in kind from every other sector built this
session — it calls for SEGMENT-LEVEL decomposition (revenue/EBIT/ROIC per
business line, from Ind AS 108 segment-reporting notes), Sum-of-the-Parts
(SOTP) valuation built up business-by-business, and historical capital-
allocation/acquisition-return tracking. That is a genuinely different
calculation architecture from the single `SectorMetric` threshold-curve
scoring every other sector framework uses (it would need something closer
to a dedicated package like `app/calculations/balance_sheet_intelligence/`
or `quarterly_intelligence/` — a segment-aware data model, not a flat
metrics dict) and is NOT attempted here. This framework instead scores
what IS computable today from consolidated financials (the same generic
ratios every sector already gets) plus three genuinely NA
portfolio-level signals sourced from segment-reporting notes
(`sotp_discount_pct`, `corporate_overhead_pct`,
`segment_revenue_concentration_pct`) — a real but partial proxy for the
MD spec's Portfolio Quality / Capital Allocation / Valuation dimensions,
not the full segment-by-segment SOTP engine the spec describes. Building
that properly is a separate, much larger feature, not a same-pass addition.
"""
from __future__ import annotations
from app.sectors.base import SectorFramework, SectorMetric, SectorRedFlag


class DiversifiedSector(SectorFramework):
    sector_name = "Diversified"
    sector_aliases = [
        "Diversified", "Holding Company", "Conglomerate", "Investment Company",
    ]

    SECTOR_WEIGHTS = {
        "growth": 0.21,
        "profitability": 0.23,
        "cash_flow": 0.18,
        "balance_sheet": 0.18,
        "efficiency": 0.13,
        "valuation": 0.07,
    }

    def key_metrics(self) -> list[SectorMetric]:
        return [
            SectorMetric(
                "revenue_cagr_3y", "Revenue CAGR (3Y)", 0.10, "high",
                "higher_is_better", "%",
                "Consolidated revenue growth — blends every segment; check segment mix before crediting one business",
                thresholds=[(0, 15), (5, 32), (10, 52), (15, 68), (20, 82), (25, 92), (30, 100)],
            ),
            SectorMetric(
                "ebitda_margin", "EBITDA Margin", 0.12, "high",
                "higher_is_better", "%",
                "Consolidated EBITDA margin — a blended figure that can hide a strong segment subsidizing a weak one",
                thresholds=[(5, 10), (10, 28), (15, 45), (20, 62), (26, 78), (32, 90), (40, 100)],
            ),
            SectorMetric(
                "roce", "ROCE", 0.12, "high",
                "higher_is_better", "%",
                "Consolidated capital efficiency across the whole portfolio",
                thresholds=[(0, 5), (8, 22), (12, 42), (16, 60), (20, 76), (26, 88), (34, 100)],
            ),
            SectorMetric(
                "roic", "ROIC", 0.10, "high",
                "higher_is_better", "%",
                "Return on invested capital — should exceed the group's cost of capital across the portfolio",
                thresholds=[(0, 5), (8, 22), (12, 42), (16, 60), (20, 76), (26, 88), (34, 100)],
            ),
            SectorMetric(
                "debt_to_equity", "Debt/Equity", 0.08, "medium",
                "lower_is_better", "x",
                "Consolidated leverage — can mask debt concentrated in one weak subsidiary; check standalone too",
                thresholds=[(0, 100), (0.3, 85), (0.6, 68), (1.0, 50), (1.5, 30), (2.2, 10), (3.0, 0)],
            ),
            SectorMetric(
                "net_debt_to_ebitda", "Net Debt / EBITDA", 0.08, "medium",
                "lower_is_better", "x",
                "Leverage relative to earnings power — a conglomerate-wide blended figure",
                thresholds=[(0, 100), (0.5, 88), (1.0, 72), (1.5, 55), (2.5, 35), (3.5, 15), (5.0, 0)],
            ),
            SectorMetric(
                "fcf_to_pat", "FCF / PAT", 0.10, "high",
                "higher_is_better", "%",
                "Cash conversion — capital-hungry segments can absorb group cash even as consolidated PAT looks healthy",
                thresholds=[(0, 10), (20, 28), (40, 48), (60, 65), (75, 80), (90, 92), (110, 100)],
            ),
            SectorMetric(
                "pe_ratio", "P/E", 0.06, "low",
                "neutral", "x",
                "Consolidated P/E is a poor primary valuation tool for a conglomerate — SOTP is preferred where segment data supports it",
                thresholds=[(0, 50), (10, 68), (16, 85), (24, 80), (35, 60), (50, 38), (75, 15)],
            ),
            SectorMetric(
                "sotp_discount_pct", "SOTP Discount (%)", 0.08, "medium",
                "lower_is_better", "%",
                "Market cap's discount to an estimated sum-of-the-parts value — the spec explicitly warns not to "
                "assume a universal holding discount is unjustified; a large one may reflect governance, "
                "complexity or liquidity concerns rather than pure mispricing",
                thresholds=[(0, 100), (15, 80), (30, 60), (45, 40), (60, 20), (80, 5)],
                available_from_yfinance=False,
                na_message="Requires a segment-level SOTP estimate — not sourced from any structured feed today",
            ),
            SectorMetric(
                "corporate_overhead_pct", "Corporate Overhead / Revenue", 0.08, "medium",
                "lower_is_better", "%",
                "Unallocated corporate/holding-company costs as % of consolidated revenue — should be justified by portfolio scale",
                thresholds=[(0.5, 100), (1, 85), (2, 65), (3, 45), (5, 25), (8, 10), (12, 0)],
                available_from_yfinance=False,
                na_message="Corporate overhead from segment-reporting notes in the annual report",
            ),
            SectorMetric(
                "segment_revenue_concentration_pct", "Largest Segment Revenue Share", 0.08, "low",
                "lower_is_better", "%",
                "Largest single segment's share of consolidated revenue — high concentration means the "
                "'diversified' classification isn't delivering much actual risk diversification",
                thresholds=[(30, 100), (45, 80), (60, 60), (75, 40), (85, 20), (95, 5)],
                available_from_yfinance=False,
                na_message="Segment revenue mix from segment-reporting notes in the annual report",
            ),
        ]

    def red_flag_rules(self) -> list[SectorRedFlag]:
        return [
            SectorRedFlag(
                condition="sotp_discount_pct > 50",
                severity="HIGH",
                title="Large SOTP Discount",
                description="Market cap trades at a large discount to estimated sum-of-the-parts value — investigate whether this reflects governance, complexity or liquidity concerns rather than pure mispricing.",
            ),
            SectorRedFlag(
                condition="corporate_overhead_pct > 6",
                severity="MEDIUM",
                title="High Corporate Overhead",
                description="Unallocated corporate/holding-company costs above 6% of consolidated revenue — check whether portfolio scale justifies this overhead.",
            ),
            SectorRedFlag(
                condition="roce < 8",
                severity="MEDIUM",
                title="Weak Consolidated Capital Returns",
                description="Consolidated ROCE below 8% suggests capital is trapped in low-return segments — check the segment mix before assuming a portfolio-wide problem.",
            ),
            SectorRedFlag(
                condition="debt_to_equity > 1.5",
                severity="HIGH",
                title="Elevated Consolidated Leverage",
                description="D/E above 1.5x at the consolidated level — a parent can look healthy while debt is concentrated in one weak subsidiary, so check standalone and segment-level debt too.",
            ),
            SectorRedFlag(
                condition="segment_revenue_concentration_pct > 85",
                severity="MEDIUM",
                title="High Segment Concentration",
                description="Over 85% of revenue from a single segment despite a 'Diversified' classification — the portfolio isn't delivering much real risk diversification.",
            ),
            SectorRedFlag(
                condition="fcf_to_pat < 30",
                severity="MEDIUM",
                title="Weak Cash Conversion",
                description="FCF/PAT below 30% — capital-hungry segments may be absorbing group cash even as consolidated PAT looks healthy.",
            ),
        ]

    def _check_rule(self, rule: SectorRedFlag, metrics: dict, data: dict) -> bool:
        cond = rule.condition
        if cond == "sotp_discount_pct > 50":
            v = metrics.get("sotp_discount_pct"); return v is not None and v > 50
        if cond == "corporate_overhead_pct > 6":
            v = metrics.get("corporate_overhead_pct"); return v is not None and v > 6
        if cond == "roce < 8":
            v = metrics.get("roce"); return v is not None and v < 8
        if cond == "debt_to_equity > 1.5":
            v = metrics.get("debt_to_equity"); return v is not None and v > 1.5
        if cond == "segment_revenue_concentration_pct > 85":
            v = metrics.get("segment_revenue_concentration_pct"); return v is not None and v > 85
        if cond == "fcf_to_pat < 30":
            v = metrics.get("fcf_to_pat"); return v is not None and v < 30
        return False
