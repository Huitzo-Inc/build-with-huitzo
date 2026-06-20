"""The model-swap "aha" is RUNNABLE and self-verifying OFFLINE — no Hub, no model.

This locks the differentiator in CI: the SAME governed `recommend` run under two
different stub "models" produces a byte-identical decision + eval + audit, and only
the justification prose differs. If that ever stops being true, the build goes red.
"""

from __future__ import annotations

import pytest

from grounded_reco.demo_model_swap import StubModel, governed_signature, run_under


@pytest.mark.asyncio
async def test_governance_is_model_independent_only_prose_differs():
    a = await run_under(StubModel(name="claude-sonnet-4-6", style="measured"))
    b = await run_under(StubModel(name="gpt-4o", style="terse"))

    # The model-independent governance (pick, score, ranking, eval, audit) is identical.
    assert governed_signature(a) == governed_signature(b)
    # The deterministic winner and a passing eval gate — decided by Python, not the model.
    assert a.pick == "NorthAPI"
    assert a.eval_passed is True
    assert a.withheld is False and a.escalated is False
    # Only the prose differs — and both ground themselves in the Python-chosen pick.
    assert a.justification != b.justification
    assert a.justification and "NorthAPI" in a.justification
    assert b.justification and "NorthAPI" in b.justification
