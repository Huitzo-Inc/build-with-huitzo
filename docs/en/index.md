# Learning path

A guided order for working through this repo. Each project's own README is the full tutorial; this page is the map.

Every rung below builds and tests on your laptop, with no Hub account and no API key.

## Before you start (optional, five minutes)

- **[Build with an AI agent](./claude-code-setup.md)**: install the Huitzo developer environment for Claude Code. It gives your agent verified SDK references, the docs-first workflow, and reviewer agents, so the code it writes matches the patterns in this repo. Optional, but it is the fastest way to go from these examples to your own pack.

## Pick a path

- **Build a pack** (Python) — the ladder below, Tier 0 through Tier 6. Start here if you are not sure.
- **Build a dashboard** (React) — [the dashboard path](#the-dashboard-path), D0 onward. No Python required.

## Start here

1. **[Tier 0: hello-pack](../../projects/00-hello-pack)** (~5 min): text in, model call, typed output. Do this first.

## Tier 1: single-purpose packs (~10 minutes each)

2. **[`01a-doc-to-json`](../../projects/01a-doc-to-json)**: read a document, return typed fields.
3. **[`01b-macro-snapshot`](../../projects/01b-macro-snapshot)**: call a public API, return a grounded summary.
4. **[`01c-inbox-triage`](../../projects/01c-inbox-triage)**: deterministic triage owns urgency; the model only drafts a reply, and the pack never sends.
5. **[`01d-daily-digest`](../../projects/01d-daily-digest)**: a sales CSV becomes a summary plus one anomaly flag.

## Tier 2: governed packs (~15 minutes)

6. **[`02-grounded-reco`](../../projects/02-grounded-reco)**: deterministic logic, automatic evals, and a full audit trail. This is where governance becomes real. Pair it with [The aha moment](./the-aha-moment.md).

## Tier 3: composition (~30 minutes)

7. **[`03-claims-pipeline`](../../projects/03-claims-pipeline)**: three typed commands composed into one governed pipeline. A workflow is declarative data the executor type-checks.

## Tier 4: build a frontend (~40 minutes)

8. **[`04-first-dashboard`](../../projects/04-first-dashboard)**: a React dashboard that calls a pack from the browser with `useCommand`. The frontend is a thin consumer of decisions the pack already made. Runs locally with no Hub.

> **Front-end developer?** You do not have to climb the whole ladder first. See [the dashboard path](#the-dashboard-path) below — this rung is D1 on it.

## Tier 5: interact with huitzo.ai from outside (~40 minutes)

9. **[`05-pack-from-outside`](../../projects/05-pack-from-outside)**: drive a deployed pack from REST, the CLI, the hosted MCP server, and CI. One mental model, four doors.

## Tier 6: fullstack (~1 hour)

10. **[`06-fullstack-triage`](../../projects/06-fullstack-triage)**: a pack and a dashboard in one project, coupled only by the command API and tested end to end on your laptop.

## The dashboard path

For developers who build interfaces. It starts with a dashboard rather than a pack, and every rung hands you the pack it calls, already written and already tested — **you never write Python to finish one.**

1. **[D0: `d0-hello-dashboard`](../../projects/d0-hello-dashboard)** (~10 min): the smallest module Hub can mount. No pack, no network, no command call. The `mount`/`unmount` contract.
2. **[D1: `04-first-dashboard`](../../projects/04-first-dashboard)** (~40 min): call a real pack command with `useCommand`, against a mock Hub that runs on your laptop.
3. *D2: `d2-forms-and-input`* — in progress: typed forms from a declarative `FormFieldSpec`, with the pack's own validation errors landing on the right fields.
4. **[D3: `d3-design-system`](../../projects/d3-design-system)** (~30 min): the same snapshot rendered generic, then on brand tokens — and the design rules turned into tests that fail the build.
5. *D4: `d4-slow-commands`* — in progress: `useStreamingCommand`, the `CommandReceipt` path with `tasks.poll`, `useRealtime`, Hub toasts and breadcrumbs.
6. *D5: `d5-governed-ui`* — in progress: `TemplateFrame`, `ResultSection` and `EvidenceLink` rendering a withheld decision and its audit record. The dashboard answer to `02-grounded-reco`.
7. **[D6: `d6-ship-it`](../../projects/d6-ship-it)** (~30 min): validate, build, publish, and version against a command contract — with a dependency-free preflight that catches version drift, an undeclared pack, and a bundle that forgot to export `mount`.

**Capstone:** both paths meet at [`06-fullstack-triage`](../../projects/06-fullstack-triage) (~1 hour) — read with a hook, write with the client, optimistic updates with revert, and the fast-versus-queued command contract.

They are the same repository seen from two directions.

## Regulated reference solutions

Not a rung on the ladder. These take the governed pattern all the way into one regulated vertical, as a credible starting point for a real client deliverable meant to be adapted and resold.

- **[`08-trade-surveillance`](../../projects/08-trade-surveillance)**: screen trades for market-abuse patterns, with deterministic detection, a model-written analyst narrative, a grounding eval, and a full audit record.

## Coming soon

- **Tier 7: `07-sovereign-suite`**: a multi-tenant, deploy-anywhere governed system for a conglomerate. The reachable summit, where every prior rung composes up. Star the repo to follow along.

## Going deeper

This repo holds the hands-on tutorials. For API reference and conceptual explanation, see [docs.huitzo.ai](https://docs.huitzo.ai/docs/).
