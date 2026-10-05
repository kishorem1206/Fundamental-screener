# frontend/tsconfig.json — Beginner Explanation

> **Source file:** `frontend/tsconfig.json`

---

## 1. What is this file?

This is the **TypeScript configuration for the frontend package**. It inherits from the root `tsconfig.json` but adds settings specific to React and browser development.

The frontend needs different TypeScript settings from the backend because:
- The backend runs in Node.js (server environment)
- The frontend runs in the browser (different APIs: `document`, `window`, `fetch`, etc.)
- The frontend uses React's JSX syntax (`<App />` → `React.createElement(App, ...)`)

---

## 5. Line-by-line explanation

### Inheritance

```json
"extends": "../tsconfig.json",
```

Inherits all strict settings from the root: `strictNullChecks`, `exactOptionalPropertyTypes`, `noUncheckedIndexedAccess`, etc.

---

### Target and library

```json
"target": "ES2020",
"lib": ["ES2020", "DOM", "DOM.Iterable"],
```

**`target: "ES2020"`** — TypeScript compiles to ES2020 JavaScript. The root sets `ES2022` (for Node.js, which is always up-to-date). The frontend targets `ES2020` because some older but still-supported browsers might not support ES2022 features. Vite's esbuild further transpiles/polyfills as needed.

**`lib: ["ES2020", "DOM", "DOM.Iterable"]`** — The type libraries TypeScript uses:
- `ES2020` — Core JavaScript types (`Promise`, `Array`, `Map`, etc.)
- `DOM` — Browser API types: `document`, `window`, `HTMLElement`, `fetch`, `MouseEvent`, etc. Without this, TypeScript doesn't know what `document.getElementById()` is.
- `DOM.Iterable` — Makes DOM collections iterable: `for (const el of document.querySelectorAll("div"))` without this would error because `NodeList` wouldn't be iterable.

The backend does NOT include `DOM` because Node.js doesn't have `document` or `window`.

---

### Module system

```json
"module": "ESNext",
"moduleResolution": "Bundler",
```

**`module: "ESNext"`** — Generates modern ESM syntax. Vite's bundler handles the final transformation.

**`moduleResolution: "Bundler"`** — A TypeScript 5.0+ mode that tells TypeScript to resolve imports the way Vite (a bundler) does:
- Does NOT require `.js` extensions in imports (bundlers handle this)
- Supports `package.json` `exports` fields
- More relaxed than `NodeNext`

This is why frontend code can write `import { App } from "./App"` (no `.js`), while backend code must write `import { App } from "./App.js"`.

---

### JSX support

```json
"jsx": "react-jsx",
```

**`jsx: "react-jsx"`** — Transforms JSX syntax in `.tsx` files.

`react-jsx` uses the modern automatic JSX transform (React 17+). Instead of requiring `import React from "react"` at the top of every file, the transform is injected automatically.

```tsx
// What you write:
function App() {
  return <div className="app">Hello</div>;
}

// What TypeScript generates (simplified):
import { jsx as _jsx } from "react/jsx-runtime";
function App() {
  return _jsx("div", { className: "app", children: "Hello" });
}
```

Without `"jsx": "react-jsx"`, TypeScript would leave JSX unchanged and the browser would crash trying to parse `<div>` as JavaScript.

---

### Directory settings

```json
"rootDir": "./src",
"outDir": "./dist",
```

Same pattern as other packages. But in practice, Vite doesn't use the TypeScript compiler to produce the final bundle — it uses esbuild. The `tsc` in `"build": "tsc && vite build"` only runs for type-checking. Vite does the actual bundling.

---

### Path alias

```json
"paths": {
  "@stock-screener/shared": ["../shared/src/index.ts"]
}
```

Same as the backend — allows `import { Exchange } from "@stock-screener/shared"` and TypeScript resolves it to the shared source. Vite also reads this via `vite.config.ts`'s `resolve.alias` to handle the import at runtime in the dev server and bundle.

---

### Include/exclude

```json
"include": ["src/**/*"],
"exclude": ["node_modules", "dist", "src/**/*.js"]
```

**`"src/**/*.js"`** is explicitly excluded — if any `.js` files exist in `src/` (e.g., a JavaScript config file someone put there), TypeScript won't try to type-check them.

---

## 6. Frontend vs backend tsconfig differences

| Setting | Frontend | Backend | Why different |
|---------|----------|---------|---------------|
| `target` | `ES2020` | `ES2022` (inherited) | Browser compat vs Node.js |
| `lib` | `ES2020, DOM, DOM.Iterable` | Not set (Node types only) | Browser has DOM, Node.js doesn't |
| `module` | `ESNext` | `NodeNext` | Bundler vs Node.js resolution |
| `moduleResolution` | `Bundler` | `NodeNext` | Vite bundler vs Node.js resolution |
| `jsx` | `react-jsx` | Not set | Frontend has React, backend doesn't |

---

## 7. Dependencies

| Depends on | Why |
|-----------|-----|
| Root `tsconfig.json` | Inherits strict settings |

| What depends on this file | Why |
|--------------------------|-----|
| `tsc --noEmit` in `typecheck` script | Type checking |
| Vite via `vite.config.ts` | Reads for JSX transform config |
| IDE / VS Code | Frontend autocomplete and type checking |

---

## 8. Simple mental model

The frontend tsconfig is like **rules for an office that serves customers in a browser storefront** (vs the backend, which is a back-office on a server):
- Customer-facing offices need to know about the "customer environment" (DOM: windows, buttons, forms)
- The server back-office doesn't need to know about customer-facing furniture
- The storefront speaks ESNext (modern browser language)
- The back-office speaks NodeNext (server language with explicit file extensions)
- Both follow the same strict company-wide rules (from root tsconfig)
