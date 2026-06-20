"""
Module: doc_to_json.commands.seed_document
Description: The write half of the doc-to-json exercise. extract-claim reads a
            document from storage by id; this command puts one there. Keeping the
            seed as a pack command (rather than a one-off script) means the whole
            exercise runs through the same `huitzo run` path and the same Policy
            Card, and it teaches the `storage:write` permission alongside the
            `storage:read` that extract-claim already uses.
"""

from __future__ import annotations

from huitzo_sdk import Context, command

from doc_to_json.models.args import SeedDocumentArgs
from doc_to_json.models.output import SeedResult


@command("seed-document", namespace="reef", timeout=30)
async def seed_document(args: SeedDocumentArgs, ctx: Context) -> SeedResult:
    """Write a claim document into the key-value store under an id, for extract-claim to read."""
    # One write, through the one interface, behind the storage:write permission.
    # The id is the contract between the two commands: seed under it here, read by
    # it in extract-claim. Storage stays the source of truth; the blob never rides
    # in an extract-claim request.
    await ctx.storage.save(args.document_id, args.text)
    ctx.log.info(f"seed-document: id={args.document_id} chars={len(args.text)}")
    return SeedResult(document_id=args.document_id, characters=len(args.text))
