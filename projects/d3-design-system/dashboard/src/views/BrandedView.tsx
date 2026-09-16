// ✅ THE AFTER. This is the file to copy from.
//
// Same data as GenericView, same information, and not one colour decision of our
// own. Every value below either comes from a `hz-*` primitive or resolves through
// a `var(--*)` token, which is what makes it follow Hub's theme — including a
// white-labelled Hub whose brand you have never seen.
//
// The four rules this file is demonstrating:
//
//  1. TYPOGRAPHIC HIERARCHY, three tiers, always: an eyebrow label, then a real
//     <h1>, then body copy in --color-text-secondary. Never lead with a
//     paragraph; never set everything at one weight.
//  2. THE ACCENT BUDGET: --color-accent appears ONCE per viewport, on the one
//     thing you want clicked. Here that is the single hz-btn--primary. Status
//     colours (success/warning/error) are not decoration and do not count.
//  3. LAYERED BACKGROUNDS: --color-bg-primary (page) sits under
//     --color-bg-elevated (cards). hz-card already handles the elevated layer and
//     its shadow, so you never author either.
//  4. SPACING ON THE SCALE: var(--space-*), a 4px scale. Vertical gap between
//     major sections is --space-12 or more. Whitespace is part of the design.
//
// A test in design-rules.test.ts fails the build if anyone reintroduces a hex
// literal here, so the rule is enforced rather than merely documented.

import { SAMPLE, trend } from "../sample";

export function BrandedView() {
  const direction = trend(SAMPLE.delta_pct);

  return (
    <div
      className="huitzo-dashboard"
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-12)",
        padding: "var(--space-8)",
        background: "var(--color-bg-primary)",
        borderRadius: "var(--radius-lg)",
      }}
    >
      {/* Tier 1 + 2 + 3: eyebrow, heading, supporting copy. */}
      <header style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
        <p className="hz-eyebrow" style={{ margin: 0 }}>
          {SAMPLE.country} · {SAMPLE.latest_year}
        </p>
        <h1 style={{ margin: 0 }}>Macro snapshot</h1>
        <p style={{ margin: 0, color: "var(--color-text-secondary)", maxWidth: "60ch" }}>
          {SAMPLE.summary}
        </p>
      </header>

      {/* Two figures. The card primitive owns the surface, the radius and the
          shadow, so there is nothing here to get wrong. */}
      <section
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: "var(--space-5)",
        }}
      >
        <div className="hz-card hz-card--md">
          <p className="hz-eyebrow" style={{ margin: 0 }}>
            {SAMPLE.indicator}
          </p>
          <p className="hz-stat__number" style={{ margin: 0 }}>
            {SAMPLE.latest_value}
          </p>
        </div>

        <div className="hz-card hz-card--md">
          <p className="hz-eyebrow" style={{ margin: 0 }}>
            Year on year
          </p>
          {/* Status colour, carrying MEANING, not decoration: the modifier is
              chosen from the data, not picked to look nice. */}
          <p
            className={
              direction === "improving"
                ? "hz-stat__number hz-stat__number--success"
                : direction === "worsening"
                  ? "hz-stat__number hz-stat__number--warning"
                  : "hz-stat__number"
            }
            style={{ margin: 0 }}
          >
            {SAMPLE.delta_pct}%
          </p>
        </div>
      </section>

      {/* The accent, spent once, on the one action worth taking. */}
      <footer style={{ display: "flex", gap: "var(--space-4)", alignItems: "center" }}>
        <button className="hz-btn hz-btn--primary" type="button">
          Run snapshot
        </button>
        <button className="hz-btn hz-btn--ghost" type="button">
          Change country
        </button>
      </footer>
    </div>
  );
}
