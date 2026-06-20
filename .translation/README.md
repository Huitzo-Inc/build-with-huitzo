# Bilingual system

This repo is English and Spanish. You only ever hand-edit English.

## The three rules

1. **Code is one tree.** All example code, comments, and identifiers are in English (the universal default). Code is never duplicated per language. A fix happens in one place.
2. **English is the source of truth.** Every `.md` file is authored in English. Reference and deep explanation are not duplicated here at all; they live once at [docs.huitzo.ai](https://docs.huitzo.ai/docs/). This repo carries only the tutorials that are tied to the code.
3. **Spanish is a reviewed derivative.** Each Spanish file is a translation of a specific English file, and it declares which version it was translated from.

## How a Spanish file stays honest

Every Spanish file (`*.es.md`, or anything under `docs/es/`) starts with a marker:

```
<!-- i18n-source-sha: <sha256 of the English source file> -->
```

The `i18n` CI job ([`../scripts/check_i18n_staleness.py`](../scripts/check_i18n_staleness.py)) recomputes the English file's sha256 and compares. If English changed and the Spanish file was not re-reviewed, the marker no longer matches, the file is flagged **stale**, and the build fails. Spanish can never silently rot.

## The workflow

1. Edit the English file.
2. CI flags the Spanish counterpart as stale.
3. A model drafts the Spanish update (the secret-gated drafting workflow), opening a PR. Or you update it by hand.
4. A human reviews the Spanish.
5. Run `python scripts/check_i18n_staleness.py --fix` to stamp the current English sha, then commit.

Pairing rules used by the gate:

| Spanish file | English source |
|--------------|----------------|
| `<name>.es.md` | `<name>.md` (same directory) |
| `docs/es/<path>` | `docs/en/<path>` |

This is Huitzo's own thesis dogfooded: an AI model does the heavy lifting on your content, with a deterministic guardrail that keeps it correct.
