"""
Before adding sector-specific annual-report or quarterly-report note
extraction for this sector, check the two dedicated extraction engines'
Area Registries first — app/ingestion/annual_report_ingestion.py and
app/ingestion/quarterly_results_client.py (see also "Important md
files/Annual_Report_Fetching_Extraction_Engine.md" and
".../Quarterly_Report_Fetching_Extraction_Engine.md") — an existing
area may already cover what this sector needs.

Capital Goods, Industrials, and Defence sector frameworks.

Order-book metrics (order_book_to_revenue, order_inflow_growth, book_to_bill,
export_order_pct) are filled from the Quarterly Sector KPI Extraction Engine
(`qtr_capgoods_*` keys, INR crore, results press release -> deck -> transcript
cascade) through the ledger bridge's QUARTERLY_FALLBACKS. order_book_to_revenue is
closing backlog / trailing-four-quarter Screener revenue and is only written when
four consecutive quarters exist. Rarely disclosed in a comparable form (mostly N/A): capacity
utilisation (section 10; stored only as one company-wide figure), aftermarket share of
orders, dealer economics.
Known traps: segment-only backlog next to the group figure (CG Power), rolling-
forecast backlog definitions (Thermax TOESL), figures in crore vs million vs billion.

Capital Goods: industrial machinery, heavy equipment, power equipment.
Industrials: diversified industrials, engineering conglomerates.
Defence: aerospace defence, defence electronics, shipbuilding.
"""
from __future__ import annotations
from app.sectors.base import SectorFramework, SectorMetric, SectorRedFlag
from app.sectors.construction import ConstructionSector


