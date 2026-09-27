"""
Before adding sector-specific annual-report or quarterly-report note
extraction for this sector, check the two dedicated extraction engines'
Area Registries first — app/ingestion/annual_report_ingestion.py and
app/ingestion/quarterly_results_client.py (see also "Important md
files/Annual_Report_Fetching_Extraction_Engine.md" and
".../Quarterly_Report_Fetching_Extraction_Engine.md") — an existing
area may already cover what this sector needs.

NBFC sector framework — Non-Banking Financial Companies.

Completely separate from BankingSector. NBFCs:
- Cannot accept demand deposits
- Do NOT have CASA, deposit growth, CD ratio metrics
- Have AUM growth, collection efficiency, cost of borrowing, ALM metrics
- Regulated by RBI under NBFC regulations (not Banking Regulation Act)
- Higher leverage acceptable varies by sub-type (housing finance 8-10x, MFI 5-7x)

Sub-types supported via inheritance:
  NBFCSector (base — diversified NBFC)
  ├── HousingFinanceSector    (housing finance companies)
  ├── MicrofinanceSector      (microfinance institutions)
  └── GoldLoanSector          (gold loan NBFCs)

Most operational metrics (AUM, GNPA, collection efficiency) are NOT available
from yfinance standard financial statements.
"""
from __future__ import annotations
from app.sectors.base import SectorFramework, SectorMetric, SectorRedFlag


