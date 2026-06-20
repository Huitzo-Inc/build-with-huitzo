"""
Module: daily_digest.models.args
Description: Pydantic argument model for the daily-digest command. The SDK validates
            these args before your command runs, so bad input never reaches your logic.
            The CSV arrives as text on purpose: it keeps the pack fully offline-testable.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class DigestArgs(BaseModel):
    sales_csv: str = Field(
        min_length=1,
        description="Raw CSV text with columns date,category,amount",
    )
