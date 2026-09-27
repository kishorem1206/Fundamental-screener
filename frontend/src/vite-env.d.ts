/// <reference types="vite/client" />

interface Window {
  /** Set by the standalone export build (see main.tsx) — a real FullAnalysis
   * object once the backend injects it; a placeholder string otherwise. */
  __EXPORT_ANALYSIS__?: unknown;
  /** Path-keyed lookup of pre-fetched API responses for the export build —
   * see api.ts's req() and app/reporting/html_export_service.py. */
  __EXPORT_BUNDLE__?: Record<string, unknown>;
}
