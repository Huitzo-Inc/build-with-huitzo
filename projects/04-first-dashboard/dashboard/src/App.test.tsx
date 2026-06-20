// A smoke test that App wires the SDK hooks together without crashing. We mock the
// React SDK so the test runs with no Hub and no network: useCommand returns an idle
// state, the Hub hooks return mock navigation/context. This proves the component
// composition (header + panel) renders; the real SDK integration is checked by
// `npm run build` (tsc typechecks against the real SDK types) and by dev.tsx.

import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

vi.mock("@huitzo/dashboard-sdk-react", () => ({
  useCommand: () => ({
    execute: vi.fn(),
    data: null,
    loading: false,
    error: null,
    reset: vi.fn(),
    status: "idle",
    isIdle: true,
    isSuccess: false,
    isError: false,
  }),
  useHubNavigation: () => ({
    navigateToHub: vi.fn(),
    navigateToDashboard: vi.fn(),
    navigateToExplore: vi.fn(),
    navigateToSettings: vi.fn(),
    currentDashboard: "first-dashboard",
  }),
  useHubContext: () => ({
    apiUrl: "http://localhost:8787",
    dashboardSlug: "first-dashboard",
    user: null,
    theme: "dark",
    locale: "en",
    currency: undefined,
  }),
}));

// Import App AFTER the mock is registered.
const { App } = await import("./App");

describe("App", () => {
  it("renders the Hub header and an idle snapshot panel", () => {
    render(<App />);
    expect(screen.getByText("Macro Snapshot")).toBeTruthy();
    expect(screen.getByText(/first-dashboard \(dark\)/)).toBeTruthy();
    expect(screen.getByRole("button", { name: /Run snapshot/i })).toBeTruthy();
  });
});
