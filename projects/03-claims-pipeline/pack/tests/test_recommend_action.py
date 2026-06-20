"""Stage 3 tests: the decision is Python's, the model only justifies, and a
justification that is not grounded in the claim is escalated."""

from __future__ import annotations

import pytest

from claims_pipeline.commands.recommend_action import recommend_action
from claims_pipeline.models.args import RecommendArgs
from claims_pipeline.models.output import ActionRecommendation, Justification


def _args(**over) -> RecommendArgs:
    base = dict(
        claim_id="C-1",
        claim_type="auto",
        claim_amount=10_000.0,
        risk_band="low",
        risk_score=0.2,
        requires_review=False,
        risk_factors=["claim_type 'auto' carries a base weight of 0.4."],
    )
    base.update(over)
    return RecommendArgs(**base)


@pytest.mark.asyncio
async def test_action_is_decided_in_python_not_by_the_model(mock_ctx):
    # The model "wants" to escalate, but a low, clean claim auto-approves regardless.
    mock_ctx.llm.complete.return_value = Justification(text="Claim C-1 should be escalated immediately!")

    result = await recommend_action(_args(), mock_ctx)

    assert isinstance(result, ActionRecommendation)
    assert result.action == "auto_approve"


@pytest.mark.asyncio
async def test_high_risk_escalates(mock_ctx):
    mock_ctx.llm.complete.return_value = Justification(text="Claim C-1 carries high risk.")
    result = await recommend_action(_args(risk_band="high", risk_score=0.8), mock_ctx)
    assert result.action == "escalate"
    assert result.escalated is True


@pytest.mark.asyncio
async def test_medium_or_flagged_goes_to_manual_review(mock_ctx):
    mock_ctx.llm.complete.return_value = Justification(text="Claim C-1 needs a look.")
    assert (await recommend_action(_args(risk_band="medium", risk_score=0.5), mock_ctx)).action == "manual_review"
    assert (await recommend_action(_args(requires_review=True), mock_ctx)).action == "manual_review"


@pytest.mark.asyncio
async def test_ungrounded_justification_is_escalated(mock_ctx):
    # The model never mentions the claim id, so the grounding eval fails.
    mock_ctx.llm.complete.return_value = Justification(text="This looks fine to me.")

    result = await recommend_action(_args(), mock_ctx)

    assert result.eval_passed is False
    assert result.escalated is True
    assert result.audit.eval_passed is False
    mock_ctx.log.warning.assert_called_once()


@pytest.mark.asyncio
async def test_grounded_low_claim_passes_and_audits(mock_ctx):
    mock_ctx.llm.complete.return_value = Justification(text="Claim C-1 is low risk and complete; approve it.")

    result = await recommend_action(_args(), mock_ctx)

    assert result.eval_passed is True
    assert result.escalated is False
    assert result.audit.claim_id == "C-1"
    assert result.audit.action == "auto_approve"


@pytest.mark.asyncio
async def test_calls_a_profile_never_a_model_name(mock_ctx):
    mock_ctx.llm.complete.return_value = Justification(text="Claim C-1 approved.")

    await recommend_action(_args(), mock_ctx)

    call = mock_ctx.llm.complete.await_args
    assert call.kwargs["profile"] == "default"
    assert call.kwargs["schema"] is Justification
    assert "model" not in call.kwargs
