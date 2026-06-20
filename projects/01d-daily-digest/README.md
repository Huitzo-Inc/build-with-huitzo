# Tier 1: daily-digest

> Read this in [Español](./README.es.md).

A real working day in one pack. Tide Mart, a one-location convenience store, drops a daily sales CSV. This pack turns it into a plain-language digest plus one anomaly flag: which day broke pattern, by how much, and what the day looked like overall. It is the indie-hacker reach rung. The same primitives serve a one-location owner and a conglomerate; only the size of the CSV changes.

The one idea to carry out of here: **Python finds the anomaly; the model only narrates it.** Every number and every flag is computed deterministically in plain Python. The model is asked for exactly one thing, the friendly prose, and it is handed the figures so it cannot invent them.

**You will learn:** deterministic-first design with the stdlib `csv` module, anomaly detection in pure Python (z-score with a percentage fallback), how to ground a model call on figures you already computed, and how to test all of it offline.

**Time:** about ten minutes.

## Prerequisites

- Python 3.11+
- The [Huitzo CLI](https://github.com/Huitzo-Inc/huitzo-launcher) (optional for this rung, used to run against a real Hub)

## Run it

```bash
cd pack
pip install -e ".[dev]"
pytest                  # offline tests for this pack (what CI runs)
```

You should see four passing tests. They run with no network and no model: the tests hand the command a fake context whose model call is mocked, so the totals and the anomaly flags are verified without spending a token.

## What is inside

```
pack/
  huitzo.yaml                       the manifest: identity, permissions, the Policy Card
  pyproject.toml                    dependencies and the command entry point
  src/daily_digest/
    commands/daily_digest.py        parse, total, flag anomalies, then one model call
    models/args.py                  typed input (the raw CSV, validated before your code runs)
    models/output.py                typed output (every figure from Python + the model's prose)
  tests/test_daily_digest.py        offline tests
```

## The command, in three moves

```python
@command("daily-digest", namespace="reef", timeout=30)
async def daily_digest(args: DigestArgs, ctx: Context) -> DailyDigest:
    # 1) Deterministic first. Python parses the CSV and owns every number.
    #    Totals, per-category totals, top category, day count, skipped rows.

    # 2) Anomaly detection, in pure Python. Compare each day to the mean of the
    #    others: a z-score when there are enough days, a percentage rule when not.
    anomalies = _detect_anomalies(daily_totals)

    # 3) AI augmentation. One call, to a *profile*, with the computed figures handed
    #    in so the prose is grounded. The model fills exactly one field: the summary.
    narrative = await ctx.llm.complete(
        prompt=f"{_PROMPT}\n\n<data>\n{facts}\n</data>",
        profile="default",
        schema=DigestNarrative,
    )
    return DailyDigest(..., anomalies=anomalies, summary=narrative.summary)
```

Three things to notice:

1. **The anomaly is found in Python, not asked of the model.** A spiking day is a fact about numbers. Python computes the mean and spread of the other days and flags the outlier, so the flag is reproducible and auditable. A model could miss it, or hallucinate one; the deterministic rule does neither.
2. **`profile="default"` is not a model name.** The pack declares a capability profile; the deployment maps it to a concrete provider and model. That is how you swap OpenAI for Anthropic, or a cloud model for a local one, without touching this file.
3. **The model is grounded, not trusted with arithmetic.** The computed total, top category, and flagged days are formatted into the prompt, and the model is instructed to use only those figures. It writes the sentence; it never decides the number.

## Why deterministic-first matters here

An owner reading this digest is making a decision: chase down why Saturday spiked, or trust that the week was steady. If the number that drives that decision came from a model that might be off by a digit, the digest is worse than useless. So the number never comes from the model. Python computes it; the model only puts it in a friendly sentence. That division is the whole Huitzo pattern, and it is exactly what lets the same pack be trusted by a corner store and by a finance team running a thousand locations.

## The "swap the model" moment

Open `pack/huitzo.yaml` and find the `services.llm` block:

```yaml
services:
  llm:
    required: true
    requirements:
      min_context: 8000
      capabilities:
        - structured_output
```

The pack states what it needs (a context window and structured output), not which model provides it. On your Hub, the `default` profile resolves to whatever model that deployment is configured for. The same pack runs unchanged on a local model or a cloud one. That is the model-agnostic promise, made concrete.

## Run it for real

> Re-scope it first: the example uses the `@reef` org, which you do not own. Change `namespace:` in `huitzo.yaml` to an org you own and run `huitzo pack sync` before publishing. See [Run on your own Hub](../../README.md#run-on-your-own-hub).

Once you have early access to a Hub:

```bash
huitzo login
huitzo run @your-org/daily-digest/daily-digest --args '{"sales_csv": "date,category,amount\n2026-06-01,snacks,120\n2026-06-01,drinks,80"}'
```

## Next

Same pattern, more surface. The shape never changes: Python owns the facts, the model writes the prose. The governed rung, [02-grounded-reco](../02-grounded-reco), adds an eval and an audit trail on top of this core.
