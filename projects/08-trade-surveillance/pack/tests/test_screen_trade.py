"""screen-trade is governed: Python detects + decides, the model only narrates, and the
disposition + audit do not depend on what the model says. All offline."""

from __future__ import annotations

import pytest

from trade_surveillance.commands.screen_trade import screen_trade
from trade_surveillance.models.args import MarketContext, ScreenTradeArgs, Trade
from trade_surveillance.models.output import AlertNarrative, SurveillanceAlert


def _args(**market_kw) -> ScreenTradeArgs:
    trade = Trade(
        trade_id="T-9",
        symbol="ACME",
        side="buy",
        quantity=100,
        price=103.10,
        timestamp="2026-06-19T15:58:30Z",
    )
    market = dict(
        prevailing_bid=100.00,
        prevailing_ask=100.10,
        minutes_to_close=2,
        trader_avg_quantity=100,
        recent_cancel_ratio=0.0,
        own_account_both_sides=False,
    )
    market.update(market_kw)
    return ScreenTradeArgs(trade=trade, market=MarketContext(**market))


def _clean_args() -> ScreenTradeArgs:
    trade = Trade(
        trade_id="T-0",
        symbol="ACME",
        side="buy",
        quantity=100,
        price=100.05,
        timestamp="2026-06-19T11:00:00Z",
    )
    market = MarketContext(
        prevailing_bid=100.00,
        prevailing_ask=100.10,
        minutes_to_close=120,
        trader_avg_quantity=100,
        recent_cancel_ratio=0.0,
    )
    return ScreenTradeArgs(trade=trade, market=market)


@pytest.mark.asyncio
async def test_clean_trade_clears_without_calling_the_model(mock_ctx):
    result = await screen_trade(_clean_args(), mock_ctx)
    assert isinstance(result, SurveillanceAlert)
    assert result.signals == []
    assert result.risk_band == "low"
    assert result.disposition == "clear"
    assert result.escalated is False
    assert result.narrative is None
    # The whole point: a quiet trade never spends a token.
    mock_ctx.llm.complete.assert_not_called()


@pytest.mark.asyncio
async def test_flagged_trade_narrates_evaluates_and_escalates(mock_ctx):
    mock_ctx.llm.complete.return_value = AlertNarrative(
        text="ACME was flagged for an off-market price and marking the close: an aggressive "
        "buy 3% through the mid in the final minutes."
    )
    result = await screen_trade(_args(), mock_ctx)

    assert {"off_market_price", "marking_the_close"} <= {s.code for s in result.signals}
    assert result.risk_band == "high"
    assert result.eval_passed is True
    assert result.disposition == "escalate"
    assert result.escalated is True
    assert result.narrative and "ACME" in result.narrative
    # The model was consulted through a profile, with the schema, never a model name.
    call = mock_ctx.llm.complete.await_args
    assert call.kwargs["profile"] == "default"
    assert call.kwargs["schema"] is AlertNarrative
    assert "model" not in call.kwargs
    # The audit trail records the deterministic verdict.
    assert result.audit.disposition == "escalate"
    assert "off_market_price" in result.audit.signals_fired


@pytest.mark.asyncio
async def test_model_cannot_downgrade_the_disposition(mock_ctx):
    # The model tries to wave it off. Python does not care: a high-risk, grounded alert
    # still escalates. The narrative cannot move the decision.
    mock_ctx.llm.complete.return_value = AlertNarrative(
        text="ACME off-market price looks benign to me; no action needed, safe to clear."
    )
    result = await screen_trade(_args(), mock_ctx)
    assert result.risk_band == "high"
    assert result.disposition == "escalate"
    assert result.escalated is True


@pytest.mark.asyncio
async def test_ungrounded_narrative_fails_eval_and_escalates(mock_ctx):
    # A narrative that names neither the instrument nor a flagged pattern is not trusted.
    mock_ctx.llm.complete.return_value = AlertNarrative(text="Everything looks fine overall.")
    result = await screen_trade(_args(), mock_ctx)
    assert result.eval_passed is False
    assert result.disposition == "escalate"
    assert any("grounding" in f for f in result.eval_findings)


@pytest.mark.asyncio
async def test_medium_band_grounded_goes_to_review_not_escalate(mock_ctx):
    # Only the off-market signal fires (0.35 -> medium): not high, so a grounded
    # narrative routes to an analyst review rather than a human escalation.
    mock_ctx.llm.complete.return_value = AlertNarrative(
        text="ACME printed at an off-market price, 3% away from the prevailing mid."
    )
    result = await screen_trade(_args(minutes_to_close=120), mock_ctx)  # not near the close
    assert {s.code for s in result.signals} == {"off_market_price"}
    assert result.risk_band == "medium"
    assert result.eval_passed is True
    assert result.disposition == "review"
    assert result.escalated is False
