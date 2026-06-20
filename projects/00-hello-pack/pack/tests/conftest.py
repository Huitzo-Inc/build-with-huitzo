"""Pytest configuration for hello-pack.

The tests run fully offline: we hand the command a fake ``ctx`` whose ``llm``
is a mock. That is the standard Huitzo unit-testing pattern: your deterministic
logic is tested without a live model, and the model call is asserted, not made.
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
    ctx.llm = AsyncMock()
    ctx.log = MagicMock()
    ctx.command_name = "hello"
    ctx.namespace = "reef"
    return ctx
