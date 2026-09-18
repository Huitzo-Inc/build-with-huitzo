// The container wires the SDK to the table. The initial list uses useCommand (a
// declarative fetch). The mutations use client.commands.execute directly, because a
// mutation needs the promise to REJECT on failure so the table can revert its
// optimistic update; the client call does exactly that.

import { isCommandReceipt } from "@huitzo/dashboard-sdk";
import { useCommand, useHuitzo } from "@huitzo/dashboard-sdk-react";

import { ExpenseTable } from "./ExpenseTable";
import {
  APPROVE_EXPENSE,
  CLASSIFY_EXPENSE,
  LIST_EXPENSES,
  type ApprovalResult,
  type Category,
  type ClassifyResult,
  type Expense,
  type ListResult,
} from "../types";

export function ExpensePanel() {
  const { client, user } = useHuitzo();

  // Declarative fetch: runs on mount, manages loading/error/data for us.
  const { data, loading, error } = useCommand<ListResult>(LIST_EXPENSES, { initialArgs: {} });

  const onApprove = async (id: string, approve: boolean): Promise<void> => {
    await client.commands.execute<ApprovalResult>(APPROVE_EXPENSE, {
      expense_id: id,
      approve,
      approver: user?.email ?? "unknown",
    });
  };

  const onClassify = async (expense: Expense): Promise<Category> => {
    const res = await client.commands.execute<ClassifyResult>(CLASSIFY_EXPENSE, {
      expense_id: expense.id,
      vendor: expense.vendor,
      amount: expense.amount,
      memo: expense.memo,
    });
    // execute() returns a union: a fast-queue command runs inline and returns its
    // result (HTTP 200); a medium/long-queue command is handed to a worker and
    // returns a receipt instead (HTTP 202). classify-expense is fast, so the
    // receipt branch is a deployment misconfiguration, not a normal path.
    if (isCommandReceipt(res)) {
      throw new Error(
        `classify-expense was queued (task ${res.task_id}). Poll client.tasks.get() for the result, ` +
          "or move the command back to the fast queue.",
      );
    }
    return res.result.category;
  };

  if (loading) return <p role="status">Loading expenses...</p>;
  if (error)
    return (
      <p className="hz-card--warning" role="alert">
        {error.message}
      </p>
    );

  return (
    <ExpenseTable
      initialExpenses={data?.expenses ?? []}
      onApprove={onApprove}
      onClassify={onClassify}
    />
  );
}
