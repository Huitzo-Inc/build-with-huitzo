# Door 2: the CLI

The same command, run from the Huitzo CLI. This is the fastest way for a person (or a
shell script) to drive a deployed pack.

## Authenticate

Two ways, pick one:

```bash
# Interactive, for a person at a terminal:
huitzo login

# Non-interactive, for a script or CI job (a key with the commands:execute scope):
export HUITZO_TOKEN=sk-huitzo-...
```

## Run a command

```bash
huitzo run @reef/macro-snapshot/country-snapshot \
  --args '{"country": "USA", "indicator": "inflation"}' \
  --output json
```

`--output json` prints a machine-readable envelope so a script can parse it:

```json
{ "ok": true, "data": { "country": "USA", "latest_value": 3.4, "summary": "..." } }
```

## Branch on the exit code

The CLI maps outcomes to exit codes, so a shell script can react without parsing:

| Exit code | Meaning | What a script should do |
|-----------|---------|-------------------------|
| `0` | success | use the result |
| `2` | auth failed | re-authenticate, then retry |
| `4` / `5` | transient (rate limit, service) | back off and retry |
| `10` | the command itself failed | do not retry; surface the error |

```bash
if huitzo run @reef/macro-snapshot/country-snapshot --args '{"country":"USA"}' --output json > out.json; then
  jq .data.summary out.json
else
  case $? in
    2) echo "re-auth needed" ;;
    4|5) echo "transient, retry later" ;;
    10) echo "command failed, see the error" ;;
  esac
fi
```

Same key, same command, same `{data: ...}` envelope as the REST door. The CLI is just a
friendlier shell over the API.
