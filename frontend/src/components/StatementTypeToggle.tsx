export type StatementType = "CONSOLIDATED" | "STANDALONE";

// Shared Consolidated/Standalone toggle for the P&L Intelligence, Balance
// Sheet, and Cash Flow tabs — each of those three engines' backend
// `compute_*_intelligence()` functions accept an explicit `statement_type`
// override (no silent fallback to the other one when forced), matching
// this control 1:1. The PDF report deliberately has NO equivalent toggle —
// it always renders CONSOLIDATED only, per an explicit user instruction
// (see `equity_report_mapper.py`'s per-section guards).
export default function StatementTypeToggle({
  value,
  onChange,
}: {
  value: StatementType;
  onChange: (v: StatementType) => void;
}) {
  return (
    <div className="inline-flex rounded-lg p-0.5" style={{ background: "rgba(255,255,255,0.06)" }}>
      {(["CONSOLIDATED", "STANDALONE"] as const).map((opt) => (
        <button
          key={opt}
          onClick={() => onChange(opt)}
          className="px-3 py-1.5 text-xs font-medium rounded-md transition-colors"
          style={{
            background: value === opt ? "var(--accent-blue)" : "transparent",
            color: value === opt ? "#1a1a1a" : "var(--text-dim)",
          }}
        >
          {opt === "CONSOLIDATED" ? "Consolidated" : "Standalone"}
        </button>
      ))}
    </div>
  );
}
