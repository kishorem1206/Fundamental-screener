# frontend/index.html — Beginner Explanation

> **Source file:** `frontend/index.html`

---

## 1. What is this file?

This is the **single HTML page** that the browser loads for the entire application. In a React single-page application (SPA), this is the only HTML file — React renders all the actual UI into a `<div>` inside it.

---

## 2. Why only one HTML file?

Traditional websites have one HTML file per page: `home.html`, `about.html`, `contact.html`.

React SPAs work differently:
- The browser loads `index.html` once
- JavaScript (React) takes over and renders the UI
- When you "navigate" (e.g., to `/screener`), JavaScript updates the page content without reloading `index.html`

This makes navigation faster and allows more dynamic interfaces.

---

## 5. Line-by-line explanation

### Line 1: Document type

```html
<!doctype html>
```

Tells the browser this is an HTML5 document. Without this, browsers enter "quirks mode" — a compatibility mode for ancient websites with different rendering rules. Always include this on line 1.

---

### Line 2: Root HTML element

```html
<html lang="en">
```

**`lang="en"`** — Declares the page language as English. Used by:
- Screen readers (accessibility)
- Search engines
- Browser spell check

---

### Lines 3–8: Head section

```html
<head>
  <meta charset="UTF-8" />
  <link rel="icon" type="image/svg+xml" href="/vite.svg" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Stock Screener</title>
</head>
```

**`<meta charset="UTF-8">`** — Text encoding declaration. UTF-8 supports all characters (English, Hindi, Japanese, special symbols). Must be the first tag in `<head>` so the browser decodes the rest of the HTML correctly.

**`<link rel="icon" type="image/svg+xml" href="/vite.svg">`** — The favicon (the icon shown in the browser tab). Currently uses Vite's default SVG icon.

> TODO: Replace `/vite.svg` with a custom stock screener icon when branding is defined.

**`<meta name="viewport" content="width=device-width, initial-scale=1.0">`** — Critical for mobile responsiveness. Without this:
- `width=device-width` → the page width matches the device width (not the desktop width zoomed out)
- `initial-scale=1.0` → no initial zoom

**`<title>Stock Screener</title>`** — Text shown in the browser tab and when bookmarked.

---

### Lines 9–12: Body section

```html
<body>
  <div id="root"></div>
  <script type="module" src="/src/main.tsx"></script>
</body>
```

**`<div id="root"></div>`** — An empty `<div>` with the ID `root`. This is where React mounts. Before React loads, this is empty. After React loads, the entire application UI lives inside here.

React attaches via `frontend/src/main.tsx`:
```typescript
const root = document.getElementById("root")!;
createRoot(root).render(<App />);
```

**`<script type="module" src="/src/main.tsx">`** — Loads the application entry point.

- **`type="module"`** — This is an ES Module (uses `import`/`export`). Modules are deferred by default (don't block HTML parsing) and have their own scope.
- **`src="/src/main.tsx"`** — Vite serves this file. Vite's dev server intercepts requests for `.tsx` files, compiles TypeScript/JSX on the fly, and returns JavaScript.

**Why `/src/main.tsx` not `/src/main.js`?** In development, Vite transforms `.tsx` → JavaScript in memory before serving. In production (`pnpm build`), Vite compiles everything and the HTML is updated to point to the compiled bundle.

---

## 3. What Vite does with this file

During development (`pnpm dev`):
```
Browser requests http://localhost:5173/
  ↓
Vite serves index.html as-is
  ↓
Browser parses HTML, finds <script src="/src/main.tsx">
  ↓
Browser requests /src/main.tsx
  ↓
Vite intercepts, compiles main.tsx to JavaScript, returns it
  ↓
JavaScript runs: React renders <App /> into <div id="root">
```

During production build (`pnpm build`):
```
Vite reads index.html
  ↓
Vite compiles all TypeScript/JSX
  ↓
Vite bundles and minifies JavaScript
  ↓
Updates index.html to reference bundled files:
  <script src="/assets/index-abc123.js">
  ↓
Output written to frontend/dist/
```

---

## 7. Dependencies

| Depends on | Why |
|-----------|-----|
| Vite | Serves this file in dev, transforms it in build |
| `frontend/src/main.tsx` | The script that boots React |

| What depends on this file | Why |
|--------------------------|-----|
| Vite dev server | Entry point for the browser |
| Production deployment | Served by nginx/CDN as the SPA entry point |

---

## 8. Simple mental model

`index.html` is the **empty storefront** of the application:
- The storefront shell (HTML structure, meta tags, title) is defined here
- The store's interior (all the actual UI) is built by React and injected into `<div id="root">`
- Vite is the construction crew that builds the interior when customers (browsers) arrive
