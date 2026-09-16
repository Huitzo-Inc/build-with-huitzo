// The view is a pure function of its props, so every state renders with no Hub,
// no SDK and no network. The states that matter most here are the governed ones:
// a withheld result is not an error, and the UI has to say so.

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { RecommendationView } from "./components/RecommendationView";
import type { Recommendation } from "./types";

const passing: Recommendation = {
  pick: "NorthAPI",
  score: 0.815,
  ranked: [
    { name: "NorthAPI", score: 0.815, as_of: "2026-06-10" },
    { name: "PremiumCloud", score: 0.683, as_of: "2026-06-01" },
  ],
  justification: "NorthAPI earned the top score of 0.815.",
  eval_passed: true,
  eval_findings: ["freshness: OK, pick 'NorthAPI' within 3650 days."],
  withheld: false,
  escalated: false,
  audit: {
    timestamp: "2026-06-18T18:20:27Z",
    autonomy: "suggest",
    candidate_count: 3,
    pick: "NorthAPI",
    eval_passed: true,
    eval_findings: [],
    escalated: false,
  },
};

const withheld: Recommendation = {
  ...passing,
  eval_passed: false,
  eval_findings: ["freshness: FAIL, pick 'NorthAPI' is 900 days old."],
  withheld: true,
  escalated: true,
  audit: { ...passing.audit, eval_passed: false, escalated: true },
};

const base = { loading: false, error: null, data: null, onRun: () => {} };

describe("RecommendationView", () => {
  it("idle: offers the run button and nothing else", () => {
    render(<RecommendationView {...base} />);
    expect(screen.getByRole("button", { name: "Run recommendation" })).toBeTruthy();
  });

  it("loading: disables the button so a second run cannot race the first", () => {
    render(<RecommendationView {...base} loading />);
    expect(screen.getByRole("button", { name: "Running…" }).hasAttribute("disabled")).toBe(true);
  });

  it("error: shows the message in an alert", () => {
    render(<RecommendationView {...base} error="Pack not installed on this tenant." />);
    expect(screen.getByRole("alert").textContent).toContain("Pack not installed");
  });

  it("success: shows the pick, the justification and the findings", () => {
    render(<RecommendationView {...base} data={passing} />);
    expect(screen.getByText("NorthAPI")).toBeTruthy();
    expect(screen.getByText(passing.justification!)).toBeTruthy();
    expect(screen.getByText(passing.eval_findings[0])).toBeTruthy();
  });

  it("success: does NOT announce a withheld banner", () => {
    render(<RecommendationView {...base} data={passing} />);
    expect(screen.queryByRole("status")).toBeNull();
  });

  it("withheld: leads with the governance state, not with the number", () => {
    render(<RecommendationView {...base} data={withheld} />);
    const banner = screen.getByRole("status");
    expect(banner.textContent).toContain("Withheld");
    expect(banner.textContent).toContain("escalated to a human");
  });

  it("withheld: marks the pick as not-to-be-trusted", () => {
    const { container } = render(<RecommendationView {...base} data={withheld} />);
    expect(container.querySelector(".hz-stat__number--warning")).not.toBeNull();
  });

  it("always renders the audit line, passing or withheld", () => {
    const { container, rerender } = render(<RecommendationView {...base} data={passing} />);
    expect(container.textContent).toContain("autonomy suggest");
    rerender(<RecommendationView {...base} data={withheld} />);
    expect(container.textContent).toContain("autonomy suggest");
  });
});
