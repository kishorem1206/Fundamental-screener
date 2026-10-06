"""Builds the integrated report PDF. See the package docstring."""
from __future__ import annotations

import re
from datetime import date, datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import Session

from app.config import config
from app.framework import sector_rank, store
from app.framework.decisions import best_alternative, replacement, values
from app.infrastructure.database.models import FundamentalAnalysis, PortfolioHolding, Stock
from app.logger import logger

_HERE = Path(__file__).parent
_DEEP_TEMPLATE = _HERE.parent.parent / "bie" / "report" / "template.html.jinja"
_FONT = _HERE.parent / "fonts" / "Fraunces-Variable.ttf"
_FOOTER = """<div style="font-size:8px; width:100%; padding:0 16mm; color:#8d9994; font-family:Inter,sans-serif;
  display:flex; justify-content:space-between;"><span>Equity Research · Integrated report · __NAME__ · Part A: Stock Quality framework</span>
  <span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>"""

SCORES = [
    ("quality", "Quality", "Is this a good business? 70% Fundamental + 30% Business Quality. 50 is the gate, 65+ preferred."),
    ("fundamental", "Fundamental", "Are the financial numbers strong?"),
    ("quantitative", "Quantitative", "Are the measurable numbers getting better or worse?"),
    ("relative_strength", "Relative strength", "Is it doing better than the market, its sector and its peers?"),
    ("technical", "Technical", "Is price behaviour confirming strength or reversal?"),
    ("valuation", "Valuation", "Is the price reasonable? Higher is cheaper."),
]
PARTS = [("fundamental", "Fundamental Score"), ("business_quality", "Business Quality"), ("quantitative", "Quantitative Score"),
         ("relative_strength", "Relative Strength"), ("technical", "Technical Score"), ("valuation", "Valuation Score")]
LABELS = {
    "growth": "Growth", "profitability": "Profitability", "cash_flow": "Cash flow", "balance_sheet": "Balance sheet",
    "efficiency": "Efficiency (add-on)", "earnings_consistency": "Earnings consistency", "working_capital_trend": "Working-capital trend",
    "share_dilution": "Share dilution", "dividend_sustainability": "Dividend sustainability", "durability": "Durability of returns",
    "margin_resilience": "Margin resilience", "predictability": "Predictability", "capital_allocation": "Capital allocation",
    "promoter_behaviour": "Promoter behaviour", "management_credibility": "Management credibility",
    "growth_acceleration": "Growth acceleration", "margin_change": "Margin change", "return_change": "Return change",
    "debt_change": "Debt change", "volatility": "Volatility", "drawdown": "Drawdown", "risk_adjusted_return": "Risk-adjusted return",
    "vs_market": "vs Nifty 50", "vs_sector": "vs sector", "sector_percentile": "Sector percentile",
    "resilience": "Resilience in market falls", "drawdown_vs_market": "Drawdown vs market", "near_52_week_high": "Near 52-week high",
    "trend_structure": "Trend structure", "moving_averages": "Moving averages", "rsi": "RSI (14)", "macd": "MACD",
    "volume": "Volume confirmation", "breakout": "Breakout / breakdown", "base": "Base / contraction", "reversal": "Reversal structure",
    "pe_vs_history": "P/E vs own history", "pe_vs_sector": "P/E vs industry", "pb_vs_history": "P/B vs own history",
    "pb_vs_sector": "P/B vs industry", "peg": "PEG", "ev_ebitda": "EV/EBITDA", "fcf_yield": "Free-cash-flow yield",
    "deep_report": "Deep report value",
}
_HIDDEN = {"score", "weight", "source", "governance_flags", "note", "basis"}
_PART_SOURCE = {
    "fundamental": "the app's existing category scores (Screener first, Yahoo where Screener has nothing) plus the framework inputs listed",
    "relative_strength": "NSE daily index file and stored adjusted daily prices",
    "technical": "stored daily prices, with the technical screener's RSI, MACD and divergence engines",
    "valuation": "Screener market cap moved to the price date by the stored close; Screener quarterly net profit and net worth; "
                 "industry peers from the stocks table",
}


