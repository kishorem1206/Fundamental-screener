"""
Before adding sector-specific annual-report or quarterly-report note
extraction for this sector, check the two dedicated extraction engines'
Area Registries first — app/ingestion/annual_report_ingestion.py and
app/ingestion/quarterly_results_client.py (see also "Important md
files/Annual_Report_Fetching_Extraction_Engine.md" and
".../Quarterly_Report_Fetching_Extraction_Engine.md") — an existing
area may already cover what this sector needs.

Telecom sector framework.

Operator KPIs (ARPU, customers and growth, churn, data usage, 4G/5G base), tower-company
tenancy and equipment order books come from the Quarterly Sector KPI Extraction Engine
(`qtr_tel_*`; cascade deck -> press release -> results filing -> transcript). Service FCF margin
needs EBITDA and capex stated in the same document, else stays N/A. Traps: India vs group/Africa
figures (Airtel), ARPU in INR vs US$, monthly vs quarterly churn, tower vs co-location counts.
Telecom - Infrastructure (tower companies) routes here, not to the roads/ports Infrastructure
framework.
Mobile, broadband, fiber, enterprise connectivity, data centers.
High capex, high debt — ARPU and subscriber growth are key metrics.
"""
from __future__ import annotations
from app.sectors.base import SectorFramework, SectorMetric, SectorRedFlag


