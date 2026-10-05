# frontend/src/App.tsx — Beginner Explanation

> **Source file:** `frontend/src/App.tsx`

---

## 1. What is this file?

This is the **main React component** of the frontend — what the user actually sees in their browser.

Currently it renders the **System Health Dashboard**: a page that calls the backend's `/health` API and shows a table of all service statuses (database, Redis, MCP providers, LLM).

This is the only visible page in Phase 1. In later phases, this will be replaced or expanded with the actual stock screener interface.

---

## 2. Why does this file exist?

Every React application has a root component — one top-level component that renders everything else. This is that root component. It's the starting point of the visual interface.

In React, your UI is made up of **components** — reusable pieces of UI written as TypeScript functions that return HTML-like code (JSX). `App` is the root component; it will eventually contain or route to all other components.

---

## 3. Where does it fit in the project?

```
frontend/index.html
  → <div id="root"></div>
        ↓
frontend/src/main.tsx
  → createRoot(root).render(<App />)
        ↓
frontend/src/App.tsx ← THIS FILE
  → renders the health dashboard
  → calls /api/health on load
```

---

## 4. Technology involved

- **React** — A JavaScript library for building user interfaces using components
- **TypeScript** — Type-safe JavaScript. The `.tsx` extension means TypeScript + JSX.
- **JSX** — A syntax that lets you write HTML-like code inside JavaScript/TypeScript files. Browsers don't understand JSX; Vite compiles it to regular JavaScript.
- **React hooks** — Functions that let you add state and lifecycle behaviour to components. Used here: `useState`, `useEffect`.
- **Tailwind CSS** — A CSS utility library. Instead of writing `.my-class { color: green }`, you use class names like `text-green-800` directly in JSX.
- **`fetch()`** — The browser API for making HTTP requests.

---

## 5. Line-by-line explanation

### Lines 1: Import React hooks

```typescript
import { useEffect, useState } from "react";
```

**`useState`** — A React hook that gives a component its own **state** (data that the component tracks and that causes re-renders when changed).

**`useEffect`** — A React hook that runs code in response to events (component mounting, state changes, etc.). Used here to fetch health data when the component first loads.

---

### Lines 3–8: TypeScript interfaces

```typescript
interface HealthData {
  status: "ok" | "degraded" | "error";
  timestamp: string;
  uptime: number;
  services: Record<string, { status: string; detail?: string; provider?: string }>;
}
```

**`interface HealthData`** — Defines the TypeScript type of the data returned from `/api/health`. This matches what `backend/src/routes/health.ts` sends back.

**Why define this here?** This is the frontend's "contract" with the backend API. If the backend changes its response shape, TypeScript will flag the mismatch here.

---

### Lines 10–16: Status colour mapping

```typescript
const STATUS_COLOR: Record<string, string> = {
  ok: "bg-green-100 text-green-800",
  not_configured: "bg-yellow-100 text-yellow-800",
  degraded: "bg-yellow-100 text-yellow-800",
  error: "bg-red-100 text-red-800",
  unavailable: "bg-gray-100 text-gray-600",
};
```

**`Record<string, string>`** — A dictionary mapping status strings to Tailwind CSS class strings.

This maps each service status to the appropriate visual styling:
- `"ok"` → green background, green text
- `"not_configured"` → yellow (warning, not error)
- `"degraded"` → yellow
- `"error"` → red background, red text
- `"unavailable"` → grey (not critical)

Used in the JSX to add colour to the status badges.

---

### Lines 18–22: Component function and state

```typescript
export function App() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
```

**`export function App()`** — A React component is just a TypeScript function that returns JSX. `export` makes it importable in `main.tsx`.

**`useState<HealthData | null>(null)`** — Creates a state variable `health` with initial value `null`. Returns an array: `[currentValue, setterFunction]`. When `setHealth(data)` is called, React re-renders the component with the new value.

The three state variables:
- **`health`** — The fetched health data (null until loaded)
- **`loading`** — Whether the request is in progress (starts `true`)
- **`err`** — Any error message (null if no error)

**State vs regular variables:** Regular variables reset every render. State persists across renders and triggers re-renders when changed. This is fundamental to React.

