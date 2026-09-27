import { useState, useEffect, useCallback } from "react";
import { api } from "./api";
import type { FullAnalysis, Stock } from "./types";
import TopBar, { type Section } from "./components/TopBar";
import QuickScreener from "./components/QuickScreener";
import ExploreView from "./components/ExploreView";
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
    // 2000 comfortably covers the full ~1610-company universe (grown from
    // 884 on 2026-09-17) — the old 1000 cap silently truncated the
    // alphabetically-sorted list before "P", making everything from
    // roughly the back third of the alphabet unsearchable in the global
    // search box regardless of query (found live: "pin" never matched
    // "Pine Labs").
    api.getStocks(undefined, 2000).then(({ stocks }) => setAllStocks(stocks)).catch(() => {});
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

      <main className="max-w-6xl mx-auto px-6 py-8">
        {startError && (
          <div className="rounded-lg px-4 py-3 text-sm mb-6"
               style={{ background: "rgba(217,105,79,0.1)", border: "1px solid rgba(217,105,79,0.3)", color: "#d9694f" }}>
            {startError}
          </div>
        )}
        {phase === "explore" && section === "quick" && (
          <QuickScreener onAnalyse={startFullAnalysis} totalStocks={allStocks.length} />
        )}
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
