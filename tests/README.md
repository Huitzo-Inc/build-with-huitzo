# Regression gate

`test_regression_gate.py` is the repo-wide safety net. It encodes **one offline
test per bug class** that an end-to-end sweep of the exercises found and fixed, so
a fixed class of bug can never quietly come back through a new pack, a new
dashboard, or an edit to an old one.

**The rule: no exercise ships unless it stays green here.** It runs in CI
([`regression-gate.yml`](../.github/workflows/regression-gate.yml)) on every push
and pull request, alongside the per-pack tests.

It is pure static analysis (AST + YAML + text) — no network, no Hub, no model —
so it runs in milliseconds and never flakes.

| Bug class (from the sweep) | Invariant enforced here |
|---|---|
| 1. Structured output not enum-reliable | Every `Literal`/enum field a command sends to the model via `schema=` has its allowed values named in the prompt. |
| 2. Structured output coaxed from prose | Anything passed to `schema=` is a Pydantic `BaseModel`. |
| 3 & 4. Pipeline block dropped / stage refs unresolved | Every pipeline stage references a command declared in the same pack. |
| 5. Tier-5 client request shapes | REST wraps args under `"args"` and uses the full `@scope/pack/command` path; MCP uses `/mcp/` with an SSE `Accept`. |
| 6. Dashboards crash "process is not defined" | Every dashboard `vite.config.ts` defines `process.env.NODE_ENV` **and** installs a `process` shim. |
| 7. Pydantic command results not serializable | Every `@command` returns a Pydantic model. |

Run it locally:

```bash
pip install pytest pyyaml
pytest tests/test_regression_gate.py -v
```

When you add an exercise, you generally do not touch this file — the gate
discovers packs and dashboards automatically. You only edit it when a *new* bug
class is found in production and you want to make sure it never recurs.
