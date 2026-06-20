"""
Module: grounded_reco.evals
Description: The deterministic decision logic and the eval guardrail, kept apart from
            the command so the governance contract is auditable in one place. Nothing
            here calls a model. Python scores, ranks, chooses, and then judges the
            result before it is allowed to reach a user.

These two responsibilities are the heart of why this is a governed pack and not a
thin LLM wrapper:

  - score_candidates / choose: the model never decides. Python does.
  - run_eval: every generation is checked against fixed rules before release.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

from grounded_reco.models.args import Candidate
from grounded_reco.models.output import ScoredCandidate

# Composite scoring weights. Documented and fixed: a reader can predict the pick
# by hand. cost is inverted (cheaper is better); quality and reliability are
# rewarded directly. Weights sum to 1.0 so the score stays on a 0-1 scale.
_W_COST = 0.30
_W_QUALITY = 0.40
_W_RELIABILITY = 0.30


def score_one(candidate: Candidate) -> float:
    """The transparent scoring formula, applied to a single candidate.

    score = 0.30 * (1 - cost) + 0.40 * quality + 0.30 * reliability

    All three inputs are on a 0-1 scale, so the result is on a 0-1 scale. There is
    no model in this function and there never will be: this is the decision.
    """
    return round(
        _W_COST * (1.0 - candidate.cost)
        + _W_QUALITY * candidate.quality
        + _W_RELIABILITY * candidate.reliability,
        6,
    )


def score_candidates(candidates: list[Candidate]) -> list[ScoredCandidate]:
    """Score every candidate and return them ranked best-first.

    Ties break deterministically by name, so the same input always yields the same
    ordering, a property the determinism test relies on.
    """
    scored = [
        ScoredCandidate(name=c.name, score=score_one(c), as_of=c.as_of) for c in candidates
    ]
    scored.sort(key=lambda s: (-s.score, s.name))
    return scored


def choose(ranked: list[ScoredCandidate]) -> ScoredCandidate:
    """The pick is the top of the deterministic ranking. Full stop.

    Caller guarantees a non-empty list (args validation requires >= 1 candidate).
    """
    return ranked[0]


def _parse_as_of(value: str) -> date | None:
    """Parse an ISO date defensively. A malformed date is itself an eval finding,
    not an exception that crashes the run."""
    try:
        return date.fromisoformat(value.strip())
    except (ValueError, AttributeError):
        return None


def check_freshness(pick: ScoredCandidate, freshness_days: int, today: date) -> str | None:
    """Freshness guardrail. Returns a finding string if the pick's data is too old
    (or undated/future-dated), else None.

    A stale pick is the classic silent failure of a recommendation system: the
    answer looks confident and is wrong because the inputs moved. Here it is caught
    before release.
    """
    as_of = _parse_as_of(pick.as_of)
    if as_of is None:
        return f"freshness: pick '{pick.name}' has an unparseable as_of date '{pick.as_of}'."
    if as_of > today:
        return f"freshness: pick '{pick.name}' is dated in the future ({pick.as_of})."
    age_days = (today - as_of).days
    if age_days > freshness_days:
        return (
            f"freshness: pick '{pick.name}' data is {age_days} days old, "
            f"older than the {freshness_days}-day threshold."
        )
    return None


def check_grounding(pick: ScoredCandidate, justification_text: str) -> str | None:
    """Grounding guardrail. The model's justification must reference the pick by
    name; if it does not, the prose is not grounded in the decision and is flagged.

    This is a cheap, deterministic consistency check: it catches a justification
    that wandered off to a different option or that was generic boilerplate.
    """
    if pick.name.lower() not in justification_text.lower():
        return (
            f"grounding: justification does not mention the chosen pick '{pick.name}'; "
            "it may not be grounded in the deterministic decision."
        )
    return None


def run_eval(
    pick: ScoredCandidate,
    justification_text: str,
    freshness_days: int,
    today: date | None = None,
) -> tuple[bool, list[str]]:
    """Run the full deterministic eval over a chosen pick and its justification.

    Returns (eval_passed, findings). findings always records what was checked, so a
    passing run leaves a positive audit trail too, not just failures.
    """
    today = today or datetime.now(UTC).date()
    findings: list[str] = []

    freshness_finding = check_freshness(pick, freshness_days, today)
    if freshness_finding is not None:
        findings.append(freshness_finding)
    else:
        findings.append(f"freshness: OK, pick '{pick.name}' within {freshness_days} days.")

    grounding_finding = check_grounding(pick, justification_text)
    if grounding_finding is not None:
        findings.append(grounding_finding)
    else:
        findings.append("grounding: OK, justification references the pick.")

    eval_passed = freshness_finding is None and grounding_finding is None
    return eval_passed, findings
