import DeepReportButton from "./DeepReportButton";
import DeepReportSection from "./sections/DeepReportSection";
import { useState } from "react";
import { FileText, Download, Gauge, ShieldCheck, Database, Sparkles, IndianRupee, Landmark, Percent, ArrowLeftRight } from "lucide-react";
import type { FullAnalysis } from "../types";
import { api } from "../api";
import KpiCard from "./charts/KpiCard";
import ScoreGauge from "./charts/ScoreGauge";
import OverviewSection from "./sections/OverviewSection";
import SummarySection from "./sections/SummarySection";
import FinancialsSection from "./sections/FinancialsSection";
import ScoresSection from "./sections/ScoresSection";
import SectorSection from "./sections/SectorSection";
import PeerSection from "./sections/PeerSection";
import RisksSection from "./sections/RisksSection";
import NewsSection from "./sections/NewsSection";
import CalendarSection from "./sections/CalendarSection";
import DeepResearchSection from "./sections/DeepResearchSection";
import AiSection from "./sections/AiSection";
import ConcallSection from "./sections/ConcallSection";
import PlIntelligenceSection from "./sections/PlIntelligenceSection";
import BalanceSheetIntelligenceSection from "./sections/BalanceSheetIntelligenceSection";
import CashFlowIntelligenceSection from "./sections/CashFlowIntelligenceSection";
import QuarterlySection from "./sections/QuarterlySection";
import BankRoeSection from "./sections/BankRoeSection";
import EditorialReport from "./EditorialReport";

type Tab = "overview" | "editorial" | "deep_report" | "summary" | "financials" | "quarterly" | "bank_roe" | "pl_intelligence" | "balance_sheet_intelligence" | "cash_flow_intelligence" | "scores" | "sector" | "peers" | "risks" | "news" | "calendar" | "concall" | "research" | "ai";

const TABS: { key: Tab; label: string }[] = [
  { key: "overview", label: "Overview" },
  { key: "editorial", label: "Editorial Report" },
  { key: "deep_report", label: "Deep Report" },
  { key: "summary", label: "Summary" },
  { key: "financials", label: "Financials" },
  { key: "quarterly", label: "Quarterly" },
  { key: "bank_roe", label: "ROE & Valuation" },
  { key: "pl_intelligence", label: "P&L Intelligence" },
  { key: "balance_sheet_intelligence", label: "Balance Sheet" },
  { key: "cash_flow_intelligence", label: "Cash Flow" },
  { key: "scores", label: "Scores" },
  { key: "sector", label: "Sector" },
  { key: "peers", label: "Peers" },
  { key: "risks", label: "Risks & Catalysts" },
  { key: "news", label: "News" },
  { key: "calendar", label: "Calendar" },
  { key: "concall", label: "Concall" },
  { key: "research", label: "Deep Research" },
  { key: "ai", label: "AI Analysis" },
];

// ROE -> book value -> P/B modelling only makes sense for balance-sheet lenders.
const LENDER_SECTORS = new Set(["Banks", "NBFCs", "Housing Finance", "Microfinance", "Gold Loans"]);

interface Props { analysis: FullAnalysis; }

