"""Renders the company intelligence report: Jinja → HTML → PDF through
headless Chromium (the same engine the existing editorial PDF uses, with its
own template and no dependency on the dashboard bundle).
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import Session

from app.bie.report.builder import build_report
from app.config import config

_HERE = Path(__file__).parent
_FONT = _HERE.parent.parent / "reporting" / "fonts" / "Fraunces-Variable.ttf"
_FOOTER = """
<div style="font-size:8px; width:100%; padding:0 16mm; color:#8d9994; font-family:Inter,sans-serif;
            display:flex; justify-content:space-between;">
  <span>Fundamental Research · Deep report · __NAME__</span>
  <span><span class="pageNumber"></span> / <span class="totalPages"></span></span>
</div>"""


def render_html(db: Session, company_id: str) -> str:
    env = Environment(loader=FileSystemLoader(_HERE), autoescape=select_autoescape(["html", "jinja"]))
    return env.get_template("template.html.jinja").render(r=build_report(db, company_id), font_url=_FONT.as_uri())


def render_report(db: Session, company_id: str) -> str:
    """Writes the HTML and PDF to the reports directory; returns the PDF path."""
    from playwright.sync_api import sync_playwright

    reports = Path(config.reports_dir).resolve()
    reports.mkdir(parents=True, exist_ok=True)
    stem = f"BIE-{company_id.split(':')[-1]}-{date.today():%Y%m%d}"
    html_path, pdf_path = reports / f"{stem}.html", reports / f"{stem}.pdf"
    html = render_html(db, company_id)
    html_path.write_text(html, encoding="utf-8")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page()
            page.goto(html_path.as_uri(), wait_until="load")
            page.evaluate("document.fonts.ready")
            page.pdf(path=str(pdf_path), format="A4", print_background=True, display_header_footer=True,
                     header_template="<div></div>", footer_template=_FOOTER.replace("__NAME__", company_id.split(":")[-1]),
                     margin={"top": "16mm", "bottom": "16mm", "left": "16mm", "right": "16mm"})
        finally:
            browser.close()
    return str(pdf_path)
