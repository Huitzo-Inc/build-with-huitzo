"""Pytest configuration for trade-surveillance.

The tests run fully offline. We hand the command a fake ``ctx`` whose ``llm`` is a
mock, so the deterministic detection, the eval guardrail, the disposition, and the
audit are all exercised without a live model. Because Python owns the verdict, we can
prove the disposition does not depend on what the model narrates.
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
    ctx.command_name = "screen-trade"
    ctx.namespace = "reef"
    return ctx
