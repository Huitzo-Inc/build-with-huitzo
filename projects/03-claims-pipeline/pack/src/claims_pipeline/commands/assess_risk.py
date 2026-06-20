"""
Module: claims_pipeline.commands.assess_risk
Description: Stage 2 of the pipeline. Pure deterministic risk scoring, no model at all.
            This stage exists to make a point: not every step in an AI pipeline is an
            AI step. The risk band that drives the recommendation is a fact about fixed
            rules, so it is computed in Python and is fully reproducible and auditable.

            Its input (AssessArgs) is a strict subset of stage 1's output, and its
            output (RiskAssessment) carries forward exactly what stage 3 needs.
"""

from __future__ import annotations

from huitzo_sdk import Context, command

from claims_pipeline import risk
from claims_pipeline.models.args import AssessArgs
from claims_pipeline.models.output import RiskAssessment


@command("assess-risk", namespace="reef", timeout=30)
async def assess_risk(args: AssessArgs, ctx: Context) -> RiskAssessment:
    """Score the claim's risk from fixed rules. No model: this is a deterministic decision."""
    assessment = risk.assess(
        claim_id=args.claim_id,
        claim_type=args.claim_type,
        claim_amount=args.claim_amount,
        requires_review=args.requires_review,
        missing_fields=args.missing_fields,
    )
    ctx.log.info(
        f"assess-risk: id={assessment.claim_id} score={assessment.risk_score} band={assessment.risk_band}"
    )
    return assessment
