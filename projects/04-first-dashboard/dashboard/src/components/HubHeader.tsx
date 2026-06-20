// The header reads its place in Hub from the SDK: useHubNavigation for the back
// button, useHubContext for the (reactive) theme and the current dashboard slug.
// These work because Hub passed a context object to mount(); in dev, dev.tsx
// supplies a mock one.

import { useHubContext, useHubNavigation } from "@huitzo/dashboard-sdk-react";

export function HubHeader() {
  const { navigateToHub } = useHubNavigation();
  const { dashboardSlug, theme } = useHubContext();

  return (
    <header style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "1.5rem" }}>
      <button className="hz-btn hz-btn--ghost" onClick={navigateToHub}>
        &larr; Hub
      </button>
      <h1 style={{ margin: 0 }}>Macro Snapshot</h1>
      <span className="hz-eyebrow" style={{ marginLeft: "auto" }}>
        {dashboardSlug} ({theme})
      </span>
    </header>
  );
}
