# Tier 0: hello-pack

> Read this in [Español](./README.es.md).

The smallest complete Intelligence Pack. Text goes in, one model call runs through the SDK, and a typed, validated result comes back. If you do one thing in this repo, do this. It is the fastest path to a running pack and it plants the one idea everything else builds on: **deterministic Python owns what it can, and the model is asked only for the part Python cannot do.**

**You will learn:** the `@command` decorator, typed args and output with Pydantic, calling a model through a profile (never a hard-coded model name), and how to test a pack offline.

**Time:** about five minutes.

## Prerequisites

- Python 3.11+
- The [Huitzo CLI](https://github.com/Huitzo-Inc/huitzo-launcher) (optional for this rung, used to run against a real Hub)

## Run it

```bash
cd pack
pip install -e ".[dev]"
pytest                  # offline tests for this pack (what CI runs)
```

You should see three passing tests. They run with no network and no model: the test hands the command a fake context whose model call is mocked, so your logic is verified without spending a token.

## Build it yourself (the fastest way to learn)

Reading working code is slower than writing it. Try this first:

1. Open `src/hello_pack/commands/hello.py` and delete the body of `hello`,
   leaving just `async def hello(args: HelloArgs, ctx: Context) -> TextInsight:`
   and a `raise NotImplementedError`.
2. Run `pytest`. It fails — **the tests are the spec.** Read them in
   `tests/test_hello.py`: they tell you exactly what the command must do (compute
   the word count in Python, call the model for the judgement, return a typed
   `TextInsight`).
3. Re-implement the three steps until the tests pass. The block under
   ["The command, line by line"](#the-command-line-by-line) is the solution if
   you get stuck.

That loop — a failing test that pins the contract, then code until green — is how
you will build every real pack. The rest of this README explains the solution.

## What is inside

```
pack/
  huitzo.yaml                  the manifest: identity, permissions, the Policy Card
  pyproject.toml               dependencies and the command entry point
  src/hello_pack/
    commands/hello.py          the command itself
    models/args.py             typed input (validated before your code runs)
    models/output.py           typed output (what the model returns + a Python fact)
  tests/test_hello.py          offline tests
```

## The command, line by line

```python
@command("hello", namespace="reef", timeout=30)
async def hello(args: HelloArgs, ctx: Context) -> TextInsight:
    # 1) Deterministic first. Python owns what Python can do reliably.
    word_count = len(args.text.split())

    # 2) AI augmentation. One call, to a *profile*, returning a validated model.
    insight = await ctx.llm.complete(
        prompt=f"{_PROMPT}\n\n<text>\n{args.text}\n</text>",
        profile="default",
        schema=ModelInsight,
    )

    # 3) Combine the model's judgement with the deterministic fact.
    return TextInsight(word_count=word_count, **insight.model_dump())
```

Three things to notice:

1. **The word count is computed in Python, not asked of the model.** Anything deterministic stays deterministic. The model is never the bottleneck or the source of avoidable errors.
2. **`profile="default"` is not a model name.** The pack declares a capability profile; the deployment maps it to a concrete provider and model. That is how you swap OpenAI for Anthropic, or a cloud model for a local one, without touching this file.
3. **`schema=ModelInsight` returns a validated instance,** not a string you have to parse. Structured output is the default handoff between your code and the model.

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
huitzo run @your-org/hello-pack/hello --args '{"text": "Huitzo makes AI work where your data lives."}'
```

## Next

Tier 1: [`01a-doc-to-json`](../01a-doc-to-json) reads a real document from storage and returns typed fields. Same pattern, more surface.
