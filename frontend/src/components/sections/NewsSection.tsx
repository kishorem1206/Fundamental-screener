import { useState, useEffect } from "react";
import { ExternalLink, Newspaper } from "lucide-react";
import { api } from "../../api";
import type { FullAnalysis, NewsItem } from "../../types";

function timeAgo(iso: string | null) {
  if (!iso) return "—";
  const dt = new Date(iso);
  if (Number.isNaN(dt.getTime())) return iso;
  const diffMs = Date.now() - dt.getTime();
  const days = Math.floor(diffMs / 86400000);
  if (days === 0) return "Today";
  if (days === 1) return "Yesterday";
  if (days < 30) return `${days}d ago`;
  return dt.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
}

export default function NewsSection({ analysis }: { analysis: FullAnalysis }) {
  const companyId = analysis.company_info?.stock_id || analysis.stock_id;
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!companyId) { setLoading(false); return; }
    setLoading(true);
    api.getCompanyNews(companyId)
      .then((r) => setNews(r.news))
      .catch(() => setNews([]))
      .finally(() => setLoading(false));
  }, [companyId]);

  if (loading) {
    return <div className="py-12 flex items-center justify-center"><div className="spinner" /></div>;
  }

  if (news.length === 0) {
    return (
      <div className="card-rich p-6 text-center text-sm" style={{ color: "var(--text-muted)" }}>
        No recent news available for this company.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {news.map((n, i) => (
        <a
          key={i}
          href={n.url || undefined}
          target="_blank"
          rel="noreferrer"
          className="card-rich interactive p-4 flex items-start gap-3 group"
          style={{ textDecoration: "none", cursor: n.url ? "pointer" : "default" }}
        >
          <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5"
               style={{ background: "rgba(201,162,39,0.12)", border: "1px solid rgba(201,162,39,0.25)" }}>
            <Newspaper className="h-3.5 w-3.5" style={{ color: "#e8c766" }} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-3">
              <p className="text-sm font-semibold leading-snug" style={{ color: "var(--text-primary)" }}>
                {n.headline}
              </p>
              {n.url && <ExternalLink className="h-3.5 w-3.5 flex-shrink-0 mt-0.5 opacity-0 group-hover:opacity-60 transition-opacity" style={{ color: "var(--text-dim)" }} />}
            </div>
            {n.summary && (
              <p className="text-xs mt-1.5 leading-relaxed" style={{ color: "var(--text-secondary)" }}>
                {n.summary}
              </p>
            )}
            <div className="flex items-center gap-2 mt-2 text-xs" style={{ color: "var(--text-dim)" }}>
              {n.provider && <span>{n.provider}</span>}
              {n.provider && <span>·</span>}
              <span>{timeAgo(n.published_at)}</span>
            </div>
          </div>
        </a>
      ))}
    </div>
  );
}
