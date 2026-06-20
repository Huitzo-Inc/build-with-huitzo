"""Stage 1 tests: Python proves the unambiguous fields; the model only judges."""

from __future__ import annotations

import pytest

from claims_pipeline.commands.extract_claim import extract_claim
from claims_pipeline.models.args import ExtractArgs
from claims_pipeline.models.output import ClaimFields, ExtractedClaim

_FULL_DOC = (
    "Claim filed by Dana Reef. Policy number HMO-4471829. "
    "Incident date 2026-05-12. Estimated damage $12,500.00 to the vehicle."
)


@pytest.mark.asyncio
async def test_proves_fields_in_python_not_the_model(mock_ctx):
    # The model classifies and summarizes; it is NOT trusted with the hard fields.
    mock_ctx.llm.complete.return_value = ClaimFields(
        claimant_name="Dana Reef", claim_type="auto", summary="A vehicle damage claim."
    )

    result = await extract_claim(ExtractArgs(claim_id="C-1", document_text=_FULL_DOC), mock_ctx)

    assert isinstance(result, ExtractedClaim)
    assert result.policy_number == "HMO-4471829"
    assert result.incident_date == "2026-05-12"
    assert result.claim_amount == 12500.0
    assert result.missing_fields == []
    assert result.requires_review is False


@pytest.mark.asyncio
async def test_missing_field_forces_review_even_if_model_is_confident(mock_ctx):
    # Document has no dollar amount. Python flags review no matter what the model says.
    doc = "Claim by Dana Reef. Policy number HMO-4471829. Incident date 2026-05-12."
    mock_ctx.llm.complete.return_value = ClaimFields(
        claimant_name="Dana Reef", claim_type="auto", summary="A claim with no stated amount."
    )

    result = await extract_claim(ExtractArgs(claim_id="C-2", document_text=doc), mock_ctx)

    assert result.claim_amount is None
    assert "claim_amount" in result.missing_fields
    assert result.requires_review is True


@pytest.mark.asyncio
async def test_amount_is_parsed_to_a_float(mock_ctx):
    mock_ctx.llm.complete.return_value = ClaimFields(
        claimant_name=None, claim_type="property", summary="x"
    )
    doc = "Policy number AB-1234. Incident date 2026-01-02. Loss of $1,250,000.00 reported."

    result = await extract_claim(ExtractArgs(claim_id="C-3", document_text=doc), mock_ctx)

    assert result.claim_amount == 1_250_000.0


@pytest.mark.asyncio
async def test_calls_a_profile_never_a_model_name(mock_ctx):
    mock_ctx.llm.complete.return_value = ClaimFields(claimant_name=None, claim_type="other", summary="x")

    await extract_claim(ExtractArgs(claim_id="C-4", document_text=_FULL_DOC), mock_ctx)

    mock_ctx.llm.complete.assert_awaited_once()
    call = mock_ctx.llm.complete.await_args
    assert call.kwargs["profile"] == "default"  # a capability profile
    assert call.kwargs["schema"] is ClaimFields  # structured output
    assert "model" not in call.kwargs  # a pack must never name a model
