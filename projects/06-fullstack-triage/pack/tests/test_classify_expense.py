"""classify-expense: rules first (no model), model only for the fuzzy vendors."""

from __future__ import annotations

import pytest

from expense_triage.commands.classify_expense import classify_expense
from expense_triage.models.args import ClassifyArgs
from expense_triage.models.output import Classification


@pytest.mark.asyncio
async def test_known_vendor_uses_rules_and_never_calls_the_model(mock_ctx):
    result = await classify_expense(
        ClassifyArgs(expense_id="E-1", vendor="Uber", amount=42.50, memo="airport"), mock_ctx
    )
    assert result.category == "travel"
    assert result.source == "rules"
    mock_ctx.llm.complete.assert_not_called()  # the whole point: the 90% never hit the model


@pytest.mark.asyncio
async def test_unknown_vendor_falls_back_to_the_model(mock_ctx):
    mock_ctx.llm.complete.return_value = Classification(category="other")

    result = await classify_expense(
        ClassifyArgs(expense_id="E-4", vendor="Highwater Consulting", amount=1200, memo="retainer"),
        mock_ctx,
    )

    assert result.source == "model"
    assert result.category == "other"
    mock_ctx.llm.complete.assert_awaited_once()


@pytest.mark.asyncio
async def test_needs_approval_is_a_deterministic_threshold(mock_ctx):
    small = await classify_expense(ClassifyArgs(expense_id="E-1", vendor="Uber", amount=42.50), mock_ctx)
    large = await classify_expense(ClassifyArgs(expense_id="E-9", vendor="Delta", amount=900.0), mock_ctx)
    assert small.needs_approval is False
    assert large.needs_approval is True


@pytest.mark.asyncio
async def test_model_branch_calls_a_profile_never_a_model_name(mock_ctx):
    mock_ctx.llm.complete.return_value = Classification(category="software")

    await classify_expense(ClassifyArgs(expense_id="E-X", vendor="Zzyzx LLC", amount=10.0), mock_ctx)

    call = mock_ctx.llm.complete.await_args
    assert call.kwargs["profile"] == "default"
    assert call.kwargs["schema"] is Classification
    assert "model" not in call.kwargs
