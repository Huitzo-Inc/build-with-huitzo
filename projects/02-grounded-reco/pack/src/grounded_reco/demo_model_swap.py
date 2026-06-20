"""
Module: grounded_reco.demo_model_swap
Description: The model-swap "aha", made RUNNABLE offline — no Hub, no network, no API key.

    It runs the REAL `recommend` command twice — once under a "Claude-style" stub
    model, once under a "GPT-style" stub — and prints them side by side. The pick,
    the score, the ranking, the eval gate, and the audit record come out
    byte-identical, because they are deterministic Python the model never touches.
    Only the one-sentence justification differs, because that is the one thing the
    model writes. That is the whole value proposition you cannot get from a raw
    Anthropic-SDK-plus-Pydantic wrapper: swap the model, keep the governed decision
    and the audit — and prove it in five seconds without leaving your laptop.

Run it:
    cd projects/02-grounded-reco/pack
    pip install -e ".[dev]"
    python -m grounded_reco.demo_model_swap
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from typing import Any

from grounded_reco.commands.recommend import recommend
from grounded_reco.models.args import Candidate, RecommendArgs
from grounded_reco.models.output import Justification, Recommendation

# The pick name is handed to the model in the prompt ("Chosen pick (decided, do not
# change): <name> (score ...)"). A real model reads it and writes prose naming it;
# our stubs do the same, so the deterministic grounding eval passes for both.
_PICK_RE = re.compile(r"Chosen pick \(decided, do not change\): (.*?) \(score")


@dataclass
class StubModel:
    """A fake LLM provider. It writes model-flavored prose that names the
    Python-chosen pick — exactly what the contract asks of a real model, and
    nothing more. It cannot change the decision because it is never asked to."""

    name: str
    style: str  # "measured" or "terse" — just to make the prose visibly differ

    async def complete(self, *, prompt: str, profile: str, schema: type[Any]) -> Any:
        match = _PICK_RE.search(prompt)
        pick = match.group(1) if match else "the top candidate"
        if self.style == "measured":
            text = (
                f"{pick} earns the highest composite score here, edging out the field on "
                f"the balance of reliability and cost, so it is the soundest choice for "
                f"this objective."
            )
        else:
            text = f"Pick {pick}: best overall cost/quality/reliability trade-off for the goal."
        # Honor the schema the same way the real backend does: a validated instance.
        return schema(text=text)


class _Log:
    """A no-op logger so the real command's ctx.log.info/warning calls just work."""

    def info(self, *_a: object, **_k: object) -> None: ...
    def warning(self, *_a: object, **_k: object) -> None: ...


@dataclass
class _Ctx:
    """The minimal slice of Context that `recommend` actually uses: an llm + a log."""

    llm: StubModel
    log: _Log = field(default_factory=_Log)


# A realistic candidate set for a regulated healthcare client choosing a vendor.
_ARGS = RecommendArgs(
    objective="Choose the vendor that best balances reliability and cost for a regulated healthcare client.",
    freshness_days=3650,
    candidates=[
        Candidate(name="NorthAPI", cost=0.30, quality=0.80, reliability=0.95, as_of="2026-06-10"),
        Candidate(name="BudgetStream", cost=0.10, quality=0.55, reliability=0.60, as_of="2026-06-12"),
        Candidate(name="PremiumCloud", cost=0.85, quality=0.92, reliability=0.90, as_of="2026-06-01"),
    ],
)


async def run_under(model: StubModel, args: RecommendArgs = _ARGS) -> Recommendation:
    """Run the REAL recommend command with the given stub model as ctx.llm."""
    return await recommend(args, _Ctx(llm=model))  # type: ignore[arg-type]


def governed_signature(rec: Recommendation) -> dict[str, Any]:
    """The model-INDEPENDENT part of the result: everything except the prose and the
    wall-clock timestamp. If two models produce the same signature, the governance
    is provably model-agnostic — the decision did not depend on the model."""
    return {
        "pick": rec.pick,
        "score": rec.score,
        "ranked": [(c.name, c.score) for c in rec.ranked],
        "eval_passed": rec.eval_passed,
        "eval_findings": rec.eval_findings,
        "withheld": rec.withheld,
        "escalated": rec.escalated,
        "audit": rec.audit.model_dump(exclude={"timestamp"}),
    }


async def main() -> None:
    claude = StubModel(name="claude-sonnet-4-6", style="measured")
    gpt = StubModel(name="gpt-4o", style="terse")

    a = await run_under(claude)
    b = await run_under(gpt)

    same = governed_signature(a) == governed_signature(b)

    print("=" * 72)
    print("SAME governed pack. SWAP the model. Offline, no Hub.")
    print("=" * 72)
    for model, rec in ((claude, a), (gpt, b)):
        print(f"\n--- model = {model.name} ---")
        print(f"  pick            : {rec.pick}   (score {rec.score})")
        print(f"  ranked          : {[ (c.name, c.score) for c in rec.ranked ]}")
        print(f"  eval_passed     : {rec.eval_passed}")
        print(f"  eval_findings   : {rec.eval_findings}")
        print(f"  withheld        : {rec.withheld}    escalated: {rec.escalated}")
        print(f"  audit.autonomy  : {rec.audit.autonomy}   audit.pick: {rec.audit.pick}")
        print(f"  justification   : {rec.justification!r}")

    print("\n" + "-" * 72)
    print(f"Governed decision + audit identical across both models : {same}")
    print("Only the justification prose differs                    : "
          f"{a.justification != b.justification}")
    print("-" * 72)
    print(
        "\nThat is the difference from a raw Anthropic-SDK + Pydantic wrapper: the\n"
        "decision, the eval gate, and the audit are deterministic Python the model\n"
        "cannot move, so your client is never locked to one vendor and the\n"
        "governance never changes when the model does. Shown, not claimed."
    )
    # Self-check so the demo fails loudly if the invariant ever breaks.
    assert same, "Governance is NOT model-independent — the decision changed with the model!"
    assert a.justification != b.justification, "Stubs should produce visibly different prose."


if __name__ == "__main__":
    asyncio.run(main())
