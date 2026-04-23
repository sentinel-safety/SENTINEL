from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import httpx

from sentinel._version import __version__
from sentinel.errors import AuthError, RateLimitError, SentinelError, ServerError
from sentinel.errors import TimeoutError as SentinelTimeoutError
from sentinel.events import EventsAPI

logger = logging.getLogger("sentinel")

DEFAULT_TIMEOUT = 10.0
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_BASE = 0.5
DEFAULT_RETRY_CAP = 30.0


class SentinelClient:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        timeout: float = DEFAULT_TIMEOUT,
        retry_attempts: int = DEFAULT_RETRY_ATTEMPTS,
        retry_base_seconds: float = DEFAULT_RETRY_BASE,
        retry_cap_seconds: float = DEFAULT_RETRY_CAP,
        http_client: httpx.Client | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")
        if not base_url:
            raise ValueError("base_url is required")
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout
        self._retry_attempts = retry_attempts
        self._retry_base_seconds = retry_base_seconds
        self._retry_cap_seconds = retry_cap_seconds
        self._owns_http = http_client is None
        self._http = http_client or httpx.Client(timeout=timeout)
        self.events = EventsAPI(client=self)

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def retry_attempts(self) -> int:
        return self._retry_attempts

    @property
    def retry_base_seconds(self) -> float:
        return self._retry_base_seconds

    @property
    def retry_cap_seconds(self) -> float:
        return self._retry_cap_seconds

    def _default_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "User-Agent": f"sentinel-python/{__version__}",
            "Content-Type": "application/json",
        }

    def request_json(
        self,
        *,
        method: str,
        path: str,
        json_body: Mapping[str, Any],
        extra_headers: Mapping[str, str] | None = None,
    ) -> httpx.Response:
        url = f"{self._base_url}{path}"
        headers = self._default_headers()
        if extra_headers:
            headers.update(dict(extra_headers))
        try:
            response = self._http.request(method, url, json=dict(json_body), headers=headers)
        except httpx.TimeoutException as exc:
            raise SentinelTimeoutError(str(exc)) from exc
        except httpx.TransportError as exc:
            raise SentinelError(str(exc)) from exc
        self._raise_for_status(response)
        return response

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.status_code in (401, 403):
            raise AuthError(f"{response.status_code} authentication failure")
        if response.status_code == 429:
            raise RateLimitError("429 rate limited", retry_after_seconds=None)
        if 500 <= response.status_code < 600:
            raise ServerError(
                f"{response.status_code} server error",
                status_code=response.status_code,
            )

    def close(self) -> None:
        if self._owns_http:
            self._http.close()

    def __enter__(self) -> SentinelClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
