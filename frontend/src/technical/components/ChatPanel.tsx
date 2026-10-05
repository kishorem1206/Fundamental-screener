import { useState, useEffect, useRef, useCallback } from "react";
import type { ChatSession, ChatMessage } from "../types";
import {
  createChatSession,
  listChatSessions,
  getChatMessages,
  sendChatMessage,
  deleteChatSession,
} from "../api";

// ─── Cinematic mountain background ───────────────────────────────────────────

function MountainBackground() {
  return (
    <svg
      style={{
        position: "absolute",
        inset: 0,
        width: "100%",
        height: "100%",
        pointerEvents: "none",
        zIndex: 0,
      }}
      viewBox="0 0 1440 900"
      preserveAspectRatio="xMidYMax slice"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <radialGradient id="cg-sky" cx="50%" cy="22%" r="55%">
          <stop offset="0%" stopColor="#4F7CFF" stopOpacity="0.09" />
          <stop offset="50%" stopColor="#8B5CF6" stopOpacity="0.05" />
          <stop offset="100%" stopColor="#030712" stopOpacity="0" />
        </radialGradient>
        <radialGradient id="cg-ridge" cx="50%" cy="68%" r="42%">
          <stop offset="0%" stopColor="#8B5CF6" stopOpacity="0.22" />
          <stop offset="55%" stopColor="#4F7CFF" stopOpacity="0.07" />
          <stop offset="100%" stopColor="#030712" stopOpacity="0" />
        </radialGradient>
      </defs>

      {/* Base */}
      <rect width="1440" height="900" fill="#030712" />
      {/* Sky glow */}
      <rect width="1440" height="900" fill="url(#cg-sky)" />
      {/* Ridge glow */}
      <rect width="1440" height="900" fill="url(#cg-ridge)" />

      {/* Stars */}
      {[
        [108, 72, 1.2, 0.45], [255, 44, 0.9, 0.38], [412, 88, 1.4, 0.32],
        [590, 36, 1.0, 0.42], [734, 66, 0.8, 0.48], [880, 28, 1.3, 0.38],
        [1034, 82, 1.1, 0.28], [1182, 52, 0.9, 0.43], [1330, 70, 1.3, 0.33],
        [178, 140, 0.8, 0.28], [522, 122, 1.0, 0.22], [810, 112, 0.9, 0.32],
        [1078, 138, 1.1, 0.28], [340, 58, 0.7, 0.35], [970, 48, 1.0, 0.30],
        [1260, 96, 0.8, 0.38], [66, 110, 0.6, 0.25], [650, 98, 0.9, 0.30],
      ].map(([cx, cy, r, op], i) => (
        <circle key={i} cx={cx} cy={cy} r={r} fill="white" opacity={op} />
      ))}

      {/* Far mountains — blue-purple tint */}
      <path
        d="M0,635 L55,558 L120,592 L195,512 L280,555 L365,468 L445,515 L535,442 L615,488 L705,408 L788,455 L875,385 L958,430 L1045,365 L1135,412 L1222,375 L1308,408 L1440,382 L1440,900 L0,900Z"
        fill="rgba(16,26,65,0.52)"
      />
      {/* Mid mountains — darker */}
      <path
        d="M0,682 L88,622 L175,655 L262,592 L352,632 L442,562 L532,600 L622,530 L712,572 L802,505 L892,548 L982,478 L1072,524 L1162,485 L1252,518 L1342,490 L1440,512 L1440,900 L0,900Z"
        fill="rgba(6,10,26,0.82)"
      />
      {/* Near mountains — nearly black */}
      <path
        d="M0,748 L105,695 L205,718 L308,672 L418,702 L512,655 L615,682 L722,635 L825,668 L925,622 L1025,655 L1132,615 L1235,648 L1332,622 L1440,640 L1440,900 L0,900Z"
        fill="rgba(3,6,15,0.94)"
      />
      {/* Foreground ridge */}
      <path
        d="M0,808 L175,792 L355,800 L535,788 L715,796 L895,782 L1075,792 L1255,784 L1440,788 L1440,900 L0,900Z"
        fill="#030712"
      />
    </svg>
  );
}

// ─── Markdown-lite renderer ────────────────────────────────────────────────────

