"""
Module: trade_surveillance.evals
Description: The deterministic guardrail and disposition logic, run AFTER the model and
            BEFORE anything reaches an analyst. The model's narrative is checked for
            grounding (does it actually name the instrument and a flagged pattern?), and
            the disposition (clear / review / escalate) is decided in Python from the
            risk band and the eval result. The model never sets the disposition.
"""

from __future__ import annotations

from trade_surveillance.models.output import Disposition, RiskBand, Signal


def check_grounding(symbol: str, signals: list[Signal], narrative_text: str) -> str | None:
    """Return a finding string if the narrative is ungrounded, else None.

    Grounded means: it names the instrument AND references at least one pattern that
    actually fired. An ungrounded narrative may have drifted or be generic filler, so
    it must not be trusted — the caller escalates instead.
    """
    text = narrative_text.lower()
    if symbol.lower() not in text:
        return f"grounding: narrative does not name the instrument '{symbol}'."
    if not any(s.label.lower() in text or s.code.replace("_", " ") in text for s in signals):
        return "grounding: narrative references none of the flagged patterns."
    return None


def run_eval(symbol: str, signals: list[Signal], narrative_text: str) -> tuple[bool, list[str]]:
    """Run the deterministic eval over an alert narrative. Returns (passed, findings).

    Findings always records what was checked, so a passing screen leaves a positive
    audit trail too — not only failures.
    """
    findings: list[str] = []
    grounding = check_grounding(symbol, signals, narrative_text)
    if grounding is not None:
        findings.append(grounding)
    else:
        findings.append("grounding: OK, narrative names the instrument and a flagged pattern.")
    return grounding is None, findings


def decide_disposition(risk_band: RiskBand, eval_passed: bool) -> Disposition:
    """Decide the disposition in Python. High risk, or any ungrounded narrative, routes
    to a human (escalate); medium risk goes to an analyst (review); low risk clears.

    An ungrounded narrative never silently clears: if the model's account of a flagged
    trade cannot be trusted, a person looks at it.
    """
    if risk_band == "high" or not eval_passed:
        return "escalate"
    if risk_band == "medium":
        return "review"
    return "clear"
