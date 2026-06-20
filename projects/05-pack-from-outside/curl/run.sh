#!/usr/bin/env bash
# Door 1, the rawest one: drive a deployed pack with nothing but curl.
# This is the same request every other door (the Python client, the CLI, MCP) makes
# underneath. Set your key and run it.
#
#   export HUITZO_API_KEY=sk-huitzo-...
#   ./run.sh USA inflation
set -euo pipefail

API_URL="${HUITZO_API_URL:-https://huitzo.ai}"
COUNTRY="${1:-USA}"
INDICATOR="${2:-inflation}"

if [[ -z "${HUITZO_API_KEY:-}" ]]; then
  echo "Set HUITZO_API_KEY first (a key with the commands:execute scope)." >&2
  exit 1
fi

# POST the command. The path is the full @scope/pack/command; the body carries the
# pack's args under an "args" key. The response is wrapped in a {"data": ...}
# envelope. For a fast command, data.result is the answer right here.
curl -sS -X POST "${API_URL}/api/v1/commands/@reef/macro-snapshot/country-snapshot" \
  -H "Authorization: Bearer ${HUITZO_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{\"args\": {\"country\": \"${COUNTRY}\", \"indicator\": \"${INDICATOR}\"}}"

# A slow command instead returns {"data": {"task_id": "...", "status": "pending"}}.
# In that case you poll until the status is terminal:
#
#   curl -sS "${API_URL}/api/v1/tasks/<task_id>" \
#     -H "Authorization: Bearer ${HUITZO_API_KEY}"
#
# That sync-or-async branch is the one thing every Huitzo client has to handle.
# huitzo_client.py does it for you; this script shows the bytes on the wire.
