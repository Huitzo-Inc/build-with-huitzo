# Reference solution: trade-surveillance (financial markets)

> Read this in [Español](./README.es.md).

This is the first of the **regulated reference solutions** — not a teaching rung, but a credible starting point a partner adapts for a real client. It applies the same governed pattern you learned on the ladder ([Tier 2](../02-grounded-reco), [Tier 3](../03-claims-pipeline)) to **market-abuse surveillance** for a broker-dealer or asset manager.

A trade comes in. Deterministic Python runs fixed, documented detectors for the classic abuse patterns — off-market pricing, marking the close, layering/spoofing, wash trades, size anomalies — and computes a risk score and band. **Only when something fires** does the model write a short alert note for a compliance analyst. A deterministic eval checks that note is grounded before anyone sees it, and Python — never the model — decides whether the alert clears, goes to review, or escalates to a human. Every screen leaves a detailed audit record.

> **Read this as a real deliverable.** Surveillance is one of the most heavily regulated AI surfaces in capital markets (MAR, FINRA, SEC). What makes it defensible is exactly the Huitzo shape: the *detection and the decision are deterministic, reproducible, and auditable*, and the model is confined to prose a guardrail checks. Swap the detectors for AML transaction monitoring, suitability/best-execution review, or disclosure checks and the skeleton does not change. That portability is the partner's product: adapt it per client, resell it self-hosted so the client's order flow never leaves their boundary.

**You will learn / what it proves:** the governed pattern scales straight from a toy to a regulated capital-markets deliverable; deterministic detection owns whether an alert fires (the model cannot raise or suppress one); a grounding eval and a human-escalation gate sit between the model and the analyst; and every screen is audited — model-agnostic and self-hosted throughout.

## Run it

```bash
cd pack
pip install -e ".[dev]"
pytest                  # offline tests for this pack (what CI runs)
```

You should see ten passing tests, with no network and no model. They encode the governance contract: a clean trade clears without ever calling the model; a flagged trade is narrated, eval'd, and escalated; and — the key test — the **model cannot change the disposition** (a high-risk alert escalates even if the narrative says "looks fine").

## The governed flow

```python
# 1) DETERMINISTIC DETECTION — Python owns whether an alert fires and how severe.
signals = rules.detect_signals(trade, market)
risk_score = rules.score(signals)
risk_band = rules.band(risk_score)

# 2) A clean trade never calls the model. Deterministic for the quiet 99%.
if not signals:
    return SurveillanceAlert(..., disposition="clear", ...)

# 3) AI NARRATION — one call, to a profile, returning a validated instance. The model
#    explains the alert Python raised; it does not score, band, or dispose.
narrative = await ctx.llm.complete(prompt=..., profile="default", schema=AlertNarrative)

# 4) EVAL + DISPOSITION + AUDIT — all deterministic Python.
eval_passed, findings = evals.run_eval(trade.symbol, signals, narrative.text)
disposition = evals.decide_disposition(risk_band, eval_passed)   # clear | review | escalate
```

## The detectors are the auditable core

`rules.py` holds the whole detection model in readable Python — fixed thresholds and weights a compliance officer can read, defend, and tune, with no model anywhere near the verdict:

| Signal | Fires when | Weight |
|---|---|---|
| `off_market_price` | execution > 2% from the prevailing mid | 0.35 |
| `marking_the_close` | aggressive print in the last 5 minutes | 0.30 |
| `layering_spoofing` | recent order cancel-ratio ≥ 80% | 0.30 |
| `wash_trade` | same beneficial owner both sides | 0.40 |
| `size_anomaly` | ≥ 10× the trader's average size | 0.20 |

The composite score is a capped weighted sum; the band thresholds are constants. You can predict any trade's band by hand — which is the point: a regulator can too.

## Why this is not a thin LLM wrapper

A wrapper would ask the model "is this suspicious?" and return the answer. This does the opposite, and that inversion is what makes it shippable into a regulated firm:

1. **The detection is deterministic.** The model never decides whether an alert fires; `rules.py` does, reproducibly.
2. **The model only narrates, and the narrative is checked.** An ungrounded note (one that names neither the instrument nor a flagged pattern) is never trusted — it escalates to a human instead.
3. **The disposition is Python's.** `decide_disposition` routes from the band + eval; the model cannot clear a high-risk alert. A test asserts exactly this.
4. **Every screen is audited.** A cleared trade leaves the same evidence shape as an escalated one, so nothing is invisible to an examiner. The Policy Card (`autonomy: suggest`, `escalation`, `audit: detailed`) is the contract the platform enforces.

## Adapt it for a client

This is meant to be repointed. To turn it into another markets surveillance or a different vertical:

- Edit `rules.py`: change the detectors, thresholds, and weights to the client's risk appetite and rulebook (e.g. AML transaction-monitoring rules, suitability checks).
- Keep the shape: detection → (model narrates) → eval → deterministic disposition → audit.
- Re-scope the namespace to an org you own (`huitzo.yaml` → `huitzo pack sync`) and publish to the client's self-hosted Hub. Their order flow never leaves their boundary.

## Run it for real

> Re-scope it first: the example uses the `@reef` org. Change `namespace:` in `huitzo.yaml` to an org you own and run `huitzo pack sync` before publishing. See [Run on your own Hub](../../README.md#run-on-your-own-hub).

```bash
huitzo login
huitzo run @your-org/trade-surveillance/screen-trade --args '{
  "trade":  {"trade_id": "T-9", "symbol": "ACME", "side": "buy", "quantity": 100, "price": 103.10, "timestamp": "2026-06-19T15:58:30Z"},
  "market": {"prevailing_bid": 100.00, "prevailing_ask": 100.10, "minutes_to_close": 2, "trader_avg_quantity": 100, "recent_cancel_ratio": 0.0}
}'
```
