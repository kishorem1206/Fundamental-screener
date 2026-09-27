"""
Before adding sector-specific annual-report or quarterly-report note
extraction for this sector, check the two dedicated extraction engines'
Area Registries first — app/ingestion/annual_report_ingestion.py and
app/ingestion/quarterly_results_client.py (see also "Important md
files/Annual_Report_Fetching_Extraction_Engine.md" and
".../Quarterly_Report_Fetching_Extraction_Engine.md") — an existing
area may already cover what this sector needs.

Consumer Durables sector framework.
White goods, appliances, electronics, air conditioners, refrigerators, washing machines.
Covers both branded players (Voltas, Havells, Whirlpool) and component-linked businesses.

`volume_growth_yoy` and `market_share` below (both
available_from_yfinance=False) are now filled by the Quarterly Sector KPI
Extraction Engine (`app/ingestion/quarterly_operating_metrics_ingestion.py`,
"consumer_durables" area, added 2026-09-20) — sourced from NSE quarterly
Investor Presentation filings, stored as `qtr_volume_growth_yoy`/
`qtr_consumer_durables_market_share`. Confirmed exact live on Voltas' real
Q1 FY27 filing (a narrative MD&A earnings note, not a slide deck): "RAC
volumes grew 45% year on year" / "achieved a 17.3% secondary market share"
for the primary Room Air Conditioner segment. Blue Star's real Q1 FY27
deck was checked as a second company and has no comparable numeric
disclosure (only qualitative segment commentary) — a genuine per-company
miss, same pattern as every other sector's occasional non-disclosing
company, not a bug. Havells/V-Guard/Whirlpool also had no matching
"rac volumes"/"secondary market share" phrasing in their latest filings;
Crompton's deck is a much larger (142-page) investor-day-style strategy
presentation reporting market share as basis-point CHANGES rather than
absolute %, in a bar/infographic layout resembling the rejected Ambuja
Cement bar-chart page — not targeted, to avoid the same scrambled-text
extraction risk found and fixed there.
"""
from __future__ import annotations
from app.sectors.base import SectorFramework, SectorMetric, SectorRedFlag


