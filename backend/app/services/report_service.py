"""
PDF report generation using ReportLab.
Generates a professional equity research report from a completed analysis.
"""
from __future__ import annotations
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.graphics.shapes import Drawing, String, Rect
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.legends import Legend

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from app.config import config
from app.logger import logger


# ── "Mindful Finance" design system — ported 2026-09-15 from
# `Macro analysis.html`, the same tokens the banking Jinja/HTML report
# (app/reporting/templates/banking_report.html.jinja) already uses, so all
# three render surfaces (this PDF, the banking PDF, the React UI) now share
# one visual language instead of this file's own earlier bright-blue
# SaaS-dashboard palette. ───────────────────────────────────────────────────

BG_DARK = colors.HexColor("#070f1f")     # navy-950
BG_CARD = colors.HexColor("#0f1f3d")     # navy-850 — flat fallback (ReportLab has no blur/glass)
ACCENT = colors.HexColor("#c9a227")      # gold — primary brand/chart accent
ACCENT_GOLD_BRIGHT = colors.HexColor("#e8c766")
ACCENT_GREEN = colors.HexColor("#4fb3a0")   # teal — positive/improving
ACCENT_RED = colors.HexColor("#d9694f")     # terracotta red — negative/declining
ACCENT_YELLOW = colors.HexColor("#e0793c")  # orange — warning/medium severity
TEXT_PRIMARY = colors.HexColor("#f3f0e6")   # ink — warm off-white
TEXT_SECONDARY = colors.HexColor("#a9b3c9") # ink-dim — legible ONLY on navy/BG_CARD surfaces
TEXT_DIM = colors.HexColor("#6f7c96")       # ink-faint — labels/captions, legible on white (~4.4:1)
BORDER = colors.HexColor("#26365c")         # a visible hairline against navy-850 cards
DARK_NAVY = colors.HexColor("#070f1f")      # navy-950 — dark text on the white cover page
# TEXT_SECONDARY (#a9b3c9) is a light ink-dim tone built for navy card
# backgrounds; every table in this file defaults to a BG_CARD (navy) fill via
# _table_style(), so text inside tables is correctly light-on-dark. But many
# prose paragraphs (Company Overview, AI narrative, blueprint sections, risk-
# card descriptions) are appended straight to the white-page story, or sit on
# a near-white alpha-tinted card (risk cards, bull/bear cells) — TEXT_SECONDARY
# there reads as washed-out, low-contrast text. Found 2026-09-15 visually
# verifying the "Mindful Finance" migration. TEXT_BODY/TEXT_BODY_DIM are the
# dark equivalents for those on-white/on-light-tint contexts.
TEXT_BODY = colors.HexColor("#33415c")      # dark slate-navy — prose on white/light backgrounds
TEXT_BODY_DIM = colors.HexColor("#5b6b85")  # de-emphasized text on white/light backgrounds

# Fraunces — the reference's display serif for headings/big numbers. A
# genuine static-weight file doesn't exist upstream (Google's Fraunces is
# variable-only, confirmed checking the fonts repo), but the variable TTF
# registers and renders cleanly on its own (verified visually) — no
# fonttools instancing needed. Falls back to Helvetica-Bold (this file's
# original heading font) if the bundled file is ever missing, so a report
# still generates rather than crashing on a font-registration error.
_FRAUNCES_PATH = Path(__file__).resolve().parent.parent / "reporting" / "fonts" / "Fraunces-Variable.ttf"
try:
    pdfmetrics.registerFont(TTFont("Fraunces", str(_FRAUNCES_PATH)))
    FONT_DISPLAY = "Fraunces"
except Exception as e:
    logger.warning("report_service: Fraunces font registration failed, falling back to Helvetica-Bold", error=str(e))
    FONT_DISPLAY = "Helvetica-Bold"


def _styles():
    styles = getSampleStyleSheet()
    return {
        # TEXT_PRIMARY (near-white, #f1f5f9) was designed for a dark canvas
        # background that this cover page never actually paints — on the
        # real (white) page it was nearly invisible. Found 2026-09-13 while
        # adding the price line below (which inherited the same bug via the
        # same convention). Uses DARK_NAVY instead, which is legible on white.
        "title": ParagraphStyle("title", fontName=FONT_DISPLAY, fontSize=24,
                                textColor=DARK_NAVY, alignment=TA_CENTER, spaceAfter=4),
        "subtitle": ParagraphStyle("subtitle", fontName="Helvetica", fontSize=12,
                                   textColor=TEXT_BODY_DIM, alignment=TA_CENTER, spaceAfter=4),
        "section": ParagraphStyle("section", fontName=FONT_DISPLAY, fontSize=16,
                                  textColor=ACCENT, spaceBefore=16, spaceAfter=8),
        # "body"/"bullet" are for text inside tables, which default to a navy
        # (BG_CARD) fill via _table_style() — TEXT_SECONDARY is correctly
        # light-on-dark there. Free paragraphs on the white page use
        # "body_light"/"bullet_light" instead (see TEXT_BODY comment above).
        "body": ParagraphStyle("body", fontName="Helvetica", fontSize=9,
                               textColor=TEXT_SECONDARY, leading=14, spaceAfter=4),
        "body_light": ParagraphStyle("body_light", fontName="Helvetica", fontSize=9,
                                     textColor=TEXT_BODY, leading=14, spaceAfter=4),
        "label": ParagraphStyle("label", fontName="Helvetica-Bold", fontSize=8,
                                textColor=TEXT_DIM, spaceAfter=2),
        "big_number": ParagraphStyle("big_number", fontName=FONT_DISPLAY, fontSize=28,
                                     textColor=ACCENT, alignment=TA_CENTER),
        "caption": ParagraphStyle("caption", fontName="Helvetica", fontSize=8,
                                  textColor=TEXT_DIM, alignment=TA_CENTER, spaceAfter=2),
        "bullet": ParagraphStyle("bullet", fontName="Helvetica", fontSize=9,
                                 textColor=TEXT_SECONDARY, leading=13, leftIndent=12,
                                 firstLineIndent=-8, spaceAfter=3),
        "bullet_light": ParagraphStyle("bullet_light", fontName="Helvetica", fontSize=9,
                                       textColor=TEXT_BODY, leading=13, leftIndent=12,
                                       firstLineIndent=-8, spaceAfter=3),
        "disclaimer": ParagraphStyle("disclaimer", fontName="Helvetica", fontSize=7,
                                     textColor=TEXT_DIM, alignment=TA_CENTER),
        "score_label": ParagraphStyle("score_label", fontName="Helvetica-Bold", fontSize=10,
                                      textColor=TEXT_PRIMARY, alignment=TA_CENTER),
        "score_value": ParagraphStyle("score_value", fontName=FONT_DISPLAY, fontSize=19,
                                      textColor=ACCENT, alignment=TA_CENTER),
        # Real bug found 2026-09-15: text ratings ("ATTRACTIVE") shared
        # score_value's size with numeric scores ("77") — at the Investment
        # Snapshot's ~86pt usable column width, a bold 10-letter word has no
        # break point and force-splits mid-word. Word-badges get their own
        # smaller size.
        "score_value_text": ParagraphStyle("score_value_text", fontName=FONT_DISPLAY, fontSize=13,
                                           textColor=ACCENT, alignment=TA_CENTER),
    }


def _rating_color(rating: str | None) -> object:
    if not rating:
        return TEXT_SECONDARY
    r = rating.upper()
    if r in ("STRONG", "CHEAP", "ATTRACTIVE", "BUY"):
        return ACCENT_GREEN
    if r in ("POOR", "VERY_EXPENSIVE", "SELL"):
        return ACCENT_RED
    if r in ("WEAK", "EXPENSIVE", "HOLD"):
        return ACCENT_YELLOW
    return ACCENT


def _fmt(val, suffix="", decimals=1, na_str="N/A"):
    if val is None:
        return na_str
    try:
        return f"{float(val):.{decimals}f}{suffix}"
    except (TypeError, ValueError):
        return na_str


def _fmt_cr(val, decimals=1, na_str="N/A"):
    """Raw absolute-rupee float -> "Rs. X,XXX Cr", same /1e7 convention
    already used for market cap on the cover page. Real bug found
    2026-09-15: ForwardEstimate revenue rows are raw yfinance absolute
    rupees (unlike market cap / P&L figures, which are pre-scaled
    elsewhere), and rendered as "207300000000.00" without this."""
    if val is None:
        return na_str
    try:
        cr = float(val) / 1e7
    except (TypeError, ValueError):
        return na_str
    return f"Rs. {cr:,.{decimals}f} Cr"


_PDF_UNICODE_REPLACEMENTS = {
    "‘": "'", "’": "'", "“": '"', "”": '"',
    "–": "-", "—": "--", "…": "...", "•": "-",
    " ": " ", "�": "",
}


def _sanitize_for_pdf(text: str | None) -> str | None:
    """AI-generated blueprint/ai_analysis text goes straight into
    Paragraph() with no encoding pass — ReportLab's default Helvetica only
    covers WinAnsiEncoding (roughly Latin-1); any character outside that
    renders as a tofu box. Real bug found 2026-09-15: "debt■to■equity" in a
    generated ITC report. Common Unicode punctuation is mapped to its ASCII
    equivalent first; anything still outside Latin-1 is dropped rather than
    guessed at."""
    if not text:
        return text
    for src, repl in _PDF_UNICODE_REPLACEMENTS.items():
        text = text.replace(src, repl)
    return "".join(c for c in text if ord(c) < 256)


def _metric_table_rows(data: list[tuple]) -> list[list]:
    """Build table rows from (label, value) pairs."""
    return [[Paragraph(str(label), ParagraphStyle("tl", fontName="Helvetica", fontSize=8,
                                                   textColor=TEXT_SECONDARY)),
             Paragraph(str(value), ParagraphStyle("tv", fontName="Helvetica-Bold", fontSize=8,
                                                   textColor=TEXT_PRIMARY, alignment=TA_RIGHT))]
            for label, value in data]


