import { useHubContext, useHubNavigation } from "@huitzo/dashboard-sdk-react";

export function HubHeader() {
  const { navigateToHub } = useHubNavigation();
  const { dashboardSlug, theme } = useHubContext();

  return (
    <header style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "1.5rem" }}>
      <button className="hz-btn hz-btn--ghost" onClick={navigateToHub}>
        &larr; Hub
      </button>
      <h1 style={{ margin: 0 }}>Expense Triage</h1>
      <span className="hz-eyebrow" style={{ marginLeft: "auto" }}>
        {dashboardSlug} ({theme})
      </span>
    </header>
  );
}
