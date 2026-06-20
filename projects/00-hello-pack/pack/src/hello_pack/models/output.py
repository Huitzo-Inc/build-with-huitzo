"""
Module: hello_pack.models.output
Description: Output models for the hello command. Two models on purpose: the part
             the model is responsible for, and the deterministic field Python adds.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Sentiment = Literal["positive", "neutral", "negative"]


class ModelInsight(BaseModel):
    """The slice of the result the model is asked to produce.

    This is the schema handed to ``ctx.llm.complete(schema=...)``. The model
    fills exactly these fields, validated on the way back. Notice what is *not*
    here: anything Python can compute reliably on its own.
    """

    summary: str = Field(description="One-sentence, plain-language summary of the text.")
    sentiment: Sentiment = Field(description="Overall sentiment of the text.")
    key_points: list[str] = Field(
        default_factory=list,
        description="Up to three short key points found in the text.",
    )


class TextInsight(ModelInsight):
    """The full command output: model insight + one deterministic Python fact."""

    word_count: int = Field(
        description="Number of words, computed in Python, never asked of the model.",
    )
