"""
Module: trade_surveillance.models.args
Description: Typed inputs for the screen-trade command. The SDK validates these before
            the command runs, so a malformed trade or market snapshot never reaches the
            deterministic detectors. Everything the surveillance rules need is typed and
            in range — the rules can rely on it, and an auditor can read exactly what was
            considered.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Side = Literal["buy", "sell"]


class Trade(BaseModel):
    """A single execution to screen. These are facts about what happened."""

    trade_id: str = Field(min_length=1, description="Unique id for the execution.")
    symbol: str = Field(min_length=1, description="The instrument ticker, e.g. 'ACME'.")
    side: Side = Field(description="'buy' or 'sell'.")
    quantity: int = Field(gt=0, description="Number of shares/contracts executed.")
    price: float = Field(gt=0, description="Execution price.")
    timestamp: str = Field(description="ISO-8601 execution time, e.g. '2026-06-19T15:58:30Z'.")


class MarketContext(BaseModel):
    """The surrounding facts the detectors compare the trade against. All deterministic
    inputs — a real deployment sources these from the order book and the trader's
    history; here they are passed in so the exercise runs offline and reproducibly."""

    prevailing_bid: float = Field(gt=0, description="Best bid at execution time.")
    prevailing_ask: float = Field(gt=0, description="Best ask at execution time.")
    minutes_to_close: int = Field(
        ge=0, description="Minutes between the execution and the session close."
    )
    trader_avg_quantity: int = Field(
        gt=0, description="The trader's recent average order size, for the size-anomaly rule."
    )
    recent_cancel_ratio: float = Field(
        ge=0.0,
        le=1.0,
        description="Fraction of the trader's recent orders that were canceled before "
        "filling (a layering/spoofing signal). 0 = never cancels, 1 = always cancels.",
    )
    own_account_both_sides: bool = Field(
        default=False,
        description="True when the same beneficial owner sits on both sides around this "
        "execution (a wash-trade signal).",
    )


class ScreenTradeArgs(BaseModel):
    """Input to screen-trade: one execution plus the market context to judge it against."""

    trade: Trade
    market: MarketContext
