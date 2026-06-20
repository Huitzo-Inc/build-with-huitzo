"""
Module: trade_surveillance.models.output
Description: Typed outputs for screen-trade, split on purpose. ``AlertNarrative`` is the
            ONLY thing the model produces (prose for a compliance analyst). Everything
            load-bearing — which abuse signals fired, the risk score and band, the
            disposition, and the audit record — is deterministic Python the model never
            touches. That split is the regulated-surveillance contract: a model may
            describe an alert, it may never decide whether one fires.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

RiskBand = Literal["low", "medium", "high"]
# clear = no action; review = analyst should look; escalate = route to a compliance officer.
Disposition = Literal["clear", "review", "escalate"]


class Signal(BaseModel):
    """One market-abuse pattern that the deterministic detectors fired. Pure Python."""

    code: str = Field(description="Stable rule code, e.g. 'off_market_price'.")
    label: str = Field(description="Human-readable pattern name, e.g. 'Off-market price'.")
    detail: str = Field(description="Why it fired, with the numbers that triggered it.")
    weight: float = Field(description="Contribution to the risk score, 0-1.")


class AlertNarrative(BaseModel):
    """The slice the model is responsible for: a short analyst-facing narrative.

    This is the schema handed to ``ctx.llm.complete(schema=...)``. The model explains
    the alert that Python already raised, naming the instrument and the flagged
    pattern(s). It does not score, band, or decide the disposition — none of those
    fields are here.
    """

    text: str = Field(
        description="Two or three sentences for a compliance analyst, naming the symbol "
        "and the flagged pattern(s), using only the provided signals. No new findings.",
    )


class SurveillanceAudit(BaseModel):
    """The detailed audit record written for every screen, pass or alert. Pure Python.

    The Policy Card declares ``audit.level: detailed``; this is what that means here.
    A regulated surveillance function lives or dies on its evidence trail, so a cleared
    trade leaves the same record shape as an escalated one."""

    timestamp: str = Field(description="UTC ISO-8601 timestamp of the screen.")
    autonomy: Literal["suggest"] = Field(description="Autonomy level, mirroring the Policy Card.")
    trade_id: str = Field(description="The screened trade's id.")
    symbol: str = Field(description="The screened instrument.")
    risk_score: float = Field(description="Deterministic composite risk score, 0-1.")
    risk_band: RiskBand = Field(description="The deterministic risk band.")
    signals_fired: list[str] = Field(
        default_factory=list, description="Codes of every detector that fired."
    )
    eval_passed: bool = Field(description="Whether the deterministic grounding eval passed.")
    disposition: Disposition = Field(description="The deterministic disposition.")
    escalated: bool = Field(description="Whether the alert was routed to a human.")


class SurveillanceAlert(BaseModel):
    """The full command output: the deterministic verdict, the model's narrative, the
    eval result, and the audit record, with the governance flags up front.

    The model's ``narrative`` is present when an alert fired, but trust it only when
    ``eval_passed``; the ``disposition`` and ``escalated`` flags are Python's and are
    authoritative regardless of what the narrative says.
    """

    trade_id: str = Field(description="The screened trade's id.")
    symbol: str = Field(description="The screened instrument.")
    risk_score: float = Field(description="Deterministic composite risk score, 0-1.")
    risk_band: RiskBand = Field(description="Deterministic risk band: low, medium, or high.")
    signals: list[Signal] = Field(
        default_factory=list, description="Every abuse pattern the detectors fired, with detail."
    )
    narrative: str | None = Field(
        default=None,
        description="The model's analyst narrative for the alert, or null for a clean trade "
        "(no model call is made when nothing fired).",
    )
    eval_passed: bool = Field(description="Did the deterministic grounding eval pass?")
    eval_findings: list[str] = Field(
        default_factory=list, description="Human-readable findings from the eval."
    )
    disposition: Disposition = Field(description="clear, review, or escalate — decided in Python.")
    escalated: bool = Field(description="True when routed to a human compliance officer.")
    audit: SurveillanceAudit = Field(description="The detailed audit record for this screen.")
