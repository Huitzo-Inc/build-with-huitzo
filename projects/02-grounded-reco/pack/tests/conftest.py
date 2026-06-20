"""Pytest configuration for grounded-reco.

The tests run fully offline. We hand the command a fake ``ctx`` whose ``llm`` is a
mock, so the deterministic decision, the eval guardrail, and the audit record are
all exercised without a live model. The model call is asserted, not made, and
because Python owns the decision, we can prove the pick does not depend on what the
model returns.
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
    ctx.command_name = "recommend"
    ctx.namespace = "reef"
    return ctx
