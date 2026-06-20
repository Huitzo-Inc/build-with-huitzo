// One row, pure presentation. It takes an expense and three callbacks and renders the
// vendor, amount, category, status, and the right buttons. No hooks, no SDK, so it is
// trivial to test.

import { formatAmount, type Expense } from "../types";

export interface ExpenseRowProps {
  expense: Expense;
  busy: boolean;
  onClassify: (expense: Expense) => void;
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
}

export function ExpenseRow(props: ExpenseRowProps) {
  const { expense, busy, onClassify, onApprove, onReject } = props;

  return (
    <tr>
      <td>{expense.vendor}</td>
      <td>{formatAmount(expense.amount)}</td>
      <td>
        {expense.category ?? (
          <button className="hz-btn hz-btn--ghost" disabled={busy} onClick={() => onClassify(expense)}>
            {busy ? "Classifying..." : "Classify"}
          </button>
        )}
      </td>
      <td>
        <span className={`hz-eyebrow status-${expense.status}`}>{expense.status}</span>
      </td>
      <td>
        {expense.status === "pending" && (
          <span style={{ display: "inline-flex", gap: "0.5rem" }}>
            <button className="hz-btn hz-btn--primary" disabled={busy} onClick={() => onApprove(expense.id)}>
              Approve
            </button>
            <button className="hz-btn hz-btn--secondary" disabled={busy} onClick={() => onReject(expense.id)}>
              Reject
            </button>
          </span>
        )}
      </td>
    </tr>
  );
}
