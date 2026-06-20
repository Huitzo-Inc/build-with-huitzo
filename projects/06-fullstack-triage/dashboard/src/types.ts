// The contract between the dashboard and the expense-triage pack. No shared code:
// the dashboard mirrors the pack's Pydantic models as TypeScript types and agrees on
// the three command ids. That single coupling point is the whole fullstack lesson.

export const LIST_EXPENSES = "@reef/expense-triage/list-expenses";
export const CLASSIFY_EXPENSE = "@reef/expense-triage/classify-expense";
export const APPROVE_EXPENSE = "@reef/expense-triage/approve-expense";

export type Category = "travel" | "meals" | "software" | "office" | "other";
export type Status = "pending" | "approved" | "rejected";

export interface Expense {
  id: string;
  vendor: string;
  amount: number;
  memo: string;
  category: Category | null;
  status: Status;
}

export interface ListResult {
  expenses: Expense[];
  total: number;
}

export interface ClassifyResult {
  expense_id: string;
  category: Category;
  needs_approval: boolean;
  source: "rules" | "model";
}

export interface ApprovalResult {
  expense_id: string;
  status: Status;
  approver: string;
  decided_at: string;
}

/** Replace one expense in a list with a patched copy. Pure, so it is unit-tested. */
export function updateExpense(list: Expense[], id: string, patch: Partial<Expense>): Expense[] {
  return list.map((e) => (e.id === id ? { ...e, ...patch } : e));
}

/** Format a dollar amount. Pure, unit-tested. */
export function formatAmount(amount: number): string {
  return amount.toLocaleString(undefined, { style: "currency", currency: "USD" });
}
