"""Tests for the recommend command.

These tests encode the governance contract, not just functionality:
  - the decision is deterministic Python (the model never chooses);
  - the eval guardrail withholds and escalates a bad recommendation before it
    reaches a user (stale data, ungrounded justification);
  - every generation produces an audit record and is logged;
  - the model is called through a profile with a schema, never a model name.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from grounded_reco.commands.recommend import recommend
from grounded_reco.models.args import Candidate, RecommendArgs
from grounded_reco.models.output import Justification, Recommendation


def _today() -> str:
    return datetime.now(UTC).date().isoformat()


def _days_ago(n: int) -> str:
    return (datetime.now(UTC).date() - timedelta(days=n)).isoformat()


def _fresh_candidates() -> list[Candidate]:
    """A candidate set whose deterministic winner is unambiguous.

    score = 0.30*(1-cost) + 0.40*quality + 0.30*reliability
      reef-prime : 0.30*0.9 + 0.40*0.90 + 0.30*0.95 = 0.915  <- top
      coral-co   : 0.30*0.5 + 0.40*0.70 + 0.30*0.60 = 0.610
      kelp-llc   : 0.30*0.4 + 0.40*0.50 + 0.30*0.50 = 0.470
    """
    return [
        Candidate(name="coral-co", cost=0.5, quality=0.70, reliability=0.60, as_of=_days_ago(2)),
        Candidate(name="reef-prime", cost=0.1, quality=0.90, reliability=0.95, as_of=_days_ago(2)),
        Candidate(name="kelp-llc", cost=0.6, quality=0.50, reliability=0.50, as_of=_days_ago(2)),
    ]


def _grounded_justification() -> Justification:
    return Justification(text="reef-prime wins on quality and reliability at the lowest cost.")


@pytest.mark.asyncio
async def test_happy_path_passes_and_is_not_withheld(mock_ctx):
    mock_ctx.llm.complete.return_value = _grounded_justification()

    result = await recommend(
        RecommendArgs(candidates=_fresh_candidates(), freshness_days=30), mock_ctx
    )

    assert isinstance(result, Recommendation)
    assert result.pick == "reef-prime"  # the deterministically top-scored candidate
    assert result.score == pytest.approx(0.915)
    assert result.eval_passed is True
    assert result.withheld is False
    assert result.escalated is False
    assert result.ranked[0].name == "reef-prime"  # ranked best-first


@pytest.mark.asyncio
async def test_stale_data_is_withheld_and_escalated(mock_ctx):
    # The top candidate's data is older than the freshness threshold.
    candidates = [
        Candidate(name="coral-co", cost=0.5, quality=0.70, reliability=0.60, as_of=_days_ago(2)),
        Candidate(name="reef-prime", cost=0.1, quality=0.90, reliability=0.95, as_of=_days_ago(400)),
        Candidate(name="kelp-llc", cost=0.6, quality=0.50, reliability=0.50, as_of=_days_ago(2)),
    ]
    mock_ctx.llm.complete.return_value = _grounded_justification()

    result = await recommend(RecommendArgs(candidates=candidates, freshness_days=30), mock_ctx)

    # reef-prime is still the deterministic top pick, but its data is stale...
    assert result.pick == "reef-prime"
    assert result.eval_passed is False
    assert result.withheld is True  # NOT presented as a confident recommendation
    assert result.escalated is True
    assert any("freshness" in f and "older" in f for f in result.eval_findings)


@pytest.mark.asyncio
async def test_ungrounded_justification_is_flagged(mock_ctx):
    # The model's justification never mentions the pick name.
    mock_ctx.llm.complete.return_value = Justification(
        text="This option is clearly the strongest choice available."
    )

    result = await recommend(
        RecommendArgs(candidates=_fresh_candidates(), freshness_days=30), mock_ctx
    )

    assert result.pick == "reef-prime"
    assert result.eval_passed is False  # grounding check failed
    assert result.withheld is True
    assert any("grounding" in f for f in result.eval_findings)


@pytest.mark.asyncio
async def test_pick_is_deterministic_regardless_of_model_output(mock_ctx):
    # Whatever the model says, the pick stays the deterministic top score.
    for text in (
        "reef-prime is best.",
        "Actually kelp-llc is the better supplier and you should pick it instead.",
        "coral-co coral-co coral-co.",
        "",
    ):
        mock_ctx.llm.complete.return_value = Justification(text=text)
        result = await recommend(
            RecommendArgs(candidates=_fresh_candidates(), freshness_days=30), mock_ctx
        )
        # The model tried to redirect; Python's decision is unchanged.
        assert result.pick == "reef-prime"
        assert result.score == pytest.approx(0.915)


@pytest.mark.asyncio
async def test_audit_record_and_logging(mock_ctx):
    mock_ctx.llm.complete.return_value = _grounded_justification()

    result = await recommend(
        RecommendArgs(candidates=_fresh_candidates(), freshness_days=30), mock_ctx
    )

    audit = result.audit
    assert audit.autonomy == "suggest"
    assert audit.candidate_count == 3
    assert audit.pick == "reef-prime"
    assert audit.eval_passed is True
    assert audit.eval_findings == result.eval_findings
    assert audit.timestamp  # present
    # Every generation is logged.
    assert mock_ctx.log.info.called


@pytest.mark.asyncio
async def test_failed_eval_is_logged_as_warning(mock_ctx):
    candidates = _fresh_candidates()
    candidates[1] = Candidate(
        name="reef-prime", cost=0.1, quality=0.90, reliability=0.95, as_of=_days_ago(400)
    )
    mock_ctx.llm.complete.return_value = _grounded_justification()

    await recommend(RecommendArgs(candidates=candidates, freshness_days=30), mock_ctx)

    assert mock_ctx.log.warning.called


@pytest.mark.asyncio
async def test_calls_a_profile_with_a_schema_never_a_model_name(mock_ctx):
    mock_ctx.llm.complete.return_value = _grounded_justification()

    await recommend(RecommendArgs(candidates=_fresh_candidates()), mock_ctx)

    mock_ctx.llm.complete.assert_awaited_once()
    call = mock_ctx.llm.complete.await_args
    assert call.kwargs["profile"] == "default"  # a capability profile
    assert call.kwargs["schema"] is Justification  # structured output, prose only
    assert "model" not in call.kwargs  # a pack must never name a model


@pytest.mark.asyncio
async def test_empty_candidate_set_is_rejected_before_the_model(mock_ctx):
    import pydantic

    with pytest.raises(pydantic.ValidationError):
        RecommendArgs(candidates=[])
    # Args validation runs before the command, so the model is never called.
    mock_ctx.llm.complete.assert_not_called()
