"""
Before adding sector-specific annual-report or quarterly-report note
extraction for this sector, check the two dedicated extraction engines'
Area Registries first — app/ingestion/annual_report_ingestion.py and
app/ingestion/quarterly_results_client.py (see also "Important md
files/Annual_Report_Fetching_Extraction_Engine.md" and
".../Quarterly_Report_Fetching_Extraction_Engine.md") — an existing
area may already cover what this sector needs.

IT Services sector framework — PROMPT.md Section 18.
Covers Indian IT services and software exporters (TCS, Infosys, Wipro, HCL, LTI, etc.)

Key metrics per spec:
Constant-currency growth, EBIT margin, employee growth, revenue/employee,
utilization rate, attrition rate, deal wins/TCV, order book, client concentration,
FCF, ROCE, ROIC, net cash/debt position.

Most operational metrics (utilization, attrition, deal wins, CC growth)
are NOT available from yfinance standard financial statements.

Quarterly operational metrics are filled from the Quarterly Sector KPI Extraction
Engine (`qtr_it_*`: CC growth YoY/QoQ, USD revenue, headcount, LTM attrition, utilisation,
deal/large-deal TCV, top-5/10 client %, geography/vertical mix, offshore effort, $1M+ clients,
derived revenue/employee) via the ledger bridge; an annual/transcript value on file wins. Traps:
INR vs USD revenue, CC vs reported growth, utilisation with vs without trainees, total vs
large-deal TCV, voluntary vs total attrition, segment/acquisition-only CC figures. Not disclosed
comparably (N/A): pricing/billing rates, subcontractor ratio, recurring-revenue %, deal
pipeline, software ARR/NRR/CAC/LTV, hardware unit/ASP data.
"""
from __future__ import annotations
from app.sectors.base import SectorFramework, SectorMetric, SectorRedFlag


