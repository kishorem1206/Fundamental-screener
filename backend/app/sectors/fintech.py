"""
Before adding sector-specific annual-report or quarterly-report note
extraction for this sector, check the two dedicated extraction engines'
Area Registries first — app/ingestion/annual_report_ingestion.py and
app/ingestion/quarterly_results_client.py (see also "Important md
files/Annual_Report_Fetching_Extraction_Engine.md" and
".../Quarterly_Report_Fetching_Extraction_Engine.md") — an existing
area may already cover what this sector needs.

Fintech sector framework — Financial_Services_Analysis_Framework.md §10.
Payments, digital lending, wealthtech, insurtech, financial marketplaces,
embedded finance. Asset-light, volume/take-rate driven — GTV/TPV growth and
take rate matter more than revenue growth alone: a fintech growing volume
without monetizing it, or growing revenue only via take-rate expansion on a
shrinking base, needs different scrutiny than a traditional company (spec's
own closing line for this section: "A high-growth fintech should not be
evaluated using revenue CAGR alone").

Built 2026-09-17 — previously every fintech (Pine Labs, PB Fintech, etc.)
fell through to GenericSector's 10 universal metrics, since no dedicated
framework existed (confirmed via a live gap-analysis audit against the spec
this same day). `gtv_growth`/`take_rate`/`contribution_margin`/
`merchant_count` are genuinely disclosed by fintech companies (confirmed
live on Pine Labs' own concall transcript and annual report — GTV growth,
take-rate commentary, and merchant terminology all present) but have no
structured-API source (not on yfinance, not on Screener) — they're sourced
via `app/ingestion/earnings_call_client.py`'s LLM extraction over the
company's own earnings-call transcript, the same mechanism already built
for IT Services' attrition_rate/utilization_rate/deal_wins_tcv.
"""
from __future__ import annotations
from app.sectors.base import SectorFramework, SectorMetric, SectorRedFlag


