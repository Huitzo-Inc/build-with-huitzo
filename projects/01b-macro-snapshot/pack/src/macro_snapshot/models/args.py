"""
Module: macro_snapshot.models.args
Description: Pydantic argument model for the country-snapshot command. The SDK
            validates these args before your command runs, so bad input never
            reaches your logic. The country and indicator are closed Literal
            sets, so a typo is a validation error, never a bad API call.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# Closed set of ISO-3166 alpha-3 country codes this demo supports. Keeping it a
# Literal means an unsupported country is rejected by validation, not at runtime.
Country = Literal["USA", "COL", "MEX", "CHL", "PER"]

# Friendly indicator names. The mapping to World Bank codes lives in the command,
# so the public argument stays human-readable and the API code stays internal.
Indicator = Literal["gdp", "gdp_growth", "inflation"]


class SnapshotArgs(BaseModel):
    country: Country = Field(
        description="ISO-3166 alpha-3 country code to pull the indicator for.",
    )
    indicator: Indicator = Field(
        default="gdp",
        description="Which macro indicator to fetch. Mapped to a World Bank code in Python.",
    )
