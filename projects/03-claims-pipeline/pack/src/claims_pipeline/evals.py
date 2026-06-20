"""
Module: claims_pipeline.evals
Description: The deterministic decision and the eval guardrail for stage 3, kept apart
            from the command so the governance contract is auditable in one place.
            Python chooses the action; the model only justifies it; this eval checks
            that justification before it reaches a user. Nothing here calls a model.
"""

from __future__ import annotations

from claims_pipeline.models.output import Action, RiskBand


def decide_action(risk_band: RiskBand, requires_review: bool) -> Action:
    """Choose the action from the risk band and the review gate. Full stop, in Python.

    - high risk            -> escalate (a human must decide)
    - medium, or flagged   -> manual_review
    - low and clean        -> auto_approve

    The model never makes this call; it only explains the call after it is made.
    """
    if risk_band == "high":
        return "escalate"
    if risk_band == "medium" or requires_review:
        return "manual_review"
    return "auto_approve"


def check_grounding(claim_id: str, justification_text: str) -> str | None:
    """Grounding guardrail. The model's justification must mention the claim id; if
    it does not, the prose is not clearly about this claim and is flagged.

    A cheap, deterministic consistency check: it catches a justification that drifted
    to a different claim or that is generic boilerplate.
    """
    if claim_id.lower() not in justification_text.lower():
        return (
            f"grounding: justification does not mention claim '{claim_id}'; "
            "it may not be grounded in this claim."
        )
    return None


def run_eval(claim_id: str, justification_text: str) -> tuple[bool, list[str]]:
    """Run the deterministic eval over a recommendation's justification.

    Returns (eval_passed, findings). findings always records what was checked, so a
    passing run leaves a positive audit trail too, not just failures.
    """
    findings: list[str] = []

    grounding_finding = check_grounding(claim_id, justification_text)
    if grounding_finding is not None:
        findings.append(grounding_finding)
    else:
        findings.append(f"grounding: OK, justification references claim '{claim_id}'.")

    eval_passed = grounding_finding is None
    return eval_passed, findings
