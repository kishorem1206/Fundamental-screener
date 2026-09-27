"""
Before adding sector-specific annual-report or quarterly-report note
extraction for this sector, check the two dedicated extraction engines'
Area Registries first — app/ingestion/annual_report_ingestion.py and
app/ingestion/quarterly_results_client.py (see also "Important md
files/Annual_Report_Fetching_Extraction_Engine.md" and
".../Quarterly_Report_Fetching_Extraction_Engine.md") — an existing
area may already cover what this sector needs.

FMCG sector framework — PROMPT.md Section 20.
Fast Moving Consumer Goods — Hindustan Unilever, Nestle, Britannia, Dabur, Marico, etc.

Key metrics per spec:
Volume growth, price/mix growth, gross margin, distribution strength,
premiumization %, rural exposure %, working capital days, FCF, ROCE, ROIC,
valuation (typically premium for quality FMCG).

Volume growth and premiumization are NOT available from yfinance.

`volume_growth_yoy` and `price_mix_growth` (both available_from_yfinance=
False) are now filled by the Quarterly Sector KPI Extraction Engine
("fmcg" area, 2026-09-20): `qtr_volume_growth_yoy` (company-wide underlying
volume growth, REPORTED) and `qtr_fmcg_price_mix_growth` (derived from
underlying sales vs volume growth). Confirmed exact live on HUL and Dabur;
see app/ingestion/quarterly_operating_metrics_ingestion.py for the full
investigation, including a caught mislabel on a scrambled chart page.
`rural_revenue_pct` / `premiumization_pct` stay NA — not quantified in
quarterly decks.
"""
from __future__ import annotations
from app.sectors.base import SectorFramework, SectorMetric, SectorRedFlag


