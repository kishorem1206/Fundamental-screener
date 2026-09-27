import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "node:path";
import { viteSingleFile } from "vite-plugin-singlefile";

// Separate build target for the standalone "Download HTML" export — inlines
// all JS+CSS into one offline-capable file (frontend/export.html). Kept out
// of vite.config.ts deliberately: that config's manualChunks vendor split is
// the opposite of what a singlefile build needs. See html_export_service.py
// and the "build:export" npm script for how this output gets used.
export default defineConfig({
  plugins: [react(), viteSingleFile()],
  build: {
    outDir: "dist-export",
    cssCodeSplit: false,
    rollupOptions: {
      input: resolve(__dirname, "export.html"),
    },
  },
});
