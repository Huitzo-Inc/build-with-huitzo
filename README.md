# build-with-huitzo

**Learn to build on Huitzo by shipping real things, one rung at a time.** This is the hands-on, copy-paste way to go from a five-minute "hello world" to a governed, multi-tenant deployment — whether you build the Python that decides, the React that shows it, or both.

[![tests](https://github.com/Huitzo-Inc/build-with-huitzo/actions/workflows/test-packs.yml/badge.svg)](https://github.com/Huitzo-Inc/build-with-huitzo/actions/workflows/test-packs.yml)
[![regression-gate](https://github.com/Huitzo-Inc/build-with-huitzo/actions/workflows/regression-gate.yml/badge.svg)](https://github.com/Huitzo-Inc/build-with-huitzo/actions/workflows/regression-gate.yml)
[![i18n](https://github.com/Huitzo-Inc/build-with-huitzo/actions/workflows/i18n.yml/badge.svg)](https://github.com/Huitzo-Inc/build-with-huitzo/actions/workflows/i18n.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-informational.svg)](./LICENSE)
[![huitzo-sdk](https://img.shields.io/pypi/v/huitzo-sdk?label=huitzo-sdk)](https://pypi.org/project/huitzo-sdk/)

> Read this in [Español](./README.es.md). Full reference docs live at [docs.huitzo.ai](https://docs.huitzo.ai/docs/).

Huitzo is the AI operating system for regulated companies. The unit you build and ship is an **Intelligence Pack**: deterministic Python that owns the decisions, with an AI model called only where it adds value. Every example here is that pattern, tested in CI so it runs on the first try.

> ⭐ **New here? Read [The aha moment](./docs/en/the-aha-moment.md) first** ([Español](./docs/es/the-aha-moment.md)). One governed pack, the model swapped from Claude to GPT‑4o by changing a single config line — same decision, same audit, same Policy Card. It is the fastest way to feel *why* you build a regulated solution on Huitzo instead of wiring an LLM SDK directly.

## Two ways in

Both paths run entirely on your laptop, need no account and no API key, and end at
the same place. Pick the one that matches what you build.

| | **Build a pack** (Python) | **Build a dashboard** (React) |
|---|---|---|
| **You write** | The deterministic logic that owns the decision | The interface a person actually uses |
| **You need** | Python 3.11+ | Node 20+ |
| **Start at** | [`00-hello-pack`](./projects/00-hello-pack) — 5 min | [`d0-hello-dashboard`](./projects/d0-hello-dashboard) — 10 min |
| **Full route** | [The ladder](#the-ladder), Tier 0 → 6 | [The dashboard path](#the-dashboard-path), D0 → Tier 6 |

Not sure? Start with the pack. It is the shorter of the two, and it is the thing a
dashboard calls.

### Quickstart: your first pack (about five minutes)

Python 3.11+ is the only thing you need.

```bash
# 1. Get the examples and open the first pack
git clone https://github.com/Huitzo-Inc/build-with-huitzo
cd build-with-huitzo/projects/00-hello-pack/pack

# 2. Create a virtualenv, install the SDK, and run the pack's tests
python3 -m venv .venv && source .venv/bin/activate   # macOS/Linux/WSL2
pip install -e ".[dev]"
pytest                  # the pack's offline tests (exactly what CI runs)
```

> Windows (PowerShell): `py -3 -m venv .venv`, then `.venv\Scripts\Activate.ps1`, before `pip install -e ".[dev]"`.

Three passing tests means you have a working Intelligence Pack. Now read
[`00-hello-pack`](./projects/00-hello-pack) to see what you just ran, then follow
the [learning path](./docs/en/index.md).

### Quickstart: your first dashboard (about ten minutes)

Node 20+ is the only thing you need — no Python, and no pack.

```bash
git clone https://github.com/Huitzo-Inc/build-with-huitzo
cd build-with-huitzo/projects/d0-hello-dashboard/dashboard

npm install
npm test                # 5 tests: the Hub mount contract
npm run dev             # http://localhost:3000
```

That is a real Huitzo Dashboard running with no Hub at all. Read
[`d0-hello-dashboard`](./projects/d0-hello-dashboard) for what just happened.

Everything in this repo runs offline like that. The CLI and a Hub account come in
later, when you want to publish — see [Run on your own Hub](#run-on-your-own-hub).

## Build it with an AI agent (optional, five minutes)

If you use [Claude Code](https://code.claude.com/docs/en/overview), install the
Huitzo developer environment before you write your own pack:

```text
/plugin marketplace add Huitzo-Inc/pack-claude-env
/plugin install huitzo@huitzo
/huitzo:huitzo-init
```

It gives your agent verified SDK references, docs-first workflow skills, reviewer
agents, and a hook that catches a hard-coded model name before you commit it.
Full instructions, both install channels, and an illustrated walkthrough:
**[Build with an AI agent](./docs/en/claude-code-setup.md)**.

## The ladder

Each rung composes the ones below it, so the hardest project is reachable rather than a cliff. Pick where you are.

| Rung | Project | What you will build | What it proves |
|------|---------|---------------------|----------------|
| **Tier 0** | [`00-hello-pack`](./projects/00-hello-pack) | Text in, one model call, structured output. Swap the model with one line of config. | The SDK, the one interface, model-agnostic routing. The fastest path to a running pack. |
| **Tier 1** | [`01a-doc-to-json`](./projects/01a-doc-to-json) | Read a PDF (claim, lab report, contract), return typed fields. | Storage + AI + structured output. The homepage promise. |
| **Tier 1** | [`01b-macro-snapshot`](./projects/01b-macro-snapshot) | Call a public API (World Bank), return a grounded summary. | HTTP integration + grounded AI. |
| **Tier 1** | [`01c-inbox-triage`](./projects/01c-inbox-triage) | Read email, classify it, draft a reply for a human to send. | Deterministic triage owns urgency; the model only drafts, and the pack never sends. |
| **Tier 1** | [`01d-daily-digest`](./projects/01d-daily-digest) | Turn a sales CSV into a summary plus one anomaly flag. | The same primitives serve a one-location shop and a conglomerate. |
| **Tier 2** | [`02-grounded-reco`](./projects/02-grounded-reco) | A recommendation that will not hallucinate: deterministic logic, automatic evals, full audit trail. | The governance layer and Policy Card. Where Huitzo stops looking like a thin LLM wrapper. |
| **Tier 3** | [`03-claims-pipeline`](./projects/03-claims-pipeline) | Three typed commands composed into one governed pipeline. | Composition: a workflow is declarative data the executor type-checks, not glue code. |
| **Tier 4** | [`04-first-dashboard`](./projects/04-first-dashboard) | A React dashboard that calls a pack from the browser. | The frontend: a Dashboard SDK app is a thin consumer of decisions the pack already made. |
| **Tier 5** | [`05-pack-from-outside`](./projects/05-pack-from-outside) | Drive a deployed pack from REST, the CLI, hosted MCP, and CI. | One mental model, four doors: how to interact with huitzo.ai from anywhere. |
| **Tier 6** | [`06-fullstack-triage`](./projects/06-fullstack-triage) | A pack and a dashboard in one project, tested end to end on your laptop. | Fullstack: the command API is the single contract between Python and the UI. |
| Tier 7 | `07-sovereign-suite` | A multi-tenant, deploy-anywhere governed system for a conglomerate. | **Coming soon** — star the repo to follow along. |

## The dashboard path

If you build interfaces, this is your route. It starts with a dashboard rather than
a pack, and every rung hands you the pack it calls, already written and already
tested — **you never have to write Python to finish one.**

| Rung | Project | What you will build | What it proves |
|------|---------|---------------------|----------------|
| **D0** | [`d0-hello-dashboard`](./projects/d0-hello-dashboard) | The smallest module Hub can mount. No pack, no network. | The `mount`/`unmount` contract: a dashboard is a module Hub runs, not a website. |
| **D1** | [`04-first-dashboard`](./projects/04-first-dashboard) | A dashboard that calls a real pack command with `useCommand`, against a mock Hub. | The frontend is a thin consumer of decisions the Python already made. |
| **D2** | [`06-fullstack-triage`](./projects/06-fullstack-triage) | Reading with a hook, writing with the client, optimistic updates with revert. | The command API is the single contract between Python and the UI. |

More rungs are in progress — declarative forms, the brand token system, streaming
and queued commands, and the governed interface that renders a withheld decision
and its evidence record. See [the learning path](./docs/en/index.md) for the map.

> **Already know packs?** Tier 4 is D1. The two paths are the same repository seen
> from two directions, and they meet at Tier 6.

## Regulated reference solutions

Beyond the learning ladder, these are credible starting points for a real client deliverable — the governed pattern applied to a specific regulated vertical, meant to be **adapted and resold**, not just read. Each is self-hosted and model-agnostic, so the client's data never leaves their boundary and they are never locked to a vendor.

| Vertical | Solution | What it does |
|----------|----------|--------------|
| **Financial markets** | [`08-trade-surveillance`](./projects/08-trade-surveillance) | Screen trades for market-abuse patterns (off-market pricing, marking the close, spoofing, wash trades, size anomalies): deterministic detection + risk band, a model-written analyst narrative, a grounding eval, and a full audit record — high-risk or ungrounded alerts escalate to a human. |

More verticals (banking, government) follow the same skeleton; adapt the detectors and keep the governance.

## Run on your own Hub

Everything above runs and tests offline. To publish and run an example on a real Hub, two things matter.

**1. Use an org you own.** The examples are scoped to the `@reef` org. You almost certainly do not own `reef`, so re-scope each pack to an organization you do own before publishing:

```bash
huitzo login
# In the pack's huitzo.yaml, change the namespace to your org slug:
#   pack:
#     namespace: your-org        # was: reef
huitzo pack sync                  # rewrites pyproject.toml entry points from huitzo.yaml
huitzo pack publish
huitzo run @your-org/hello-pack/hello --args '{"text": "..."}'
```

The `namespace:` in `huitzo.yaml` is authoritative. `huitzo pack sync` rewrites the `pyproject.toml` entry points to match, so you never edit those by hand. **You do _not_ need to touch the `namespace=` argument in the `@command(...)` decorator** — the platform takes the published namespace from the entry points (set by `huitzo.yaml` + `pack sync`), so the decorator value is metadata only and changing your org does not require editing it. (You may update it to match for readability, but nothing breaks if you leave it.) Dashboards work the same way: change `namespace` and `pack_dependencies` in `huitzo-dashboard.yaml`, and the command ids in the dashboard's `types.ts`, to your org.

You get a developer org when you enable Developer Mode (the CLI prompts you on your first publish, or you can do it in the Hub). Your org slug is shown in the Hub.

**2. The deployment must have what the pack needs.** A pack that calls a model needs the deployment's LLM registry to have a model meeting its `services.llm` floor (a context window plus `structured_output`). A pack that calls an external API needs a matching HTTP integration. [`01b-macro-snapshot`](./projects/01b-macro-snapshot) walks through adding one in the Hub.

## Run for real: request a Hub sandbox

Every exercise builds and tests on your laptop with no account. To run the later
rungs (Tiers 4–6: dashboards, the outside-in clients, the governed pipeline)
against a **live, governed Hub** — and to feel the model-swap and Policy Card
story end to end — request a partner **sandbox Hub**:

- **Request access:** start at [huitzo.ai](https://huitzo.ai) (early access), or
  email the partner team at **ernesto@huitzo.ai** with your org and what you want
  to build. Tell us you came from `build-with-huitzo`.
- **What you get:** an isolated sandbox Hub, pre-wired with a model that clears
  the packs' `structured_output` floor, where you can `huitzo publish` and
  `huitzo run` these exercises and your own packs for real.
- **It is isolated by design.** A sandbox is air-gapped from any customer Hub —
  the same zero-access, self-hosted boundary your own regulated clients get. You
  build and resell on that boundary; the sandbox lets you feel it first.

## How these examples are kept honest

- **Every pack is tested in CI** against the published `huitzo-sdk`, so a broken example fails the build, not your afternoon.
- **A weekly [SDK drift check](./.github/workflows/sdk-drift.yml) rebuilds every example against the *latest* published SDKs**, ignoring the lockfile. Pull-request CI is reproducible (it installs what the lockfile pins), which means it cannot notice a new SDK major landing upstream. This job can, so an example that stops compiling is our problem before it is yours.
- **A [regression gate](./tests/README.md) guards every bug class our end-to-end sweep found and fixed.** One offline test per bug class (enum-reliability, pipeline refs, dashboard `process` crashes, client request shapes, …) runs on every change, so a fixed bug can never quietly come back. No exercise ships unless it stays green.
- **English is the single source of truth; Spanish is a reviewed translation.** A [staleness gate](./.translation/README.md) blocks any Spanish file from drifting out of date with its English source. You only ever hand-edit English.
- **Mock names are fictional.** Companies like Nautilus Mutual and Leviathan Holdings are placeholders. No real customers appear anywhere.

## What you need

**To build and test every exercise:**

- Python 3.11+ and `pip`
- Node 20+ and npm for the dashboard rungs (Tiers 4 and 6)
- The [`huitzo-sdk`](https://pypi.org/project/huitzo-sdk/) from PyPI (installed per pack, by the quickstart above)

**Only when you want to publish or run against a live Hub:**

- The [Huitzo CLI](https://github.com/Huitzo-Inc/huitzo-launcher) ([install commands](./docs/en/claude-code-setup.md#dont-have-the-cli-yet)) — runs natively on Windows, macOS (Apple Silicon), Linux, and WSL2. The Studio **runner** (not the CLI) needs WSL2 on Windows.
- Early access to a Huitzo Hub. Every exercise is built and tested locally without one.

**Optional:** [Claude Code](https://code.claude.com/docs/en/overview) plus the [Huitzo developer environment](./docs/en/claude-code-setup.md), if you want an AI agent that already knows the SDK.

## Contributing

New packs are welcome, especially community templates. See [CONTRIBUTING.md](./CONTRIBUTING.md) and look for issues labeled `good first issue`. Security reports go to [SECURITY.md](./SECURITY.md).

## License

[MIT](./LICENSE). Build on these freely.
