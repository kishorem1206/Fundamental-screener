"""
Before adding sector-specific annual-report or quarterly-report note
extraction for this sector, check the two dedicated extraction engines'
Area Registries first — app/ingestion/annual_report_ingestion.py and
app/ingestion/quarterly_results_client.py (see also "Important md
files/Annual_Report_Fetching_Extraction_Engine.md" and
".../Quarterly_Report_Fetching_Extraction_Engine.md") — an existing
area may already cover what this sector needs.

Metals & Mining sector framework — implements "Important md files/Sector
analysis framework/Commodities_Metals_and_Mining_Analysis_Framework.md".
Base metals (steel, aluminium, copper, zinc), precious metals, mining companies.
MiningSector inherits this with adjustments for royalty/reserve-based dynamics.

`ebitda_per_tonne`/`cost_per_tonne`/`production_volume_growth` (wired
2026-09-20) are sourced from `app/ingestion/annual_report_ingestion.py`'s
`metals_operating_metrics` area — production/sales volume is never on
Screener or yfinance. Validated live against three real companies with
genuinely different disclosure quality: JSW Steel's MD&A gives a clean
current+prior-year production table AND a directly-reported EBITDA/tonne
figure (both Consolidated and Standalone); Tata Steel's report has usable
narrative volume data but no direct EBITDA/tonne figure; Hindalco's report
has no comparably extractable text at all — its production charts extract
as scrambled, reversed digit strings via pdfplumber, an accepted
per-company miss (same class as Ambuja Cements'/JK Paper's).
"""
from __future__ import annotations
from app.sectors.base import SectorFramework, SectorMetric, SectorRedFlag


