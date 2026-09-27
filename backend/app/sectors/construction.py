"""
Before adding sector-specific annual-report or quarterly-report note
extraction for this sector, check the two dedicated extraction engines'
Area Registries first — app/ingestion/annual_report_ingestion.py and
app/ingestion/quarterly_results_client.py (see also "Important md
files/Annual_Report_Fetching_Extraction_Engine.md" and
".../Quarterly_Report_Fetching_Extraction_Engine.md") — an existing
area may already cover what this sector needs.

Construction & Infrastructure sector framework.

Order-book metrics are filled from the Quarterly Sector KPI Extraction Engine
(`qtr_capgoods_*`, shared with Capital Goods — see capital_goods.py). EPC-specific
traps: backlog that adds L1 positions (KEC), inflows "YTD as of results date" that run past
quarter end (KPIL, KEC), backlog including multi-decade mine-developer contracts (DBL, Power
Mech), and standalone vs consolidated books. Billing/collection and retention analysis
(spec sections 8-9) stays annual-report/Screener based.
EPC contractors, road builders, bridge constructors, water/irrigation projects.
InfrastructureSector inherits this — adds concession/BOT revenue layer.
"""
from __future__ import annotations
from app.sectors.base import SectorFramework, SectorMetric, SectorRedFlag


class ConstructionSector(SectorFramework):
    sector_name = "Construction"
    sector_aliases = [
        "Construction", "EPC", "Engineering & Construction",
        "Engineering, Procurement & Construction",
    ]

    SECTOR_WEIGHTS = {
        "growth": 0.24,
        "profitability": 0.20,
        "cash_flow": 0.20,
        "balance_sheet": 0.22,
        "efficiency": 0.10,
        "valuation": 0.04,
    }

    def key_metrics(self) -> list[SectorMetric]:
        return [
            SectorMetric(
                "revenue_cagr_3y", "Revenue CAGR (3Y)", 0.10, "high",
                "higher_is_better", "%",
                "Revenue growth — execution of existing order book drives revenue",
                thresholds=[(0, 15), (5, 30), (10, 48), (15, 65), (20, 80), (25, 92), (30, 100)],
            ),
            SectorMetric(
                "order_book_to_revenue", "Order Book / Revenue", 0.14, "high",
                "higher_is_better", "x",
                "Order book cover — 3-4x revenue provides ~2.5-3 years of visibility",
                thresholds=[(1.0, 15), (1.5, 30), (2.0, 48), (2.5, 62), (3.0, 76), (3.5, 88), (4.5, 100)],
                available_from_yfinance=False,
                na_message="Order book from company quarterly disclosures; not in yfinance",
            ),
            SectorMetric(
                "order_inflow_growth", "Order Inflow Growth (YoY)", 0.12, "high",
                "higher_is_better", "%",
                "New orders won in the year — leading indicator for future revenue",
                thresholds=[(-10, 5), (0, 22), (5, 42), (10, 60), (15, 76), (20, 88), (25, 100)],
                available_from_yfinance=False,
                na_message="Order inflows from company disclosures",
            ),
            SectorMetric(
                "book_to_bill", "Book-to-Bill (latest quarter)", 0.05, "medium",
                "higher_is_better", "x",
                "Order intake / revenue for the quarter — lumpy for EPC (one large award swings it); read with backlog cover",
                thresholds=[(0.5, 5), (0.8, 25), (1.0, 48), (1.3, 68), (1.8, 85), (2.5, 100)],
                available_from_yfinance=False,
                na_message="Order intake and revenue from the quarterly results release / investor presentation",
            ),
            SectorMetric(
                "export_order_pct", "International Share of Order Intake", 0.0, "low",
                "neutral", "%",
                "International share of the quarter's order intake — display only, not scored",
                available_from_yfinance=False,
                na_message="Only issuers that state the international split of orders (e.g. L&T)",
            ),
            SectorMetric(
                "international_backlog_pct", "International Share of Order Backlog", 0.0, "low",
                "neutral", "%",
                "Overseas share of the closing order book — display only; currency/country risk context",
                available_from_yfinance=False,
                na_message="Only issuers that state the international split of the backlog",
            ),
            SectorMetric(
                "ebitda_margin", "EBITDA Margin", 0.12, "high",
                "higher_is_better", "%",
                "EPC EBITDA 8-14%; infrastructure projects 20-30%",
                thresholds=[(0, 5), (4, 18), (6, 38), (8, 58), (10, 74), (12, 87), (15, 100)],
            ),
            SectorMetric(
                "pat_margin", "PAT Margin", 0.06, "medium",
                "higher_is_better", "%",
                "Net margin — EPC: 3-7%; infra: 8-15%",
                thresholds=[(0, 5), (2, 22), (4, 42), (6, 60), (8, 75), (10, 87), (14, 100)],
            ),
            SectorMetric(
                "working_capital_days", "Working Capital Days", 0.12, "high",
                "lower_is_better", "days",
                "Net working capital — EPC companies often have 90-150 day WC; above 180 is stressed",
                thresholds=[(30, 100), (60, 85), (90, 70), (120, 52), (150, 35), (180, 15), (240, 0)],
            ),
            SectorMetric(
                "debt_to_equity", "Debt/Equity", 0.12, "high",
                "lower_is_better", "x",
                "Leverage — EPC should be below 1x; infra concession 2-4x is typical",
                thresholds=[(0, 100), (0.3, 85), (0.6, 70), (1.0, 52), (1.5, 32), (2.0, 15), (3.0, 0)],
            ),
            SectorMetric(
                "roce", "ROCE", 0.10, "high",
                "higher_is_better", "%",
                "Capital efficiency — EPC: 15-25%; infra concessions: 10-18% (long-gestation)",
                thresholds=[(0, 5), (8, 22), (12, 45), (16, 62), (20, 78), (26, 90), (32, 100)],
            ),
            SectorMetric(
                "fcf_to_pat", "FCF / PAT", 0.08, "high",
                "higher_is_better", "%",
                "Cash conversion — construction is working-capital intensive; FCF often negative during growth",
                thresholds=[(0, 10), (15, 25), (35, 45), (55, 62), (70, 78), (85, 90), (100, 100)],
            ),
            SectorMetric(
                "receivable_days", "Receivable Days", 0.08, "medium",
                "lower_is_better", "days",
                "Debtor days — high receivables = government payment delays or disputed bills",
                thresholds=[(30, 100), (60, 85), (90, 68), (120, 50), (150, 32), (180, 15), (240, 0)],
            ),
            SectorMetric(
                "ev_to_ebitda", "EV/EBITDA", 0.06, "low",
                "neutral", "x",
                "Construction companies trade 10-18x on order visibility",
                thresholds=[(0, 55), (5, 78), (8, 88), (12, 80), (16, 62), (22, 40), (30, 18)],
            ),
        ]

    def red_flag_rules(self) -> list[SectorRedFlag]:
        return [
            SectorRedFlag(
                condition="order_book_to_revenue < 2",
                severity="HIGH",
                title="Low Order Book Cover",
                description="Order book below 2x revenue means less than 2 years of execution visibility — revenue growth at risk.",
            ),
            SectorRedFlag(
                condition="working_capital_days > 180",
                severity="HIGH",
                title="Very High Working Capital",
                description="Working capital above 180 days signals severe payment delays from clients or overbilling disputes.",
            ),
            SectorRedFlag(
                condition="debt_to_equity > 2",
                severity="HIGH",
                title="Very High Leverage",
                description="D/E above 2x for an EPC/construction company — working capital + capex debt is dangerous.",
            ),
            SectorRedFlag(
                condition="ebitda_margin < 7",
                severity="HIGH",
                title="Very Low EBITDA Margin",
                description="EPC EBITDA below 7% leaves little buffer for cost overruns — project economics are marginal.",
            ),
            SectorRedFlag(
                condition="order_inflow_growth < -10",
                severity="HIGH",
                title="Sharply Declining Order Inflows",
                description="Order inflow down >10% signals capex cycle slowdown or competitive bid losses.",
            ),
            SectorRedFlag(
                condition="receivable_days > 150",
                severity="MEDIUM",
                title="Very High Receivables",
                description="Receivable days above 150 signals government payment delays or disputes on billed amounts.",
            ),
        ]

    def _check_rule(self, rule: SectorRedFlag, metrics: dict, data: dict) -> bool:
        cond = rule.condition
        if cond == "order_book_to_revenue < 2":
            v = metrics.get("order_book_to_revenue"); return v is not None and v < 2
        if cond == "working_capital_days > 180":
            v = metrics.get("working_capital_days"); return v is not None and v > 180
        if cond == "debt_to_equity > 2":
            v = metrics.get("debt_to_equity"); return v is not None and v > 2
        if cond == "ebitda_margin < 7":
            v = metrics.get("ebitda_margin"); return v is not None and v < 7
        if cond == "order_inflow_growth < -10":
            v = metrics.get("order_inflow_growth"); return v is not None and v < -10
        if cond == "receivable_days > 150":
            v = metrics.get("receivable_days"); return v is not None and v > 150
        return False


class InfrastructureSector(ConstructionSector):
    """Infrastructure concessions — BOT/HAM, toll roads, ports, airports, bridges."""
    sector_name = "Infrastructure"
    sector_aliases = [
        "Infrastructure", "Roads", "Ports", "Airports", "Highways",
        "BOT", "HAM", "Concessions", "Toll Roads",
    ]

    SECTOR_WEIGHTS = {
        "growth": 0.22,
        "profitability": 0.20,
        "cash_flow": 0.25,
        "balance_sheet": 0.22,
        "efficiency": 0.08,
        "valuation": 0.03,
    }
