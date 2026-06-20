#!/usr/bin/env python3
"""Block Spanish files from drifting out of date with their English source.

English is the single source of truth. Every Spanish file declares the sha256
of the exact English file it was translated from, in a marker near the top:

    <!-- i18n-source-sha: <64 hex chars> -->

This gate recomputes the English sha and compares. If they differ (English
changed and Spanish was not re-reviewed), the file is STALE and the build fails.

Pairing rules:
  - <name>.es.md            <-> <name>.md            (same directory)
  - docs/es/<path>          <-> docs/en/<path>

Usage:
  python scripts/check_i18n_staleness.py          # check, exit 1 if stale
  python scripts/check_i18n_staleness.py --fix     # stamp current English sha
                                                   # (run after a human reviews
                                                   #  the translation)
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARKER = re.compile(r"<!--\s*i18n-source-sha:\s*([0-9a-fA-F]{64}|PENDING)\s*-->")


def english_source_for(es_path: Path) -> Path | None:
    """Return the English source path for a Spanish file, or None if unmapped."""
    posix = es_path.as_posix()
    if "/docs/es/" in posix or posix.endswith("docs/es") or "/es/" in posix and "/docs/" in posix:
        return Path(posix.replace("/docs/es/", "/docs/en/", 1))
    if es_path.name.endswith(".es.md"):
        return es_path.with_name(es_path.name[: -len(".es.md")] + ".md")
    return None


def spanish_files() -> list[Path]:
    files = set(ROOT.rglob("*.es.md"))
    docs_es = ROOT / "docs" / "es"
    if docs_es.exists():
        files.update(p for p in docs_es.rglob("*.md"))
    return sorted(p for p in files if ".venv" not in p.parts and "node_modules" not in p.parts)


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def declared_sha(text: str) -> str | None:
    m = MARKER.search(text)
    return m.group(1) if m else None


def stamp(es_path: Path, sha: str) -> None:
    text = es_path.read_text(encoding="utf-8")
    marker = f"<!-- i18n-source-sha: {sha} -->"
    if MARKER.search(text):
        text = MARKER.sub(marker, text, count=1)
    else:
        text = marker + "\n" + text
    es_path.write_text(text, encoding="utf-8")


def main() -> int:
    fix = "--fix" in sys.argv
    stale: list[str] = []
    missing_source: list[str] = []
    fixed: list[str] = []

    for es in spanish_files():
        rel = es.relative_to(ROOT).as_posix()
        en = english_source_for(es)
        if en is None:
            missing_source.append(f"{rel}: cannot map to an English source")
            continue
        if not en.exists():
            missing_source.append(f"{rel}: English source {en.relative_to(ROOT).as_posix()} not found")
            continue

        current = sha256_of(en)
        if fix:
            stamp(es, current)
            fixed.append(rel)
            continue

        declared = declared_sha(es.read_text(encoding="utf-8"))
        if declared != current:
            reason = "no marker" if declared is None else ("PENDING" if declared == "PENDING" else "out of date")
            stale.append(f"{rel}  ({reason}; English source changed)")

    if fix:
        for f in fixed:
            print(f"stamped {f}")
        print(f"\nStamped {len(fixed)} Spanish file(s) with the current English sha.")
        return 0

    if missing_source:
        print("Unmapped Spanish files:")
        for m in missing_source:
            print(f"  - {m}")

    if stale:
        print("\nSTALE translations (English changed, Spanish not re-reviewed):")
        for s in stale:
            print(f"  - {s}")
        print(
            "\nFix: update the Spanish file, then run "
            "`python scripts/check_i18n_staleness.py --fix` to stamp it."
        )
        return 1

    if missing_source:
        return 1

    print(f"All {len(spanish_files())} Spanish file(s) are in sync with their English source.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
