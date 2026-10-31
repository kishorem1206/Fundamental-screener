// Full-screen explanation of the CANSLIM page. The bands here mirror backend/app/canslim/score.py.
import { useEffect, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { ChevronLeft, ChevronRight, X } from "lucide-react";

const LETTERS: { letter: string; name: string; asks: string; why: string; bands: [string, string][]; note?: string }[] = [
  { letter: "C", name: "Current earnings", asks: "Is profit in the latest quarter well above the same quarter last year?",
    why: "Big winners usually show a jump in earnings before their biggest price moves.",
    bands: [["Up 50% or more", "100"], ["Up 25% or more", "85"], ["Up 15% or more", "60"], ["Up by less", "35"], ["Down", "15"]],
    note: "Sales up 20% or more adds 5 to a score of 60 or above. Sales falling takes off 5. Strong sales never rescue weak profit. A company that has just turned profitable scores 60; a loss in both quarters scores 15." },
  { letter: "A", name: "Annual earnings", asks: "Has profit compounded well over several years?",
    why: "It separates lasting growth from one good quarter.",
    bands: [["25% a year or more, with ROE of 17%+", "100"], ["25% a year or more", "85"], ["15% a year or more", "60"], ["Lower growth", "35"], ["Profit fell", "15"]],
    note: "Uses three years, or five if three cannot be read. A loss in the latest year scores 15. Profitable now after an earlier loss scores 50, because no growth rate can be worked out." },
  { letter: "N", name: "New highs", asks: "Is the share near its 52-week high?",
    why: "O'Neil's point is that leaders often look expensive and keep rising. Stocks near their lows tend to stay weak.",
    bands: [["Within 5% of the high", "100"], ["Within 15%", "80"], ["Within 25%", "50"], ["Within 40%", "25"], ["Further below", "10"]],
    note: "The other half of N, a new product or new management, has no data feed, so it is not scored." },
  { letter: "S", name: "Supply and demand", asks: "Is more volume coming in than usual?",
    why: "A rise on heavy volume suggests large buyers are behind it.",
    bands: [["10-day volume 1.5x the 50-day", "100"], ["1.25x", "85"], ["1.0x", "60"], ["Below the average", "30"]],
    note: "This reads volume only. It does not know whether the volume came on up days or down days." },
  { letter: "L", name: "Leader or laggard", asks: "Has the share beaten the other stocks?",
    why: "O'Neil bought the leaders of a move, not the cheap laggards.",
    bands: [["RS Rating 80 or above", "a leader"], ["The score", "equals the RS Rating, 1 to 99"]],
    note: "The RS Rating ranks every stock on its return over three, six and twelve months, with the latest three months counted twice. A stock with under a year of prices has no rating." },
  { letter: "I", name: "Institutional sponsorship", asks: "Do FIIs and DIIs own a healthy share?",
    why: "Institutions move prices. Too few means nobody is backing it; too many means few buyers are left.",
    bands: [["20% to 70% held", "100"], ["10% to 20%", "70"], ["70% to 90%, crowded", "60"], ["5% to 10%", "40"], ["Under 5% or over 90%", "20"]] },
  { letter: "M", name: "Market direction", asks: "Is the overall market in an uptrend?",
    why: "Most stocks follow the market, so O'Neil avoided new buying in a correction.",
    bands: [["Nifty 50 above its 50- and 200-day averages, 50-day above 200-day", "100"], ["Above the 200-day", "60"], ["Above the 50-day only", "40"], ["Below both", "10"]],
    note: "This is the same for every stock, so a weak market lowers every CANSLIM score together." },
];

const COLUMNS: [string, string][] = [
  ["CANSLIM", "The plain average of the letters that could be read. A stock needs at least 4 of the 7, otherwise it shows no score."],
  ["Peer quality", "Where the stock's Quality Score ranks among its peers: its basic industry, or its industry when that is too small. 90 means better than about 90% of them."],
  ["Combined", "60% CANSLIM + 40% peer quality. CANSLIM looks at growth and momentum; peer quality adds how good the business is. If one is missing, the other stands alone and the stock's detail says so."],
];

const STEPS = [
  "Check the market line first. If M says correction, O'Neil's rule is to hold back from new buying.",
  "Use the letter buttons to keep only stocks strong on C, A, N, S and L. Few stocks pass all of them, and that is the point.",
  "Click a stock to see the numbers behind each letter. A high score can rest on one unusual quarter.",
  "Run a full analysis on the ones that matter. CANSLIM finds candidates; it does not judge the business.",
  "If you buy, O'Neil's rule is a stop-loss 7-8% below the purchase price, never moved lower.",
];

// Paper colours are fixed on purpose: the book reads the same in any theme
const PAPER = "#f7f1e3", INK = "#2e2819", SOFT = "#6a5f49", RULE = "#d8ccb2", GOLD = "#9a7416";
const TITLE_FONT = "Fraunces, Georgia, serif";
const BODY_FONT = "Georgia, 'Times New Roman', serif";

function Box({ title, children }: { title?: string; children: ReactNode }) {
  return (
    <div style={{ border: `1px solid ${RULE}`, borderRadius: 8, padding: "12px 14px", marginBottom: 12, background: "rgba(255,255,255,0.45)" }}>
      {title && <div style={{ fontFamily: TITLE_FONT, fontWeight: 600, fontSize: 14, color: INK, marginBottom: 6 }}>{title}</div>}
      {children}
    </div>
  );
}

function Heading({ eyebrow, title }: { eyebrow: string; title: string }) {
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ fontFamily: "Inter, sans-serif", fontSize: 10, letterSpacing: "0.14em", textTransform: "uppercase", color: GOLD, fontWeight: 600 }}>{eyebrow}</div>
      <h2 style={{ fontFamily: TITLE_FONT, fontSize: 24, lineHeight: 1.2, fontWeight: 600, color: INK }}>{title}</h2>
    </div>
  );
}

