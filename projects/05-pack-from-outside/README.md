# Tier 5: pack-from-outside

> Read this in [Español](./README.es.md).

So far you have built things that run inside Huitzo: packs, a pipeline, a dashboard. This rung goes the other way. Reef Supply Co. has a deployed pack and wants to call it from their own systems: a shell script, a backend service, an AI assistant, a CI pipeline. This is how you drive a Huitzo pack from outside.

The one idea to carry out of here: **there is one mental model, and four doors into it.** REST, the CLI, the hosted MCP server, and a CI action are not four different products. They are four ways to do the same four steps:

```
  a key (commands:execute)  ->  execute a command  ->  sync result or async task  ->  unwrap {data: ...}
        REST  |  CLI  |  hosted MCP  |  CI action
```

**You will learn:** how to authenticate with an API key, how to execute a command over REST and handle the sync-versus-async split, how the CLI maps outcomes to exit codes, how the hosted MCP server lets Claude or Cursor call your pack, and how a CI action gates a merge on a pack's output.

**Time:** about forty minutes.

## A note on structure

This rung is a **client**, not a pack. It has no `pack/` directory and no `huitzo.yaml`, on purpose: you are consuming a pack, not authoring one. That is why the layout below looks different from every other rung.

## Run it

The Python client ships with tests that run fully offline (the HTTP layer is mocked), so you can verify the client logic with no Hub and no key:

```bash
cd python
pip install -e ".[dev]"
pytest -q        # 7 passing tests
```

To call a real pack, you need a deployed pack and an API key with the `commands:execute` scope. Every "for real" command below is gated behind that.

## What is inside

```
05-pack-from-outside/
  curl/run.sh            Door 1, raw: the request on the wire, with curl
  python/
    huitzo_client.py     Door 1, ergonomic: a tiny httpx client (sync/async, retries)
    mcp_client.py        Door 3: a hand-written MCP JSON-RPC client
    test_huitzo_client.py    offline tests (respx-mocked): envelope, async poll, 429, errors
    test_mcp_client.py       offline tests: tool-name mapping, initialize/list/call
  cli/USAGE.md           Door 2: huitzo run, --output json, exit-code branching
  mcp/connectors.md      Door 3: paste-in configs for Claude.ai, Cursor, VS Code
  ci/gate.yml            Door 4: a run-pack-action workflow to copy into your repo
```

## Door 1: REST

The rawest version is one `curl` (`curl/run.sh`): POST the args to
`/api/v1/commands/{namespace}/{name}` with a Bearer key, and read `data.result` back.

The ergonomic version is `python/huitzo_client.py`. Its whole job is the four steps, and the one subtlety worth seeing is the sync-versus-async branch:

```python
data = self._post_command(client, namespace, name, args or {})
if "task_id" in data:
    return self._poll_task(client, data["task_id"])  # long command: poll the task
return data["result"]                                 # fast command: result is right here
```

Fast commands answer inline. Long commands hand back a `task_id` you poll at
`/api/v1/tasks/{id}` until the status is terminal. The client also honors `Retry-After`
on a 429 and surfaces the `correlation_id` on an error, so a failure in your logs matches
a request in Huitzo's.

## Door 2: CLI

`cli/USAGE.md` shows the same call as `huitzo run @your-org/macro-snapshot/country-snapshot
--output json`, and how the CLI maps outcomes to exit codes (`0` success, `2` re-auth,
`4`/`5` transient, `10` command failed) so a shell script can branch without parsing.

## Door 3: hosted MCP

Huitzo runs an MCP server at `https://huitzo.ai/mcp` that exposes your commands as tools,
so Claude.ai or Cursor can call your pack. `mcp/connectors.md` has the paste-in configs;
`python/mcp_client.py` speaks the JSON-RPC by hand so you can see what a connector does.
The one Huitzo-specific detail is the lossless tool-name mapping:

```python
to_mcp_tool_name("@reef/macro-snapshot/country-snapshot")  # -> "reef__macro-snapshot__country-snapshot"
```

MCP auth is API-key only; JWTs are rejected by design, because a connector config lives
in a client UI for months and needs a long-lived, scoped, revocable credential.

## Door 4: CI gate

`ci/gate.yml` is a GitHub Action you copy into your own repo. It runs a pack on every
pull request with `huitzo-inc/run-pack-action@v1` and fails the build unless a JSONPath
condition holds. That is how you put a Huitzo decision in the path of a merge. (It is not
active in this repo; GitHub only runs workflows under the repo-root `.github/workflows/`.)

## Test the clients with no Hub

The two test files are the point of this rung as much as the clients are. They mock the
HTTP and transport layers (with `respx`), so they prove the client logic, the envelope
unwrap, the sync-versus-async branch, the 429 retry, the tool-name round-trip, without a
Hub or a key:

```python
@respx.mock
def test_async_command_polls_until_success():
    respx.post(CMD_URL).mock(return_value=httpx.Response(200, json={"data": {"task_id": "task_1", "status": "pending"}}))
    respx.get(f"{API}/api/v1/tasks/task_1").mock(side_effect=[
        httpx.Response(200, json={"success": True, "data": {"status": "started"}}),
        httpx.Response(200, json={"success": True, "data": {"status": "success", "result": _SNAPSHOT}}),
    ])
    assert _client().execute("reef", "country-snapshot", {"country": "USA"}) == _SNAPSHOT
```

## What is the same through every door

- **One scope.** Every door uses an API key with `commands:execute`. Nothing here can
  publish a pack, manage keys, or touch billing.
- **Tenant isolation.** RLS enforces that a key only ever sees and runs commands its
  tenant is allowed to, identically across REST, CLI, and MCP. A cross-tenant id returns
  404, not 403, so the API never even confirms another tenant's command exists.
- **Correlation ids.** Every response (and every error) carries a `correlation_id` that
  ties your logs to Huitzo's.

Four doors, one governed, audited, RLS-isolated execution behind all of them.

## Next

You have built packs, composed them, put a dashboard on one, and driven one from outside.
[Tier 6: fullstack-triage](../06-fullstack-triage) brings the pack and the dashboard into
a single project and tests them end to end on your laptop.
