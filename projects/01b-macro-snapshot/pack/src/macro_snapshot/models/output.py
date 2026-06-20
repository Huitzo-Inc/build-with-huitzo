"""
Module: macro_snapshot.models.output
Description: Output models for the country-snapshot command. Two models on
            purpose: the one-field slice the model is asked to write, and the
            full output whose numbers all come from deterministic Python. The
            model never touches a figure; it only narrates the ones it is given.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class MacroSummary(BaseModel):
    """The slice of the result the model is asked to produce.

    This is the schema handed to ``ctx.llm.complete(schema=...)``. The model
    fills exactly this field, validated on the way back. Notice what is *not*
    here: every number, which Python computed and the model only describes.
    """

    summary: str = Field(
        description=(
            "A 2-3 sentence plain-language summary that narrates only the figures "
            "provided in the prompt. No invented numbers."
        ),
    )


class CountrySnapshot(BaseModel):
    """The full command output: deterministic numbers + the model's narration.

    Every numeric field is produced in Python from the World Bank response.
    Only ``summary`` comes from the model, and it only describes these numbers.
    """

    country: str = Field(description="ISO-3166 alpha-3 country code that was requested.")
    indicator: str = Field(description="Friendly indicator name that was requested.")
    latest_value: float | None = Field(
        description="Latest non-null observation value, picked in Python. None if no data.",
    )
    latest_year: str | None = Field(
        description="Year of the latest non-null observation. None if no data.",
    )
    delta_pct: float | None = Field(
        description=(
            "Percent change from the prior available period to the latest, computed "
            "in Python. None if a prior period is unavailable."
        ),
    )
    summary: str = Field(
        description="Plain-language narration of the numbers above, written by the model.",
    )
    source: str = Field(
        default="World Bank",
        description="Where the figures came from.",
    )