class ITServicesSector(SectorFramework):
    sector_name = "Information Technology"
    sector_aliases = [
        "Information Technology", "IT Services", "IT",
        # "Technology" (bare) deliberately excluded — too generic, matched
        # "Financial Technology (Fintech)" as a whole word and mis-routed
        # Pine Labs (a payments company) into the IT framework. Every real
        # IT company in the DB already matches via a more specific alias
        # ("IT - Software", "IT - Services", "Software - Application", ...).
        #
        # "Software" (bare) also excluded, 2026-09-16 — matched inside
        # "TV Broadcasting & Software Production" (NSE's own basic_industry
        # label for TV production/broadcasting companies — "software" here
        # means broadcast program content, not computer software), silently
        # routing real media companies into IT. Real IT companies with
        # basic_industry="Software Products" still resolve correctly via
        # the industry-level "IT - Software" exact match one level up.
        "Software Services", "BPO", "IT - Software",
        "Computers - Software & Consulting",
    ]

    SECTOR_WEIGHTS = {
        "growth": 0.27,
        "profitability": 0.27,
        "cash_flow": 0.21,
        "balance_sheet": 0.11,
        "efficiency": 0.08,
        "valuation": 0.06,
    }

    def key_metrics(self) -> list[SectorMetric]:
        return [
            # ── Growth ────────────────────────────────────────────────────────
            SectorMetric(
                "revenue_cagr_3y", "Revenue CAGR (3Y)", 0.12, "high",
                "higher_is_better", "%",
                "Revenue 3Y CAGR — proxy for demand and market share; USD revenue growth preferred",
                thresholds=[(0, 15), (3, 30), (6, 48), (10, 66), (14, 82), (18, 92), (22, 100)],
            ),
            SectorMetric(
                "pat_cagr_3y", "PAT CAGR (3Y)", 0.08, "high",
                "higher_is_better", "%",
                "Earnings growth — should be broadly in line with or above revenue growth",
                thresholds=[(0, 10), (5, 30), (10, 55), (15, 70), (20, 85), (25, 100)],
            ),
            # ── NOT available from yfinance ───────────────────────────────────
            SectorMetric(
                "cc_revenue_growth", "Constant-Currency Revenue Growth", 0.10, "high",
                "higher_is_better", "%",
                "Revenue growth in USD constant currency — strips out FX benefit/headwind",
                thresholds=[(-2, 5), (0, 22), (3, 42), (6, 62), (9, 78), (12, 90), (15, 100)],
                available_from_yfinance=False,
                na_message="CC growth disclosed quarterly by companies; not in yfinance statements",
            ),
            SectorMetric(
                "deal_wins_tcv", "Deal Wins (TCV, USD Bn)", 0.10, "high",
                "higher_is_better", "USD Bn",
                "Total Contract Value of new deals — forward revenue visibility",
                thresholds=[(0, 10), (0.3, 28), (0.6, 48), (1.0, 65), (2.0, 80), (4.0, 92), (8.0, 100)],
                available_from_yfinance=False,
                na_message="TCV deal wins disclosed in quarterly earnings presentations",
            ),
            SectorMetric(
                "attrition_rate", "Attrition Rate (LTM)", 0.08, "high",
                "lower_is_better", "%",
                "Trailing 12-month employee attrition — below 15% is healthy; above 20% is elevated",
                thresholds=[(8, 100), (12, 88), (15, 72), (18, 55), (22, 35), (28, 15), (35, 0)],
                available_from_yfinance=False,
                na_message="Attrition disclosed in quarterly results; not in yfinance financial statements",
            ),
            SectorMetric(
                "utilization_rate", "Billable Utilization Rate", 0.08, "high",
                "higher_is_better", "%",
                "% of billable employees on revenue-generating projects — 80-85% is optimal",
                thresholds=[(60, 20), (70, 45), (75, 62), (80, 78), (83, 88), (86, 96), (90, 100)],
                available_from_yfinance=False,
                na_message="Utilization rate is operational data from quarterly presentations",
            ),
            SectorMetric(
                "revenue_per_employee", "Revenue per Employee (USD)", 0.06, "medium",
                "higher_is_better", "USD k",
                "Revenue productivity per employee — higher = better pricing/mix or automation",
                thresholds=[(15, 20), (20, 38), (25, 55), (30, 70), (40, 83), (55, 93), (70, 100)],
                available_from_yfinance=False,
                na_message="Employee count not in yfinance; requires HR data from annual reports",
            ),
            SectorMetric(
                "client_concentration_top10", "Top-10 Client Revenue %", 0.06, "medium",
                "lower_is_better", "%",
                "Revenue from top 10 clients as % — higher concentration = more revenue risk",
                thresholds=[(15, 100), (25, 85), (35, 68), (45, 50), (55, 32), (65, 15), (80, 0)],
                available_from_yfinance=False,
                na_message="Client concentration data from annual reports / investor presentations",
            ),
            SectorMetric(
                "large_deal_tcv", "Large-Deal TCV (USD Bn)", 0.0, "low",
                "neutral", "USD Bn",
                "TCV of large deal wins in the quarter; a TCV is not near-term revenue — display only, not scored",
                available_from_yfinance=False,
                na_message="Stated in results releases/fact sheets",
            ),
            SectorMetric(
                "client_concentration_top5", "Top-5 Client Revenue %", 0.0, "low",
                "neutral", "%",
                "Revenue share of the five largest clients — display only, not scored",
                available_from_yfinance=False,
                na_message="Stated by some issuers (Infosys, HCL)",
            ),
            SectorMetric(
                "north_america_revenue_pct", "North America Share of Revenue", 0.0, "low",
                "neutral", "%",
                "Geographic mix — currency and demand exposure — display only, not scored",
                available_from_yfinance=False,
                na_message="Stated in results releases/fact sheets",
            ),
            SectorMetric(
                "bfsi_revenue_pct", "BFSI Share of Revenue", 0.0, "low",
                "neutral", "%",
                "Vertical mix — BFSI is the largest and most cyclical Indian IT vertical — display only, not scored",
                available_from_yfinance=False,
                na_message="Stated in fact sheets",
            ),
            SectorMetric(
                "offshore_effort_pct", "Offshore Effort %", 0.0, "low",
                "neutral", "%",
                "Offshore share of delivery effort — margin lever — display only, not scored",
                available_from_yfinance=False,
                na_message="Stated in fact sheets",
            ),
            SectorMetric(
                "million_dollar_clients", "US$1M+ Clients", 0.0, "low",
                "neutral", "units",
                "Count of clients above US$1 million — client-mining depth — display only, not scored",
                available_from_yfinance=False,
                na_message="Stated in fact sheets",
            ),
            # ── Profitability (available) ─────────────────────────────────────
            SectorMetric(
                "ebit_margin", "EBIT Margin", 0.14, "high",
                "higher_is_better", "%",
                "Operating margin — Tier-1 IT targets 20-25%; 15-20% for mid-tier",
                thresholds=[(5, 10), (10, 28), (15, 52), (18, 68), (21, 82), (25, 93), (30, 100)],
            ),
            SectorMetric(
                "ebitda_margin", "EBITDA Margin", 0.08, "medium",
                "higher_is_better", "%",
                "EBITDA margin — adds back D&A (significant for leased offices/tech)",
                thresholds=[(8, 10), (12, 30), (16, 52), (20, 70), (24, 84), (28, 94), (35, 100)],
            ),
            SectorMetric(
                "roce", "ROCE", 0.10, "high",
                "higher_is_better", "%",
                "Capital efficiency — IT is asset-light; 30-50%+ ROCE is achievable",
                thresholds=[(5, 10), (15, 30), (25, 55), (35, 72), (45, 85), (55, 94), (70, 100)],
            ),
            SectorMetric(
                "roic", "ROIC", 0.08, "high",
                "higher_is_better", "%",
                "Return on invested capital — asset-light model should generate high ROIC",
                thresholds=[(5, 10), (15, 30), (25, 55), (35, 72), (45, 85), (55, 94), (70, 100)],
            ),
            # ── Cash Flow ─────────────────────────────────────────────────────
            SectorMetric(
                "fcf_to_pat", "FCF / PAT", 0.12, "high",
                "higher_is_better", "%",
                "IT should convert near 100% of PAT to FCF — low capex, negative working capital",
                thresholds=[(20, 15), (50, 35), (70, 55), (80, 68), (90, 82), (100, 93), (110, 100)],
            ),
            SectorMetric(
                "cfo_to_pat", "CFO / PAT", 0.08, "high",
                "higher_is_better", "%",
                "Operating cash conversion — should be >90% for IT services",
                thresholds=[(20, 10), (50, 30), (70, 52), (80, 68), (90, 82), (100, 92), (115, 100)],
            ),
            # ── Balance Sheet ─────────────────────────────────────────────────
            SectorMetric(
                "debt_to_equity", "Net Debt/Equity", 0.06, "medium",
                "lower_is_better", "x",
                "IT companies should be net-cash; D/E above 0.3x warrants scrutiny",
                thresholds=[(-1.0, 100), (0, 92), (0.2, 78), (0.5, 55), (0.8, 35), (1.2, 15), (2.0, 0)],
            ),
            # ── Valuation ─────────────────────────────────────────────────────
            SectorMetric(
                "pe_ratio", "P/E", 0.08, "medium",
                "neutral", "x",
                "Tier-1 IT typically 20-30x; mid-tier 15-22x",
                thresholds=[(0, 45), (10, 68), (18, 85), (25, 80), (32, 65), (45, 45), (65, 22), (100, 5)],
            ),
            SectorMetric(
                "ev_to_ebitda", "EV/EBITDA", 0.06, "medium",
                "neutral", "x",
                "Enterprise multiple — 12-20x typical for IT services",
                thresholds=[(0, 55), (8, 78), (12, 88), (18, 80), (24, 62), (32, 40), (45, 18)],
            ),
        ]

    def red_flag_rules(self) -> list[SectorRedFlag]:
        return [
            SectorRedFlag(
                condition="ebit_margin < 12",
                severity="HIGH",
                title="Very Low EBIT Margin",
                description="EBIT margin below 12% for an IT services company indicates severe pricing pressure or wage cost inflation.",
            ),
            SectorRedFlag(
                condition="ebit_margin < 16",
                severity="MEDIUM",
                title="Below-Par EBIT Margin",
                description="EBIT margin 12-16% is below industry norm — needs recovery or risks market share loss to lower-cost peers.",
            ),
            SectorRedFlag(
                condition="attrition_rate > 22",
                severity="HIGH",
                title="Very High Attrition",
                description="Attrition above 22% disrupts delivery, raises hiring costs, and signals talent flight — clients may get nervous.",
            ),
            SectorRedFlag(
                condition="attrition_rate > 18",
                severity="MEDIUM",
                title="Elevated Attrition",
                description="Attrition 18-22% is elevated — watch for talent cost inflation and project delivery risks.",
            ),
            SectorRedFlag(
                condition="fcf_to_pat < 60",
                severity="HIGH",
                title="Low Cash Conversion for IT",
                description="FCF/PAT below 60% for an asset-light IT company is very low — suggests working capital issues or aggressive capitalization.",
            ),
            SectorRedFlag(
                condition="revenue_cagr_3y < 5",
                severity="HIGH",
                title="Weak Revenue Growth",
                description="Revenue CAGR below 5% for an IT services company signals client losses, pricing pressure, or vertical slowdown.",
            ),
            SectorRedFlag(
                condition="client_concentration_top10 > 50",
                severity="MEDIUM",
                title="High Client Concentration",
                description="Top-10 clients above 50% of revenue creates significant revenue concentration risk.",
            ),
            SectorRedFlag(
                condition="debt_to_equity > 0.5",
                severity="MEDIUM",
                title="Unusual Leverage for IT",
                description="D/E above 0.5x is unusual for an IT company — investigate if due to acquisitions or operational issues.",
            ),
        ]

    def _compute_special_metric(self, name: str, metrics: dict, data: dict) -> float | None:
        if name == "revenue_per_employee":
            employees = (data.get("company_info") or {}).get("employees")
            revenue_series = (data.get("income") or {}).get("revenue") or {}
            if not employees or employees <= 0:
                return None
            latest_revenue = None
            for yr in sorted(revenue_series.keys(), reverse=True):
                v = revenue_series[yr]
                if v is not None:
                    latest_revenue = v
                    break
            if latest_revenue is None:
                return None
            # revenue is in absolute INR/USD; convert to USD thousands proxy
            # revenue_per_employee in USD k = revenue_M / employees * 1000
            revenue_m = latest_revenue / 1e6  # absolute → millions
            return round(revenue_m / employees * 1000, 1)
        return None

    def _check_rule(self, rule: SectorRedFlag, metrics: dict, data: dict) -> bool:
        cond = rule.condition
        if cond == "ebit_margin < 12":
            v = metrics.get("ebit_margin"); return v is not None and v < 12
        if cond == "ebit_margin < 16":
            v = metrics.get("ebit_margin"); return v is not None and 12 <= v < 16
        if cond == "attrition_rate > 22":
            v = metrics.get("attrition_rate"); return v is not None and v > 22
        if cond == "attrition_rate > 18":
            v = metrics.get("attrition_rate"); return v is not None and 18 <= v <= 22
        if cond == "fcf_to_pat < 60":
            v = metrics.get("fcf_to_pat"); return v is not None and v < 60
        if cond == "revenue_cagr_3y < 5":
            v = metrics.get("revenue_cagr_3y"); return v is not None and v < 5
        if cond == "client_concentration_top10 > 50":
            v = metrics.get("client_concentration_top10"); return v is not None and v > 50
        if cond == "debt_to_equity > 0.5":
            v = metrics.get("debt_to_equity"); return v is not None and v > 0.5
        return False
