// ❌ THE BEFORE. Do not copy anything from this file.
//
// This is the page an AI assistant writes when nobody tells it about the design
// system: a centred headline, one subtitle paragraph, a blue gradient button, and
// a pile of hand-picked hex values. It is not broken and it is not ugly. It is
// *generic* — it could belong to any product, which is exactly the problem.
//
// Read it once, notice how much of it is colour decisions you had to invent, then
// compare it to BrandedView.tsx, which renders the same data with none of them.
//
// Every hard-coded value below is a bug this rung teaches you to see:
//   - hex literals        -> should be var(--color-*)
//   - the gradient CTA    -> should be hz-btn--primary
//   - the hand-rolled shadow -> should be var(--shadow-*), or just hz-card
//   - px paddings         -> should be var(--space-*)
//   - everything centred, one font weight -> no typographic hierarchy at all
//
// It also only works in dark mode. Flip the dev host to data-theme="light" and
// watch it stay stubbornly dark, because none of these colours go through a token.

import { SAMPLE } from "../sample";

export function GenericView() {
  return (
    <div
      style={{
        backgroundColor: "#0b0b0c",
        color: "#e9e9e9",
        borderRadius: "12px",
        padding: "48px 32px",
        textAlign: "center",
        boxShadow: "0 4px 24px rgba(0, 0, 0, 0.45)",
        fontFamily: "Inter, system-ui, sans-serif",
      }}
    >
      <h1 style={{ fontSize: "32px", fontWeight: 600, margin: "0 0 12px" }}>
        Welcome to Macro Snapshot
      </h1>
      <p style={{ color: "#9ca3af", margin: "0 auto 32px", maxWidth: "48ch" }}>
        View the latest macroeconomic indicator for a country. {SAMPLE.summary}
      </p>

      <div style={{ display: "flex", gap: "16px", justifyContent: "center", marginBottom: "32px" }}>
        <div
          style={{
            backgroundColor: "#18181b",
            border: "1px solid #27272a",
            borderRadius: "8px",
            padding: "20px 28px",
          }}
        >
          <div style={{ fontSize: "13px", color: "#9ca3af", marginBottom: "6px" }}>
            {SAMPLE.indicator}
          </div>
          <div style={{ fontSize: "28px", fontWeight: 600 }}>{SAMPLE.latest_value}</div>
        </div>
        <div
          style={{
            backgroundColor: "#18181b",
            border: "1px solid #27272a",
            borderRadius: "8px",
            padding: "20px 28px",
          }}
        >
          <div style={{ fontSize: "13px", color: "#9ca3af", marginBottom: "6px" }}>change</div>
          <div style={{ fontSize: "28px", fontWeight: 600, color: "#22c55e" }}>
            {SAMPLE.delta_pct}%
          </div>
        </div>
      </div>

      <button
        style={{
          background: "linear-gradient(90deg, #155dfc 0%, #7c3aed 100%)",
          color: "#ffffff",
          border: "none",
          borderRadius: "8px",
          padding: "12px 28px",
          fontSize: "15px",
          fontWeight: 500,
          cursor: "pointer",
        }}
      >
        Get Started
      </button>
    </div>
  );
}
