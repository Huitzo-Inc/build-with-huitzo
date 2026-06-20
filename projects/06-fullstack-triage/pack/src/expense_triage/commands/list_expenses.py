"""
Module: expense_triage.commands.list_expenses
Description: List expenses, optionally filtered by status. Pure deterministic Python,
            no model. The dashboard calls this on load to render the table.
"""

from __future__ import annotations

from huitzo_sdk import Context, command

from expense_triage import rules
from expense_triage.models.args import ListArgs
from expense_triage.models.output import ListResult


@command("list-expenses", namespace="reef", timeout=30)
async def list_expenses(args: ListArgs, ctx: Context) -> ListResult:
    """Return the expenses, optionally filtered by status. No model is involved."""
    expenses = rules.SEED_EXPENSES
    if args.status is not None:
        expenses = [e for e in expenses if e.status == args.status]
    ctx.log.info(f"list-expenses: status={args.status} returned={len(expenses)}")
    return ListResult(expenses=list(expenses), total=len(expenses))
