"""One lock for every PDFium call in the process.

PDFium is not thread-safe: two threads may not call it at the same time, even
on different documents, and the server runs work on many threads. A clash is a
segmentation fault that kills the whole server, not an exception that could be
caught (seen 2026-10-30: `FPDF_LoadPage`, during a full analysis). So every use
holds this lock and closes its pages itself, rather than leaving them for the
garbage collector, which could free them from any thread.
"""
from __future__ import annotations

import threading

PDFIUM_LOCK = threading.RLock()