class NBFCSector(SectorFramework):
    sector_name = "NBFCs"
    sector_aliases = [
        "NBFC",
        "NBFCs",
        "Non-Banking Financial Company",
        "Non-Banking Financial Companies",
        "Non Banking Financial",
        "Diversified NBFC",
        "Credit Services",  # real NSE/exchange industry tag on 15 active stocks
                            # (e.g. Bajaj Finance) — added while generalizing
                            # Stage 8 to NBFCs; these were previously falling
                            # through to Generic (or, before the word-boundary
                            # fix in registry.py, accidentally matching IT
                            # Services via a substring collision).
    ]

    SECTOR_WEIGHTS = {
        "growth": 0.25,
        "profitability": 0.31,
        "cash_flow": 0.06,
        "balance_sheet": 0.29,
        "efficiency": 0.03,
        "valuation": 0.06,
    }

    def key_metrics(self) -> list[SectorMetric]:
        return [
            # ── Growth ────────────────────────────────────────────────────────
            SectorMetric(
                "revenue_cagr_3y", "Revenue/NII CAGR (3Y)", 0.12, "high",
                "higher_is_better", "%",
                "Revenue or NII 3Y CAGR — proxy for AUM/loan book growth",
                thresholds=[(0, 10), (5, 30), (8, 50), (12, 65), (16, 80), (20, 92), (25, 100)],
                applicable_to=["nbfc"],
            ),
            SectorMetric(
                "pat_cagr_3y", "PAT CAGR (3Y)", 0.08, "high",
                "higher_is_better", "%",
                "PAT 3Y CAGR — profitability growth trajectory",
                thresholds=[(0, 10), (5, 30), (10, 55), (15, 70), (20, 87), (25, 100)],
                applicable_to=["nbfc"],
            ),
            SectorMetric(
                "aum_growth_3y", "AUM Growth (3Y CAGR)", 0.10, "high",
                "higher_is_better", "%",
                "Assets Under Management 3Y CAGR — core business growth indicator",
                thresholds=[(0, 10), (5, 30), (10, 55), (15, 72), (20, 88), (25, 100)],
                available_from_yfinance=False,
                na_message="AUM not separately reported in yfinance; use revenue CAGR as proxy",
                applicable_to=["nbfc"],
            ),

            # ── Profitability ─────────────────────────────────────────────────
            SectorMetric(
                "roe", "Return on Equity (ROE)", 0.18, "high",
                "higher_is_better", "%",
                "ROE — primary profitability metric; 15-20%+ is strong for quality NBFCs",
                thresholds=[(0, 5), (5, 18), (10, 40), (14, 60), (17, 76), (20, 88), (25, 100)],
                applicable_to=["nbfc"],
            ),
            SectorMetric(
                "roa", "Return on Assets (ROA)", 0.14, "high",
                "higher_is_better", "%",
                "ROA — 2-3% is strong for NBFCs (higher than banks due to risk profile)",
                thresholds=[(0, 5), (0.5, 22), (1.0, 42), (1.8, 60), (2.5, 78), (3.2, 92), (4.0, 100)],
                applicable_to=["nbfc"],
            ),
            SectorMetric(
                "nim", "Net Interest Margin (NIM)", 0.12, "high",
                "higher_is_better", "%",
                "NIM — NBFCs typically earn higher NIM (4-10%) than banks to compensate for higher risk",
                thresholds=[(1.0, 15), (2.5, 35), (4.0, 58), (6.0, 76), (8.0, 90), (10.0, 100)],
                available_from_yfinance=False,
                na_message="NIM requires NII and loan-asset breakdowns from NBFC filings",
                applicable_to=["nbfc"],
            ),
            SectorMetric(
                "pat_margin", "PAT Margin", 0.06, "medium",
                "higher_is_better", "%",
                "Net profit margin on total income",
                thresholds=[(0, 10), (5, 30), (10, 50), (15, 68), (20, 84), (25, 100)],
                applicable_to=["nbfc"],
            ),

            # ── Asset Quality ─────────────────────────────────────────────────
            SectorMetric(
                "gross_npa", "Gross NPA Ratio", 0.15, "high",
                "lower_is_better", "%",
                "Gross NPA / Gross Loan Book — lower is better; <3% considered healthy for NBFCs",
                thresholds=[(0, 100), (1, 90), (2, 75), (3.5, 55), (5, 35), (8, 15), (12, 0)],
                available_from_yfinance=False,
                na_message="Gross NPA requires NBFC regulatory filings, not in yfinance",
                applicable_to=["nbfc"],
            ),
            SectorMetric(
                "net_npa", "Net NPA Ratio", 0.10, "high",
                "lower_is_better", "%",
                "Net NPA / Net Loan Book — residual credit risk after provisions",
                thresholds=[(0, 100), (0.5, 90), (1.0, 72), (2.0, 50), (3.5, 28), (5.0, 10), (7.0, 0)],
                available_from_yfinance=False,
                na_message="Net NPA requires provisioning data from NBFC quarterly filings",
                applicable_to=["nbfc"],
            ),
            SectorMetric(
                "provision_coverage_ratio", "Provision Coverage Ratio", 0.08, "medium",
                "higher_is_better", "%",
                "Provisions / Gross NPAs — indicates loss-absorption buffer",
                thresholds=[(20, 10), (40, 30), (55, 52), (68, 70), (78, 85), (90, 100)],
                available_from_yfinance=False,
                na_message="PCR requires provisioning detail from NBFC filings",
                applicable_to=["nbfc"],
            ),
            SectorMetric(
                "credit_cost", "Credit Cost", 0.12, "high",
                "lower_is_better", "%",
                "Provisions / Average Loan Book — directly impacts profitability",
                thresholds=[(0, 100), (0.5, 90), (1.0, 75), (1.5, 58), (2.5, 38), (3.5, 18), (5.0, 0)],
                available_from_yfinance=False,
                na_message="Credit cost requires provision and loan-book detail from NBFC filings",
                applicable_to=["nbfc"],
            ),
            SectorMetric(
                "collection_efficiency", "Collection Efficiency", 0.10, "high",
                "higher_is_better", "%",
                "Collections / Demand — key NBFC operational metric; below 95% is concerning",
                thresholds=[(80, 10), (90, 35), (95, 65), (97, 80), (98.5, 92), (100, 100)],
                available_from_yfinance=False,
                na_message="Collection efficiency is operational data from NBFC monthly filings",
                applicable_to=["nbfc"],
            ),

            # ── Funding / Liability ───────────────────────────────────────────
            SectorMetric(
                "cost_of_borrowing", "Cost of Borrowing", 0.10, "high",
                "lower_is_better", "%",
                "Average cost of funds — lower means better NIM and profitability",
                thresholds=[(5, 100), (6.5, 88), (7.5, 72), (8.5, 55), (9.5, 38), (10.5, 20), (12, 0)],
                available_from_yfinance=False,
                na_message="Borrowing cost requires liability schedule from NBFC filings",
                applicable_to=["nbfc"],
            ),
            SectorMetric(
                "debt_to_equity", "Leverage (D/E)", 0.10, "high",
                "neutral", "x",
                "NBFCs have higher leverage than industrials but lower than banks; 3-7x is typical",
                # NBFC-specific thresholds: not same as banks (8-12x) or industrials (1-2x)
                thresholds=[(0, 60), (2, 80), (4, 90), (6, 80), (8, 60), (10, 38), (14, 15), (18, 0)],
                applicable_to=["nbfc"],
            ),
            SectorMetric(
                "interest_coverage", "Interest Coverage", 0.06, "medium",
                "higher_is_better", "x",
                "EBIT / Interest — NBFCs have natural high interest expense; 1.3-2x is typical",
                thresholds=[(0, 5), (1.0, 30), (1.3, 55), (1.6, 72), (2.0, 85), (2.5, 95), (3.0, 100)],
                applicable_to=["nbfc"],
            ),

            # ── Capital ───────────────────────────────────────────────────────
            SectorMetric(
                "capital_adequacy_ratio", "Capital Adequacy Ratio (CRAR)", 0.10, "high",
                "higher_is_better", "%",
                "Total capital / Risk-weighted assets — RBI NBFC minimum is 15%; 18%+ comfortable",
                thresholds=[(10, 0), (15, 40), (17, 62), (19, 78), (22, 90), (25, 100)],
                available_from_yfinance=False,
                na_message="CAR requires RBI regulatory filings for NBFCs",
                applicable_to=["nbfc"],
            ),

            # ── ROE-simulator ideas (mentor's method; app/calculations/bank_roe_engine.py) ──
            SectorMetric(
                "sustainable_growth_gap", "Growth Beyond Self-Funding (pp)", 0.08, "high",
                "lower_is_better", "pp",
                "AUM/balance-sheet growth minus ROE x (1 - payout). Above zero, growth must be funded by fresh "
                "equity — a lender's dilution engine",
                thresholds=[(-5, 100), (0, 90), (3, 75), (6, 55), (10, 35), (15, 15), (20, 0)],
                available_from_yfinance=False,
                na_message="Needs balance-sheet growth, payout and ROE — derived by the ROE engine",
                applicable_to=["nbfc"],
            ),
            SectorMetric(
                "pb_roe_premium_pct", "P/B Premium to ROE-Justified (%)", 0.06, "medium",
                "neutral", "%",
                "Current P/B vs the P/B this ROE has earned on the mentor's (bank-derived) anchor curve — a "
                "guide to how much of the multiple is hope; high-ROE NBFCs legitimately earn more than a bank",
                thresholds=[(-40, 45), (-20, 80), (0, 90), (25, 75), (50, 50), (100, 25), (200, 5)],
                available_from_yfinance=False,
                na_message="Needs P/B and run-rate ROE — derived by the ROE engine",
                applicable_to=["nbfc"],
            ),

            # ── Valuation ─────────────────────────────────────────────────────
            SectorMetric(
                "pb_ratio", "Price-to-Book (P/B)", 0.10, "medium",
                "neutral", "x",
                "P/B for NBFCs — quality high-ROE NBFCs command premium P/B; interpret with ROE/ROA",
                # A high-ROE NBFC at 3-4x P/B is NOT overvalued; a low-ROE at 2x IS
                thresholds=[(0.3, 35), (0.7, 55), (1.2, 72), (2.0, 82), (3.0, 78), (4.5, 60), (7.0, 35), (12, 5)],
                applicable_to=["nbfc"],
            ),
            SectorMetric(
                "pe_ratio", "Price-to-Earnings (P/E)", 0.08, "medium",
                "neutral", "x",
                "P/E multiple — for NBFCs, 15-30x is typical; quality growth NBFCs at premium",
                thresholds=[(0, 45), (8, 68), (14, 85), (20, 80), (28, 65), (38, 45), (55, 22), (80, 5)],
                applicable_to=["nbfc"],
            ),
        ]

    def red_flag_rules(self) -> list[SectorRedFlag]:
        return [
            SectorRedFlag(
                condition="roe < 10",
                severity="HIGH",
                title="Low ROE for NBFC",
                description="ROE below 10% for an NBFC signals poor profitability — likely stressed asset quality or thin spreads.",
            ),
            SectorRedFlag(
                condition="roa < 1.0",
                severity="HIGH",
                title="Very Low ROA",
                description="ROA below 1% for an NBFC indicates very thin margins — credit costs may be eroding profitability.",
            ),
            SectorRedFlag(
                condition="gross_npa > 5",
                severity="HIGH",
                title="High Gross NPA",
                description="Gross NPA above 5% signals deteriorating portfolio quality — provisions will compress ROE significantly.",
            ),
            SectorRedFlag(
                condition="gross_npa > 3",
                severity="MEDIUM",
                title="Elevated Gross NPA",
                description="Gross NPA above 3% requires monitoring — trend matters more than the absolute level.",
            ),
            SectorRedFlag(
                condition="credit_cost > 2.5",
                severity="HIGH",
                title="Very High Credit Cost",
                description="Credit cost above 2.5% severely impairs NBFC profitability and will compress ROE.",
            ),
            SectorRedFlag(
                condition="collection_efficiency < 95",
                severity="HIGH",
                title="Poor Collection Efficiency",
                description="Collection efficiency below 95% is a leading indicator of NPA buildup and portfolio stress.",
            ),
            SectorRedFlag(
                condition="debt_to_equity > 10",
                severity="HIGH",
                title="Excessive Leverage",
                description="D/E above 10x for an NBFC (excluding banks) is dangerously high — rollover risk and solvency concern.",
            ),
            SectorRedFlag(
                condition="capital_adequacy_ratio < 15",
                severity="HIGH",
                title="Capital Adequacy Below RBI Minimum",
                description="CRAR below RBI's 15% minimum for NBFCs raises regulatory and solvency risk.",
            ),
            SectorRedFlag(
                condition="pat_cagr_3y < 5",
                severity="MEDIUM",
                title="Weak Earnings Growth",
                description="PAT CAGR below 5% over 3 years suggests stagnating profitability or elevated credit costs.",
            ),
            SectorRedFlag(
                condition="interest_coverage < 1.2",
                severity="HIGH",
                title="Dangerously Low Interest Coverage",
                description="Interest coverage below 1.2x means operating income barely covers interest — solvency risk.",
            ),
        ]

    def _check_rule(self, rule: SectorRedFlag, metrics: dict, data: dict) -> bool:
        cond = rule.condition
        if cond == "roe < 10":
            v = metrics.get("roe"); return v is not None and v < 10
        if cond == "roa < 1.0":
            v = metrics.get("roa"); return v is not None and v < 1.0
        if cond == "gross_npa > 5":
            v = metrics.get("gross_npa"); return v is not None and v > 5
        if cond == "gross_npa > 3":
            v = metrics.get("gross_npa"); return v is not None and 3 < v <= 5
        if cond == "credit_cost > 2.5":
            v = metrics.get("credit_cost"); return v is not None and v > 2.5
        if cond == "collection_efficiency < 95":
            v = metrics.get("collection_efficiency"); return v is not None and v < 95
        if cond == "debt_to_equity > 10":
            v = metrics.get("debt_to_equity"); return v is not None and v > 10
        if cond == "capital_adequacy_ratio < 15":
            v = metrics.get("capital_adequacy_ratio"); return v is not None and v < 15
        if cond == "pat_cagr_3y < 5":
            v = metrics.get("pat_cagr_3y"); return v is not None and v < 5
        if cond == "interest_coverage < 1.2":
            v = metrics.get("interest_coverage"); return v is not None and v < 1.2
        return False

    def _compute_special_metric(self, name: str, metrics: dict, data: dict) -> float | None:
        """Prefer an authoritative ingested value (BSE/NSE/Screener, see
        app/sectors/banking_data_bridge.py) over anything derived from
        generic yfinance financials — same mechanism BankingSector uses
        (app/sectors/banking.py), reused as-is (Architecture v2 Stage 8):
        gross_npa/net_npa/provision_coverage_ratio/credit_cost/
        capital_adequacy_ratio/nim/roa are the exact same metric_ids for
        both sectors (confirmed via app/metrics/registry.py's
        applicable_sectors), so the bridge dict key stays
        "_banking_authoritative_metrics" rather than a sector-neutral
        rename that would touch working, tested code for no functional
        gain. Subclasses (HousingFinanceSector, MicrofinanceSector,
        GoldLoanSector) inherit this automatically."""
        bridge = (data or {}).get("_banking_authoritative_metrics", {})
        if name in bridge:
            return bridge[name]
        if name == "roa":
            return metrics.get("roa")  # yfinance-derived fallback
        if name in ("sustainable_growth_gap", "pb_roe_premium_pct"):
            from app.calculations.bank_roe_engine import scoring_metrics
            return scoring_metrics(metrics, data).get(name)
        return None


