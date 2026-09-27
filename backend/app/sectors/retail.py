"""
Before adding sector-specific annual-report or quarterly-report note
extraction for this sector, check the two dedicated extraction engines'
Area Registries first — app/ingestion/annual_report_ingestion.py and
app/ingestion/quarterly_results_client.py (see also "Important md
files/Annual_Report_Fetching_Extraction_Engine.md" and
".../Quarterly_Report_Fetching_Extraction_Engine.md") — an existing
area may already cover what this sector needs.

Retail sector framework.
Organized retail, e-commerce, specialty stores, fashion, food retail.
Same-store sales growth, store count, inventory turns are key.

`store_count_growth`, `revenue_per_sqft` and (partially) `sssg` below
(all available_from_yfinance=False) are now addressed by the Quarterly
Sector KPI Extraction Engine (`app/ingestion/quarterly_operating_metrics_
ingestion.py`, "retail" area, added 2026-09-20) — sourced from NSE
quarterly Investor Presentation filings. Trent's real Q1 FY27 deck is the
only candidate checked so far: a clean company-wide "AT A GLANCE" snapshot
gives store count/retail area/revenue directly (`qtr_retail_store_count`,
`qtr_retail_revenue_per_sqft`) — confirmed exact live with the primary
model (store_count=1,312, retail_area=18,040,000 sq ft, revenue=5,666
Cr). An earlier attempt this session hit the Groq daily-quota fallback
guard and was correctly blocked — the fallback model had mislabeled
"City Presence" (330) as store count instead of the real 1,312, a real
observed error the guard exists to catch. SSSG is a genuine, documented
gap — Trent's own deck
discloses it only as vague qualitative text ("low single digits"), no
number, and the prompt is instructed to return null rather than guess one.
`store_count_growth_yoy` is derived from our own prior-year ledger value
(no same-deck YoY pair exists in this document), so it stays null until a
second year of quarterly ingestion accumulates.
"""
from __future__ import annotations
from app.sectors.base import SectorFramework, SectorMetric, SectorRedFlag


