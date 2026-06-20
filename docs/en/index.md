# Learning path

A guided order for working through this repo. Each project's own README is the full tutorial; this page is the map.

## Start here

1. **[Tier 0: hello-pack](../../projects/00-hello-pack)**: text in, model call, typed output. Five minutes. Do this first.

## Tier 1: single-purpose packs (an afternoon each)

2. **`01a-doc-to-json`**: read a document, return typed fields.
3. **`01b-macro-snapshot`**: call a public API, return a grounded summary.
4. **`01c-inbox-triage`**: deterministic triage owns urgency; the model only drafts a reply, and the pack never sends.
5. **`01d-daily-digest`**: a sales CSV becomes a summary plus one anomaly flag.

## Tier 2: governed packs (a few days)

6. **`02-grounded-reco`**: deterministic logic, automatic evals, and a full audit trail. This is where governance becomes real.

## Tier 3: composition

7. **`03-claims-pipeline`**: three typed commands composed into one governed pipeline. A workflow is declarative data the executor type-checks.

## Tier 4: build a frontend

8. **`04-first-dashboard`**: a React dashboard that calls a pack from the browser with `useCommand`. The frontend is a thin consumer of decisions the pack already made. Runs locally with no Hub.

## Tier 5: interact with huitzo.ai from outside

9. **`05-pack-from-outside`**: drive a deployed pack from REST, the CLI, the hosted MCP server, and CI. One mental model, four doors.

## Tier 6: fullstack

10. **`06-fullstack-triage`**: a pack and a dashboard in one project, coupled only by the command API and tested end to end on your laptop.

## Coming soon

- **Tier 7: `07-sovereign-suite`**: a multi-tenant, deploy-anywhere governed system for a conglomerate. The reachable summit, where every prior rung composes up. Tracked as a GitHub issue; star the repo to follow along.

## Going deeper

This repo holds the hands-on tutorials. For API reference and conceptual explanation, see [docs.huitzo.ai](https://docs.huitzo.ai/docs/).
