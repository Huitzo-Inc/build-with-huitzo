/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import cssInjectedByJsPlugin from "vite-plugin-css-injected-by-js";

// A Huitzo Dashboard ships as a single ES module that exports `mount`/`unmount`.
// Vite "library mode" builds exactly that from src/main.tsx, and
// css-injected-by-js folds the design tokens into the one main.js so there is no
// separate stylesheet to load. In dev (`vite` / `huitzo dashboard dev`), index.html
// loads src/dev.tsx instead, which mounts the app with a mock Hub context.
//
// This config is identical in every dashboard rung. You write it once and never
// think about it again, which is why D0 gets it out of the way first.
export default defineConfig(({ mode }) => ({
  // Dev server port — the README walkthrough opens http://localhost:3000.
  server: { port: 3000 },
  // Library-mode builds do NOT get Vite's automatic `process.env.NODE_ENV`
  // replacement, and a dashboard bundles React to run standalone in the Hub —
  // there is no outer bundler to define `process`. Without this, React's
  // `process.env.NODE_ENV` checks reach a bare `process` in the browser and the
  // Hub fails to mount with "process is not defined". Replace it at build time.
  // Gate "production" on the production build ONLY: the Hub build (mode
  // "production") gets React's small prod build; dev AND vitest (mode "test")
  // get the dev build. Otherwise test mode loads react-dom's prod internals and
  // `npm test` dies with "React.act is not a function".
  define: {
    "process.env.NODE_ENV": JSON.stringify(
      mode === "production" ? "production" : "development",
    ),
  },
  plugins: [react(), cssInjectedByJsPlugin()],
  build: {
    lib: {
      entry: "src/main.tsx",
      formats: ["es"],
      fileName: () => "main.js",
    },
    cssCodeSplit: false,
    // Bundle everything (including React) so the dashboard also runs standalone
    // in a plain browser via dev.tsx, with no Hub providing shared dependencies.
    rollupOptions: {
      output: {
        // Belt-and-suspenders for the browser: some bundled deps probe `process`
        // directly (Node runtime detection, e.g. `process.versions`). The Hub has
        // no `process`, so install a minimal shim before the module body runs so
        // those bare reads can't throw "process is not defined".
        banner:
          'globalThis.process||(globalThis.process={env:{},versions:{},platform:""});',
      },
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    css: false,
  },
}));