export default function AnalysisDashboard({ analysis }: Props) {
  const [tab, setTab] = useState<Tab>("overview");
  const [generatingPdf, setGeneratingPdf] = useState(false);
  const [pdfReady, setPdfReady] = useState(analysis.report_available);

  const company = analysis.company_info;
  const scores = analysis.scores;
  const score = analysis.overall_score;
  const confidence = analysis.confidence_score;
  const dq = analysis.data_quality_score;
  const aiRating = analysis.ai_analysis?.rating || analysis.ai_rating;
  const valRating = analysis.ai_analysis?.valuation_view || analysis.valuation_rating;

  const handleGeneratePdf = async () => {
    setGeneratingPdf(true);
    try {
      await api.generateReport(analysis.id);
      setPdfReady(true);
    } catch (e) {
      console.error(e);
    } finally {
      setGeneratingPdf(false);
    }
  };

  const ratingColor: Record<string, string> = {
    STRONG: "#4fb3a0", GOOD: "#c9a227", FAIR: "#e0793c", WEAK: "#d9694f", POOR: "#d9694f",
  };

  return (
    <div className="space-y-6 fade-in">
      {/* Company header */}
      <div className="card-rich p-6">
        <div className="flex flex-col xl:flex-row xl:items-center gap-6">
          {/* Company info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="badge badge-blue text-xs">
                {company?.exchange}: {company?.symbol}
              </span>
              {company?.market_cap_category && (
                <span className="badge badge-gray text-xs">
                  {company.market_cap_category.replace("_", " ")}
                </span>
              )}
              {aiRating && (
                <span className="badge" style={{
                  color: ratingColor[aiRating] || "#a9b3c9",
                  background: `${ratingColor[aiRating] || "#a9b3c9"}18`,
                  border: `1px solid ${ratingColor[aiRating] || "#a9b3c9"}35`,
                }}>{aiRating}{valRating ? ` · ${valRating}` : ""}</span>
              )}
            </div>
            <h1 className="text-2xl font-bold mt-1" style={{ color: "var(--text-primary)" }}>
              {company?.company_name || analysis.stock_id}
            </h1>
            <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>
              {company?.sector}
              {company?.industry ? ` · ${company.industry}` : ""}
            </p>
            {company?.symbol && <div className="mt-3"><DeepReportButton symbol={company.symbol} /></div>}
            {company?.current_price?.price != null && (
              <div className="flex items-baseline gap-2 mt-2 flex-wrap">
                <span className="text-xl font-bold tabular-nums" style={{ color: "var(--text-primary)" }}>
                  ₹{company.current_price.price.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
                {company.current_price.change_pct != null && (
                  <span className="text-sm font-semibold tabular-nums"
                        style={{ color: company.current_price.change_pct >= 0 ? "#4fb3a0" : "#d9694f" }}>
                    {company.current_price.change_pct >= 0 ? "+" : ""}
                    {company.current_price.change_pct.toFixed(2)}%
                  </span>
                )}
                <span className="text-xs" style={{ color: "var(--text-dim)" }}>
                  Yahoo Finance · {new Date(company.current_price.as_of).toLocaleString("en-IN", {
                    hour: "2-digit", minute: "2-digit", day: "2-digit", month: "short",
                  })}
                </span>
              </div>
            )}
            {analysis.metrics?.data_years !== undefined && (
              <p className="text-xs mt-2" style={{ color: "var(--text-dim)" }}>
                {analysis.metrics.data_years} years of financial data
                {analysis.metrics.years_available?.length > 0
                  ? ` (${analysis.metrics.years_available[0]}–${analysis.metrics.years_available.at(-1)})`
                  : ""}
              </p>
            )}
          </div>

          <ScoreGauge value={score} />
        </div>

        {/* Live snapshot — price, market cap, P/E, 52-week range */}
        <div className="flex flex-wrap gap-3 mt-5">
          <KpiCard label="Price"
                   value={company?.current_price?.price != null ? `₹${company.current_price.price.toLocaleString("en-IN", { maximumFractionDigits: 2 })}` : "—"}
                   sub={company?.current_price?.change_pct != null ? `${company.current_price.change_pct >= 0 ? "+" : ""}${company.current_price.change_pct.toFixed(2)}% today` : undefined}
                   icon={IndianRupee} accent={company?.current_price?.change_pct != null && company.current_price.change_pct >= 0 ? "#4fb3a0" : "#d9694f"} />
          <KpiCard label="Market Cap"
                   value={(() => {
                     const mc = company?.market_cap ?? analysis.metrics?.market_cap;
                     return mc != null ? `₹${(mc / 1e7).toLocaleString("en-IN", { maximumFractionDigits: 0 })} Cr` : "—";
                   })()}
                   sub={company?.market_cap_category?.replace(/_/g, " ") || undefined}
                   icon={Landmark} accent="#c9a227" />
          <KpiCard label="P/E (TTM)"
                   value={analysis.metrics?.pe_ratio != null ? `${analysis.metrics.pe_ratio.toFixed(1)}x` : "—"}
                   sub="trailing twelve months" icon={Percent} accent="#e0793c" />
          <KpiCard label="52-Week Range"
                   value={company?.week52_low != null && company?.week52_high != null
                     ? `₹${company.week52_low.toFixed(0)}–₹${company.week52_high.toFixed(0)}` : "—"}
                   sub="Yahoo Finance" icon={ArrowLeftRight} accent="#7fb8ff" />
        </div>

        {/* KPI row */}
        <div className="flex flex-wrap gap-3 mt-3">
          <KpiCard label="Confidence" value={confidence !== null ? `${confidence.toFixed(0)}%` : "—"}
                   sub="analysis confidence" icon={ShieldCheck} accent="#e8c766" />
          <KpiCard label="Data Quality" value={dq !== null ? `${dq.toFixed(0)}%` : "—"}
                   sub="data completeness" icon={Database} accent="#7fb8ff" />
          <KpiCard label="AI Rating" value={aiRating || "—"} sub={valRating || undefined}
                   icon={Sparkles} accent={ratingColor[aiRating || ""] || "#a9b3c9"} />
          <KpiCard label="Overall Rating" value={scores?.overall_rating || "—"}
                   sub="composite score band" icon={Gauge} accent="#c9a227" />
        </div>

        {/* PDF buttons */}
        <div className="mt-5 pt-4 flex items-center gap-3 flex-wrap"
             style={{ borderTop: "1px solid var(--border-subtle)" }}>
          {pdfReady ? (
            <>
              <a href={api.getReportUrl(analysis.id)} target="_blank" rel="noreferrer"
                 className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium"
                 style={{ background: "rgba(201,162,39,0.15)", color: "#e8c766",
                          border: "1px solid rgba(201,162,39,0.3)", textDecoration: "none" }}>
                <FileText className="h-3.5 w-3.5" /> View Report
              </a>
              <a href={api.getReportUrl(analysis.id)} download
                 className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium"
                 style={{ background: "rgba(201,162,39,0.15)", color: "#e8c766",
                          border: "1px solid rgba(201,162,39,0.3)", textDecoration: "none" }}>
                <Download className="h-3.5 w-3.5" /> Download PDF
              </a>
            </>
          ) : (
            <button
              onClick={handleGeneratePdf}
              disabled={generatingPdf}
              className="px-4 py-2 rounded-lg text-sm font-medium"
              style={{ background: "#c9a227", color: "white", border: "none",
                       cursor: generatingPdf ? "not-allowed" : "pointer",
                       opacity: generatingPdf ? 0.7 : 1 }}>
              {generatingPdf ? "Generating PDF…" : "Generate PDF Report"}
            </button>
          )}
          <a href={api.getHtmlReportUrl(analysis.id)} download
             className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium"
             style={{ background: "rgba(127,184,255,0.15)", color: "#7fb8ff",
                      border: "1px solid rgba(127,184,255,0.3)", textDecoration: "none" }}>
            <Download className="h-3.5 w-3.5" /> Download HTML
          </a>
          <span className="text-xs" style={{ color: "var(--text-dim)" }}>
            Analysis ID: {analysis.id}
          </span>
        </div>
      </div>

      {/* Tab navigation */}
      <div className="flex items-center gap-1 flex-wrap"
           style={{ borderBottom: "1px solid var(--border-subtle)", paddingBottom: "0" }}>
        {TABS.filter(({ key }) => key !== "bank_roe" || LENDER_SECTORS.has(analysis.sector_analysis?.sector_name ?? "")).map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className="tab-btn"
            style={{
              borderBottom: tab === key ? "2px solid #c9a227" : "2px solid transparent",
              borderRadius: "0",
              paddingBottom: "10px",
              color: tab === key ? "#e8c766" : "var(--text-muted)",
            }}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div>
        {tab === "overview" && <OverviewSection analysis={analysis} />}
        {tab === "editorial" && <EditorialReport analysis={analysis} />}
        {tab === "summary" && <SummarySection analysis={analysis} />}
        {tab === "financials" && <FinancialsSection analysis={analysis} />}
        {tab === "deep_report" && <DeepReportSection analysis={analysis} />}
        {tab === "quarterly" && <QuarterlySection analysis={analysis} />}
        {tab === "bank_roe" && <BankRoeSection analysis={analysis} />}
        {tab === "pl_intelligence" && <PlIntelligenceSection analysis={analysis} />}
        {tab === "balance_sheet_intelligence" && <BalanceSheetIntelligenceSection analysis={analysis} />}
        {tab === "cash_flow_intelligence" && <CashFlowIntelligenceSection analysis={analysis} />}
        {tab === "scores" && <ScoresSection analysis={analysis} />}
        {tab === "sector" && <SectorSection analysis={analysis} />}
        {tab === "peers" && <PeerSection analysis={analysis} />}
        {tab === "risks" && <RisksSection analysis={analysis} />}
        {tab === "news" && <NewsSection analysis={analysis} />}
        {tab === "calendar" && <CalendarSection analysis={analysis} />}
        {tab === "concall" && <ConcallSection analysis={analysis} />}
        {tab === "research" && <DeepResearchSection analysis={analysis} />}
        {tab === "ai" && <AiSection analysis={analysis} />}
      </div>
    </div>
  );
}
