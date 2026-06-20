# Door 3: connect your pack to Claude, Cursor, and other MCP clients

Huitzo runs a hosted Model Context Protocol (MCP) server at `https://huitzo.ai/mcp/`. It
exposes every command your tenant can see as an MCP tool. Point an MCP client at it and
an AI assistant can call your pack directly, with your governance and audit intact.

`mcp_client.py` in this folder speaks the same JSON-RPC by hand so you can see what the
connector does. To use it from a real client, you just paste a config.

> Use the trailing slash: `…/mcp/`, not `…/mcp`. The no-slash URL 307-redirects to
> `/mcp/`, and that redirect can downgrade `https` → `http`. Pointing connectors at the
> slash form directly avoids it.

## Auth: API key only

The MCP endpoint accepts only an API key (`sk-huitzo-...`) with the `commands:execute`
scope. JWTs and cookies are rejected by design, because a connector config sits in a
client UI for months and needs a long-lived, scoped, revocable credential. Mint one from
your Hub account settings, or:

```bash
curl -X POST https://huitzo.ai/api/v1/account/api-keys \
  -H "Authorization: Bearer <your-jwt>" \
  -H "Content-Type: application/json" \
  -d '{"name": "claude-connector", "scopes": ["commands:execute"]}'
```

The plaintext key is returned exactly once. Store it now.

## Claude.ai / Claude Desktop

Add a custom connector of type Streamable HTTP:

```json
{
  "mcpServers": {
    "huitzo": {
      "type": "streamable-http",
      "url": "https://huitzo.ai/mcp/",
      "headers": { "Authorization": "Bearer sk-huitzo-..." }
    }
  }
}
```

## Cursor / VS Code

```json
{
  "mcp": {
    "servers": {
      "huitzo": {
        "type": "streamable-http",
        "url": "https://huitzo.ai/mcp/",
        "headers": { "Authorization": "Bearer sk-huitzo-..." }
      }
    }
  }
}
```

## What the assistant sees

Your command `@reef/macro-snapshot/country-snapshot` shows up as the tool
`reef__macro-snapshot__country-snapshot`. The mapping is lossless: split on `__` and
prepend `@`. Tenant isolation is enforced exactly as on the REST endpoint, so the client
can only ever see and call commands your key's tenant is allowed to.
