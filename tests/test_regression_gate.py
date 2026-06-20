"""Regression gate: one offline test per bug class found in the staging e2e sweep.

The rule this file enforces is simple: **no exercise ships unless it stays green
here.** Each of the seven core-path bugs that the 2026-06 staging sweep found and
fixed is encoded below as a repo-side invariant, so the *class* of bug can never
quietly come back through a new pack, a new dashboard, or an edit to an old one.

These tests are pure static analysis (AST + YAML + text). They need no network,
no Hub, and no model — they run in milliseconds in CI and lock in the discipline
that made every demo run on the first try.

Bug classes (each found and fixed during an end-to-end sweep of the exercises):
  1. Structured output not enum-reliable — a Literal/enum slice sent to the model
     whose prompt never lists the allowed values. → every such prompt must.
  2. Structured output via `schema=` — a typed command must hand the model a
     Pydantic schema, not coax JSON from prose. → schema= usage is a BaseModel.
  3. Pipelines dropped on publish / 4. stage refs unresolved — a pipeline stage
     must reference a command declared in the same pack.
  5. Tier-5 client request shapes — REST wraps args under "args" and uses the
     full @scope/pack/command path; MCP uses /mcp/ with an SSE Accept header.
  6. Dashboards crash "process is not defined" — a dashboard vite.config must
     define process.env.NODE_ENV AND install a process shim.
  7. Pydantic command results — every @command returns a Pydantic model (the
     contract the backend serializes at the HTTP boundary).
"""

from __future__ import annotations

import ast
import tomllib
from pathlib import Path

import pytest

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - CI installs pyyaml
    yaml = None  # type: ignore[assignment]

ROOT = Path(__file__).resolve().parent.parent
PROJECTS = ROOT / "projects"


def _pack_dirs() -> list[Path]:
    return sorted(p.parent for p in PROJECTS.glob("*/pack/huitzo.yaml"))


def _pack_py_files(pack: Path) -> list[Path]:
    return sorted((pack / "src").rglob("*.py"))


def _pack_id(pack: Path) -> str:
    return pack.parent.name


PACKS = _pack_dirs()
PACK_IDS = [_pack_id(p) for p in PACKS]


# --------------------------------------------------------------------------- #
# Shared AST helpers
# --------------------------------------------------------------------------- #
def _literal_values(node: ast.expr, aliases: dict[str, list[str]] | None = None) -> list[str] | None:
    """Return the string members of a ``Literal[...]`` annotation, else None.

    Handles ``Literal["a", "b"]``, the ``X | None`` optional wrapper, and a
    ``Name`` that refers to a module-level Literal alias (e.g. a field annotated
    ``category: Category`` where ``Category = Literal[...]``) when ``aliases`` is
    supplied. Resolving aliases is essential — every pack defines its enums as
    aliases, so without this the enum check would pass vacuously.
    """
    aliases = aliases or {}
    if isinstance(node, ast.Name) and node.id in aliases:
        return aliases[node.id]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        # Optional[X] written as ``X | None`` — recurse into both sides.
        for side in (node.left, node.right):
            vals = _literal_values(side, aliases)
            if vals is not None:
                return vals
        return None
    if isinstance(node, ast.Subscript):
        base = node.value
        if isinstance(base, ast.Name) and base.id == "Literal":
            elts = node.slice.elts if isinstance(node.slice, ast.Tuple) else [node.slice]
            out = [e.value for e in elts if isinstance(e, ast.Constant) and isinstance(e.value, str)]
            return out or None
    return None


