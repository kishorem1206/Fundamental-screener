"""
Before adding sector-specific annual-report or quarterly-report note
extraction for this sector, check the two dedicated extraction engines'
Area Registries first — app/ingestion/annual_report_ingestion.py and
app/ingestion/quarterly_results_client.py (see also "Important md
files/Annual_Report_Fetching_Extraction_Engine.md" and
".../Quarterly_Report_Fetching_Extraction_Engine.md") — an existing
area may already cover what this sector needs.

Insurance sector framework — completely separate from Banking and NBFC.

Covers:
- Life Insurance (LIC, HDFC Life, SBI Life, ICICI Prudential Life)
- General Insurance (New India, United India, Oriental, Star Health)
- Health Insurance

Most insurance-specific metrics (combined ratio, loss ratio, solvency ratio,
embedded value, VNB, persistency) are NOT available from yfinance standard
financial statements. The framework marks these clearly.

Insurance companies are valued on embedded value (EV) and Value of New Business
(VNB) — NOT on P/E or EV/EBITDA like industrial companies.
"""
from __future__ import annotations
from app.sectors.base import SectorFramework, SectorMetric, SectorRedFlag


class InsuranceSector(SectorFramework):
    sector_name = "Insurance"
    sector_aliases = [
        "Insurance",
        "Life Insurance",
        "General Insurance",
        "Health Insurance",
        "Non Life Insurance",
        "Reinsurance",
    ]

    SECTOR_WEIGHTS = {
        "growth": 0.25,
        "profitability": 0.32,
        "cash_flow": 0.05,
        "balance_sheet": 0.26,
        "efficiency": 0.06,
        "valuation": 0.06,
    }

    def key_metrics(self) -> list[SectorMetric]:
        return [
            # ── Growth (some available from yfinance via total revenue) ────────
            SectorMetric(
                "revenue_cagr_3y", "Premium/Revenue CAGR (3Y)", 0.12, "high",
                "higher_is_better", "%",
                "Total revenue CAGR — proxy for gross written premium growth",
                thresholds=[(0, 10), (5, 30), (8, 50), (12, 65), (16, 82), (20, 92), (25, 100)],
                applicable_to=["insurance"],
            ),
            SectorMetric(
                "pat_cagr_3y", "PAT CAGR (3Y)", 0.08, "high",
                "higher_is_better", "%",
                "Profit after tax 3Y CAGR",
                thresholds=[(0, 10), (5, 30), (10, 55), (15, 70), (20, 88), (25, 100)],
                applicable_to=["insurance"],
            ),
            # ── Insurance-specific growth (NOT available from yfinance) ────────
            SectorMetric(
                "gwp_growth", "Gross Written Premium Growth", 0.12, "high",
                "higher_is_better", "%",
                "Annual GWP growth — primary top-line growth metric for insurers",
                thresholds=[(0, 10), (5, 30), (10, 55), (15, 72), (20, 88), (25, 100)],
                available_from_yfinance=False,
                na_message="GWP requires premium data from IRDAI/annual reports, not in yfinance",
                applicable_to=["insurance"],
            ),

            # ── Profitability (available) ─────────────────────────────────────
            SectorMetric(
                "roe", "Return on Equity (ROE)", 0.16, "high",
                "higher_is_better", "%",
                "ROE — 15-20%+ for quality insurers",
                thresholds=[(0, 5), (5, 20), (10, 42), (14, 60), (17, 76), (20, 88), (25, 100)],
                applicable_to=["insurance"],
            ),
            SectorMetric(
                "pat_margin", "PAT Margin", 0.10, "high",
                "higher_is_better", "%",
                "Net profit margin — insurance PAT margins vary widely by mix",
                thresholds=[(0, 10), (3, 28), (7, 48), (12, 65), (17, 80), (22, 100)],
                applicable_to=["insurance"],
            ),
            # ── Insurance-specific profitability (NOT available) ──────────────
            SectorMetric(
                "combined_ratio", "Combined Ratio", 0.15, "high",
                "lower_is_better", "%",
                "Loss ratio + expense ratio — below 100% means underwriting profit",
                thresholds=[(80, 100), (90, 85), (95, 70), (100, 50), (105, 30), (110, 10), (120, 0)],
                available_from_yfinance=False,
                na_message="Combined ratio requires claim and expense breakdowns from IRDAI filings",
                applicable_to=["insurance"],
            ),
            SectorMetric(
                "loss_ratio", "Loss/Claims Ratio", 0.12, "high",
                "lower_is_better", "%",
                "Net claims incurred / Net premiums earned — core underwriting quality",
                thresholds=[(40, 100), (55, 88), (65, 72), (72, 55), (80, 35), (90, 15), (100, 0)],
                available_from_yfinance=False,
                na_message="Loss ratio requires claims data from IRDAI/annual reports",
                applicable_to=["insurance"],
            ),
            SectorMetric(
                "expense_ratio", "Expense Ratio", 0.08, "medium",
                "lower_is_better", "%",
                "Operating expenses / Net premiums — efficiency of cost management",
                thresholds=[(10, 100), (15, 88), (20, 72), (25, 55), (30, 38), (38, 18), (45, 0)],
                available_from_yfinance=False,
                na_message="Expense ratio requires operating expense breakdown from IRDAI filings",
                applicable_to=["insurance"],
            ),

            # ── Life-insurance specific ────────────────────────────────────────
            SectorMetric(
                "vnb_margin", "VNB Margin", 0.14, "high",
                "higher_is_better", "%",
                "Value of New Business margin — measures profitability of new policies (life only)",
                thresholds=[(0, 10), (10, 35), (18, 55), (22, 70), (26, 83), (30, 93), (35, 100)],
                available_from_yfinance=False,
                na_message="VNB and embedded value are actuarial data from life insurer annual reports",
                applicable_to=["insurance"],
            ),
            SectorMetric(
                "persistency_13m", "13-Month Persistency Ratio", 0.10, "high",
                "higher_is_better", "%",
                "% of policies that persist 13 months — early lapse indicator (life only)",
                thresholds=[(55, 10), (65, 30), (75, 55), (80, 72), (85, 85), (90, 100)],
                available_from_yfinance=False,
                na_message="Persistency ratio is actuarial data from life insurer filings",
                applicable_to=["insurance"],
            ),

            # ── Capital / Solvency ────────────────────────────────────────────
            SectorMetric(
                "solvency_ratio", "Solvency Ratio", 0.14, "high",
                "higher_is_better", "x",
                "Available solvency margin / Required solvency margin — IRDAI minimum 1.5x",
                thresholds=[(1.0, 0), (1.5, 40), (1.8, 60), (2.2, 78), (2.8, 90), (3.5, 100)],
                available_from_yfinance=False,
                na_message="Solvency ratio requires actuarial/IRDAI data, not in yfinance",
                applicable_to=["insurance"],
            ),

            # ── Valuation ─────────────────────────────────────────────────────
            SectorMetric(
                "pb_ratio", "Price-to-Book (P/B)", 0.08, "medium",
                "neutral", "x",
                "P/B for insurers — less meaningful than EV/VNB for life; use with caution",
                thresholds=[(0.5, 40), (1.0, 60), (2.0, 78), (3.5, 82), (5.0, 70), (8.0, 45), (12, 15)],
                applicable_to=["insurance"],
            ),
            SectorMetric(
                "pe_ratio", "Price-to-Earnings (P/E)", 0.06, "low",
                "neutral", "x",
                "P/E — less ideal for life insurance; better used for general insurance",
                thresholds=[(0, 45), (10, 68), (18, 82), (25, 75), (35, 58), (50, 35), (80, 10)],
                applicable_to=["insurance"],
            ),
        ]

    def red_flag_rules(self) -> list[SectorRedFlag]:
        return [
            SectorRedFlag(
                condition="combined_ratio > 105",
                severity="HIGH",
                title="Underwriting Loss",
                description="Combined ratio above 105% means the insurer loses money on pure underwriting — relies on investment income to be profitable.",
            ),
            SectorRedFlag(
                condition="loss_ratio > 85",
                severity="HIGH",
                title="Very High Loss/Claims Ratio",
                description="Loss ratio above 85% leaves minimal margin for expenses — underwriting profitability under severe stress.",
            ),
            SectorRedFlag(
                condition="solvency_ratio < 1.5",
                severity="HIGH",
                title="Solvency Below IRDAI Minimum",
                description="Solvency ratio below IRDAI's 1.5x minimum is a serious regulatory and financial risk.",
            ),
            SectorRedFlag(
                condition="persistency_13m < 65",
                severity="HIGH",
                title="Very Low Policy Persistency",
                description="13-month persistency below 65% means high early-lapse rates — customer churn destroying new business value.",
            ),
            SectorRedFlag(
                condition="roe < 10",
                severity="MEDIUM",
                title="Low ROE for Insurer",
                description="ROE below 10% signals weak underwriting quality or investment returns failing to compensate.",
            ),
            SectorRedFlag(
                condition="revenue_cagr_3y < 5",
                severity="MEDIUM",
                title="Weak Premium Growth",
                description="Revenue/premium CAGR below 5% suggests market share loss or weak distribution.",
            ),
            SectorRedFlag(
                condition="vnb_margin < 15",
                severity="MEDIUM",
                title="Weak VNB Margin (Life)",
                description="VNB margin below 15% for a life insurer indicates poor product mix or high distribution costs.",
            ),
        ]

    def _check_rule(self, rule: SectorRedFlag, metrics: dict, data: dict) -> bool:
        cond = rule.condition
        if cond == "combined_ratio > 105":
            v = metrics.get("combined_ratio"); return v is not None and v > 105
        if cond == "loss_ratio > 85":
            v = metrics.get("loss_ratio"); return v is not None and v > 85
        if cond == "solvency_ratio < 1.5":
            v = metrics.get("solvency_ratio"); return v is not None and v < 1.5
        if cond == "persistency_13m < 65":
            v = metrics.get("persistency_13m"); return v is not None and v < 65
        if cond == "roe < 10":
            v = metrics.get("roe"); return v is not None and v < 10
        if cond == "revenue_cagr_3y < 5":
            v = metrics.get("revenue_cagr_3y"); return v is not None and v < 5
        if cond == "vnb_margin < 15":
            v = metrics.get("vnb_margin"); return v is not None and v < 15
        return False
