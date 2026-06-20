"""Offline tests for the REST client. respx mocks the HTTP layer, so these prove the
client logic (envelope unwrap, sync-vs-async branch, retry on 429, error handling)
with no Hub and no network."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from huitzo_client import HuitzoClient, HuitzoError

API = "https://huitzo.ai"
# The full command path is @scope/pack/command; the client joins namespace + name.
NAMESPACE = "@reef/macro-snapshot"
NAME = "country-snapshot"
CMD_URL = f"{API}/api/v1/commands/{NAMESPACE}/{NAME}"

_SNAPSHOT = {"country": "USA", "indicator": "inflation", "latest_value": 3.4, "summary": "Eased."}


def _client() -> HuitzoClient:
    # No real waiting: the retry and poll loops use this no-op sleep.
    return HuitzoClient(API, "sk-huitzo-test", poll_interval=0, sleep=lambda _s: None)


@respx.mock
def test_sync_command_returns_the_result():
    route = respx.post(CMD_URL).mock(
        return_value=httpx.Response(
            200, json={"data": {"result": _SNAPSHOT, "execution": {"duration_ms": 7, "status": "completed"}}}
        )
    )

    result = _client().execute(NAMESPACE, NAME, {"country": "USA"})

    assert result == _SNAPSHOT
    # The pack args ride under an "args" key — posting them bare drops them server-side.
    sent = json.loads(route.calls.last.request.content)
    assert sent == {"args": {"country": "USA"}}


@respx.mock
def test_async_command_polls_until_success():
    respx.post(CMD_URL).mock(
        return_value=httpx.Response(200, json={"data": {"task_id": "task_1", "status": "pending"}})
    )
    respx.get(f"{API}/api/v1/tasks/task_1").mock(
        side_effect=[
            httpx.Response(200, json={"success": True, "data": {"status": "started"}}),
            httpx.Response(200, json={"success": True, "data": {"status": "success", "result": _SNAPSHOT}}),
        ]
    )

    result = _client().execute(NAMESPACE, NAME, {"country": "USA"})

    assert result == _SNAPSHOT


@respx.mock
def test_rate_limit_is_retried_then_succeeds():
    respx.post(CMD_URL).mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "0"}, json={"success": False, "error": {"message": "slow down"}}),
            httpx.Response(200, json={"data": {"result": _SNAPSHOT, "execution": {"status": "completed"}}}),
        ]
    )

    result = _client().execute(NAMESPACE, NAME, {"country": "USA"})

    assert result == _SNAPSHOT


@respx.mock
def test_error_envelope_raises_with_correlation_id():
    respx.post(CMD_URL).mock(
        return_value=httpx.Response(
            400,
            json={
                "success": False,
                "error": {"message": "bad country", "code": "VALIDATION_FAILED", "correlation_id": "req_abc"},
            },
        )
    )

    with pytest.raises(HuitzoError) as exc:
        _client().execute(NAMESPACE, NAME, {"country": "??"})

    assert exc.value.code == "VALIDATION_FAILED"
    assert exc.value.correlation_id == "req_abc"
