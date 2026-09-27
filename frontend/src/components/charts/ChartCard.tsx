import type { ReactNode } from "react";

interface Props {
  eyebrow: string;
  title: string;
  legend?: ReactNode;
  children: ReactNode;
  className?: string;
}

export default function ChartCard({ eyebrow, title, legend, children, className = "" }: Props) {
  return (
    <div className={`card-rich p-5 ${className}`}>
      <div className="flex items-start justify-between gap-4 mb-4">
        <div>
          <p className="eyebrow">{eyebrow}</p>
          <p className="text-sm font-semibold mt-0.5" style={{ color: "var(--text-primary)" }}>
            {title}
          </p>
        </div>
        {legend && <div className="flex items-center gap-4 text-[11px]" style={{ color: "var(--text-dim)" }}>{legend}</div>}
      </div>
      {children}
    </div>
  );
}

export function LegendDot({ color, label }: { color: string; label: string }) {
  return (
    <span className="flex items-center gap-1.5">
      <span className="w-2.5 h-2.5 rounded-full" style={{ background: color }} />
      {label}
    </span>
  );
}

export function ChartEmptyState({ message = "No data available" }: { message?: string }) {
  return (
    <div className="flex items-center justify-center text-xs" style={{ height: 180, color: "var(--text-dim)" }}>
      {message}
    </div>
  );
}

export const chartTooltipStyle = {
  contentStyle: {
    background: "var(--bg-card)",
    border: "1px solid var(--border-subtle)",
    borderRadius: 10,
    color: "var(--text-primary)",
    fontSize: 12,
    boxShadow: "0 8px 24px rgba(0,0,0,0.35)",
  },
  labelStyle: { color: "var(--text-secondary)", marginBottom: 4, fontWeight: 600 },
};

export const axisTick = { fill: "var(--text-dim)", fontSize: 11 };
export const gridStroke = "rgba(255,255,255,0.05)";