def _table_style(alternating: bool = True) -> TableStyle:
    cmds = [
        ("BACKGROUND", (0, 0), (-1, -1), BG_CARD),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [BG_CARD, colors.HexColor("#142a4f")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    return TableStyle(cmds)


_TREND_LABEL = {
    "STRONGLY_IMPROVING": ("Strongly Improving", ACCENT_GREEN),
    "IMPROVING": ("Improving", ACCENT_GREEN),
    "STABLE": ("Stable", TEXT_SECONDARY),
    "DETERIORATING": ("Deteriorating", ACCENT_YELLOW),
    "STRONGLY_DETERIORATING": ("Strongly Deteriorating", ACCENT_RED),
    "VOLATILE": ("Volatile", ACCENT_YELLOW),
}


def _kpi_card_row(story: list, cards: list[dict], W: float, cols: int = 4) -> None:
    """Design-doc KPI card sketch (label / big value / status badge),
    reusable across the cover-page snapshot tiles and the Key Financial
    Metrics grid instead of one-off bespoke tables. `cards`:
    [{"label", "value", "status"?, "status_color"?, "sub"?}, ...]. Cards
    render `cols` per row; a short final row is padded with blank cells so
    ReportLab's Table gets a consistent column count."""
    label_style = ParagraphStyle("kpi_label", fontName="Helvetica", fontSize=7.5, textColor=TEXT_DIM)
    value_style = ParagraphStyle("kpi_value", fontName=FONT_DISPLAY, fontSize=16,
                                  textColor=TEXT_PRIMARY, spaceBefore=2)
    sub_style = ParagraphStyle("kpi_sub", fontName="Helvetica", fontSize=7, textColor=TEXT_DIM, spaceBefore=2)

    col_w = W / cols
    rows_out = []
    for i in range(0, len(cards), cols):
        row_cards = cards[i:i + cols]
        row_data = []
        for card in row_cards:
            cell = [Paragraph(str(card["label"]).upper(), label_style), Paragraph(str(card["value"]), value_style)]
            status = card.get("status")
            if status:
                color = card.get("status_color") or TEXT_SECONDARY
                cell.append(Paragraph(f'<font color="#{color.hexval()[2:]}">{status}</font>', sub_style))
            elif card.get("sub"):
                cell.append(Paragraph(str(card["sub"]), sub_style))
            row_data.append(cell)
        while len(row_data) < cols:
            row_data.append([Paragraph("", label_style)])
        rows_out.append(row_data)

    t = Table(rows_out, colWidths=[col_w] * cols)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BG_CARD),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.3 * cm))


def _score_bar_drawing(value: float | None, width: float = 150, height: float = 8) -> Drawing:
    """Horizontal 0-100 score bar — ReportLab-native equivalent of
    charts.py::score_bar's SVG version (this renderer has no SVG support),
    used to give the Investment Snapshot's category scores (design doc
    item #8) visual weight instead of a plain label/value table row."""
    d = Drawing(width, height)
    d.add(Rect(0, 0, width, height, fillColor=BORDER, strokeColor=None, rx=height / 2, ry=height / 2))
    if value is not None:
        v = max(0.0, min(100.0, value))
        color = ACCENT_GREEN if v >= 65 else ACCENT if v >= 40 else ACCENT_YELLOW if v >= 20 else ACCENT_RED
        bar_w = width * v / 100
        if bar_w > 0:
            d.add(Rect(0, 0, bar_w, height, fillColor=color, strokeColor=None, rx=height / 2, ry=height / 2))
    return d


def _render_investment_snapshot(story: list, analysis, ai: dict, scores: dict, S: dict, W: float) -> None:
    """Design doc item #8: "Investment Snapshot should become a hero
    component" — moved to the cover page (2026-09-15) from its former spot
    deep in the report, right after the Key Financial Metrics table."""
    story.append(Paragraph("Investment Snapshot", S["section"]))
    overall = analysis.overall_score
    confidence = analysis.confidence_score
    dq = analysis.data_quality_score
    ai_rating = ai.get("rating") or analysis.ai_rating or "—"
    val_rating = ai.get("valuation_view") or analysis.valuation_rating or "—"

    snapshot_data = [
        [Paragraph("Fundamental Score", S["score_label"]),
         Paragraph("AI Rating", S["score_label"]),
         Paragraph("Confidence", S["score_label"]),
         Paragraph("Data Quality", S["score_label"]),
         Paragraph("Valuation", S["score_label"])],
        [Paragraph(f"{overall:.0f}/100" if overall else "—", S["score_value"]),
         Paragraph(f'<font color="#{_rating_color(ai_rating).hexval()[2:]}">{ai_rating}</font>', S["score_value_text"]),
         Paragraph(f"{confidence:.0f}%" if confidence else "—", S["score_value"]),
         Paragraph(f"{dq:.0f}%" if dq else "—", S["score_value"]),
         Paragraph(f'<font color="#{_rating_color(val_rating).hexval()[2:]}">{val_rating}</font>', S["score_value_text"])],
    ]
    t = Table(snapshot_data, colWidths=[W / 5] * 5)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BG_CARD),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5 * cm))

    # ── Component scores ──────────────────────────────────────────────────
    story.append(Paragraph("Score Breakdown", S["section"]))
    score_items = [
        ("Growth", scores.get("growth")),
        ("Profitability", scores.get("profitability")),
        ("Cash Flow", scores.get("cash_flow")),
        ("Balance Sheet", scores.get("balance_sheet")),
        ("Efficiency", scores.get("efficiency")),
        ("Valuation", scores.get("valuation")),
    ]
    score_label_style = ParagraphStyle("sl", fontName="Helvetica-Bold", fontSize=9, textColor=TEXT_SECONDARY)
    score_value_style = ParagraphStyle("sv", fontName="Helvetica-Bold", fontSize=9,
                                        textColor=TEXT_PRIMARY, alignment=TA_RIGHT)
    score_rows = [
        [Paragraph(label, score_label_style), _score_bar_drawing(val), Paragraph(_fmt(val, "/100", 0), score_value_style)]
        for label, val in score_items
    ]
    t = Table(score_rows, colWidths=[W * 0.28, W * 0.52, W * 0.2])
    style = _table_style()
    style.add("ALIGN", (1, 0), (1, -1), "CENTER")
    t.setStyle(style)
    story.append(t)
    story.append(Spacer(1, 0.5 * cm))


def _render_key_takeaways(story: list, risks: list, catalysts: list, S: dict) -> None:
    """Design doc item #4's cover-page sketch: 3-5 scannable checkmark/
    warning bullets synthesized from data already on the analysis row — no
    new LLM call, pure selection (top catalysts as +, top HIGH-severity
    risks as an alert), same "reuse what's already there" discipline as
    every other cover-page addition this session."""
    highlights = [(c.get("title", ""), True) for c in (catalysts or [])[:2]]
    highlights += [(r.get("title", ""), False) for r in (risks or []) if r.get("severity") == "HIGH"][:2]
    highlights = [(t, positive) for t, positive in highlights if t]
    if not highlights:
        return
    story.append(Paragraph("Key Takeaways", S["label"]))
    for title, positive in highlights:
        # Plain ASCII marks, not Unicode check/warning glyphs — WinAnsiEncoding
        # (this renderer's font encoding) has no checkmark glyph; a raw ✓
        # would just be a second tofu-box bug of the same kind item #1-4
        # just fixed.
        mark = f'<font color="#{ACCENT_GREEN.hexval()[2:]}">+</font>' if positive \
            else f'<font color="#{ACCENT_YELLOW.hexval()[2:]}">!</font>'
        story.append(Paragraph(f"{mark} {_sanitize_for_pdf(title)}", S["bullet_light"]))
    story.append(Spacer(1, 0.3 * cm))


def _render_blueprint_sections(story: list, sections: list, S: dict) -> None:
    """Shared renderer for a list of Report Blueprint sections (Stage L3) —
    factored out so both the general narrative block and the P&L-specific
    one (Stage P3) use the same dispatch logic."""
    for section in sections:
        story.append(Paragraph(_sanitize_for_pdf(section.get("title", "")), S["label"]))
        if section.get("content"):
            story.append(Paragraph(_sanitize_for_pdf(section["content"]), S["body_light"]))
        for kp in section.get("key_points") or []:
            story.append(Paragraph(f"• {_sanitize_for_pdf(kp)}", S["bullet_light"]))
        for item in section.get("items") or []:
            title, description = _sanitize_for_pdf(item.get("title", "")), _sanitize_for_pdf(item.get("description", ""))
            sev = item.get("severity")
            if sev:
                color = ACCENT_RED if sev == "HIGH" else ACCENT_YELLOW if sev == "MEDIUM" else TEXT_DIM
                story.append(Paragraph(
                    f'<font color="#{color.hexval()[2:]}"><b>[{sev}]</b></font> '
                    f'<b>{title}</b>: {description}',
                    S["body_light"]
                ))
            else:
                story.append(Paragraph(f'<b>{title}</b>: {description}', S["bullet_light"]))
        story.append(Spacer(1, 0.2 * cm))


def _pnl_year_label(period: str) -> str:
    if period == "TTM":
        return "TTM"
    try:
        return f"FY{period[2:4]}"
    except (TypeError, IndexError):
        return period


def _render_pnl_dashboard_header(story: list, pnl: dict, S: dict, W: float) -> None:
    """Design doc item #9: "P&L section must feel like a financial
    dashboard" — a KPI row (latest Revenue/PAT/EPS/OPM, each with a trend
    badge from the same `trend_direction()` used everywhere else in this
    report) and a large Revenue vs. Operating Profit chart, both ahead of
    the detailed 12-year table."""
    from app.calculations.engine import trend_direction

    table = pnl.get("table") or {}
    fiscal_years = pnl.get("fiscal_years") or []
    if not fiscal_years:
        return
    latest = fiscal_years[-1]

    def _latest_and_trend(label: str, key: str, unit: str, decimals: int = 0) -> dict:
        series = table.get(key) or {}
        ordered = [series.get(y) for y in fiscal_years if series.get(y) is not None]
        card = {"label": label, "value": _fmt(series.get(latest), unit, decimals)}
        if len(ordered) >= 2:
            trend = trend_direction(ordered)
            if trend in _TREND_LABEL:
                status_label, status_color = _TREND_LABEL[trend]
                card["status"], card["status_color"] = status_label, status_color
        return card

    _kpi_card_row(story, [
        _latest_and_trend("Revenue (Cr)", "sales", "", 0),
        _latest_and_trend("Net Profit (Cr)", "net_profit", "", 0),
        _latest_and_trend("EPS (Rs.)", "eps", "", 2),
        _latest_and_trend("OPM", "opm", "%", 1),
    ], W)

    # Large Revenue & Operating Profit trend — the report's other bar+line
    # combos (peer performance, price history) use HorizontalLineChart; this
    # is deliberately a grouped VerticalBarChart instead since both series
    # here are absolute Cr figures on the same scale, not a rate overlaid
    # on a level.
    sales_series = table.get("sales") or {}
    op_series = table.get("operating_profit") or {}
    years = [y for y in fiscal_years if sales_series.get(y) is not None][-10:]
    if len(years) >= 2:
        story.append(Spacer(1, 0.2 * cm))
        story.append(Paragraph("Revenue &amp; Operating Profit (Rs. Cr)", S["label"]))
        drawing = Drawing(W, 220)
        chart = VerticalBarChart()
        chart.x, chart.y = 45, 30
        chart.width, chart.height = W - 60, 165
        chart.data = [[sales_series.get(y, 0) for y in years], [op_series.get(y, 0) or 0 for y in years]]
        chart.categoryAxis.categoryNames = [_pnl_year_label(y) for y in years]
        chart.categoryAxis.labels.fontSize = 7
        chart.valueAxis.labelTextFormat = "%0.0f"
        chart.bars[0].fillColor = ACCENT
        chart.bars[1].fillColor = ACCENT_GREEN
        chart.groupSpacing = 6
        chart.barSpacing = 1
        drawing.add(chart)
        legend = Legend()
        legend.x, legend.y = 45, 205
        legend.alignment = "left"
        legend.fontSize = 7
        legend.colorNamePairs = [(ACCENT, "Revenue"), (ACCENT_GREEN, "Operating Profit")]
        drawing.add(legend)
        story.append(drawing)
    story.append(Spacer(1, 0.3 * cm))


