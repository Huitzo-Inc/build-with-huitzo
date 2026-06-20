"""Tests for the extract-claim command."""

from __future__ import annotations

import pytest

from doc_to_json.commands.extract_claim import extract_claim
from doc_to_json.models.args import ExtractClaimArgs
from doc_to_json.models.output import ClaimExtraction, ClaimRecord

# A fictional Nautilus Mutual claim with every required field present.
_COMPLETE_CLAIM = """
Nautilus Mutual Claim Intake Form

Claimant: Mariana Castillo
Policy Number: NM-48201773
Incident Date: 2026-05-09
Claimed Amount: $4,200.00

Description: A burst pipe in the kitchen ceiling damaged the cabinetry and flooring.
The claimant reports the leak began overnight and was discovered the next morning.
"""

# The same form with the policy number and amount removed.
_INCOMPLETE_CLAIM = """
Nautilus Mutual Claim Intake Form

Claimant: Mariana Castillo
Incident Date: 2026-05-09

Description: A burst pipe in the kitchen ceiling damaged the cabinetry and flooring.
"""


@pytest.mark.asyncio
async def test_complete_claim_passes_model_fields_through_and_needs_no_review(mock_ctx):
    mock_ctx.storage.get.return_value = _COMPLETE_CLAIM
    mock_ctx.llm.complete.return_value = ClaimExtraction(
        claimant_name="Mariana Castillo",
        policy_number="NM-48201773",
        incident_date="2026-05-09",
        claim_amount="$4,200.00",
        claim_type="property",
        summary="A burst pipe damaged the kitchen. The claimant seeks $4,200.00 for cabinetry and flooring.",
    )

    result = await extract_claim(ExtractClaimArgs(document_id="doc-1"), mock_ctx)

    assert isinstance(result, ClaimRecord)
    # Model fields pass through untouched.
    assert result.claimant_name == "Mariana Castillo"
    assert result.claim_type == "property"
    assert result.summary.startswith("A burst pipe")
    # Deterministic gate: every required field was found, so no review needed.
    assert result.missing_fields == []
    assert result.requires_review is False


@pytest.mark.asyncio
async def test_missing_required_fields_force_review_regardless_of_model(mock_ctx):
    mock_ctx.storage.get.return_value = _INCOMPLETE_CLAIM
    # The model "hallucinates" a policy number and amount the document does not contain.
    # The deterministic gate must not trust it: Python's regex pass owns the verdict.
    mock_ctx.llm.complete.return_value = ClaimExtraction(
        claimant_name="Mariana Castillo",
        policy_number="NM-99999999",
        incident_date="2026-05-09",
        claim_amount="$9,999.00",
        claim_type="property",
        summary="A burst pipe damaged the kitchen.",
    )

    result = await extract_claim(ExtractClaimArgs(document_id="doc-2"), mock_ctx)

    assert result.requires_review is True
    assert "policy_number" in result.missing_fields
    assert "claim_amount" in result.missing_fields
    # The incident date was present, so it is not flagged.
    assert "incident_date" not in result.missing_fields
    # Injection-safety: the model's hallucinated values are DISCARDED. The record
    # carries Python's regex verdict (None here), never the forged string.
    assert result.policy_number is None
    assert result.claim_amount is None


@pytest.mark.asyncio
async def test_calls_a_profile_with_the_schema_and_never_a_model_name(mock_ctx):
    mock_ctx.storage.get.return_value = _COMPLETE_CLAIM
    mock_ctx.llm.complete.return_value = ClaimExtraction(
        claimant_name="Mariana Castillo",
        policy_number="NM-48201773",
        incident_date="2026-05-09",
        claim_amount="$4,200.00",
        claim_type="property",
        summary="A burst pipe damaged the kitchen.",
    )

    await extract_claim(ExtractClaimArgs(document_id="doc-3"), mock_ctx)

    mock_ctx.llm.complete.assert_awaited_once()
    call = mock_ctx.llm.complete.await_args
    assert call.kwargs["profile"] == "default"  # a capability profile
    assert call.kwargs["schema"] is ClaimExtraction  # structured output
    assert "model" not in call.kwargs  # a pack must never name a model
