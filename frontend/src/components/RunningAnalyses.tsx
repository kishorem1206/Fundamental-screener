// A strip under the top bar, on every page, for full analyses running on the server.
// The work happens on the server, so nothing here keeps a run alive: this only shows it,
// which is why it survives changing page, changing tab and refreshing.
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api";

interface Run { analysis_id: string; company_name: string; symbol: string; status: string; current_stage: string | null; overall_progress: number }
interface Finished { analysis_id: string; company_name: string; ok: boolean; error: string | null }

const POLL_MS = 4000;

export default function RunningAnalyses({ openId, onOpenRunning, onOpenFinished }: {
  openId: string | null; onOpenRunning: (id: string) => void; onOpenFinished: (id: string) => void;
}) {
  const [runs, setRuns] = useState<Run[]>([]);
  const [finished, setFinished] = useState<Finished[]>([]);
  const seen = useRef<Map<string, Run>>(new Map());

  const poll = useCallback(async () => {
    try {
      const { analyses } = await api.activeAnalyses();
      setRuns(analyses);
      const active = new Set(analyses.map((a) => a.analysis_id));
      for (const [id, run] of seen.current) {
        if (active.has(id)) continue;
        seen.current.delete(id);
        const s = await api.getAnalysisStatus(id);
        setFinished((f) => [...f, { analysis_id: id, company_name: run.company_name, ok: s.status === "COMPLETED", error: s.error_message ?? null }]);
      }
      analyses.forEach((a) => seen.current.set(a.analysis_id, a));
    } catch { /* the next poll tries again */ }
  }, []);

  useEffect(() => {
    poll();
    const timer = setInterval(poll, POLL_MS);
    // browsers slow timers in a hidden tab, so catch up as soon as it is visible again
    const onShow = () => { if (document.visibilityState === "visible") poll(); };
    document.addEventListener("visibilitychange", onShow);
    return () => { clearInterval(timer); document.removeEventListener("visibilitychange", onShow); };
  }, [poll]);

  const dismiss = (id: string) => setFinished((f) => f.filter((x) => x.analysis_id !== id));
  const shownRuns = runs.filter((r) => r.analysis_id !== openId);
  const shownDone = finished.filter((f) => f.analysis_id !== openId);
  if (shownRuns.length === 0 && shownDone.length === 0) return null;

  const link = { color: "var(--accent-gold-bright)" };
  return (
    <div className="max-w-6xl mx-auto px-6 pt-3 space-y-1.5 text-xs">
      {shownRuns.map((r) => (
        <div key={r.analysis_id} className="flex items-center gap-3 rounded-lg px-3 py-2" style={{ border: "1px solid var(--border-subtle)", background: "var(--glass)", color: "var(--text-secondary)" }}>
          <span><b style={{ color: "var(--text-primary)" }}>{r.company_name}</b>: full analysis running, {Math.min(100, Math.round(r.overall_progress))}%
            {r.current_stage ? ` · ${r.current_stage.replace(/_/g, " ")}` : ""}. You can keep working.</span>
          <button onClick={() => onOpenRunning(r.analysis_id)} className="ml-auto underline" style={link}>View</button>
        </div>
      ))}
      {shownDone.map((f) => (
        <div key={f.analysis_id} className="flex items-center gap-3 rounded-lg px-3 py-2" style={{ border: `1px solid ${f.ok ? "#4fb3a0" : "#d9694f"}`, background: "var(--glass)", color: "var(--text-secondary)" }}>
          <span><b style={{ color: "var(--text-primary)" }}>{f.company_name}</b>: {f.ok ? "full analysis finished." : `full analysis failed${f.error ? `: ${f.error}` : "."}`}</span>
          {f.ok && <button onClick={() => { dismiss(f.analysis_id); onOpenFinished(f.analysis_id); }} className="ml-auto underline" style={link}>Open</button>}
          <button onClick={() => dismiss(f.analysis_id)} className={f.ok ? "underline" : "ml-auto underline"} style={{ color: "var(--text-dim)" }}>Dismiss</button>
        </div>
      ))}
    </div>
  );
}
