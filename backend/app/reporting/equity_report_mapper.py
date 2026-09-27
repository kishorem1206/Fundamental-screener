"""Maps this app's existing analysis data into the `EquityReport` JSON
contract consumed by the Node/PDFKit renderer at `pdf-renderer/` (ported
from the user's Replit "equity-pdf-renderer" project, 2026-09-15). One
function, reused for every sector — the renderer's `keyMetrics`/
`businessFacts` are a flat, sector-agnostic `Metric[]`, and this app already
computes exactly that shape per sector via `sector_analysis["key_metrics"]`
(each sector framework — including "Banks" — returns its own metric list),
so bank-specific ratios (NIM, GNPA/NNPA, CASA, CAR) flow through with no
special-casing, same as any other sector's ratios.

Deliberately narrower than the old ReportLab/Jinja renderers: the target
`EquityReport` contract has no slot for concall highlights, the change log,
brand portfolio tables, or a peer relative-performance chart — matching the
Replit renderer's actual sections exactly (the user's explicit ask) means
those simply aren't mapped here, not that they were forgotten.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

from sqlalchemy.orm import Session

_STATUS_TO_SEVERITY = {
    "EXCELLENT": "positive", "GOOD": "positive",
    "FAIR": "warning", "POOR": "negative", "N/A": "neutral",
}

_ACRONYMS = {"Roe": "ROE", "Roa": "ROA", "Roce": "ROCE", "Roic": "ROIC", "Ebitda": "EBITDA",
             "Eps": "EPS", "Pat": "PAT", "Pbt": "PBT", "Cagr": "CAGR", "Fcf": "FCF", "Yoy": "YoY",
             "Opm": "OPM", "Npm": "NPM", "Gpm": "GPM", "Pe": "P/E", "Pb": "P/B", "Cfo": "CFO",
             "Nim": "NIM", "Npa": "NPA", "Casa": "CASA", "Car": "CAR"}

# Matches source_ledger.py's own tier hierarchy (1 = regulatory/exchange
# filing, 2 = high-quality secondary aggregator, 3 = context/industry) —
# the PDF's static Sources table has no hover/legend like the frontend's,
# so a bare "1"/"2"/"3" reads as meaningless; spell out what it ranks.
_TIER_LABEL = {1: "Primary", 2: "Secondary", 3: "Tertiary"}

# Screener.in's own scraped "about"/description text carries inline
# footnote markers ("...accessories.[1].") referencing ITS OWN source list,
# which is meaningless once quoted into this report — strip them rather
# than let a bare "[1]" appear with nothing for it to point to.
_CITATION_DOT_RE = re.compile(r"\.\[\d{1,3}(?:\s*,\s*\d{1,3})*\]\.?")
_CITATION_RE = re.compile(r"\s*\[\d{1,3}(?:\s*,\s*\d{1,3})*\]")


def _readable(flag: str) -> str:
    words = flag.replace("_", " ").title().split()
    return " ".join(_ACRONYMS.get(w, w) for w in words)


_RISK_IMPACT_SCORE = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}

# PDF Upgrade plan, Priority 2 #8 — maps ManagementGuidance.status
# (models.py's own vocabulary) onto the doc's suggested ahead/on-track/
# below/qualitative framing for the guidance status matrix.
_GUIDANCE_STATUS_LABEL = {
    "ACHIEVED": "Ahead", "UPGRADED": "Ahead",
    "REITERATED": "On track", "NEW": "On track",
    "PARTIALLY_ACHIEVED": "Partial",
    "MISSED": "Below", "DOWNGRADED": "Below",
    "WITHDRAWN": "Withdrawn",
}
_GUIDANCE_STATUS_TONE = {
    "ACHIEVED": "positive", "UPGRADED": "positive",
    "REITERATED": "neutral", "NEW": "neutral",
    "PARTIALLY_ACHIEVED": "warning",
    "MISSED": "negative", "DOWNGRADED": "negative",
    "WITHDRAWN": "neutral",
}


def _risk_heatmap(risks: list[dict]) -> list[dict] | None:
    """PDF Upgrade plan, Priority 2 #10 — impact x probability matrix
    instead of a flat list. Both axes are real, already-computed signals
    (`orchestrator.py::_identify_universal_risks`'s own `severity` and
    `confidence` fields), not invented precision: `severity` (HIGH/MEDIUM/
    LOW) becomes the impact axis, `confidence` (an existing 0-1 float this
    app already attaches to every risk) becomes the probability axis. The
    doc's own suggested category taxonomy (valuation compression,
    execution, capital efficiency, etc.) isn't force-fit — each risk keeps
    its own already-assigned `category` field, just human-readable."""
    if not risks:
        return None
    points = []
    for r in risks[:12]:
        severity = (r.get("severity") or "MEDIUM").upper()
        confidence = r.get("confidence")
        points.append({
            "label": r.get("title") or "Risk",
            "category": _readable(r.get("category")) if r.get("category") else "Other",
            "impact": _RISK_IMPACT_SCORE.get(severity, 2),
            "probabilityPct": round(confidence * 100) if confidence is not None else 50,
            "severity": severity,
        })
    return points or None


def _pdf_safe(text: str | None) -> str | None:
    """PDFKit's standard-14 fonts use WinAnsiEncoding (cp1252) — a superset
    of ASCII that already covers em/en dashes, smart quotes, ellipsis and
    bullet natively (confirmed rendering correctly in the vendor's own
    sample), unlike ReportLab's stricter Latin-1-only default. Only true
    outliers (₹, non-Latin scripts, emoji) need handling — encode/decode
    through cp1252 drops exactly those, never guesses at a replacement."""
    if not text:
        return text
    text = _CITATION_DOT_RE.sub(".", text)
    text = _CITATION_RE.sub("", text)
    return text.encode("cp1252", errors="ignore").decode("cp1252")


def _severity_for(status: str | None) -> str:
    return _STATUS_TO_SEVERITY.get((status or "N/A").upper(), "neutral")


# ai_analysis list fields (bull_case/bear_case/monitoring_points) occasionally
# come back from the LLM with a malformed nested-JSON artifact leaking in as
# its own list item (e.g. a stray "bear_case" key name) rather than a clean
# prose bullet — found live on Maruti's bull case ("...enabling flexible
# investment", "bear_case"). `app/reporting/data_builder.py` (the banking
# report's builder) already has this exact filter under the same name; not
# imported from there to avoid coupling this universal mapper to the
# banking-only module's dependencies for one small pure-string helper.
_KNOWN_AI_ARTIFACT_TOKENS = {
    "bull_case", "bear_case", "key_risks", "key_catalysts", "monitoring_points",
    "investment_thesis", ":", "",
}


def _clean_ai_points(items: list) -> list[str]:
    cleaned = []
    for item in items or []:
        text = str(item).strip()
        if not text or text in _KNOWN_AI_ARTIFACT_TOKENS:
            continue
        if text.startswith("[") and text.endswith("]"):
            continue
        cleaned.append(text)
    return cleaned


def _sentiment_severity(sentiment: str | None) -> str:
    s = (sentiment or "").upper()
    if s == "BUY":
        return "positive"
    if s == "SELL":
        return "negative"
    if s == "HOLD":
        return "warning"
    return "neutral"


def _short_date(iso: str | None) -> str | None:
    """"2026-09-14" -> "14 Sep '26" — the sources table's date-range column
    wraps awkwardly with full ISO date-to-date strings (the vendor's
    `compactLabel` truncation heuristic is character-count-based, not exact
    glyph measurement, so it under-truncates a string this long); the demo
    data it was built against only ever had single short dates."""
    if not iso:
        return None
    try:
        d = datetime.fromisoformat(iso[:10])
        return d.strftime("%-d %b '%y")
    except ValueError:
        return iso[:10]


def _fiscal_label(period: str) -> str:
    if period == "TTM":
        return "TTM"
    m = re.search(r"(\d{4})", period)
    return f"FY{m.group(1)[2:]}" if m else period


def _company_market(analysis, live_price: dict | None) -> tuple[dict, dict]:
    company = analysis.company_info or {}
    market = (analysis.financial_data or {}).get("market") or {}
    price = (live_price or {}).get("price")
    if price is None:
        price = market.get("current_price") or company.get("current_price")
    change_pct = (live_price or {}).get("change_pct")
    market_cap = company.get("market_cap") or market.get("market_cap")
    company_out = {
        "name": company.get("company_name") or "Unknown Company",
        "ticker": company.get("symbol") or "",
        "exchange": company.get("exchange") or "",
        "sector": company.get("sector") or "",
        "asOf": datetime.now(timezone.utc).strftime("%d %B %Y"),
        "analystName": "Fundamental Equity Research",
    }
    market_out = {
        "price": float(price) if price is not None else None,
        "currency": "INR",
        "changePct": float(change_pct) if change_pct is not None else None,
        "marketCapCr": float(market_cap) / 1e7 if market_cap else None,
        "pe": None,
        "week52Low": float(market["week52_low"]) if market.get("week52_low") is not None else None,
        "week52High": float(market["week52_high"]) if market.get("week52_high") is not None else None,
    }
    return company_out, market_out


def _key_metrics(sector_analysis: dict) -> list[dict]:
    out = []
    for m in sector_analysis.get("key_metrics") or []:
        if not m.get("available") or m.get("value") is None:
            continue
        out.append({
            "label": m.get("label") or m.get("name"),
            "value": m["value"],
            "unit": m.get("unit") or "",
            "severity": _severity_for(m.get("status")),
        })
    return out


def _score_breakdown(scores: dict) -> list[dict]:
    order = [("growth", "Growth"), ("profitability", "Profitability"), ("cash_flow", "Cash flow"),
             ("balance_sheet", "Balance sheet"), ("efficiency", "Efficiency"), ("valuation", "Valuation")]
    out = []
    for key, label in order:
        val = scores.get(key)
        if val is None:
            continue
        v = float(val)
        severity = "positive" if v >= 65 else "warning" if v >= 40 else "negative"
        out.append({"label": label, "score": round(v), "severity": severity})
    return out


def _financials(pnl: dict) -> dict | None:
    fiscal_years = pnl.get("fiscal_years") or []
    if not fiscal_years:
        return None
    table = pnl.get("table") or {}
    years = fiscal_years[-6:]
    combo_years = fiscal_years[-10:]

    def series(key: str, name: str, color: str | None = None) -> dict | None:
        vals = table.get(key) or {}
        pts = [{"label": _fiscal_label(y), "value": vals[y]} for y in years if vals.get(y) is not None]
        if len(pts) < 2:
            return None
        out = {"name": name, "points": pts}
        if color:
            out["color"] = color
        return out

    revenue_series = series("sales", "Revenue")
    profit_series = series("operating_profit", "Operating profit", "#c28b32")
    margin_series = series("opm", "OPM")

    # PDF Upgrade plan, Priority 2 #1 — ONE coordinated chart (columns =
    # revenue, line = operating margin, thin line = operating profit)
    # replacing the two separate revenue/profit and margin charts, with a
    # callout stating the 5Y revenue CAGR and latest margin so the reader
    # isn't left to infer "is growth translating into operating leverage?"
    # from raw lines alone.
    revenue_margin_combo = None
    combo_sales = table.get("sales") or {}
    combo_opm = table.get("opm") or {}
    combo_op_profit = table.get("operating_profit") or {}
    combo_bar_pts = [{"label": _fiscal_label(y), "value": combo_sales[y]} for y in combo_years if combo_sales.get(y) is not None]
    combo_opm_pts = [{"label": _fiscal_label(y), "value": combo_opm[y]} for y in combo_years if combo_opm.get(y) is not None]
    combo_profit_pts = [{"label": _fiscal_label(y), "value": combo_op_profit[y]} for y in combo_years if combo_op_profit.get(y) is not None]
    if len(combo_bar_pts) >= 2 and len(combo_opm_pts) >= 2:
        combo_lines = [{"name": "Operating margin", "points": combo_opm_pts, "color": "#4e8d72"}]
        if len(combo_profit_pts) >= 2:
            combo_lines.append({"name": "Operating profit", "points": combo_profit_pts, "color": "#c28b32"})
        sales_cagr_5y = (pnl.get("growth") or {}).get("sales_cagr", {}).get("5y")
        latest_margin = next((combo_opm[y] for y in reversed(combo_years) if combo_opm.get(y) is not None), None)
        callout_parts = []
        if sales_cagr_5y is not None:
            callout_parts.append(f"Revenue grew at a {sales_cagr_5y:.1f}% 5-year CAGR")
        if latest_margin is not None:
            callout_parts.append(f"latest operating margin is {latest_margin:.1f}%")
        revenue_margin_combo = {
            "bar": {"name": "Revenue", "points": combo_bar_pts},
            "lines": combo_lines,
            "callout": " while ".join(callout_parts) + "." if callout_parts else None,
        }

    cols = [_fiscal_label(y) for y in years]
    rows_spec = [("Sales", "sales", True), ("Operating profit", "operating_profit", False),
                 ("OPM", "opm", False), ("Net profit", "net_profit", False), ("EPS", "eps", False)]
    table_rows = []
    for label, key, highlight in rows_spec:
        vals = table.get(key) or {}
        if not any(vals.get(y) is not None for y in years):
            continue
        row = {"label": label, "values": [vals.get(y) for y in years]}
        if highlight:
            row["highlight"] = True
        table_rows.append(row)

    financials: dict = {}
    if revenue_margin_combo:
        financials["revenueMarginCombo"] = revenue_margin_combo
    elif revenue_series:
        # Fall back to the old two-chart view only when there isn't enough
        # margin history to build the consolidated combo chart — never
        # silently drop the revenue trend entirely.
        financials["revenueSeries"] = revenue_series
        if profit_series:
            financials["profitSeries"] = profit_series
        if margin_series:
            financials["marginSeries"] = [margin_series]
    if table_rows:
        financials["table"] = {
            "title": "P&L history",
            "subtitle": "Consolidated financial history — values normalized to Rs. Cr",
            "columns": cols,
            "rows": table_rows,
        }
    flags = [_readable(f) for f in (pnl.get("red_flags") or [])]
    positives = [_readable(f) for f in (pnl.get("positive_signals") or [])]
    if flags:
        financials["flags"] = flags
    if positives:
        financials["positives"] = positives
    return financials or None


def _ownership(db: Session, company_id: str) -> dict | None:
    from app.infrastructure.database.models import Shareholding, ShareholdingScreener

    nse_rows = (db.query(Shareholding).filter_by(company_id=company_id)
                .order_by(Shareholding.period_end.desc()).limit(6).all())
    screener_rows = (db.query(ShareholdingScreener).filter_by(company_id=company_id, frequency="quarterly")
                      .order_by(ShareholdingScreener.period_end.desc()).limit(20).all())
    if not nse_rows and not screener_rows:
        return None

    ownership: dict = {}
    if screener_rows:
        latest = screener_rows[0]
        ownership["mix"] = [
            {"label": "Promoter", "value": float(latest.promoter_pct), "unit": "%"}
            if latest.promoter_pct is not None else None,
            {"label": "FII", "value": float(latest.fii_pct), "unit": "%"}
            if latest.fii_pct is not None else None,
            {"label": "DII", "value": float(latest.dii_pct), "unit": "%"}
            if latest.dii_pct is not None else None,
            {"label": "Public", "value": float(latest.public_pct), "unit": "%"}
            if latest.public_pct is not None else None,
        ]
        ownership["mix"] = [m for m in ownership["mix"] if m is not None]
        chart_rows = list(reversed(screener_rows))
        trend = []
        for r in chart_rows:
            point: dict = {"label": r.period_end}
            if r.promoter_pct is not None:
                point["promoter"] = float(r.promoter_pct)
            if r.fii_pct is not None:
                point["fii"] = float(r.fii_pct)
            if r.dii_pct is not None:
                point["dii"] = float(r.dii_pct)
            if r.public_pct is not None:
                point["public"] = float(r.public_pct)
            trend.append(point)
        if len(trend) >= 2:
            ownership["trend"] = trend

    if nse_rows:
        latest_nse = nse_rows[0]
        pledge_val = float(latest_nse.pledge_pct) if latest_nse.pledge_pct is not None else None
        ownership["pledgeStatus"] = (
            f"{pledge_val:.1f}% of promoter holding pledged (as of {latest_nse.period_end})"
            if pledge_val and pledge_val > 0 else "No pledge reported"
        )
        ownership["table"] = {
            "title": "Shareholding history",
            "subtitle": "NSE quarterly XBRL filings — the only source with pledge data",
            "columns": ["Promoter %", "Public %", "Pledge %"],
            "rows": [
                {"label": r.period_end, "values": [
                    float(r.promoter_pct) if r.promoter_pct is not None else None,
                    float(r.public_pct) if r.public_pct is not None else None,
                    float(r.pledge_pct) if r.pledge_pct is not None else None,
                ]}
                for r in nse_rows
            ],
        }
    return ownership or None


def _market_intelligence(db: Session, company_id: str) -> dict | None:
    from app.infrastructure.database.models import (
        AnalystConsensus, ForwardEstimate, EarningsCalendar, CompanyNews,
    )

    ac_rows = db.query(AnalystConsensus).filter_by(company_id=company_id).all()
    cal_row = db.query(EarningsCalendar).filter_by(company_id=company_id).first()
    news_rows = (db.query(CompanyNews).filter_by(company_id=company_id)
                 .order_by(CompanyNews.published_at.desc()).limit(10).all())
    if not ac_rows and not cal_row and not news_rows:
        return None

    mi: dict = {}
    if ac_rows:
        mi["consensus"] = [
            {
                "source": r.source,
                "sentiment": (r.sentiment or "N/A").upper(),
                "target": float(r.target_price_mean) if r.target_price_mean is not None else None,
                "impliedUpsidePct": float(r.implied_upside_pct) if r.implied_upside_pct is not None else None,
            }
            for r in ac_rows
        ]
    if cal_row and cal_row.next_earnings_date:
        mi["earningsCalendar"] = f"Next earnings: {cal_row.next_earnings_date}"
    if news_rows:
        mi["news"] = [
            {
                "date": r.published_at.strftime("%d %b %Y") if r.published_at else "",
                "headline": _pdf_safe(r.headline) or "",
                "source": r.provider or "",
                # PDF Upgrade plan, Priority 2 #9 — a keyword heuristic,
                # not a claim of precise editorial categorization (this app
                # has no structured event-type field on CompanyNews);
                # "Price" is the honest fallback when no keyword matches,
                # not a guess dressed up as a real category.
                "category": _classify_news(r.headline),
            }
            for r in news_rows
        ]
    return mi or None


_NEWS_CATEGORY_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("Capital Allocation", ("dividend", "buyback", "bonus", "rights issue", "fundraise", "qip", "preferential", "stake sale")),
    ("Regulation", ("sebi", "rbi", "court", "regulatory", "penalty", "compliance", "tribunal", "ministry", "notice")),
    ("Governance", ("board", "resign", "appoint", "director", " ceo", " cfo", "independent director", "audit committee", "management change")),
    ("Operations", ("plant", "launch", "production", "capacity", "expansion", "factory", "acquisition", "merger", "partnership", "contract", "order win")),
]


def _classify_news(headline: str) -> str:
    lower = (headline or "").lower()
    for label, keywords in _NEWS_CATEGORY_KEYWORDS:
        if any(kw in lower for kw in keywords):
            return label
    return "Price"


def _business_segments(db: Session, company_id: str) -> list[dict] | None:
    from app.infrastructure.database.models import BusinessSegment

    rows = db.query(BusinessSegment).filter_by(company_id=company_id).all()
    if not rows:
        return None
    latest_year = max(r.fiscal_year for r in rows)
    latest = [r for r in rows if r.fiscal_year == latest_year]
    total = sum(float(r.revenue) for r in latest)
    if total <= 0:
        return None
    latest.sort(key=lambda r: r.revenue, reverse=True)
    year_match = re.search(r"(\d{4})", latest_year)
    year_label = f"FY{year_match.group(1)[2:]}" if year_match else latest_year
    return [
        {
            "name": r.segment_name,
            "sharePct": round(float(r.revenue) / total * 100, 1),
            "summary": f"Rs. {float(r.revenue):,.0f} Cr revenue in {year_label} "
                       f"({float(r.revenue) / total * 100:.1f}% of total).",
        }
        for r in latest[:6]
    ]


_SEGMENT_MIX_TOP_N = 5  # + one "Other" bucket = 6, matching the chart's 6-color palette


def _segment_mix_by_year(db: Session, company_id: str) -> list[dict] | None:
    """PDF Upgrade plan, Priority 2 #2 — revenue mix BY YEAR (the existing
    `_business_segments()` above stays the latest-year-only donut input;
    this is the companion 100%-stacked-by-year view, "avoid a pie when the
    objective is to compare multiple periods").

    Real bug found live-testing Maruti: picking each year's own top-6
    segments independently lets the SET of segment names differ year to
    year (a company can report a new minor line item, or an old one can
    drop below the cutoff) — the union across 6 years exceeded the chart's
    6-color palette and overflowed its legend. Fixed by choosing ONE fixed
    set of tracked names (the latest year's top N, the most relevant to a
    reader) and bucketing every other segment, in every year, into
    "Other" — segment identity and color now stay stable across the whole
    chart regardless of how the underlying reporting has drifted."""
    from app.infrastructure.database.models import BusinessSegment

    rows = db.query(BusinessSegment).filter_by(company_id=company_id).all()
    if not rows:
        return None
    years = sorted({r.fiscal_year for r in rows}, key=_year_sort_key)[-6:]
    if not years:
        return None
    latest_year = years[-1]
    latest_rows = sorted((r for r in rows if r.fiscal_year == latest_year), key=lambda r: r.revenue, reverse=True)
    tracked_names = [r.segment_name for r in latest_rows[:_SEGMENT_MIX_TOP_N]]

    periods = []
    for year in years:
        year_rows = [r for r in rows if r.fiscal_year == year]
        if not year_rows:
            continue
        year_match = re.search(r"(\d{4})", year)
        label = f"FY{year_match.group(1)[2:]}" if year_match else year
        by_name = {r.segment_name: float(r.revenue) for r in year_rows}
        segments = [{"name": name, "value": by_name[name]} for name in tracked_names if by_name.get(name)]
        other_total = sum(v for k, v in by_name.items() if k not in tracked_names)
        if other_total > 0:
            segments.append({"name": "Other", "value": other_total})
        if segments:
            periods.append({"label": label, "segments": segments})
    return periods if len(periods) >= 2 else None


def _segment_growth(db: Session, company_id: str) -> list[dict] | None:
    """PDF Upgrade plan, Priority 2 #2 — latest-year YoY growth rate per
    segment. `growthPct: None` (not 0) for a segment with no prior-year
    figure to compare against — never a fabricated "0% growth"."""
    from app.infrastructure.database.models import BusinessSegment

    rows = db.query(BusinessSegment).filter_by(company_id=company_id).all()
    if not rows:
        return None
    years = sorted({r.fiscal_year for r in rows}, key=_year_sort_key)
    if len(years) < 2:
        return None
    latest_year, prior_year = years[-1], years[-2]
    latest = {r.segment_name: float(r.revenue) for r in rows if r.fiscal_year == latest_year}
    prior = {r.segment_name: float(r.revenue) for r in rows if r.fiscal_year == prior_year}
    ranked = sorted(latest.items(), key=lambda kv: kv[1], reverse=True)[:6]
    growth = []
    for name, value in ranked:
        prior_value = prior.get(name)
        growth_pct = round((value - prior_value) / prior_value * 100, 1) if prior_value else None
        growth.append({"label": name, "growthPct": growth_pct})
    return growth if any(g["growthPct"] is not None for g in growth) else None


def _segment_mix_callout(mix_periods: list[dict] | None, growth: list[dict] | None) -> str | None:
    """PDF Upgrade plan, Priority 4 "Explanations" — one-line takeaway
    naming the largest segment (from the latest mix period) and the
    fastest-growing segment (from the YoY growth list), so the chart isn't
    left to speak for itself. Returns None if either half can't be
    honestly determined rather than guessing."""
    largest = None
    if mix_periods:
        latest = mix_periods[-1]
        real_segments = [s for s in latest["segments"] if s["name"] != "Other"]
        if real_segments:
            top = max(real_segments, key=lambda s: s["value"])
            total = sum(s["value"] for s in latest["segments"])
            share_pct = top["value"] / total * 100 if total else None
            largest = f"{top['name']} is the largest segment" + (f" at {share_pct:.0f}% of revenue" if share_pct is not None else "")

    fastest = None
    if growth:
        grown = [g for g in growth if g["growthPct"] is not None]
        if grown:
            top_grower = max(grown, key=lambda g: g["growthPct"])
            if top_grower["growthPct"] > 0:
                fastest = f"{top_grower['label']} grew fastest at {top_grower['growthPct']:.0f}% YoY"

    if largest and fastest:
        return f"{largest}; {fastest}."
    if largest:
        return f"{largest}."
    if fastest:
        return f"{fastest}."
    return None


_CLIENT_CONCENTRATION_METRICS = [
    ("client_concentration_top10", "Top 10 Clients"),
    ("customer_concentration_top3", "Top 3 Customers"),
]


def _client_concentration(sector_analysis: dict) -> dict | None:
    """Only an aggregate ratio is ever ingested (IT Services/Auto
    Ancillaries/Electronics frameworks each define one) — never named
    per-client revenue shares, so this returns a single label+percentage
    for a 2-slice "concentration vs. rest" pie, not a fabricated breakdown
    of individual clients this app has no data for."""
    key_metrics = sector_analysis.get("key_metrics") or []
    by_name = {m.get("name"): m for m in key_metrics}
    for name, label in _CLIENT_CONCENTRATION_METRICS:
        m = by_name.get(name)
        if m and m.get("available") and isinstance(m.get("value"), (int, float)):
            return {"label": label, "pct": max(0.0, min(100.0, float(m["value"])))}
    return None


def _fmt(val, suffix: str = "", decimals: int = 1) -> str:
    if val is None:
        return "N/A"
    try:
        return f"{float(val):,.{decimals}f}{suffix}"
    except (TypeError, ValueError):
        return "N/A"


def _year_sort_key(y: str) -> str:
    m = re.search(r"(\d{4})", y)
    return m.group(1) if m else y


def _series_points(series_dict: dict, years: list[str], scale: float = 1.0) -> list[dict]:
    return [{"label": _fiscal_label(y), "value": series_dict[y] / scale} for y in years if series_dict.get(y) is not None]


# ── Financials tab: categorized Key Metrics with trend badges ──────────────
# Same authoritative 7-state trend enum the Overview tab uses (not the
# Financials tab's own weaker 3-state simplification) — this is the mapping
# already used once for the old ReportLab renderer's KPI grid.
_TREND_SEVERITY = {
    "STRONGLY_IMPROVING": "positive", "IMPROVING": "positive", "STABLE": "neutral",
    "DETERIORATING": "warning", "STRONGLY_DETERIORATING": "negative",
    "VOLATILE": "warning", "INSUFFICIENT_DATA": "neutral",
}
_TREND_LABEL_TEXT = {
    # Plain ASCII, not arrow glyphs — PDFKit's base-14 fonts use
    # WinAnsiEncoding (cp1252), which has no ↑/↓/→/⚡ codepoints; they
    # rendered as mojibake ("!'"). Color already encodes direction
    # (positive=green/negative=red/warning=orange), so the label doesn't
    # need a symbol on top of that.
    "STRONGLY_IMPROVING": "Strongly Improving", "IMPROVING": "Improving",
    "STABLE": "Stable", "DETERIORATING": "Deteriorating",
    "STRONGLY_DETERIORATING": "Strongly Deteriorating", "VOLATILE": "Volatile",
    "INSUFFICIENT_DATA": "N/A",
}

# (label, metric_key, unit, trend_key|None) per category — exact keys/
# grouping the Financials tab's `FinancialsSection.tsx` uses. Only 6 of these
# ~33 keys have a real trend field on `analysis.metrics` (confirmed by
# reading that component) — the rest render as plain values, never a
# fabricated trend.
_METRIC_GROUP_SPECS = [
    ("Growth", [
        ("Revenue CAGR 3Y", "revenue_cagr_3y", "%", None),
        ("Revenue CAGR 5Y", "revenue_cagr_5y", "%", None),
        ("EBITDA CAGR 3Y", "ebitda_cagr_3y", "%", None),
        ("PAT CAGR 3Y", "pat_cagr_3y", "%", None),
        ("PAT CAGR 5Y", "pat_cagr_5y", "%", None),
        ("EPS CAGR 3Y", "eps_cagr_3y", "%", None),
        ("FCF CAGR 3Y", "fcf_cagr_3y", "%", None),
    ]),
    ("Profitability", [
        ("Gross Margin", "gross_margin", "%", None),
        ("EBITDA Margin", "ebitda_margin", "%", "ebitda_margin_trend"),
        ("EBIT Margin", "ebit_margin", "%", None),
        ("PAT Margin", "pat_margin", "%", "pat_margin_trend"),
        ("ROE", "roe", "%", "roe_trend"),
        ("ROCE", "roce", "%", "roce_trend"),
        ("ROIC", "roic", "%", None),
    ]),
    ("Cash Flow & Balance Sheet", [
        ("CFO/PAT", "cfo_to_pat", "%", None),
        ("FCF/PAT", "fcf_to_pat", "%", "fcf_trend"),
        ("FCF Margin", "fcf_margin", "%", None),
        ("Debt/Equity", "debt_to_equity", "x", "debt_trend"),
        ("Net Debt/EBITDA", "net_debt_to_ebitda", "x", None),
        ("Interest Coverage", "interest_coverage", "x", None),
        ("Current Ratio", "current_ratio", "x", None),
    ]),
    ("Efficiency", [
        ("Asset Turnover", "asset_turnover", "x", None),
        ("Inventory Days", "inventory_days", "days", None),
        ("Receivable Days", "receivable_days", "days", None),
        ("Payable Days", "payable_days", "days", None),
        ("CapEx/Revenue", "capex_to_revenue", "%", None),
    ]),
    ("Valuation", [
        ("P/E", "pe_ratio", "x", None),
        ("Forward P/E", "forward_pe", "x", None),
        ("P/B", "pb_ratio", "x", None),
        ("EV/EBITDA", "ev_to_ebitda", "x", None),
        ("EV/Sales", "ev_to_sales", "x", None),
        ("FCF Yield", "fcf_yield", "%", None),
        ("Dividend Yield", "dividend_yield", "%", None),
    ]),
]


def _metric_groups(metrics: dict) -> list[dict]:
    groups = []
    for category, specs in _METRIC_GROUP_SPECS:
        items = []
        for label, key, unit, trend_key in specs:
            val = metrics.get(key)
            if val is None:
                continue
            entry: dict = {"label": label, "value": f"{val:.0f} days"} if unit == "days" else {"label": label, "value": float(val), "unit": unit}
            trend = metrics.get(trend_key) if trend_key else None
            if trend in _TREND_SEVERITY:
                entry["status"] = _TREND_LABEL_TEXT[trend]
                entry["severity"] = _TREND_SEVERITY[trend]
            items.append(entry)
        if items:
            groups.append({"category": category, "metrics": items})
    return groups


def _pnl_bridge(metrics: dict) -> list[dict] | None:
    """Revenue -> EBITDA -> PAT for the latest fiscal year all three exist
    for — same "common year" rule the frontend's `latestPnlBridge` uses.
    Sourced from `analysis.metrics`' own `*_series` fields (the same series
    the Overview tab's waterfall reads), not `pnl_engine`'s separately
    computed table, so this always agrees with what the app UI shows."""
    rev = metrics.get("revenue_series") or {}
    ebitda = metrics.get("ebitda_series") or {}
    pat = metrics.get("pat_series") or {}
    common = sorted(
        (y for y in rev if ebitda.get(y) is not None and pat.get(y) is not None and rev.get(y) is not None),
        key=_year_sort_key,
    )
    if not common:
        return None
    y = common[-1]
    return [
        {"label": f"Revenue ({_fiscal_label(y)})", "value": round(rev[y] / 1e7, 1)},
        {"label": "EBITDA", "value": round(ebitda[y] / 1e7, 1)},
        {"label": "PAT", "value": round(pat[y] / 1e7, 1)},
    ]


def _cash_flow_bridge(metrics: dict) -> dict | None:
    """PDF Upgrade plan, Priority 2 #3 — PAT -> CFO -> Free Cash Flow as a
    waterfall (Capex isn't its own bar: FCF = CFO + capex, capex already
    negative in the ledger, so the CFO->FCF connector already visually
    represents "minus capex" — same "only running totals are bars"
    convention the existing P&L bridge above uses), plus a 3-year mini-
    trend table making the cash-conversion story checkable at a glance."""
    pat = metrics.get("pat_series") or {}
    cfo = metrics.get("cfo_series") or {}
    fcf = metrics.get("fcf_series") or {}
    common = sorted((y for y in pat if cfo.get(y) is not None and fcf.get(y) is not None), key=_year_sort_key)
    if not common:
        return None
    latest = common[-1]
    recent = common[-3:]
    pat_latest, fcf_latest = pat[latest], fcf[latest]
    callout = None
    if pat_latest and pat_latest > 0:  # a negative/zero PAT denominator makes the ratio meaningless, not just weak
        conversion_pct = fcf_latest / pat_latest * 100
        strength = "strong" if conversion_pct >= 80 else "moderate" if conversion_pct >= 40 else "weak"
        callout = f"FCF/PAT conversion was {conversion_pct:.0f}% in {_fiscal_label(latest)} — {strength} cash conversion."
    return {
        "steps": [
            {"label": "PAT", "value": round(pat[latest] / 1e7, 1)},
            {"label": "CFO", "value": round(cfo[latest] / 1e7, 1)},
            {"label": "Free Cash Flow", "value": round(fcf[latest] / 1e7, 1)},
        ],
        "callout": callout,
        "table": {
            "title": f"{len(recent)}-year cash conversion trend",
            "columns": [_fiscal_label(y) for y in recent],
            "rows": [
                {"label": "PAT", "values": [round(pat[y] / 1e7, 1) if pat.get(y) is not None else None for y in recent]},
                {"label": "CFO", "values": [round(cfo[y] / 1e7, 1) if cfo.get(y) is not None else None for y in recent]},
                {"label": "Free Cash Flow", "values": [round(fcf[y] / 1e7, 1) if fcf.get(y) is not None else None for y in recent], "highlight": True},
            ],
        },
    }


def _working_capital_trend(metrics: dict) -> dict | None:
    """PDF Upgrade plan, Priority 2 #4 — inventory/receivable/payable days
    + cash-conversion cycle as one multi-line chart (all four already
    share a "days" unit, so a single shared scale is meaningful, unlike
    the revenue-vs-margin chart above). `payable_days_series` is newly
    exposed by `engine.py` for this (previously only its latest value was
    surfaced, matching inventory/receivable which already had series)."""
    inv = metrics.get("inventory_days_series") or {}
    rec = metrics.get("receivable_days_series") or {}
    pay = metrics.get("payable_days_series") or {}
    ccc = metrics.get("ccc_series") or {}
    years = sorted(set(inv) | set(rec) | set(pay) | set(ccc), key=_year_sort_key)[-8:]
    if len(years) < 2:
        return None

    def line(series: dict, name: str, color: str) -> dict | None:
        pts = _series_points(series, years)
        return {"name": name, "points": pts, "color": color} if len(pts) >= 2 else None

    series_list = [
        line(inv, "Inventory days", "#245b8e"),
        line(rec, "Receivable days", "#4e8d72"),
        line(pay, "Payable days", "#c28b32"),
        line(ccc, "Cash conversion cycle", "#b65755"),
    ]
    series_list = [s for s in series_list if s]
    if len(series_list) < 2:
        return None

    latest_year = years[-1]
    prior_year = years[-2] if len(years) > 1 else None
    annotation = None
    if prior_year and ccc.get(latest_year) is not None and ccc.get(prior_year) is not None:
        delta = ccc[latest_year] - ccc[prior_year]
        # A sub-1-day delta rounds to "0 days" below but a raw sign check
        # would still label it "lengthened"/"shortened" — self-contradictory
        # phrasing ("lengthened by 0 days"). Round first, then classify.
        rounded_delta = round(abs(delta))
        direction = "held steady" if rounded_delta == 0 else ("shortened" if delta < 0 else "lengthened")
        annotation = (
            f"Cash conversion cycle held steady in {_fiscal_label(latest_year)} vs. {_fiscal_label(prior_year)}."
            if direction == "held steady"
            else f"Cash conversion cycle {direction} by {rounded_delta:.0f} days in {_fiscal_label(latest_year)} vs. {_fiscal_label(prior_year)}."
        )
    return {"series": series_list, "annotation": annotation}


def _revenue_ebitda_margin_combo(metrics: dict) -> dict | None:
    rev = metrics.get("revenue_series") or {}
    margin = metrics.get("ebitda_margin_series") or {}
    years = sorted((y for y in rev if margin.get(y) is not None), key=_year_sort_key)[-8:]
    bar_pts = _series_points(rev, years, scale=1e7)
    line_pts = _series_points(margin, years)
    if len(bar_pts) < 2 or len(line_pts) < 2:
        return None
    return {"bar": {"name": "Revenue (Cr)", "points": bar_pts}, "lines": [{"name": "EBITDA Margin %", "points": line_pts}]}


def _sales_margins_combo(pnl: dict) -> dict | None:
    """Same source/formula as `app/routes/history_charts.py`'s
    `sales_and_margins` (kept deliberately in sync — same pnl_engine table,
    same NPM = net_profit/sales computation) — not re-derived independently."""
    table = pnl.get("table") or {}
    fiscal_years = pnl.get("fiscal_years") or []
    sales = table.get("sales") or {}
    opm = table.get("opm") or {}
    net_profit = table.get("net_profit") or {}
    years = [y for y in fiscal_years if sales.get(y) is not None][-10:]
    if len(years) < 2:
        return None
    bar_pts = [{"label": _fiscal_label(y), "value": sales[y]} for y in years]
    opm_pts = [{"label": _fiscal_label(y), "value": opm[y]} for y in years if opm.get(y) is not None]
    npm_pts = []
    for y in years:
        s, np_ = sales.get(y), net_profit.get(y)
        if s and np_ is not None:
            npm_pts.append({"label": _fiscal_label(y), "value": round(np_ / s * 100, 2)})
    lines = []
    if len(opm_pts) >= 2:
        lines.append({"name": "OPM %", "points": opm_pts})
    if len(npm_pts) >= 2:
        lines.append({"name": "NPM %", "points": npm_pts})
    if not lines:
        return None
    return {"bar": {"name": "Sales (Cr)", "points": bar_pts}, "lines": lines}


_PL_SCORE_COMPONENT_LABELS = {
    "M1": "M1 Sector Margin", "M2": "M2 Margin Headroom", "M3": "M3 Doubling Velocity",
    "M4": "M4 Earnings Quality", "M5": "M5 Structural Ratio",
}
_PL_VELOCITY_NOTES = {
    "PAT_FASTER": "PAT is compounding faster than revenue — suggests margin expansion / operating leverage.",
    "PAT_SLOWER": "PAT is compounding slower than revenue — suggests margin compression or cost pressure.",
    "ROUGHLY_SAME": "PAT and revenue are doubling at a similar pace — stable economics.",
}


def _pnl_intelligence(pli: dict) -> dict | None:
    """Maps `compute_pl_intelligence()`'s output (app/calculations/
    pl_intelligence/) into the PDF's `pnlIntelligence` section — additive
    and structurally parallel to `_financials(pnl)` above, reading the
    NEWER, separate P&L Analysis Engine rather than `pnl_engine.py`'s
    output (Stage 0 boundary: the two never mix)."""
    period = pli.get("period")
    if not period:
        return None
    # User's explicit instruction: the PDF renders CONSOLIDATED figures
    # only, never a silent STANDALONE substitute — `compute_pl_intelligence()`
    # itself DOES fall back to STANDALONE when a company has no CONSOLIDATED
    # `pnl_*` ledger data (a deliberate, separate "show something" choice
    # for the frontend/API), so the PDF mapper must gate on the ACTUAL
    # statement_type used, omitting this section entirely rather than
    # rendering standalone-sourced numbers unlabeled as if consolidated.
    #
    # This guard still holds when a company (confirmed live: Netweb
    # Technologies, Bandhan Bank) has NO consolidated data at all —
    # `compute_pl_intelligence()` now honestly reports `"CONSOLIDATED"` for
    # such companies (`single_statement_source: True`), since a
    # subsidiary-less company's standalone figures already ARE what its
    # consolidated figures would be. The section is included, correctly,
    # not omitted — the invariant this guard exists for ("never label
    # fallback data as consolidated") is satisfied one layer earlier now,
    # not weakened.
    if pli.get("statement_type") != "CONSOLIDATED":
        return None

    score = pli.get("score") or {}
    components = score.get("components") or {}
    score_components = [
        {"label": label, "value": components.get(key), "unit": ""}
        for key, label in _PL_SCORE_COMPONENT_LABELS.items()
        if components.get(key) is not None
    ]

    cascade_period = (pli.get("cascade") or {}).get(period, {})
    cascade_steps = [
        {"label": label, "value": cascade_period.get(key)}
        for key, label in (("revenue", "Revenue"), ("ebitda", "EBITDA"), ("ebit", "EBIT"), ("pbt", "PBT"), ("pat", "PAT"))
        if cascade_period.get(key) is not None
    ]

    margins = pli.get("margins") or {}
    margin_metrics = []
    if margins.get("ebitda_margin") is not None:
        margin_metrics.append({"label": "EBITDA Margin", "value": margins["ebitda_margin"], "unit": "%"})
    if margins.get("pat_margin") is not None:
        margin_metrics.append({"label": "PAT Margin", "value": margins["pat_margin"], "unit": "%"})
    stability = margins.get("stability") or {}
    if stability.get("avg_5y") is not None:
        margin_metrics.append({"label": "5Y Avg PAT Margin", "value": stability["avg_5y"], "unit": "%"})
    if stability.get("classification"):
        margin_metrics.append({"label": "Stability", "value": _readable(stability["classification"])})

    peer = pli.get("peer_percentiles") or {}
    peer_rows = []
    for key, label in (("pat_margin", "PAT Margin"), ("ebitda_margin", "EBITDA Margin")):
        entry = peer.get(key) or {}
        if entry.get("percentile") is not None:
            company_value = entry.get("company_value")
            median = entry.get("peer_median")
            peer_rows.append({
                "metric": label,
                "companyValue": f"{company_value:.1f}%" if company_value is not None else "N/A",
                "median": f"{median:.1f}%" if median is not None else "N/A",
                "percentile": entry["percentile"],
            })
    peer_benchmark = (
        {"title": f"Peer benchmark ({peer.get('peer_count', 0)} peers)", "rows": peer_rows}
        if peer_rows else None
    )

    doubling = pli.get("doubling") or {}
    growth_velocity = []
    for key, label in (("revenue", "Revenue Doubling"), ("pat", "PAT Doubling")):
        d = doubling.get(key) or {}
        years = d.get("doubling_years")
        if years is None:
            continue
        if d.get("method") == "EMPIRICAL" and d.get("start_year") and d.get("end_year"):
            note = f"Actual doubling FY{d['start_year']} → FY{d['end_year']}"
        elif d.get("method") == "CAGR_THEORETICAL":
            note = "Estimated from historical CAGR, not an actual historical doubling"
        else:
            note = None
        growth_velocity.append({"label": label, "value": years, "unit": "yrs", "note": note})
    velocity_note = _PL_VELOCITY_NOTES.get(doubling.get("velocity_comparison"))

    structure = pli.get("structure") or {}
    structure_metrics = []
    if structure.get("standalone_revenue") is not None:
        structure_metrics.append({"label": "Standalone Revenue", "value": f"Rs. {structure['standalone_revenue']:,.0f} Cr"})
    if structure.get("consolidated_revenue") is not None:
        structure_metrics.append({"label": "Consolidated Revenue", "value": f"Rs. {structure['consolidated_revenue']:,.0f} Cr"})
    if structure.get("csr") is not None:
        structure_metrics.append({
            "label": "CSR", "value": f"{structure['csr']:.2f}",
            "note": _readable(structure["csr_band"]) if structure.get("csr_band") else None,
        })
    structure_metrics.append({
        "label": "Structure",
        "value": "SOTP required" if structure.get("sotp_required") else "Single business",
    })

    eq = pli.get("earnings_quality") or {}
    earnings_quality = None
    if eq.get("eqi") is not None:
        core = eq["eqi"]
        earnings_quality = {
            "title": f"Earnings Quality Index {core * 100:.0f}%",
            "slices": [
                {"name": "Core operating income", "value": core, "color": "#4fb3a0"},
                {"name": "Non-core / other income", "value": 1 - core, "color": "#d9694f"},
            ],
            "note": _readable(eq["classification"]) if eq.get("classification") else None,
        }

    flags = pli.get("diagnostic_flags") or []
    flags_group = (
        {"title": "P&L flags & signals", "items": [_readable(f) for f in flags], "severity": "warning"}
        if flags else None
    )

    return {
        "period": period,
        "statementType": pli.get("statement_type", ""),
        "score": {
            "value": score.get("master_pl_score"),
            "classification": _readable(score["classification"]) if score.get("classification") else None,
            "algorithmVersion": score.get("algorithm_version", ""),
        },
        "scoreComponents": score_components,
        "cascade": cascade_steps,
        "cascadeNote": (
            "Gross Profit isn't shown — Screener.in's P&L view has no material-cost/COGS "
            "breakdown for any sector, so it's never estimated."
        ),
        "margins": margin_metrics,
        "peerBenchmark": peer_benchmark,
        "growthVelocity": growth_velocity,
        "velocityNote": velocity_note,
        "structure": structure_metrics,
        "earningsQuality": earnings_quality,
        "flags": flags_group,
    }


_BS_ARCHETYPE_TONE = {"STRONG": "positive", "TRANSFORMING": "warning", "MIDDLE": "neutral", "WEAK": "negative"}


def _balance_sheet_intelligence(bsi: dict) -> dict | None:
    """Maps `compute_balance_sheet_intelligence()`'s output (app/
    calculations/balance_sheet_intelligence/) into the PDF's
    `balanceSheetIntelligence` section — additive, structurally parallel to
    `_pnl_intelligence()` above, folded into the same combined PDF as new
    pages after it (Milestone 9). Every sub-block is only populated when
    real data supports it — never a fabricated placeholder for a company
    with no balance-sheet data or a financial institution routed away from
    working-capital analysis."""
    period = bsi.get("period")
    if not period:
        return None
    # PDF renders CONSOLIDATED only — see `_pnl_intelligence()`'s identical
    # guard above for the full rationale, including why this still holds
    # (and now correctly INCLUDES the section) for single-statement-source
    # companies like Netweb Technologies / Bandhan Bank.
    if bsi.get("statement_type") != "CONSOLIDATED":
        return None
    integrity = bsi.get("balance_sheet_integrity") or {}
    if integrity.get("status") == "BALANCE_SHEET_INTEGRITY_ERROR":
        return None

    dm = bsi.get("derived_metrics") or {}
    snapshot_metrics = []
    for key, label, unit in (
        ("total_equity", "Total Equity", ""), ("net_debt", "Net Debt", ""),
        ("debt_to_equity", "Debt/Equity", "x"), ("liabilities_to_equity", "Liabilities/Equity", "x"),
        ("net_debt_to_ebitda", "Net Debt/EBITDA", "x"), ("roce", "ROCE", "%"),
    ):
        if dm.get(key) is not None:
            snapshot_metrics.append({"label": label, "value": dm[key], "unit": unit})
    wc = bsi.get("working_capital") or {}
    if wc.get("current_ratio_latest") is not None:
        snapshot_metrics.append({"label": "Current Ratio", "value": wc["current_ratio_latest"], "unit": "x"})
    if wc.get("ccc_latest") is not None:
        ccc_note = "Screener, latest period (preferred source)" if (wc.get("single_period_fallback") or {}).get("ccc") else None
        snapshot_metrics.append({"label": "Cash Conversion Cycle", "value": wc["ccc_latest"], "unit": " days", "note": ccc_note})

    house = bsi.get("house") or {}
    house_sources = [{"label": s["label"], "value": s["value"]} for s in house.get("sources", [])]
    house_applications = [{"label": a["label"], "value": a["value"]} for a in house.get("applications", [])]

    hcs = bsi.get("historical_common_size") or {}
    composition_periods = None
    if len(hcs) >= 2:
        composition_periods = [
            {
                "label": _fiscal_label(period_key),
                "segments": [{"name": _readable(field), "value": pct} for field, pct in pcts.items() if pct is not None],
            }
            for period_key, pcts in sorted(hcs.items(), key=lambda kv: _year_sort_key(kv[0]))
        ]
        composition_periods = [p for p in composition_periods if p["segments"]]
        if len(composition_periods) < 2:
            composition_periods = None

    ht = bsi.get("historical_trends") or {}
    net_worth_trend = ht.get("net_worth", {}).get("5Y") or ht.get("net_worth", {}).get("3Y")
    net_worth_note = None
    if net_worth_trend and net_worth_trend.get("cagr") is not None:
        net_worth_note = f"Net worth CAGR of {net_worth_trend['cagr']:.1f}% over {net_worth_trend['periods_available'] - 1} year(s) on record."

    ppe_metrics = []
    fixed_assets_trend = ht.get("fixed_assets", {}).get("3Y") or {}
    cwip_trend = ht.get("capital_work_in_progress", {}).get("3Y") or {}
    if fixed_assets_trend.get("cagr") is not None:
        ppe_metrics.append({"label": "Fixed Assets CAGR (3Y)", "value": fixed_assets_trend["cagr"], "unit": "%"})
    if cwip_trend.get("cagr") is not None:
        ppe_metrics.append({"label": "CWIP CAGR (3Y)", "value": cwip_trend["cagr"], "unit": "%"})

    roce_metrics = []
    if dm.get("roce") is not None:
        roce_metrics.append({"label": "ROCE", "value": dm["roce"], "unit": "%"})
    if dm.get("ebit_margin") is not None:
        roce_metrics.append({"label": "EBIT Margin", "value": dm["ebit_margin"], "unit": "%"})
    if dm.get("capital_employed_turnover") is not None:
        roce_metrics.append({"label": "Capital Employed Turnover", "value": dm["capital_employed_turnover"], "unit": "x"})

    archetype = bsi.get("archetype") or {}
    archetype_classification = archetype.get("classification")
    archetype_block = None
    if archetype_classification and archetype_classification != "NOT_APPLICABLE":
        archetype_block = {
            "classification": _readable(archetype_classification),
            "tone": _BS_ARCHETYPE_TONE.get(archetype_classification, "neutral"),
            "evidence": archetype.get("evidence") or [],
        }

    triggered_flags = [f for f in (bsi.get("risk_flags") or []) if f.get("status") == "TRIGGERED"]
    risk_flags_group = (
        {"title": "Balance sheet risk flags", "items": [f"{_readable(f['flag_id'])}: {'; '.join(f.get('evidence') or [])}" for f in triggered_flags], "severity": "warning"}
        if triggered_flags else None
    )

    coverage = bsi.get("coverage") or {}
    coverage_table = None
    if coverage.get("metrics"):
        gap_rows = [
            {"label": _readable(metric), "values": [m["status"]]}
            for metric, m in sorted(coverage["metrics"].items())
            if m["status"] in ("MISSING_INPUT", "SOURCE_REQUIRED")
        ]
        coverage_table = {
            "title": "Data coverage",
            "subtitle": f"{coverage.get('coverage_pct', 0):.0f}% of {coverage.get('total_metrics', 0)} tracked metrics available or calculable",
            "columns": ["Status"],
            "rows": gap_rows,
        }

    return {
        "period": period,
        "statementType": bsi.get("statement_type", ""),
        "snapshotMetrics": snapshot_metrics,
        "house": (
            {"sources": house_sources, "applications": house_applications}
            if house_sources and house_applications else None
        ),
        "compositionByYear": composition_periods,
        "netWorthNote": net_worth_note,
        "ppeMetrics": ppe_metrics,
        "roceMetrics": roce_metrics,
        "archetype": archetype_block,
        "riskFlags": risk_flags_group,
        "coverageTable": coverage_table,
    }


_CF_ARCHETYPE_TONE = {
    "CASH_COMPOUNDER": "positive", "CASH_HARVEST": "positive", "GROWTH_REINVESTMENT": "neutral",
    "ASSET_LIQUIDATION_SUPPORTED": "warning", "WORKING_CAPITAL_TRAP": "warning",
    "DEBT_FUNDED_BUSINESS": "negative", "MIXED": "neutral",
}


def _cash_flow_intelligence(cfi: dict) -> dict | None:
    """Maps `compute_cash_flow_intelligence()`'s output (app/calculations/
    cash_flow_intelligence/) into the PDF's `cashFlowIntelligence` section —
    additive, structurally parallel to `_balance_sheet_intelligence()`
    above, folded into the same combined PDF as new pages after it
    (Milestone 9). Every sub-block is only populated when real data
    supports it — never a fabricated placeholder for a company with no
    Screener cash-flow schedule data."""
    period = cfi.get("period")
    if not period:
        return None
    # PDF renders CONSOLIDATED only — see `_pnl_intelligence()`'s identical
    # guard above for the full rationale, including why this still holds
    # (and now correctly INCLUDES the section) for single-statement-source
    # companies like Netweb Technologies / Bandhan Bank.
    if cfi.get("statement_type") != "CONSOLIDATED":
        return None

    reconciliation = cfi.get("reconciliation") or {}
    cfo_bridge = reconciliation.get("cfo_bridge") or {}
    bridge_steps = [
        {"label": label, "value": cfo_bridge.get(field)}
        for field, label in (
            ("operating_profit", "Operating Profit"), ("receivables_change", "Receivables"),
            ("inventory_change", "Inventory"), ("payables_change", "Payables"),
            ("loans_advances_change", "Loans & Advances"), ("other_wc_change", "Other WC Items"),
            ("taxes_paid", "Taxes Paid"),
        )
        if cfo_bridge.get(field) is not None
    ]
    cfo_bridge_block = (
        {"steps": bridge_steps, "total": {"label": "Computed CFO", "value": cfo_bridge.get("computed_cfo")}}
        if bridge_steps and cfo_bridge.get("computed_cfo") is not None else None
    )

    conversion = cfi.get("conversion") or {}
    conversion_latest = conversion.get("latest") or {}
    conversion_metrics = []
    if conversion_latest.get("ratio_pct") is not None:
        conversion_metrics.append({"label": "CFO / Operating Profit", "value": conversion_latest["ratio_pct"], "unit": "%"})
    if conversion.get("cumulative_3y", {}).get("cumulative_cfo_to_operating_profit_pct") is not None:
        conversion_metrics.append({"label": "3Y Cumulative Conversion", "value": conversion["cumulative_3y"]["cumulative_cfo_to_operating_profit_pct"], "unit": "%"})

    investing_breakdown = (cfi.get("investing") or {}).get("breakdown") or {}
    investing_metrics = [
        {"label": label, "value": investing_breakdown[field]}
        for field, label in (
            ("fixed_assets_purchased", "Capex"), ("fixed_assets_sold", "Asset Sales"),
            ("interest_received", "Interest Received"),
        )
        if investing_breakdown.get(field) is not None
    ]

    financing_breakdown = (cfi.get("financing") or {}).get("breakdown") or {}
    debt_financing = (cfi.get("financing") or {}).get("debt_financing") or {}
    financing_metrics = [
        {"label": label, "value": financing_breakdown[field]}
        for field, label in (
            ("borrowings_raised", "Borrowings Raised"), ("borrowings_repaid", "Borrowings Repaid"),
            ("dividends_paid", "Dividends Paid"),
        )
        if financing_breakdown.get(field) is not None
    ]
    if debt_financing.get("classification"):
        financing_metrics.append({"label": "Debt Direction", "value": _readable(debt_financing["classification"]), "unit": ""})

    fcf = cfi.get("free_cash_flow") or {}
    fcf_quality = (fcf.get("quality") or {}).get("classification")
    fcf_metrics = []
    fcf_recon = fcf.get("reconciliation") or {}
    if fcf_recon.get("reported_fcf") is not None:
        fcf_metrics.append({"label": "Free Cash Flow", "value": fcf_recon["reported_fcf"], "unit": ""})

    archetype = cfi.get("archetype") or {}
    archetype_classification = archetype.get("classification")
    archetype_block = None
    if archetype_classification and archetype_classification != "MIXED":
        archetype_block = {
            "classification": _readable(archetype_classification),
            "tone": _CF_ARCHETYPE_TONE.get(archetype_classification, "neutral"),
            "evidence": archetype.get("evidence") or [],
        }

    triggered_flags = [f for f in (cfi.get("risk_flags") or []) if f.get("status") == "TRIGGERED"]
    risk_flags_group = (
        {"title": "Cash flow risk flags", "items": [f"{_readable(f['flag_id'])}: {'; '.join(f.get('evidence') or [])}" for f in triggered_flags], "severity": "warning"}
        if triggered_flags else None
    )

    coverage = cfi.get("coverage") or {}
    coverage_table = None
    if coverage.get("metrics"):
        gap_rows = [
            {"label": _readable(metric), "values": [m["status"]]}
            for metric, m in sorted(coverage["metrics"].items())
            if m["status"] in ("MISSING_INPUT", "SOURCE_REQUIRED", "PARTIAL")
        ]
        coverage_table = {
            "title": "Data coverage",
            "subtitle": f"{coverage.get('coverage_pct', 0):.0f}% of {coverage.get('total_metrics', 0)} tracked metrics available or calculable",
            "columns": ["Status"],
            "rows": gap_rows,
        }

    return {
        "period": period,
        "statementType": cfi.get("statement_type", ""),
        "cfoBridge": cfo_bridge_block,
        "conversionMetrics": conversion_metrics or None,
        "investingMetrics": investing_metrics or None,
        "financingMetrics": financing_metrics or None,
        "fcfMetrics": fcf_metrics or None,
        "fcfQuality": _readable(fcf_quality) if fcf_quality else None,
        "archetype": archetype_block,
        "riskFlags": risk_flags_group,
        "coverageTable": coverage_table,
    }


def _eps_pe_combo(db: Session, company_id: str) -> dict | None:
    from app.infrastructure.database.models import ValuationHistory
    rows = (db.query(ValuationHistory).filter_by(company_id=company_id)
            .order_by(ValuationHistory.period_end.asc()).all())
    rows = [r for r in rows if r.eps is not None][-10:]
    if len(rows) < 2:
        return None
    bar_pts = [{"label": _fiscal_label(r.period_end), "value": float(r.eps)} for r in rows]
    pe_pts = [{"label": _fiscal_label(r.period_end), "value": float(r.pe)} for r in rows if r.pe is not None]
    lines = [{"name": "P/E", "points": pe_pts}] if len(pe_pts) >= 2 else []
    return {"bar": {"name": "EPS (Rs.)", "points": bar_pts}, "lines": lines}


def _valuation_vs_price(db: Session, company_id: str) -> dict | None:
    """PDF Upgrade plan, Priority 2 #6 — "has the stock become more
    expensive because earnings improved, because the multiple expanded, or
    both?" Price + P/E together, answering a different question from the
    existing EPS/P-E combo above (EPS trend vs. multiple) — this pairs the
    multiple directly against the PRICE that trades on it."""
    from app.infrastructure.database.models import ValuationHistory
    rows = (db.query(ValuationHistory).filter_by(company_id=company_id)
            .order_by(ValuationHistory.period_end.asc()).all())
    rows = [r for r in rows if r.price is not None and r.pe is not None][-10:]
    if len(rows) < 2:
        return None
    price_pts = [{"label": _fiscal_label(r.period_end), "value": float(r.price)} for r in rows]
    pe_pts = [{"label": _fiscal_label(r.period_end), "value": float(r.pe)} for r in rows]
    first_pe, last_pe = pe_pts[0]["value"], pe_pts[-1]["value"]
    first_price, last_price = price_pts[0]["value"], price_pts[-1]["value"]
    price_change_pct = (last_price - first_price) / first_price * 100 if first_price else None
    pe_change_pct = (last_pe - first_pe) / first_pe * 100 if first_pe else None
    callout = None
    if price_change_pct is not None and pe_change_pct is not None:
        if price_change_pct > 0 and pe_change_pct > 0 and abs(pe_change_pct) > abs(price_change_pct) * 0.3:
            callout = f"Price is up {price_change_pct:.0f}% while the P/E multiple expanded {pe_change_pct:.0f}% — some of the gain is multiple expansion, not just earnings growth."
        elif price_change_pct > 0 and pe_change_pct <= 0:
            callout = f"Price is up {price_change_pct:.0f}% while the P/E multiple contracted {abs(pe_change_pct):.0f}% — the gain is earnings-driven, not multiple expansion."
        else:
            callout = f"Price changed {price_change_pct:+.0f}% and the P/E multiple changed {pe_change_pct:+.0f}% over the period shown."
    return {
        "price": {"name": "Price", "points": price_pts},
        "pe": {"name": "P/E", "points": pe_pts},
        "callout": callout,
    }


# ── Scores tab detail ───────────────────────────────────────────────────────
_SCORE_CATEGORIES = [
    ("growth", "Growth"), ("profitability", "Profitability"), ("cash_flow", "Cash flow"),
    ("balance_sheet", "Balance sheet"), ("efficiency", "Efficiency"), ("valuation", "Valuation"),
]


def _score_detail(scores: dict, metrics: dict) -> dict | None:
    detail: dict = {}
    radar = [{"label": label, "value": float(scores[key])} for key, label in _SCORE_CATEGORIES if scores.get(key) is not None]
    if len(radar) >= 3:
        detail["radar"] = radar
    weights = scores.get("weights") or {}
    comp_weights = [{"label": label, "value": float(weights[key])} for key, label in _SCORE_CATEGORIES if weights.get(key)]
    if comp_weights:
        detail["compositeWeights"] = comp_weights
    piotroski = metrics.get("piotroski")
    if piotroski and piotroski.get("score") is not None:
        detail["piotroski"] = {
            "score": piotroski.get("score"),
            "checksAvailable": piotroski.get("checks_available", 0),
            "components": [{"label": c.get("label"), "passed": c.get("passed")} for c in (piotroski.get("components") or [])],
        }
    return detail or None


# ── Peers tab ────────────────────────────────────────────────────────────────
_PEER_METRIC_COLS = [
    ("revenue_cagr_3y", "Rev CAGR", "%"), ("ebitda_margin", "EBITDA%", "%"),
    ("roce", "ROCE%", "%"), ("roe", "ROE%", "%"), ("debt_to_equity", "D/E", "x"),
    ("fcf_to_pat", "FCF/PAT", "%"), ("pe_ratio", "P/E", "x"), ("pb_ratio", "P/B", "x"),
]
_PERCENTILE_METRIC_SPECS = [
    ("revenue_cagr_3y", "Revenue CAGR 3Y", "%"), ("ebitda_margin", "EBITDA Margin", "%"),
    ("roce", "ROCE", "%"), ("roe", "ROE", "%"), ("fcf_to_pat", "FCF/PAT", "%"),
    ("debt_to_equity", "Debt/Equity", "x"), ("net_debt_to_ebitda", "Net Debt/EBITDA", "x"),
    ("pe_ratio", "P/E", "x"), ("pb_ratio", "P/B", "x"), ("ev_to_ebitda", "EV/EBITDA", "x"),
]


def _peers_detail(analysis, extras: dict) -> dict | None:
    peers_data = analysis.peers or {}
    peer_rows = peers_data.get("peers") or []
    if not peer_rows:
        return None
    sector_medians = peers_data.get("sector_medians") or {}
    percentiles = peers_data.get("company_percentiles") or {}
    metrics = analysis.metrics or {}
    company = analysis.company_info or {}

    detail: dict = {}

    def _table_row(name: str, symbol: str, mcap, values: dict, highlight: bool = False) -> dict:
        row: dict = {
            "label": name,
            "values": [symbol, round(mcap / 1e7) if mcap else None] + [values.get(k) for k, _, _ in _PEER_METRIC_COLS],
        }
        if highlight:
            row["highlight"] = True
        return row

    rows = [_table_row(company.get("company_name") or "Subject", company.get("symbol") or "", company.get("market_cap"), metrics, highlight=True)]
    for p in peer_rows[:10]:
        rows.append(_table_row(p.get("company_name") or p.get("symbol") or "", p.get("symbol") or "", p.get("market_cap"), p))
    if sector_medians:
        rows.append(_table_row("Sector median", "—", None, sector_medians))
    detail["table"] = {
        "title": "Peer comparison",
        "subtitle": f"{peers_data.get('peer_count', len(peer_rows))} peers · {peers_data.get('industry') or peers_data.get('sector') or ''}",
        "columns": ["Symbol", "Mkt Cap (Cr)"] + [label for _, label, _ in _PEER_METRIC_COLS],
        # 10 columns crammed into the space after the company-name column
        # forced everything to one equal width — narrow enough (~35px) that
        # a plain text ticker like "MARUTI" wrapped mid-word. Symbol is the
        # only non-numeric column here; give it real room and let the 8
        # short numeric columns share the rest evenly.
        "columnWidths": [1.7, 1.3] + [1.0] * len(_PEER_METRIC_COLS),
        "rows": rows,
    }

    scatter_points = []
    if metrics.get("revenue_cagr_3y") is not None and metrics.get("roce") is not None:
        scatter_points.append({
            "name": company.get("company_name") or "Subject",
            "x": float(metrics["revenue_cagr_3y"]), "y": float(metrics["roce"]),
            "size": (company.get("market_cap") or 0) / 1e9, "isSubject": True,
        })
    for p in peer_rows:
        if p.get("revenue_cagr_3y") is not None and p.get("roce") is not None:
            scatter_points.append({
                "name": p.get("company_name") or p.get("symbol") or "",
                "x": float(p["revenue_cagr_3y"]), "y": float(p["roce"]),
                "size": (p.get("market_cap") or 0) / 1e9 or 4,
            })
    if len(scatter_points) >= 2:
        detail["scatter"] = {"xLabel": "Revenue CAGR 3Y (%)", "yLabel": "ROCE (%)", "points": scatter_points}

    pct_rows = []
    for key, label, unit in _PERCENTILE_METRIC_SPECS:
        pctile = percentiles.get(key)
        if pctile is None:
            continue
        pct_rows.append({
            "metric": label,
            "companyValue": _fmt(metrics.get(key), unit),
            "median": _fmt(sector_medians.get(key), unit),
            "percentile": float(pctile),
        })
    if pct_rows:
        detail["percentiles"] = pct_rows

    perf_series = (extras.get("peer_performance") or {}).get("series") or []
    if len(perf_series) >= 2:
        detail["relativePerformance"] = [
            {"name": s["name"], **({"color": "#c9a227"} if s.get("is_subject") else {}),
             "points": [{"label": p["date"][5:], "value": p["value"]} for p in s["points"]]}
            for s in perf_series
        ]
    dot_plot = _peer_dot_plot(analysis)
    if dot_plot:
        detail["dotPlot"] = dot_plot
    return detail or None


_PEER_DOT_PLOT_METRICS = [
    ("revenue_cagr_3y", "Revenue CAGR 3Y", "%"), ("ebitda_margin", "EBITDA Margin", "%"),
    ("roce", "ROCE", "%"), ("roe", "ROE", "%"), ("pe_ratio", "P/E", "x"),
]


def _peer_dot_plot(analysis) -> list[dict] | None:
    """PDF Upgrade plan, Priority 2 #7 — "where peer data exists, a dot
    plot would be more readable than prose." PAT margin isn't one of the
    metrics this app's peer comparison already tracks (`_PEER_METRIC_COLS`
    above has no `pat_margin`) — ROE stands in for it rather than
    fabricating a PAT-margin peer comparison this app doesn't actually
    compute."""
    peers_data = analysis.peers or {}
    peer_rows = peers_data.get("peers") or []
    if not peer_rows:
        return None
    metrics = analysis.metrics or {}
    company = analysis.company_info or {}
    subject_name = company.get("company_name") or "Subject"

    rows = []
    for key, label, unit in _PEER_DOT_PLOT_METRICS:
        peer_points = [
            {"name": p.get("company_name") or p.get("symbol") or "", "value": float(p[key])}
            for p in peer_rows if p.get(key) is not None
        ]
        subject_value = metrics.get(key)
        if subject_value is None and not peer_points:
            continue
        rows.append({
            "metric": label,
            "unit": unit,
            "subjectName": subject_name,
            "subjectValue": float(subject_value) if subject_value is not None else None,
            "peers": peer_points,
        })
    return rows or None


# ── Calendar tab ─────────────────────────────────────────────────────────────
_FORWARD_PERIOD_LABELS = {"0q": "This Q", "+1q": "Next Q", "0y": "This FY", "+1y": "Next FY", "LTG": "Long-term"}


def _calendar(db: Session, company_id: str) -> dict | None:
    from app.infrastructure.database.models import EarningsCalendar, CorporateAction, ForwardEstimate, BrokerResearchReport

    cal_row = db.query(EarningsCalendar).filter_by(company_id=company_id).first()
    ca_rows = (db.query(CorporateAction).filter_by(company_id=company_id)
               .order_by(CorporateAction.action_date.desc()).limit(10).all())
    fwd_rows = db.query(ForwardEstimate).filter_by(company_id=company_id).all()
    broker_rows = (db.query(BrokerResearchReport).filter_by(company_id=company_id)
                   .order_by(BrokerResearchReport.report_date.desc()).limit(10).all())
    if not (cal_row or ca_rows or fwd_rows or broker_rows):
        return None

    calendar: dict = {}
    if cal_row:
        calendar["kpis"] = [
            {"label": "Next Earnings", "value": cal_row.next_earnings_date or "N/A"},
            {"label": "Ex-Dividend", "value": cal_row.ex_dividend_date or "N/A"},
            {"label": "Expected EPS", "value": _fmt(cal_row.expected_eps_avg, "", 2)},
            {"label": "EPS Range", "value": f"{_fmt(cal_row.expected_eps_low, '', 2)}–{_fmt(cal_row.expected_eps_high, '', 2)}"},
        ]
    if ca_rows:
        calendar["corporateActions"] = {
            "title": "Recent corporate actions",
            "columns": ["Type", "Value"],
            "rows": [{"label": r.action_date, "values": [r.action_type, float(r.value)]} for r in ca_rows],
        }
    if fwd_rows:
        forward: dict = {}
        # Revenue rows are raw absolute rupees (unlike EPS, already a small
        # per-share number) — same /1e7 Cr scaling used everywhere else in
        # this report, or the table renders "28,06,57,49,500" instead of a
        # readable Cr figure.
        for metric_type, key, label, scale, avg_col in [
            ("eps", "eps", "EPS", 1, "Avg"),
            ("revenue", "revenue", "Revenue", 1e7, "Avg (Cr)"),
        ]:
            m_rows = [r for r in fwd_rows if r.metric_type == metric_type and r.avg is not None]
            if not m_rows:
                continue
            forward[key] = {
                "title": f"Forward estimates — {label}",
                "columns": [avg_col, "Low–High", "# Analysts"],
                "rows": [
                    {"label": _FORWARD_PERIOD_LABELS.get(r.period_label, r.period_label),
                     "values": [round(float(r.avg) / scale, 2),
                                f"{_fmt(float(r.low) / scale if r.low is not None else None, '', 2)}–{_fmt(float(r.high) / scale if r.high is not None else None, '', 2)}",
                                r.num_analysts or "N/A"]}
                    for r in m_rows
                ],
            }
        if forward:
            calendar["forwardEstimates"] = forward
    if broker_rows:
        calendar["brokerReports"] = {
            "title": "Broker rating history",
            "columns": ["Broker", "Rating", "Target", "Upside %"],
            "rows": [
                {"label": r.report_date, "values": [
                    r.broker_name, r.rating or "N/A",
                    float(r.target_price) if r.target_price is not None else None,
                    float(r.upside_pct) if r.upside_pct is not None else None,
                ]}
                for r in broker_rows
            ],
        }
    return calendar or None


# ── Concall tab (deliberately excludes "promises"/Open Management
# Commitments — the user asked for that to stay out of the report) ─────────
def _concall(db: Session, company_id: str, extras: dict) -> dict | None:
    from app.interpretation.concall_report_data import build_concall_report_data
    data = build_concall_report_data(db, company_id)
    if not data or not data.get("latest_transcript"):
        return None

    concall: dict = {}
    lt = data["latest_transcript"]
    participants = ", ".join(p.get("name", "") for p in (lt.get("management_participants") or [])[:4])
    meta_parts = [lt.get("quarter") or lt.get("call_date") or lt.get("filing_date") or ""]
    if participants:
        meta_parts.append(f"Management: {participants}")
    meta = " · ".join(p for p in meta_parts if p)
    if meta:
        concall["transcriptMeta"] = meta

    highlights = extras.get("concall_highlights")
    if highlights and highlights.get("sections"):
        concall["highlights"] = [
            {"title": s["heading"], "items": [_pdf_safe(b) for b in s["bullets"][:6]], "severity": "neutral"}
            for s in highlights["sections"]
        ]

    topic_sentiment = data.get("topic_sentiment") or []
    if topic_sentiment:
        concall["topicSentiment"] = [{"topic": t["topic"], "sentiment": t["sentiment"], "arrow": t.get("arrow", "")} for t in topic_sentiment]

    what_changed = data.get("what_changed") or []
    if what_changed:
        concall["whatChanged"] = [_pdf_safe(c) for c in what_changed]

    gc = data.get("guidance_consistency")
    if gc:
        concall["guidanceConsistency"] = {"score": float(gc["score"]), "metricsTracked": gc["metrics_tracked"], "totalUpdates": gc["total_updates"]}

    guidance = data.get("guidance") or []
    if guidance:
        def _target(g: dict) -> str:
            if g["guidance_type"] == "quantitative":
                if g.get("target_low") is not None and g.get("target_high") is not None:
                    return f"{g['target_low']:g}-{g['target_high']:g} {g.get('unit') or ''}".strip()
                if g.get("target_value") is not None:
                    return f"{g['target_value']:g} {g.get('unit') or ''}".strip()
                return "—"
            return "qualitative"
        concall["guidanceTable"] = {
            "title": "Management guidance",
            "columns": ["Period", "Target", "Tone", "Status"],
            "rows": [
                {"label": g["metric"].replace("_", " ").title(), "values": [g.get("period") or "—", _target(g), g.get("tone") or "—", g["status"]]}
                for g in guidance[:15]
            ],
        }
        # PDF Upgrade plan, Priority 2 #8 — a real status matrix (colored
        # badge, not a plain-text column) alongside the table above. Maps
        # this app's own `ManagementGuidance.status` vocabulary (models.py:
        # NEW|REITERATED|UPGRADED|DOWNGRADED|WITHDRAWN|ACHIEVED|MISSED|
        # PARTIALLY_ACHIEVED, computed deterministically in Python, never
        # by the LLM) onto the doc's own suggested ahead/on-track/below/
        # qualitative framing — never a fabricated "latest actual" number,
        # since guidance-to-actual-outcome matching isn't computed yet
        # (see concall_report_data.py's own docstring on this gap).
        concall["guidanceMatrix"] = [
            {
                "metric": g["metric"].replace("_", " ").title(),
                "target": _target(g),
                "status": _GUIDANCE_STATUS_LABEL.get(g["status"], g["status"].replace("_", " ").title()),
                "statusTone": _GUIDANCE_STATUS_TONE.get(g["status"], "neutral"),
            }
            for g in guidance[:15]
        ]

    credibility = data.get("credibility") or []
    if credibility:
        concall["credibility"] = [
            f"{c['metric'].replace('_', ' ').title()}: {c['guidance_count']} updates — "
            f"{c['upgraded_count']} upgraded, {c['downgraded_count']} downgraded, "
            f"{c['reiterated_count']} reiterated (latest: {c['last_status']})"
            for c in credibility
        ]
    return concall or None


# ── Deep Research tab ────────────────────────────────────────────────────────
def _severity_for_flag(raw: str | None) -> str:
    r = (raw or "").upper()
    return "negative" if r == "HIGH" else "warning" if r == "MEDIUM" else "neutral"


_SENTENCE_SPLIT_RE = re.compile(r"(?<=[a-zA-Z]{3}\.)\s+(?=[A-Z])")


def _deep_research(analysis) -> list[dict] | None:
    """PDF Upgrade plan, Priority 3 "Deep-research pages" — a repeating
    visual rhythm (short heading, one-sentence conclusion, supporting
    paragraph) instead of a full-page text block. `conclusion` is the
    section's own first sentence (same sentence-boundary regex already
    used for the cover page's "So what?" text above), not a fabricated
    new summary — the PDF just gives it emphasis. A genuine per-section
    source tag isn't added: this app has no per-paragraph source metadata
    for AI-narrated deep-research prose (only a whole-report generation
    note, already shown once at the end of the AI view section) —
    inventing a distinct tag per section would misrepresent precision
    this app doesn't have."""
    sections = (analysis.report_blueprint or {}).get("sections") or []
    out = []
    for s in sections:
        if s.get("id") == "key_questions":  # defensive — already removed at generation time
            continue
        entry: dict = {"title": s.get("title", "")}
        if s.get("content"):
            normalized = (_pdf_safe(s["content"]) or "").replace("\n", " ").strip()
            entry["content"] = normalized
            sentences = _SENTENCE_SPLIT_RE.split(normalized)
            if len(sentences) > 1 and sentences[0]:
                entry["conclusion"] = sentences[0].strip()
                entry["content"] = " ".join(sentences[1:]).strip()
        items = s.get("items") or []
        key_points = s.get("key_points") or []
        if key_points and not items:
            items = [{"description": kp} for kp in key_points]
        if items:
            mapped_items = []
            for it in items:
                # Only include keys actually present — the TS side
                # distinguishes Q&A-shaped items from title/description
                # items by checking `!== undefined`; a JSON `null` for an
                # absent key would satisfy that check too and misclassify
                # every item as Q&A-shaped.
                mapped: dict = {}
                if it.get("title"):
                    mapped["title"] = _pdf_safe(it["title"])
                if it.get("description"):
                    mapped["description"] = _pdf_safe(it["description"])
                if it.get("question"):
                    mapped["question"] = _pdf_safe(it["question"])
                if it.get("answer"):
                    mapped["answer"] = _pdf_safe(it["answer"])
                if it.get("severity"):
                    mapped["severity"] = _severity_for_flag(it["severity"])
                mapped_items.append(mapped)
            entry["items"] = mapped_items
        if entry.get("content") or entry.get("items"):
            out.append(entry)
    return out or None



