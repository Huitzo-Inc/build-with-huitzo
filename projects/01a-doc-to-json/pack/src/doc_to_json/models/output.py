"""
Module: doc_to_json.models.output
Description: Output models for the extract-claim command. Two models on purpose: the
             part the model is responsible for (judgement), and the deterministic
             fields Python adds (which required fields are missing, and whether the
             record needs a human).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# The closed set of claim types the model is allowed to classify into. A Literal,
# not a free string, so the classification is validated on the way back.
ClaimType = Literal["auto", "property", "liability", "medical", "other"]


class ClaimExtraction(BaseModel):
    """The slice of the result the model is asked to produce.

    This is the schema handed to ``ctx.llm.complete(schema=...)``. The model fills
    exactly these fields, validated on the way back. The fields here either need
    judgement (a name buried in prose, a classification, a written summary) or are
    confirmed by the model after Python's first pass. Optional fields are ``None``
    when the model cannot find them.
    """

    claimant_name: str | None = Field(
        default=None,
        description="Full name of the person filing the claim, or null if not stated.",
    )
    policy_number: str | None = Field(
        default=None,
        description="Policy number as written in the document, or null if absent.",
    )
    incident_date: str | None = Field(
        default=None,
        description="Date the incident occurred, in ISO YYYY-MM-DD form, or null if absent.",
    )
    claim_amount: str | None = Field(
        default=None,
        description="Claimed dollar amount as written (for example '$4,200.00'), or null if absent.",
    )
    claim_type: ClaimType = Field(
        description="Classification of the claim into one of the allowed categories.",
    )
    summary: str = Field(
        description="A two to three sentence plain-language summary of the claim.",
    )


class SeedResult(BaseModel):
    """The seed-document result: confirmation that a document was written to storage.

    No model is involved here; this is a deterministic storage write. The result
    echoes the id you read back with and how many characters were stored.
    """

    document_id: str = Field(description="Storage id the document was written under.")
    characters: int = Field(description="Number of characters stored, for a quick sanity check.")
    stored: bool = Field(default=True, description="Always true on success; the write either lands or raises.")


class ClaimRecord(ClaimExtraction):
    """The full command output: the model's extraction plus two deterministic facts.

    Python adds ``missing_fields`` (the required fields its own regex pass could not
    find) and ``requires_review`` (true when anything required is missing). Neither
    is ever asked of the model: a deterministic gate decides what a human must see.
    """

    missing_fields: list[str] = Field(
        default_factory=list,
        description="Required fields Python could not extract deterministically. Computed in code, never asked of the model.",
    )
    requires_review: bool = Field(
        description="True when any required field is missing. A deterministic gate, not a model opinion.",
    )
