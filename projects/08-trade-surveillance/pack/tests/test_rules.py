"""The deterministic detectors fire (and stay quiet) exactly as documented — no model."""

from __future__ import annotations

from trade_surveillance.models.args import MarketContext, Trade
from trade_surveillance import rules


def _trade(**kw) -> Trade:
    base = dict(
        trade_id="T-1",
        symbol="ACME",
        side="buy",
        quantity=100,
        price=100.05,
        timestamp="2026-06-19T15:00:00Z",
    )
    base.update(kw)
    return Trade(**base)


def _market(**kw) -> MarketContext:
    base = dict(
        prevailing_bid=100.00,
        prevailing_ask=100.10,
        minutes_to_close=120,
        trader_avg_quantity=100,
        recent_cancel_ratio=0.0,
        own_account_both_sides=False,
    )
    base.update(kw)
    return MarketContext(**base)


def test_clean_trade_fires_nothing_and_scores_low():
    signals = rules.detect_signals(_trade(price=100.05), _market())
    assert signals == []
    assert rules.score(signals) == 0.0
    assert rules.band(0.0) == "low"


def test_off_market_price_fires_above_threshold():
    # 3% away from the 100.05 mid.
    s = rules.detect_off_market_price(_trade(price=103.10), _market())
    assert s is not None and s.code == "off_market_price"


def test_marking_the_close_needs_aggression_and_proximity():
    # Aggressive buy at the ask inside the last 5 minutes -> fires.
    assert (
        rules.detect_marking_the_close(_trade(price=100.10), _market(minutes_to_close=2))
        is not None
    )
    # Same trade earlier in the session -> does not fire.
    assert (
        rules.detect_marking_the_close(_trade(price=100.10), _market(minutes_to_close=60)) is None
    )


def test_spoofing_wash_and_size_detectors():
    assert rules.detect_layering_spoofing(_trade(), _market(recent_cancel_ratio=0.9)) is not None
    assert rules.detect_layering_spoofing(_trade(), _market(recent_cancel_ratio=0.5)) is None
    assert rules.detect_wash_trade(_trade(), _market(own_account_both_sides=True)) is not None
    assert (
        rules.detect_size_anomaly(_trade(quantity=2000), _market(trader_avg_quantity=100))
        is not None
    )
    assert rules.detect_size_anomaly(_trade(quantity=300), _market(trader_avg_quantity=100)) is None


def test_score_caps_at_one_and_bands_are_predictable():
    # off_market (0.35) + marking_close (0.30) = 0.65 -> high
    signals = rules.detect_signals(_trade(price=103.10), _market(minutes_to_close=2))
    codes = {s.code for s in signals}
    assert {"off_market_price", "marking_the_close"} <= codes
    assert rules.band(rules.score(signals)) == "high"
    # Single off-market signal (0.35) -> medium
    assert rules.band(0.35) == "medium"
    assert rules.band(0.19) == "low"
    # Everything fires -> capped at 1.0, never above.
    everything = rules.detect_signals(
        _trade(price=103.10, quantity=5000),
        _market(
            minutes_to_close=1,
            recent_cancel_ratio=0.95,
            own_account_both_sides=True,
            trader_avg_quantity=100,
        ),
    )
    assert rules.score(everything) == 1.0
