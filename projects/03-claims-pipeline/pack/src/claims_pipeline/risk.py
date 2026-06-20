"""
Module: claims_pipeline.risk
Description: The deterministic risk model for stage 2, kept apart from the command so
            the scoring rules are auditable in one place. Nothing here calls a model.
            A reader can predict the risk band of any claim by hand, which is exactly
            the property an insurer's compliance team needs.
"""

from __future__ import annotations

from claims_pipeline.models.output import ClaimType, RiskAssessment, RiskBand

# Fixed, documented inputs. Each claim type carries a base risk weight; the dollar
# amount is normalized against a high-value threshold; a missing-data claim gets a
# penalty because an incomplete claim is, itself, a risk. Weights are chosen so the
# score stays on a 0-1 scale.
_TYPE_WEIGHT: dict[ClaimType, float] = {
    "auto": 0.40,
    "property": 0.50,
    "health": 0.60,
    "liability": 0.70,
    "other": 0.50,
}
_HIGH_VALUE_THRESHOLD = 250_000.0  # a claim at or above this maxes out the amount factor
_REVIEW_PENALTY = 0.15            # added when stage 1 flagged the claim for review
_UNKNOWN_AMOUNT_FACTOR = 0.5     # an unproven amount is treated as moderate, not zero

_W_TYPE = 0.5
_W_AMOUNT = 0.4

_BAND_MEDIUM = 0.40
_BAND_HIGH = 0.70


def _amount_factor(claim_amount: float | None) -> float:
    """Normalize the dollar amount to 0-1. Unknown amount is moderate, not free."""
    if claim_amount is None:
        return _UNKNOWN_AMOUNT_FACTOR
    return min(max(claim_amount, 0.0) / _HIGH_VALUE_THRESHOLD, 1.0)


def _band_for(score: float) -> RiskBand:
    """Map a score to a band. The thresholds are fixed and documented."""
    if score >= _BAND_HIGH:
        return "high"
    if score >= _BAND_MEDIUM:
        return "medium"
    return "low"


def assess(
    claim_id: str,
    claim_type: ClaimType,
    claim_amount: float | None,
    requires_review: bool,
    missing_fields: list[str],
) -> RiskAssessment:
    """Score a claim's risk from the fixed rules and explain every contribution.

    score = 0.5 * type_weight + 0.4 * amount_factor + (0.15 if requires_review)

    The score is clamped to 1.0. The returned ``risk_factors`` spell out each
    contribution so the band is never a black box.
    """
    type_weight = _TYPE_WEIGHT[claim_type]
    amount_factor = _amount_factor(claim_amount)
    review_penalty = _REVIEW_PENALTY if requires_review else 0.0

    score = round(min(1.0, _W_TYPE * type_weight + _W_AMOUNT * amount_factor + review_penalty), 4)
    band = _band_for(score)

    factors: list[str] = [
        f"claim_type '{claim_type}' carries a base weight of {type_weight}.",
    ]
    if claim_amount is None:
        factors.append("amount could not be proven, treated as moderate risk.")
    else:
        pct = round(amount_factor * 100)
        factors.append(f"amount ${claim_amount:,.0f} is {pct}% of the ${_HIGH_VALUE_THRESHOLD:,.0f} high-value mark.")
    if requires_review:
        factors.append(
            f"stage 1 flagged the claim for review ({len(missing_fields)} required field(s) missing); "
            f"+{_REVIEW_PENALTY} penalty applied."
        )

    return RiskAssessment(
        claim_id=claim_id,
        claim_type=claim_type,
        claim_amount=claim_amount,
        requires_review=requires_review,
        risk_score=score,
        risk_band=band,
        risk_factors=factors,
    )
