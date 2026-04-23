from __future__ import annotations

from datetime import UTC, datetime

import pytest

from sentinel._retry import compute_backoff, parse_retry_after


def test_backoff_doubles_and_caps() -> None:
    assert compute_backoff(attempt=1, base=0.5, cap=8.0) == 0.5
    assert compute_backoff(attempt=2, base=0.5, cap=8.0) == 1.0
    assert compute_backoff(attempt=3, base=0.5, cap=8.0) == 2.0
    assert compute_backoff(attempt=4, base=0.5, cap=8.0) == 4.0
    assert compute_backoff(attempt=10, base=0.5, cap=8.0) == 8.0


def test_backoff_rejects_non_positive_attempt() -> None:
    with pytest.raises(ValueError):
        compute_backoff(attempt=0, base=1.0, cap=4.0)


def test_parse_retry_after_numeric() -> None:
    now = datetime(2026, 4, 20, 12, 0, 0, tzinfo=UTC)
    assert parse_retry_after("5", now=now) == 5.0


def test_parse_retry_after_http_date() -> None:
    now = datetime(2026, 4, 20, 12, 0, 0, tzinfo=UTC)
    result = parse_retry_after("Mon, 20 Apr 2026 12:00:30 GMT", now=now)
    assert result is not None
    assert abs(result - 30.0) < 1.0


def test_parse_retry_after_invalid_returns_none() -> None:
    now = datetime(2026, 4, 20, 12, 0, 0, tzinfo=UTC)
    assert parse_retry_after("banana", now=now) is None


def test_parse_retry_after_none_returns_none() -> None:
    now = datetime(2026, 4, 20, 12, 0, 0, tzinfo=UTC)
    assert parse_retry_after(None, now=now) is None


def test_parse_retry_after_negative_clamped_to_zero() -> None:
    now = datetime(2026, 4, 20, 12, 0, 0, tzinfo=UTC)
    assert parse_retry_after("-5", now=now) == 0.0
