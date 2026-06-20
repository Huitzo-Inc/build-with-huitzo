# Tier 3: claims-pipeline

> Read this in [Español](./README.es.md).

Nautilus Mutual processes insurance claims all day. One claim has to be read, scored for risk, and routed to the right outcome: auto-approve the small clean ones, send the borderline ones to a human, escalate the risky ones. This pack does that as a **pipeline**: three small commands, composed in order, with the platform type-checking the handoff between every step.

This is the first rung where you stop writing one command and start composing several. The one idea to carry out of here: **a workflow on Huitzo is declarative data the executor validates, not glue code you maintain by hand.** You declare the stages in `huitzo.yaml`; each stage is an ordinary `@command` you can test and run on its own.

> **Read this as a real deliverable, not a toy.** This is the *shape* of the regulated-client solution you build on Huitzo and resell: a deterministic decision at every gate, a model confined to bounded prose an eval checks, a full audit record per run, a Policy Card the platform enforces — model-agnostic and self-hosted, so your client is never locked to a vendor and their claims never leave their boundary. Swap "insurance claim" for prior-auth, KYC, or loan adjudication and the skeleton does not change. That portability is the business: learn it once here, ship it to every regulated client.

**You will learn:** how to declare a pipeline in the manifest, how to keep each stage independently testable, how the typed handoff between stages is enforced before anything runs, and the reminder that **not every step in an AI pipeline is an AI step** (the risk stage calls no model at all).

**Time:** about thirty minutes.

## Prerequisites