def band(v: float | None) -> str:
    if v is None:
        return "—"
    return "strong" if v >= 65 else "good" if v >= 50 else "borderline" if v >= 40 else "weak" if v >= 30 else "very weak"


def _fmt(v) -> str:
    if isinstance(v, float):
        return f"{v:,.2f}".rstrip("0").rstrip(".")
    if isinstance(v, dict):
        return ", ".join(f"{k} {_fmt(x)}" for k, x in v.items())
    if isinstance(v, list):
        return ", ".join(_fmt(x) for x in v)
    return str(v)


def facts(part: dict) -> str:
    if part.get("score") is None and part.get("reason"):
        return part["reason"]
    return " · ".join(f"{k.replace('_', ' ')}: {_fmt(v)}" for k, v in part.items() if k not in _HIDDEN and v not in (None, "", [], {}))


def _style(font_url: str) -> str:
    """The deep report's own stylesheet (itself the app's editorial design), so all three parts look alike."""
    text = _DEEP_TEMPLATE.read_text(encoding="utf-8")
    m = re.search(r"<style>(.*?)</style>", text, re.S)
    return (m.group(1) if m else "").replace("{{ font_url }}", font_url)


def _editorial_pdf(db: Session, stock: Stock) -> tuple[str | None, str]:
    a = (db.query(FundamentalAnalysis).filter(FundamentalAnalysis.stock_id == stock.id, FundamentalAnalysis.status == "COMPLETED")
         .order_by(FundamentalAnalysis.created_at.desc()).first())
    if a is None:
        return None, "No full analysis has been run for this company, so the editorial report is not included. Run a full analysis to add it."
    if a.report_path and Path(a.report_path).exists():
        return a.report_path, f"Editorial report from the full analysis of {a.created_at:%d %b %Y}."
    from app.reporting.editorial_pdf_service import generate_editorial_pdf

    path = generate_editorial_pdf(a.id, db)
    a.report_path = path
    db.commit()
    return path, f"Editorial report from the full analysis of {a.created_at:%d %b %Y}."


def _deep_pdf(db: Session, stock: Stock) -> tuple[str | None, str]:
    from app.bie.jobs import built_at

    if built_at(db, stock.id) is None:
        return None, "The deep report has not been built for this company, so it is not included. Build it from the Deep Report tab."
    today = Path(config.reports_dir).resolve() / f"BIE-{stock.symbol}-{date.today():%Y%m%d}.pdf"
    if today.exists():
        return str(today), "Deep report rendered today from the facts on file."
    from app.bie.report.render import render_report

    return render_report(db, stock.id), "Deep report rendered from the facts on file."


def context(db: Session, stock: Stock) -> dict:
    row = store.latest(db, stock.id)
    if row is None:
        raise LookupError(f"No framework scores for {stock.symbol} yet")
    v = values(row)
    detail = row.detail or {}
    peers = [r for r in store.latest_for_all(db) if (s := db.get(Stock, r.stock_id)) is not None and s.sector == stock.sector]
    rank = sector_rank.ranks([(r.stock_id, stock.sector, float(r.quality) if r.quality is not None else None) for r in peers]).get(stock.id)
    alt = best_alternative(db, stock, stock.id)
    repl = (replacement({**v, "symbol": stock.symbol, "valuation_view": row.valuation_view}, alt, detail, store.latest(db, alt["stock_id"]))
            if alt and row.classification in ("Replacement Candidate", "Improving / Watch", "Avoid") else None)
    explanation = detail.get("explanation")
    if not explanation:
        from app.framework.explain import fallback, pack
        explanation = fallback(pack(v, detail, alt))
    holding = db.query(PortfolioHolding).filter(PortfolioHolding.stock_id == stock.id).all()
    parts = []
    for key, title in PARTS:
        d = detail.get(key) or {}
        parts.append({"key": key, "title": title, "score": d.get("score"), "reason": d.get("reason"),
                      "rows": [{"name": LABELS.get(n, n), "weight": p.get("weight"), "score": p.get("score"), "facts": facts(p),
                                "note": p.get("note"), "source": p.get("source") or p.get("basis")}
                               for n, p in (d.get("components") or {}).items()],
                      "not_measured": d.get("not_measured"), "source": _PART_SOURCE.get(key) or d.get("source")})
    return {
        "stock": stock, "row": row, "v": v, "detail": detail, "rank": rank, "alt": alt, "replacement": repl,
        "explanation": explanation, "decision": detail.get("decision") or {}, "momentum": detail.get("momentum") or {},
        "quality": detail.get("quality") or {}, "valuation": detail.get("valuation") or {}, "trend": detail.get("trend") or {},
        "why_holding_up": (detail.get("relative_strength") or {}).get("why_holding_up"),
        "double_in": (detail.get("fundamental") or {}).get("double_in") or {},
        "scores": [{"key": k, "label": l, "question": q, "value": v.get(k),
                    "band": ((row.valuation_view or "—").lower() if k == "valuation" else band(v.get(k)))} for k, l, q in SCORES],
        "parts": parts, "held": sum(float(h.value) for h in holding) if holding else None,
        "generated": datetime.now(timezone.utc), "band": band,
    }


