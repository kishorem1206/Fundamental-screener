# frontend/package.json — Beginner Explanation

> **Source file:** `frontend/package.json`

---

## 1. What is this file?

The frontend's `package.json` defines the React application's identity, scripts, and dependencies. This package is responsible for what users see in the browser.

---

## 5. Line-by-line explanation

### Identity

```json
{
  "name": "@stock-screener/web",
  "version": "0.1.0",
  "private": true,
  "type": "module",
```

**`name: "@stock-screener/web"`** — The scoped package name. Note it's "web" not "frontend" — the name reflects what the package IS (a web app), not where it lives in the folder structure.

**`type: "module"`** — All `.js` files use ES Modules. Required for Vite and modern React.

No `"main"` or `"exports"` — the frontend is never imported as a library by other packages.

---

### Scripts

```json
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "typecheck": "tsc --noEmit"
  },
```

**`"dev": "vite"`** — Starts Vite's development server on port 5173 with:
- Hot Module Replacement (HMR): when you save a file, only that component re-renders, not the whole page
- TypeScript/TSX compilation on-the-fly
- Proxy for API calls (via `vite.config.ts`)

**`"build": "tsc && vite build"`** — Production build, two steps:
1. `tsc` — TypeScript type checking (fails the build if there are type errors)
2. `vite build` — Bundle and minify all JS/CSS into static files in `frontend/dist/`

Why `tsc` first? Vite uses esbuild (very fast) for bundling, which intentionally skips TypeScript type checking for speed. Running `tsc` first catches type errors before the bundle is produced.

**`"preview": "vite preview"`** — Serves the production build locally for testing before deploying. Useful to verify the production bundle behaves the same as the dev server.

**`"typecheck": "tsc --noEmit"`** — Type checking only, no output files. Used in CI.

---

### Runtime dependencies

```json
  "dependencies": {
    "@stock-screener/shared": "workspace:*",
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  },
```

**`react: "^19.0.0"`** — The React library itself. Provides `useState`, `useEffect`, `createContext`, hooks, and the virtual DOM system.

**`react-dom: "^19.0.0"`** — React's DOM renderer. Provides `createRoot()` and the code that translates React's virtual DOM into actual browser DOM changes.

Why are these separate packages? React itself is platform-agnostic. `react-dom` is one renderer for browsers. `react-native` would be used instead for mobile apps. Same React code, different renderers.

**`@stock-screener/shared: "workspace:*"`** — Workspace reference to the shared package, for shared types and utilities.

---

### Dev dependencies

```json
  "devDependencies": {
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "@vitejs/plugin-react": "^4.3.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "tailwindcss": "^3.4.0",
    "typescript": "^5.7.0",
    "vite": "^6.0.0"
  }
```

| Package | Purpose |
|---------|---------|
| `@types/react` | TypeScript definitions for React (hooks, event types, etc.) |
| `@types/react-dom` | TypeScript definitions for ReactDOM |
| `@vitejs/plugin-react` | Vite plugin that: enables JSX transform, adds HMR support |
| `autoprefixer` | PostCSS plugin: adds vendor prefixes (`-webkit-`, `-moz-`) to CSS |
| `postcss` | CSS processing pipeline (used by Tailwind) |
| `tailwindcss` | Utility-first CSS framework |
| `typescript` | TypeScript compiler for type checking |
| `vite` | The build tool and dev server |

**Why is `tailwindcss` in devDependencies?** Tailwind generates CSS at build time — in the final production build, the output is plain CSS with no Tailwind dependency. The browser never needs Tailwind itself.

**Why is `vite` in devDependencies?** Same reason — Vite bundles everything during build. The user's browser only sees the output bundle, not Vite itself.

---

## 6. The `tsc && vite build` split explained

```
pnpm build
  ↓
tsc (TypeScript compiler)
  - Reads frontend/tsconfig.json
  - Type checks all .tsx/.ts files
  - If errors: STOP, don't bundle
  - If no errors: exit with 0
  ↓
vite build (esbuild under the hood)
  - Bundles all .tsx/.ts files WITHOUT type checking (fast!)
  - Processes Tailwind CSS via PostCSS
  - Minifies JavaScript and CSS
  - Outputs to frontend/dist/:
    frontend/dist/
    ├── index.html        (updated with asset references)
    ├── assets/
    │   ├── index-abc123.js    (bundled + minified JS)
    │   └── index-def456.css   (bundled + minified CSS)
```

The `&&` means "run vite build ONLY IF tsc succeeds" — type errors block the build.

---

## 7. Dependencies

| Depends on | Why |
|-----------|-----|
| `react` + `react-dom` | The UI framework |
| `vite` | Dev server and bundler |
| `tailwindcss` + `postcss` | CSS utilities |
| `@stock-screener/shared` | Shared types |

| What depends on this file | Why |
|--------------------------|-----|
| `pnpm install` | Installs packages |
| `pnpm dev` (from root) | Runs `"dev": "vite"` |
| `pnpm build` (from root) | Runs `"build": "tsc && vite build"` |

---

## 8. Simple mental model

The frontend `package.json` is like the **supply list for the showroom**:
- **Runtime supplies** (must be present when customers visit): React (the UI framework), react-dom (connects it to browsers), shared types
- **Setup tools** (only needed by the interior designers before opening): Vite (the builder), TypeScript (the quality inspector), Tailwind (the design system), PostCSS (the CSS workshop)
- **Scripts** = daily operating procedures: open for design sessions (`dev`), prepare for grand opening (`build`), final walkthrough before opening (`preview`)
