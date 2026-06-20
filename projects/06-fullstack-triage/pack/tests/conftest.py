"""Pytest configuration for expense-triage. Offline: the model is mocked, so the
deterministic rules are tested without a live model and the model call is asserted,
not made."""

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
    ctx.namespace = "reef"
    return ctx
