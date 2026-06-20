"""
Module: grounded_reco.models.output
Description: Output models for the recommend command. Separated on purpose into the
            part the model produces (Justification), the part Python computes
            (ScoredCandidate, AuditRecord), and the assembled result (Recommendation).
            The model is asked for exactly one thing: prose. Everything load-bearing
            (the pick, the score, the eval outcome, the audit) is Python's.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Justification(BaseModel):
    """The slice of the result the model is responsible for.

    This is the schema handed to ``ctx.llm.complete(schema=...)``. The model
    writes a short, factual justification for the pick that Python already chose.
    It does not choose, score, or rank. Notice what is not here: the pick name,
    the score, the ranking: all of that is decided in Python before this call.
    """

    text: str = Field(
        description="One or two sentences justifying the given pick using only the "
        "provided numbers. Must name the pick. Must not propose a different option.",
    )


class ScoredCandidate(BaseModel):
    """One candidate after deterministic scoring. Pure Python output."""

    name: str = Field(description="The candidate's name.")
    score: float = Field(description="Deterministic composite score, 0-1. Higher is better.")
    as_of: str = Field(description="The candidate's data date, carried through for the eval.")


class AuditRecord(BaseModel):
    """The detailed audit record written for every generation. Pure Python output.

    The Policy Card declares ``audit.level: detailed``; this is what that means in
    practice. It is returned in the output and also logged via ``ctx.log.info``,
    so a withheld recommendation leaves the same evidence trail as a passing one.
    """

    timestamp: str = Field(description="UTC ISO-8601 timestamp of the generation.")
    autonomy: Literal["suggest"] = Field(
        description="Autonomy level under which this ran, mirroring the Policy Card.",
    )
    candidate_count: int = Field(description="How many candidates were scored.")
    pick: str | None = Field(description="The deterministically chosen pick, or None if withheld.")
    eval_passed: bool = Field(description="Whether the deterministic eval passed.")
    eval_findings: list[str] = Field(
        default_factory=list,
        description="Every finding the eval recorded, pass or fail.",
    )
    escalated: bool = Field(description="Whether the result was escalated for human review.")


class Recommendation(BaseModel):
    """The full command output: the deterministic decision, the model's prose, the
    eval verdict, and the audit record, with the governance flags front and center.

    When the eval fails, ``withheld`` and ``escalated`` are True; ``pick`` and
    ``justification`` may still be present for the human reviewer, but the flags
    make clear this is NOT a confident answer. When the eval passes, both flags
    are False and the recommendation stands on its own.
    """

    pick: str | None = Field(description="The chosen candidate, or None if no input.")
    score: float | None = Field(description="The pick's deterministic score, or None.")
    ranked: list[ScoredCandidate] = Field(
        default_factory=list,
        description="All candidates, ranked best-first by deterministic score.",
    )
    justification: str | None = Field(
        default=None,
        description="The model's justification for the pick. Present even when withheld, "
        "so a reviewer can see what was generated; trust it only when eval_passed.",
    )
    eval_passed: bool = Field(description="Did the deterministic eval pass?")
    eval_findings: list[str] = Field(
        default_factory=list,
        description="Human-readable findings from the eval (freshness, grounding).",
    )
    withheld: bool = Field(
        description="True when the eval failed: the result is NOT presented as a "
        "confident recommendation.",
    )
    escalated: bool = Field(
        description="True when the result was routed to a human (per the Policy Card).",
    )
    audit: AuditRecord = Field(description="The detailed audit record for this generation.")