class RetailSector(SectorFramework):
    sector_name = "Retail"
    sector_aliases = [
        "Retail", "Organized Retail", "Specialty Retail", "Department Stores",
        "Supermarkets", "E-commerce", "Fashion Retail", "Food Retail",
    ]

    SECTOR_WEIGHTS = {
        "growth": 0.26,
        "profitability": 0.22,
        "cash_flow": 0.19,
        "balance_sheet": 0.16,
        "efficiency": 0.13,
        "valuation": 0.04,
    }

    def key_metrics(self) -> list[SectorMetric]:
        return [
            SectorMetric(
                "revenue_cagr_3y", "Revenue CAGR (3Y)", 0.12, "high",
                "higher_is_better", "%",
                "Revenue growth — blends SSG + new store additions",
                thresholds=[(0, 15), (5, 30), (10, 48), (15, 65), (20, 80), (25, 92), (30, 100)],
            ),
            SectorMetric(
                "sssg", "Same-Store Sales Growth (SSSG)", 0.14, "high",
                "higher_is_better", "%",
                "Like-for-like sales growth excluding new stores — quality of existing base",
                thresholds=[(-5, 0), (0, 20), (3, 42), (6, 62), (10, 78), (14, 90), (18, 100)],
                available_from_yfinance=False,
                na_message="SSSG disclosed quarterly by retailers; not in yfinance financial statements",
            ),
            SectorMetric(
                "store_count_growth", "Store Count Growth (YoY)", 0.10, "medium",
                "higher_is_better", "%",
                "Annual store additions — retail rollout pace; too fast can dilute quality",
                thresholds=[(0, 20), (3, 38), (7, 55), (12, 70), (18, 82), (25, 92), (35, 100)],
                available_from_yfinance=False,
                na_message="Store count from company disclosures",
            ),
            SectorMetric(
                "revenue_per_sqft", "Revenue per Sq. Ft. (INR)", 0.10, "high",
                "higher_is_better", "INR",
                "Sales productivity per unit of retail space — quality indicator",
                thresholds=[(3000, 15), (5000, 32), (7000, 52), (9000, 68), (12000, 82), (16000, 93), (20000, 100)],
                available_from_yfinance=False,
                na_message="Revenue per sq.ft from company disclosures (total area vs total revenue)",
            ),
            SectorMetric(
                "gross_margin", "Gross Margin", 0.12, "high",
                "higher_is_better", "%",
                "Gross margin — apparel 40-60%; grocery 15-25%; multi-brand varies widely",
                thresholds=[(8, 10), (15, 28), (22, 48), (30, 65), (38, 80), (45, 92), (55, 100)],
            ),
            SectorMetric(
                "ebitda_margin", "EBITDA Margin", 0.10, "high",
                "higher_is_better", "%",
                "EBITDA margin (post-Ind AS 116 lease adjustment preferred) — 8-15% is healthy",
                thresholds=[(0, 5), (4, 22), (6, 42), (8, 60), (10, 75), (14, 88), (18, 100)],
            ),
            SectorMetric(
                "inventory_days", "Inventory Days", 0.10, "medium",
                "lower_is_better", "days",
                "Inventory turns — 30-60 days for apparel; 15-30 for food/FMCG retail",
                thresholds=[(15, 100), (25, 88), (40, 72), (55, 55), (70, 38), (90, 18), (120, 0)],
            ),
            SectorMetric(
                "roce", "ROCE", 0.08, "high",
                "higher_is_better", "%",
                "Capital efficiency — lean balance sheet retailers generate 20-35%+ ROCE",
                thresholds=[(0, 5), (8, 22), (14, 42), (20, 62), (26, 78), (32, 90), (40, 100)],
            ),
            SectorMetric(
                "debt_to_equity", "Debt/Equity (ex-leases)", 0.08, "medium",
                "lower_is_better", "x",
                "Financial debt (excluding Ind AS 116 lease liabilities) — should be low for retail",
                thresholds=[(0, 100), (0.2, 88), (0.4, 72), (0.6, 55), (0.8, 38), (1.2, 18), (2.0, 0)],
            ),
            SectorMetric(
                "fcf_to_pat", "FCF / PAT", 0.08, "medium",
                "higher_is_better", "%",
                "Cash conversion — watch for heavy store expansion capex reducing FCF",
                thresholds=[(0, 10), (20, 28), (40, 48), (60, 65), (75, 80), (90, 92), (110, 100)],
            ),
            SectorMetric(
                "pe_ratio", "P/E", 0.06, "low",
                "neutral", "x",
                "Quality retail commands premium P/E — 30-60x for high-growth grocers/fashion",
                thresholds=[(0, 45), (12, 65), (20, 80), (30, 82), (45, 70), (65, 50), (90, 25)],
            ),
        ]

    def red_flag_rules(self) -> list[SectorRedFlag]:
        return [
            SectorRedFlag(
                condition="sssg < 0",
                severity="HIGH",
                title="Negative Same-Store Sales",
                description="Negative SSSG means existing stores are losing relevance — structural demand loss or poor merchandising.",
            ),
            SectorRedFlag(
                condition="inventory_days > 80",
                severity="HIGH",
                title="Very High Inventory Days",
                description="Inventory above 80 days in retail signals overstocking and potential markdown risk — cash flow impact.",
            ),
            SectorRedFlag(
                condition="ebitda_margin < 5",
                severity="HIGH",
                title="Very Low EBITDA Margin",
                description="EBITDA below 5% for a retailer leaves no room for interest, capex, or working capital — profitability at risk.",
            ),
            SectorRedFlag(
                condition="gross_margin < 18",
                severity="MEDIUM",
                title="Low Gross Margin",
                description="Gross margin below 18% for non-grocery retail suggests pricing power erosion or category mix issues.",
            ),
            SectorRedFlag(
                condition="revenue_cagr_3y < 8",
                severity="MEDIUM",
                title="Below-Par Revenue Growth",
                description="Revenue CAGR below 8% for an organized retailer suggests slow store rollout or weak SSG.",
            ),
            SectorRedFlag(
                condition="roce < 12",
                severity="MEDIUM",
                title="Low Capital Returns",
                description="ROCE below 12% in retail means store economics are not generating adequate returns.",
            ),
        ]

    def _check_rule(self, rule: SectorRedFlag, metrics: dict, data: dict) -> bool:
        cond = rule.condition
        if cond == "sssg < 0":
            v = metrics.get("sssg"); return v is not None and v < 0
        if cond == "inventory_days > 80":
            v = metrics.get("inventory_days"); return v is not None and v > 80
        if cond == "ebitda_margin < 5":
            v = metrics.get("ebitda_margin"); return v is not None and v < 5
        if cond == "gross_margin < 18":
            v = metrics.get("gross_margin"); return v is not None and v < 18
        if cond == "revenue_cagr_3y < 8":
            v = metrics.get("revenue_cagr_3y"); return v is not None and v < 8
        if cond == "roce < 12":
            v = metrics.get("roce"); return v is not None and v < 12
        return False