function Bands({ rows }: { rows: [string, string][] }) {
  return (
    <div style={{ border: `1px solid ${RULE}`, borderRadius: 6, overflow: "hidden" }}>
      <div style={{ display: "flex", justifyContent: "space-between", padding: "4px 10px", background: "rgba(154,116,22,0.12)", fontFamily: "Inter, sans-serif", fontSize: 10, letterSpacing: "0.08em", textTransform: "uppercase", color: SOFT }}>
        <span>Test</span><span>Score</span>
      </div>
      {rows.map(([test, score]) => (
        <div key={test} style={{ display: "flex", justifyContent: "space-between", gap: 12, padding: "5px 10px", borderTop: `1px solid ${RULE}`, fontSize: 13, color: INK }}>
          <span>{test}</span><b style={{ fontFamily: "Inter, sans-serif", fontSize: 12, whiteSpace: "nowrap" }}>{score}</b>
        </div>
      ))}
    </div>
  );
}

function pages(go: (page: number) => void): { label: string; node: ReactNode }[] {
  const first = 2; // the first letter's page, counting from 0
  return [
    { label: "Introduction", node: <>
      <Heading eyebrow="CANSLIM" title="Understanding the CANSLIM screen" />
      <p style={{ marginBottom: 10 }}>CANSLIM is William O'Neil's method for finding growth stocks before their biggest moves. He studied the best-performing shares of many years and found they tended to share seven traits. Each letter stands for one.</p>
      <Box title="How it is scored here">Every stock gets 0 to 100 on each letter, from data already in this app. A letter with no data is left out, never counted as zero.</Box>
      <Box title="Reading the colours">
        <div><b style={{ color: "#2f8a78" }}>70 and above</b> is strong</div>
        <div><b style={{ color: GOLD }}>50 to 69</b> is middling</div>
        <div><b style={{ color: "#bb4a31" }}>Below 50</b> is weak</div>
      </Box>
      <Box>A separate read. It does not change your Quality Score, classifications or any other score.</Box>
    </> },
    { label: "Contents", node: <>
      <Heading eyebrow="Contents" title="In this book" />
      <div style={{ border: `1px solid ${RULE}`, borderRadius: 8, overflow: "hidden" }}>
        {LETTERS.map((l, i) => (
          <button key={l.letter} onClick={() => go(first + i)} className="w-full text-left" style={{ display: "flex", gap: 10, padding: "6px 12px", borderTop: i ? `1px solid ${RULE}` : undefined, color: INK }}>
            <b style={{ fontFamily: TITLE_FONT, color: GOLD, width: 16 }}>{l.letter}</b><span style={{ flex: 1 }}>{l.name}</span><span style={{ color: SOFT }}>{first + i + 1}</span>
          </button>
        ))}
        {[["The three totals", 9], ["How to use it", 10], ["What it does not do", 11]].map(([name, page]) => (
          <button key={name} onClick={() => go(page as number)} className="w-full text-left" style={{ display: "flex", gap: 10, padding: "6px 12px", borderTop: `1px solid ${RULE}`, color: INK }}>
            <span style={{ width: 16 }} /><span style={{ flex: 1 }}>{name}</span><span style={{ color: SOFT }}>{(page as number) + 1}</span>
          </button>
        ))}
      </div>
    </> },
    ...LETTERS.map((l) => ({ label: l.name, node: <>
      <Heading eyebrow={`The letter ${l.letter}`} title={l.name} />
      <Box title="The question">{l.asks}</Box>
      <Box title="Why it matters">{l.why}</Box>
      <Bands rows={l.bands} />
      {l.note && <p style={{ marginTop: 10, fontSize: 12.5, color: SOFT }}>{l.note}</p>}
    </> })),
    { label: "The three totals", node: <>
      <Heading eyebrow="Putting it together" title="The three totals" />
      {COLUMNS.map(([name, text]) => <Box key={name} title={name}>{text}</Box>)}
    </> },
    { label: "How to use it", node: <>
      <Heading eyebrow="In practice" title="How to use it" />
      {STEPS.map((step, i) => <Box key={step} title={`Step ${i + 1}`}>{step}</Box>)}
    </> },
    { label: "What it does not do", node: <>
      <Heading eyebrow="Limits" title="What it does not do" />
      <Box title="No timing">It does not spot chart patterns such as a cup and handle, or tell you when to buy.</Box>
      <Box title="No balance sheet">It does not look at debt, cash flow or valuation, which is why peer quality is blended in.</Box>
      <Box title="Only as fresh as the data">Scores use the last quarter stored in the app and update once a day. During results season a newly reported quarter can take time to appear.</Box>
      <p style={{ fontSize: 12, color: SOFT }}>Sources: William O'Neil's CANSLIM method, your CANSLIM notes, and InCred Money's guide to CANSLIM in India.</p>
    </> },
  ];
}