def _render_pnl_table(story: list, pnl: dict, S: dict, W: float) -> None:
    table = pnl.get("table", {})
    fiscal_years = pnl.get("fiscal_years", [])
    recent = fiscal_years[-6:] if len(fiscal_years) > 6 else fiscal_years
    columns = recent + (["TTM"] if "TTM" in (table.get("sales") or {}) else [])
    if not columns:
        return

    header_style = ParagraphStyle("pnl_h", fontName="Helvetica-Bold", fontSize=7.5,
                                   textColor=TEXT_PRIMARY, alignment=TA_RIGHT)
    label_style = ParagraphStyle("pnl_l", fontName="Helvetica", fontSize=7.5, textColor=TEXT_SECONDARY)
    cell_style = ParagraphStyle("pnl_c", fontName="Helvetica", fontSize=7.5,
                                 textColor=TEXT_PRIMARY, alignment=TA_RIGHT)

    rows_spec = [
        ("Sales (Cr)", "sales", 0), ("Operating Profit (Cr)", "operating_profit", 0),
        ("OPM %", "opm", 1), ("Other Income (Cr)", "other_income", 0),
        ("Interest (Cr)", "interest", 0), ("Depreciation (Cr)", "depreciation", 0),
        ("PBT (Cr)", "pbt", 0), ("Net Profit (Cr)", "net_profit", 0), ("EPS (Rs.)", "eps", 2),
    ]
    data = [[Paragraph("Particulars", header_style)] + [Paragraph(_pnl_year_label(c), header_style) for c in columns]]
    for label, key, decimals in rows_spec:
        series = table.get(key) or {}
        row = [Paragraph(label, label_style)]
        for c in columns:
            v = series.get(c)
            row.append(Paragraph(_fmt(v, "", decimals) if v is not None else "—", cell_style))
        data.append(row)

    col_widths = [W * 0.24] + [W * 0.76 / len(columns)] * len(columns)
    t = Table(data, colWidths=col_widths)
    t.setStyle(_table_style())
    story.append(t)
    story.append(Spacer(1, 0.3 * cm))


def _render_pnl_cagr_cards(story: list, pnl: dict, S: dict, W: float) -> None:
    growth = pnl.get("growth", {})
    spc = pnl.get("stock_price_cagr", {})
    header_style = ParagraphStyle("cagr_h", fontName="Helvetica-Bold", fontSize=7.5,
                                   textColor=TEXT_PRIMARY, alignment=TA_RIGHT)
    label_style = ParagraphStyle("cagr_l", fontName="Helvetica", fontSize=7.5, textColor=TEXT_SECONDARY)
    cell_style = ParagraphStyle("cagr_c", fontName="Helvetica", fontSize=7.5,
                                 textColor=TEXT_PRIMARY, alignment=TA_RIGHT)

    windows = ["10y", "7y", "5y", "3y"]
    rows_spec = [
        ("Sales CAGR", growth.get("sales_cagr", {})),
        ("Profit CAGR", growth.get("profit_cagr", {})),
        ("EPS CAGR", growth.get("eps_cagr", {})),
        ("Stock Price CAGR", spc),
    ]
    data = [[Paragraph("Compounded Growth", header_style)] + [Paragraph(w.upper(), header_style) for w in windows]]
    for label, series in rows_spec:
        row = [Paragraph(label, label_style)]
        for w in windows:
            v = series.get(w)
            row.append(Paragraph(_fmt(v, "%") if v is not None else "—", cell_style))
        data.append(row)

    col_widths = [W * 0.3] + [W * 0.7 / len(windows)] * len(windows)
    t = Table(data, colWidths=col_widths)
    t.setStyle(_table_style())
    story.append(t)
    story.append(Spacer(1, 0.3 * cm))


def _render_chip_row(story: list, items: list[str], color, W: float, cols: int = 2) -> None:
    """Design doc item #9/#15: "Use visual chips" instead of a plain
    bulleted list — a colored-background badge per flag, several per row,
    rather than a colored dot next to plain text."""
    if not items:
        return
    chip_style = ParagraphStyle("chip", fontName="Helvetica-Bold", fontSize=8, textColor=color)
    col_w = W / cols
    rows_out = []
    for i in range(0, len(items), cols):
        row_items = items[i:i + cols]
        row = [Paragraph(text, chip_style) for text in row_items]
        while len(row) < cols:
            row.append(Paragraph("", chip_style))
        rows_out.append(row)
    t = Table(rows_out, colWidths=[col_w] * cols)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.Color(color.red, color.green, color.blue, alpha=0.12)),
        ("BOX", (0, 0), (-1, -1), 0, colors.transparent),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.Color(color.red, color.green, color.blue, alpha=0.12)]),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.15 * cm))


_ACRONYMS = {"Roe": "ROE", "Roa": "ROA", "Roce": "ROCE", "Roic": "ROIC", "Ebitda": "EBITDA",
             "Eps": "EPS", "Pat": "PAT", "Pbt": "PBT", "Cagr": "CAGR", "Fcf": "FCF", "Yoy": "YoY",
             "Opm": "OPM", "Npm": "NPM", "Gpm": "GPM", "Pe": "P/E", "Pb": "P/B", "Cfo": "CFO"}


def _render_pnl_flags(story: list, pnl: dict, S: dict, W: float) -> None:
    def _readable(flag: str) -> str:
        words = flag.replace("_", " ").title().split()
        return " ".join(_ACRONYMS.get(w, w) for w in words)

    red_flags = pnl.get("red_flags") or []
    signals = pnl.get("positive_signals") or []
    if red_flags:
        story.append(Paragraph("P&amp;L Red Flags", S["label"]))
        _render_chip_row(story, [_readable(f) for f in red_flags], ACCENT_RED, W)
    if signals:
        story.append(Paragraph("P&amp;L Positive Signals", S["label"]))
        _render_chip_row(story, [_readable(s) for s in signals], ACCENT_GREEN, W)


def _render_concall_section(story: list, data: dict, highlights: dict | None, S: dict, W: float) -> None:
    """Concall Intelligence System, Stage C5 — deterministic extraction/
    tracking data from Stages C0-C4, rendered as-is. No narrative LLM call
    here (no concall-specific Report Blueprint stage exists yet). Extended
    2026-09-15 (Premium PDF System, Stages B2/B3/B5) for the topic-sentiment
    grid, quarter-over-quarter change bullets and guidance consistency
    score `concall_report_data.py` already computes but this renderer
    didn't consume yet, plus the arthneeti/generated highlights block."""
    transcript = data.get("latest_transcript")
    if not transcript:
        return

    story.append(PageBreak())
    story.append(Paragraph("Management Commentary", S["section"]))
    call_label = transcript.get("quarter") or transcript.get("call_date") or transcript.get("filing_date") or ""
    story.append(Paragraph(f"Latest earnings call: {call_label}, NSE filing.", S["caption"]))
    participants = transcript.get("management_participants") or []
    if participants:
        names = ", ".join(p.get("name", "") for p in participants[:4])
        story.append(Paragraph(f"Management: {names}", S["caption"]))
    story.append(Spacer(1, 0.2 * cm))

    if highlights and highlights.get("sections"):
        source_note = (
            f'Results &amp; Concall Highlights (source: arthneeti.com)' if highlights["source"] == "ARTHNEETI"
            else "Results &amp; Concall Highlights (generated from this report's own extracted data)"
        )
        story.append(Paragraph(source_note, S["label"]))
        for section in highlights["sections"]:
            story.append(Paragraph(f'<b>{section["heading"]}</b>', S["body_light"]))
            for b in section["bullets"][:6]:
                story.append(Paragraph(f"• {b}", S["bullet_light"]))
            story.append(Spacer(1, 0.1 * cm))
        story.append(Spacer(1, 0.2 * cm))

    topic_sentiment = data.get("topic_sentiment") or []
    if topic_sentiment:
        story.append(Paragraph("Management Tone by Topic", S["label"]))
        ts_header = ParagraphStyle("ts_h", fontName="Helvetica-Bold", fontSize=7.5, textColor=TEXT_PRIMARY)
        ts_cell = ParagraphStyle("ts_c", fontName="Helvetica", fontSize=8, textColor=TEXT_PRIMARY)
        _SENT_COLOR = {"POSITIVE": ACCENT_GREEN, "NEGATIVE": ACCENT_RED, "NEUTRAL": TEXT_SECONDARY, "MIXED": ACCENT_YELLOW}

        def _cell(t):
            color = _SENT_COLOR.get(t["sentiment"], TEXT_SECONDARY)
            return [Paragraph(t["topic"], ts_cell),
                    Paragraph(f'<font color="#{color.hexval()[2:]}">{t["arrow"]} {t["sentiment"].title()}</font>', ts_cell)]

        # 2 topics per row (4 cells) to use page width efficiently.
        grid_data = [[Paragraph("Topic", ts_header), Paragraph("Tone", ts_header),
                      Paragraph("Topic", ts_header), Paragraph("Tone", ts_header)]]
        for i in range(0, len(topic_sentiment), 2):
            row = _cell(topic_sentiment[i])
            row += _cell(topic_sentiment[i + 1]) if i + 1 < len(topic_sentiment) else [Paragraph("", ts_cell), Paragraph("", ts_cell)]
            grid_data.append(row)
        t_grid = Table(grid_data, colWidths=[W * 0.2, W * 0.3, W * 0.2, W * 0.3])
        t_grid.setStyle(_table_style())
        story.append(t_grid)
        story.append(Spacer(1, 0.25 * cm))

    what_changed = data.get("what_changed") or []
    if what_changed:
        story.append(Paragraph("What Changed Since Last Call", S["label"]))
        for c in what_changed:
            story.append(Paragraph(f"• {c}", S["bullet_light"]))
        story.append(Spacer(1, 0.2 * cm))

    guidance_consistency = data.get("guidance_consistency")
    if guidance_consistency:
        story.append(Paragraph(
            f'Guidance Consistency: <b>{guidance_consistency["score"]:.0f}/100</b> '
            f'({guidance_consistency["metrics_tracked"]} metrics tracked, '
            f'{guidance_consistency["total_updates"]} quarter-over-quarter updates on record — '
            f"reiterated/upgraded vs. downgraded, not a hit-rate accuracy score).",
            S["caption"]
        ))
        story.append(Spacer(1, 0.15 * cm))

    guidance = data.get("guidance") or []
    if guidance:
        header_style = ParagraphStyle("cc_h", fontName="Helvetica-Bold", fontSize=7.5, textColor=TEXT_PRIMARY)
        cell_style = ParagraphStyle("cc_c", fontName="Helvetica", fontSize=7.5, textColor=TEXT_PRIMARY)
        rows = [[Paragraph(h, header_style) for h in ("Metric", "Period", "Target", "Tone", "Status")]]
        for g in guidance:
            if g["guidance_type"] == "quantitative":
                if g["target_low"] is not None and g["target_high"] is not None:
                    target = f"{g['target_low']:g}-{g['target_high']:g} {g['unit'] or ''}"
                elif g["target_value"] is not None:
                    target = f"{g['target_value']:g} {g['unit'] or ''}"
                else:
                    target = "—"
            else:
                target = "qualitative"
            rows.append([
                Paragraph(g["metric"].replace("_", " ").title(), cell_style),
                Paragraph(g["period"] or "—", cell_style),
                Paragraph(target, cell_style),
                Paragraph(g["tone"] or "—", cell_style),
                Paragraph(g["status"], cell_style),
            ])
        t = Table(rows, colWidths=[W * 0.22, W * 0.16, W * 0.28, W * 0.18, W * 0.16])
        t.setStyle(_table_style())
        story.append(t)
        story.append(Spacer(1, 0.3 * cm))

    credibility = data.get("credibility") or []
    if credibility:
        story.append(Paragraph("Guidance Consistency (across quarters on record)", S["label"]))
        for c in credibility:
            story.append(Paragraph(
                f"• {c['metric'].replace('_', ' ').title()}: {c['guidance_count']} updates — "
                f"{c['upgraded_count']} upgraded, {c['downgraded_count']} downgraded, "
                f"{c['reiterated_count']} reiterated (latest: {c['last_status']})",
                S["bullet_light"]
            ))
        story.append(Spacer(1, 0.2 * cm))

    promises = data.get("promises") or []
    if promises:
        story.append(Paragraph("Open Management Commitments (unverified — see disclaimer)", S["label"]))
        for p in promises:
            story.append(Paragraph(f"• {p['promise'][:220]}", S["bullet_light"]))
        story.append(Spacer(1, 0.2 * cm))