class TelecomSector(SectorFramework):
    sector_name = "Telecom"
    sector_aliases = [
        "Telecom", "Telecommunications", "Mobile", "Wireless",
        "Telecom Services", "Media & Telecom", "Internet", "Broadband",
    ]

    SECTOR_WEIGHTS = {
        "growth": 0.24,
        "profitability": 0.24,
        "cash_flow": 0.22,
        "balance_sheet": 0.22,
        "efficiency": 0.05,
        "valuation": 0.03,
    }

    def key_metrics(self) -> list[SectorMetric]:
        return [
            SectorMetric(
                "revenue_cagr_3y", "Revenue CAGR (3Y)", 0.10, "high",
                "higher_is_better", "%",
                "Revenue growth — telecom ARPU hikes and subscriber consolidation drive growth",
                thresholds=[(0, 15), (3, 30), (5, 48), (8, 65), (12, 80), (16, 92), (20, 100)],
            ),
            SectorMetric(
                "arpu", "ARPU (INR/month)", 0.14, "high",
                "higher_is_better", "INR",
                "Average Revenue per User — most important telecom metric; ₹200+ is the 5G breakeven zone",
                thresholds=[(80, 10), (120, 28), (160, 48), (200, 65), (230, 80), (260, 92), (300, 100)],
                available_from_yfinance=False,
                na_message="ARPU from telecom operator quarterly disclosures; not in yfinance",
            ),
            SectorMetric(
                "subscriber_growth_yoy", "Subscriber Net Additions (YoY)", 0.10, "high",
                "higher_is_better", "%",
                "Subscriber growth rate — market consolidation means leaders gain at tail's expense",
                thresholds=[(-5, 5), (0, 22), (2, 42), (5, 62), (8, 78), (12, 90), (15, 100)],
                available_from_yfinance=False,
                na_message="Subscriber data from TRAI monthly reports or operator disclosures",
            ),
            SectorMetric(
                "data_revenue_pct", "Data Revenue %", 0.08, "medium",
                "higher_is_better", "%",
                "Data/digital revenue as % of total — higher data share = higher ARPU potential",
                thresholds=[(20, 20), (30, 38), (40, 55), (50, 70), (60, 82), (70, 93), (80, 100)],
                available_from_yfinance=False,
                na_message="Data/voice revenue split from operator disclosures",
            ),
            SectorMetric(
                "churn_pct", "Monthly Churn", 0.0, "low",
                "neutral", "%",
                "Monthly subscriber churn — retention quality; lower is better — display only, not scored",
                available_from_yfinance=False,
                na_message="Stated by mobile operators in results filings",
            ),
            SectorMetric(
                "data_usage_gb_per_sub", "Data Usage / Customer / Month", 0.0, "low",
                "neutral", "GB",
                "Monetisation headroom — usage grows faster than ARPU — display only, not scored",
                available_from_yfinance=False,
                na_message="Stated by mobile operators",
            ),
            SectorMetric(
                "tenancy_ratio", "Tenancy Ratio", 0.0, "low",
                "neutral", "x",
                "Tenants per tower — the tower company's operating leverage — display only, not scored",
                available_from_yfinance=False,
                na_message="Stated by tower companies (co-locations / towers)",
            ),
            SectorMetric(
                "market_share_mobile_pct", "Mobile Subscriber Market Share", 0.0, "low",
                "neutral", "%",
                "Share of India's wireless subscribers (TRAI monthly report) — display only, not scored",
                available_from_yfinance=False,
                na_message="TRAI publishes operator shares mostly as chart labels; only some are extractable",
            ),
            SectorMetric(
                "wireless_broadband_share_pct", "Wireless Broadband Share", 0.0, "low",
                "neutral", "%",
                "Share of India's wireless broadband subscribers (TRAI operator table) — display only, not scored",
                available_from_yfinance=False,
                na_message="TRAI operator table, top-five operators",
            ),
            SectorMetric(
                "ebitda_margin", "EBITDA Margin", 0.12, "high",
                "higher_is_better", "%",
                "Telecom EBITDA 30-45% is healthy; reflects scale and network density",
                thresholds=[(10, 5), (18, 22), (25, 42), (32, 62), (38, 78), (44, 92), (50, 100)],
            ),
            SectorMetric(
                "ebitda_minus_capex_margin", "EBITDA - CapEx Margin (Service FCF)", 0.12, "high",
                "higher_is_better", "%",
                "Service FCF margin — EBITDA after capex; key for 5G-investing operators",
                thresholds=[(0, 10), (5, 28), (10, 48), (14, 65), (18, 80), (22, 92), (28, 100)],
                available_from_yfinance=False,
                na_message="Requires EBITDA and capex data (capex partially in yfinance)",
            ),
            SectorMetric(
                "net_debt_to_ebitda", "Net Debt / EBITDA", 0.14, "high",
                "lower_is_better", "x",
                "Leverage — Indian telecom is highly levered; <2.5x is safe; >4x is distressed",
                thresholds=[(0, 100), (0.5, 90), (1.0, 78), (1.5, 65), (2.5, 48), (4.0, 25), (6.0, 5)],
            ),
            SectorMetric(
                "debt_to_equity", "Debt/Equity", 0.10, "high",
                "lower_is_better", "x",
                "Very high leverage is common; above 5x equity is dangerous",
                thresholds=[(0, 100), (1, 85), (2, 70), (3, 52), (5, 30), (7, 12), (10, 0)],
            ),
            SectorMetric(
                "capex_to_revenue", "CapEx / Revenue", 0.10, "medium",
                "lower_is_better", "%",
                "Capital intensity — 5G capex cycle drives 20-30% capex/revenue; watch trajectory",
                thresholds=[(5, 100), (10, 85), (15, 68), (20, 50), (25, 32), (30, 15), (40, 0)],
            ),
            SectorMetric(
                "roce", "ROCE", 0.08, "medium",
                "higher_is_better", "%",
                "Capital efficiency — telecom should earn 10-18%+ once 5G cycle matures",
                thresholds=[(0, 5), (5, 22), (8, 42), (12, 62), (16, 78), (20, 90), (26, 100)],
            ),
            SectorMetric(
                "ev_to_ebitda", "EV/EBITDA", 0.06, "low",
                "neutral", "x",
                "Telecom trades 8-14x; infrastructure-rich operators at premium",
                thresholds=[(0, 55), (4, 78), (6, 90), (9, 82), (13, 65), (18, 42), (25, 18)],
            ),
        ]

    def red_flag_rules(self) -> list[SectorRedFlag]:
        return [
            SectorRedFlag(
                condition="arpu < 130",
                severity="HIGH",
                title="Very Low ARPU",
                description="ARPU below ₹130/month is below 5G break-even — unsustainable for network investment recovery.",
            ),
            SectorRedFlag(
                condition="net_debt_to_ebitda > 5",
                severity="HIGH",
                title="Dangerous Leverage",
                description="Net Debt/EBITDA above 5x — debt restructuring or equity dilution risk; watch AGR and spectrum dues.",
            ),
            SectorRedFlag(
                condition="net_debt_to_ebitda > 3.5",
                severity="MEDIUM",
                title="Elevated Leverage",
                description="Net Debt/EBITDA 3.5-5x — limited financial flexibility; ARPU hikes required to deleverage.",
            ),
            SectorRedFlag(
                condition="ebitda_margin < 25",
                severity="HIGH",
                title="Low EBITDA Margin",
                description="EBITDA below 25% for a telecom operator signals cost inefficiency or market share losses.",
            ),
            SectorRedFlag(
                condition="subscriber_growth_yoy < -3",
                severity="HIGH",
                title="Subscriber Loss",
                description="Subscriber base shrinking — loss of market share to competitors; ARPU must compensate.",
            ),
            SectorRedFlag(
                condition="capex_to_revenue > 30",
                severity="MEDIUM",
                title="Very High CapEx Intensity",
                description="CapEx above 30% of revenue — 5G rollout or spectrum purchases consuming free cash flow.",
            ),
        ]

    def _check_rule(self, rule: SectorRedFlag, metrics: dict, data: dict) -> bool:
        cond = rule.condition
        if cond == "arpu < 130":
            v = metrics.get("arpu"); return v is not None and v < 130
        if cond == "net_debt_to_ebitda > 5":
            v = metrics.get("net_debt_to_ebitda"); return v is not None and v > 5
        if cond == "net_debt_to_ebitda > 3.5":
            v = metrics.get("net_debt_to_ebitda"); return v is not None and 3.5 < v <= 5
        if cond == "ebitda_margin < 25":
            v = metrics.get("ebitda_margin"); return v is not None and v < 25
        if cond == "subscriber_growth_yoy < -3":
            v = metrics.get("subscriber_growth_yoy"); return v is not None and v < -3
        if cond == "capex_to_revenue > 30":
            v = metrics.get("capex_to_revenue"); return v is not None and v > 30
        return False
