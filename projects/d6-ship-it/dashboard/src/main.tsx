// The PRODUCTION entry point, and the whole contract between your dashboard and
// Huitzo Hub. Everything else in this rung is detail; these two functions are the
// thing to learn.
//
// A Huitzo Dashboard is not a website. It is a module Hub imports and runs inside
// itself. Hub calls mount() with a DOM node to render into and a HuitzoContext
// (the shared session, the user, the theme, navigation), and calls unmount() when
// the user navigates away.
//
// Note what the dashboard owns: its OWN React root and its OWN ErrorBoundary. A
// crash in here is contained and never takes Hub down with it.

import { createRoot, type Root } from "react-dom/client";
import type { HuitzoContext } from "@huitzo/dashboard-sdk";
import { HuitzoProvider } from "@huitzo/dashboard-sdk-react";
import "@huitzo/dashboard-sdk-react/styles";

import { App } from "./App";
import { ErrorBoundary } from "./components/ErrorBoundary";

// Keyed by container so Hub can mount the same dashboard into more than one node,
// and so unmount() can find the right root to tear down. A WeakMap lets a detached
// container be garbage collected without leaking its root.
const roots = new WeakMap<HTMLElement, Root>();

export function mount(container: HTMLElement, context: HuitzoContext): void {
  const root = createRoot(container);
  roots.set(container, root);
  root.render(
    <ErrorBoundary>
      <HuitzoProvider context={context}>
        <App />
      </HuitzoProvider>
    </ErrorBoundary>,
  );
}

export function unmount(container: HTMLElement): void {
  roots.get(container)?.unmount();
  roots.delete(container);
}
