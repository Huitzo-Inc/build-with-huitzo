"""Tests for the seed-document command.

Like the rest of the pack these run fully offline: ``ctx.storage`` is mocked, so we
assert the write happens with the right key and value without touching real storage.
"""

from __future__ import annotations

import pytest

from doc_to_json.commands.seed_document import seed_document
from doc_to_json.models.args import SeedDocumentArgs
from doc_to_json.models.output import SeedResult

_DOC = """Nautilus Mutual Claim Intake Form
Claimant: Mariana Castillo
Policy Number: NM-48201773
Incident Date: 2026-05-09
Claimed Amount: $4,200.00
"""


@pytest.mark.asyncio
async def test_seed_document_writes_text_under_the_id(mock_ctx):
    result = await seed_document(
        SeedDocumentArgs(document_id="claim-00417", text=_DOC), mock_ctx
    )

    # The write goes to storage under the given id, value-first.
    mock_ctx.storage.save.assert_awaited_once_with("claim-00417", _DOC)
    assert isinstance(result, SeedResult)
    assert result.document_id == "claim-00417"
    assert result.characters == len(_DOC)
    assert result.stored is True


@pytest.mark.asyncio
async def test_seed_document_id_is_the_contract_with_extract_claim(mock_ctx):
    # Whatever id you seed under is exactly what extract-claim will read back.
    await seed_document(SeedDocumentArgs(document_id="claim-99", text="hello"), mock_ctx)
    saved_key = mock_ctx.storage.save.await_args.args[0]
    assert saved_key == "claim-99"