function renderContent(text: string) {
  const lines = text.split("\n");
  return lines.map((line, i) => {
    const parts = line.split(/(\*\*[^*]+\*\*)/g).map((part, j) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return <strong key={j}>{part.slice(2, -2)}</strong>;
      }
      return part.split(/(`[^`]+`)/g).map((chunk, k) => {
        if (chunk.startsWith("`") && chunk.endsWith("`")) {
          return (
            <code
              key={k}
              className="px-1.5 py-0.5 rounded text-xs font-mono"
              style={{ background: "rgba(79,124,255,0.15)", color: "#93BBFF" }}
            >
              {chunk.slice(1, -1)}
            </code>
          );
        }
        return chunk;
      });
    });

    if (line.startsWith("## "))
      return <p key={i} className="font-semibold mt-3" style={{ color: "#CBD5E1" }}>{line.slice(3)}</p>;
    if (line.startsWith("# "))
      return <p key={i} className="font-bold mt-3 text-base" style={{ color: "#F1F5F9" }}>{line.slice(2)}</p>;
    if (line.match(/^\d+\.\s/) || line.startsWith("- ") || line.startsWith("* "))
      return <li key={i} className="ml-4 list-disc list-inside" style={{ color: "#CBD5E1" }}>{parts}</li>;
    if (line.trim() === "") return <br key={i} />;
    return <p key={i} style={{ color: "#CBD5E1" }}>{parts}</p>;
  });
}

// ─── Message bubble ────────────────────────────────────────────────────────────

function Bubble({ msg }: { msg: ChatMessage }) {
  const isUser = msg.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      {!isUser && (
        <div
          className="shrink-0 w-7 h-7 rounded-full flex items-center justify-center mr-2.5 mt-0.5 text-xs"
          style={{ background: "linear-gradient(135deg, #4F7CFF 0%, #8B5CF6 100%)" }}
        >
          ✦
        </div>
      )}
      <div
        className={`max-w-[78%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
          isUser ? "bubble-user rounded-br-sm" : "bubble-ai rounded-bl-sm"
        }`}
        style={isUser ? { color: "#FFFFFF" } : { color: "#CBD5E1" }}
      >
        {isUser ? (
          <span className="whitespace-pre-wrap">{msg.content}</span>
        ) : (
          <div className="space-y-0.5">{renderContent(msg.content)}</div>
        )}
        {msg.llm_intent_type && msg.llm_intent_type !== "GENERAL" && (
          <span className="mt-1.5 block text-[10px] font-mono tracking-wide"
            style={{ color: "rgba(148,163,184,0.45)" }}>
            intent: {msg.llm_intent_type}
          </span>
        )}
      </div>
    </div>
  );
}

// ─── Session list sidebar item ─────────────────────────────────────────────────

function SessionItem({
  session, active, onSelect, onDelete,
}: {
  session: ChatSession; active: boolean; onSelect: () => void; onDelete: () => void;
}) {
  return (
    <div
      onClick={onSelect}
      className={`group session-item flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer truncate ${active ? "active" : ""}`}
    >
      <div className="flex items-center gap-2 min-w-0 flex-1">
        <span className="text-xs shrink-0" style={{ color: active ? "#4F7CFF" : "rgba(148,163,184,0.4)" }}>◈</span>
        <span className="truncate text-xs font-medium" style={{ color: active ? "#93BBFF" : "#94A3B8" }}>
          {session.title ?? "New chat"}
        </span>
      </div>
      <button
        onClick={(e) => { e.stopPropagation(); onDelete(); }}
        className="ml-2 text-xs opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
        style={{ color: "#64748B" }}
        onMouseEnter={(e) => { (e.currentTarget as HTMLButtonElement).style.color = "#F87171"; }}
        onMouseLeave={(e) => { (e.currentTarget as HTMLButtonElement).style.color = "#64748B"; }}
        title="Delete"
      >
        ×
      </button>
    </div>
  );
}

// ─── Typing indicator ──────────────────────────────────────────────────────────

function TypingIndicator() {
  return (
    <div className="flex justify-start mb-4">
      <div
        className="shrink-0 w-7 h-7 rounded-full flex items-center justify-center mr-2.5 text-xs"
        style={{ background: "linear-gradient(135deg, #4F7CFF 0%, #8B5CF6 100%)" }}
      >
        ✦
      </div>
      <div className="bubble-ai rounded-2xl rounded-bl-sm px-4 py-3.5 flex gap-1.5 items-center">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="typing-dot w-1.5 h-1.5 rounded-full"
            style={{ background: "#4F7CFF", animationDelay: `${i * 0.2}s` }}
          />
        ))}
      </div>
    </div>
  );
}

// ─── Welcome screen ────────────────────────────────────────────────────────────

const EXAMPLE_PROMPTS = [
  { icon: "📉", text: "Show me oversold stocks in Nifty 50" },
  { icon: "💹", text: "What's the current price of INFY?" },
  { icon: "🏢", text: "Give me RELIANCE fundamentals" },
  { icon: "📊", text: "Find large cap stocks near lower Bollinger Band" },
];

function WelcomeScreen({ onPrompt }: { onPrompt: (text: string) => void }) {
  return (
    <div className="flex flex-col items-center justify-center text-center px-8 h-full"
      style={{ position: "relative", zIndex: 1 }}>
      {/* Icon */}
      <div
        className="icon-glow w-14 h-14 rounded-2xl flex items-center justify-center mb-6"
        style={{
          background: "linear-gradient(135deg, rgba(79,124,255,0.18) 0%, rgba(139,92,246,0.15) 100%)",
          border: "1px solid rgba(79,124,255,0.28)",
          fontSize: "26px",
        }}
      >
        📈
      </div>

      {/* Heading */}
      <h2
        className="text-2xl font-semibold mb-2 tracking-tight"
        style={{
          background: "linear-gradient(135deg, #93BBFF 0%, #C4B5FD 100%)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
          backgroundClip: "text",
        }}
      >
        Ask me about Indian stocks
      </h2>

      {/* Subtitle */}
      <p className="text-sm mb-8" style={{ color: "#3D4F72" }}>
        Your AI assistant for NSE · BSE · technicals &amp; market intelligence
      </p>

      {/* Prompt chips */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 max-w-xl w-full">
        {EXAMPLE_PROMPTS.map(({ icon, text }) => (
          <button
            key={text}
            onClick={() => onPrompt(text)}
            className="prompt-chip text-left rounded-xl px-4 py-3 flex items-center gap-3"
          >
            <span className="text-base shrink-0">{icon}</span>
            <span className="text-xs leading-snug" style={{ color: "#94A3B8" }}>{text}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

// ─── Main ChatPanel ────────────────────────────────────────────────────────────

export default function ChatPanel() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollBottom = () => bottomRef.current?.scrollIntoView({ behavior: "smooth" });

  useEffect(() => {
    listChatSessions().then(setSessions).catch(() => setSessions([]));
  }, []);

  useEffect(() => {
    if (!activeId) { setMessages([]); return; }
    getChatMessages(activeId).then(setMessages).catch(() => setMessages([]));
  }, [activeId]);

  useEffect(() => { scrollBottom(); }, [messages, sending]);

  const handleNewSession = async () => {
    const s = await createChatSession();
    setSessions((prev) => [s, ...prev]);
    setActiveId(s.id);
    setMessages([]);
    inputRef.current?.focus();
  };

  const handleSelectSession = useCallback(
    (id: string) => { if (id !== activeId) setActiveId(id); },
    [activeId],
  );

  const handleDeleteSession = async (id: string) => {
    await deleteChatSession(id);
    setSessions((prev) => prev.filter((s) => s.id !== id));
    if (activeId === id) { setActiveId(null); setMessages([]); }
  };

  const handleSend = async (overrideText?: string) => {
    const text = (overrideText ?? input).trim();
    if (!text || sending) return;

    let sessionId = activeId;
    if (!sessionId) {
      const s = await createChatSession();
      setSessions((prev) => [s, ...prev]);
      setActiveId(s.id);
      sessionId = s.id;
    }

    const tempUser: ChatMessage = {
      id: `tmp-${Date.now()}`,
      session_id: sessionId,
      role: "user",
      content: text,
      llm_intent_type: null,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUser]);
    setInput("");
    setSending(true);
    setError(null);

    try {
      const reply = await sendChatMessage(sessionId, text);
      setMessages((prev) => [...prev.filter((m) => m.id !== tempUser.id), tempUser, reply]);
      setSessions((prev) =>
        prev.map((s) => (s.id === sessionId ? { ...s, message_count: s.message_count + 2 } : s)),
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to send message");
      setMessages((prev) => prev.filter((m) => m.id !== tempUser.id));
    } finally {
      setSending(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); void handleSend(); }
  };

  const showWelcome = !activeId && messages.length === 0;

  return (
    /* Outer wrapper: fills the parent (h-full set by App.tsx flex child) */
    <div style={{ display: "flex", height: "100%", overflow: "hidden", background: "var(--bg-base)" }}>

      {/* ── Sidebar (never scrolls) ──────────────────────────────────────── */}
      <aside
        style={{
          width: "224px",
          flexShrink: 0,
          display: "flex",
          flexDirection: "column",
          padding: "12px",
          gap: "12px",
          background: "var(--bg-panel)",
          borderRight: "1px solid var(--border-subtle)",
          overflowY: "auto",
        }}
      >
        <button onClick={handleNewSession} className="btn-new-chat w-full py-2.5 rounded-xl text-white text-xs font-semibold tracking-wide">
          + New chat
        </button>

        <p className="text-[10px] font-semibold tracking-[0.12em] uppercase px-1" style={{ color: "var(--text-dim)" }}>
          Recent chats
        </p>

        <div style={{ flex: 1, overflowY: "auto" }} className="space-y-0.5 -mx-1 px-1">
          {sessions.length === 0 && (
            <p className="text-xs px-3 py-2" style={{ color: "var(--text-dim)" }}>No chats yet</p>
          )}
          {sessions.map((s) => (
            <SessionItem
              key={s.id}
              session={s}
              active={s.id === activeId}
              onSelect={() => handleSelectSession(s.id)}
              onDelete={() => handleDeleteSession(s.id)}
            />
          ))}
        </div>

        <p className="text-[10px] px-1 pb-0.5 leading-relaxed" style={{ color: "var(--text-dim)" }}>
          Powered by GPT-OSS via Ollama
        </p>
      </aside>

      {/* ── Chat area (mountain bg + scrollable messages + fixed input) ──── */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0, position: "relative", overflow: "hidden" }}>

        {/* Mountain background — stays fixed behind scrolling content */}
        <MountainBackground />

        {/* Scrollable messages — sits above the mountain */}
        <div style={{ flex: 1, overflowY: "auto", position: "relative", zIndex: 1 }}>
          {showWelcome ? (
            <div style={{ height: "100%", display: "flex" }}>
              <WelcomeScreen onPrompt={(text) => void handleSend(text)} />
            </div>
          ) : (
            <div className="px-6 py-5 max-w-3xl mx-auto">
              {messages.map((m) => <Bubble key={m.id} msg={m} />)}
              {sending && <TypingIndicator />}
              {error && (
                <div
                  className="text-xs text-center py-2 px-4 rounded-lg mt-2"
                  style={{
                    background: "rgba(248,113,113,0.08)",
                    border: "1px solid rgba(248,113,113,0.2)",
                    color: "#F87171",
                  }}
                >
                  {error}
                </div>
              )}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        {/* Input area — always locked to bottom */}
        <div
          style={{
            flexShrink: 0,
            padding: "16px 20px",
            borderTop: "1px solid var(--border-subtle)",
            background: "rgba(3,7,18,0.82)",
            backdropFilter: "blur(14px)",
            position: "relative",
            zIndex: 2,
          }}
        >
          <div className="max-w-3xl mx-auto">
            <div className="input-glass rounded-2xl px-4 py-3 flex gap-3 items-end">
              <textarea
                ref={inputRef}
                rows={1}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about stocks… (Enter to send, Shift+Enter for newline)"
                className="flex-1 resize-none bg-transparent text-sm outline-none max-h-32 overflow-y-auto"
                style={{ color: "var(--text-primary)", caretColor: "var(--accent-blue)" }}
                onInput={(e) => {
                  const t = e.currentTarget;
                  t.style.height = "auto";
                  t.style.height = `${Math.min(t.scrollHeight, 128)}px`;
                }}
              />
              <button
                onClick={() => void handleSend()}
                disabled={!input.trim() || sending}
                className="btn-send shrink-0 px-4 py-2 rounded-xl text-white text-sm font-semibold"
              >
                {sending ? "…" : "Send"}
              </button>
            </div>
            <p className="text-[10px] text-center mt-2 tracking-wide" style={{ color: "var(--text-dim)" }}>
              Read-only — no order execution
            </p>
          </div>
        </div>

      </div>
    </div>
  );
}
