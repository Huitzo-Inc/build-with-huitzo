"""Tests for the hello command."""

from __future__ import annotations

import pytest

from hello_pack.commands.hello import hello
from hello_pack.models.args import HelloArgs
from hello_pack.models.output import ModelInsight, TextInsight


@pytest.mark.asyncio
async def test_returns_typed_insight(mock_ctx):
    mock_ctx.llm.complete.return_value = ModelInsight(
        summary="A friendly greeting.",
        sentiment="positive",
        key_points=["greeting", "friendly"],
    )

    result = await hello(HelloArgs(text="Hello there, lovely day"), mock_ctx)

    assert isinstance(result, TextInsight)
    assert result.summary == "A friendly greeting."
    assert result.sentiment == "positive"
    assert result.key_points == ["greeting", "friendly"]


@pytest.mark.asyncio
async def test_word_count_is_deterministic_python_not_the_model(mock_ctx):
    # The model returns no word count; Python always computes it.
    mock_ctx.llm.complete.return_value = ModelInsight(
        summary="x", sentiment="neutral", key_points=[]
    )

    result = await hello(HelloArgs(text="one two three four five"), mock_ctx)

    assert result.word_count == 5


@pytest.mark.asyncio
async def test_calls_a_profile_never_a_model_name(mock_ctx):
    mock_ctx.llm.complete.return_value = ModelInsight(
        summary="x", sentiment="neutral", key_points=[]
    )

    await hello(HelloArgs(text="one two three"), mock_ctx)

    mock_ctx.llm.complete.assert_awaited_once()
    call = mock_ctx.llm.complete.await_args
    assert call.kwargs["profile"] == "default"  # a capability profile
    assert call.kwargs["schema"] is ModelInsight  # structured output
    assert "model" not in call.kwargs  # a pack must never name a model
