# Tier 1: macro-snapshot

> Read this in [Español](./README.es.md).

A pack that reaches a real API. A fictional research desk, **Marlin Research**, wants a grounded read on one country's economy: pull one macro indicator from the World Bank, then get a plain-language summary back. The catch, and the whole point: **the model never produces a number.** Python fetches the data, picks the latest observation, and computes the change. The model is handed those figures and asked only to write the sentence. This is what "grounded AI" means in practice. The numbers are facts; the model narrates them.

**You will learn:** calling an external API through `ctx.http` (host configured by the deployment, not hard-coded), defensive parsing of a real-world response shape, the deterministic-first split done in earnest, and how to keep a model from inventing figures by giving it only the figures it is allowed to use.

**Time:** about ten minutes.

## Prerequisites

- Python 3.11+
- The [Huitzo CLI](https://github.com/Huitzo-Inc/huitzo-launcher) (optional for this rung, used to run against a real Hub)

## Run it

```bash
cd pack
pip install -e ".[dev]"
pytest                  # offline tests for this pack (what CI runs)
```

You should see eight passing tests. They run with no network and no model: the test hands the command a fake context whose HTTP and model calls are both mocked, so your parsing and math are verified without a live API or a spent token.

## What is inside

```
pack/
  huitzo.yaml                          the manifest: identity, permissions, the Policy Card
  pyproject.toml                       dependencies and the command entry point
  src/macro_snapshot/
    commands/country_snapshot.py       the command itself
    models/args.py                     typed input (closed country + indicator sets)
    models/output.py                   typed output (Python's numbers + the model's sentence)
  tests/test_country_snapshot.py       offline tests
```

## The command, the shape that matters

```python
@command("country-snapshot", namespace="reef", timeout=30)
async def country_snapshot(args: SnapshotArgs, ctx: Context) -> CountrySnapshot:
    code = _INDICATOR_CODES[args.indicator]            # friendly name -> WB code, in Python

    raw = await ctx.http.get(                           # host is the integration, path is relative
        f"/v2/country/{args.country}/indicator/{code}",
        params={"format": "json", "mrv": 5},
    )
    data = json.loads(raw) if isinstance(raw, str) else raw   # dict or JSON string, both handled

    # Deterministic first: Python picks the latest non-null point and the delta.
    latest_value, latest_year, delta_pct = _latest_and_delta(data[1])

    # AI augmentation: hand the model only the parsed figures, ask for a sentence.
    narration = await ctx.llm.complete(
        prompt=f"{_PROMPT}\n\n<figures>\n{facts}\n</figures>",
        profile="default",
        schema=MacroSummary,
    )

    return CountrySnapshot(latest_value=latest_value, ..., summary=narration.summary)
```

Four things to notice:

1. **The numbers come from Python, the sentence comes from the model.** `latest_value`, `latest_year`, and `delta_pct` are computed from the World Bank response. The model receives those figures and writes the summary. It is never asked to do arithmetic or recall a statistic, so it cannot get one wrong.
2. **The model only sees the figures it is allowed to repeat.** The prompt contains exactly the parsed numbers, with an instruction to use only those and invent nothing. That is the difference between a model that narrates your data and a model that makes things up.
3. **The host is the integration, not the code.** `ctx.http.get` takes a relative path. The base URL (`api.worldbank.org`) is configured at deploy time and allow-listed in the manifest. Swap that integration for an internal API and the command does not change a line.
4. **The response is parsed defensively.** The World Bank returns a two-element list, `[metadata, observations]`, and the value can be a JSON string or already-parsed. The command handles both and raises a clear `ExternalAPIError` on an unexpected shape, rather than throwing an opaque `KeyError` deep in your logic.

## The "swap any internal API" moment

Open `pack/huitzo.yaml` and find the `services.http` block:

```yaml
services:
  http:
    required: true
    allowed_domains:
      - "api.worldbank.org"
    timeout: 15
```

The pack declares which host it is allowed to reach. The base URL itself is resolved by the deployment's HTTP integration. Today it is the World Bank. Tomorrow it is your data warehouse, your pricing service, or your claims database, with the same command code and the same deterministic-first split. The pattern is the product: Python owns the math, the model owns the sentence, and the data source is a deployment detail.

Note the cross-check the manifest enforces: every domain in `services.http.allowed_domains` must also appear in `policy.data_scope.external_domains`. A pack can only reach what its Policy Card allows.

## Run it for real

Two one-time setup steps, then you can run this pack against a Hub.

### 1. Re-scope it to your own org

The example is scoped to `@reef`, which you do not own. In `pack/huitzo.yaml`, change `namespace:` to an org you own, then sync and publish:

```bash
huitzo login
# pack/huitzo.yaml -> pack.namespace: your-org   (was: reef)
huitzo pack sync
huitzo pack publish
```

See [Run on your own Hub](../../README.md#run-on-your-own-hub) for the full explanation.

### 2. Add the World Bank integration in Hub

This pack reaches `api.worldbank.org` through an HTTP **integration**, not a hardcoded URL. The command calls `ctx.http.get("/v2/country/...")` with a relative path, and the deployment supplies the base URL. So add that integration once in the Hub before the first real run:

1. Open the Hub and click **Integrations** in the left sidebar (the `/integrations` page).

   <!-- screenshot: the Integrations page with the "+ Add integration" button -->

2. Click **+ Add integration**. In the form, set:
   - **Type**: `HTTP`
   - **Name**: `worldbank` (any tenant-unique slug; lowercase letters, digits, dashes)
   - **Base URL**: `https://api.worldbank.org`
   - **Timeout (s)**: `30` (the default is fine)
   - **Allowed domains (CSV)**: leave blank (the base URL host is allowed automatically)
   - **Bearer token** / **Basic auth**: leave blank (the World Bank API needs no auth)

   <!-- screenshot: the New integration form filled in for the World Bank API -->

3. Click **Create integration**. Hub runs a health probe against the base URL; once it shows healthy, the integration is ready.

   <!-- screenshot: the created worldbank integration showing a healthy status -->

The integration name does not need to match anything in the pack. At run time the deployment wires your HTTP integration to this pack's `ctx.http`, so `ctx.http.get("/v2/country/USA/indicator/...")` resolves to `https://api.worldbank.org/v2/country/USA/indicator/...`. (Prefer the API? `POST /api/v1/integrations` with `{"type":"http","name":"worldbank","config":{"base_url":"https://api.worldbank.org"}}`.)

### 3. Run it

```bash
huitzo run @your-org/macro-snapshot/country-snapshot --args '{"country": "USA", "indicator": "gdp"}'
```

## Next

[Tier 1: `01c-inbox-triage`](../01c-inbox-triage) is the next rung: deterministic rules own how urgent an email is, the model only drafts a reply, and the pack never sends it. Same pattern, more surface: deterministic logic first, the model only for the judgement call, every external reach declared in the Policy Card.

> Building a dashboard? This is the pack [Tier 4: `04-first-dashboard`](../04-first-dashboard) puts a UI on. You can jump there now — it needs nothing from Tiers 2 or 3.
