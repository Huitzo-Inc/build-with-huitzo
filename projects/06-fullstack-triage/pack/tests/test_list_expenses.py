"""list-expenses: deterministic, filterable, no model."""

from __future__ import annotations

import pytest

from expense_triage.commands.list_expenses import list_expenses
from expense_triage.models.args import ListArgs
from expense_triage.models.output import ListResult


@pytest.mark.asyncio
async def test_lists_all_expenses(mock_ctx):
    result = await list_expenses(ListArgs(), mock_ctx)
    assert isinstance(result, ListResult)
    assert result.total == len(result.expenses)
    assert result.total >= 1


@pytest.mark.asyncio
async def test_filters_by_status(mock_ctx):
    result = await list_expenses(ListArgs(status="approved"), mock_ctx)
    assert all(e.status == "approved" for e in result.expenses)


@pytest.mark.asyncio
async def test_no_model_is_called(mock_ctx):
    await list_expenses(ListArgs(), mock_ctx)
    mock_ctx.llm.complete.assert_not_called()
