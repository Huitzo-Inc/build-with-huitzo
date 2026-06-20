"""
Module: trade_surveillance.rules
Description: The deterministic market-abuse detectors. Every signal here is a fixed,
            documented rule over the trade and the market context — no model, fully
            reproducible, and predictable by hand. This is the part a regulator audits
            and a compliance officer must be able to defend. The model never runs here.

            Each detector returns a Signal (with the numbers that triggered it) or None.
            The composite score is a simple weighted sum of the fired signals' weights,
            capped at 1.0; the band thresholds are constants. Tune the thresholds/weights
            to a desk's risk appetite — but keep them here, in readable Python, not in a
            prompt.
"""

from __future__ import annotations

from trade_surveillance.models.args import MarketContext, Trade
from trade_surveillance.models.output import RiskBand, Signal

# --- Thresholds (documented, auditable; a desk tunes these to its risk appetite) ---
_OFF_MARKET_PCT = 0.02  # execution >2% away from the mid is "off-market"
_MARKING_CLOSE_MINUTES = 5  # aggressive prints inside the last 5 minutes draw scrutiny
_SPOOFING_CANCEL_RATIO = 0.80  # canceling >=80% of recent orders is a layering signal
_SIZE_ANOMALY_MULTIPLE = 10.0  # >=10x the trader's average size is anomalous

# --- Signal weights (contribution to the 0-1 composite score) ---
_WEIGHTS = {
    "off_market_price": 0.35,
    "marking_the_close": 0.30,
    "layering_spoofing": 0.30,
    "wash_trade": 0.40,
    "size_anomaly": 0.20,
}

# --- Band thresholds over the composite score ---
_HIGH_BAND = 0.50
_MEDIUM_BAND = 0.20


def _mid(market: MarketContext) -> float:
    return (market.prevailing_bid + market.prevailing_ask) / 2.0


def detect_off_market_price(trade: Trade, market: MarketContext) -> Signal | None:
    """Fire when the execution price is far from the prevailing mid."""
    mid = _mid(market)
    deviation = abs(trade.price - mid) / mid
    if deviation > _OFF_MARKET_PCT:
        return Signal(
            code="off_market_price",
            label="Off-market price",
            detail=f"executed at {trade.price} vs mid {mid:.4f} "
            f"({deviation * 100:.1f}% away, threshold {_OFF_MARKET_PCT * 100:.0f}%).",
            weight=_WEIGHTS["off_market_price"],
        )
    return None


def detect_marking_the_close(trade: Trade, market: MarketContext) -> Signal | None:
    """Fire on an aggressive print in the final minutes (a marking-the-close signal).

    'Aggressive' = a buy at or above the ask, or a sell at or below the bid: the trade
    reaches across the spread to move the closing print rather than rest passively.
    """
    if market.minutes_to_close > _MARKING_CLOSE_MINUTES:
        return None
    aggressive = (trade.side == "buy" and trade.price >= market.prevailing_ask) or (
        trade.side == "sell" and trade.price <= market.prevailing_bid
    )
    if aggressive:
        return Signal(
            code="marking_the_close",
            label="Marking the close",
            detail=f"aggressive {trade.side} at {trade.price} with "
            f"{market.minutes_to_close} min to close (threshold {_MARKING_CLOSE_MINUTES}).",
            weight=_WEIGHTS["marking_the_close"],
        )
    return None


def detect_layering_spoofing(trade: Trade, market: MarketContext) -> Signal | None:
    """Fire when the trader cancels an unusually high fraction of recent orders."""
    if market.recent_cancel_ratio >= _SPOOFING_CANCEL_RATIO:
        return Signal(
            code="layering_spoofing",
            label="Layering / spoofing",
            detail=f"recent cancel ratio {market.recent_cancel_ratio:.0%} "
            f"(threshold {_SPOOFING_CANCEL_RATIO:.0%}).",
            weight=_WEIGHTS["layering_spoofing"],
        )
    return None


def detect_wash_trade(trade: Trade, market: MarketContext) -> Signal | None:
    """Fire when the same beneficial owner sits on both sides (no change in ownership)."""
    if market.own_account_both_sides:
        return Signal(
            code="wash_trade",
            label="Wash trade",
            detail="same beneficial owner on both sides; no genuine change of ownership.",
            weight=_WEIGHTS["wash_trade"],
        )
    return None


def detect_size_anomaly(trade: Trade, market: MarketContext) -> Signal | None:
    """Fire when the trade is far larger than the trader's recent average size."""
    if trade.quantity >= _SIZE_ANOMALY_MULTIPLE * market.trader_avg_quantity:
        multiple = trade.quantity / market.trader_avg_quantity
        return Signal(
            code="size_anomaly",
            label="Size anomaly",
            detail=f"{trade.quantity} is {multiple:.0f}x the trader's average "
            f"{market.trader_avg_quantity} (threshold {_SIZE_ANOMALY_MULTIPLE:.0f}x).",
            weight=_WEIGHTS["size_anomaly"],
        )
    return None


_DETECTORS = (
    detect_off_market_price,
    detect_marking_the_close,
    detect_layering_spoofing,
    detect_wash_trade,
    detect_size_anomaly,
)


def detect_signals(trade: Trade, market: MarketContext) -> list[Signal]:
    """Run every detector in order and return the signals that fired."""
    return [s for detector in _DETECTORS if (s := detector(trade, market)) is not None]


def score(signals: list[Signal]) -> float:
    """Composite risk score: the summed weights of fired signals, capped at 1.0."""
    return round(min(1.0, sum(s.weight for s in signals)), 4)


def band(risk_score: float) -> RiskBand:
    """Map a composite score to a band. Fixed thresholds, predictable by hand."""
    if risk_score >= _HIGH_BAND:
        return "high"
    if risk_score >= _MEDIUM_BAND:
        return "medium"
    return "low"
