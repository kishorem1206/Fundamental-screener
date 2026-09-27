// Extracted from PeerSection.tsx's inline component (P&L Analysis Engine
// plan, Milestone 6) — first reused by PlIntelligenceSection.tsx's peer
// benchmark subsection, so it moved here instead of being duplicated.
export default function PercentileBar({ value }: { value: number | null | undefined }) {
  if (value === null || value === undefined) return <span style={{ color: "var(--text-dim)" }}>—</span>;
  const color =
    value >= 75 ? "#4fb3a0" :
    value >= 50 ? "#e8c766" :
    value >= 25 ? "#e0793c" : "#d9694f";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, justifyContent: "flex-end" }}>
      <div style={{ width: 56, height: 5, borderRadius: 3, background: "var(--border-subtle)", overflow: "hidden" }}>
        <div style={{ width: `${value}%`, height: "100%", background: color, borderRadius: 3 }} />
      </div>
      <span style={{ color, fontWeight: 600, minWidth: 28, textAlign: "right", fontSize: 12 }}>
        {value}
      </span>
    </div>
  );
}