_KPI_UNIT_FORMATS = {
    "%": lambda v: f"{v:.1f}%",
    "MT": lambda v: f"{v:.2f} MT",
    "tonnes": lambda v: f"{v:,.0f} t",
    "units": lambda v: f"{v:,.0f}",
    "INR": lambda v: f"Rs {v:,.2f}" if abs(v) < 100 else f"Rs {v:,.0f}",
    "INR Cr": lambda v: f"Rs {v:,.0f} Cr",
    "USD/bbl": lambda v: f"${v:.2f}/bbl",
    "days": lambda v: f"{v:.2f} days",
    "x": lambda v: f"{v:.2f}x",
    "Mn": lambda v: f"{v:,.2f} Mn",
    "GB": lambda v: f"{v:,.1f} GB",
    "MW": lambda v: f"{v:,.0f} MW",
    "tpd": lambda v: f"{v:,.0f} t/day",
    "MLD": lambda v: f"{v:,.0f} MLD",
    "km": lambda v: f"{v:,.0f} km",
    "MMSCMD": lambda v: f"{v:,.2f} MMSCMD",
    "MMSCM": lambda v: f"{v:,.1f} MMSCM",
    "TBtu": lambda v: f"{v:,.0f} TBtu",
    "MMTPA": lambda v: f"{v:,.1f} MMTPA",
    "lakh": lambda v: f"{v:,.2f} lakh",
    "INR/SCM": lambda v: f"Rs {v:,.2f}/SCM",
    "MU": lambda v: f"{v:,.0f} MU",
    "INR/kWh": lambda v: f"Rs {v:,.2f}/kWh",
    "ckm": lambda v: f"{v:,.0f} ckm",
    "MVA": lambda v: f"{v:,.0f} MVA",
    "Bn units": lambda v: f"{v:,.2f} Bn units",
    "Bn GB": lambda v: f"{v:,.2f} Bn GB",
    "USD": lambda v: f"US${v:,.2f}",
    "kt": lambda v: f"{v:,.0f} kt",
    "Mn sq ft": lambda v: f"{v:,.1f} Mn sq ft",
    "Mn dwt": lambda v: f"{v:,.2f} Mn dwt",
    "Bn": lambda v: f"{v:,.2f} Bn",
    "USD/day": lambda v: f"US${v:,.0f}/day",
    "USD Bn": lambda v: f"US${v:.2f} Bn",
    "USD Mn": lambda v: f"US${v:,.0f} Mn",
    "USD k": lambda v: f"US${v:.1f}k",
}


