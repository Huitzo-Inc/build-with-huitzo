# CLAUDE.md

Public learning repository: graded example projects ("rungs") for building on Huitzo. Read
`README.md` for the ladder and `CONTRIBUTING.md` for the ground rules; this file only lists what an
agent cannot infer from the code.

## Layout

- `projects/<rung>/pack/` is an Intelligence Pack: `huitzo.yaml`, Python commands, offline tests.
- `projects/<rung>/dashboard/` is a React/TypeScript dashboard that builds `dist/main.js` and runs
  against a `dev.tsx` mock context, no Hub needed.
- `projects/05-pack-from-outside/` is client code (REST, CLI, MCP, CI), not a pack.
- `docs/en/` is the source of every guide; `docs/es/` and `README.es.md` are reviewed derivatives.
- `tests/test_regression_gate.py` and `.github/workflows/` are the CI contract.

## Local checks (run before a pull request)

```bash
cd projects/<rung>/pack && pip install -e ".[dev]" && pytest -q        # a pack
cd projects/<rung>/dashboard && npm install && npm test && npm run build  # a dashboard
python scripts/check_i18n_staleness.py                                   # after editing any English .md
python scripts/check_i18n_staleness.py --fix                             # only after the Spanish is reviewed
```

## Rules that CI or the reviewers enforce

- Deterministic Python owns the decision; the model is called only where it adds value.
- Never name a model in pack code. Use `ctx.llm.complete(..., profile="default")`.
- Type inputs and outputs with Pydantic and pass `schema=` so the model returns a validated instance.
- Every pack ships tests that run offline against a mock `ctx`; `projects/00-hello-pack` is the shape.
- Edit English files only. Fix content in `docs/en/` or `README.md`, never in a Spanish file.
- Public copy has no em dashes and no internal jargon. Lead with what the developer builds.
- Examples are scoped to the `@reef` namespace. Do not point them at a real Hub in the repo.
- Keep a pull request to one rung or one fix.

## Working with an agent

- `.claude/` is gitignored on purpose. Per-machine settings stay local; do not commit them.
- The supported agent setup is the `huitzo` plugin from `Huitzo-Inc/pack-claude-env`
  (`/plugin marketplace add Huitzo-Inc/pack-claude-env`, then `/plugin install huitzo@huitzo`).
  Run `/huitzo:huitzo-init` inside a rung; see `docs/en/claude-code-setup.md`.
- Only public knowledge belongs here: docs.huitzo.ai, the published `huitzo-sdk` and
  `@huitzo/dashboard-sdk*` packages, and `huitzo --help`. No company facts, no private links.
