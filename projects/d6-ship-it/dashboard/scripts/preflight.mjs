#!/usr/bin/env node
// Preflight: everything that would otherwise fail AFTER you publish.
//
// `huitzo dashboard publish` needs a Hub account, so you cannot rehearse it on a
// laptop. But almost every failed publish is one of a handful of mistakes that are
// perfectly checkable offline — a version that drifted between two files, a
// command you call but never declared, a bundle that built fine and forgot to
// export the one function Hub calls. This script finds those in about a second.
//
//   node scripts/preflight.mjs          # after npm run build
//   npm run preflight                   # builds first, then runs this
//
// Exit code 0 means ship it. Non-zero prints what to fix and why it matters.
// Warnings (⚠) do not fail the run; they are things that are fine for an example
// in this repo and wrong for anything you actually publish.

import { readFileSync, existsSync, readdirSync, statSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const errors = [];
const warnings = [];

const fail = (what, why) => errors.push({ what, why });
const warn = (what, why) => warnings.push({ what, why });

// ---------------------------------------------------------------------------
// 1. The manifest parses and carries what Hub needs.
// ---------------------------------------------------------------------------
// Deliberately a hand-rolled reader for the flat keys we need rather than a YAML
// dependency: a preflight you can copy into any project beats a tidy one you
// cannot. `huitzo dashboard validate` does the full schema check.
const manifestPath = join(root, "huitzo-dashboard.yaml");
if (!existsSync(manifestPath)) {
  fail("huitzo-dashboard.yaml is missing", "Hub cannot register a dashboard without a manifest.");
}
const manifestText = existsSync(manifestPath) ? readFileSync(manifestPath, "utf8") : "";
const scalar = (key) => {
  const m = manifestText.match(new RegExp(`^\\s{2}${key}:\\s*["']?([^"'\\n#]+?)["']?\\s*(?:#.*)?$`, "m"));
  return m ? m[1].trim() : null;
};

const name = scalar("name");
const namespace = scalar("namespace");
const version = scalar("version");
const entryPoint = scalar("entry_point");

for (const [key, value] of Object.entries({ name, namespace, version })) {
  if (!value) fail(`dashboard.${key} is missing from the manifest`, "Hub keys the dashboard on it.");
}

// ---------------------------------------------------------------------------
// 2. The version is semver, and the two files agree on it.
// ---------------------------------------------------------------------------
// package.json and huitzo-dashboard.yaml each carry a version. They drift the
// first time someone bumps one and forgets the other, and then the version Hub
// shows is not the version you built.
const pkg = JSON.parse(readFileSync(join(root, "package.json"), "utf8"));
if (version && !/^\d+\.\d+\.\d+([-+].+)?$/.test(version)) {
  fail(`version "${version}" is not semver`, "Hub orders releases by semver; a bad one cannot be ranked.");
}
if (version && pkg.version !== version) {
  fail(
    `version drift: package.json says ${pkg.version}, huitzo-dashboard.yaml says ${version}`,
    "Bump both, or the version Hub publishes is not the one you think you built.",
  );
}

// ---------------------------------------------------------------------------
// 3. Every command the code calls has its pack declared.
// ---------------------------------------------------------------------------
// This is the check that earns the script. A command id is a plain string in
// TypeScript, so nothing stops you calling @reef/some-pack/thing without ever
// declaring @reef/some-pack in pack_dependencies. It compiles, it tests green,
// and Hub then has no idea your dashboard depends on that pack.
const srcFiles = [];
(function walk(dir) {
  for (const entry of readdirSync(dir)) {
    const p = join(dir, entry);
    if (statSync(p).isDirectory()) walk(p);
    else if (/\.(ts|tsx)$/.test(entry) && !/\.test\.tsx?$/.test(entry)) srcFiles.push(p);
  }
})(join(root, "src"));

// Module specifiers are stripped first. A scoped npm subpath import such as
// `@huitzo/dashboard-sdk-react/styles` is shaped exactly like a command id, so
// scanning raw source reports it as an undeclared pack. Removing the specifiers
// is the difference between a check people trust and one they learn to ignore.
const stripModuleSpecifiers = (src) =>
  src
    .replace(/\bfrom\s*["'][^"']+["']/g, "") // import x from "…" / export … from "…"
    .replace(/\bimport\s*["'][^"']+["']/g, "") // side-effect import "…"
    .replace(/\bdeclare\s+module\s*["'][^"']+["']/g, ""); // ambient decl in *.d.ts

const called = new Set();
for (const f of srcFiles) {
  const src = stripModuleSpecifiers(readFileSync(f, "utf8"));
  for (const m of src.matchAll(/["'`](@[a-z0-9-]+\/[a-z0-9-]+\/[a-z0-9-]+)["'`]/g)) {
    called.add(m[1]);
  }
}

const declared = new Set();
for (const m of manifestText.matchAll(/scope:\s*["']?(@[a-z0-9-]+)["']?[\s\S]*?name:\s*["']?([a-z0-9-]+)["']?/g)) {
  declared.add(`${m[1]}/${m[2]}`);
}

for (const id of called) {
  const pack = id.split("/").slice(0, 2).join("/");
  if (!declared.has(pack)) {
    fail(
      `the code calls ${id} but ${pack} is not in pack_dependencies`,
      "Hub uses pack_dependencies to show required packs and to check the tenant has them installed.",
    );
  }
}
for (const pack of declared) {
  if (![...called].some((id) => id.startsWith(`${pack}/`))) {
    warn(`${pack} is declared but never called`, "A stale dependency makes your dashboard look like it needs more than it does.");
  }
}

// ---------------------------------------------------------------------------
// 4. The built bundle actually exports the Hub contract.
// ---------------------------------------------------------------------------
// The single most common way a dashboard builds cleanly and then fails to load:
// the bundle is fine, and it does not export mount/unmount. Nothing in `tsc` or
// vitest checks this, because neither ever looks at dist/.
const distPath = join(root, "dist", entryPoint ?? "main.js");
if (!existsSync(distPath)) {
  fail(`dist/${entryPoint ?? "main.js"} does not exist`, "Run `npm run build` first — publish uploads this file.");
} else {
  const mod = await import(pathToFileURL(distPath).href).catch((e) => {
    fail(`dist/${entryPoint ?? "main.js"} could not be imported: ${e.message}`, "Hub imports it exactly this way.");
    return null;
  });
  if (mod) {
    for (const fn of ["mount", "unmount"]) {
      if (typeof mod[fn] !== "function") {
        fail(`the bundle does not export ${fn}()`, "Hub calls it by name; without it the dashboard never renders.");
      }
    }
  }
}

// ---------------------------------------------------------------------------
// 5. You are publishing to an org you own.
// ---------------------------------------------------------------------------
if (namespace === "reef") {
  warn(
    'namespace is still "reef"',
    "The examples are scoped to an org you do not own. Change it before publishing for real.",
  );
}

// ---------------------------------------------------------------------------
// Report.
// ---------------------------------------------------------------------------
const label = `${namespace ?? "?"}/${name ?? "?"}@${version ?? "?"}`;
for (const { what, why } of warnings) console.warn(`⚠  ${what}\n   ${why}`);
for (const { what, why } of errors) console.error(`✖  ${what}\n   ${why}`);

if (errors.length) {
  console.error(`\npreflight FAILED for ${label} — ${errors.length} blocking issue(s).`);
  process.exit(1);
}
console.log(`✔  preflight passed for ${label}${warnings.length ? ` (${warnings.length} warning(s))` : ""}.`);
console.log("   Next: huitzo dashboard validate && huitzo dashboard publish");
