"""Stage 2 tests: risk is a deterministic fact. No model is involved, and the test
proves it by asserting the model is never called."""

from __future__ import annotations

import pytest

from claims_pipeline.commands.assess_risk import assess_risk
from claims_pipeline.models.args import AssessArgs
from claims_pipeline.models.output import RiskAssessment


def _args(**over) -> AssessArgs:
    base = dict(
        claim_id="C-1",
        claim_type="auto",
        claim_amount=10_000.0,
        requires_review=False,
        missing_fields=[],
    )
    base.update(over)
    return AssessArgs(**base)


@pytest.mark.asyncio
async def test_small_clean_auto_claim_is_low_risk(mock_ctx):
    result = await assess_risk(_args(), mock_ctx)
    assert isinstance(result, RiskAssessment)
    assert result.risk_band == "low"


@pytest.mark.asyncio
async def test_high_value_liability_is_high_risk(mock_ctx):
    result = await assess_risk(_args(claim_type="liability", claim_amount=300_000.0), mock_ctx)
    assert result.risk_band == "high"


@pytest.mark.asyncio
async def test_review_flag_adds_a_penalty_and_a_factor(mock_ctx):
    clean = await assess_risk(_args(), mock_ctx)
    flagged = await assess_risk(_args(requires_review=True, missing_fields=["claim_amount"]), mock_ctx)
    assert flagged.risk_score > clean.risk_score
    assert any("review" in f for f in flagged.risk_factors)


@pytest.mark.asyncio
async def test_unknown_amount_is_treated_as_moderate(mock_ctx):
    result = await assess_risk(_args(claim_amount=None), mock_ctx)
    assert any("could not be proven" in f for f in result.risk_factors)


@pytest.mark.asyncio
async def test_no_model_is_ever_called(mock_ctx):
    # The whole point of this stage: it is pure Python. The model stays untouched.
    await assess_risk(_args(), mock_ctx)
    mock_ctx.llm.complete.assert_not_called()
