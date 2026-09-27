"""
Before adding sector-specific annual-report or quarterly-report note
extraction for this sector, check the two dedicated extraction engines'
Area Registries first — app/ingestion/annual_report_ingestion.py and
app/ingestion/quarterly_results_client.py (see also "Important md
files/Annual_Report_Fetching_Extraction_Engine.md" and
".../Quarterly_Report_Fetching_Extraction_Engine.md") — an existing
area may already cover what this sector needs.

Banking sector framework.
Covers commercial banks (public and private sector) ONLY.
NBFCs and Insurance have their own dedicated frameworks.

Key distinction:
- Banks: regulated by RBI under Banking Regulation Act, take deposits, lend
- NBFCs: Non-Banking Financial Companies, cannot accept demand deposits
- Insurance: regulated by IRDAI, completely different business model

Most critical banking metrics (NIM, GNPA, NNPA, CASA, CAR) are NOT available from
standard yfinance financial statements and are marked available_from_yfinance=False.
The framework computes what it can (ROA, ROE, PAT margin, book value) from available data.
"""
from __future__ import annotations
from app.sectors.base import SectorFramework, SectorMetric, SectorRedFlag


class BankingSector(SectorFramework):
    sector_name = "Banks"
    sector_aliases = [
        "Banks",
        "Banking",
        "Bank",
        "Public Sector Bank",
        "Private Sector Bank",
        "PSB",
        "Nationalised Bank",
        "Scheduled Commercial Bank",
    ]

    SECTOR_WEIGHTS = {
        "growth": 0.22,
        "profitability": 0.36,
        "cash_flow": 0.06,
        "balance_sheet": 0.27,
        "efficiency": 0.03,
        "valuation": 0.06,
    }

    def key_metrics(self) -> list[SectorMetric]:
        return [
            # ── Growth (available from yfinance) ──────────────────────────────
            SectorMetric(
                "revenue_cagr_3y", "NII/Revenue CAGR (3Y)", 0.12, "high",
                "higher_is_better", "%",
                "Net Interest Income or total revenue 3-year CAGR — proxy for loan book growth",
                thresholds=[(0, 10), (5, 30), (8, 50), (12, 65), (16, 80), (20, 90), (25, 100)],
                applicable_to=["bank"],
            ),
            SectorMetric(
                "pat_cagr_3y", "PAT CAGR (3Y)", 0.08, "high",
                "higher_is_better", "%",
                "Profit after tax 3-year CAGR reflecting earnings power",
                thresholds=[(0, 10), (5, 30), (10, 55), (15, 70), (20, 85), (25, 100)],
                applicable_to=["bank"],
            ),

            # ── Profitability (ROA/ROE available; NIM, credit cost not) ──────
            SectorMetric(
                "roe", "Return on Equity (ROE)", 0.20, "high",
                "higher_is_better", "%",
                "ROE is the primary profitability measure for banks — above 15% is best-in-class",
                thresholds=[(0, 5), (6, 20), (10, 40), (13, 60), (16, 75), (18, 87), (22, 100)],
                applicable_to=["bank"],
            ),
            SectorMetric(
                "roa", "Return on Assets (ROA)", 0.18, "high",
                "higher_is_better", "%",
                "ROA measures how efficiently a bank uses its asset base; 1-1.5% is quality range",
                thresholds=[(0, 5), (0.3, 20), (0.6, 40), (0.9, 60), (1.1, 75), (1.4, 88), (1.8, 100)],
                applicable_to=["bank"],
            ),
            SectorMetric(
                "pat_margin", "PAT Margin", 0.08, "medium",
                "higher_is_better", "%",
                "Net profit margin on total income",
                thresholds=[(0, 10), (5, 30), (10, 50), (15, 68), (20, 82), (25, 100)],
                applicable_to=["bank"],
            ),
            # ── NOT available from yfinance — regulatory/operational data ────
            SectorMetric(
                "nim", "Net Interest Margin (NIM)", 0.18, "high",
                "higher_is_better", "%",
                "NIM = Net Interest Income / Average Earning Assets — spread quality indicator",
                thresholds=[(1.0, 20), (2.0, 45), (2.8, 65), (3.5, 80), (4.2, 92), (5.0, 100)],
                available_from_yfinance=False,
                na_message="NIM requires NII and earning-asset split from bank filings (not in yfinance)",
                applicable_to=["bank"],
            ),
            SectorMetric(
                "gross_npa", "Gross NPA Ratio", 0.15, "high",
                "lower_is_better", "%",
                "Gross NPA / Gross Advances — measures portfolio credit quality",
                thresholds=[(0, 100), (1, 90), (2, 75), (3, 55), (5, 35), (8, 15), (12, 0)],
                available_from_yfinance=False,
                na_message="Gross NPA ratio requires RBI quarterly filings, not available in yfinance",
                applicable_to=["bank"],
            ),
            SectorMetric(
                "net_npa", "Net NPA Ratio", 0.12, "high",
                "lower_is_better", "%",
                "Net NPA / Net Advances after provisions — residual credit risk",
                thresholds=[(0, 100), (0.5, 90), (1.0, 72), (2.0, 50), (3.5, 28), (5.0, 10), (7.0, 0)],
                available_from_yfinance=False,
                na_message="Net NPA requires provisioning breakdowns from bank filings",
                applicable_to=["bank"],
            ),
            SectorMetric(
                "provision_coverage_ratio", "Provision Coverage Ratio (PCR)", 0.10, "high",
                "higher_is_better", "%",
                "Provisions / Gross NPAs — higher means better loss buffer",
                thresholds=[(30, 10), (50, 30), (65, 55), (75, 73), (80, 87), (90, 100)],
                available_from_yfinance=False,
                na_message="PCR requires provisioning data from bank quarterly filings",
                applicable_to=["bank"],
            ),
            SectorMetric(
                "casa_ratio", "CASA Ratio", 0.10, "high",
                "higher_is_better", "%",
                "Current + Savings Account deposits / Total deposits — lower cost funding",
                thresholds=[(10, 10), (25, 30), (35, 55), (42, 72), (48, 85), (55, 100)],
                available_from_yfinance=False,
                na_message="CASA ratio requires deposit composition data from bank filings",
                applicable_to=["bank"],
            ),
            SectorMetric(
                "credit_cost", "Credit Cost", 0.12, "high",
                "lower_is_better", "%",
                "Provisions / Average Advances — higher means more stressed portfolio",
                thresholds=[(0, 100), (0.3, 90), (0.6, 75), (1.0, 55), (1.5, 35), (2.5, 15), (3.5, 0)],
                available_from_yfinance=False,
                na_message="Credit cost requires provision and advances detail from bank filings",
                applicable_to=["bank"],
            ),
            SectorMetric(
                "capital_adequacy_ratio", "Capital Adequacy Ratio (CRAR)", 0.12, "high",
                "higher_is_better", "%",
                "Total capital / Risk-weighted assets — RBI minimum 11.5%; above 15% is comfortable",
                thresholds=[(8, 0), (11.5, 40), (13, 60), (15, 78), (17, 90), (20, 100)],
                available_from_yfinance=False,
                na_message="CAR/CRAR requires RBI regulatory filings, not in yfinance",
                applicable_to=["bank"],
            ),
            SectorMetric(
                "cost_to_income_ratio", "Cost-to-Income Ratio", 0.08, "medium",
                "lower_is_better", "%",
                "Operating costs / Net income — efficiency measure; below 45% is efficient",
                thresholds=[(30, 100), (40, 85), (45, 70), (50, 55), (55, 38), (60, 20), (70, 0)],
                available_from_yfinance=False,
                na_message="Cost-to-income requires operating expense breakdowns from bank filings",
                applicable_to=["bank"],
            ),
            SectorMetric(
                "slippage_ratio", "Slippage Ratio", 0.08, "high",
                "lower_is_better", "%",
                "Fresh NPAs added during quarter / Opening standard advances — forward-looking stress",
                thresholds=[(0, 100), (0.5, 88), (1.0, 70), (1.5, 50), (2.5, 28), (3.5, 10), (5.0, 0)],
                available_from_yfinance=False,
                na_message="Slippage ratio requires quarterly NPA movement data from bank filings",
                applicable_to=["bank"],
            ),
            # ── Valuation (available from yfinance via market data) ───────────
            SectorMetric(
                "pb_ratio", "Price-to-Book (P/B)", 0.12, "high",
                "neutral", "x",
                "Primary valuation metric for banks — 1-3x normal; quality banks trade 2-4x",
                # Not simply lower-is-better: distress bank at 0.3x P/B is NOT cheap
                thresholds=[(0.3, 40), (0.7, 60), (1.2, 78), (2.0, 85), (3.0, 76), (4.5, 58), (7.0, 30), (12, 5)],
                applicable_to=["bank"],
            ),
            SectorMetric(
                "pe_ratio", "Price-to-Earnings (P/E)", 0.08, "medium",
                "neutral", "x",
                "Earnings multiple — for banks, 10-20x is typical; quality banks command premium",
                thresholds=[(0, 50), (6, 72), (10, 88), (16, 82), (22, 68), (30, 50), (45, 28), (80, 8)],
                applicable_to=["bank"],
            ),
            # ── ROE-simulator ideas (mentor's method; app/calculations/bank_roe_engine.py) ──
            SectorMetric(
                "sustainable_growth_gap", "Growth Beyond Self-Funding (pp)", 0.08, "high",
                "lower_is_better", "pp",
                "Balance-sheet growth minus ROE x (1 - payout). Above zero, growth must be funded by fresh shares — "
                "the dilution that quietly eats per-share returns",
                thresholds=[(-5, 100), (0, 90), (3, 75), (6, 55), (10, 35), (15, 15), (20, 0)],
                available_from_yfinance=False,
                na_message="Needs balance-sheet growth, payout and ROE — derived by the ROE engine",
                applicable_to=["bank"],
            ),
            SectorMetric(
                "pb_roe_premium_pct", "P/B Premium to ROE-Justified (%)", 0.06, "medium",
                "neutral", "%",
                "Current P/B vs the P/B this ROE has earned on the mentor's anchor curve. A large premium means "
                "the market is paying for improvement not yet delivered; a discount can be a value trap or a bargain",
                thresholds=[(-40, 45), (-20, 80), (0, 90), (25, 75), (50, 50), (100, 25), (200, 5)],
                available_from_yfinance=False,
                na_message="Needs P/B and run-rate ROE — derived by the ROE engine",
                applicable_to=["bank"],
            ),
            # ── Leverage — banks are naturally highly leveraged via deposits ──
            SectorMetric(
                "debt_to_equity", "Leverage (D/E)", 0.06, "low",
                "neutral", "x",
                "Total liabilities/equity — banks naturally run 8-12x; not comparable to non-banks",
                # 8-12x is normal for banks; red flag only if excessively above peers
                thresholds=[(0, 60), (5, 80), (10, 85), (13, 75), (16, 55), (20, 30), (25, 5)],
                applicable_to=["bank"],
            ),
        ]

    def red_flag_rules(self) -> list[SectorRedFlag]:
        return [
            SectorRedFlag(
                condition="roe < 8",
                severity="HIGH",
                title="Very Low ROE for Bank",
                description="ROE below 8% for a bank is seriously weak — likely struggling with asset quality or thin margins.",
            ),
            SectorRedFlag(
                condition="roe < 12",
                severity="MEDIUM",
                title="Below-Par ROE",
                description="ROE below 12% is sub-standard for banking — cost of equity typically demands 13-15%.",
            ),
            SectorRedFlag(
                condition="roa < 0.5",
                severity="HIGH",
                title="Very Low ROA",
                description="ROA below 0.5% signals severely stressed profitability — thin spreads or heavy provisioning.",
            ),
            SectorRedFlag(
                condition="gross_npa > 5",
                severity="HIGH",
                title="High Gross NPA",
                description="Gross NPA above 5% indicates significant portfolio stress — credit costs will compress profitability.",
            ),
            SectorRedFlag(
                condition="gross_npa > 3",
                severity="MEDIUM",
                title="Elevated Gross NPA",
                description="Gross NPA above 3% requires monitoring — deterioration would compress margins sharply.",
            ),
            SectorRedFlag(
                condition="net_npa > 2",
                severity="HIGH",
                title="High Net NPA",
                description="Net NPA above 2% after provisions indicates residual credit risk that could require further provisioning.",
            ),
            SectorRedFlag(
                condition="credit_cost > 2",
                severity="HIGH",
                title="Very High Credit Cost",
                description="Credit cost above 2% severely compresses NIM — earnings are being consumed by provisions.",
            ),
            SectorRedFlag(
                condition="casa_ratio < 25",
                severity="MEDIUM",
                title="Low CASA Ratio",
                description="CASA below 25% means heavier reliance on costly term deposits — NIM compression risk.",
            ),
            SectorRedFlag(
                condition="capital_adequacy_ratio < 12",
                severity="HIGH",
                title="Thin Capital Buffer",
                description="Capital adequacy near RBI minimum leaves little buffer for credit shocks or growth.",
            ),
            SectorRedFlag(
                condition="revenue_cagr_3y < 5",
                severity="MEDIUM",
                title="Weak Loan/Revenue Growth",
                description="Revenue CAGR below 5% suggests weak loan book growth or margin compression.",
            ),
        ]

    def _check_rule(self, rule: SectorRedFlag, metrics: dict, data: dict) -> bool:
        cond = rule.condition
        if cond == "roe < 8":
            v = metrics.get("roe"); return v is not None and v < 8
        if cond == "roe < 12":
            v = metrics.get("roe"); return v is not None and 8 <= v < 12
        if cond == "roa < 0.5":
            v = metrics.get("roa"); return v is not None and v < 0.5
        if cond == "gross_npa > 5":
            v = metrics.get("gross_npa"); return v is not None and v > 5
        if cond == "gross_npa > 3":
            v = metrics.get("gross_npa"); return v is not None and 3 < v <= 5
        if cond == "net_npa > 2":
            v = metrics.get("net_npa"); return v is not None and v > 2
        if cond == "credit_cost > 2":
            v = metrics.get("credit_cost"); return v is not None and v > 2
        if cond == "casa_ratio < 25":
            v = metrics.get("casa_ratio"); return v is not None and v < 25
        if cond == "capital_adequacy_ratio < 12":
            v = metrics.get("capital_adequacy_ratio"); return v is not None and v < 12
        if cond == "revenue_cagr_3y < 5":
            v = metrics.get("revenue_cagr_3y"); return v is not None and v < 5
        return False

    def _compute_special_metric(self, name: str, metrics: dict, data: dict) -> float | None:
        """Prefer an authoritative ingested value (BSE filing/results-API, see
        app/sectors/banking_data_bridge.py and app/ingestion/banking_ingestion.py)
        over anything derived from generic yfinance financials — per
        sector_frameworks/banking.md's source hierarchy, company/exchange-reported
        figures outrank calculated ones."""
        bridge = (data or {}).get("_banking_authoritative_metrics", {})
        if name in bridge:
            return bridge[name]
        if name == "roa":
            return metrics.get("roa")  # yfinance-derived fallback
        if name in ("sustainable_growth_gap", "pb_roe_premium_pct"):
            from app.calculations.bank_roe_engine import scoring_metrics
            return scoring_metrics(metrics, data).get(name)
        return None
