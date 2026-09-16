# Build with an AI agent

> **Illustrated walkthrough:** the same steps with screenshots are in
> [the step-by-step install guide](https://huitzo-my.sharepoint.com/:w:/g/personal/ernesto_huitzo_ai/IQBmjQk-U-pCRqonwrt9o7_CAQv1gfp3ruaT6oji1uEAX5w?e=549vuB).
> If you would rather just read commands, everything you need is on this page.

Every project in this repo is written to be read by a person *and* built on by an
AI coding agent. [`pack-claude-env`](https://github.com/Huitzo-Inc/pack-claude-env)
is the Huitzo developer environment for [Claude Code](https://code.claude.com/docs/en/overview):
it hands your agent verified API references, a docs-first workflow, reviewer
agents, and safety hooks, so the code it writes looks like the code in this repo.

This step is **optional**. Every rung here runs fine without it. But the moment
you stop copying examples and start writing your own pack, this is what keeps an
agent from inventing an SDK that does not exist.

**Time:** about five minutes.

## What it gives you

| | What it does |
|---|---|
| **Reference skills** | Exact, version-pinned API surfaces for `huitzo-sdk`, `huitzo.yaml`, the dashboard SDK, the CLI, and the platform REST API. The agent reads the real signature instead of guessing. |
| **Workflow skills** | `/draft-spec`, `/draft-docs`, `/add-command`, `/scaffold-dashboard`, `/test-pack`, `/validate-pack`, `/test-dashboard`, `/dashboard-dev`, `/sandbox`, `/publish`. |
| **Agents** | `pack-developer` and `dashboard-developer` to build; `pack-reviewer` and `dashboard-reviewer` to grade the result against a checklist; `docs-writer`, `spec-architect`. |
| **Path-scoped rules** | Rules that load only when a matching file is edited — SDK patterns, error handling, testing, the manifest, traceability, Hub contract, React patterns, dashboard design. |
| **Safety hooks** | A blocking secrets scan on writes, plus non-blocking nudges for missing traceability headers, hex colours in dashboards, a hard-coded `model=` on `ctx.llm`, and `dangerouslySetInnerHTML`. |

That `model=` nudge is the repo's whole thesis enforced at the keystroke: a pack
asks for a **profile**, never a named model. See [The aha moment](./the-aha-moment.md).

## Install it as a Claude Code plugin (recommended)

Inside Claude Code, run these two commands:

```text
/plugin marketplace add Huitzo-Inc/pack-claude-env
/plugin install huitzo@huitzo
```

Then open a pack, dashboard, or project directory and run:

```text
/huitzo:huitzo-init
```

`huitzo-init` **shows you a plan and asks before writing anything.** It adds the
path-scoped rules to `.claude/rules/`, a managed block to `CLAUDE.md` and
`AGENTS.md`, and `CONSTITUTION.md`. If the project has a `docs/` directory it also
registers the `pack-docs` MCP server in `.mcp.json`. It never overwrites an
existing file and never touches `settings.json`.

Skills are then available as `/huitzo:<skill>`; agents and hooks are live as soon
as the plugin is enabled.

### Try it on this repo

The fastest way to see the difference is to point it at a rung you have already
finished:

```text
cd projects/00-hello-pack/pack
/huitzo:huitzo-init
```

Then ask the agent to add a second command. Watch it read the `huitzo-sdk`
reference skill before it writes, scaffold the args model and the test alongside
the command, and register it in `huitzo.yaml` — the same shape as the command
that is already there.

## Or let the Huitzo CLI seed it

If you are starting a brand-new project rather than working in this repo, the CLI
offers the same environment as it scaffolds:

```bash
huitzo pack new my-pack          # → "Would you like to set up a Claude Code environment?" → yes
huitzo dashboard new my-dash     # same prompt
huitzo project init my-project   # seeded silently (pack + dashboard)
```

The CLI copies the environment into the project's `.claude/` directory, filtered
by profile, and puts `CONSTITUTION.md` next to it. Skills are available as
`/<skill>` (no `huitzo:` prefix on this channel). Run `/huitzo-init` once to wire
up the project docs MCP server.

Three profiles decide what gets seeded: `full-stack` (the default), `pack-only`,
and `dashboard-only`.

> **Pick one channel per project.** The plugin and the seed both work, but if you
> install both, the hooks run twice.

## Don't have the CLI yet?

```bash
# macOS / Linux / WSL2
curl -sSf https://raw.githubusercontent.com/Huitzo-Inc/huitzo-launcher/main/install.sh | sh
```

```powershell
# Windows (PowerShell)
iwr -useb https://raw.githubusercontent.com/Huitzo-Inc/huitzo-launcher/main/install.ps1 | iex
```

macOS is Apple Silicon only; Homebrew also works:
`brew install Huitzo-Inc/tap/huitzo`.

## Keeping it current

```text
/plugin update huitzo
/huitzo:huitzo-init     # refresh the managed blocks and rules
```

Existing files are never overwritten, so to receive a new version of a rule,
delete your copy of that rule file and re-run `huitzo-init`. On the seed channel,
re-run `/huitzo-init` or copy `claude/` from a fresh clone over `.claude/`.

## Two different MCP servers

Do not confuse them:

- **`pack-docs`** (project-local) serves *your own* `docs/` directory to the
  agent. `/huitzo-init` writes it into `.mcp.json` when `docs/` exists. It needs
  `pip install "your-docs-mcp==1.1.2" "mcp<2"` in the project environment.
- **The Hub-hosted docs server**, configured by `huitzo mcp setup docs`, serves
  the *platform* documentation into your user-level Claude settings.

A third, `@huitzo/dashboard-mcp`, exposes a dashboard's commands, primitives, and
brand tokens to any MCP-aware client — useful on the dashboard rungs.

## Next

Go build something: [Tier 0: hello-pack](../../projects/00-hello-pack) if you are
starting out, or the [learning path](./index.md) for the full map.
