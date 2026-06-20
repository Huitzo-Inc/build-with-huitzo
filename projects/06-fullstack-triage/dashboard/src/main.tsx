// Production entry and the Hub contract: export mount(container, context) and
// unmount(container). Identical shape to Tier 4; see ../../04-first-dashboard for the
// line-by-line explanation.

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
