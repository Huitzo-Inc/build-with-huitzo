"""
Module: daily_digest.models.output
Description: Output models for the daily-digest command. The split is the whole point of
             the rung: every number and every flagged anomaly is computed in Python, and
             the model is asked for exactly one thing -- the prose that narrates them.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Anomaly(BaseModel):
    """One day the deterministic series flagged as out of pattern.

    Python decides this -- never the model. The date, the figures, and the reason
    are all produced by the anomaly-detection logic so the flag is reproducible.
    """

    date: str = Field(description="The day that was flagged, as it appeared in the CSV.")
    amount: float = Field(description="That day's actual total sales.")
    expected: float = Field(description="The expected total (mean of the other days).")
    reason: str = Field(description="Plain reason the day was flagged, written by Python.")


class DigestNarrative(BaseModel):
    """The slice of the result the model is asked to produce.

    This is the schema handed to ``ctx.llm.complete(schema=...)``. The model writes
    one thing -- a short, friendly digest grounded on numbers Python already computed.
    Notice what is *not* here: any number, any anomaly decision.
    """

    summary: str = Field(
        description=(
            "A short, friendly plain-language digest of the day, grounded only on the "
            "figures and anomalies provided. No new numbers, no invented trends."
        )
    )


class DailyDigest(BaseModel):
    """The full command output: every figure from Python, only ``summary`` from the model."""

    total_sales: float = Field(
        description="Sum of all valid rows, computed in Python -- never asked of the model.",
    )
    top_category: str = Field(
        description="Category with the highest total, computed in Python.",
    )
    day_count: int = Field(
        description="Number of distinct days found in the data, computed in Python.",
    )
    rows_skipped: int = Field(
        description="Count of malformed rows skipped while parsing, computed in Python.",
    )
    anomalies: list[Anomaly] = Field(
        default_factory=list,
        description="Days flagged out of pattern by Python -- the model never decides these.",
    )
    summary: str = Field(
        description="The model's plain-language digest, grounded on the figures above.",
    )
