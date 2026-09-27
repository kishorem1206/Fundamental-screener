"""Renders the PDF export as a true snapshot of the generated HTML, via
headless Chromium (Playwright) — see banking_stock_analysis_report.md
section 52 for why this was chosen over a pure-Python CSS renderer.
"""
from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

from app.logger import logger

_HEADER_TEMPLATE = """
<div style="font-size:8px; width:100%; padding:0 24px; color:#8a90a0; font-family:Inter,sans-serif;
            display:flex; justify-content:space-between;">
  <span class="title"></span>
</div>
"""
_FOOTER_TEMPLATE = """
<div style="font-size:8px; width:100%; padding:0 24px; color:#8a90a0; font-family:Inter,sans-serif;
            display:flex; justify-content:space-between;">
  <span>Fundamental Screener — Banking Intelligence Report</span>
  <span><span class="pageNumber"></span> / <span class="totalPages"></span></span>
</div>
"""


def generate_pdf_from_html(html_path: str) -> str:
    """Load the local HTML file in headless Chromium and export it to a
    same-named .pdf via Playwright's native page.pdf() — preserves
    backdrop-filter/gradients/inline-SVG charts exactly as rendered."""
    html_file = Path(html_path).resolve()
    pdf_path = html_file.with_suffix(".pdf")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page()
            page.goto(html_file.as_uri(), wait_until="networkidle")
            page.emulate_media(media="print")
            page.pdf(
                path=str(pdf_path),
                format="A4",
                print_background=True,
                display_header_footer=True,
                header_template=_HEADER_TEMPLATE,
                footer_template=_FOOTER_TEMPLATE,
                margin={"top": "36px", "bottom": "36px", "left": "0px", "right": "0px"},
            )
        finally:
            browser.close()

    logger.info("PDF report generated", path=str(pdf_path))
    return str(pdf_path)
