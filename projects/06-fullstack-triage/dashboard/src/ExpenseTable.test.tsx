// The optimistic-update behavior is the heart of this rung, and it is testable with
// no Hub because ExpenseTable takes plain async callbacks. We pass callbacks that
// resolve or reject and assert the UI sticks or reverts.

import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { ExpenseTable } from "./components/ExpenseTable";
import type { Expense } from "./types";

const pending: Expense = {
  id: "E-1",
  vendor: "Uber",
  amount: 42.5,
  memo: "ride",
  category: "travel",
  status: "pending",
};

const unclassified: Expense = {
  id: "E-4",
  vendor: "Highwater Consulting",
  amount: 1200,
  memo: "retainer",
  category: null,
  status: "pending",
};

const noop = () => Promise.resolve();

describe("ExpenseTable optimistic updates", () => {
  it("approve sticks when the command succeeds", async () => {
    const onApprove = vi.fn().mockResolvedValue(undefined);
    render(<ExpenseTable initialExpenses={[pending]} onApprove={onApprove} onClassify={() => Promise.resolve("other")} />);

    fireEvent.click(screen.getByRole("button", { name: "Approve" }));

    expect(onApprove).toHaveBeenCalledWith("E-1", true);
    await waitFor(() => expect(screen.getByText("approved")).toBeTruthy());
  });

  it("approve reverts when the command fails", async () => {
    const onApprove = vi.fn().mockRejectedValue(new Error("server said no"));
    render(<ExpenseTable initialExpenses={[pending]} onApprove={onApprove} onClassify={() => Promise.resolve("other")} />);

    fireEvent.click(screen.getByRole("button", { name: "Approve" }));

    // It flips optimistically, then reverts to pending and shows the error.
    await waitFor(() => expect(screen.getByRole("alert").textContent).toContain("server said no"));
    expect(screen.getByText("pending")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Approve" })).toBeTruthy();
  });

  it("classify fills in the category from the callback", async () => {
    const onClassify = vi.fn().mockResolvedValue("software");
    render(<ExpenseTable initialExpenses={[unclassified]} onApprove={noop} onClassify={onClassify} />);

    fireEvent.click(screen.getByRole("button", { name: "Classify" }));

    expect(onClassify).toHaveBeenCalledWith(unclassified);
    await waitFor(() => expect(screen.getByText("software")).toBeTruthy());
  });
});
