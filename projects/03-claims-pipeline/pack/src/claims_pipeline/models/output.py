"""
Module: claims_pipeline.models.output
Description: Typed output models, one per stage, plus the model slices the LLM fills.
            These are the *producing* side of the pipeline contract. Each stage's
            output carries forward exactly what the next stage's input
            (`models/args.py`) needs. Everything load-bearing (ids, amounts, the
            risk band, the action, the audit) is Python's; the model is confined to
            the two small slices that genuinely need language (ClaimFields,
            Justification).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ClaimType = Literal["auto", "property", "health", "liability", "other"]
RiskBand = Literal["low", "medium", "high"]
Action = Literal["auto_approve", "manual_review", "escalate"]


# --- Stage 1: extract ---------------------------------------------------------

class ClaimFields(BaseModel):
    """The slice of stage 1 the model is responsible for.

    Handed to ``ctx.llm.complete(schema=...)``. The model classifies and writes a
    summary. It is not asked for the policy number, amount, or date: those are
    proven in Python by regex, because they have a fixed shape.
    """

    claimant_name: str | None = Field(
        default=None, description="The claimant's name if clearly stated, else null."
    )
    claim_type: ClaimType = Field(description="The claim category, classified by the model.")
    summary: str = Field(description="A two to three sentence plain-language summary of the claim.")


class ExtractedClaim(BaseModel):
    """Stage 1 output. The model slice plus the deterministic fields Python proves,
    plus the review gate. This is what stage 2 receives."""

    claim_id: str = Field(description="Carried through unchanged.")
    claimant_name: str | None = Field(description="From the model.")
    claim_type: ClaimType = Field(description="From the model.")
    policy_number: str | None = Field(description="Proven by Python regex, or None.")
    incident_date: str | None = Field(description="Proven by Python regex (ISO date), or None.")
    claim_amount: float | None = Field(description="Proven by Python regex (dollar amount), or None.")
    summary: str = Field(description="From the model.")
    missing_fields: list[str] = Field(description="Required fields Python could not prove.")
    requires_review: bool = Field(description="Python's gate: True when any required field is missing.")


# --- Stage 2: assess risk (no model) ------------------------------------------

class RiskAssessment(BaseModel):
    """Stage 2 output. Pure Python: a transparent risk score and band, with the
    reasons. No model touched this. This is what stage 3 receives."""

    claim_id: str = Field(description="Carried through unchanged.")
    claim_type: ClaimType = Field(description="Carried through for stage 3's prompt.")
    claim_amount: float | None = Field(description="Carried through for stage 3's prompt.")
    requires_review: bool = Field(description="Carried through from stage 1's review gate.")
    risk_score: float = Field(description="Deterministic composite risk, 0-1. Higher is riskier.")
    risk_band: RiskBand = Field(description="low / medium / high, derived from the score.")
    risk_factors: list[str] = Field(description="Human-readable reasons behind the score.")


# --- Stage 3: recommend an action ---------------------------------------------

class Justification(BaseModel):
    """The slice of stage 3 the model is responsible for: prose only.

    The action is already decided in Python. The model explains it and must name
    the claim so the grounding eval can confirm the prose is about this claim.
    """

    text: str = Field(
        description="One or two sentences justifying the already-decided action. Must mention the claim id.",
    )


class ActionAudit(BaseModel):
    """The detailed audit record for stage 3, written for every recommendation."""

    timestamp: str = Field(description="UTC ISO-8601 timestamp of the recommendation.")
    claim_id: str = Field(description="The claim this record is about.")
    action: Action = Field(description="The deterministically chosen action.")
    risk_band: RiskBand = Field(description="The risk band the action was based on.")
    eval_passed: bool = Field(description="Whether the deterministic eval passed.")
    eval_findings: list[str] = Field(description="Every finding the eval recorded, pass or fail.")
    escalated: bool = Field(description="Whether the result was escalated for human review.")


class ActionRecommendation(BaseModel):
    """Stage 3 output: the final pipeline result. The decision and the audit are
    Python's; the rationale is the model's, trusted only when the eval passed."""

    claim_id: str = Field(description="Carried through unchanged.")
    action: Action = Field(description="The recommended action, decided in Python.")
    rationale: str = Field(description="The model's justification. Trust it only when eval_passed.")
    eval_passed: bool = Field(description="Did the deterministic eval pass?")
    eval_findings: list[str] = Field(description="Human-readable findings from the eval.")
    escalated: bool = Field(description="True when escalated to a human (per the Policy Card).")
    audit: ActionAudit = Field(description="The detailed audit record for this recommendation.")
