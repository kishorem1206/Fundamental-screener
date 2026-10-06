import { useState, useEffect, useCallback } from "react";
import { api } from "./api";
import type { FullAnalysis, Stock } from "./types";
import TopBar, { type Section } from "./components/TopBar";
import QuickScreener from "./components/QuickScreener";
import ExploreView from "./components/ExploreView";
import AssumptionCenter from "./components/AssumptionCenter";
import CombinedScore from "./components/CombinedScore";
import Portfolio from "./components/Portfolio";
import TechnicalScreener from "./technical/TechnicalScreener";
import AnalysisProgress from "./components/AnalysisProgress";
import AnalysisDashboard from "./components/AnalysisDashboard";

type Phase = "explore" | "progress" | "result";

export default function App() {
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<FullAnalysis | null>(null);
  const [recentAnalyses, setRecentAnalyses] = useState<FullAnalysis[]>([]);
  const [allStocks, setAllStocks] = useState<Stock[]>([]);
  const [startError, setStartError] = useState("");
  const [section, setSection] = useState<Section>("explore");

  const phase: Phase = analysis ? "result" : analysisId ? "progress" : "explore";

  const loadRecent = useCallback(async () => {
    try {
      const { analyses } = await api.getAnalyses();
      setRecentAnalyses(analyses.slice(0, 8));
    } catch {
      // silent
    }
  }, []);

  useEffect(() => {
    loadRecent();
    // 2000 comfortably covered the ~1610-company universe on 2026-09-17
    // (raised from the old 1000, which silently truncated the alphabetical
    // list before "P" — "pin" never matched "Pine Labs"). By 2026-09-28
    // the universe grew to 2624 active stocks (IPO-promotion backfill),
    // silently recreating the identical truncation bug here AND in
    // QuickScreener's coverage counter (`totalStocks={allStocks.length}`
    // in the JSX below) — that counter showed "2,624 of 2,000 stocks
    // scored" once every stock actually had a score. Raised to 5000, with
    // real headroom this time. Backend ceiling: routes/stocks.py's
    // `list_stocks(limit: ... le=5000)`, raised to match.
    api.getStocks(undefined, 5000).then(({ stocks }) => setAllStocks(stocks)).catch(() => {});
  }, [loadRecent]);

  const handleAnalysisStarted = (id: string) => {
    setStartError("");
    setAnalysisId(id);
    setAnalysis(null);
  };

  const handleAnalysisComplete = async (id: string) => {
    try {
      const data = await api.getAnalysis(id);
      setAnalysis(data);
      loadRecent();
    } catch (e) {
      console.error("Failed to load analysis", e);
    }
  };

  const handleViewAnalysis = async (id: string) => {
    try {
      const data = await api.getAnalysis(id);
      setAnalysis(data);
      setAnalysisId(id);
    } catch { /* silent */ }
  };

  const handleBack = () => {
    setAnalysisId(null);
    setAnalysis(null);
    setStartError("");
    loadRecent();
  };

  const startFullAnalysis = async (stockId: string) => {
    setStartError("");
    try {
      const { analysis_id } = await api.startAnalysis(stockId);
      handleAnalysisStarted(analysis_id);
    } catch (e: unknown) {
      setStartError(e instanceof Error ? e.message : "Failed to start analysis");
    }
  };

  const handleTopBarPick = async (stock: Stock) => {
    setStartError("");
    try {
      const { analysis_id } = await api.startAnalysis(stock.id);
      handleAnalysisStarted(analysis_id);
    } catch (e: unknown) {
      setStartError(e instanceof Error ? e.message : "Failed to start analysis");
    }
  };

  return (
    <div className="min-h-screen" style={{ background: "var(--bg-base)" }}>
      <TopBar
        allStocks={allStocks}
        showBack={phase !== "explore"}
        onBack={handleBack}
        onPick={handleTopBarPick}
        section={section}
        onSection={(next) => { handleBack(); setSection(next); }}
      />

      {/* The technical screener is a full-width workspace with its own sidebars, so it sits outside the page column. */}
      {phase === "explore" && section === "technical" && <TechnicalScreener />}

      <main className="max-w-6xl mx-auto px-6 py-8" style={phase === "explore" && section === "technical" ? { display: "none" } : undefined}>
        {startError && (
          <div className="rounded-lg px-4 py-3 text-sm mb-6"
               style={{ background: "rgba(217,105,79,0.1)", border: "1px solid rgba(217,105,79,0.3)", color: "#d9694f" }}>
            {startError}
          </div>
        )}
        {phase === "explore" && section === "quick" && (
          <QuickScreener onAnalyse={startFullAnalysis} totalStocks={allStocks.length} />
        )}
        {phase === "explore" && section === "assumptions" && <AssumptionCenter />}
        {phase === "explore" && section === "combined" && <CombinedScore onAnalyse={startFullAnalysis} />}
        {phase === "explore" && section === "portfolio" && <Portfolio />}
        {phase === "explore" && section === "explore" && (
          <ExploreView
            onAnalysisStarted={handleAnalysisStarted}
            recentAnalyses={recentAnalyses}
            onViewAnalysis={handleViewAnalysis}
          />
        )}
        {phase === "progress" && analysisId && (
          <AnalysisProgress analysisId={analysisId} onComplete={handleAnalysisComplete} />
        )}
        {phase === "result" && analysis && (
          <AnalysisDashboard analysis={analysis} />
        )}
      </main>
    </div>
  );
}
