"""One integrated report per company: the Stock Quality framework section
(new), then the existing editorial report, then the deep report — bound into
a single PDF. The two existing reports are rendered exactly as before
(editorial_pdf_service.py, app/bie/report/render.py) and not changed; only the
opening section is new, drawn in the same editorial design.

    GET /api/framework/{symbol}/integrated-report.pdf
"""
