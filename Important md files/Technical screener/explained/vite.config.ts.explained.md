# frontend/vite.config.ts — Beginner Explanation

> **Source file:** `frontend/vite.config.ts`

---

## 1. What is this file?

This is the **Vite configuration file** for the frontend.

Vite is the build tool and development server for the frontend. This file tells Vite: which plugins to use, how to resolve imports, which port to run on, and how to proxy API requests to the backend.

---

## 2. Why does this file exist?

Without configuration, Vite uses defaults (port 5173, no proxy, no plugins). But we need:
1. The React plugin — to understand JSX and React-specific features
2. An alias for `@stock-screener/shared` — so imports from the shared package resolve to source files directly (faster, no need to build shared first)
3. A proxy — so `/api/health` in the browser goes to `http://localhost:3001/health` (the backend)

---

## 3. Where does it fit in the project?

```
pnpm dev (in frontend/)
  → "vite"
  → Vite reads vite.config.ts
  → Starts dev server on port 5173
  → Handles all import resolution, JSX compilation, hot reloading
  → Proxies /api/* requests to localhost:3001
```

---

## 5. Line-by-line explanation

### Lines 1–3: Imports

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
```

**`defineConfig`** — A Vite helper function that just returns your config object as-is but provides TypeScript type checking. Without it, you'd have to add `/** @type {import('vite').UserConfig} */` comment instead.

**`react from "@vitejs/plugin-react"`** — The official Vite plugin for React. It:
- Transforms JSX into `React.createElement()` calls
- Enables Fast Refresh (hot reload that preserves React state when you save a file)

**`path from "path"`** — Node.js's built-in module for working with file paths. Used to build the alias path.

---

### Lines 5–21: The config object

```typescript
export default defineConfig({
  plugins: [react()],
```

**`plugins: [react()]`** — Installs the React plugin. `react()` is called (it's a function that returns the plugin). You could add more plugins here (Tailwind Vite plugin, for example).

---

```typescript
  resolve: {
    alias: {
      "@stock-screener/shared": path.resolve(__dirname, "../shared/src/index.ts"),
    },
  },
```

**`resolve.alias`** — Tells Vite: "When you see this import path, use this actual file instead."

**`"@stock-screener/shared"`** — The npm package name of the shared workspace package.

**`path.resolve(__dirname, "../shared/src/index.ts")`** — The absolute path to the shared package's source file. `__dirname` is the directory of `vite.config.ts` (i.e., the `frontend/` folder). `"../shared/src/index.ts"` goes up one level and into `shared/src/index.ts`.

**Why this alias?** Without it, Vite would look in `frontend/node_modules/@stock-screener/shared` for compiled JavaScript files. The alias makes Vite use the TypeScript source directly — which means:
- Changes to `shared/` are instantly reflected in the frontend (no rebuild needed)
- Full type information is available
- Faster development experience

---

```typescript
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:3001",
        rewrite: (p) => p.replace(/^\/api/, ""),
      },
    },
  },
```

**`server.port: 5173`** — The development server runs on this port. Open `http://localhost:5173` in your browser.

**`server.proxy`** — Configures URL proxying in development. This is a critical setting.

**The problem:** The React app running in the browser is at `localhost:5173`. The backend API is at `localhost:3001`. Due to CORS security rules, browsers restrict cross-origin requests. Even though we have CORS configured, proxying is cleaner.

**`"/api"`** — Any request that starts with `/api` gets proxied.

**`target: "http://localhost:3001"`** — Where to forward the proxied request.

**`rewrite: (p) => p.replace(/^\/api/, "")`** — Removes the `/api` prefix before forwarding.

So: `fetch("/api/health")` in App.tsx:
1. Browser sends GET `/api/health` to Vite dev server (same origin, no CORS issue)
2. Vite proxy sees `/api/health` matches the `/api` rule
3. Vite strips `/api` → `/health`
4. Vite forwards to `http://localhost:3001/health`
5. Backend responds → Vite passes response back to browser

In production, a real proxy (Nginx, API gateway) would do this. The Vite proxy is only for development.

---

## 6. How it works — import resolution

```
App.tsx has:
  import { App } from "./App"
        ↓
Vite resolves "./App" → frontend/src/App.tsx (same directory, bundler mode finds .tsx)
        ↓

Some future file has:
  import { DSLExpressionSchema } from "@stock-screener/shared"
        ↓
Vite sees "@stock-screener/shared"
Checks alias → maps to: /Users/kishore/.../shared/src/index.ts
        ↓
Vite processes shared/src/index.ts directly
No separate compilation step needed
```

---

## 7. Dependencies

| Depends on | Why |
|-----------|-----|
| `vite` package | The build tool being configured |
| `@vitejs/plugin-react` | React + JSX support |
| `path` (Node.js built-in) | Build alias paths |
| `shared/src/index.ts` | Target of the shared package alias |

| What depends on this file | Why |
|--------------------------|-----|
| `pnpm dev` (frontend) | Vite reads this file when starting |
| `pnpm build` (frontend) | Vite reads this for production builds |
| All frontend source files | Their imports are resolved using this config |

---

## 8. What happens if I change or remove something?

| Change | Consequence |
|--------|-------------|
| Remove `react()` plugin | JSX compilation fails; browser can't understand `<App />` syntax |
| Change proxy target to wrong port | API calls fail; health dashboard shows "API unreachable" |
| Remove the `rewrite` function | Proxy forwards `/api/health` → backend gets `/api/health` → 404 (no route matches) |
| Remove the alias | Must `pnpm build` the shared package before any frontend import works |
| Change port to 3001 | Conflicts with the backend server |

---

## 9. Beginner concepts to learn

- **What is a build tool?** — A program that transforms source code (TypeScript, JSX) into browser-executable JavaScript
- **What is hot reloading?** — Automatically updating the browser when you save a file, without a full page refresh
- **What is a proxy?** — A server that forwards requests on behalf of another (here: Vite forwards to the backend)
- **What is CORS?** — A browser security policy restricting cross-origin (different port/domain) requests
- **What is an alias?** — A shortcut that maps one import path to a different file location

---

## 10. Simple mental model

Vite is like a **post office building** that does three things:

1. **Translates TypeScript/JSX into browser language** (like translating letters from one language to another before delivery)

2. **Package shortcuts** — When you write `import X from "@stock-screener/shared"`, Vite goes to the shortcut table and says "oh, that package lives over here at `../shared/src/index.ts`" — like a forwarding address

3. **API proxy** — When the frontend says "get me `/api/health`", Vite acts as a middleman: it takes the request, strips the `/api` prefix, forwards it to the backend at port 3001, and brings back the answer
