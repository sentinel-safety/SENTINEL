from __future__ import annotations

import pytest

from sentinel.errors import (
    AuthError,
    RateLimitError,
    SentinelError,
    ServerError,
)
from sentinel.errors import (
    TimeoutError as SentinelTimeoutError,
)


def test_all_errors_inherit_from_sentinel_error() -> None:
    for cls in (AuthError, RateLimitError, SentinelTimeoutError, ServerError):
        assert issubclass(cls, SentinelError)


def test_auth_error_is_raised_with_message() -> None:
    with pytest.raises(AuthError) as info:
        raise AuthError("invalid api key")
    assert "invalid api key" in str(info.value)


def test_rate_limit_error_carries_retry_after() -> None:
    err = RateLimitError("slow down", retry_after_seconds=42.0)
    assert err.retry_after_seconds == 42.0


def test_server_error_carries_status_code() -> None:
    err = ServerError("boom", status_code=503)
    assert err.status_code == 503
