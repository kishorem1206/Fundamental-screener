import { useCallback, useEffect, useRef, useState } from "react";
import { FileText, Loader2, RefreshCw, Sheet } from "lucide-react";
import { api } from "../api";

export interface DeepReportStatus {
  symbol: string;
  facts: number;
  built: boolean;
  built_at: string | null;
  job: { state: "running" | "done" | "failed"; step: string | null; steps_done: number; errors: Record<string, string> } | null;
}

const day = (iso: string) => new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });

/** Build, follow and open a company's deep report (the sourced, sector-first PDF). */
export default function DeepReportButton({ symbol, onBuilt }: { symbol: string; onBuilt?: () => void }) {
  const [status, setStatus] = useState<DeepReportStatus | null>(null);
  const [error, setError] = useState("");
  const wasRunning = useRef(false);

  const refresh = useCallback(async () => {
    try {
      const next = await api.bieStatus(symbol);
      setStatus(next);
      setError("");
      if (wasRunning.current && next.job?.state === "done") onBuilt?.();
      wasRunning.current = next.job?.state === "running";
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Could not read the report status");
    }
  }, [symbol, onBuilt]);

  useEffect(() => { setStatus(null); wasRunning.current = false; refresh(); }, [refresh]);

  const running = status?.job?.state === "running";
  useEffect(() => {
    if (!running) return;
    const timer = setInterval(refresh, 3000);
    return () => clearInterval(timer);
  }, [running, refresh]);

  const build = async () => {
    try {
      await api.bieBuild(symbol);
      wasRunning.current = true;
      await refresh();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Could not start the build");
    }
  };

  if (error) return <span className="text-xs" style={{ color: "var(--accent-red)" }}>{error}</span>;
  if (!status) return null;

  const failed = status.job?.state === "failed";
  const missing = status.job?.state === "done" ? Object.keys(status.job.errors).length : 0;
  const primary = { background: "var(--accent-blue)", color: "#10182b" };

  if (running) {
    return (
      <div className="flex items-center gap-2 text-sm" style={{ color: "var(--text-secondary)" }}>
        <Loader2 size={15} className="animate-spin" />
        <span>Building deep report · {status.job?.step ?? "Starting"} <span style={{ color: "var(--text-muted)" }}>(step {status.job?.steps_done})</span></span>
      </div>
    );
  }
  return (
    <div className="flex items-center gap-3 flex-wrap">
      {status.built ? (
        <a href={`/api/bie/${symbol}/report.pdf`} target="_blank" rel="noreferrer"
           className="inline-flex items-center gap-2 px-3 py-2 rounded-md text-sm font-semibold" style={primary}
           title="Opens in a new tab. The PDF is drawn fresh each time, which takes up to a minute.">
          <FileText size={15} /> Open deep report (PDF)
        </a>
      ) : (
        <button onClick={build} className="inline-flex items-center gap-2 px-3 py-2 rounded-md text-sm font-semibold" style={primary}>
          <FileText size={15} /> Build deep report
        </button>
      )}
      {status.built && (
        <a href={`/api/bie/${symbol}/model.xlsx`} className="inline-flex items-center gap-1 text-sm" style={{ color: "var(--accent-gold-bright)" }}
           title="The model behind the report: history, assumptions, forecast statements, valuation and charts.">
          <Sheet size={14} /> Excel model
        </a>
      )}
      {status.built && (
        <button onClick={build} className="inline-flex items-center gap-1 text-xs" style={{ color: "var(--text-muted)" }}
                title="Fetch the latest filings and rebuild. Takes a few minutes.">
          <RefreshCw size={12} /> Rebuild
        </button>
      )}
      <span className="text-xs" style={{ color: failed ? "var(--accent-red)" : "var(--text-muted)" }}>
        {failed ? `Build failed: ${Object.values(status.job?.errors ?? {})[0] ?? "unknown error"}`
          : status.built && status.built_at ? `Built ${day(status.built_at)}${missing ? ` · ${missing} source${missing > 1 ? "s" : ""} unavailable` : ""}`
          : "Sector, company, forecast and sources in one PDF. Takes a few minutes."}
      </span>
    </div>
  );
}