class HousingFinanceSector(NBFCSector):
    """
    Housing Finance Companies (HFCs) — specialized NBFC sub-type.
    Examples: HDFC Ltd, LIC Housing Finance, Can Fin Homes, Aavas Financiers.

    Key differences from generic NBFC:
    - Lower NIM (3-5%) due to lower risk, longer tenure
    - Higher leverage acceptable (7-10x) due to secure collateral
    - Asset quality naturally better due to mortgage security
    - CAR minimum 15% same as NBFC
    - Key additional metrics: LTV, fixed-rate vs floating mix
    """
    sector_name = "Housing Finance"
    sector_aliases = [
        "Housing Finance",
        "HFC",
        "Home Finance",
        "Mortgage Finance",
        "NBFC - Housing Finance",
    ]

    SECTOR_WEIGHTS = {
        "growth": 0.24,
        "profitability": 0.29,
        "cash_flow": 0.06,
        "balance_sheet": 0.32,
        "efficiency": 0.03,
        "valuation": 0.06,
    }

    def red_flag_rules(self) -> list[SectorRedFlag]:
        base_rules = super().red_flag_rules()
        hfc_rules = [
            SectorRedFlag(
                condition="gross_npa > 4",
                severity="HIGH",
                title="High NPA for Housing Finance",
                description="Gross NPA above 4% for a housing finance company is elevated — mortgage quality is deteriorating.",
            ),
        ]
        # Override the generic NBFC NPA threshold with HFC-specific one
        filtered = [r for r in base_rules if r.condition != "gross_npa > 5"]
        return filtered + hfc_rules