def _fmt_kpi(value: float, unit: str) -> str:
    fn = _KPI_UNIT_FORMATS.get(unit)
    return fn(value) if fn else f"{value:,.2f}"


def _sector_kpis(kpis: dict | None) -> dict | None:
    """Maps `compute_quarterly_sector_kpis()` (app/calculations/
    quarterly_sector_kpis.py) into the PDF's `sectorKpis` section — the
    physical/operating KPIs (occupancy, ARPOB, GRM, volume growth, bookings...)
    from NSE filings. Every value carries its source in the notes so the
    PDF shows provenance, same as the dashboard. Data-driven: any sector added
    to `_SECTOR_METRICS` flows through with no change here."""
    if not kpis or not kpis.get("available") or not kpis.get("metrics"):
        return None
    metrics = kpis["metrics"]
    periods = sorted({p for m in metrics for p in m["series"]})[-4:]
    grid = [{"label": m["label"], "value": _fmt_kpi(m["latest_value"], m["unit"]),
             "note": m.get("source_label")} for m in metrics]
    history = None
    if len(periods) > 1:
        history = {
            "title": "Trailing quarters",
            "columns": periods,
            "rows": [{"label": m["label"],
                      "values": [(_fmt_kpi(m["series"][p], m["unit"]) if p in m["series"] else None) for p in periods]}
                     for m in metrics],
        }
    notes = []
    for m in metrics:
        bits = [m["label"] + ":", m.get("source_label") or "source n/a"]
        if m.get("confidence"):
            bits.append(f"({m['confidence'].lower()} confidence, {str(m.get('data_type') or '').lower()})")
        if m.get("source_document"):
            bits.append("— " + str(m["source_document"]))
        notes.append(_pdf_safe(" ".join(bits)))
    return {
        "sectorName": kpis.get("sector_name") or "Sector",
        "meta": f"Latest quarter {kpis.get('latest_quarter')} · {str(kpis.get('statement_type') or '').title()} · "
                "sourced from NSE filings (investor presentation, results press release, earnings call).",
        "metrics": grid,
        "history": history,
        "notes": {"title": "Sources", "items": notes, "severity": "neutral"},
    }


