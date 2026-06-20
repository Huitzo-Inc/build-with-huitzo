"""
Module: mcp_client
Description: A minimal client for Huitzo's hosted Model Context Protocol (MCP) server.
            This is the door that lets Claude.ai, Cursor, and any MCP client call your
            pack's commands as tools. Here we speak the same JSON-RPC by hand so you can
            see exactly what the connector does under the hood.

            Two things make this door specific:
              - Auth is API-key only (sk-huitzo-...). JWTs are rejected by design,
                because a connector config sits in a client UI for months.
              - Huitzo command ids map losslessly to MCP-legal tool names:
                    @scope/pack/command  <->  scope__pack__command
"""

from __future__ import annotations

import json
from typing import Any

import httpx


def to_mcp_tool_name(command_id: str) -> str:
    """`@scope/pack/command` -> `scope__pack__command` (MCP tool names cannot use / or @)."""
    return command_id.lstrip("@").replace("/", "__")


def to_command_id(tool_name: str) -> str:
    """`scope__pack__command` -> `@scope/pack/command`. The inverse of to_mcp_tool_name."""
    return "@" + tool_name.replace("__", "/")


class McpClient:
    """Talk to https://huitzo.ai/mcp over JSON-RPC. API key must carry commands:execute."""

    # Streamable HTTP MCP. The protocol version the client speaks during the handshake.
    PROTOCOL_VERSION = "2025-03-26"

    def __init__(self, api_url: str, api_key: str):
        # The path is /mcp/ (with the trailing slash). Hitting /mcp redirects to
        # /mcp/, and that redirect can downgrade the scheme to http; using the
        # canonical path avoids it. Still short enough to paste into a connector.
        self.endpoint = f"{api_url.rstrip('/')}/mcp/"
        self.api_key = api_key
        self._id = 0

    @property
    def _headers(self) -> dict[str, str]:
        # Streamable HTTP replies as Server-Sent Events, so the client MUST accept
        # both application/json and text/event-stream or the server returns 406.
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }

    @staticmethod
    def _parse_response(response: httpx.Response) -> dict[str, Any]:
        """Read one JSON-RPC message from a Streamable HTTP reply.

        The transport frames the response as SSE (``event: message`` /
        ``data: {json}``); a plain-JSON reply is also accepted as a fallback. The
        last ``data:`` payload is the response to our request.
        """
        text = response.text
        payloads: list[str] = []
        for block in text.split("\n\n"):
            data = "\n".join(
                line[len("data:") :].lstrip()
                for line in block.splitlines()
                if line.startswith("data:")
            )
            if data:
                payloads.append(data)
        return json.loads(payloads[-1] if payloads else text)

    def _rpc(self, client: httpx.Client, method: str, params: dict[str, Any] | None = None) -> Any:
        self._id += 1
        payload = {"jsonrpc": "2.0", "id": self._id, "method": method}
        if params is not None:
            payload["params"] = params
        response = client.post(self.endpoint, json=payload, headers=self._headers)
        response.raise_for_status()
        body = self._parse_response(response)
        if body.get("error"):
            raise RuntimeError(f"MCP error: {body['error']}")
        return body.get("result")

    def list_tools(self) -> list[dict[str, Any]]:
        """initialize + tools/list: discover every command visible to this key's tenant."""
        with httpx.Client(timeout=60.0) as client:
            self._rpc(
                client,
                "initialize",
                {
                    "protocolVersion": self.PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "huitzo-tier5-client", "version": "1.0"},
                },
            )
            result = self._rpc(client, "tools/list")
            return result.get("tools", [])

    def call(self, command_id: str, arguments: dict[str, Any] | None = None) -> Any:
        """tools/call against one command. Returns the parsed JSON result block."""
        with httpx.Client(timeout=60.0) as client:
            result = self._rpc(
                client,
                "tools/call",
                {"name": to_mcp_tool_name(command_id), "arguments": arguments or {}},
            )
            # tools/call returns a single text content block whose body is JSON.
            text = result["content"][0]["text"]
            return json.loads(text)
