"""Pytest configuration for claims-pipeline.

The command tests run fully offline: we hand each command a fake ``ctx`` whose
``llm`` is a mock. Deterministic logic (extraction, risk scoring, the decision,
the eval) is tested without a live model; the model call is asserted, not made.
The risk stage calls no model at all, so its test asserts the model is untouched.
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
    ctx.namespace = "reef"
    return ctx