def _bank_roe(br: dict | None) -> dict | None:
    """Maps `compute_bank_roe_analysis()` (app/calculations/bank_roe_engine.py,
    a port of the mentor's IDFC FIRST ROE simulator) into the PDF's
    `bankRoe` section. Same numbers the dashboard tab shows."""
    if not br or not br.get("available"):
        return None
    s, sus, vc = br["start"], br.get("sustainability") or {}, br.get("valuation_check") or {}
    dup = br.get("dupont") or []
    last = dup[-1] if dup else None
    metrics = [
        {"label": "Run-rate ROE", "value": f"{s['run_rate_roe']:.1f}%", "note": s.get("run_rate_source")},
        {"label": "Price / Book", "value": f"{s['pb']:.2f}x", "note": f"Rs {s['price']:.2f} on BV Rs {s['bvps']:.1f}"},
        {"label": "Market-implied ROE", "value": f"{vc['market_implied_roe']:.1f}%" if vc.get("market_implied_roe") is not None else None,
         "note": f"COE {vc.get('coe')}% / growth {vc.get('long_run_growth')}%"},
        {"label": "Self-funded growth", "value": f"{sus['self_funded_growth']:.1f}%" if sus.get("self_funded_growth") is not None else None,
         "note": "ROE x (1 - payout)"},
        {"label": "Balance-sheet growth", "value": f"{sus['balance_sheet_growth']:.1f}%" if sus.get("balance_sheet_growth") is not None else None},
        {"label": "Crossover ROE", "value": f"{sus['crossover_roe']:.1f}%" if sus.get("crossover_roe") is not None else None,
         "note": "ROE at which growth needs no new shares"},
        {"label": "Payout ratio", "value": f"{s['payout_pct']:.1f}%"},
        {"label": "ROA x leverage (last FY)", "value": f"{last['roa']:.2f}% x {last['leverage']:.1f}x" if last else None,
         "note": f"= ROE {last['roe']:.1f}% ({last['fy']})" if last else None},
    ]
    scenarios = {
        "title": "Scenarios (10-year, mentor's ROE-simulator method)",
        "subtitle": "Equity compounds at ROE x (1 - payout); growth beyond that is funded by new shares.",
        "columns": ["ROE", "Growth", "Exit P/B", "Price multiple", "New equity", "Share count", "Verdict"],
        "columnWidths": [0.8, 0.8, 0.8, 1, 1.1, 1, 3.4],
        "rows": [{
            "label": p["name"],
            "values": [f"{p['params']['roe']:.1f}%", f"{p['params']['g']:.0f}%", f"{p['params']['pb']:.1f}x",
                       f"{p['rows'][-1]['multiple']:.1f}x", f"Rs {p['raised'] / 1000:,.0f}k Cr",
                       f"+{p['dilution'] * 100:.0f}%", p["verdict"]],
        } for p in br.get("presets") or []],
    }
    dupont = {
        "title": "DuPont: ROE = ROA x leverage (average balances)",
        "columns": ["ROE", "ROA", "Leverage", "Equity growth"],
        "rows": [{"label": d["fy"], "values": [f"{d['roe']:.1f}%", f"{d['roa']:.2f}%", f"{d['leverage']:.1f}x",
                                               f"{d['equity_growth']:.1f}%" if d.get("equity_growth") is not None else None]}
                 for d in dup],
    }
    checklist = {"title": "What to check each quarter", "severity": "neutral", "items": [
        _pdf_safe(f"{c['title']}: {c['why']}" + (f" (now {c['value']:.1f} {c['unit']})" if c.get("value") is not None else ""))
        for c in br.get("checklist") or []]}
    return {
        "meta": f"Scenario model on {br.get('sector_name', 'lender')} economics — run-rate ROE {s['run_rate_roe']:.1f}% ({s.get('run_rate_source')}).",
        "metrics": metrics,
        "insights": {"title": "What the numbers say", "severity": "neutral", "items": [_pdf_safe(t) for t in br.get("insights") or []]},
        "scenarios": scenarios,
        "dupont": dupont,
        "checklist": checklist,
        "disclaimer": br.get("disclaimer"),
    }


