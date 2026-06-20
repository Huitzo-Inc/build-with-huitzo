# Tier 2: grounded-reco

> Read this in [Español](./README.es.md).

A governed recommendation pack. It picks the best option from a candidate set, where a wrong or stale recommendation is expensive. The decision is made by deterministic Python. The model only explains the decision. A deterministic eval checks the result before it ever reaches a user, and a detailed audit record is written for every run. This is the rung where a Huitzo pack stops looking like a thin wrapper around a model and starts looking like governed software that happens to use a model.

**You will learn:** how to keep the decision in Python and confine the model to prose; how to add an automatic eval guardrail that withholds a bad answer before release; how to produce an audit record for every generation; and how the Policy Card declares autonomy, audit level, and escalation so the platform enforces them.

**Time:** about fifteen minutes.

## Prerequisites

- Python 3.11+
- The [Huitzo CLI](https://github.com/Huitzo-Inc/huitzo-launcher) (optional for this rung, used to run against a real Hub)
- The [`hello-pack`](../00-hello-pack/) tier first, if you have not done it. This pack assumes you know the `@command` decorator, typed args/output, and the profile-not-a-model-name rule.

## The scenario

You have a set of candidate options (think suppliers, allocations, vendors) and you need to recommend one. Each candidate carries a few normalized numbers and a date saying when its data was last refreshed. The cost of a wrong or out-of-date pick is real, so a confident-sounding answer built on stale numbers is worse than no answer at all.

## Run it

```bash
cd pack
pip install -e ".[dev]"
pytest                  # offline tests for this pack (what CI runs)
```

You should see nine passing tests, with no network and no model. They do not just check that the command works; they encode the governance contract: the pick is deterministic, a stale or ungrounded result is withheld and escalated, and every run is audited.

**See the model-swap "aha" yourself, offline:**

```bash
python -m grounded_reco.demo_model_swap
```

This runs the *real* `recommend` command under two different stub "models" and prints them side by side. The pick, the eval gate, and the audit come out **byte-identical** — only the one-sentence justification differs. That is the model-agnostic + governance story you cannot get from a raw LLM-SDK wrapper, shown in five seconds with no Hub. (The same invariant is locked in CI by `tests/test_model_swap_demo.py`.)

## What is inside

```
pack/
  huitzo.yaml                      the manifest: identity, one permission, the Policy Card
  pyproject.toml                   dependencies and the command entry point
  src/grounded_reco/
    commands/recommend.py          the command: decide -> justify -> eval -> audit
    evals.py                       the deterministic decision logic and the eval guardrail
    models/args.py                 typed input (Candidate, RecommendArgs)
    models/output.py               typed output (Justification, ScoredCandidate, AuditRecord, Recommendation)
  tests/test_recommend.py          offline tests that encode the governance contract
```

## Why this is not a thin LLM wrapper

A thin wrapper asks the model to choose, then returns whatever the model said. This pack does the opposite. Four properties make it governed, and each one is something a wrapper does not have.

### 1. The decision is deterministic. The model does not choose.

`evals.py` scores every candidate with a fixed, documented formula and ranks them. The top of the ranking is the pick. There is no model in that path.

```python
# score = 0.30 * (1 - cost) + 0.40 * quality + 0.30 * reliability
ranked = score_candidates(args.candidates)   # pure Python
pick = choose(ranked)                         # pick = ranked[0]
```

Because the score is fixed weights over the candidate numbers, you can predict the pick by hand, and it is reproducible: the same input always yields the same pick. One of the tests proves this directly by changing what the model returns (including a justification that says "pick kelp-llc instead") and asserting the pick never moves.

### 2. The model is asked only to explain, and the explanation is checked.

After Python has chosen, the model is given the pick and the numbers and asked for a one or two sentence justification. It is told, explicitly, not to propose a different option. The objective free-text is passed inside `<objective>...</objective>` tags with an instruction to treat it as data, not as instructions: a basic prompt-injection guard for untrusted input.

```python
justification = await ctx.llm.complete(
    prompt=prompt,            # contains the decided pick + the ranking + tagged objective
    profile="default",        # a capability profile, never a model name
    schema=Justification,     # structured output: the model returns prose, nothing else
)
```

The model returns prose. It cannot return a different pick, because the pick is not one of the fields it fills.

### 3. An automatic eval guards the result before it reaches a user.

This is the heart of the tier. After the model responds and before anything is returned, `run_eval` applies two deterministic checks:

- **Freshness.** The chosen pick carries an `as_of` date. If that data is older than `freshness_days` (default 30), or undated, or dated in the future, the eval fails. A stale recommendation is the classic silent failure: it looks confident and is wrong because the inputs moved underneath it.
- **Grounding.** The model's justification must mention the chosen pick by name. If it does not, the prose is not grounded in the decision (it may have wandered to a different option or be generic filler), and the eval fails.

When the eval fails, the result is **withheld** and **escalated**:

```python
withheld = not eval_passed
escalated = not eval_passed
```

A withheld result is never presented as a confident recommendation. The `pick` and `justification` may still be attached so a human reviewer can see exactly what was generated, but the `withheld` and `escalated` flags are the signal: do not act on this; a person needs to look. That is how the eval blocks a bad recommendation before it reaches a user, instead of after.

### 4. Every generation is audited.

The Policy Card declares `audit.level: detailed`. The command honors that by building an `AuditRecord` for every run (timestamp, autonomy level, candidate count, the pick, the eval outcome, and every eval finding), returning it in the output and logging it. A passing run and a withheld run leave the same evidence trail, so the failures are not invisible.

```python
audit = AuditRecord(
    timestamp=...,
    autonomy="suggest",
    candidate_count=len(args.candidates),
    pick=pick.name,
    eval_passed=eval_passed,
    eval_findings=eval_findings,
    escalated=escalated,
)
ctx.log.info(...)   # passing run
ctx.log.warning(...)  # withheld run
```

## The Policy Card

Open `pack/huitzo.yaml` and find the `policy` block. This is not documentation; the platform enforces it, and the manifest loader cross-checks that the pack's `permissions` are a subset of `policy.allowed_actions`.

```yaml
policy:
  autonomy: suggest                 # the pack proposes; a human disposes
  allowed_actions:
    - llm:complete
  data_scope:
    scope: tenant
  escalation:
    requires_human_approval:
      - recommend                   # this command escalates to a person
  audit:
    level: detailed                 # every generation is audited in detail
```

`autonomy: suggest` says this pack does not act on its own. `escalation` names `recommend`, so a withheld result has a defined destination: human review. `audit.level: detailed` is the contract the `AuditRecord` fulfills. The code and the Policy Card say the same thing, and the platform holds the pack to it.

## The "swap the model" moment

Like every Huitzo pack, this one declares a capability requirement, never a model name:

```yaml
services:
  llm:
    required: true
    requirements:
      min_context: 8000
      capabilities:
        - structured_output
```

The deterministic decision, the eval, and the audit do not change when the model changes. Swap the `default` profile from a cloud model to a local one and the governance is identical, because none of it depends on the model.

## Run it for real

> Re-scope it first: the example uses the `@reef` org, which you do not own. Change `namespace:` in `huitzo.yaml` to an org you own and run `huitzo pack sync` before publishing. See [Run on your own Hub](../../README.md#run-on-your-own-hub).

Once you have early access to a Hub:

```bash
huitzo login
huitzo run @your-org/grounded-reco/recommend --args '{
  "candidates": [
    {"name": "reef-prime", "cost": 0.1, "quality": 0.9, "reliability": 0.95, "as_of": "2026-06-01"},
    {"name": "coral-co",   "cost": 0.5, "quality": 0.7, "reliability": 0.6,  "as_of": "2026-06-10"}
  ],
  "objective": "favor reliability",
  "freshness_days": 30
}'
```

Change one `as_of` to a date well in the past and run it again: the pick is the same, but the result comes back `withheld` and `escalated`, with a freshness finding in the audit. That is the guardrail doing its job.

## Next

You now have the governed pattern: deterministic decision, eval guardrail, audit, Policy Card. Higher tiers add storage, files, and multi-step pipelines on top of exactly this spine.