---

### Lines 24–34: The data fetch

```typescript
  useEffect(() => {
    fetch("/api/health")
      .then((r) => r.json() as Promise<HealthData>)
      .then((data) => {
        setHealth(data);
        setLoading(false);
      })
      .catch((e: Error) => {
        setErr(e.message);
        setLoading(false);
      });
  }, []);
```

**`useEffect(() => { ... }, [])`** — Runs the function inside it after the component first renders. The empty array `[]` means "run this only once, when the component mounts" (not on every re-render).

**`fetch("/api/health")`** — Makes an HTTP GET request to `/api/health`. Since the Vite dev server has a proxy configured, this gets rewritten to `http://localhost:3001/health`.

**`.then((r) => r.json() as Promise<HealthData>)`** — When the response arrives, parse it as JSON. `as Promise<HealthData>` is a TypeScript assertion telling the compiler "this JSON will match the HealthData shape."

**`.then((data) => { setHealth(data); setLoading(false); })`** — When JSON parsing is done, update state: store the data and mark loading as complete.

**`.catch((e: Error) => { setErr(e.message); setLoading(false); })`** — If anything fails (network error, server down), store the error message and stop the loading indicator.

**Why `.then()` chains?** `fetch()` is asynchronous — it returns a Promise. `.then()` registers a callback that runs when the Promise resolves. This is the older Promise-chain style (vs. `async/await`). Both work the same way.

---

### Lines 36–101: The JSX (what renders on screen)

```typescript
  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 font-mono">
```

**`return (...)` in a React component** — Returns JSX, which React renders as HTML.

**`className`** — In JSX, HTML's `class` attribute is written as `className` (because `class` is a reserved word in JavaScript).

