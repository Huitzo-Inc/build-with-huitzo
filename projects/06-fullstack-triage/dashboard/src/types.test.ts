import { describe, it, expect } from "vitest";

import { formatAmount, updateExpense, type Expense } from "./types";

const expenses: Expense[] = [
  { id: "E-1", vendor: "Uber", amount: 42.5, memo: "", category: "travel", status: "pending" },
  { id: "E-2", vendor: "GitHub", amount: 21, memo: "", category: "software", status: "pending" },
];

describe("updateExpense", () => {
  it("patches only the matching expense, immutably", () => {
    const next = updateExpense(expenses, "E-1", { status: "approved" });
    expect(next[0].status).toBe("approved");
    expect(next[1].status).toBe("pending");
    expect(expenses[0].status).toBe("pending"); // original is untouched
  });

  it("leaves the list unchanged when no id matches", () => {
    const next = updateExpense(expenses, "nope", { status: "rejected" });
    expect(next.map((e) => e.status)).toEqual(["pending", "pending"]);
  });
});

describe("formatAmount", () => {
  it("formats as USD currency", () => {
    expect(formatAmount(42.5)).toMatch(/42\.50/);
    expect(formatAmount(42.5)).toContain("$");
  });
});
