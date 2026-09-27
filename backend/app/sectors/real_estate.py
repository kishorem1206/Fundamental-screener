"""
Before adding sector-specific annual-report or quarterly-report note
extraction for this sector, check the two dedicated extraction engines'
Area Registries first — app/ingestion/annual_report_ingestion.py and
app/ingestion/quarterly_results_client.py (see also "Important md
files/Annual_Report_Fetching_Extraction_Engine.md" and
".../Quarterly_Report_Fetching_Extraction_Engine.md") — an existing
area may already cover what this sector needs.

Real Estate sector framework.
Residential developers, commercial developers, REITs, office/retail parks.
Pre-sales (bookings), collections, inventory, launch pipeline are key.

`pre_sales_value` and `collections_growth_yoy` below (both
available_from_yfinance=False) are now filled by the Quarterly Sector KPI
Extraction Engine (`app/ingestion/quarterly_operating_metrics_ingestion.py`,
"realty" area, added 2026-09-20) — sourced from NSE quarterly Investor
Presentation filings, stored as `qtr_realty_pre_sales_value`/
`qtr_realty_collections_growth_yoy`. Confirmed exact live on Godrej
Properties' real Q1 FY27 deck (a clean row-based "Sales highlights"
table): Booking Value 8,651 Cr, Customer Collections 4,348 Cr (vs 3,670
Cr Q1 FY26), matching the table's own stated YoY%. `launch_pipeline_msf`
and `unsold_inventory_months` are NOT addressed — the former was tried
and dropped after a real, caught fabrication (the primary model invented
a launches figure that appears nowhere in the source text, confirmed by
direct string search — see the ingestion module's docstring); the latter
was never disclosed as a single figure in any real candidate deck checked
(Godrej, Prestige), consistent with this metric's own na_message pointing
to third-party data (PropEquity) instead.
"""
from __future__ import annotations
from app.sectors.base import SectorFramework, SectorMetric, SectorRedFlag


