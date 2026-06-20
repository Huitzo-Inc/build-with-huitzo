# Contributing

Thanks for helping people learn Huitzo. New packs, fixes, and community templates are all welcome. Look for issues labeled `good first issue`.

## Ground rules for an example pack

- **Deterministic Python first.** The model is an augmentation, not the processor. If deterministic code can decide it, deterministic code decides it. A pack that is only an LLM call is not a good example here.
- **Never name a model in pack code.** Call `ctx.llm.complete(..., profile="default")`. Model selection is a deployment concern.
- **Type your input and output** with Pydantic models. Use `schema=` so the model returns a validated instance.
- **Every pack ships with tests that run offline** (mock `ctx`), so the example passes CI without a live model. See `projects/00-hello-pack` for the reference shape.
- **Public copy has no em-dashes** and avoids internal jargon. Lead with what the developer builds.

## Not every rung is a pack

Most rungs are Intelligence Packs (a `pack/` directory). Two kinds are not, on purpose:

- **Dashboards** (Tiers 4 and 6) are React/TypeScript apps in a `dashboard/` directory. They consume a pack via the Dashboard SDK and ship a `dist/main.js` that exports `mount`/`unmount`. They run and test locally with no Hub via a `dev.tsx` mock context.
- **The outside-in rung** (Tier 5) is client code, not a pack: no `pack/` and no `huitzo.yaml`. It drives a deployed pack from REST, the CLI, MCP, and CI.

The pack ground rules above still apply in spirit: deterministic-first, no model names in code, typed boundaries, offline tests.

## Publishing on a Hub

The examples are scoped to the `@reef` org. To publish or run one on a real Hub, re-scope it to an org you own: change `namespace:` in `huitzo.yaml` (and `huitzo-dashboard.yaml` for dashboards) and run `huitzo pack sync`. The deployment also has to have what the pack needs (an LLM model meeting the `services.llm` floor, and any HTTP integration the pack calls). See [Run on your own Hub](./README.md#run-on-your-own-hub).

## Local checks

```bash
# A pack
cd projects/<rung>/pack
pip install -e ".[dev]"
pytest -q

# A dashboard (Tiers 4, 6)
cd projects/<rung>/dashboard
npm install
npm test          # offline component tests (jsdom)
npm run build     # typechecks and bundles dist/main.js

# The outside-in client rung (Tier 5)
cd projects/05-pack-from-outside/python
pip install -e ".[dev]"
pytest -q

# The bilingual gate (after editing any English .md)
python scripts/check_i18n_staleness.py        # check
python scripts/check_i18n_staleness.py --fix  # stamp after the Spanish is reviewed
```

## Translations

Edit the **English** file only. The Spanish counterpart is a reviewed derivative kept in sync by the i18n gate. See [.translation/README.md](./.translation/README.md). Do not fix content by editing a Spanish file; fix the English and re-translate.

## Pull requests

Keep PRs focused on one rung or one fix. CI runs the pack tests and the i18n gate; both must be green.
