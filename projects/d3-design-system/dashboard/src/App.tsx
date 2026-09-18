// The whole rung is this toggle: the same snapshot, rendered two ways.
//
// Flip between them in the browser and the difference is immediate. Then read the
// two files — GenericView is 90 lines of colour decisions, BrandedView is the same
// information with none.

import { useState } from "react";
import { useHubContext } from "@huitzo/dashboard-sdk-react";

import { BrandedView } from "./views/BrandedView";
import { GenericView } from "./views/GenericView";

export function App() {
  const [branded, setBranded] = useState(true);
  const { theme } = useHubContext();

  return (
    <div
      className="huitzo-dashboard"
      style={{
        maxWidth: 820,
        margin: "0 auto",
        padding: "var(--space-8) var(--space-5)",
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-8)",
      }}
    >
      <header style={{ display: "flex", alignItems: "center", gap: "var(--space-4)" }}>
        <p className="hz-eyebrow hz-eyebrow--accent" style={{ margin: 0 }}>
          Dashboard rung D3
        </p>
        <span
          className="hz-code"
          style={{ marginLeft: "auto", color: "var(--color-text-muted)" }}
        >
          theme: {theme}
        </span>
      </header>

      <div
        role="group"
        aria-label="Which treatment to show"
        style={{ display: "flex", gap: "var(--space-3)" }}
      >
        <button
          type="button"
          className={branded ? "hz-btn hz-btn--secondary" : "hz-btn hz-btn--ghost"}
          aria-pressed={branded}
          onClick={() => setBranded(true)}
        >
          Branded
        </button>
        <button
          type="button"
          className={!branded ? "hz-btn hz-btn--secondary" : "hz-btn hz-btn--ghost"}
          aria-pressed={!branded}
          onClick={() => setBranded(false)}
        >
          Generic
        </button>
      </div>

      <main>{branded ? <BrandedView /> : <GenericView />}</main>

      <p style={{ margin: 0, color: "var(--color-text-muted)", fontSize: "0.9rem" }}>
        Switch the dev host between <code className="hz-code">data-theme="dark"</code> and{" "}
        <code className="hz-code">"light"</code> in <code className="hz-code">index.html</code>.
        The branded view follows. The generic one cannot, because none of its colours
        go through a token.
      </p>
    </div>
  );
}
