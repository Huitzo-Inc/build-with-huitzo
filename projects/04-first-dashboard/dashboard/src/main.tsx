// The PRODUCTION entry point and the Hub contract. A Huitzo Dashboard is a module
// that exports `mount(container, context)` and `unmount(container)`. Hub imports
// this file, calls mount() with the DOM node to render into and a HuitzoContext
// (shared JWT session, navigation, user), and calls unmount() when the user leaves.
//
// The dashboard creates its OWN React root and wraps the app in its own
// ErrorBoundary, so a crash here is contained and never takes Hub down.

import { createRoot, type Root } from "react-dom/client";
import type { HuitzoContext } from "@huitzo/dashboard-sdk";
import { HuitzoProvider } from "@huitzo/dashboard-sdk-react";
import "@huitzo/dashboard-sdk-react/styles";

import { App } from "./App";
import { ErrorBoundary } from "./components/ErrorBoundary";

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
