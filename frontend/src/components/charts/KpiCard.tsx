import type { LucideIcon } from "lucide-react";
import { TrendingUp, TrendingDown } from "lucide-react";

interface Props {
  label: string;
  value: string;
  sub?: string | null;
  icon?: LucideIcon;
  accent?: string;
  trend?: { value: number; label?: string } | null;
  loading?: boolean;
}

export default function KpiCard({
  label, value, sub, icon: Icon, accent = "#c9a227", trend, loading,
}: Props) {
  const positive = trend != null && trend.value >= 0;

  return (
    <div className="card-rich interactive p-4 flex-1 min-w-[168px]">
      <div className="flex items-start justify-between gap-3">
        <span className="eyebrow">{label}</span>
        {Icon && (
          <div
            className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0"
            style={{ background: `${accent}17`, border: `1px solid ${accent}30` }}
          >
            <Icon className="h-3.5 w-3.5" style={{ color: accent }} />
          </div>
        )}
      </div>
      {loading ? (
        <span className="skeleton h-6 w-20 mt-2" />
      ) : (
        <p className="text-2xl font-bold tracking-tight tabular-nums mt-1.5"
           style={{ color: "var(--text-primary)", fontFamily: "var(--font-display)" }}>
          {value}
        </p>
      )}
      <div className="flex items-center gap-2 mt-1">
        {trend != null && (
          <span
            className="flex items-center gap-0.5 text-xs font-semibold"
            style={{ color: positive ? "#4fb3a0" : "#d9694f" }}
          >
            {positive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
            {Math.abs(trend.value).toFixed(2)}%
          </span>
        )}
        {sub && <span className="text-xs" style={{ color: "var(--text-dim)" }}>{sub}</span>}
      </div>
    </div>
  );
}
