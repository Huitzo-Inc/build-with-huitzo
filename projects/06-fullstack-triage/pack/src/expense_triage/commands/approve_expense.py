"""
Module: expense_triage.commands.approve_expense
Description: Record a human's approve-or-reject decision on an expense. Pure
            deterministic Python, no model. The pack is `suggest` autonomy: it does
            not decide approvals on its own, it records the decision a person made in
            the dashboard. The `approve` flag in the args IS that human decision.
"""

from __future__ import annotations

from datetime import UTC, datetime

from huitzo_sdk import Context, command

from expense_triage.models.args import ApproveArgs
from expense_triage.models.output import ApprovalResult, Status


@command("approve-expense", namespace="reef", timeout=30)
async def approve_expense(args: ApproveArgs, ctx: Context) -> ApprovalResult:
    """Record the human's decision. No model: this just writes down what a person chose."""
    status: Status = "approved" if args.approve else "rejected"
    decided_at = datetime.now(UTC).isoformat()
    ctx.log.info(f"approve-expense: id={args.expense_id} status={status} by={args.approver}")
    return ApprovalResult(
        expense_id=args.expense_id,
        status=status,
        approver=args.approver,
        decided_at=decided_at,
    )
