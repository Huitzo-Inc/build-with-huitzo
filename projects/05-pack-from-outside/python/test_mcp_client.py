"""Offline tests for the MCP client. The tool-name mapping is pure and tested
directly; the JSON-RPC calls are tested with respx, so no Hub is needed."""

from __future__ import annotations

import json

import httpx
import respx

from mcp_client import McpClient, to_command_id, to_mcp_tool_name

API = "https://huitzo.ai"
# The client posts to the canonical /mcp/ (trailing slash) to dodge the scheme-
# downgrading redirect that /mcp issues.
MCP_URL = f"{API}/mcp/"


def _sse(message: dict) -> httpx.Response:
    """Frame a JSON-RPC message the way Streamable HTTP does: as a single SSE event."""
    body = f"event: message\ndata: {json.dumps(message)}\n\n"
    return httpx.Response(200, text=body, headers={"content-type": "text/event-stream"})


def test_tool_name_mapping_round_trips():
    command_id = "@reef/macro-snapshot/country-snapshot"
    tool = to_mcp_tool_name(command_id)
    assert tool == "reef__macro-snapshot__country-snapshot"
    assert to_command_id(tool) == command_id


@respx.mock
def test_list_tools_initializes_then_lists():
    respx.post(MCP_URL).mock(
        side_effect=[
            httpx.Response(200, json={"jsonrpc": "2.0", "id": 1, "result": {"capabilities": {"tools": {}}}}),
            httpx.Response(
                200,
                json={
                    "jsonrpc": "2.0",
                    "id": 2,
                    "result": {"tools": [{"name": "reef__macro-snapshot__country-snapshot"}]},
                },
            ),
        ]
    )

    tools = McpClient(API, "sk-huitzo-test").list_tools()

    assert tools[0]["name"] == "reef__macro-snapshot__country-snapshot"


@respx.mock
def test_call_parses_the_text_result_block_over_sse():
    inner = {"result": {"country": "USA", "latest_value": 3.4}, "correlation_id": "req_1"}
    route = respx.post(MCP_URL).mock(
        return_value=_sse(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "result": {"content": [{"type": "text", "text": json.dumps(inner)}]},
            }
        )
    )

    result = McpClient(API, "sk-huitzo-test").call(
        "@reef/macro-snapshot/country-snapshot", {"country": "USA"}
    )

    assert result == inner
    # The pack args ride under tools/call params.arguments, by the MCP tool name.
    sent = json.loads(route.calls.last.request.content)
    assert sent["params"]["name"] == "reef__macro-snapshot__country-snapshot"
    assert sent["params"]["arguments"] == {"country": "USA"}
