"""approve-expense: records a human's decision. Deterministic, no model."""

from __future__ import annotations

import pytest

from expense_triage.commands.approve_expense import approve_expense
from expense_triage.models.args import ApproveArgs
from expense_triage.models.output import ApprovalResult


@pytest.mark.asyncio
async def test_approve_records_approved(mock_ctx):
    result = await approve_expense(
        ApproveArgs(expense_id="E-3", approve=True, approver="dana@reef.example"), mock_ctx
    )
    assert isinstance(result, ApprovalResult)
    assert result.status == "approved"
    assert result.approver == "dana@reef.example"
    assert result.decided_at  # an ISO timestamp was recorded


@pytest.mark.asyncio
async def test_reject_records_rejected(mock_ctx):
    result = await approve_expense(
        ApproveArgs(expense_id="E-3", approve=False, approver="dana@reef.example"), mock_ctx
    )
    assert result.status == "rejected"


@pytest.mark.asyncio
async def test_no_model_is_called(mock_ctx):
    await approve_expense(ApproveArgs(expense_id="E-3", approve=True, approver="x"), mock_ctx)
    mock_ctx.llm.complete.assert_not_called()
