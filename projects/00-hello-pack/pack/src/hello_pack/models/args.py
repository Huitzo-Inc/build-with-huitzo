"""
Module: hello_pack.models.args
Description: Pydantic argument model for the hello command. The SDK validates these
            args before your command runs, so bad input never reaches your logic.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class HelloArgs(BaseModel):
    text: str = Field(
        min_length=1,
        description="The text to analyze. Anything from a sentence to a few paragraphs.",
    )
