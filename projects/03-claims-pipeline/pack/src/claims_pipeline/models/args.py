"""
Module: claims_pipeline.models.args
Description: Typed input models, one per stage. The pipeline contract lives here:
            every field a downstream stage asks for must be produced by the stage
            before it. `models/output.py` produces; this file consumes. The test
            `test_pipeline_contract.py` enforces that the two line up, so a broken
            handoff fails in CI, not in production.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from claims_pipeline.models.output import ClaimType, RiskBand


class ExtractArgs(BaseModel):
    """Stage 1 input: the raw claim, as text. (doc-to-json shows how to read it
    from storage; here we take the text directly so the pipeline stays the lesson.)"""

    claim_id: str = Field(min_length=1, description="Stable id for this claim, carried through every stage.")
    document_text: str = Field(min_length=1, description="The claim document text to read.")


class AssessArgs(BaseModel):
    """Stage 2 input. Every field here must exist on stage 1's ExtractedClaim output.

    Notice this is a strict subset of ExtractedClaim: the assess stage only needs
    what it scores on. The handoff is typed, so the executor (and the contract test)
    catch a missing or renamed field before the pipeline ever runs.
    """

    claim_id: str = Field(description="Carried through from stage 1.")
    claim_type: ClaimType = Field(description="The model-classified claim type from stage 1.")
    claim_amount: float | None = Field(description="The deterministic dollar amount, or None if not found.")
    requires_review: bool = Field(description="Stage 1's deterministic 'a human must look' gate.")
    missing_fields: list[str] = Field(description="Required fields stage 1 could not prove.")


class RecommendArgs(BaseModel):
    """Stage 3 input. Every field here must exist on stage 2's RiskAssessment output."""

    claim_id: str = Field(description="Carried through from stages 1 and 2.")
    claim_type: ClaimType = Field(description="Carried through for the justification prompt.")
    claim_amount: float | None = Field(description="Carried through for the justification prompt.")
    risk_band: RiskBand = Field(description="The deterministic risk band from stage 2.")
    risk_score: float = Field(description="The deterministic risk score from stage 2.")
    requires_review: bool = Field(description="Carried through from stage 1's review gate.")
    risk_factors: list[str] = Field(description="Human-readable reasons behind the risk band.")