def _render_change_log(story: list, change_log: dict | None, S: dict) -> None:
    """Premium PDF System, Stage B7 — silently absent on a company's
    first-ever analysis or when nothing material changed, per the module's
    own docstring; never fabricates a change that isn't a real delta
    between two stored FundamentalAnalysis rows."""
    if not change_log or not change_log.get("has_material_change"):
        return
    story.append(Paragraph("What Changed Since Last Analysis", S["section"]))
    for c in change_log.get("changes", []):
        story.append(Paragraph(f"• {c}", S["bullet_light"]))
    for r in change_log.get("new_risks", []):
        story.append(Paragraph(f'<font color="#{ACCENT_RED.hexval()[2:]}">• New risk:</font> {r}', S["bullet_light"]))
    for r in change_log.get("resolved_risks", []):
        story.append(Paragraph(f'<font color="#{ACCENT_GREEN.hexval()[2:]}">• Resolved risk:</font> {r}', S["bullet_light"]))
    story.append(Spacer(1, 0.3 * cm))


_SEGMENT_COLORS = [ACCENT, ACCENT_GREEN, ACCENT_YELLOW, ACCENT_RED, ACCENT_GOLD_BRIGHT, TEXT_DIM]


def _render_business_mix(story: list, db, company_id: str, S: dict, W: float) -> None:
    """Design doc item #12: replace a business-segments paragraph with a
    single-glance composition visual. `BusinessSegment` is already ingested
    (TradingView, used in the frontend's SummarySection) but was never
    queried in this renderer before 2026-09-15."""
    from app.infrastructure.database.models import BusinessSegment
    rows = db.query(BusinessSegment).filter_by(company_id=company_id).all()
    if not rows:
        return
    latest_year = max(r.fiscal_year for r in rows)
    latest = [r for r in rows if r.fiscal_year == latest_year]
    total = sum(float(r.revenue) for r in latest)
    if total <= 0:
        return
    latest.sort(key=lambda r: r.revenue, reverse=True)

    # fiscal_year is sometimes a bare calendar year ("2025") and sometimes a
    # full period-end date ("2026-03-31") depending on source — normalize
    # to "FY25"/"FY26" either way rather than printing "FY2026-03-31".
    year_match = re.search(r"(\d{4})", latest_year)
    year_label = f"FY{year_match.group(1)[2:]}" if year_match else latest_year
    story.append(Paragraph(f"Business Mix ({year_label})", S["label"]))
    bar_data = [[""] * len(latest)]
    bar_widths = []
    for r in latest:
        pct = float(r.revenue) / total
        bar_widths.append(max(W * pct, 2))
    t = Table(bar_data, colWidths=bar_widths, rowHeights=[14])
    style_cmds = [("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 0),
                  ("BOTTOMPADDING", (0, 0), (-1, -1), 0), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                  ("RIGHTPADDING", (0, 0), (-1, -1), 0)]
    for i in range(len(latest)):
        style_cmds.append(("BACKGROUND", (i, 0), (i, 0), _SEGMENT_COLORS[i % len(_SEGMENT_COLORS)]))
    t.setStyle(TableStyle(style_cmds))
    story.append(t)
    story.append(Spacer(1, 0.15 * cm))

    legend_style = ParagraphStyle("seg_legend", fontName="Helvetica", fontSize=8, textColor=TEXT_SECONDARY)
    for i, r in enumerate(latest[:6]):
        pct = float(r.revenue) / total * 100
        color = _SEGMENT_COLORS[i % len(_SEGMENT_COLORS)]
        story.append(Paragraph(
            f'<font color="#{color.hexval()[2:]}">●</font> {r.segment_name} — {pct:.0f}%',
            legend_style
        ))
    story.append(Spacer(1, 0.3 * cm))


def _render_company_overview(story: list, db, company_id: str, summary_row_cls, extras: dict, S: dict, W: float) -> None:
    """Design doc's explicit complaint: "Company Overview on page 1 looks
    too much and non-readable" — was a raw About + full key_points wiki-text
    dump. Restructured: trimmed About, a Business Mix visual, the existing
    Brand Portfolio table, then the full key_points text still available
    but de-emphasized (smaller/muted), not the lead content."""
    summary_row = db.query(summary_row_cls).filter_by(company_id=company_id).first()
    if not (summary_row and (summary_row.about or summary_row.key_points)):
        _render_business_mix(story, db, company_id, S, W)
        _render_brands_section(story, extras.get("brands") or [], S, W)
        return

    story.append(Paragraph("Company Overview", S["section"]))
    if summary_row.about:
        # First 2-3 sentences only — the full About paragraph is often a
        # dense multi-sentence company history; a scannable lead beats a wall
        # of text on the page readers see first. Real bug found 2026-09-15
        # testing Jyothy Labs: a naive ". "-split truncated "Mr. M. P.
        # Ramachandran" after "Mr." and again after "P." — sentence
        # boundaries need at least a 3-letter word before the period (so
        # "Mr."/initials never count) and a capital letter after it.
        sentences = re.split(r"(?<=[a-zA-Z]{3}\.)\s+(?=[A-Z])", summary_row.about.replace("\n", " "))
        trimmed = " ".join(sentences[:3]).strip()
        if trimmed and not trimmed.endswith("."):
            trimmed += "."
        story.append(Paragraph(trimmed, S["body_light"]))
        story.append(Spacer(1, 0.2 * cm))

    _render_business_mix(story, db, company_id, S, W)
    _render_brands_section(story, extras.get("brands") or [], S, W)

    if summary_row.key_points:
        muted_style = ParagraphStyle("overview_detail", parent=S["body"], fontSize=8, textColor=TEXT_DIM)
        story.append(Paragraph("Full Business Detail", S["label"]))
        story.append(Paragraph(summary_row.key_points, muted_style))
        story.append(Spacer(1, 0.3 * cm))


def _render_brands_section(story: list, brands: list, S: dict, W: float) -> None:
    """Premium PDF System, Stage B1 — structured brand facts extracted
    from Screener.in's Key Points text, validated against the source
    (see `brand_extraction.py`)."""
    if not brands:
        return
    story.append(Paragraph("Brand Portfolio", S["section"]))
    header = ParagraphStyle("br_h", fontName="Helvetica-Bold", fontSize=7.5, textColor=TEXT_PRIMARY)
    cell = ParagraphStyle("br_c", fontName="Helvetica", fontSize=8, textColor=TEXT_PRIMARY)
    rows = [[Paragraph(h, header) for h in ("Brand", "Category", "Ownership", "Market Share")]]
    for b in brands[:15]:
        share = f'{b["market_share_pct"]:g}%' if b["market_share_pct"] is not None else "—"
        if b.get("market_share_context"):
            share += f' ({b["market_share_context"]})'
        rows.append([
            Paragraph(b["brand_name"], cell), Paragraph(b.get("category") or "—", cell),
            Paragraph((b.get("ownership") or "—").title(), cell), Paragraph(share, cell),
        ])
    t = Table(rows, colWidths=[W * 0.22, W * 0.22, W * 0.16, W * 0.4])
    t.setStyle(_table_style())
    story.append(t)
    story.append(Spacer(1, 0.4 * cm))


def _downsample_points(points: list[dict], n: int = 20) -> list[dict]:
    if len(points) <= n:
        return points
    step = len(points) / n
    return [points[int(i * step)] for i in range(n)]


def _render_price_chart(story: list, price_chart: dict, S: dict, W: float,
                         only: str | None = None, title: str | None = "Price History") -> None:
    """1Y (daily) / 5Y (weekly) price chart — yfinance (2026-09-15, chosen
    over TradingView Desktop/Dhan, see price_chart.py's module docstring).
    `only="1y"` renders a single, full-width, dominant chart (design doc
    item #4/#5: "the 1-year chart should be LARGE... never shrink a chart
    merely to make text fit") — used on the cover page. With no `only`,
    both windows render side by side at half width, downsampled to ~20
    points each — used later in the report where they're secondary."""
    windows = [("1y", "1-Year", price_chart.get("1y") or []), ("5y", "5-Year", price_chart.get("5y") or [])]
    if only:
        windows = [w for w in windows if w[0] == only]
    windows = [(k, label, pts) for k, label, pts in windows if len(pts) >= 2]
    if not windows:
        return

    full_width = len(windows) == 1
    # Real bug found 2026-09-15: with the heading appended straight to
    # `story`, a chart too tall to fit the page's remaining space moved to
    # the next page while its own heading stayed behind — an orphaned
    # section title over a blank page bottom (exactly the failure mode the
    # design doc's item #2 calls out by name). Built as one local block and
    # wrapped in KeepTogether so the heading and its chart move as a unit.
    block: list = []
    if title:
        block.append(Paragraph(title, S["section"]))
    col_w = W if full_width else W / len(windows) - 0.3 * cm
    chart_h, drawing_h = (280, 320) if full_width else (118, 170)
    drawings = []
    for _, label, points in windows:
        pts = _downsample_points(points, n=30 if full_width else 20)
        drawing = Drawing(col_w, drawing_h)
        chart = HorizontalLineChart()
        chart.x, chart.y = 40, 30
        chart.width, chart.height = col_w - 50, chart_h
        values = [p["close"] for p in pts]
        chart.data = [values]
        chart.valueAxis.valueMin = min(values) * 0.95
        chart.valueAxis.valueMax = max(values) * 1.05
        chart.valueAxis.labelTextFormat = "Rs. %0.0f"
        chart.categoryAxis.categoryNames = [""] * len(pts)
        chart.lines[0].strokeColor = ACCENT
        chart.lines[0].strokeWidth = 2 if full_width else 1.75
        drawing.add(chart)
        if not full_width:
            drawing.add(String(34, drawing_h - 12, label, fontSize=9, fontName="Helvetica-Bold", fillColor=TEXT_SECONDARY))
        drawings.append(drawing)

    # Side by side, not stacked — Platypus flows one flowable per line
    # unless placed as table cells.
    if len(drawings) == 1:
        block.append(drawings[0])
    else:
        t = Table([drawings], colWidths=[col_w + 0.3 * cm] * len(drawings))
        t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        block.append(t)
    block.append(Spacer(1, 0.3 * cm))
    story.append(KeepTogether(block))


def _render_peer_performance_chart(story: list, peer_performance: dict, S: dict, W: float) -> None:
    """Premium PDF System, Stage B4 — 1Y rebased (=100 at period start)
    price performance vs. peers. ReportLab's native chart (not SVG — the
    ReportLab path has no SVG renderer, unlike the Jinja/HTML banking path
    which uses `charts.py`). `peer_performance["series"][*]["points"]`
    already arrives downsampled to ~14 points per series —
    `premium_report_data.py::_downsample` does it once for both renderers,
    since a daily series (~250 points) is illegible at report width."""
    series = peer_performance.get("series") or []
    if len(series) < 2:  # need the subject + at least one peer for this to mean anything
        return

    story.append(Paragraph("Relative Price Performance vs. Peers (1Y, rebased to 100)", S["section"]))

    _COLORS = [ACCENT, ACCENT_GREEN, ACCENT_YELLOW, ACCENT_RED, TEXT_DIM]
    # ReportLab's chart.data requires every row the same length — series can
    # differ slightly (a recently-listed peer has fewer daily points), so
    # truncate to the shortest rather than crash on a jagged grid.
    n_points = min(len(s["points"]) for s in series)
    drawing = Drawing(W, 220)
    chart = HorizontalLineChart()
    chart.x, chart.y = 40, 30
    chart.width, chart.height = W - 90, 165
    chart.data = [[p["value"] for p in s["points"][:n_points]] for s in series]
    all_vals = [v for row in chart.data for v in row]
    chart.valueAxis.valueMin = min(all_vals) - 5
    chart.valueAxis.valueMax = max(all_vals) + 5
    chart.categoryAxis.categoryNames = [""] * n_points
    chart.categoryAxis.labels.fontSize = 6
    for i, s in enumerate(series):
        chart.lines[i].strokeColor = _COLORS[i % len(_COLORS)]
        chart.lines[i].strokeWidth = 2 if s.get("is_subject") else 1.25
    drawing.add(chart)
    legend = Legend()
    legend.x, legend.y = 40, 212
    legend.alignment = "left"
    legend.fontSize = 7
    legend.dx, legend.dy = 7, 7
    legend.dxTextSpace = 4
    legend.deltay = 3
    legend.columnMaximum = len(series)  # single column — the default auto-wrap
    # (2-3 rows per column) overlapped swatches under the next column's text
    # for long company names, found rendering real peer data (2026-09-15).
    legend.colorNamePairs = [(_COLORS[i % len(_COLORS)], s["name"][:28]) for i, s in enumerate(series)]
    drawing.add(legend)
    story.append(drawing)
    story.append(Spacer(1, 0.4 * cm))


def _render_source_ledger(story: list, ledger: list, S: dict, W: float) -> None:
    """Premium PDF System, Stage B6 — every source already tracked
    per-row across the app's ingestion modules, aggregated for one
    "where did this report's numbers come from" page (matches
    `pdf generation.md` Page 14)."""
    if not ledger:
        return
    story.append(PageBreak())
    story.append(Paragraph("Sources &amp; Evidence", S["section"]))
    story.append(Paragraph(
        "Every data source used in this report, grouped by reliability tier "
        "(1 = regulatory/exchange filing, 2 = high-quality secondary aggregator, 3 = context/industry).",
        S["caption"]
    ))
    story.append(Spacer(1, 0.2 * cm))
    header = ParagraphStyle("sl_h", fontName="Helvetica-Bold", fontSize=7.5, textColor=TEXT_PRIMARY)
    cell = ParagraphStyle("sl_c", fontName="Helvetica", fontSize=7.5, textColor=TEXT_PRIMARY)
    # Tier as a colored badge, not a plain gray digit — same tag/chip visual
    # language already used for severity (Risk Radar) and sentiment
    # (Concall Management Tone) elsewhere in this report.
    _tier_color = {1: ACCENT_GREEN, 2: ACCENT, 3: TEXT_DIM}
    rows = [[Paragraph(h, header) for h in ("Source", "Used For", "Tier", "Date Range", "Facts")]]
    for e in ledger:
        date_range = (
            f'{e["date_from"][:10]} – {e["date_to"][:10]}' if e.get("date_from") and e.get("date_to")
            else (e.get("date_from") or "")[:10] or "—"
        )
        tier_color = _tier_color.get(e["tier"], TEXT_DIM)
        rows.append([
            Paragraph(e["source"], cell), Paragraph(e["used_for"], cell),
            Paragraph(f'<font color="#{tier_color.hexval()[2:]}"><b>Tier {e["tier"]}</b></font>', cell),
            Paragraph(date_range, cell), Paragraph(str(e["fact_count"]), cell),
        ])
    t = Table(rows, colWidths=[W * 0.2, W * 0.36, W * 0.1, W * 0.24, W * 0.1])
    t.setStyle(_table_style())
    story.append(t)
    story.append(Spacer(1, 0.3 * cm))


def generate_pdf_report(analysis_id: str, db) -> str:
    """Generate a PDF report and return its file path."""
    from app.infrastructure.database.models import FundamentalAnalysis
    analysis: FundamentalAnalysis = db.query(FundamentalAnalysis).filter_by(id=analysis_id).first()
    if analysis is None:
        raise ValueError(f"Analysis {analysis_id} not found")

    reports_dir = Path(config.reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = reports_dir / f"{analysis_id}.pdf"

    company = analysis.company_info or {}
    metrics = analysis.metrics or {}
    scores = analysis.scores or {}
    ai = analysis.ai_analysis or {}
    risks = analysis.risks or []
    catalysts = analysis.catalysts or []
    sector_data = analysis.sector_analysis or {}

    company_name = company.get("company_name", "Unknown Company")
    sector = company.get("sector", "")
    symbol = company.get("symbol", "")
    exchange = company.get("exchange", "")
    analysis_date = datetime.now(timezone.utc).strftime("%B %d, %Y")

    # Fetched fresh at generation time, not reused from the analysis run's
    # company_info snapshot — a PDF regenerated later would otherwise show a
    # stale price. See app/ingestion/live_price.py's module docstring.
    from app.ingestion.live_price import fetch_live_price
    live_price = fetch_live_price(symbol, exchange) if symbol else None
    if live_price is None:
        live_price = company.get("current_price")

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
    )

    S = _styles()
    story = []
    W = A4[0] - 3.6 * cm  # usable width

    # Moved up from just before the (former) Company Overview section — the
    # redesigned cover page (design-doc-driven, 2026-09-15) needs extras
    # (brands/change_log) and company_id before the cover is built, not after.
    company_id = company.get("stock_id") or analysis.stock_id
    from app.reporting.premium_report_data import build_premium_extras
    extras = build_premium_extras(db, company_id, analysis) if company_id else {}

    # ── Cover page ────────────────────────────────────────────────────────────
    story.append(Spacer(1, 1.5 * cm))
    story.append(Paragraph("FUNDAMENTAL EQUITY RESEARCH", S["label"]))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(company_name, S["title"]))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(f"{sector}  ·  {exchange}: {symbol}", S["subtitle"]))
    story.append(Spacer(1, 0.2 * cm))
    if live_price and live_price.get("price") is not None:
        chg = live_price.get("change_pct")
        chg_str = f"  ({chg:+.2f}%)" if chg is not None else ""
        chg_color = ACCENT_GREEN if (chg or 0) >= 0 else ACCENT_RED
        story.append(Paragraph(
            f'Rs. {live_price["price"]:,.2f}<font color="#{chg_color.hexval()[2:]}">{chg_str}</font>',
            ParagraphStyle("price", fontName="Helvetica-Bold", fontSize=16,
                           textColor=DARK_NAVY, alignment=TA_CENTER, spaceAfter=8, leading=20),
        ))
        range_bits = []
        if live_price.get("day_low") is not None and live_price.get("day_high") is not None:
            range_bits.append(f"Day range Rs. {live_price['day_low']:,.2f}-Rs. {live_price['day_high']:,.2f}")
        if live_price.get("previous_close") is not None:
            range_bits.append(f"Prev close Rs. {live_price['previous_close']:,.2f}")
        # yfinance_client.py's market.week52_high/low — real data, fetched
        # for every analysis already, never rendered in this report until
        # now. Pulled from the stored analysis run, not re-fetched live
        # (unlike current price/day range above): a 52-week range doesn't
        # meaningfully go stale between generation and viewing.
        market_snapshot = (analysis.financial_data or {}).get("market") or {}
        week52_low = market_snapshot.get("week52_low")
        week52_high = market_snapshot.get("week52_high")
        if week52_low is not None and week52_high is not None:
            range_bits.append(f"52-week range Rs. {week52_low:,.2f}-Rs. {week52_high:,.2f}")
        if range_bits:
            story.append(Paragraph("  ·  ".join(range_bits), S["caption"]))
        story.append(Paragraph(
            f"As of {live_price['as_of'][:16].replace('T', ' ')} UTC · Source: Yahoo Finance",
            S["caption"]
        ))

        # Live Snapshot KPI cards — same 4 fields as the app's own header
        # KPI row (AnalysisDashboard.tsx), so the PDF and UI show the
        # identical snapshot.
        market_cap = company.get("market_cap") or metrics.get("market_cap")
        pe_ratio = metrics.get("pe_ratio")
        story.append(Spacer(1, 0.3 * cm))
        _kpi_card_row(story, [
            {"label": "Price", "value": f"Rs. {live_price['price']:,.2f}"},
            {"label": "Market Cap", "value": f"Rs. {market_cap / 1e7:,.0f} Cr" if market_cap else "N/A"},
            {"label": "P/E (TTM)", "value": _fmt(pe_ratio, "x") if pe_ratio is not None else "N/A"},
            {"label": "52-Week Range", "value": f"{week52_low:,.0f}-{week52_high:,.0f}"
                if week52_low is not None and week52_high is not None else "N/A"},
        ], W)
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(f"Analysis Date: {analysis_date}", S["caption"]))
    story.append(Spacer(1, 0.3 * cm))

    # Investment View — moved onto the cover (design doc item #4/#8): the
    # reader should see the verdict before anything else, not after 7+ pages.
    _render_investment_snapshot(story, analysis, ai, scores, S, W)

    from app.interpretation.price_chart import build_price_charts
    price_charts = build_price_charts(symbol, exchange)
    _render_price_chart(story, price_charts, S, W, only="1y", title="1-Year Price Performance")

    _render_key_takeaways(story, risks, catalysts, S)

    story.append(HRFlowable(width=W, color=ACCENT, thickness=1, spaceAfter=16))

    # ── Company overview (Screener.in's about/key_points, 2026-09-12) ──────────
    # Sector-agnostic — every Screener.in company page has this, not just
    # banks (whose separate HTML/PDF renderer, app/reporting/, gets the same
    # treatment). key_points sometimes carries a real revenue-mix breakdown
    # (confirmed on TCS: "BFSI: 31.9%, Consumer Business: 15.4%...").
    from app.infrastructure.database.models import CompanySummary

    _render_change_log(story, extras.get("change_log"), S)

    _render_company_overview(story, db, company_id, summary_row_cls=CompanySummary, extras=extras, S=S, W=W)

    # ── Business & Interpretation (Report Blueprint, Stage L3 of the Llama
    # Report Interpretation Architecture — local-Llama-generated, validated
    # narrative, additive alongside the existing AI Analysis section below;
    # see app/interpretation/. Empty/missing blueprint renders nothing —
    # this pipeline stage is best-effort and never blocks the report. The
    # 6 pnl_-prefixed sections are rendered in their own dedicated P&L
    # section below instead, not here — see _render_blueprint_sections.) ───
    blueprint = analysis.report_blueprint or {}
    all_sections = blueprint.get("sections") or []
    narrative_sections = [s for s in all_sections if not s.get("id", "").startswith("pnl_")]
    pnl_narrative_sections = [s for s in all_sections if s.get("id", "").startswith("pnl_")]

    if narrative_sections:
        story.append(Paragraph("Business & Interpretation", S["section"]))
        story.append(Paragraph(
            "Generated by a local Llama model, interpreting only the deterministic data above — "
            "see the disclaimer at the end of this report.",
            S["caption"]
        ))
        story.append(Spacer(1, 0.15 * cm))
        _render_blueprint_sections(story, narrative_sections, S)

    # ── Profit & Loss Analysis (P&L Analysis System, Stage P3) — 10Y+TTM
    # table, CAGR/margin cards and deterministic flags from
    # app/calculations/pnl_engine.py, computed fresh here (not persisted
    # separately — same "fetch fresh at render time" pattern as live_price
    # above), plus the 6 pnl_ narrative sections from the same blueprint
    # used above. ────────────────────────────────────────────────────────────
    from app.calculations.pnl_engine import compute_pnl_analysis
    # Real bug found 2026-09-13: `sector` here is company_info's macro
    # sector ("Financial Services"), not the framework's actual sector name
    # ("NBFCs" etc.) that pnl_engine's _FINANCIAL_SECTORS gate checks
    # against — using it silently disabled the bank/NBFC-specific interest/
    # other-income flag gating for every financial-sector company that
    # renders through this ReportLab path (Banks itself uses the separate
    # Jinja path, which had the identical bug, fixed in data_builder.py).
    pnl = compute_pnl_analysis(
        db, company_id, sector_name=sector_data.get("sector_name")
    ) if company_id else {}
    if pnl.get("years_of_data"):
        story.append(PageBreak())
        story.append(Paragraph("Profit & Loss Analysis", S["section"]))
        story.append(Paragraph(
            f"{pnl['years_of_data']}-year consolidated P&amp;L history, Screener.in.",
            S["caption"]
        ))
        story.append(Spacer(1, 0.2 * cm))
        _render_pnl_dashboard_header(story, pnl, S, W)
        _render_pnl_cagr_cards(story, pnl, S, W)
        _render_pnl_flags(story, pnl, S, W)
        _render_pnl_table(story, pnl, S, W)
        if pnl_narrative_sections:
            story.append(Spacer(1, 0.2 * cm))
            _render_blueprint_sections(story, pnl_narrative_sections, S)

    # ── Management Commentary (Concall Intelligence System, Stage C5) ──────────
    from app.interpretation.concall_report_data import build_concall_report_data
    concall_data = build_concall_report_data(db, company_id) if company_id else {}
    _render_concall_section(story, concall_data, extras.get("concall_highlights"), S, W)

    # ── Key financial metrics ─────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("Key Financial Metrics", S["section"]))
    story.append(Paragraph(
        "Trend badges compare the metric's most recent period-over-period move against its own history "
        "(see app/calculations/engine.py::trend_direction) — shown only where enough historical data exists.",
        S["caption"]
    ))
    story.append(Spacer(1, 0.2 * cm))
    # (label, metric_key, unit, trend_key|None) — trend_key is None for
    # metrics the calc engine doesn't compute a trend series for.
    _kpi_specs = [
        ("Revenue CAGR (3Y)", "revenue_cagr_3y", "%", None),
        ("PAT CAGR (3Y)", "pat_cagr_3y", "%", None),
        ("EPS CAGR (3Y)", "eps_cagr_3y", "%", None),
        ("Gross Margin", "gross_margin", "%", None),
        ("EBITDA Margin", "ebitda_margin", "%", "ebitda_margin_trend"),
        ("PAT Margin", "pat_margin", "%", "pat_margin_trend"),
        ("ROCE", "roce", "%", "roce_trend"),
        ("ROE", "roe", "%", "roe_trend"),
        ("ROIC", "roic", "%", None),
        ("FCF/PAT", "fcf_to_pat", "%", "fcf_trend"),
        ("CFO/PAT", "cfo_to_pat", "%", None),
        ("Debt/Equity", "debt_to_equity", "x", "debt_trend"),
        ("Net Debt/EBITDA", "net_debt_to_ebitda", "x", None),
        ("Interest Coverage", "interest_coverage", "x", None),
        ("Current Ratio", "current_ratio", "x", None),
        ("P/E", "pe_ratio", "x", None),
        ("EV/EBITDA", "ev_to_ebitda", "x", None),
        ("P/B", "pb_ratio", "x", None),
        ("FCF Yield", "fcf_yield", "%", None),
        ("Dividend Yield", "dividend_yield", "%", None),
    ]
    kpi_cards = []
    for label, key, unit, trend_key in _kpi_specs:
        card = {"label": label, "value": _fmt(metrics.get(key), unit)}
        trend = metrics.get(trend_key) if trend_key else None
        if trend and trend in _TREND_LABEL:
            status_label, status_color = _TREND_LABEL[trend]
            card["status"], card["status_color"] = status_label, status_color
        kpi_cards.append(card)
    _kpi_card_row(story, kpi_cards, W, cols=4)
    story.append(Spacer(1, 0.2 * cm))

    # 5-year window of the same price_charts fetched for the cover's 1-year
    # chart — design doc item #4: "the 5-year chart can appear later in the
    # market/price section" (rather than sharing the cover with the 1-year
    # chart, which should be the sole dominant visual there).
    _render_price_chart(story, price_charts, S, W, only="5y", title="5-Year Price Performance")
    _render_peer_performance_chart(story, extras.get("peer_performance") or {}, S, W)

    # ── Ownership & Governance (Architecture v2 Stage 3, wired into the
    # pipeline 2026-09-13) — NSE shareholding/pledge is the sole
    # governance-critical source; Screener's supplementary trend has no
    # pledge field at all (see migration 0016) so it's shown separately,
    # never blended into the same row. ─────────────────────────────────────
    from app.infrastructure.database.models import (
        Shareholding, ShareholdingScreener, GovernanceEvent, AnalystConsensus,
        ForwardEstimate, CorporateAction, CompanyNews, EarningsCalendar,
    )
    sh_rows = (db.query(Shareholding).filter_by(company_id=company_id)
               .order_by(Shareholding.period_end.desc()).limit(4).all())
    gov_events = (db.query(GovernanceEvent).filter_by(company_id=company_id)
                  .order_by(GovernanceEvent.event_date.desc()).limit(6).all())
    # Queried once at a depth (20) that serves both the KPI row (index 0 =
    # latest) and the trend chart (reversed to chronological order) — Item
    # 13's "large dominant trend chart" needs more history than the old
    # 4-row supplementary table did.
    sh_screener_rows = (db.query(ShareholdingScreener).filter_by(company_id=company_id, frequency="quarterly")
                        .order_by(ShareholdingScreener.period_end.desc()).limit(20).all())

    if sh_rows or gov_events or sh_screener_rows:
        block: list = [Paragraph("Ownership &amp; Governance", S["section"])]
        latest_screener = sh_screener_rows[0] if sh_screener_rows else None
        if latest_screener:
            block.append(Paragraph(
                f"As of {latest_screener.period_end} (Screener.in, quarterly).", S["caption"]
            ))
            block.append(Spacer(1, 0.1 * cm))
            _kpi_card_row(block, [
                {"label": "Promoter", "value": _fmt(latest_screener.promoter_pct, "%")},
                {"label": "FII", "value": _fmt(latest_screener.fii_pct, "%")},
                {"label": "DII", "value": _fmt(latest_screener.dii_pct, "%")},
                {"label": "Public", "value": _fmt(latest_screener.public_pct, "%")},
            ], W, cols=4)

        chart_rows = list(reversed(sh_screener_rows))
        # A field that's None for every quarter (e.g. ITC has no promoter
        # group at all — Screener reports that as a blank field, not 0)
        # must NOT be plotted as a flat 0% line: that would fabricate a
        # data point the source never actually reported. Only series with
        # a real value at every selected period are charted; others are
        # dropped from the chart (and its legend) entirely rather than
        # gap-filled or zero-filled.
        _own_series_specs = [("Promoter", ACCENT, [r.promoter_pct for r in chart_rows]),
                              ("FII", ACCENT_GREEN, [r.fii_pct for r in chart_rows]),
                              ("DII", ACCENT_YELLOW, [r.dii_pct for r in chart_rows])]
        _own_series = [(name, color, [float(v) for v in vals]) for name, color, vals in _own_series_specs
                       if all(v is not None for v in vals)]
        if len(chart_rows) >= 2 and _own_series:
            block.append(Paragraph("Ownership Trend (Screener.in, quarterly)", S["label"]))
            drawing = Drawing(W, 220)
            chart = HorizontalLineChart()
            chart.x, chart.y = 40, 30
            chart.width, chart.height = W - 90, 165
            chart.data = [vals for _, _, vals in _own_series]
            all_vals = [v for _, _, vals in _own_series for v in vals]
            chart.valueAxis.valueMin = max(0, min(all_vals) - 5)
            chart.valueAxis.valueMax = max(all_vals) + 5
            chart.valueAxis.labelTextFormat = "%0.0f%%"
            chart.categoryAxis.categoryNames = [""] * len(chart_rows)
            for i, (_, color, _) in enumerate(_own_series):
                chart.lines[i].strokeColor = color
                chart.lines[i].strokeWidth = 2
            drawing.add(chart)
            legend = Legend()
            legend.x, legend.y = 40, 212
            legend.alignment = "left"
            legend.fontSize = 7
            legend.dx, legend.dy = 7, 7
            legend.dxTextSpace = 4
            legend.deltay = 3
            legend.columnMaximum = len(_own_series)
            legend.colorNamePairs = [(color, name) for name, color, _ in _own_series]
            drawing.add(legend)
            block.append(drawing)
            block.append(Spacer(1, 0.2 * cm))
        # Heading + KPI row + chart move as a unit — same KeepTogether fix
        # already applied to _render_price_chart, so the heading can't
        # strand at a page bottom while the chart flows to the next page.
        story.append(KeepTogether(block))

        latest_nse = sh_rows[0] if sh_rows else None
        if latest_nse is not None:
            pledge_val = float(latest_nse.pledge_pct) if latest_nse.pledge_pct is not None else None
            if pledge_val and pledge_val > 0:
                p_color = ACCENT_RED if pledge_val > 10 else ACCENT_YELLOW
                p_text = f"PLEDGE STATUS: {pledge_val:.1f}% of promoter holding pledged (as of {latest_nse.period_end})"
            else:
                p_color = ACCENT_GREEN
                p_text = "PLEDGE STATUS: No Pledge Reported"
            _render_chip_row(story, [p_text], p_color, W, cols=1)

        if sh_rows:
            story.append(Paragraph(
                "Promoter shareholding &amp; pledge history — NSE quarterly XBRL filings, "
                "the only source with pledge data.",
                S["caption"]
            ))
            sh_table_rows = [[Paragraph("Period", S["label"]), Paragraph("Promoter %", S["label"]),
                               Paragraph("Public %", S["label"]), Paragraph("Pledge %", S["label"])]]
            for r in sh_rows:
                pledge_val = float(r.pledge_pct) if r.pledge_pct is not None else None
                pledge_color = ACCENT_RED if (pledge_val or 0) > 10 else (ACCENT_YELLOW if (pledge_val or 0) > 0 else TEXT_SECONDARY)
                sh_table_rows.append([
                    Paragraph(r.period_end, S["body"]),
                    Paragraph(_fmt(r.promoter_pct, "%"), S["body"]),
                    Paragraph(_fmt(r.public_pct, "%"), S["body"]),
                    Paragraph(f'<font color="#{pledge_color.hexval()[2:]}">{_fmt(r.pledge_pct, "%")}</font>', S["body"]),
                ])
            t = Table(sh_table_rows, colWidths=[W * 0.25] * 4)
            t.setStyle(_table_style())
            story.append(t)
            story.append(Spacer(1, 0.2 * cm))
        if gov_events:
            for ev in gov_events:
                sev = ev.severity or "LOW"
                color = ACCENT_RED if sev == "HIGH" else ACCENT_YELLOW if sev == "MEDIUM" else TEXT_DIM
                story.append(Paragraph(
                    f'<font color="#{color.hexval()[2:]}"><b>[{sev}] {ev.event_type}</b></font> — {ev.description}',
                    S["body_light"]
                ))
            story.append(Spacer(1, 0.2 * cm))

    # ── Market Intelligence: analyst consensus, forward estimates, earnings
    # calendar, corporate actions, news (2026-09-13, all Yahoo Finance) ────────
    ac_rows = db.query(AnalystConsensus).filter_by(company_id=company_id).all()
    fwd_rows = db.query(ForwardEstimate).filter_by(company_id=company_id).all()
    cal_row = db.query(EarningsCalendar).filter_by(company_id=company_id).first()
    ca_rows = (db.query(CorporateAction).filter_by(company_id=company_id)
               .order_by(CorporateAction.action_date.desc()).limit(6).all())
    news_rows = (db.query(CompanyNews).filter_by(company_id=company_id)
                 .order_by(CompanyNews.published_at.desc()).limit(6).all())

    if ac_rows or fwd_rows or cal_row or ca_rows or news_rows:
        story.append(PageBreak())
        heading_block: list = [Paragraph("Market Intelligence", S["section"])]

        if ac_rows:
            sent_cards = []
            for row in ac_rows:
                sentiment = (row.sentiment or "N/A").upper()
                upside = f' · +{_fmt(row.implied_upside_pct, "%")}' if row.implied_upside_pct is not None else ""
                # Short one-line sub, matching every other KPI card in this
                # file (e.g. "-0.28% today", "MICRO CAP") — the full
                # low-high range doesn't fit a card's sub slot without
                # wrapping into and visually crowding the big value above
                # it (found 2026-09-15 rendering real ITC analyst data).
                sent_cards.append({
                    "label": row.source,
                    "value": f'<font color="#{_rating_color(sentiment).hexval()[2:]}">{sentiment}</font>',
                    "sub": f'Rs. {_fmt(row.target_price_mean)} target{upside}',
                })
            heading_block.append(Paragraph("Analyst Consensus", S["label"]))
            _kpi_card_row(heading_block, sent_cards, W, cols=min(len(sent_cards), 4))
            heading_block.append(Paragraph(
                "Each card above is a distinct external analyst source, never averaged together.",
                S["caption"]
            ))
        # Heading + Analyst Consensus KPI row move as a unit, same
        # KeepTogether fix used everywhere else a heading precedes a chart
        # or card row in this file.
        story.append(KeepTogether(heading_block))
        story.append(Spacer(1, 0.1 * cm))

        if fwd_rows:
            story.append(Paragraph("Forward Estimates (Yahoo Finance consensus)", S["label"]))
            # ForwardEstimate.period_label is a relative code ("0q"/"+1q"/
            # "0y"/"+1y"), not a literal fiscal-year string — no FY numbers
            # exist in this data to label the chart with, so this maps to
            # readable relative labels instead of fabricating "FY27E" etc.
            _period_order = ["0q", "+1q", "0y", "+1y"]
            _period_labels = {"0q": "This Q", "+1q": "Next Q", "0y": "This FY", "+1y": "Next FY"}
            for metric_type, chart_title, fmt_fn, scale in (
                ("eps", "EPS (Rs.)", lambda v: _fmt(v, "", 2), 1),
                # ForwardEstimate revenue rows are raw absolute rupees (see
                # _fmt_cr's docstring) — the bar values themselves need the
                # same /1e7 scaling the table caption already gets via
                # _fmt_cr, or the chart renders "8000000000000.0" on its
                # y-axis instead of the doc-required Rs. Cr figure (found
                # 2026-09-15 rendering real ITC estimates).
                ("revenue", "Revenue (Rs. Cr)", _fmt_cr, 1e7),
            ):
                m_rows = [r for r in fwd_rows if r.metric_type == metric_type and r.avg is not None]
                if len(m_rows) < 2:
                    continue
                m_rows = sorted(
                    m_rows,
                    key=lambda r: _period_order.index(r.period_label) if r.period_label in _period_order else 99,
                )
                labels = [_period_labels.get(r.period_label, r.period_label) for r in m_rows]
                avgs = [float(r.avg) / scale for r in m_rows]
                drawing = Drawing(W, 175)
                drawing.add(String(0, 160, chart_title, fontSize=8, fontName="Helvetica-Bold", fillColor=TEXT_DIM))
                chart = VerticalBarChart()
                chart.x, chart.y = 45, 20
                chart.width, chart.height = W - 60, 125
                chart.data = [avgs]
                chart.categoryAxis.categoryNames = labels
                chart.categoryAxis.labels.fontSize = 8
                chart.valueAxis.labelTextFormat = "%0.1f"
                chart.bars[0].fillColor = ACCENT
                chart.barWidth = 22
                drawing.add(chart)
                story.append(drawing)
                range_cells = [
                    [Paragraph(l, S["label"]) for l in labels],
                    [Paragraph(f"{fmt_fn(r.low)}–{fmt_fn(r.high)}", S["body"]) for r in m_rows],
                ]
                t = Table(range_cells, colWidths=[W / len(m_rows)] * len(m_rows))
                t.setStyle(_table_style())
                story.append(t)
                story.append(Spacer(1, 0.2 * cm))

        if cal_row:
            story.append(Paragraph("Earnings Calendar", S["label"]))
            _kpi_card_row(story, [{
                "label": "Next Earnings",
                "value": cal_row.next_earnings_date or "N/A",
                "sub": f"Ex-div {cal_row.ex_dividend_date or 'N/A'} · EPS est. "
                       f"{_fmt(cal_row.expected_eps_avg, '', 2)} "
                       f"({_fmt(cal_row.expected_eps_low, '', 2)}–{_fmt(cal_row.expected_eps_high, '', 2)})",
            }], W, cols=1)

        if ca_rows:
            story.append(Paragraph("Recent Corporate Actions", S["label"]))
            ca_header_style = ParagraphStyle("ca_h", fontName="Helvetica-Bold", fontSize=8.5, textColor=DARK_NAVY)
            for row in ca_rows:
                unit = " per share" if row.action_type == "DIVIDEND" else ":1 split"
                cell = [
                    Paragraph(f"{row.action_date} &middot; {row.action_type}", ca_header_style),
                    Paragraph(f"{_fmt(row.value, '', 2)}{unit}", S["body_light"]),
                ]
                t = Table([[cell]], colWidths=[W])
                t.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.Color(ACCENT.red, ACCENT.green, ACCENT.blue, alpha=0.08)),
                    ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                    ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LINEBEFORE", (0, 0), (0, 0), 3, ACCENT),
                ]))
                story.append(t)
                story.append(Spacer(1, 0.08 * cm))
            story.append(Spacer(1, 0.15 * cm))

        if news_rows:
            story.append(Paragraph("Recent News", S["label"]))
            news_h_style = ParagraphStyle("news_h", fontName="Helvetica-Bold", fontSize=8.5,
                                           textColor=DARK_NAVY, leading=11)
            news_c_style = ParagraphStyle("news_c", fontName="Helvetica", fontSize=7,
                                           textColor=TEXT_DIM, spaceBefore=2)
            for row in news_rows:
                pub = row.published_at.strftime("%Y-%m-%d") if row.published_at else ""
                cell = [
                    Paragraph(_sanitize_for_pdf(row.headline), news_h_style),
                    Paragraph(f"{pub}  &middot;  {row.provider or 'Yahoo Finance'}", news_c_style),
                ]
                t = Table([[cell]], colWidths=[W])
                t.setStyle(TableStyle([
                    ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]))
                story.append(t)
                story.append(Spacer(1, 0.08 * cm))
            story.append(Spacer(1, 0.15 * cm))

    # ── Risks ─────────────────────────────────────────────────────────────────
    # Design doc item #15: "Risk Radar" — each risk as its own severity-
    # colored card (tinted background, not just a colored [HIGH] tag inline
    # in a paragraph), same chip/card visual language as the P&L flags and
    # KPI cards above.
    if risks:
        story.append(PageBreak())
        story.append(Paragraph("Risk Radar", S["section"]))
        sev_style = ParagraphStyle("risk_sev", fontName="Helvetica-Bold", fontSize=8)
        # TEXT_PRIMARY (near-white) was designed for a dark canvas — same
        # bug class already documented on the cover page (2026-09-13) and
        # re-found here 2026-09-15: these risk cards have a light tinted
        # background, not a dark one, so near-white title text was
        # rendering invisibly. Uses DARK_NAVY, same fix as the cover page.
        title_style = ParagraphStyle("risk_title", fontName="Helvetica-Bold", fontSize=10, textColor=DARK_NAVY)
        # Same light-tinted (near-white) card background as the title above —
        # the description text had the exact same TEXT_SECONDARY-on-light bug,
        # just missed in the earlier pass. Uses TEXT_BODY, the dark equivalent.
        desc_style = ParagraphStyle("risk_desc", fontName="Helvetica", fontSize=8.5, textColor=TEXT_BODY, spaceBefore=2)
        for risk in risks[:8]:
            sev = risk.get("severity", "LOW")
            color = ACCENT_RED if sev == "HIGH" else ACCENT_YELLOW if sev == "MEDIUM" else TEXT_DIM
            cell = [
                Paragraph(f'<font color="#{color.hexval()[2:]}">{sev}</font>', ParagraphStyle("rs", parent=sev_style, textColor=color)),
                Paragraph(_sanitize_for_pdf(risk.get("title", "")), title_style),
            ]
            if risk.get("description"):
                cell.append(Paragraph(_sanitize_for_pdf(risk["description"]), desc_style))
            t = Table([[cell]], colWidths=[W])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.Color(color.red, color.green, color.blue, alpha=0.08)),
                ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LINEBEFORE", (0, 0), (0, 0), 3, color),
            ]))
            story.append(t)
            story.append(Spacer(1, 0.15 * cm))

    # ── Catalysts ─────────────────────────────────────────────────────────────
    if catalysts:
        story.append(Paragraph("Positive Catalysts", S["section"]))
        _render_chip_row(story, [
            f'{_sanitize_for_pdf(cat.get("title", ""))}: {_sanitize_for_pdf(cat.get("description", ""))}'
            for cat in catalysts[:6]
        ], ACCENT_GREEN, W, cols=1)

    # ── AI Analysis ───────────────────────────────────────────────────────────
    # Design doc item #16: rating/conviction/valuation as a hero KPI row
    # (not an inline sentence), the thesis as a highlighted callout, and
    # bull/bear case as two side-by-side cards instead of two sequential
    # bullet lists reading identically.
    if ai:
        story.append(PageBreak())
        story.append(Paragraph("AI Fundamental View", S["section"]))
        ai_rating_v = ai.get("rating") or "—"
        conviction_v = ai.get("conviction") or "—"
        valuation_v = ai.get("valuation_view") or "—"

        def _colored_value(v: str) -> str:
            return f'<font color="#{_rating_color(v).hexval()[2:]}">{v}</font>'

        _kpi_card_row(story, [
            {"label": "AI Rating", "value": _colored_value(ai_rating_v)},
            {"label": "Conviction", "value": conviction_v},
            {"label": "Valuation", "value": _colored_value(valuation_v)},
        ], W, cols=3)
        story.append(Spacer(1, 0.2 * cm))

        thesis = ai.get("executive_summary") or (ai.get("investment_thesis") or [None])[0]
        if thesis:
            quote_style = ParagraphStyle("thesis", fontName="Helvetica-Oblique", fontSize=10.5,
                                          textColor=TEXT_PRIMARY, leading=15)
            t = Table([[Paragraph(f'&ldquo;{_sanitize_for_pdf(thesis)}&rdquo;', quote_style)]], colWidths=[W])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), BG_CARD),
                ("LEFTPADDING", (0, 0), (-1, -1), 16), ("RIGHTPADDING", (0, 0), (-1, -1), 16),
                ("TOPPADDING", (0, 0), (-1, -1), 14), ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
                ("LINEBEFORE", (0, 0), (0, 0), 3, ACCENT),
            ]))
            story.append(t)
            story.append(Spacer(1, 0.3 * cm))

        # Narrative paragraphs (skip executive_summary — already the thesis quote above)
        for txt_key, txt_label in [
            ("business_quality_assessment", "Business Quality"),
            ("financial_health_summary", "Financial Health"),
            ("growth_outlook", "Growth Outlook"),
            ("valuation_commentary", "Valuation Commentary"),
        ]:
            val = ai.get(txt_key)
            if val:
                story.append(Paragraph(txt_label, S["label"]))
                story.append(Paragraph(_sanitize_for_pdf(val), S["body_light"]))
                story.append(Spacer(1, 0.15 * cm))

        # Bull case / Bear case — side by side, not two sequential lists
        bull, bear = ai.get("bull_case") or [], ai.get("bear_case") or []
        if bull or bear:
            bull_style = ParagraphStyle("bull_h", fontName="Helvetica-Bold", fontSize=9, textColor=ACCENT_GREEN)
            bear_style = ParagraphStyle("bear_h", fontName="Helvetica-Bold", fontSize=9, textColor=ACCENT_RED)
            # These cells sit on a near-white alpha-tinted (0.08) background,
            # not a navy one — same TEXT_SECONDARY-on-light contrast bug as
            # the risk-card description above. Uses TEXT_BODY.
            item_style = ParagraphStyle("case_item", fontName="Helvetica", fontSize=8.5, textColor=TEXT_BODY,
                                         leading=12, spaceAfter=3)
            bull_cell = [Paragraph("Bull Case", bull_style)] + \
                [Paragraph(f"+ {_sanitize_for_pdf(b)}", item_style) for b in bull]
            bear_cell = [Paragraph("Bear Case", bear_style)] + \
                [Paragraph(f"- {_sanitize_for_pdf(b)}", item_style) for b in bear]
            t = Table([[bull_cell, bear_cell]], colWidths=[W / 2 - 0.15 * cm, W / 2 - 0.15 * cm])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, 0), colors.Color(ACCENT_GREEN.red, ACCENT_GREEN.green, ACCENT_GREEN.blue, alpha=0.08)),
                ("BACKGROUND", (1, 0), (1, 0), colors.Color(ACCENT_RED.red, ACCENT_RED.green, ACCENT_RED.blue, alpha=0.08)),
                ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            story.append(t)
            story.append(Spacer(1, 0.3 * cm))

        # Remaining bullet lists
        sections_map = [
            ("Key Risks", "key_risks"),
            ("Key Catalysts", "key_catalysts"),
            ("What to Monitor", "monitoring_points"),
        ]
        for section_title, key in sections_map:
            items = ai.get(key, [])
            if items:
                story.append(Paragraph(section_title, S["label"]))
                for item in items:
                    story.append(Paragraph(f"• {_sanitize_for_pdf(item)}", S["bullet_light"]))
                story.append(Spacer(1, 0.2 * cm))

    _render_source_ledger(story, extras.get("source_ledger") or [], S, W)

    # ── Disclaimer ────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Spacer(1, 2 * cm))
    story.append(HRFlowable(width=W, color=BORDER, thickness=0.5, spaceAfter=12))
    story.append(Paragraph(
        "This report is an analytical research output generated by an automated system using publicly "
        "available data from Yahoo Finance. It is NOT a financial advice, a buy/sell recommendation, "
        "or a guarantee of future returns. Past performance is not indicative of future results. "
        "The Business &amp; Interpretation section is generated by a local Llama language model, "
        "validated to only cite figures present in this report's own data — narrative quality and "
        "nuance are lower than the AI Fundamental Analysis section below, which uses a larger model. "
        "Management Commentary guidance is extracted from official NSE earnings-call transcript filings "
        "by an AI model restricted to management speakers only; every figure is validated against the "
        "source transcript, but extraction is not perfectly reliable. \"Open Management Commitments\" are "
        "unverified qualitative statements management made, not confirmed outcomes. "
        f"Generated: {analysis_date}  ·  Analysis ID: {analysis_id}",
        S["disclaimer"]
    ))

    try:
        doc.build(story)
        logger.info("PDF report generated", path=str(pdf_path), analysis_id=analysis_id)
        return str(pdf_path)
    except Exception as e:
        logger.error("PDF generation failed", error=str(e))
        raise
