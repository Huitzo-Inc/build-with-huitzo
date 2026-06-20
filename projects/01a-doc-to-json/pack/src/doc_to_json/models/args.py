"""
Module: doc_to_json.models.args
Description: Pydantic argument model for the extract-claim command. The SDK validates
            these args before your command runs, so bad input never reaches your logic.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ExtractClaimArgs(BaseModel):
    document_id: str = Field(
        min_length=1,
        description="Storage id of the claim document to read. The pack reads the text by id; the document is never inlined in the args.",
    )


class SeedDocumentArgs(BaseModel):
    """Args for the seed-document command: write a claim document into storage by id.

    This is the companion to extract-claim. extract-claim reads a document by id; a
    document has to get into storage first. seed-document is the write half, so the
    exercise is self-contained: seed a document, then extract from it by the same id.
    """

    document_id: str = Field(
        min_length=1,
        description="Storage id to write the document under. Pass this same id to extract-claim.",
    )
    text: str = Field(
        min_length=1,
        description="The raw claim document text to store. extract-claim reads this back by id.",
    )