- Python 3.11+
- You have done [Tier 1](../01a-doc-to-json) and [Tier 2](../02-grounded-reco). This pack reuses both patterns: stage 1 is doc-to-json's extraction, stage 3 is grounded-reco's govern-then-explain.
- The [Huitzo CLI](https://github.com/Huitzo-Inc/huitzo-launcher) (optional here, used to run the pipeline against a real Hub)

## Run it

```bash
cd pack
pip install -e ".[dev]"
pytest                  # offline tests for this pack (what CI runs)
```

You should see nineteen passing tests. They run with no network and no model. Most verify the three stages in isolation; one file, `test_pipeline_contract.py`, loads the real `huitzo.yaml` and proves the pipeline is wired correctly. That is the test that matters most, and it is explained below.

## What is inside

```
pack/
  huitzo.yaml                          the manifest, including the pipelines: block
  pyproject.toml                       dependencies and the three command entry points
  src/claims_pipeline/
    commands/extract_claim.py          stage 1: read the claim, prove fields, classify
    commands/assess_risk.py            stage 2: score risk in pure Python, no model
    commands/recommend_action.py       stage 3: decide, justify, eval, audit
    risk.py                            the deterministic risk model (kept apart, auditable)
    evals.py                           the decision + grounding eval (kept apart, auditable)
    models/args.py                     typed input, one model per stage (the consuming side)
    models/output.py                   typed output, one model per stage (the producing side)
  tests/
    test_extract_claim.py              stage 1 offline tests
    test_assess_risk.py                stage 2 offline tests (asserts the model is never called)
    test_recommend_action.py           stage 3 offline tests
    test_pipeline_contract.py          loads the manifest and proves the handoff is sound
```

## A workflow is data, not glue

Open `pack/huitzo.yaml` and find the `pipelines:` block:

```yaml
pipelines:
  score-claim:
    description: "Extract a claim, assess its risk, and recommend an action, type-checked at every handoff."
    timeout: 120
    error_strategy: fail_fast
    stages:
      - name: extract
        command: "claims-pipeline:extract-claim"
      - name: assess
        command: "claims-pipeline:assess-risk"
      - name: recommend
        command: "claims-pipeline:recommend-action"
```

That is the whole pipeline. There is no orchestration code: the platform reads this block, runs the three commands in order, and feeds each one's output into the next one's input. `error_strategy: fail_fast` means a failed stage halts the run and reports which stage failed, rather than passing bad data downstream. Because the stages are just commands, the same three functions you test below run unchanged inside the pipeline.

## Three commands, type-checked at every handoff

Each stage has a typed input and a typed output. The contract is simple and strict: **every field a stage consumes must be produced by the stage before it.** Stage 2's input (`AssessArgs`) is a subset of stage 1's output (`ExtractedClaim`); stage 3's input (`RecommendArgs`) is a subset of stage 2's output (`RiskAssessment`).

`test_pipeline_contract.py` checks this offline, with no executor — field-name compatibility, a fast proxy for the full typed validation the Hub executor runs at each handoff at runtime:

```python
handoffs = [
    (ExtractedClaim, AssessArgs),     # stage 1 output -> stage 2 input
    (RiskAssessment, RecommendArgs),  # stage 2 output -> stage 3 input
]
for producer, consumer in handoffs:
    missing = set(consumer.model_fields) - set(producer.model_fields)
    assert not missing
```

It also loads the real manifest with the SDK and checks that every stage names a command that exists in the pack, in the order the code expects. Rename a field on one stage and forget the next, and CI goes red before the pipeline ever runs for real. This is the payoff of typed composition: the wiring is checked, not hoped for.

## Not every step is an AI step

Stage 2, `assess-risk`, calls no model at all. The risk band that drives the whole recommendation is a fact about fixed, documented rules (claim type weight, dollar amount, a penalty for missing data), so it is computed in plain Python in `risk.py`. A reader can predict the band of any claim by hand. Its test asserts the point directly:

```python
async def test_no_model_is_ever_called(mock_ctx):
    await assess_risk(_args(), mock_ctx)
    mock_ctx.llm.complete.assert_not_called()
```

This is worth internalizing: a pipeline is not "a chain of model calls." It is a chain of typed steps, and most of them are deterministic Python. The model shows up only where judgement genuinely helps.

## The governed finale

Stage 3, `recommend-action`, is the Tier 2 governance pattern dropped into a pipeline. Python decides the action from the risk band; the model writes a one-sentence justification for the decision it was handed; a deterministic eval checks the justification actually mentions the claim before it is trusted; and a detailed audit record is written for every run. An ungrounded justification, or an escalate action, routes to a human. The decision and the audit are Python's; the model is confined to prose it cannot use to override anything.

## What's next (beyond this rung)

This pipeline is linear and synchronous, which is the right place to start. The platform also supports, and you can reach for once this clicks:

- **Streaming stages** that emit results incrementally (`@command(streaming=True)`, `ctx.pipe`) so a UI can render as the pipeline runs.
- **Routing** (`route=` on a chunk, `accept_routes:` on a stage) to branch high-value claims down a different path without `if/else`.
- **Parallel blocks** and **cross-pack stages** that call commands in other packs, each call audited.

Those are deliberately not built here. One rung, one idea: declarative, type-checked composition first.

## Run it for real

> Re-scope it first: the example uses the `@reef` org, which you do not own. Change `namespace:` in `huitzo.yaml` to an org you own and run `huitzo pack sync` before publishing. See [Run on your own Hub](../../README.md#run-on-your-own-hub).

Each stage is a normal command, so you can run them one at a time:

```bash
huitzo login
huitzo run @your-org/claims-pipeline/assess-risk --args '{"claim_id": "C-1", "claim_type": "liability", "claim_amount": 300000, "requires_review": false, "missing_fields": []}'
```

Once you have early access to a Hub, run the whole pipeline through the REST API:

```bash
curl -X POST https://huitzo.ai/api/v1/pipelines/reef/claims-pipeline/score-claim/execute \
  -H "Authorization: Bearer sk-huitzo-..." \
  -H "Content-Type: application/json" \
  -d '{"initial_args": {"claim_id": "C-1", "document_text": "Policy number HMO-4471829. Incident date 2026-05-12. Damage of $12,500.00."}}'
```

## Next

You have composed packs on the backend. [Tier 4: first-dashboard](../04-first-dashboard) puts a face on one: a React app that calls a pack from the browser, with no backend of your own.