class RealEstateSector(SectorFramework):
    sector_name = "Real Estate"
    sector_aliases = [
        "Real Estate", "Realty", "Housing", "Residential Developers",
        "Commercial Real Estate", "REITs", "Office Parks",
    ]

    SECTOR_WEIGHTS = {
        "growth": 0.24,
        "profitability": 0.19,
        "cash_flow": 0.22,
        "balance_sheet": 0.25,
        "efficiency": 0.07,
        "valuation": 0.03,
    }

    def key_metrics(self) -> list[SectorMetric]:
        return [
            SectorMetric(
                "pre_sales_value", "Pre-Sales / Bookings (INR Cr)", 0.14, "high",
                "higher_is_better", "INR Cr",
                "Annual bookings (value) — forward revenue indicator for residential developers",
                thresholds=[(500, 15), (1500, 32), (3000, 52), (5000, 68), (8000, 82), (12000, 93), (18000, 100)],
                available_from_yfinance=False,
                na_message="Pre-sales data from company quarterly disclosures; not in yfinance",
            ),
            SectorMetric(
                "collections_growth_yoy", "Collections Growth (YoY)", 0.12, "high",
                "higher_is_better", "%",
                "Customer payment collections — determines actual cash inflow vs booking recognition",
                thresholds=[(-5, 5), (0, 22), (5, 42), (10, 62), (15, 78), (20, 90), (25, 100)],
                available_from_yfinance=False,
                na_message="Collections data from company disclosures; not in yfinance",
            ),
            SectorMetric(
                "unsold_inventory_months", "Unsold Inventory (Months)", 0.12, "high",
                "lower_is_better", "months",
                "Months of unsold inventory at current sales pace — below 18 months is healthy",
                thresholds=[(6, 100), (12, 85), (18, 68), (24, 50), (36, 30), (48, 10)],
                available_from_yfinance=False,
                na_message="Unsold inventory data from company reports / PropEquity data",
            ),
            SectorMetric(
                "launch_pipeline_msf", "Launch Pipeline (MSF)", 0.10, "high",
                "higher_is_better", "MSF",
                "Million sq.ft of planned launches — visibility on future pre-sales",
                thresholds=[(1, 15), (3, 32), (6, 52), (10, 68), (15, 82), (22, 93), (30, 100)],
                available_from_yfinance=False,
                na_message="Launch pipeline from company guidance in investor presentations",
            ),
            SectorMetric(
                "ebitda_margin", "EBITDA Margin", 0.10, "high",
                "higher_is_better", "%",
                "Developer EBITDA 20-35%; REIT/commercial 55-70%",
                thresholds=[(5, 5), (12, 22), (18, 42), (22, 60), (28, 78), (34, 92), (40, 100)],
            ),
            SectorMetric(
                "net_debt_to_equity", "Net Debt / Equity", 0.14, "high",
                "lower_is_better", "x",
                "Leverage — net debt/equity <1x is healthy for developers; negative = net cash",
                thresholds=[(-0.5, 100), (0, 90), (0.5, 78), (1.0, 60), (1.5, 40), (2.0, 20), (3.0, 0)],
            ),
            SectorMetric(
                "debt_to_equity", "Gross Debt/Equity", 0.10, "high",
                "lower_is_better", "x",
                "Gross leverage — developers with >2x gross D/E face project-level rollover risk",
                thresholds=[(0, 100), (0.5, 85), (1.0, 70), (1.5, 52), (2.0, 32), (2.5, 15), (3.5, 0)],
            ),
            SectorMetric(
                "ocf_to_ebitda", "Operating Cash Flow / EBITDA", 0.12, "high",
                "higher_is_better", "%",
                "Collection efficiency — should be 70-100%+ for healthy cash flow",
                thresholds=[(10, 10), (30, 28), (50, 48), (70, 65), (80, 80), (90, 92), (100, 100)],
            ),
            SectorMetric(
                "roce", "ROCE", 0.08, "medium",
                "higher_is_better", "%",
                "Capital returns — real estate ROCE 12-20%+ for quality developers",
                thresholds=[(0, 5), (5, 20), (10, 40), (14, 60), (18, 76), (24, 88), (30, 100)],
            ),
            SectorMetric(
                "revenue_cagr_3y", "Revenue CAGR (3Y)", 0.08, "medium",
                "higher_is_better", "%",
                "Revenue growth — real estate revenue lags bookings by 2-3 years (completion basis)",
                thresholds=[(0, 15), (5, 32), (10, 52), (15, 68), (20, 82), (25, 92), (30, 100)],
            ),
        ]

    def red_flag_rules(self) -> list[SectorRedFlag]:
        return [
            SectorRedFlag(
                condition="net_debt_to_equity > 2",
                severity="HIGH",
                title="Very High Net Leverage",
                description="Net Debt/Equity above 2x for a developer — RERA, delivery delays and cost overruns create liquidity risk.",
            ),
            SectorRedFlag(
                condition="unsold_inventory_months > 36",
                severity="HIGH",
                title="Excessive Unsold Inventory",
                description="Inventory above 3 years at current sales pace signals demand weakness and capital locked in unsold units.",
            ),
            SectorRedFlag(
                condition="collections_growth_yoy < 0",
                severity="HIGH",
                title="Declining Collections",
                description="Negative collection growth means cash inflow from past bookings is deteriorating — working capital stress.",
            ),
            SectorRedFlag(
                condition="ebitda_margin < 15",
                severity="MEDIUM",
                title="Low EBITDA Margin",
                description="EBITDA below 15% for a developer signals cost overruns or low realization on launched inventory.",
            ),
            SectorRedFlag(
                condition="ocf_to_ebitda < 50",
                severity="MEDIUM",
                title="Low Collection Efficiency",
                description="Operating cash below 50% of EBITDA indicates bookings not converting to collections — risk of receivable buildup.",
            ),
            SectorRedFlag(
                condition="pre_sales_value < 1000",
                severity="MEDIUM",
                title="Very Low Booking Volume",
                description="Annual pre-sales below ₹1000 Cr indicates very small scale or demand weakness in the markets served.",
            ),
        ]

    def _check_rule(self, rule: SectorRedFlag, metrics: dict, data: dict) -> bool:
        cond = rule.condition
        if cond == "net_debt_to_equity > 2":
            v = metrics.get("net_debt_to_equity"); return v is not None and v > 2
        if cond == "unsold_inventory_months > 36":
            v = metrics.get("unsold_inventory_months"); return v is not None and v > 36
        if cond == "collections_growth_yoy < 0":
            v = metrics.get("collections_growth_yoy"); return v is not None and v < 0
        if cond == "ebitda_margin < 15":
            v = metrics.get("ebitda_margin"); return v is not None and v < 15
        if cond == "ocf_to_ebitda < 50":
            v = metrics.get("ocf_to_ebitda"); return v is not None and v < 50
        if cond == "pre_sales_value < 1000":
            v = metrics.get("pre_sales_value"); return v is not None and v < 1000
        return False