class FintechSector(SectorFramework):
    sector_name = "Fintech"
    sector_aliases = [
        "Financial Technology (Fintech)", "Fintech", "Payments",
        "Digital Lending", "Wealthtech", "Insurtech", "Fintech Platform",
    ]

    SECTOR_WEIGHTS = {
        "growth": 0.29,
        "profitability": 0.21,
        "cash_flow": 0.25,
        "balance_sheet": 0.12,
        "efficiency": 0.03,
        "valuation": 0.10,
    }

    def key_metrics(self) -> list[SectorMetric]:
        return [
            # ── Growth ────────────────────────────────────────────────────────
            SectorMetric(
                "revenue_cagr_3y", "Revenue CAGR (3Y)", 0.10, "medium",
                "higher_is_better", "%",
                "Revenue 3Y CAGR — a secondary growth signal here; can be inflated by take-rate "
                "changes alone, so read alongside GTV/TPV growth, not instead of it",
                thresholds=[(0, 10), (5, 25), (15, 45), (25, 62), (40, 78), (60, 90), (80, 100)],
            ),
            SectorMetric(
                "gtv_growth", "GTV / TPV Growth", 0.15, "high",
                "higher_is_better", "%",
                "Gross/Total Payment Value growth — the core volume metric for a payments-driven "
                "fintech; revenue growth alone can mask take-rate compression or expansion",
                thresholds=[(0, 10), (10, 30), (20, 50), (35, 68), (50, 82), (70, 92), (100, 100)],
                available_from_yfinance=False,
                na_message="GTV/TPV growth is disclosed in earnings-call commentary or the annual "
                            "report's business overview, not in standard financial statements.",
            ),
            # ── Monetization / Profitability ────────────────────────────────────
            SectorMetric(
                "take_rate", "Take Rate", 0.15, "high",
                "higher_is_better", "bps",
                "Revenue as a share of GTV/TPV processed — monetization intensity. Rising GTV with "
                "falling take rate means the business is growing volume, not value",
                thresholds=[(10, 15), (25, 35), (40, 55), (60, 70), (90, 82), (120, 92), (160, 100)],
                available_from_yfinance=False,
                na_message="Take rate is disclosed in earnings-call management commentary, not in "
                            "standard financial statements.",
            ),
            SectorMetric(
                "contribution_margin", "Contribution Margin", 0.12, "high",
                "higher_is_better", "%",
                "Revenue minus variable/processing costs, before fixed opex — shows whether the "
                "core unit economics work before overhead is even considered",
                thresholds=[(0, 15), (10, 32), (20, 50), (30, 66), (40, 80), (50, 90), (65, 100)],
                available_from_yfinance=False,
                na_message="Contribution margin is disclosed in earnings-call commentary, not in "
                            "standard financial statements.",
            ),
            SectorMetric(
                "ebitda_margin", "EBITDA Margin", 0.12, "medium",
                "higher_is_better", "%",
                "Many fintechs run thin or negative EBITDA margins early on — read as a trend, not "
                "a single-period pass/fail",
                thresholds=[(-20, 10), (-5, 30), (5, 50), (15, 68), (25, 82), (35, 92), (45, 100)],
            ),
            SectorMetric(
                "pat_margin", "PAT Margin", 0.08, "medium",
                "higher_is_better", "%",
                thresholds=[(-15, 10), (-5, 28), (0, 45), (5, 60), (10, 75), (18, 88), (25, 100)],
            ),
            # ── Scale (informational — no universal threshold across company sizes) ─
            SectorMetric(
                "merchant_count", "Merchant / Client Count", 0.03, "low",
                "higher_is_better", "count",
                "Active merchant or client base — the demand-side scale driver. No scored "
                "threshold (absolute counts aren't comparable across company sizes); shown for "
                "context and trend only.",
                available_from_yfinance=False,
                na_message="Merchant/client count is disclosed in earnings-call commentary or the "
                            "annual report, not in standard financial statements.",
            ),
            # ── Cash generation ──────────────────────────────────────────────────
            SectorMetric(
                "fcf_to_pat", "FCF/PAT", 0.10, "high",
                "higher_is_better", "%",
                "Free cash flow conversion — persistent negative FCF alongside growth claims "
                "is the fintech version of a red flag banks would call weak asset quality",
                thresholds=[(-50, 10), (0, 30), (30, 50), (60, 70), (90, 85), (120, 95), (150, 100)],
            ),
            SectorMetric(
                "cfo_to_pat", "CFO/PAT", 0.08, "medium",
                "higher_is_better", "%",
                thresholds=[(-50, 10), (0, 30), (40, 55), (70, 72), (100, 85), (130, 95), (160, 100)],
            ),
            SectorMetric(
                "roe", "ROE", 0.07, "medium",
                "higher_is_better", "%",
                "Many fintechs are pre-profitability or newly profitable — a low/negative ROE is "
                "expected at this stage, not automatically a red flag",
                thresholds=[(-10, 10), (0, 25), (5, 42), (10, 58), (15, 72), (22, 88), (30, 100)],
            ),
        ]

    def red_flag_rules(self) -> list[SectorRedFlag]:
        return [
            SectorRedFlag(
                condition="contribution_margin < 0",
                severity="HIGH",
                title="Negative Contribution Margin",
                description="Revenue doesn't even cover variable/processing costs before fixed "
                             "opex — the core unit economics don't work yet, independent of scale.",
            ),
            SectorRedFlag(
                condition="gtv_growth_outpacing_revenue",
                severity="MEDIUM",
                title="GTV/TPV Growth Outpacing Revenue Growth",
                description="Volume is growing meaningfully faster than revenue — consistent with "
                             "take-rate compression (growing volume without growing value) rather "
                             "than genuine monetization improvement.",
            ),
            SectorRedFlag(
                condition="fcf_to_pat < -20",
                severity="HIGH",
                title="Persistent Cash Burn",
                description="FCF running well below PAT (or PAT itself negative with cash burn) — "
                             "check funding runway and dilution history before extrapolating growth.",
            ),
            SectorRedFlag(
                condition="debt_to_equity > 1.0",
                severity="MEDIUM",
                title="Unusual Leverage for an Asset-Light Model",
                description="Fintechs are typically asset-light and should carry low leverage — "
                             "D/E above 1.0x warrants checking whether debt is funding a lending "
                             "book (a different risk profile) or plugging an operating cash gap.",
            ),
        ]

    def _check_rule(self, rule: SectorRedFlag, metrics: dict, data: dict) -> bool:
        # `metrics` here already has ledger-bridged values merged in by
        # SectorFramework.identify_risks() (base.py) — gtv_growth included.
        if rule.condition == "gtv_growth_outpacing_revenue":
            gtv = metrics.get("gtv_growth")
            rev = metrics.get("revenue_cagr_3y")
            if gtv is None or rev is None:
                return False
            return (gtv - rev) > 20
        return super()._check_rule(rule, metrics, data)
