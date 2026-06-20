# The aha moment: swap the model, keep the governance

This is the one thing to feel before you build anything serious on Huitzo.

A Huitzo Intelligence Pack never names a model. It asks for a **profile** — a
capability label — and the *deployment* decides which concrete model that
resolves to. So you can move a pack from Claude to GPT‑4o to a local model **by
changing one line of deployment config**, with **zero changes to your code** and
**zero change to the governed decision or the audit trail**.

This walkthrough proves it on a real governed pack, with real output.

> **Don't take our word for it — run it offline in five seconds (no Hub, no API key):**
> ```bash
> cd projects/02-grounded-reco/pack && pip install -e ".[dev]"
> python -m grounded_reco.demo_model_swap
> ```
> It runs the *real* `recommend` command under two different stub "models" and prints
> them side by side: the pick, the eval gate, and the audit come out **byte-identical**
> (deterministic Python the model never touches); only the justification prose differs.
> That is the whole argument, shown rather than claimed.

## The pack we'll use: [`02-grounded-reco`](../../projects/02-grounded-reco)

`recommend` is a governed recommendation. The order of operations *is* the
governance story:

1. **Python** scores and ranks the candidates and chooses the pick. The model
   does not choose.
2. The **model** writes a one‑sentence justification for the *Python‑chosen*
   pick. It is handed the decision and the numbers and told not to change them.
3. A **deterministic eval** (freshness + grounding) judges the result *before* it
   reaches a user. If it fails, the recommendation is withheld and escalated.
4. A detailed **audit record** is produced and logged for every run.

The model call is exactly this — note the `profile`, never a model name:

```python
justification: Justification = await ctx.llm.complete(
    prompt=prompt,
    profile="default",     # a capability label — NOT "claude" or "gpt-4o"
    schema=Justification,  # validated, typed output (see "the aha moment", part 2)
)
```

## Run 1 — on Claude (the deployment default)

```bash
huitzo run @reef/grounded-reco/recommend --args '{
  "objective": "Choose the vendor that best balances reliability and cost for a regulated healthcare client.",
  "freshness_days": 3650,
  "candidates": [
    {"name": "NorthAPI",     "cost": 0.30, "quality": 0.80, "reliability": 0.95, "as_of": "2026-06-10"},
    {"name": "BudgetStream", "cost": 0.10, "quality": 0.55, "reliability": 0.60, "as_of": "2026-06-12"},
    {"name": "PremiumCloud", "cost": 0.85, "quality": 0.92, "reliability": 0.90, "as_of": "2026-06-01"}
  ]
}'
```

Real output from a live Hub running `claude-sonnet-4-6`:

```json
{
  "pick": "NorthAPI",
  "score": 0.815,
  "ranked": [
    {"name": "NorthAPI",     "score": 0.815, "as_of": "2026-06-10"},
    {"name": "PremiumCloud", "score": 0.683, "as_of": "2026-06-01"},
    {"name": "BudgetStream", "score": 0.670, "as_of": "2026-06-12"}
  ],
  "justification": "NorthAPI earned the top score of 0.815, meaningfully ahead of PremiumCloud (0.683) and BudgetStream (0.670), indicating it best balances reliability and cost for a regulated healthcare client according to the deterministic scoring system.",
  "eval_passed": true,
  "eval_findings": [
    "freshness: OK, pick 'NorthAPI' within 3650 days.",
    "grounding: OK, justification references the pick."
  ],
  "withheld": false,
  "escalated": false,
  "audit": {
    "timestamp": "2026-06-18T18:20:27Z",
    "autonomy": "suggest",
    "candidate_count": 3,
    "pick": "NorthAPI",
    "eval_passed": true,
    "eval_findings": ["freshness: OK, pick 'NorthAPI' within 3650 days.",
                      "grounding: OK, justification references the pick."],
    "escalated": false
  }
}
```

## Run 2 — swap to GPT‑4o by changing ONE line