class ConsumerDurablesSector(SectorFramework):
    sector_name = "Consumer Durables"
    # "Electrical Equipment"/"Electricals" (bare) deliberately excluded —
    # real bug found live 2026-09-16: NSE uses "Electrical Equipment" as an
    # industry-level label for BOTH consumer-facing goods AND heavy
    # industrial equipment (transformers, generators — e.g. GE Vernova T&D,
    # basic_industry="Heavy Electrical Equipment", sector="Capital Goods").
    # The bare alias matched both, silently routing real capital-goods
    # companies into Consumer Durables. Every genuine consumer-durables
    # company already resolves via "Consumer Durables"/"Consumer
    # Electronics"/"Appliances"/"White Goods" (an exact sector-level match
    # in every case checked against the live DB) — removing the ambiguous
    # aliases loses no real coverage, and lets "Electrical Equipment"
    # correctly fall through to sector="Capital Goods" instead.
    sector_aliases = [
        "Consumer Durables", "Consumer Electronics", "Appliances",
        "White Goods",
    ]

    SECTOR_WEIGHTS = {
        "growth": 0.25,
        "profitability": 0.23,
        "cash_flow": 0.17,
        "balance_sheet": 0.15,
        "efficiency": 0.14,
        "valuation": 0.06,
    }

    def key_metrics(self) -> list[SectorMetric]:
        return [
            SectorMetric(
                "revenue_cagr_3y", "Revenue CAGR (3Y)", 0.12, "high",
                "higher_is_better", "%",
                "Revenue growth — premium consumer durables should grow 12-18% in a strong cycle",
                thresholds=[(0, 15), (3, 28), (6, 48), (10, 65), (14, 80), (18, 92), (22, 100)],
            ),
            SectorMetric(
                "pat_cagr_3y", "PAT CAGR (3Y)", 0.08, "high",
                "higher_is_better", "%",
                "Earnings growth — operating leverage benefits when scale rises",
                thresholds=[(0, 10), (5, 30), (10, 55), (15, 72), (20, 88), (25, 100)],
            ),
            SectorMetric(
                "volume_growth_yoy", "Volume Growth (YoY)", 0.10, "high",
                "higher_is_better", "%",
                "Unit volume growth — separates real demand from price-driven revenue growth",
                thresholds=[(-5, 0), (0, 22), (3, 42), (6, 62), (10, 78), (15, 90), (20, 100)],
                available_from_yfinance=False,
                na_message="Volume data from company disclosures / industry reports (CEAMA)",
            ),
            SectorMetric(
                "market_share", "Market Share (%)", 0.08, "medium",
                "higher_is_better", "%",
                "Category-level market share — brands with >20% share have pricing power",
                thresholds=[(2, 15), (5, 30), (10, 50), (20, 68), (30, 82), (40, 93), (55, 100)],
                available_from_yfinance=False,
                na_message="Market share from industry reports (GfK, NielsenIQ)",
            ),
            SectorMetric(
                "ebitda_margin", "EBITDA Margin", 0.14, "high",
                "higher_is_better", "%",
                "EBITDA margin — 8-14% for assembly-heavy; 14-20% for branded/IP-driven",
                thresholds=[(0, 5), (5, 22), (8, 42), (10, 60), (12, 75), (15, 87), (20, 100)],
            ),
            SectorMetric(
                "pat_margin", "PAT Margin", 0.08, "medium",
                "higher_is_better", "%",
                "Net margin — 5-10% typical; premium brands 10-15%",
                thresholds=[(0, 5), (2, 22), (4, 42), (6, 60), (8, 75), (10, 87), (14, 100)],
            ),
            SectorMetric(
                "roce", "ROCE", 0.10, "high",
                "higher_is_better", "%",
                "Capital returns — asset-light distribution model should generate 20-30%+ ROCE",
                thresholds=[(0, 5), (8, 22), (14, 45), (18, 62), (22, 78), (28, 90), (35, 100)],
            ),
            SectorMetric(
                "working_capital_days", "Working Capital Days", 0.08, "medium",
                "lower_is_better", "days",
                "Net working capital days — negative WC is ideal for strong FMCG-like brands",
                thresholds=[(-10, 100), (0, 90), (15, 78), (30, 62), (45, 45), (60, 25), (90, 0)],
            ),
            SectorMetric(
                "inventory_days", "Inventory Days", 0.08, "medium",
                "lower_is_better", "days",
                "Finished goods + WIP — seasonal products (ACs, fans) must manage pre-summer buildup",
                thresholds=[(10, 100), (20, 88), (30, 75), (45, 58), (60, 40), (80, 20), (110, 0)],
            ),
            SectorMetric(
                "debt_to_equity", "Debt/Equity", 0.08, "medium",
                "lower_is_better", "x",
                "Consumer durables should be conservatively financed — above 0.5x warrants watch",
                thresholds=[(0, 100), (0.2, 88), (0.4, 72), (0.6, 55), (0.8, 38), (1.2, 18), (2.0, 0)],
            ),
            SectorMetric(
                "fcf_to_pat", "FCF / PAT", 0.08, "medium",
                "higher_is_better", "%",
                "Cash conversion — durable brands should convert 60-80% to FCF",
                thresholds=[(0, 10), (20, 28), (40, 48), (60, 65), (75, 80), (90, 92), (110, 100)],
            ),
            SectorMetric(
                "pe_ratio", "P/E", 0.08, "medium",
                "neutral", "x",
                "Consumer durables P/E — premium brands 25-40x; commodity-like 12-20x",
                thresholds=[(0, 45), (10, 65), (18, 82), (28, 78), (38, 62), (55, 40), (80, 18)],
            ),
            SectorMetric(
                "ev_to_ebitda", "EV/EBITDA", 0.06, "low",
                "neutral", "x",
                "Enterprise multiple — 12-22x typical for quality durables brands",
                thresholds=[(0, 55), (8, 78), (12, 88), (18, 78), (24, 60), (32, 38), (45, 15)],
            ),
        ]

    def red_flag_rules(self) -> list[SectorRedFlag]:
        return [
            SectorRedFlag(
                condition="ebitda_margin < 8",
                severity="HIGH",
                title="Very Low EBITDA Margin",
                description="EBITDA below 8% signals RM cost pressure or inability to pass through costs to consumers.",
            ),
            SectorRedFlag(
                condition="volume_growth_yoy < 0",
                severity="HIGH",
                title="Volume Decline",
                description="Negative volume growth signals demand destruction or severe market share loss.",
            ),
            SectorRedFlag(
                condition="inventory_days > 75",
                severity="MEDIUM",
                title="High Inventory",
                description="Inventory above 75 days signals demand weakness or poor supply chain management — write-down risk.",
            ),
            SectorRedFlag(
                condition="roce < 14",
                severity="MEDIUM",
                title="Weak Capital Returns",
                description="ROCE below 14% for a durables company suggests poor asset utilization or margin pressure.",
            ),
            SectorRedFlag(
                condition="debt_to_equity > 0.8",
                severity="MEDIUM",
                title="Above-Norm Leverage",
                description="D/E above 0.8x is elevated for consumer durables — investigate if driven by seasonal inventory financing.",
            ),
            SectorRedFlag(
                condition="revenue_cagr_3y < 5",
                severity="HIGH",
                title="Slow Revenue Growth",
                description="Revenue CAGR below 5% for consumer durables suggests demand loss or market saturation.",
            ),
        ]

    def _check_rule(self, rule: SectorRedFlag, metrics: dict, data: dict) -> bool:
        cond = rule.condition
        if cond == "ebitda_margin < 8":
            v = metrics.get("ebitda_margin"); return v is not None and v < 8
        if cond == "volume_growth_yoy < 0":
            v = metrics.get("volume_growth_yoy"); return v is not None and v < 0
        if cond == "inventory_days > 75":
            v = metrics.get("inventory_days"); return v is not None and v > 75
        if cond == "roce < 14":
            v = metrics.get("roce"); return v is not None and v < 14
        if cond == "debt_to_equity > 0.8":
            v = metrics.get("debt_to_equity"); return v is not None and v > 0.8
        if cond == "revenue_cagr_3y < 5":
            v = metrics.get("revenue_cagr_3y"); return v is not None and v < 5
        return False