def _collect_pack_facts(pack: Path) -> dict:
    """Parse every module in a pack once and extract the facts the gate needs."""
    literal_aliases: dict[str, list[str]] = {}          # Name -> [values]
    class_literal_fields: dict[str, dict[str, list[str]]] = {}  # ClassName -> {field: [values]}
    schema_args: set[str] = set()                       # class names passed as schema=
    prompt_text_parts: list[str] = []                   # text of *PROMPT* string constants
    command_returns: list[tuple[str, ast.expr | None]] = []  # (cmd name, return annotation)
    basemodel_classes: set[str] = set()                 # classes that subclass BaseModel

    trees = {py: ast.parse(py.read_text(encoding="utf-8"), filename=str(py)) for py in _pack_py_files(pack)}

    # Pass 1: collect Literal aliases across the whole pack first, so class field
    # annotations that reference an alias (the universal convention) resolve.
    for tree in trees.values():
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                tgt = node.targets[0]
                vals = _literal_values(node.value)
                if isinstance(tgt, ast.Name) and vals is not None:
                    literal_aliases[tgt.id] = vals

    # Pass 2: everything else, resolving field annotations against the aliases.
    for tree in trees.values():
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                tgt = node.targets[0]
                if isinstance(tgt, ast.Name) and "PROMPT" in tgt.id.upper():
                    folded = _fold_str(node.value)
                    if folded:
                        prompt_text_parts.append(folded)

            # Class field annotations + BaseModel detection
            if isinstance(node, ast.ClassDef):
                if any(isinstance(b, ast.Name) and b.id.endswith("BaseModel") for b in node.bases) or any(
                    isinstance(b, ast.Attribute) and b.attr.endswith("BaseModel") for b in node.bases
                ) or any(isinstance(b, ast.Name) and b.id in basemodel_classes for b in node.bases):
                    basemodel_classes.add(node.name)
                fields: dict[str, list[str]] = {}
                for stmt in node.body:
                    if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                        vals = _literal_values(stmt.annotation, literal_aliases)
                        if vals is not None:
                            fields[stmt.target.id] = vals
                if fields:
                    class_literal_fields[node.name] = fields

            # ctx.llm.complete(... schema=X ...) / .chat(...)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr in {"complete", "chat"}:
                    for kw in node.keywords:
                        if kw.arg == "schema" and isinstance(kw.value, ast.Name):
                            schema_args.add(kw.value.id)

            # @command(...) decorated functions -> return annotation
            if isinstance(node, ast.AsyncFunctionDef | ast.FunctionDef):
                for dec in node.decorator_list:
                    dfunc = dec.func if isinstance(dec, ast.Call) else dec
                    if (isinstance(dfunc, ast.Name) and dfunc.id == "command") or (
                        isinstance(dfunc, ast.Attribute) and dfunc.attr == "command"
                    ):
                        command_returns.append((node.name, node.returns))

    return {
        "literal_aliases": literal_aliases,
        "class_literal_fields": class_literal_fields,
        "schema_args": schema_args,
        "prompt_text": "\n".join(prompt_text_parts),
        "command_returns": command_returns,
        "basemodel_classes": basemodel_classes,
    }


