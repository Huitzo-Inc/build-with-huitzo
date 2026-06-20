"""
Module: inbox_triage.models.output
Description: Output models for the triage-email command. Two models on purpose: the
             part the model is responsible for, and the deterministic fields Python adds.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Category = Literal["billing", "support", "sales", "complaint", "other"]
Confidence = Literal["low", "medium", "high"]
Urgency = Literal["low", "medium", "high"]


class EmailTriage(BaseModel):
    """The slice of the result the model is asked to produce.

    This is the schema handed to ``ctx.llm.complete(schema=...)``. The model
    fills exactly these fields, validated on the way back. Notice what is *not*
    here: urgency, the matched rules, and the human-review flag, Python owns
    those, because Python can decide them reliably and they must not depend on
    anything an email might try to talk the model into.
    """

    category: Category = Field(
        description="The single best category for this email.",
    )
    confidence: Confidence = Field(
        description="How confident the classification is.",
    )
    draft_reply: str = Field(
        description="A professional draft reply for a human to review and send. Never sent automatically.",
    )


class TriageResult(EmailTriage):
    """The full command output: model classification + reply, plus Python's deterministic triage."""

    urgency: Urgency = Field(
        description="Urgency floor computed in Python from keyword rules, never asked of the model.",
    )
    matched_rules: list[str] = Field(
        default_factory=list,
        description="Names of the deterministic keyword rules that fired, in Python.",
    )
    needs_human: bool = Field(
        description="True when urgency is high or the category is a complaint. A person must look before any reply goes out.",
    )