def build_equity_report(db: Session, analysis, extras: dict, pnl: dict, pl_intelligence: dict | None = None,
                         balance_sheet_intelligence: dict | None = None,
                         cash_flow_intelligence: dict | None = None,
                         sector_kpis: dict | None = None, bank_roe: dict | None = None) -> dict:
    """Never raises as a whole — every optional section is independently
    best-effort, matching `build_premium_extras`'s own contract, since a
    sparse-data sector (or a company mid-ingestion) should still render a
    clean report with the sections it does have data for."""
    company_info = analysis.company_info or {}
    company_id = company_info.get("stock_id") or analysis.stock_id
    scores = analysis.scores or {}
    ai = analysis.ai_analysis or {}
    risks = analysis.risks or []
    catalysts = analysis.catalysts or []
    sector_analysis = analysis.sector_analysis or {}

    from app.ingestion.live_price import fetch_live_price
    live_price = None
    try:
        live_price = fetch_live_price(company_info.get("symbol") or "", company_info.get("exchange") or "NSE")
    except Exception:
        pass

    company, market = _company_market(analysis, live_price)
    pe = sector_analysis.get("key_metrics") or []
    pe_entry = next((m for m in pe if m.get("name") == "pe_ratio"), None)
    if pe_entry and pe_entry.get("value") is not None:
        market["pe"] = float(pe_entry["value"])

    report: dict = {"company": company, "market": market}

    from app.infrastructure.database.models import CompanySummary
    summary_row = db.query(CompanySummary).filter_by(company_id=company_id).first() if company_id else None
    if summary_row and summary_row.about:
        sentences = re.split(r"(?<=[a-zA-Z]{3}\.)\s+(?=[A-Z])", summary_row.about.replace("\n", " "))
        trimmed = " ".join(sentences[:3]).strip()
        if trimmed and not trimmed.endswith("."):
            trimmed += "."
        report["overview"] = _pdf_safe(trimmed)

    price_chart = extras.get("price_chart") or {}
    pts_1y = price_chart.get("1y") or []
    if len(pts_1y) >= 2:
        step = max(1, len(pts_1y) // 30)
        sampled = pts_1y[::step]
        report["priceHistory"] = {
            "title": "Price history — 1 year",
            "series": [{"name": company["name"], "points": [
                {"label": p["date"][5:], "value": p["close"]} for p in sampled
            ]}],
        }

    takeaways = [c.get("title") for c in catalysts[:2] if c.get("title")]
    takeaways += [r.get("title") for r in risks if r.get("severity") == "HIGH" and r.get("title")][:2]
    if takeaways:
        report["keyTakeaways"] = [_pdf_safe(t) for t in takeaways]

    business: dict = {}
    if company_id:
        segments = _business_segments(db, company_id)
        if segments:
            business["segments"] = segments
        segment_mix_by_year = _segment_mix_by_year(db, company_id)
        if segment_mix_by_year:
            business["segmentMixByYear"] = segment_mix_by_year
        segment_growth = _segment_growth(db, company_id)
        if segment_growth:
            business["segmentGrowth"] = segment_growth
        segment_mix_callout = _segment_mix_callout(segment_mix_by_year, segment_growth)
        if segment_mix_callout:
            business["segmentMixCallout"] = segment_mix_callout
    client_concentration = _client_concentration(sector_analysis)
    if client_concentration:
        business["clientConcentration"] = client_concentration
    if business:
        report["business"] = business

    snapshot: dict = {
        "score": round(float(analysis.overall_score)) if analysis.overall_score is not None else None,
        "rating": ai.get("rating"),
        "confidencePct": round(float(analysis.confidence_score)) if analysis.confidence_score is not None else None,
        "dataQualityPct": round(float(analysis.data_quality_score)) if analysis.data_quality_score is not None else None,
        "valuation": ai.get("valuation_view"),
        "breakdown": _score_breakdown(scores),
    }
    if any(v is not None for k, v in snapshot.items() if k != "breakdown") or snapshot["breakdown"]:
        report["snapshot"] = snapshot

    score_detail = _score_detail(scores, analysis.metrics or {})
    if score_detail:
        report["scoreDetail"] = score_detail

    key_metrics = _key_metrics(sector_analysis)
    if key_metrics:
        report["keyMetrics"] = key_metrics

    if company_id:
        metrics = analysis.metrics or {}
        financials = _financials(pnl)
        if financials is None:
            financials = {}
        metric_groups = _metric_groups(metrics)
        if metric_groups:
            financials["metricGroups"] = metric_groups
        pnl_bridge = _pnl_bridge(metrics)
        if pnl_bridge:
            financials["pnlBridge"] = pnl_bridge
        cash_flow_bridge = _cash_flow_bridge(metrics)
        if cash_flow_bridge:
            financials["cashFlowBridge"] = cash_flow_bridge
        working_capital = _working_capital_trend(metrics)
        if working_capital:
            financials["workingCapitalTrend"] = working_capital
        # _revenue_ebitda_margin_combo/_sales_margins_combo (below) are no
        # longer wired into the PDF — PDF Upgrade plan, Priority 2 #1
        # consolidated them, `revenueSeries`+`profitSeries`+`marginSeries`
        # above, and revenue_margin_combo (built earlier in this function)
        # into ONE coordinated chart, rather than rendering 3-4 overlapping
        # revenue/margin charts on the same page. Left defined, not called,
        # in case a future non-PDF consumer wants the raw combo shape.
        eps_pe = _eps_pe_combo(db, company_id)
        if eps_pe:
            financials["epsAndPe"] = eps_pe
        valuation_vs_price = _valuation_vs_price(db, company_id)
        if valuation_vs_price:
            financials["valuationVsPrice"] = valuation_vs_price
        if financials:
            report["financials"] = financials

        if pl_intelligence:
            pnl_intelligence_section = _pnl_intelligence(pl_intelligence)
            if pnl_intelligence_section:
                report["pnlIntelligence"] = pnl_intelligence_section

        if balance_sheet_intelligence:
            bs_intelligence_section = _balance_sheet_intelligence(balance_sheet_intelligence)
            if bs_intelligence_section:
                report["balanceSheetIntelligence"] = bs_intelligence_section

        if cash_flow_intelligence:
            cf_intelligence_section = _cash_flow_intelligence(cash_flow_intelligence)
            if cf_intelligence_section:
                report["cashFlowIntelligence"] = cf_intelligence_section

        roe_section = _bank_roe(bank_roe)
        if roe_section:
            report["bankRoe"] = roe_section

        kpi_section = _sector_kpis(sector_kpis)
        if kpi_section:
            report["sectorKpis"] = kpi_section

        ownership = _ownership(db, company_id)
        if ownership:
            report["ownership"] = ownership

        market_intel = _market_intelligence(db, company_id)
        if market_intel:
            report["marketIntelligence"] = market_intel

        peers_detail = _peers_detail(analysis, extras)
        if peers_detail:
            report["peersDetail"] = peers_detail

        calendar = _calendar(db, company_id)
        if calendar:
            report["calendar"] = calendar

        concall = _concall(db, company_id, extras)
        if concall:
            report["concall"] = concall

        deep_research = _deep_research(analysis)
        if deep_research:
            report["deepResearch"] = deep_research

    if risks:
        report["risks"] = {
            "title": "Key risks",
            "severity": "negative",
            "items": [_pdf_safe(f"{r.get('title', '')}: {r.get('description', '')}".strip(": ")) for r in risks[:6]],
        }
        risk_heatmap = _risk_heatmap(risks)
        if risk_heatmap:
            report["riskHeatmap"] = risk_heatmap
    if catalysts:
        report["catalysts"] = {
            "title": "Positive catalysts",
            "severity": "positive",
            "items": [_pdf_safe(f"{c.get('title', '')}: {c.get('description', '')}".strip(": ")) for c in catalysts[:6]],
        }

    if ai:
        ai_view: dict = {
            "provider": "this app's AI fundamental analysis model",
            "rating": ai.get("rating"),
            "conviction": ai.get("conviction"),
            "valuation": ai.get("valuation_view"),
            "thesis": _pdf_safe(ai.get("executive_summary")),
            "bullCase": [_pdf_safe(b) for b in _clean_ai_points(ai.get("bull_case"))[:4]],
            "bearCase": [_pdf_safe(b) for b in _clean_ai_points(ai.get("bear_case"))[:4]],
            "monitor": [_pdf_safe(m) for m in _clean_ai_points(ai.get("monitoring_points"))[:4]],
        }
        if any(ai_view.values()):
            report["aiView"] = ai_view

    source_ledger = extras.get("source_ledger") or []
    if source_ledger:
        report["sources"] = [
            {
                "source": e["source"], "usedFor": e["used_for"],
                "tier": _TIER_LABEL.get(e["tier"], f'Tier {e["tier"]}'),
                "dateRange": (
                    f'{_short_date(e["date_from"])} – {_short_date(e["date_to"])}'
                    if e.get("date_from") and e.get("date_to") and e["date_from"][:10] != e["date_to"][:10]
                    else _short_date(e.get("date_from"))
                ),
                "facts": e["fact_count"],
                # PDF Upgrade plan, Priority 5 — this app's own derived/
                # calculated ledger rows (e.g. the P&L Analysis Engine's
                # dual-written screener metrics, source_ledger.py's
                # "Financial data / filing" bucket read straight off
                # MetricDataPoint.source) get grouped separately from
                # genuine primary/secondary/tertiary external sources.
                "isCalculated": e["source"] == "CALCULATED",
            }
            for e in source_ledger
        ]

    report["disclaimer"] = (
        "This report is an analytical research output generated by an automated system "
        "using publicly available data. It is NOT financial advice, a buy/sell "
        "recommendation, or a guarantee of future returns."
    )

    return report
