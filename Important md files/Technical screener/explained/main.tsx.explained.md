# frontend/src/main.tsx — Beginner Explanation

> **Source file:** `frontend/src/main.tsx`

---

## 1. What is this file?

This is the **entry point of the React frontend** — the first file that runs in the browser.

Its job is simple: find the `<div id="root">` element in `index.html`, and render the `<App />` component inside it. That's all. It's a one-time bootstrap file.

---

## 2. Why does this file exist?

React doesn't run directly in HTML. You write React components in TypeScript, Vite compiles them into browser-compatible JavaScript, and then this file "mounts" React onto the actual HTML page.

Think of it as the "ignition switch" — it starts the React engine.

---

## 3. Where does it fit in the project?

```
frontend/index.html
  → <script type="module" src="/src/main.tsx"></script>
        ↓
frontend/src/main.tsx ← THIS FILE runs first
  → finds <div id="root">
  → renders <App /> inside it
        ↓
frontend/src/App.tsx renders the health dashboard
```

---

## 5. Line-by-line explanation

### Lines 1–4: Imports

```typescript
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import { App } from "./App";
```

**`import { StrictMode } from "react"`** — `StrictMode` is a React development helper. It deliberately renders components twice (in development only, not production) to detect side effects and bugs. It doesn't render any visible UI itself.

**`import { createRoot } from "react-dom/client"`** — `createRoot` is React 18+'s way to initialise React. It takes a DOM element and returns a "root" object you call `.render()` on.

**`import "./index.css"`** — Imports the CSS file. Vite processes this and injects the styles into the page. The `@tailwind` directives in `index.css` are expanded into actual Tailwind utility classes.

**`import { App } from "./App"`** — Imports the root App component. Note: no `.tsx` extension needed — Vite's bundler mode resolves it automatically.

---

### Lines 6–8: Find the root element

```typescript
const root = document.getElementById("root");
if (!root) throw new Error("Root element not found");
```

**`document.getElementById("root")`** — Searches the HTML document for an element with `id="root"`. In `frontend/index.html`, we have `<div id="root"></div>`. This line finds it.

**Returns:** The DOM element, or `null` if not found.

**`if (!root) throw new Error("Root element not found")`** — A guard clause. If the `<div id="root">` is missing from `index.html` (maybe someone edited it by mistake), this throws a clear error instead of a cryptic "cannot call render on null" crash later.

---

### Lines 10–13: Mount React

```typescript
createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>
);
```

**`createRoot(root)`** — Initialises React's root renderer attached to the `<div id="root">` element.

**`.render(<StrictMode><App /></StrictMode>)`** — Renders the `App` component (wrapped in `StrictMode`) into the DOM element. React takes over the `<div id="root">` and manages its contents.

**`<StrictMode>`** — Wraps the entire application. Only active in development mode (it's a no-op in production). It:
- Detects components with unsafe lifecycle methods
- Warns about deprecated React features
- Intentionally double-invokes functions to find accidental side effects

**`<App />`** — Renders the App component. This is equivalent to calling `App()` and rendering its returned JSX.

---

## 6. How it works

```
Browser receives index.html
      ↓
Browser sees: <script type="module" src="/src/main.tsx"></script>
      ↓
Vite serves main.tsx (compiled to JavaScript)
      ↓
Browser runs main.tsx:
  1. Imports StrictMode, createRoot, index.css, App component
  2. Finds <div id="root"> in the DOM
  3. createRoot(root) — React takes ownership of the div
  4. .render(<App />) — React renders the App component tree
      ↓
App.tsx renders the health dashboard UI
React's virtual DOM is now in control
      ↓
Any future state changes trigger React re-renders
(no page reloads needed)
```

---

## 7. Dependencies

| Depends on | Why |
|-----------|-----|
| `react` package | `StrictMode` component |
| `react-dom` package | `createRoot` function |
| `./index.css` | Global CSS (Tailwind directives) |
| `./App` | The root application component |
| `frontend/index.html` | Provides the `<div id="root">` mount point |

| What depends on this file | Why |
|--------------------------|-----|
| `frontend/index.html` | References it via `<script src="/src/main.tsx">` |
| Nothing else imports it | It's the entry point; nothing imports entry points |

---

## 8. What happens if I change or remove something?

| Change | Consequence |
|--------|-------------|
| Remove the `if (!root) throw` check | If root is missing, cryptic "Cannot call render on null" error |
| Remove `StrictMode` | Development warnings suppressed; double-render in dev disabled |
| Change to `import { App } from "./App.js"` | Works in Node.js ESM, but Vite doesn't need .js extensions |
| Import wrong root element ID | React mounts to wrong element; page looks broken |

---

## 9. Simple mental model

This file is like a **theatre curtain manager**:

- The theatre (HTML page) has a stage (`<div id="root">`)
- The curtain manager (main.tsx) mounts the show (React + App)
- Once the show starts, the theatre itself doesn't do much — React manages everything on stage

It runs once at startup and then React takes over all subsequent UI changes.