def _render_part_a(ctx: dict, contents: list[dict], out: Path) -> int:
    from playwright.sync_api import sync_playwright
    from pypdf import PdfReader

    env = Environment(loader=FileSystemLoader(_HERE), autoescape=select_autoescape(["html", "jinja"]))
    html = env.get_template("framework.html.jinja").render(**ctx, contents=contents, style=_style(_FONT.as_uri()))
    html_path = out.with_suffix(".html")
    html_path.write_text(html, encoding="utf-8")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page()
            page.goto(html_path.as_uri(), wait_until="load")
            page.evaluate("document.fonts.ready")
            page.pdf(path=str(out), format="A4", print_background=True, display_header_footer=True, header_template="<div></div>",
                     footer_template=_FOOTER.replace("__NAME__", ctx["stock"].symbol),
                     margin={"top": "16mm", "bottom": "16mm", "left": "16mm", "right": "16mm"})
        finally:
            browser.close()
    return len(PdfReader(str(out)).pages)


def build(db: Session, symbol: str) -> str:
    from pypdf import PdfReader, PdfWriter

    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    if stock is None:
        raise LookupError(f"Unknown symbol '{symbol}'")
    ctx = context(db, stock)
    editorial, editorial_note = _editorial_pdf(db, stock)
    deep, deep_note = _deep_pdf(db, stock)
    reports = Path(config.reports_dir).resolve()
    reports.mkdir(parents=True, exist_ok=True)
    stem = f"INTEGRATED-{stock.symbol}-{date.today():%Y%m%d}"
    part_a = reports / f"{stem}-A.pdf"

    def contents(a_pages: int) -> list[dict]:
        out, page = [{"part": "A", "title": "Stock Quality framework: decision, six scores and their inputs", "page": 2, "note": None}], a_pages + 1
        for part, title, path, note in (("B", "Editorial report", editorial, editorial_note), ("C", "Deep report", deep, deep_note)):
            out.append({"part": part, "title": title, "page": page if path else None, "note": note})
            if path:
                page += len(PdfReader(path).pages)
        return out

    a_pages = _render_part_a(ctx, contents(1), part_a)          # first pass: count Part A's pages
    a_pages = _render_part_a(ctx, contents(a_pages), part_a)    # second: contents with the real page numbers
    writer = PdfWriter()
    for path in (part_a, editorial, deep):
        if path:
            writer.append(str(path))
    writer.add_metadata({"/Title": f"{stock.company_name} — integrated report", "/Author": "Equity Research"})
    final = reports / f"{stem}.pdf"
    with open(final, "wb") as fh:
        writer.write(fh)
    logger.info("integrated report built", symbol=stock.symbol, part_a_pages=a_pages, editorial=bool(editorial), deep=bool(deep))
    return str(final)