class MicrofinanceSector(NBFCSector):
    """
    Microfinance Institutions (MFIs) — highest-risk NBFC sub-type.
    Examples: CreditAccess Grameen, Bandhan (now universal bank), Spandana Sphoorty.

    Key differences:
    - Much higher NIM (10-15%) to compensate for high credit risk
    - Collection efficiency is THE critical daily metric
    - Credit cost can spike dramatically (2-8%) in stressed environments
    - Lower leverage acceptable (4-6x) due to higher portfolio volatility
    - Regional concentration risk very high
    """
    sector_name = "Microfinance"
    sector_aliases = [
        "Microfinance",
        "MFI",
        "Micro Finance",
        "NBFC - MFI",
        "Micro Credit",
        "SFB",
        "Small Finance Bank",
    ]

    SECTOR_WEIGHTS = {
        "growth": 0.22,
        "profitability": 0.26,
        "cash_flow": 0.05,
        "balance_sheet": 0.37,
        "efficiency": 0.05,
        "valuation": 0.05,
    }

    def red_flag_rules(self) -> list[SectorRedFlag]:
        base_rules = super().red_flag_rules()
        mfi_rules = [
            SectorRedFlag(
                condition="credit_cost > 4",
                severity="HIGH",
                title="Very High Credit Cost for MFI",
                description="Credit cost above 4% for a microfinance institution will destroy profitability — severe portfolio stress.",
            ),
            SectorRedFlag(
                condition="collection_efficiency < 90",
                severity="HIGH",
                title="Critical Collection Efficiency for MFI",
                description="Collection efficiency below 90% for an MFI is a severe warning — NPA spike typically follows in 1-2 quarters.",
            ),
        ]
        # Override generic thresholds with MFI-specific ones
        filtered = [r for r in base_rules if r.condition not in ("credit_cost > 2.5", "collection_efficiency < 95")]
        return filtered + mfi_rules


class GoldLoanSector(NBFCSector):
    """
    Gold Loan NBFCs.
    Examples: Muthoot Finance, Manappuram Finance.

    Key differences:
    - Asset quality rarely a problem (gold is collateral, can be auctioned)
    - LTV (Loan-to-Value) on gold is the critical risk metric — RBI capped at 75%
    - Business is highly seasonal and commodity-price sensitive (gold price moves NIM)
    - Funding cost very important as gold loan yields are capped
    """
    sector_name = "Gold Loans"
    sector_aliases = [
        "Gold Loan",
        "Gold Loans",
        "NBFC - Gold Loan",
    ]

    SECTOR_WEIGHTS = {
        "growth": 0.27,
        "profitability": 0.30,
        "cash_flow": 0.09,
        "balance_sheet": 0.23,
        "efficiency": 0.06,
        "valuation": 0.05,
    }
