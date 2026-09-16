// Container: wires useCommand to the view. Deliberately thin — this rung is about
// shipping, not about the UI, so the interesting file is scripts/preflight.mjs.

import { useCommand, useHubContext, useHubNavigation } from "@huitzo/dashboard-sdk-react";

import { RecommendationView } from "./components/RecommendationView";
import { COMMAND, type Candidate, type Recommendation } from "./types";

const CANDIDATES: Candidate[] = [
  { name: "NorthAPI", cost: 0.3, quality: 0.8, reliability: 0.95, as_of: "2026-06-10" },
  { name: "BudgetStream", cost: 0.1, quality: 0.55, reliability: 0.6, as_of: "2026-06-12" },
  { name: "PremiumCloud", cost: 0.85, quality: 0.92, reliability: 0.9, as_of: "2026-06-01" },
];

export function App() {
  const { execute, data, loading, error } = useCommand<Recommendation>(COMMAND);
  const { dashboardSlug } = useHubContext();
  const { navigateToHub } = useHubNavigation();

  return (
    <div
      className="huitzo-dashboard"
      style={{
        maxWidth: 720,
        margin: "0 auto",
        padding: "var(--space-8) var(--space-5)",
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-8)",
      }}
    >
      <header style={{ display: "flex", alignItems: "center", gap: "var(--space-4)" }}>
        <button className="hz-btn hz-btn--ghost" onClick={navigateToHub} type="button">
          &larr; Hub
        </button>
        <span className="hz-eyebrow" style={{ marginLeft: "auto" }}>
          {dashboardSlug}
        </span>
      </header>

      <div>
        <p className="hz-eyebrow" style={{ margin: 0 }}>
          Dashboard rung D6
        </p>
        <h1 style={{ margin: 0 }}>Ship it</h1>
        <p style={{ color: "var(--color-text-secondary)", maxWidth: "60ch" }}>
          A governed recommendation, rendered with its eval findings and audit record. The
          point of this rung is not the panel below — it is everything you check before this
          ever reaches a Hub.
        </p>
      </div>

      <RecommendationView
        loading={loading}
        error={error ? error.message : null}
        data={data ?? null}
        onRun={() =>
          void execute({
            objective: "Balance reliability and cost for a regulated healthcare client.",
            candidates: CANDIDATES,
            freshness_days: 3650,
          })
        }
      />
    </div>
  );
}