class FMCGSector(SectorFramework):
    sector_name = "Fast Moving Consumer Goods"
    sector_aliases = [
        "Fast Moving Consumer Goods", "FMCG", "Consumer Staples",
        "Consumer Goods", "Food Products", "Personal Care",
        "Household Products", "Beverages",
    ]

    SECTOR_WEIGHTS = {
        "growth": 0.22,
        "profitability": 0.26,
        "cash_flow": 0.21,
        "balance_sheet": 0.13,
        "efficiency": 0.13,
        "valuation": 0.05,
    }

    def key_metrics(self) -> list[SectorMetric]:
        return [
            # ── Growth ────────────────────────────────────────────────────────
            SectorMetric(
                "revenue_cagr_3y", "Revenue CAGR (3Y)", 0.10, "high",
                "higher_is_better", "%",
                "Revenue 3Y CAGR — blends volume growth + price/mix changes",
                thresholds=[(0, 15), (2, 28), (5, 48), (8, 65), (12, 80), (15, 92), (20, 100)],
            ),
            SectorMetric(
                "pat_cagr_3y", "PAT CAGR (3Y)", 0.08, "high",
                "higher_is_better", "%",
                "Earnings growth — should track revenue with margin leverage",
                thresholds=[(0, 10), (5, 30), (10, 55), (14, 70), (18, 85), (22, 100)],
            ),
            # ── NOT available from yfinance ───────────────────────────────────
            SectorMetric(
                "volume_growth_yoy", "Volume Growth (YoY)", 0.12, "high",
                "higher_is_better", "%",
                "Underlying volume growth — key demand indicator; separates pricing from real demand",
                thresholds=[(-5, 0), (0, 22), (2, 42), (4, 62), (6, 78), (8, 90), (10, 100)],
                available_from_yfinance=False,
                na_message="Volume growth disclosed quarterly by FMCG companies; not in yfinance",
            ),
            SectorMetric(
                "price_mix_growth", "Price / Mix Growth", 0.08, "medium",
                "neutral", "%",
                "Pricing and product mix contribution to revenue — premiumization indicator",
                thresholds=[(-3, 20), (0, 40), (2, 60), (4, 75), (6, 85), (8, 95), (10, 100)],
                available_from_yfinance=False,
                na_message="Price/mix split requires management commentary in quarterly results",
            ),
            SectorMetric(
                "rural_revenue_pct", "Rural Revenue %", 0.06, "medium",
                "neutral", "%",
                "Revenue from rural India — high rural share = high monsoon/agri-cycle exposure",
                thresholds=[(15, 55), (25, 68), (35, 78), (45, 78), (55, 68), (65, 55), (75, 42)],
                available_from_yfinance=False,
                na_message="Rural/urban revenue split from management commentary; not in yfinance",
            ),
            SectorMetric(
                "premiumization_pct", "Premium Products Revenue %", 0.06, "medium",
                "higher_is_better", "%",
                "Premium SKUs as % of revenue — higher = better margins and differentiation",
                thresholds=[(5, 20), (10, 38), (20, 56), (30, 72), (40, 84), (50, 94), (60, 100)],
                available_from_yfinance=False,
                na_message="Premium mix data from investor presentations; not in yfinance",
            ),
            # ── Profitability (available) ─────────────────────────────────────
            SectorMetric(
                "gross_margin", "Gross Margin", 0.14, "high",
                "higher_is_better", "%",
                "Gross margin — FMCG gross margins 40-60%; indicates pricing power over RM costs",
                thresholds=[(20, 15), (30, 35), (38, 55), (45, 72), (50, 84), (55, 93), (60, 100)],
            ),
            SectorMetric(
                "ebitda_margin", "EBITDA Margin", 0.12, "high",
                "higher_is_better", "%",
                "EBITDA margin — 18-25% is healthy for quality FMCG; >25% is best-in-class",
                thresholds=[(8, 10), (12, 28), (16, 50), (20, 68), (24, 82), (28, 93), (35, 100)],
            ),
            SectorMetric(
                "pat_margin", "PAT Margin", 0.08, "medium",
                "higher_is_better", "%",
                "Net margin — 12-20% for quality FMCG companies",
                thresholds=[(5, 10), (8, 28), (12, 50), (15, 68), (18, 82), (22, 93), (28, 100)],
            ),
            SectorMetric(
                "roce", "ROCE", 0.12, "high",
                "higher_is_better", "%",
                "Capital efficiency — quality FMCG generates 30-60%+ ROCE due to negative working capital",
                thresholds=[(10, 15), (20, 35), (30, 58), (40, 74), (50, 85), (60, 93), (80, 100)],
            ),
            SectorMetric(
                "roic", "ROIC", 0.08, "high",
                "higher_is_better", "%",
                "Return on invested capital — should be well above WACC for quality FMCG",
                thresholds=[(10, 15), (20, 35), (30, 58), (40, 74), (50, 85), (60, 93), (80, 100)],
            ),
            # ── Working Capital / Efficiency (available) ──────────────────────
            SectorMetric(
                "inventory_days", "Inventory Days", 0.08, "medium",
                "lower_is_better", "days",
                "FMCG inventory days — lower is better; many categories run 20-40 days",
                thresholds=[(10, 100), (20, 88), (30, 75), (40, 60), (55, 42), (70, 22), (100, 0)],
            ),
            SectorMetric(
                "receivable_days", "Receivable Days", 0.06, "medium",
                "lower_is_better", "days",
                "Debtors days — FMCG with strong brands should have low receivables (<15 days)",
                thresholds=[(5, 100), (10, 90), (15, 78), (22, 62), (30, 45), (45, 25), (60, 0)],
            ),
            # ── Cash Flow ─────────────────────────────────────────────────────
            SectorMetric(
                "fcf_to_pat", "FCF / PAT", 0.10, "high",
                "higher_is_better", "%",
                "Cash conversion — quality FMCG should convert 75-100%+ of PAT to FCF",
                thresholds=[(10, 5), (40, 25), (60, 48), (75, 68), (88, 82), (100, 93), (115, 100)],
            ),
            # ── Balance Sheet ─────────────────────────────────────────────────
            SectorMetric(
                "debt_to_equity", "Debt/Equity", 0.06, "medium",
                "lower_is_better", "x",
                "FMCG should be near debt-free; above 0.5x needs investigation",
                thresholds=[(0, 100), (0.1, 92), (0.3, 80), (0.5, 62), (0.8, 40), (1.2, 18), (2.0, 0)],
            ),
            # ── Valuation ─────────────────────────────────────────────────────
            SectorMetric(
                "pe_ratio", "P/E", 0.06, "medium",
                "neutral", "x",
                "Quality FMCG commands premium P/E (30-60x) due to earnings visibility",
                thresholds=[(0, 40), (15, 60), (25, 78), (38, 82), (50, 72), (65, 52), (90, 28), (130, 8)],
            ),
            SectorMetric(
                "ev_to_ebitda", "EV/EBITDA", 0.04, "low",
                "neutral", "x",
                "Premium FMCG typically 30-50x EV/EBITDA — high multiple reflects earnings quality",
                thresholds=[(0, 45), (15, 65), (25, 80), (35, 82), (45, 72), (60, 52), (80, 28)],
            ),
        ]

    def red_flag_rules(self) -> list[SectorRedFlag]:
        return [
            SectorRedFlag(
                condition="gross_margin < 35",
                severity="HIGH",
                title="Very Low Gross Margin for FMCG",
                description="Gross margin below 35% signals severe RM cost pressure or poor pricing power — EBITDA and PAT will be compressed.",
            ),
            SectorRedFlag(
                condition="ebitda_margin < 14",
                severity="HIGH",
                title="Low EBITDA Margin",
                description="EBITDA below 14% for FMCG indicates either RM headwinds or structural loss of pricing power.",
            ),
            SectorRedFlag(
                condition="volume_growth_yoy < 0",
                severity="HIGH",
                title="Volume Decline",
                description="Negative volume growth signals demand loss — pricing-driven revenue growth without volume is unsustainable.",
            ),
            SectorRedFlag(
                condition="roce < 20",
                severity="MEDIUM",
                title="Below-Par ROCE for FMCG",
                description="ROCE below 20% is low for FMCG — the asset-light model with strong brands should generate 30-50%+ ROCE.",
            ),
            SectorRedFlag(
                condition="fcf_to_pat < 60",
                severity="MEDIUM",
                title="Low Cash Conversion for FMCG",
                description="FCF/PAT below 60% is below par for an FMCG company — investigate working capital or capex build.",
            ),
            SectorRedFlag(
                condition="debt_to_equity > 0.5",
                severity="MEDIUM",
                title="Unusual Leverage for FMCG",
                description="D/E above 0.5x is unusual for a consumer goods company — check if acquisition-driven.",
            ),
            SectorRedFlag(
                condition="revenue_cagr_3y < 4",
                severity="HIGH",
                title="Weak Revenue Growth",
                description="Revenue CAGR below 4% for FMCG suggests market share loss or severe pricing pressure.",
            ),
        ]

    def _check_rule(self, rule: SectorRedFlag, metrics: dict, data: dict) -> bool:
        cond = rule.condition
        if cond == "gross_margin < 35":
            v = metrics.get("gross_margin"); return v is not None and v < 35
        if cond == "ebitda_margin < 14":
            v = metrics.get("ebitda_margin"); return v is not None and v < 14
        if cond == "volume_growth_yoy < 0":
            v = metrics.get("volume_growth_yoy"); return v is not None and v < 0
        if cond == "roce < 20":
            v = metrics.get("roce"); return v is not None and v < 20
        if cond == "fcf_to_pat < 60":
            v = metrics.get("fcf_to_pat"); return v is not None and v < 60
        if cond == "debt_to_equity > 0.5":
            v = metrics.get("debt_to_equity"); return v is not None and v > 0.5
        if cond == "revenue_cagr_3y < 4":
            v = metrics.get("revenue_cagr_3y"); return v is not None and v < 4
        return False
