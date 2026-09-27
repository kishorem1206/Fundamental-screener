import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import AnalysisDashboard from "./components/AnalysisDashboard";
import EditorialReport from "./components/EditorialReport";
import type { FullAnalysis } from "./types";
import "./index.css";

// Standalone export build (see frontend/export.html + html_export_service.py):
// the backend injects a real FullAnalysis object here before the file is
// downloaded. In the normal dev/prod build this is always undefined, so the
// app renders exactly as it does today.
const exportAnalysis = window.__EXPORT_ANALYSIS__;
const isExportBuild = typeof exportAnalysis === "object" && exportAnalysis !== null;

// `?view=editorial-print` — the server-side PDF renderer's target (see
// app/reporting/editorial_pdf_service.py): loads this export file headless,
// with the Editorial Report alone (no dashboard header/tab chrome) so
// Playwright's page.pdf() captures exactly the editorial document and
// nothing else. Only meaningful on an export build; a no-op query param on
// the live app otherwise.
const isEditorialPrintView = isExportBuild
  && new URLSearchParams(window.location.search).get("view") === "editorial-print";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    {isEditorialPrintView ? (
      <EditorialReport analysis={exportAnalysis as FullAnalysis} />
    ) : isExportBuild ? (
      <div className="min-h-screen" style={{ background: "var(--bg-base)" }}>
        <main className="max-w-6xl mx-auto px-6 py-8">
          <AnalysisDashboard analysis={exportAnalysis as FullAnalysis} />
        </main>
      </div>
    ) : (
      <App />
    )}
  </React.StrictMode>
);
