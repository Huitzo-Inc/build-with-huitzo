"""
Module: huitzo_client
Description: A tiny, dependency-light client for driving a DEPLOYED Huitzo pack from
            outside, over the REST API. No huitzo-sdk, just httpx, so it drops into
            any Python service, script, or CI job.

            The whole mental model is in one method, `execute`:

              1. Authenticate with an API key (sk-huitzo-...).
              2. POST the command. The response is one of two shapes:
                 - sync:  {"data": {"result": ..., "execution": ...}}
                 - async: {"data": {"task_id": ..., "status": "pending"}}
              3. For the async shape, poll GET /tasks/{id} until a terminal status.
              4. Unwrap the {"data": ...} envelope and return the result.

            Every door into Huitzo (REST, CLI, MCP, CI) is a variation on this.
"""

from __future__ import annotations

import time
from typing import Any, Callable

import httpx

_TERMINAL_STATES = {"success", "failure", "timeout", "revoked"}


class HuitzoError(Exception):
    """An error returned by the Huitzo API. Carries the correlation id so a failure
    in your logs can be matched to a request in Huitzo's logs."""

    def __init__(self, message: str, *, code: str | None = None, correlation_id: str | None = None):
        super().__init__(message)
        self.code = code
        self.correlation_id = correlation_id


class HuitzoClient:
    """Execute commands on a deployed pack. One scope is needed on the key:
    `commands:execute`."""

    def __init__(
        self,
        api_url: str,
        api_key: str,
        *,
        max_retries: int = 3,
        poll_interval: float = 1.0,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.max_retries = max_retries
        self.poll_interval = poll_interval
        # `sleep` is injectable so tests can run the retry/poll loops without waiting.
        self._sleep = sleep

    @property
    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def execute(self, namespace: str, name: str, args: dict[str, Any] | None = None) -> Any:
        """Run a command and return its result, transparently handling sync vs async."""
        with httpx.Client(timeout=60.0) as client:
            data = self._post_command(client, namespace, name, args or {})

            # The async branch: a long-running command returns a task to poll.
            if "task_id" in data:
                return self._poll_task(client, data["task_id"])

            # The sync branch: the result is right here, inside the envelope.
            return data["result"]

    def _post_command(
        self, client: httpx.Client, namespace: str, name: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        url = f"{self.api_url}/api/v1/commands/{namespace}/{name}"
        # The command endpoint takes the pack's arguments under an `args` key:
        # `{"args": {...}}`. Posting the bare arg dict drops them (the server reads
        # an empty `args` and the pack fails validation on its required fields).
        payload = {"args": args}
        for attempt in range(self.max_retries + 1):
            response = client.post(url, json=payload, headers=self._headers)

            # Rate limited: honor Retry-After and try again, up to max_retries.
            if response.status_code == 429 and attempt < self.max_retries:
                retry_after = float(response.headers.get("Retry-After", self.poll_interval))
                self._sleep(retry_after)
                continue

            return self._unwrap(response)

        raise HuitzoError("rate limited: exhausted retries", code="RATE_LIMITED")

    def _poll_task(self, client: httpx.Client, task_id: str) -> Any:
        url = f"{self.api_url}/api/v1/tasks/{task_id}"
        while True:
            data = self._unwrap(client.get(url, headers=self._headers))
            status = data.get("status")
            if status in _TERMINAL_STATES:
                if status == "success":
                    return data.get("result")
                error = data.get("error") or {}
                raise HuitzoError(
                    error.get("message", f"task {task_id} ended with status {status}"),
                    code=status,
                    correlation_id=data.get("correlation_id"),
                )
            self._sleep(self.poll_interval)

    @staticmethod
    def _unwrap(response: httpx.Response) -> dict[str, Any]:
        """Unwrap the {"data": ...} success envelope, or raise from the error envelope."""
        body = response.json()
        if response.status_code >= 400 or body.get("success") is False:
            error = body.get("error", {})
            raise HuitzoError(
                error.get("message", f"request failed with status {response.status_code}"),
                code=error.get("code"),
                correlation_id=error.get("correlation_id"),
            )
        return body["data"]
