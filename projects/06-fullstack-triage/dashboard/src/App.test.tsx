// Smoke test: App renders the header and the expense table from a mocked list
// command, with no Hub and no network.

import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

vi.mock("@huitzo/dashboard-sdk-react", () => ({
  useCommand: () => ({
    execute: vi.fn(),
    data: {
      expenses: [
        { id: "E-1", vendor: "Uber", amount: 42.5, memo: "", category: "travel", status: "pending" },
      ],
      total: 1,
    },
    loading: false,
    error: null,
    reset: vi.fn(),
    status: "success",
    isIdle: false,
    isSuccess: true,
    isError: false,
  }),
  useHuitzo: () => ({
    client: { commands: { execute: vi.fn().mockResolvedValue({ result: {}, execution: {} }) } },
    user: { email: "dana@reef.example" },
    isAuthenticated: true,
  }),
  useHubNavigation: () => ({
    navigateToHub: vi.fn(),
    navigateToDashboard: vi.fn(),
    navigateToExplore: vi.fn(),
    navigateToSettings: vi.fn(),
    currentDashboard: "expense-triage",
  }),
  useHubContext: () => ({
    apiUrl: "http://localhost:8787",
    dashboardSlug: "expense-triage",
    user: null,
    theme: "dark",
    locale: "en",
    currency: undefined,
  }),
}));

const { App } = await import("./App");

describe("App", () => {
  it("renders the header and the seeded expense", () => {
    render(<App />);
    expect(screen.getByText("Expense Triage")).toBeTruthy();
    expect(screen.getByText("Uber")).toBeTruthy();
  });
});