export default function CanslimGuide({ onClose }: { onClose: () => void }) {
  const [wide, setWide] = useState(() => window.matchMedia("(min-width: 1000px)").matches);
  const [page, setPage] = useState(0);
  const step = wide ? 2 : 1;
  const go = (p: number) => setPage(wide ? p - (p % 2) : p);
  const book = pages(go);
  const last = book.length - 1;
  const left = wide ? page - (page % 2) : page;
  const back = () => setPage((p) => Math.max(0, p - step));
  const next = () => setPage((p) => Math.min(last, p + step));

  useEffect(() => {
    const media = window.matchMedia("(min-width: 1000px)");
    const onChange = () => setWide(media.matches);
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
      if (e.key === "ArrowLeft") back();
      if (e.key === "ArrowRight") next();
    };
    const overflow = document.body.style.overflow;
    media.addEventListener("change", onChange);
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      media.removeEventListener("change", onChange);
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = overflow;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [onClose, step]);

  const sheet = (index: number, side: "left" | "right" | "single") => (
    <div key={index} style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column", background: PAPER, color: INK, fontFamily: BODY_FONT, fontSize: 14, lineHeight: 1.55,
      boxShadow: side === "left" ? "inset -18px 0 22px -18px rgba(70,52,20,0.35)" : side === "right" ? "inset 18px 0 22px -18px rgba(70,52,20,0.35)" : undefined }}>
      <div style={{ flex: 1, overflowY: "auto", padding: "26px 30px 8px" }}>{book[index]?.node}</div>
      <div style={{ padding: "8px 30px 14px", display: "flex", justifyContent: "space-between", fontSize: 11, color: SOFT, borderTop: `1px solid ${RULE}`, margin: "0 16px" }}>
        <span>{book[index]?.label}</span><span>{index + 1}</span>
      </div>
    </div>
  );
  const control = (disabled: boolean) => ({ color: "#f7f1e3", border: "1px solid rgba(247,241,227,0.4)", opacity: disabled ? 0.35 : 1 });

  // On document.body: the page's fade-in animation would otherwise trap `fixed` inside it
  return createPortal(
    <div role="dialog" aria-modal="true" aria-label="How CANSLIM works" onClick={onClose} className="fixed inset-0 flex items-center justify-center p-5"
         style={{ zIndex: 100, background: "rgba(5,10,22,0.55)", backdropFilter: "blur(9px)", WebkitBackdropFilter: "blur(9px)" }}>
      <div onClick={(e) => e.stopPropagation()} style={{ width: "min(1120px, 100%)", height: "min(740px, 100%)", display: "flex", flexDirection: "column", gap: 10 }}>
        <div style={{ flex: 1, minHeight: 0, display: "flex", borderRadius: 10, overflow: "hidden", border: "6px solid #5b3d1e", boxShadow: "0 24px 70px rgba(0,0,0,0.55)" }}>
          {wide ? <>{sheet(left, "left")}<div style={{ width: 2, background: "#b9a981" }} />{left + 1 <= last ? sheet(left + 1, "right") : <div style={{ flex: 1, background: PAPER }} />}</> : sheet(left, "single")}
        </div>
        <div className="flex items-center justify-between text-xs">
          <button onClick={back} disabled={left === 0} className="flex items-center gap-1 px-3 py-1.5 rounded-lg" style={control(left === 0)}><ChevronLeft size={14} /> Previous</button>
          <span style={{ color: "#f7f1e3" }}>{wide ? `Pages ${left + 1}-${Math.min(left + 2, last + 1)}` : `Page ${left + 1}`} of {last + 1}</span>
          <div className="flex items-center gap-2">
            <button onClick={next} disabled={left + step > last} className="flex items-center gap-1 px-3 py-1.5 rounded-lg" style={control(left + step > last)}>Next <ChevronRight size={14} /></button>
            <button onClick={onClose} aria-label="Close" className="flex items-center gap-1 px-3 py-1.5 rounded-lg" style={control(false)}><X size={14} /> Close</button>
          </div>
        </div>
      </div>
    </div>,
    document.body,
  );
}
