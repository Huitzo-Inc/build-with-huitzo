"""Pytest configuration for macro-snapshot.

The tests run fully offline: we hand the command a fake ``ctx`` whose ``http``
and ``llm`` are mocks. That is the standard Huitzo unit-testing pattern, your
deterministic parsing and math are tested without a live API or model, and both
external calls are asserted, not made.
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))


@pytest.fixture()
def mock_ctx() -> MagicMock:
    ctx = MagicMock()
    ctx.http = AsyncMock()
    ctx.llm = AsyncMock()
    ctx.log = MagicMock()
    ctx.command_name = "country-snapshot"
    ctx.namespace = "reef"
    return ctx