def _fold_str(node: ast.expr) -> str:
    """Best-effort flatten of a string constant / implicit-concat / simple join."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(v.value for v in node.values if isinstance(v, ast.Constant) and isinstance(v.value, str))
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _fold_str(node.left) + _fold_str(node.right)
    return ""


# --------------------------------------------------------------------------- #
# Bug 1 — enum-reliability: a model-decided Literal must be enumerated in the prompt
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("pack", PACKS, ids=PACK_IDS)
def test_bug1_model_enum_values_are_listed_in_the_prompt(pack: Path) -> None:
    """Every Literal field on a schema= model must have its values named in the prompt.

    This is the bug-7 keystone seen from the pack side: forced tool-use makes the
    model return well-shaped JSON, but it does not hard-enforce a Literal, so a
    vague prompt ("choose from the allowed set") lets the model emit an
    out-of-enum value. Listing the values in the prompt is the cheap, first-try
    fix; the backend's validation-retry is the safety net.
    """
    facts = _collect_pack_facts(pack)
    prompt = facts["prompt_text"].lower()
    offenders: list[str] = []
    for cls in sorted(facts["schema_args"]):
        for field, values in facts["class_literal_fields"].get(cls, {}).items():
            for v in values:
                if v.lower() not in prompt:
                    offenders.append(f"{cls}.{field} value '{v}' is not named in the prompt")
    assert not offenders, (
        f"{_pack_id(pack)}: a model-decided enum is not enumerated in the prompt "
        f"(bug 1 / enum-reliability):\n  - " + "\n  - ".join(offenders)
    )


# --------------------------------------------------------------------------- #
# Bug 2 — typed output uses a Pydantic schema, not coaxed-from-prose JSON
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("pack", PACKS, ids=PACK_IDS)
def test_bug2_schema_arg_is_a_pydantic_model(pack: Path) -> None:
    """Anything handed to ctx.llm via schema= must be a Pydantic BaseModel in this pack."""
    facts = _collect_pack_facts(pack)
    unknown = sorted(facts["schema_args"] - facts["basemodel_classes"])
    assert not unknown, (
        f"{_pack_id(pack)}: schema= is given a non-BaseModel (bug 2): {unknown}. "
        "Structured output must hand the model a Pydantic schema."
    )


# --------------------------------------------------------------------------- #
# Bugs 3 & 4 — pipeline stage refs resolve to a command declared in the pack
# --------------------------------------------------------------------------- #
@pytest.mark.skipif(yaml is None, reason="pyyaml not installed")
@pytest.mark.parametrize("pack", PACKS, ids=PACK_IDS)
def test_bug3_4_pipeline_stage_refs_resolve(pack: Path) -> None:
    """Each pipeline stage must reference a command declared in the same pack."""
    manifest = yaml.safe_load((pack / "huitzo.yaml").read_text(encoding="utf-8"))
    pipelines = manifest.get("pipelines") or {}
    if not pipelines:
        pytest.skip("no pipelines declared")
    pack_name = manifest["pack"]["name"]
    declared = {c["name"] for c in manifest.get("commands", [])}
    # ``pipelines`` is a mapping of pipeline-name -> definition.
    problems: list[str] = []
    for pipe_name, pipe in pipelines.items():
        for stage in pipe.get("stages", []):
            ref = stage.get("command", "")
            ref_pack, _, ref_cmd = ref.partition(":")
            where = f"{pipe_name}.{stage.get('name')}"
            if not ref_cmd:
                problems.append(f"stage '{where}' ref '{ref}' is not pack:command")
            elif ref_pack != pack_name:
                problems.append(f"stage '{where}' ref '{ref}' is cross-pack (pack '{ref_pack}')")
            elif ref_cmd not in declared:
                problems.append(f"stage '{where}' ref '{ref}' names no declared command")
    assert not problems, f"{_pack_id(pack)}: unresolved pipeline stage refs (bugs 3/4):\n  - " + "\n  - ".join(problems)


# --------------------------------------------------------------------------- #
# Bug 5 — Tier-5 client request shapes
# --------------------------------------------------------------------------- #
def test_bug5_rest_client_wraps_args_and_uses_full_path() -> None:
    """The Python REST client posts {"args": ...} to /api/v1/commands/@scope/pack/command."""
    src = (PROJECTS / "05-pack-from-outside" / "python" / "huitzo_client.py").read_text(encoding="utf-8")
    assert "/api/v1/commands/" in src, "REST client must hit /api/v1/commands/"
    assert '"args"' in src or "'args'" in src, "REST client must wrap the payload under 'args'"


def test_bug5_curl_uses_scoped_path_and_args() -> None:
    src = (PROJECTS / "05-pack-from-outside" / "curl" / "run.sh").read_text(encoding="utf-8")
    assert "/api/v1/commands/@" in src, "curl must use the full @scope/pack/command path"
    assert '"args"' in src, "curl must wrap the payload under 'args'"


def test_bug5_mcp_client_uses_slash_and_sse_accept() -> None:
    """MCP client must hit /mcp/ (trailing slash) and accept text/event-stream (SSE)."""
    src = (PROJECTS / "05-pack-from-outside" / "python" / "mcp_client.py").read_text(encoding="utf-8")
    assert "/mcp/" in src, "MCP client must use the trailing-slash /mcp/ URL (avoids the https->http redirect)"
    assert "text/event-stream" in src, "MCP client must send an SSE Accept header"


# --------------------------------------------------------------------------- #
# Bug 6 — dashboards must not crash "process is not defined" in the Hub
# --------------------------------------------------------------------------- #
DASHBOARDS = sorted(PROJECTS.glob("*/dashboard/vite.config.ts"))
DASHBOARD_IDS = [p.parent.parent.name for p in DASHBOARDS]


@pytest.mark.parametrize("vite_config", DASHBOARDS, ids=DASHBOARD_IDS)
def test_bug6_dashboard_vite_is_browser_safe(vite_config: Path) -> None:
    """A library-mode dashboard bundle must neutralize `process` for the browser."""
    src = vite_config.read_text(encoding="utf-8")
    assert "process.env.NODE_ENV" in src, (
        f"{vite_config}: missing the process.env.NODE_ENV define — React will read a "
        "bare `process` and the Hub mount crashes with 'process is not defined' (bug 6)."
    )
    assert "globalThis.process" in src or "banner" in src, (
        f"{vite_config}: missing the process shim banner — deps probing process.versions "
        "still crash the browser (bug 6)."
    )
    # Test-mode safety: the NODE_ENV define must gate "production" on the
    # production build, not on "not development". The broken form
    # (`mode === "development" ? "development" : "production"`) maps vitest's
    # "test" mode to "production", loading react-dom's prod internals so
    # `npm test` dies with "React.act is not a function". Require production to
    # be gated on `mode === "production"` (or a bare `JSON.stringify(mode)`).
    assert ('mode === "production"' in src) or ("JSON.stringify(mode)" in src), (
        f"{vite_config}: the process.env.NODE_ENV define resolves non-production modes "
        "(e.g. vitest's 'test') to 'production', which breaks `npm test`. Gate it on "
        '`mode === "production"`.'
    )


# --------------------------------------------------------------------------- #
# Bug 7 — every @command returns a Pydantic model (serializable at the boundary)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("pack", PACKS, ids=PACK_IDS)
def test_bug7_commands_return_a_pydantic_model(pack: Path) -> None:
    """Every @command returns a BaseModel defined in the pack (the serialized contract)."""
    facts = _collect_pack_facts(pack)
    problems: list[str] = []
    for name, returns in facts["command_returns"]:
        if returns is None:
            problems.append(f"command '{name}' has no return annotation")
        elif not isinstance(returns, ast.Name):
            problems.append(f"command '{name}' returns a non-class annotation")
        elif returns.id not in facts["basemodel_classes"]:
            problems.append(f"command '{name}' returns '{returns.id}', not a Pydantic model in this pack")
    assert not problems, f"{_pack_id(pack)}: @command return contract (bug 7):\n  - " + "\n  - ".join(problems)


# --------------------------------------------------------------------------- #
# Bug 8 — a manifest command with no pyproject entry point is a `huitzo run` dead end
# --------------------------------------------------------------------------- #
@pytest.mark.skipif(yaml is None, reason="pyyaml not installed")
@pytest.mark.parametrize("pack", PACKS, ids=PACK_IDS)
def test_bug8_manifest_commands_have_entry_points(pack: Path) -> None:
    """Every command in huitzo.yaml must be registered in pyproject.toml.

    The doc-to-json redesign rebuilt the wheel but left a hand-written
    pyproject.toml that registered only `extract-claim` — so the README's
    `huitzo run @reef/doc-to-json/seed-document` was a dead end (command not
    found). A manifest command with no entry point installs cleanly and then
    fails at runtime: the worst kind of first-run break. Also assert the
    pyproject version matches the manifest, so they cannot silently drift.
    """
    manifest = yaml.safe_load((pack / "huitzo.yaml").read_text(encoding="utf-8"))
    declared = {c["name"] for c in manifest.get("commands", [])}
    pyproject = tomllib.loads((pack / "pyproject.toml").read_text(encoding="utf-8"))
    eps = pyproject.get("project", {}).get("entry-points", {}).get("huitzo.commands", {})
    registered = {key.rsplit("/", 1)[-1] for key in eps}
    missing = sorted(declared - registered)
    assert not missing, (
        f"{_pack_id(pack)}: manifest commands with no pyproject entry point "
        f"(huitzo run will 'command not found'): {missing}. Run `huitzo pack sync`."
    )
    manifest_version = str(manifest["pack"]["version"])
    pyproject_version = str(pyproject.get("project", {}).get("version", ""))
    assert manifest_version == pyproject_version, (
        f"{_pack_id(pack)}: pyproject version {pyproject_version!r} != manifest "
        f"version {manifest_version!r} — they have drifted."
    )


def test_gate_actually_found_packs() -> None:
    """Guardrail: the gate must be pointed at the exercises, not silently empty."""
    assert len(PACKS) >= 7, f"expected the pack ladder, found only {PACK_IDS}"
    assert len(DASHBOARDS) >= 2, f"expected the dashboard exercises, found {DASHBOARD_IDS}"
