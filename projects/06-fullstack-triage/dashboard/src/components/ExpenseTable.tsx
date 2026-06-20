// The table holds the optimistic-update logic, and it is deliberately SDK-free: it
// takes the expenses plus two async callbacks (onApprove, onClassify) and manages the
// local state. That separation is what makes the optimistic-and-revert behavior
// testable with no Hub (see ExpenseTable.test.tsx): pass a callback that resolves to
// see the update stick, or one that rejects to see it revert.

import { useEffect, useState } from "react";

import { ExpenseRow } from "./ExpenseRow";
import { updateExpense, type Category, type Expense, type Status } from "../types";

export interface ExpenseTableProps {
  initialExpenses: Expense[];
  onApprove: (id: string, approve: boolean) => Promise<void>;
  onClassify: (expense: Expense) => Promise<Category>;
}

export function ExpenseTable({ initialExpenses, onApprove, onClassify }: ExpenseTableProps) {
  const [expenses, setExpenses] = useState<Expense[]>(initialExpenses);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Re-seed when the list command resolves with new data.
  useEffect(() => {
    setExpenses(initialExpenses);
  }, [initialExpenses]);

  async function decide(id: string, approve: boolean): Promise<void> {
    const snapshot = expenses;
    const status: Status = approve ? "approved" : "rejected";
    setError(null);
    setBusyId(id);
    // Optimistic: flip the status immediately so the UI feels instant.
    setExpenses((list) => updateExpense(list, id, { status }));
    try {
      await onApprove(id, approve);
    } catch (e) {
      // The command failed: revert to exactly what we had before.
      setExpenses(snapshot);
      setError(e instanceof Error ? e.message : "Could not update the expense.");
    } finally {
      setBusyId(null);
    }
  }

  async function classify(expense: Expense): Promise<void> {
    setError(null);
    setBusyId(expense.id);
    try {
      const category = await onClassify(expense);
      setExpenses((list) => updateExpense(list, expense.id, { category }));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not classify the expense.");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <section className="hz-card hz-card--lg" aria-label="Expenses">
      <p className="hz-eyebrow hz-eyebrow--accent">Expenses</p>
      {error && (
        <p className="hz-card--warning" role="alert">
          {error}
        </p>
      )}
      <table>
        <thead>
          <tr>
            <th>Vendor</th>
            <th>Amount</th>
            <th>Category</th>
            <th>Status</th>
            <th>Decision</th>
          </tr>
        </thead>
        <tbody>
          {expenses.map((expense) => (
            <ExpenseRow
              key={expense.id}
              expense={expense}
              busy={busyId === expense.id}
              onClassify={classify}
              onApprove={(id) => void decide(id, true)}
              onReject={(id) => void decide(id, false)}
            />
          ))}
        </tbody>
      </table>
    </section>
  );
}
