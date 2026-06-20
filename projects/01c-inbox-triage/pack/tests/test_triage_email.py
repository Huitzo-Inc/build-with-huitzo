"""Tests for the triage-email command.

The deterministic triage (urgency, matched rules, needs_human) is decided in Python,
so these tests pin it down independently of whatever the mocked model returns.
"""

from __future__ import annotations

import pytest

from inbox_triage.commands.triage_email import triage_email
from inbox_triage.models.args import TriageArgs
from inbox_triage.models.output import EmailTriage, TriageResult


@pytest.mark.asyncio
async def test_urgent_refund_is_high_and_needs_human(mock_ctx):
    # The model could say anything; Python's keyword rules decide urgency here.
    mock_ctx.llm.complete.return_value = EmailTriage(
        category="billing",
        confidence="high",
        draft_reply="We are sorry for the trouble and will process your refund.",
    )

    result = await triage_email(
        TriageArgs(
            subject="URGENT: I want a refund now",
            body="My order never arrived and I demand my money back immediately.",
        ),
        mock_ctx,
    )

    assert isinstance(result, TriageResult)
    assert result.urgency == "high"
    assert result.matched_rules  # at least one rule fired
    assert result.needs_human is True


@pytest.mark.asyncio
async def test_plain_order_status_is_medium_and_no_human_needed(mock_ctx):
    # "where is my order" / "tracking" are medium-urgency rules, not high.
    mock_ctx.llm.complete.return_value = EmailTriage(
        category="support",
        confidence="medium",
        draft_reply="Thanks for reaching out, here is your tracking update.",
    )

    result = await triage_email(
        TriageArgs(
            subject="Where is my order?",
            body="Hi, just checking on the tracking for my recent purchase.",
        ),
        mock_ctx,
    )

    assert result.urgency == "medium"
    assert result.needs_human is False
    # The category is the model's call, passed straight through.
    assert result.category == "support"


@pytest.mark.asyncio
async def test_calls_a_profile_never_a_model_name(mock_ctx):
    mock_ctx.llm.complete.return_value = EmailTriage(
        category="other",
        confidence="low",
        draft_reply="Thanks for your message.",
    )

    await triage_email(
        TriageArgs(subject="Hello", body="Just saying hi."),
        mock_ctx,
    )

    mock_ctx.llm.complete.assert_awaited_once()
    call = mock_ctx.llm.complete.await_args
    assert call.kwargs["profile"] == "default"  # a capability profile
    assert call.kwargs["schema"] is EmailTriage  # structured output
    assert "model" not in call.kwargs  # a pack must never name a model


@pytest.mark.asyncio
async def test_complaint_category_forces_human_even_when_low_urgency(mock_ctx):
    # No urgency keywords fire, so Python's floor is "low", but the model calls it a
    # complaint, and a complaint always needs a person regardless of urgency.
    mock_ctx.llm.complete.return_value = EmailTriage(
        category="complaint",
        confidence="medium",
        draft_reply="We are sorry to hear about your experience.",
    )

    result = await triage_email(
        TriageArgs(
            subject="A bit disappointed",
            body="The packaging could have been nicer for the price.",
        ),
        mock_ctx,
    )

    assert result.urgency == "low"
    assert result.matched_rules == []
    assert result.needs_human is True
