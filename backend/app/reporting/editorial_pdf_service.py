"""Renders the Editorial Report tab (frontend/src/components/EditorialReport.tsx)
to PDF via headless Chromium — same technique `pdf_report_service.py` already
proved out for the older banking Jinja report, pointed at a different
target: the export HTML bundle's `?view=editorial-print` mode
(frontend/src/main.tsx), which renders the editorial document alone with no
dashboard header/tab chrome. This means the PDF is a true snapshot of the
exact same React component and CSS the "Editorial Report" tab shows live —
not a re-implementation in a different rendering engine, so colours, fonts
and layout are identical by construction, and the only remaining work is
print-specific CSS (see EditorialReport.tsx's `@media print` block) rather
than reproducing the design a second time.

Replaces `equity_pdf_service.generate_pdf_report` as what "Download PDF"
returns (2026-09-21, user's explicit request) — that Node/pdf-renderer path
and the two even older ones (`report_service.py`'s ReportLab renderer,
`pdf_report_service.py` + `html_report_service.py`'s banking-only Playwright
path) are left on disk, unused, per this codebase's established convention
of not deleting previously-verified rendering code that might be wanted
again, rather than actively wiring three renderers at once.
"""
from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

from app.config import config
from app.logger import logger

_FOOTER_TEMPLATE = """
<div style="font-size:8px; width:100%; padding:0 16mm; color:#8d9994; font-family:Inter,sans-serif;
            display:flex; justify-content:space-between;">
  <span>Fundamental Research · Editorial report</span>
  <span><span class="pageNumber"></span> / <span class="totalPages"></span></span>
</div>
"""
# No header template (blank) — the document's own section eyebrows already
# orient the reader; a repeated running header would duplicate that.
_HEADER_TEMPLATE = '<div></div>'


def generate_editorial_pdf(analysis_id: str, db) -> str:
    """Ensures the export HTML bundle exists for this analysis (building it
    if needed, same as the "Download HTML" path), then renders its
    `?view=editorial-print` route to a same-named .pdf via Playwright's
    native page.pdf(). Returns the PDF's file path."""
    from app.reporting.html_export_service import generate_html_export

    reports_dir = Path(config.reports_dir).resolve()
    html_path = reports_dir / f"{analysis_id}.html"
    if not html_path.exists():
        generate_html_export(analysis_id, db)

    pdf_path = reports_dir / f"{analysis_id}.pdf"
    print_url = html_path.as_uri() + "?view=editorial-print"

    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page()
            page.goto(print_url, wait_until="load")
            # The export bundle embeds all data inline (no network fetches
            # to wait on), but Google Fonts (Fraunces/Inter) load over the
            # network — wait for them so headings don't fall back to the
            # system serif in the render.
            page.evaluate("document.fonts.ready")
            page.wait_for_selector(".er-root", timeout=15000)
            page.emulate_media(media="print")
            # Recharts (the report's price/trend/waterfall/donut/radar/scatter
            # charts, added 2026-09-21) mounts with a ~300-800ms entrance
            # animation and measures its own width via ResizeObserver, which
            # re-fires asynchronously after emulate_media's print-layout
            # reflow — page.pdf() is a single static capture with no second
            # chance, so this settle wait must outlast both before printing,
            # or a chart can be captured mid-animation or at a stale width.
            page.wait_for_timeout(1200)
            page.pdf(
                path=str(pdf_path),
                format="A4",
                print_background=True,
                display_header_footer=True,
                header_template=_HEADER_TEMPLATE,
                footer_template=_FOOTER_TEMPLATE,
                margin={"top": "16mm", "bottom": "14mm", "left": "12mm", "right": "12mm"},
            )
        finally:
            browser.close()

    logger.info("Editorial PDF generated", analysis_id=analysis_id, path=str(pdf_path))
    return str(pdf_path)
