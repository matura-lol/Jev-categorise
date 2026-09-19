"""Thin client for the TypeSafe System One API (and OpenCode Zen's mirror).

Jev is not a chat model: there is no ``/chat/completions``. One call posts a
*state* plus a map of *typed questions* and returns typed answers. The client
keeps one HTTP request per state, retries rate limits / transient failures with
backoff, and honours ``Retry-After``.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any

DEFAULT_URL = os.environ.get(
    "JEV_URL", "https://opencode.ai/zen/v1/systemone")
DEFAULT_MODEL = os.environ.get("JEV_MODEL", "jev-1.13")
DEFAULT_UA = "jev-categorise/1.0 (+https://matura.lol)"


class JevError(RuntimeError):
    """A non-retryable Jev API failure."""


class JevClient:
    """Synchronous client for ``POST /v1/systemone``.

    ``api_key`` falls back to ``JEV_API_KEY`` / ``TYPESAFE_API_KEY`` /
    ``OPENCODE_API_KEY``. ``url`` may point at TypeSafe directly
    (``https://api.typesafe.ai/v1/systemone``) or at OpenCode Zen.
    """

    def __init__(self, api_key: str | None = None, model: str | None = None,
                 url: str | None = None, timeout: float = 90.0,
                 retries: int = 8, user_agent: str = DEFAULT_UA) -> None:
        self.api_key = api_key or os.environ.get("JEV_API_KEY") or os.environ.get(
            "TYPESAFE_API_KEY") or os.environ.get("OPENCODE_API_KEY")
        if not self.api_key:
            raise JevError(
                "no API key: set JEV_API_KEY (or TYPESAFE_API_KEY / "
                "OPENCODE_API_KEY) or pass api_key=")
        self.model = model or DEFAULT_MODEL
        self.url = url or DEFAULT_URL
        self.timeout = timeout
        self.retries = retries
        self.user_agent = user_agent

    def system_one(self, state: Any, questions: dict[str, Any]) -> dict[str, Any]:
        """Evaluate every typed question against *state* in one call.

        *questions* maps a name to a :class:`~jev_categorise.primitives.Choice`,
        :class:`~jev_categorise.primitives.Score` or
        :class:`~jev_categorise.primitives.Noul` (or already-serialised dicts).
        """
        payload = {
            "state": state,
            "model": self.model,
            "questions": {
                name: q.to_wire() if hasattr(q, "to_wire") else q
                for name, q in questions.items()
            },
        }
        return self._post(payload)

    def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": self.user_agent,
        }
        last: Exception | None = None
        for attempt in range(self.retries):
            request = urllib.request.Request(self.url, data=body, headers=headers)
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as resp:
                    return json.loads(resp.read())
            except urllib.error.HTTPError as exc:
                last = exc
                if exc.code not in (429, 500, 502, 503, 504):
                    detail = exc.read().decode("utf-8", "replace")[:300]
                    raise JevError(f"HTTP {exc.code}: {detail}") from exc
                retry_after = exc.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2.0 ** attempt
            except (urllib.error.URLError, TimeoutError) as exc:
                last = exc
                delay = 2.0 ** attempt
            time.sleep(min(delay, 60.0))
        raise JevError(f"request failed after {self.retries} attempts: {last}")
