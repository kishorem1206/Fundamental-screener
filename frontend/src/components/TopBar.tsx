import { useState, useMemo, useRef, useEffect } from "react";
import { Search, ArrowLeft, LayoutGrid, Zap, SlidersHorizontal, Layers, CandlestickChart } from "lucide-react";
import type { Stock } from "../types";

export type Section = "combined" | "explore" | "quick" | "technical" | "assumptions";

interface Props {
  allStocks: Stock[];
  showBack: boolean;
  onBack: () => void;
  onPick: (stock: Stock) => void;
  section: Section;
  onSection: (section: Section) => void;
}

export default function TopBar({ allStocks, showBack, onBack, onPick, section, onSection }: Props) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const boxRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return [];
    // Real bug found live 2026-09-17: with 1610 tracked stocks, a plain
    // `.filter(...).slice(0, 8)` (no ranking) let alphabetically-earlier
    // "contains" matches (e.g. "Lupin", "Spinners", "CAPINVIT" for query
    // "pin") crowd "Pine Labs" — a "starts with" match — out of the first
    // 8 results entirely. Rank starts-with (symbol, then name) above
    // contains-anywhere before slicing, so the obvious match always wins.
    const rank = (s: Stock): number => {
      const name = s.company_name.toLowerCase();
      const symbol = s.symbol.toLowerCase();
      if (symbol === q) return 0;
      if (symbol.startsWith(q)) return 1;
      if (name.startsWith(q)) return 2;
      if (symbol.includes(q)) return 3;
      return 4; // name.includes(q) — the only remaining case once filtered
    };
    return allStocks
      .filter((s) => s.company_name.toLowerCase().includes(q) || s.symbol.toLowerCase().includes(q))
      .sort((a, b) => rank(a) - rank(b))
      .slice(0, 8);
  }, [query, allStocks]);

  const handlePick = (s: Stock) => {
    onPick(s);
    setQuery("");
    setOpen(false);
  };

  return (
    <header
      className="px-6 py-3 flex items-center gap-4 sticky top-0 z-50"
      style={{
        borderBottom: "1px solid var(--border-subtle)",
        background: "rgba(7,15,31,0.92)",
        backdropFilter: "blur(12px)",
      }}
    >
      <button onClick={onBack} className="flex items-center gap-3 text-left flex-shrink-0">
        <div className="w-7 h-7 rounded-lg flex items-center justify-center"
             style={{ background: "rgba(201,162,39,0.15)", border: "1px solid rgba(201,162,39,0.3)" }}>
          <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="#c9a227" strokeWidth="2">
            <path d="M3 3h7v7H3zM14 3h7v7h-7zM14 14h7v7h-7zM3 14h7v7H3z"/>
          </svg>
        </div>
        <div className="hidden sm:block">
          <div className="text-base font-semibold" style={{ color: "var(--text-primary)", fontFamily: "var(--font-display)" }}>
            Equity Research
          </div>
          <div className="text-xs" style={{ color: "var(--text-dim)" }}>India · NSE / BSE</div>
        </div>
      </button>

      <div ref={boxRef} className="relative flex-1 max-w-md">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5" style={{ color: "var(--text-dim)" }} />
          <input
            type="text"
            value={query}
            onChange={(e) => { setQuery(e.target.value); setOpen(true); }}
            onFocus={() => setOpen(true)}
            placeholder="Search any stock by name or symbol…"
            className="w-full rounded-lg pl-9 pr-3 py-2 text-sm"
            style={{
              background: "var(--bg-card)", border: "1px solid var(--border-subtle)",
              color: "var(--text-primary)", outline: "none",
            }}
          />
        </div>
        {open && results.length > 0 && (
          <div className="absolute top-full mt-1.5 left-0 right-0 rounded-lg overflow-hidden z-50"
               style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)", boxShadow: "0 12px 32px rgba(0,0,0,0.4)" }}>
            {results.map((s) => (
              <button
                key={s.id}
                onClick={() => handlePick(s)}
                className="w-full text-left px-3 py-2.5 flex items-center justify-between gap-3 transition-colors"
                style={{ borderBottom: "1px solid var(--border-subtle)" }}
                onMouseDown={(e) => e.preventDefault()}
              >
                <div className="min-w-0">
                  <div className="text-sm font-medium truncate" style={{ color: "var(--text-primary)" }}>
                    {s.company_name}
                  </div>
                  <div className="text-xs" style={{ color: "var(--text-dim)" }}>
                    {s.exchange}: {s.symbol} · {s.sector || "—"}
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {showBack && (
        <button
          onClick={onBack}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg flex-shrink-0"
          style={{ color: "var(--text-muted)", border: "1px solid var(--border-subtle)" }}
        >
          <ArrowLeft className="h-3 w-3" /> Back
        </button>
      )}
      <nav className="hidden md:flex items-center gap-1 flex-shrink-0">
        {([
          { key: "combined" as const, label: "Combined Score", Icon: Layers },
          { key: "explore" as const, label: "Full Analysis", Icon: LayoutGrid },
          { key: "quick" as const, label: "Quick Screener", Icon: Zap },
          { key: "technical" as const, label: "Technical Screener", Icon: CandlestickChart },
          { key: "assumptions" as const, label: "Assumptions", Icon: SlidersHorizontal },
        ]).map(({ key, label, Icon }) => {
          const active = !showBack && section === key;
          return (
            <button key={key} onClick={() => onSection(key)}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg"
                    style={{
                      color: active ? "var(--accent-gold-bright)" : "var(--text-dim)",
                      background: active ? "rgba(201,162,39,0.14)" : "transparent",
                      border: `1px solid ${active ? "rgba(201,162,39,0.35)" : "transparent"}`,
                    }}>
              <Icon className="h-3 w-3" /> {label}
            </button>
          );
        })}
      </nav>
      <span className="text-xs font-mono flex-shrink-0" style={{ color: "var(--text-dim)" }}>v0.2</span>
    </header>
  );
}
