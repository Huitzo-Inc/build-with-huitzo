// These tests need no Hub, no SDK, and no network. SnapshotView is a pure function
// of its props, so we render it in each of its four states and check the output.
// This is the payoff of splitting presentation (SnapshotView) from the hook wiring
// (SnapshotPanel): the part with the rendering logic is trivially testable.

import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { SnapshotView } from "./components/SnapshotView";
import { formatDelta, formatValue, type CountrySnapshot } from "./types";

const base = {
  country: "USA",
  indicator: "inflation" as const,
  onCountry: vi.fn(),
  onIndicator: vi.fn(),
  onRun: vi.fn(),
  loading: false,
  error: null,
  data: null,
};

const sample: CountrySnapshot = {
  country: "USA",
  indicator: "inflation",
  latest_value: 3.4,
  latest_year: "2025",
  delta_pct: -0.6,
  summary: "Inflation eased over the latest period.",
};

describe("SnapshotView", () => {
  it("idle: shows the Run button and no result", () => {
    render(<SnapshotView {...base} />);
    expect(screen.getByRole("button", { name: /Run snapshot/i })).toBeTruthy();
    expect(screen.queryByText(sample.summary)).toBeNull();
  });

  it("loading: shows progress and disables the button", () => {
    render(<SnapshotView {...base} loading={true} />);
    expect(screen.getByText(/Asking the pack/i)).toBeTruthy();
    const button = screen.getByRole("button") as HTMLButtonElement;
    expect(button.disabled).toBe(true);
  });

  it("error: shows the error message", () => {
    render(<SnapshotView {...base} error={new Error("Rate limited")} />);
    expect(screen.getByRole("alert").textContent).toContain("Rate limited");
  });

  it("success: shows the value, the delta, and the model summary", () => {
    render(<SnapshotView {...base} data={sample} />);
    expect(screen.getByText("3.4")).toBeTruthy();
    expect(screen.getByText(/-0.6%/)).toBeTruthy();
    expect(screen.getByText(sample.summary)).toBeTruthy();
  });

  it("clicking Run calls onRun", () => {
    const onRun = vi.fn();
    render(<SnapshotView {...base} onRun={onRun} />);
    fireEvent.click(screen.getByRole("button", { name: /Run snapshot/i }));
    expect(onRun).toHaveBeenCalledOnce();
  });
});

describe("formatters", () => {
  it("formatValue handles null and big numbers", () => {
    expect(formatValue(null)).toBe("no data");
    expect(formatValue(3.4)).toBe("3.4");
    expect(formatValue(25_000_000_000)).toBe("25B");
  });

  it("formatDelta signs the number and handles null", () => {
    expect(formatDelta(null)).toBe("no prior period");
    expect(formatDelta(1.2)).toBe("+1.2%");
    expect(formatDelta(-0.6)).toBe("-0.6%");
  });
});
