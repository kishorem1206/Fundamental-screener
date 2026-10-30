"""OCR for BSE's scanned quarterly-results filings.

These PDFs are SEBI Regulation 33/52 format results that get physically
signed/stamped by auditors and then scanned — the cover letter has a real
text layer, but the actual numbers pages do not. Tesseract OCR on a
high-DPI render is the only way to get text out of them without a
vision-capable LLM (none is configured for this project — see
sector_frameworks/banking.md ingestion notes).

OCR misreads individual digits often enough that every value pulled through
this path must be stored at MEDIUM confidence, never HIGH — see
app/ingestion/banking_ingestion.py.
"""
from __future__ import annotations

import pypdfium2 as pdfium
import pytesseract

from app.ingestion.pdfium_lock import PDFIUM_LOCK


def ocr_pdf_pages(pdf_bytes: bytes, page_indices: list[int], scale: float = 3.0) -> str:
    """OCR the given 0-indexed pages of a PDF and return their concatenated text."""
    images = []
    with PDFIUM_LOCK:
        pdf = pdfium.PdfDocument(pdf_bytes)
        try:
            for i in page_indices:
                if i >= len(pdf):
                    continue
                page = pdf[i]
                try:
                    images.append((i, page.render(scale=scale).to_pil()))
                finally:
                    page.close()
        finally:
            pdf.close()
    # Tesseract is slow and does not touch PDFium, so it runs outside the lock
    return "\n\n".join(f"--- page {i + 1} ---\n{pytesseract.image_to_string(image)}" for i, image in images)
