# Dashboard D6: ship-it

> Read this in [Español](./README.es.md).

Every other rung ends with "run it locally." This one is about the step after that: getting a dashboard onto a real Hub without discovering the problem once it is already published.

The one idea to carry out of here: **almost every failed publish is a mistake you could have caught offline.** A version that drifted between two files, a command you call but never declared, a bundle that compiled perfectly and forgot to export the one function Hub calls. None of those need a Hub account to find — they need someone to look. `scripts/preflight.mjs` is that someone.

**You will learn:** what the dashboard manifest actually promises Hub, why `pack_dependencies` is not documentation, the publish lifecycle (`validate` → `build` → `publish`), how to version against a command contract, and how to write a preflight you can copy into every project you ship.

**Time:** about thirty minutes.

## Prerequisites

- Node 20+ and npm
- [D0: `d0-hello-dashboard`](../d0-hello-dashboard) for the `mount`/`unmount` contract
- A Hub account only for the final two commands. Everything up to them runs offline.

## Run it

```bash
cd dashboard
npm install
npm test            # 8 tests — the view, including the governed states
npm run preflight   # builds, then checks everything publish would reject
```

The preflight passes with one warning, on purpose:

```
⚠  namespace is still "reef"
   The examples are scoped to an org you do not own. Change it before publishing for real.
✔  preflight passed for reef/ship-it@0.1.0 (1 warning(s)).
   Next: huitzo dashboard validate && huitzo dashboard publish
```

That warning is the first thing you fix when this becomes your dashboard rather than an example.

## What the manifest promises

`huitzo-dashboard.yaml` is not a description. Every field is a promise Hub relies on:

| Field | What Hub does with it |
|---|---|
| `name` + `namespace` | The identity it publishes under. Together they are the address. |
| `version` | Orders releases. Must be semver, and must match `package.json`. |
| `pack_dependencies` | Shows "required packs" on the Explore page, and checks the tenant actually has them. |
| `build.entry_point` | The file it imports and calls `mount()` on. |
| `build.min_sdk_version` | Refuses to load the dashboard on an older Hub. |

## The seven checks

`scripts/preflight.mjs` has no dependencies and takes about a second. Copy it into any dashboard and it works unchanged.

**1. The manifest exists and carries its required fields.** Hub cannot key a dashboard without `name`, `namespace` and `version`.

**2. The version is semver.** Hub orders releases by it. `v1` cannot be ranked.

**3. `package.json` and the manifest agree on that version.** They each carry one, and they drift the first time somebody bumps one and forgets the other. Then the version Hub shows is not the version you built — and you will not notice, because nothing errors.

**4. Every command the code calls has its pack declared.** This is the check that earns the script:

```js
// A command id is just a string, so nothing stops you calling a pack you
// never declared. It compiles. It tests green. Hub has no idea you need it.
if (!declared.has(pack)) fail(`the code calls ${id} but ${pack} is not in pack_dependencies`);
```

**5. A declared pack that is never called is a warning.** Stale dependencies make your dashboard look like it needs more installed than it does.

**6. The built bundle really exports `mount` and `unmount`.** The single most common way a dashboard builds cleanly and then refuses to load. Neither `tsc` nor vitest ever looks inside `dist/`, so nothing else catches it:

```js
const mod = await import(pathToFileURL(distPath).href);
for (const fn of ["mount", "unmount"]) {
  if (typeof mod[fn] !== "function") fail(`the bundle does not export ${fn}()`);
}
```

**7. You are publishing to an org you own.** A warning while `namespace: reef`.

Every one of these was verified by breaking it on purpose and watching the right check fail — a gate nobody has seen fail is not a gate.

## Then publish

```bash
huitzo dashboard validate     # full schema check, server-side rules
huitzo dashboard build        # runs npm run build
huitzo dashboard publish      # uploads dist/main.js as a new version
```

`validate` and the preflight overlap deliberately. The preflight is yours, runs offline in a second, and can check things only you know (that your command ids match your code). `validate` is the platform's, and is the authority.

Then open it from Hub at `https://hub.huitzo.com/d/ship-it`. There are no separate dashboard URLs; Hub is the single entry point and your dashboard shares its session.

> Re-scope first: change `namespace:` in `huitzo-dashboard.yaml` to an org you own, and the command ids in `src/types.ts` to match. See [Run on your own Hub](../../README.md#run-on-your-own-hub).

## Versioning against a command contract

The dashboard and the pack ship on their own cadences, coupled only by the command id and the result shape. That gives you a simple rule:

- The pack changes its **internals** — nothing to do. That is the whole point of the contract.
- The pack **adds** an optional field — nothing to do. Your `types.ts` is a subset; extra fields are ignored.
- The pack **renames or removes** a field you render, or changes a command id — that is a breaking change on the contract. Bump the dashboard and pin `pack_dependencies` to a version range that excludes the old pack.

`version: "*"` in `pack_dependencies` is fine for an example. For anything real, pin it, because `"*"` means "any version, including the one that broke you."

## Why the UI here shows governance

The panel renders a `recommend` result from [`02-grounded-reco`](../02-grounded-reco), and it treats `withheld` and `escalated` as **first-class states rather than errors**. A governed pack that withholds a result has not failed — it has done exactly its job, and the interface has to say so instead of showing a blank panel or a red toast.

That is a preview of D5, which builds the whole governed interface: `TemplateFrame`, `ResultSection`, and an `EvidenceLink` to the audit record.

## Next

That is Phase 1 of the dashboard track. The remaining rungs — declarative forms, streaming and queued commands, and the governed interface — are listed on [the learning path](../../docs/en/index.md#the-dashboard-path). The capstone both paths share is [`06-fullstack-triage`](../06-fullstack-triage).