class MetalsSector(SectorFramework):
    sector_name = "Metals"
    sector_aliases = [
        "Metals", "Steel", "Iron & Steel", "Aluminium", "Copper", "Zinc",
        "Ferrous Metals", "Non-Ferrous Metals", "Metal Products",
    ]

    SECTOR_WEIGHTS = {
        "growth": 0.21,
        "profitability": 0.23,
        "cash_flow": 0.20,
        "balance_sheet": 0.21,
        "efficiency": 0.10,
        "valuation": 0.05,
    }

    def key_metrics(self) -> list[SectorMetric]:
        return [
            SectorMetric(
                "revenue_cagr_3y", "Revenue CAGR (3Y)", 0.10, "medium",
                "higher_is_better", "%",
                "Revenue growth — metals are cyclical; revenue driven by price × volume",
                thresholds=[(0, 15), (3, 28), (5, 45), (8, 62), (12, 78), (16, 90), (20, 100)],
            ),
            SectorMetric(
                "ebitda_per_tonne", "EBITDA per Tonne (INR)", 0.12, "high",
                "higher_is_better", "INR",
                "Margin per unit — key metric for metals; isolates cost control from price cycles. "
                "Prefers the company's own DIRECTLY-reported figure (common for steel companies' MD&A) "
                "over a derived pnl_operating_profit/volume figure. Was previously modeled in USD; "
                "corrected to INR (2026-09-20) — real Indian company disclosures state this in Rs/tonne, "
                "not USD (USD is only how the global LME benchmark PRICE is quoted, a separate concept).",
                thresholds=[(2000, 10), (4000, 28), (6000, 48), (9000, 65), (12000, 80), (16000, 92), (20000, 100)],
                available_from_yfinance=False,
                na_message="Requires this company's annual report MD&A production/sales volume "
                           "disclosure to have been ingested (app/ingestion/annual_report_ingestion.py's "
                           "metals_operating_metrics area) — not on Screener or yfinance",
            ),
            SectorMetric(
                "production_volume_growth", "Production Volume Growth (YoY)", 0.10, "medium",
                "higher_is_better", "%",
                "Capacity growth — volume expansion drives revenue independent of commodity price. "
                "Computed from the same-report current+prior-year production figures in the MD&A "
                "annual-report area, where disclosed (not every company gives both years in one place).",
                thresholds=[(-5, 5), (0, 22), (3, 42), (6, 62), (10, 78), (14, 90), (18, 100)],
                available_from_yfinance=False,
                na_message="Requires this company's annual report MD&A to disclose both current- and "
                           "prior-year production volume in the same place — not every company does",
            ),
            SectorMetric(
                "cost_per_tonne", "Cost per Tonne (INR)", 0.10, "high",
                "lower_is_better", "INR",
                "Total cost of production per unit — lower cost = better competitive positioning. "
                "Derived as realisation_per_tonne - ebitda_per_tonne, not a sum of individually-"
                "extracted cost components (same conservative-derivation precedent as Cement/Paper). "
                "Was previously modeled in USD; corrected to INR (2026-09-20), same reasoning as "
                "ebitda_per_tonne above.",
                thresholds=[(35000, 100), (45000, 82), (55000, 65), (65000, 48), (75000, 30),
                            (85000, 12), (95000, 0)],
                available_from_yfinance=False,
                na_message="Requires this company's annual report MD&A production/sales volume "
                           "disclosure to have been ingested — not on Screener or yfinance",
            ),
            SectorMetric(
                "ebitda_margin", "EBITDA Margin", 0.12, "high",
                "higher_is_better", "%",
                "Steel: 10-20%; Aluminium: 15-25% — margins swing with commodity cycle",
                thresholds=[(0, 5), (5, 18), (8, 38), (12, 55), (16, 70), (22, 85), (28, 100)],
            ),
            SectorMetric(
                "pat_margin", "PAT Margin", 0.06, "medium",
                "higher_is_better", "%",
                "Net margin — highly cyclical; can turn negative in downturns",
                thresholds=[(0, 5), (3, 22), (5, 42), (8, 62), (12, 78), (16, 90), (20, 100)],
            ),
            SectorMetric(
                "net_debt_to_ebitda", "Net Debt / EBITDA", 0.14, "high",
                "lower_is_better", "x",
                "Leverage relative to earnings — metals must maintain <3x through the cycle",
                thresholds=[(0, 100), (0.5, 90), (1.0, 78), (1.5, 62), (2.5, 45), (3.5, 25), (5.0, 5)],
            ),
            SectorMetric(
                "debt_to_equity", "Debt/Equity", 0.10, "high",
                "lower_is_better", "x",
                "Leverage — heavy asset base; above 1.5x risky in commodity downcycles",
                thresholds=[(0, 100), (0.3, 88), (0.5, 75), (1.0, 58), (1.5, 38), (2.0, 18), (3.0, 0)],
            ),
            SectorMetric(
                "roce", "ROCE", 0.10, "high",
                "higher_is_better", "%",
                "Capital returns — metals should earn 12-18%+ across the cycle",
                thresholds=[(0, 5), (5, 18), (10, 42), (14, 62), (18, 78), (24, 90), (30, 100)],
            ),
            SectorMetric(
                "fcf_to_pat", "FCF / PAT", 0.08, "medium",
                "higher_is_better", "%",
                "Cash conversion — watch during capex expansion; priority on debt repayment",
                thresholds=[(0, 10), (15, 25), (35, 45), (55, 62), (70, 78), (85, 90), (100, 100)],
            ),
            SectorMetric(
                "ev_to_ebitda", "EV/EBITDA", 0.08, "medium",
                "neutral", "x",
                "Enterprise multiple — metals cyclically trade 4-8x at cycle peak, 6-12x at trough",
                thresholds=[(0, 60), (3, 85), (5, 90), (7, 80), (10, 65), (14, 45), (20, 22)],
            ),
            SectorMetric(
                "pe_ratio", "P/E", 0.05, "low",
                "neutral", "x",
                "P/E unreliable for cyclicals; use EV/EBITDA and P/B instead",
                thresholds=[(0, 55), (5, 75), (8, 88), (12, 80), (18, 62), (25, 40), (40, 18)],
            ),
            SectorMetric(
                "pb_ratio", "P/Book", 0.05, "low",
                "neutral", "x",
                "P/B — useful for asset-heavy cyclicals; below 1x may signal deep value",
                thresholds=[(0, 50), (0.5, 68), (0.8, 80), (1.2, 85), (1.6, 78), (2.5, 58), (4.0, 30)],
            ),
        ]

    def red_flag_rules(self) -> list[SectorRedFlag]:
        return [
            SectorRedFlag(
                condition="net_debt_to_ebitda > 4",
                severity="HIGH",
                title="Very High Leverage (Net Debt/EBITDA)",
                description="Net Debt/EBITDA above 4x in metals is dangerous — a commodity price drop can create debt service distress.",
            ),
            SectorRedFlag(
                condition="net_debt_to_ebitda > 2.5",
                severity="MEDIUM",
                title="Elevated Leverage",
                description="Net Debt/EBITDA 2.5-4x — watch capex and cash flow; limited margin of safety in downturn.",
            ),
            SectorRedFlag(
                condition="ebitda_margin < 8",
                severity="HIGH",
                title="Very Low EBITDA Margin",
                description="EBITDA below 8% in metals signals cost disadvantage or commodity price collapse.",
            ),
            SectorRedFlag(
                condition="roce < 8",
                severity="HIGH",
                title="Poor Capital Returns",
                description="ROCE below 8% in metals across a 3-year window means the business is value-destructive.",
            ),
            SectorRedFlag(
                condition="debt_to_equity > 2.0",
                severity="HIGH",
                title="Dangerous Leverage",
                description="D/E above 2x in a commodity cyclical — a downturn can trigger covenant breaches.",
            ),
            SectorRedFlag(
                condition="production_volume_growth < -5",
                severity="MEDIUM",
                title="Volume Decline",
                description="Production volume down 5%+ signals operational issues or market share loss.",
            ),
        ]

    def _check_rule(self, rule: SectorRedFlag, metrics: dict, data: dict) -> bool:
        cond = rule.condition
        if cond == "net_debt_to_ebitda > 4":
            v = metrics.get("net_debt_to_ebitda"); return v is not None and v > 4
        if cond == "net_debt_to_ebitda > 2.5":
            v = metrics.get("net_debt_to_ebitda"); return v is not None and 2.5 < v <= 4
        if cond == "ebitda_margin < 8":
            v = metrics.get("ebitda_margin"); return v is not None and v < 8
        if cond == "roce < 8":
            v = metrics.get("roce"); return v is not None and v < 8
        if cond == "debt_to_equity > 2.0":
            v = metrics.get("debt_to_equity"); return v is not None and v > 2.0
        if cond == "production_volume_growth < -5":
            v = metrics.get("production_volume_growth"); return v is not None and v < -5
        return False


class MiningSector(MetalsSector):
    """Mining / mineral extraction — royalties, reserve life, cost-curve positioning."""

    sector_name = "Mining"
    sector_aliases = [
        "Mining", "Coal", "Coal India", "Mineral Extraction",
        "Iron Ore Mining", "Bauxite Mining",
    ]

    SECTOR_WEIGHTS = {
        "growth": 0.19,
        "profitability": 0.23,
        "cash_flow": 0.23,
        "balance_sheet": 0.20,
        "efficiency": 0.10,
        "valuation": 0.05,
    }