In the deployment config (the Hub operator's, not yours), change one value and
restart:

```diff
  HUITZO_LLM_CLOUD_ENABLED: "true"
  HUITZO_LLM_ROUTING_MODELS: '[{"name":"claude-sonnet-4-6",...},{"name":"gpt-4o",...}]'
- HUITZO_LLM_ROUTING_DEFAULT_MODEL: claude-sonnet-4-6
+ HUITZO_LLM_ROUTING_DEFAULT_MODEL: gpt-4o
```

Re-run the **exact same command**. We verified this live: the identical pack,
unchanged, routed its model call to OpenAI's `gpt-4o` endpoint instead of
Anthropic, and produced the **byte-identical deterministic result** before the
model was ever consulted:

```
recommend: deterministic pick='NorthAPI' score=0.815 from 3 candidates
HTTP Request: POST https://api.openai.com/v1/chat/completions   ← now GPT-4o, not Anthropic
```

## What changed, and what didn't

| | Run 1 (Claude) | Run 2 (GPT‑4o) |
|---|---|---|
| **The decision** — pick, score, ranking | `NorthAPI`, `0.815` | `NorthAPI`, `0.815` — *identical* |
| **The guardrail** — freshness + grounding eval, withhold/escalate | passed, not withheld | *identical* |
| **The audit record** — autonomy, findings, escalation | logged | *identical* |
| **The Policy Card** — `autonomy: suggest`, escalation routes | enforced | *identical* |
| The one‑sentence **justification** prose | Claude's wording | GPT‑4o's wording |

Only the *prose author* changed. Everything that governs the decision is
deterministic Python, so it is **model-independent by construction** — swapping
the model *cannot* change a decision, because the model never made one. The
model is confined to a justification that the eval then checks for grounding.

## The kicker (a real thing that happened)

When we ran the swap live, the deployment's OpenAI key was
rate-limited (HTTP 429). The deployment didn't break and no code changed — we
flipped the one line back to `claude-sonnet-4-6`, and it was serving again in
seconds.

**That is the whole point.** A provider's quota, outage, price change, or model
deprecation is an *ops config change* for a Huitzo deployment — not a code
rewrite and redeploy. Your client's solution is never locked to one vendor.

## Why not just the Anthropic SDK + Pydantic?

You can absolutely call a model and validate the JSON yourself. Here is what you
take on the day you do, and what Huitzo gives you instead:

| You want… | Raw Anthropic SDK + Pydantic | Huitzo Intelligence Pack |
|---|---|---|
| **Swap the model / vendor** | Rewrite the client, re-test, redeploy. Your customer is locked to your one vendor. | One deployment config line. Zero code change. No vendor lock-in for *your* clients. |
| **Reliable structured output** | Hand-roll a retry loop that feeds validation errors back to the model. | Built in — `schema=` validates and self-corrects on a validation miss. |
| **A guardrail before output reaches a user** | Build and maintain your own eval/withhold/escalate logic. | Declarative **Policy Card** + deterministic evals the framework runs every time. |
| **An audit trail for every generation** | Build it, store it, prove it for an auditor. | Every run is audited by the framework, returned and logged. |
| **Self-hosted, zero-access for regulated data** | Build and certify the infrastructure yourself. | Runs inside your tenant; the model is called where your data already lives. |

The model is the easy part. **Governance, auditability, and not being hostage to
one vendor are the hard parts — and they are exactly what a Pack gives you for
free.** That is why a partner builds a client's regulated solution on Huitzo
instead of wiring the SDK directly.

## Try it yourself

1. Run [`02-grounded-reco`](../../projects/02-grounded-reco) against your own Hub
   (see [Run on your own Hub](../../README.md#run-on-your-own-hub)).
2. Ask your Hub operator to flip `HUITZO_LLM_ROUTING_DEFAULT_MODEL` between two
   models your deployment has configured, and restart.
3. Re-run the same command. Watch the decision, the eval, and the audit stay
   identical while only the prose changes.

Next: [`03-claims-pipeline`](../../projects/03-claims-pipeline) shows the same
governance scaled into a multi-stage, regulated-industry deliverable.