**Tailwind classes:**
- `min-h-screen` — At least 100% of the viewport height
- `bg-gray-950` — Very dark grey background (#0c0a09)
- `text-gray-100` — Very light grey text
- `font-mono` — Monospace font (the terminal/coding aesthetic)

---

```typescript
      <header className="border-b border-gray-800 px-6 py-4">
        <h1 className="text-xl font-semibold tracking-tight">
          Stock Screener <span className="text-gray-500 text-sm font-normal">v0.1 · India</span>
        </h1>
      </header>
```

A fixed header with the app name. The `<span>` inside `<h1>` renders "v0.1 · India" in smaller grey text.

---

```typescript
          {loading && <p className="text-gray-500 text-sm">Checking systems…</p>}
```

**`{loading && <p>...</p>}`** — Conditional rendering. In JSX, `{expression}` executes JavaScript inside the HTML. `loading && <p>...</p>` means "if loading is true, render this paragraph; if false, render nothing."

---

```typescript
          {err && (
            <div className="rounded-lg border border-red-800 bg-red-950 px-4 py-3 text-sm text-red-300">
              API unreachable: {err}
            </div>
          )}
```

Shows a red error box if `err` is non-null (the API couldn't be reached).

---

```typescript
          {health && (
            <div className="space-y-3">
              <div className="flex items-center gap-3 text-sm">
                <span
                  className={`inline-flex items-center rounded px-2 py-0.5 text-xs font-medium uppercase ${STATUS_COLOR[health.status] ?? "bg-gray-700 text-gray-300"}`}
                >
                  {health.status}
                </span>
                <span className="text-gray-500">
                  uptime {Math.floor(health.uptime)}s · {health.timestamp}
                </span>
              </div>
```

If `health` is non-null (data loaded successfully), show the status badge and uptime.

**Template literal in `className`:** `` `...${STATUS_COLOR[health.status] ?? "bg-gray-700 text-gray-300"}` `` — Inserts the CSS class name for the current status. If the status doesn't match any known status, falls back to grey.

---

```typescript
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-gray-500 text-xs uppercase">
                    <th className="text-left py-1 font-medium">Service</th>
                    <th className="text-left py-1 font-medium">Status</th>
                    <th className="text-left py-1 font-medium">Detail</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                  {Object.entries(health.services).map(([name, svc]) => (
                    <tr key={name}>
```

**`Object.entries(health.services)`** — Converts `{ database: {...}, redis: {...}, ... }` into an array of `[key, value]` pairs: `[["database", {...}], ["redis", {...}], ...]`.

**`.map(([name, svc]) => <tr>...</tr>)`** — For each pair, render a table row. `[name, svc]` destructures the pair.

**`key={name}`** — React requires a unique `key` prop when rendering lists. This helps React efficiently update only changed items. Without `key`, React shows a warning and may behave incorrectly.

---

```typescript
                      <td className="py-2 pr-4 text-gray-300">{name.replace(/_/g, " ")}</td>
```

**`name.replace(/_/g, " ")`** — Replaces underscores with spaces: `"kite_mcp"` → `"kite mcp"`. The `/g` flag means "replace ALL occurrences" (not just the first).

---

```typescript
                        <span
                          className={`inline-flex items-center rounded px-2 py-0.5 text-xs font-medium ${STATUS_COLOR[svc.status] ?? "bg-gray-700 text-gray-300"}`}
                        >
                          {svc.status}
                        </span>
```

Same colour badge pattern as the overall status, applied to each individual service.

---

```typescript
                      <td className="py-2 text-gray-500 text-xs">
                        {svc.detail ?? svc.provider ?? "—"}
                      </td>
```

Shows error detail if available, otherwise shows the provider name (for the LLM service), otherwise shows `"—"` (em dash) to indicate no detail.

---

## 6. How it works — rendering lifecycle

```
Browser loads http://localhost:5173
      ↓
index.html loads, Vite serves main.tsx
      ↓
main.tsx renders <App />
      ↓
App() function runs:
  - useState initializes: health=null, loading=true, err=null
  - Returns JSX with "Checking systems..." text visible
      ↓
useEffect fires after first render:
  - fetch("/api/health") starts
      ↓
Backend responds with health JSON
      ↓
.then() runs:
  - setHealth(data) → health = { status, services, ... }
  - setLoading(false) → loading = false
      ↓
React re-renders App() with new state:
  - loading is false → "Checking systems..." disappears
  - health is not null → table renders
  - Table shows database: ok, redis: ok, kite_mcp: ok, llm: not_configured
```

---

## 7. Dependencies

| Depends on | Why |
|-----------|-----|
| `react` package | `useState`, `useEffect` hooks |
| Tailwind CSS | All styling |
| `/api/health` endpoint | Data source |

| What depends on this file | Why |
|--------------------------|-----|
| `frontend/src/main.tsx` | Renders `<App />` |

---

## 8. What happens if I change or remove something?

| Change | Consequence |
|--------|-------------|
| Remove `[]` from `useEffect(fn, [])` | Fetch runs after every re-render → infinite loop |
| Remove `key={name}` from table rows | React warning; potential UI bugs when data changes |
| Change fetch URL to `/health` (no `/api/`) | Goes directly to Vite's dev server, not proxied to backend |
| Add a new status to STATUS_COLOR | New statuses get coloured instead of falling back to grey |

---

## 9. Beginner concepts to learn

- **What is React?** — A library for building UI from composable components
- **What is JSX?** — HTML-like syntax in JavaScript/TypeScript files, compiled to `React.createElement()` calls
- **What is `useState`?** — A React hook for storing data that should trigger UI updates when changed
- **What is `useEffect`?** — A React hook for running code in response to component lifecycle events
- **What is a component?** — A function that takes props and returns JSX (the building block of React UIs)
- **What is conditional rendering?** — Showing different UI based on conditions (`&&` operator, ternary)
- **What is `.map()`?** — Transforming an array into another array (often used to render lists)

---

## 10. Simple mental model

A React component is like a **vending machine display**:

- It has **state** (internal data): which items are available, current prices
- It **renders** (displays) based on its state: if no item is selected, show the selection screen
- When state changes (you insert money), it **re-renders** (updates the display)

In `App.tsx`:
- State: `{ health: null, loading: true, err: null }`
- Render #1: Shows "Checking systems..." (loading is true)
- Fetch completes → state changes → `{ health: { ... }, loading: false }`
- Re-render: Shows the health table