class CapitalGoodsSector(SectorFramework):
    sector_name = "Capital Goods"
    # Bare "Industrial" deliberately excluded — real bug found live
    # 2026-09-16: it matched as a whole word inside "Industrial Minerals"
    # (a mining company, sector="Metals & Mining") and "Industrial Gases"
    # (sector="Chemicals"), silently misrouting both into Capital Goods.
    # Replaced with the actual multi-word NSE industry-level labels this
    # framework needs ("Industrial Products", "Industrial Manufacturing") —
    # every live Capital Goods row in the DB already carries one of these
    # exact phrases, so no real coverage is lost.
    sector_aliases = [
        "Capital Goods", "Industrial Machinery", "Heavy Engineering",
        "Power Equipment", "Engineering", "Industrial Products", "Industrial Manufacturing",
    ]

    SECTOR_WEIGHTS = {
        "growth": 0.24,
        "profitability": 0.23,
        "cash_flow": 0.17,
        "balance_sheet": 0.19,
        "efficiency": 0.12,
        "valuation": 0.05,
    }

    def key_metrics(self) -> list[SectorMetric]:
        return [
            SectorMetric(
                "revenue_cagr_3y", "Revenue CAGR (3Y)", 0.10, "high",
                "higher_is_better", "%",
                "Revenue growth — lags order inflow by 6-18 months in long-cycle businesses",
                thresholds=[(0, 15), (5, 30), (10, 48), (15, 65), (20, 80), (25, 92), (30, 100)],
            ),
            SectorMetric(
                "order_book_to_revenue", "Order Book / Revenue", 0.14, "high",
                "higher_is_better", "x",
                "Order book cover — 2-3x provides strong revenue visibility",
                thresholds=[(0.8, 10), (1.2, 28), (1.8, 48), (2.2, 65), (2.8, 80), (3.5, 92), (4.5, 100)],
                available_from_yfinance=False,
                na_message="Order book from company quarterly disclosures",
            ),
            SectorMetric(
                "order_inflow_growth", "Order Inflow Growth (YoY)", 0.12, "high",
                "higher_is_better", "%",
                "New orders — leading indicator; driven by industrial and infrastructure capex cycle",
                thresholds=[(-10, 5), (0, 22), (5, 42), (10, 60), (15, 76), (20, 88), (25, 100)],
                available_from_yfinance=False,
                na_message="Order inflows from company quarterly disclosures",
            ),
            SectorMetric(
                "book_to_bill", "Book-to-Bill (latest quarter)", 0.05, "medium",
                "higher_is_better", "x",
                "Order intake / revenue for the quarter — above 1x means the order book is being replenished faster than executed",
                thresholds=[(0.5, 5), (0.8, 25), (1.0, 48), (1.2, 68), (1.5, 85), (2.0, 100)],
                available_from_yfinance=False,
                na_message="Order intake and revenue from the quarterly results release / investor presentation",
            ),
            SectorMetric(
                "export_order_pct", "Export Share of Order Intake", 0.0, "low",
                "neutral", "%",
                "Export share of the quarter's order intake — display only, not scored",
                available_from_yfinance=False,
                na_message="Only issuers that state the export split of order intake",
            ),
            SectorMetric(
                "aftermarket_order_pct", "Aftermarket Share of Order Intake", 0.0, "low",
                "neutral", "%",
                "Aftermarket/service/spares share of order intake — recurring-revenue proxy; display only, not scored",
                available_from_yfinance=False,
                na_message="Only issuers that state the aftermarket split of orders (e.g. Triveni Turbine)",
            ),
            SectorMetric(
                "capacity_utilization", "Capacity Utilisation", 0.0, "low",
                "neutral", "%",
                "Company-wide installed-capacity utilisation — display only; ranges and single-plant figures are not stored",
                available_from_yfinance=False,
                na_message="Rarely stated as one company-wide figure; mostly in concall answers",
            ),
            SectorMetric(
                "ebitda_margin", "EBITDA Margin", 0.12, "high",
                "higher_is_better", "%",
                "Capital goods EBITDA 10-18% — reflects product complexity and IP value",
                thresholds=[(0, 5), (5, 22), (8, 42), (10, 60), (13, 75), (16, 87), (20, 100)],
            ),
            SectorMetric(
                "roce", "ROCE", 0.12, "high",
                "higher_is_better", "%",
                "Capital efficiency — 15-25%+ for quality capital goods companies",
                thresholds=[(0, 5), (8, 22), (14, 45), (18, 62), (22, 78), (28, 90), (35, 100)],
            ),
            SectorMetric(
                "working_capital_days", "Working Capital Days", 0.10, "high",
                "lower_is_better", "days",
                "Net WC days — capital goods often 60-120 days; above 150 is elevated",
                thresholds=[(20, 100), (50, 85), (80, 70), (110, 52), (140, 32), (170, 15), (220, 0)],
            ),
            SectorMetric(
                "debt_to_equity", "Debt/Equity", 0.10, "high",
                "lower_is_better", "x",
                "Leverage — capital goods should be conservatively financed; above 1x warrants watch",
                thresholds=[(0, 100), (0.3, 88), (0.5, 75), (0.8, 60), (1.2, 40), (1.8, 18), (2.5, 0)],
            ),
            SectorMetric(
                "fcf_to_pat", "FCF / PAT", 0.08, "medium",
                "higher_is_better", "%",
                "Cash conversion — capital goods FCF can be lumpy during growth phase",
                thresholds=[(0, 10), (20, 28), (40, 48), (60, 65), (75, 80), (90, 92), (110, 100)],
            ),
            SectorMetric(
                "pat_cagr_3y", "PAT CAGR (3Y)", 0.08, "medium",
                "higher_is_better", "%",
                "Earnings growth — operating leverage should amplify PAT growth vs revenue",
                thresholds=[(0, 10), (5, 30), (10, 55), (15, 72), (20, 88), (28, 100)],
            ),
            SectorMetric(
                "pe_ratio", "P/E", 0.07, "medium",
                "neutral", "x",
                "Capital goods P/E 20-35x at cycle peak; 12-18x in slowdowns",
                thresholds=[(0, 45), (10, 65), (18, 82), (28, 78), (38, 60), (55, 38), (80, 15)],
            ),
            SectorMetric(
                "ev_to_ebitda", "EV/EBITDA", 0.07, "medium",
                "neutral", "x",
                "Enterprise multiple — 12-22x for quality capital goods names",
                thresholds=[(0, 55), (6, 78), (10, 90), (16, 80), (22, 62), (30, 40), (42, 18)],
            ),
        ]

    def red_flag_rules(self) -> list[SectorRedFlag]:
        return [
            SectorRedFlag(
                condition="order_book_to_revenue < 1.5",
                severity="HIGH",
                title="Low Order Book",
                description="Order book below 1.5x revenue — poor visibility and likely revenue deceleration ahead.",
            ),
            SectorRedFlag(
                condition="order_inflow_growth < -15",
                severity="HIGH",
                title="Sharply Declining Order Inflows",
                description="Order inflows down >15% signals a capex cycle downturn — revenue will follow in 12-18 months.",
            ),
            SectorRedFlag(
                condition="ebitda_margin < 8",
                severity="HIGH",
                title="Very Low EBITDA Margin",
                description="EBITDA below 8% for capital goods suggests low-value-add products or intense price competition.",
            ),
            SectorRedFlag(
                condition="working_capital_days > 150",
                severity="MEDIUM",
                title="High Working Capital",
                description="WC days above 150 signals either customer payment delays or long project execution timelines.",
            ),
            SectorRedFlag(
                condition="roce < 12",
                severity="MEDIUM",
                title="Low Capital Returns",
                description="ROCE below 12% — capital goods with IP should earn higher returns than generic manufacturers.",
            ),
            SectorRedFlag(
                condition="debt_to_equity > 1.5",
                severity="HIGH",
                title="High Leverage",
                description="D/E above 1.5x for a capital goods company amplifies risk when orders dry up.",
            ),
        ]

    def _check_rule(self, rule: SectorRedFlag, metrics: dict, data: dict) -> bool:
        cond = rule.condition
        if cond == "order_book_to_revenue < 1.5":
            v = metrics.get("order_book_to_revenue"); return v is not None and v < 1.5
        if cond == "order_inflow_growth < -15":
            v = metrics.get("order_inflow_growth"); return v is not None and v < -15
        if cond == "ebitda_margin < 8":
            v = metrics.get("ebitda_margin"); return v is not None and v < 8
        if cond == "working_capital_days > 150":
            v = metrics.get("working_capital_days"); return v is not None and v > 150
        if cond == "roce < 12":
            v = metrics.get("roce"); return v is not None and v < 12
        if cond == "debt_to_equity > 1.5":
            v = metrics.get("debt_to_equity"); return v is not None and v > 1.5
        return False


class IndustrialsSector(CapitalGoodsSector):
    """Diversified industrials, conglomerates, industrial services."""
    sector_name = "Industrials"
    sector_aliases = [
        "Industrials", "Diversified Industrials", "Industrial Services",
        "Conglomerate", "Industrial Conglomerate",
    ]


class DefenceSector(CapitalGoodsSector):
    """Aerospace & defence — long order cycles, government contracts, indigenization."""
    sector_name = "Defence"
    sector_aliases = [
        "Defence", "Defense", "Aerospace", "Aerospace & Defence",
        "Defence Equipment", "Shipbuilding",
    ]

    SECTOR_WEIGHTS = {
        "growth": 0.27,
        "profitability": 0.22,
        "cash_flow": 0.17,
        "balance_sheet": 0.19,
        "efficiency": 0.10,
        "valuation": 0.05,
    }