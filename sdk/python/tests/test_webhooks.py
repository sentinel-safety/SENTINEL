from __future__ import annotations

import hashlib
import hmac
from datetime import UTC, datetime, timedelta

import pytest

from sentinel import verify_webhook_signature
from sentinel.webhooks import WebhookSignatureError


def _sign(secret: str, timestamp: datetime, body: bytes) -> str:
    msg = f"{int(timestamp.timestamp())}.".encode() + body
    digest = hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()
    return f"t={int(timestamp.timestamp())},v1={digest}"


def test_valid_signature_does_not_raise() -> None:
    secret = "whsec_test"  # pragma: allowlist secret
    ts = datetime(2026, 4, 20, 12, 0, 0, tzinfo=UTC)
    body = b'{"hello":"world"}'
    header = _sign(secret, ts, body)
    verify_webhook_signature(header=header, secret=secret, body=body, now=ts, skew_seconds=300)


def test_malformed_header_raises() -> None:
    with pytest.raises(WebhookSignatureError):
        verify_webhook_signature(
            header="not-a-signature",
            secret="s",
            body=b"{}",
            now=datetime(2026, 4, 20, 12, 0, 0, tzinfo=UTC),
            skew_seconds=300,
        )


def test_tampered_body_raises() -> None:
    secret = "whsec_test"  # pragma: allowlist secret
    ts = datetime(2026, 4, 20, 12, 0, 0, tzinfo=UTC)
    header = _sign(secret, ts, b'{"hello":"world"}')
    with pytest.raises(WebhookSignatureError):
        verify_webhook_signature(
            header=header,
            secret=secret,
            body=b'{"hello":"evil"}',
            now=ts,
            skew_seconds=300,
        )


def test_stale_timestamp_raises() -> None:
    secret = "whsec_test"  # pragma: allowlist secret
    ts = datetime(2026, 4, 20, 12, 0, 0, tzinfo=UTC)
    body = b'{"a":1}'
    header = _sign(secret, ts, body)
    with pytest.raises(WebhookSignatureError):
        verify_webhook_signature(
            header=header,
            secret=secret,
            body=body,
            now=ts + timedelta(seconds=1000),
            skew_seconds=300,
        )


def test_future_timestamp_raises() -> None:
    secret = "whsec_test"  # pragma: allowlist secret
    ts = datetime(2026, 4, 20, 12, 0, 0, tzinfo=UTC)
    body = b'{"a":1}'
    header = _sign(secret, ts, body)
    with pytest.raises(WebhookSignatureError):
        verify_webhook_signature(
            header=header,
            secret=secret,
            body=body,
            now=ts - timedelta(seconds=1000),
            skew_seconds=300,
        )


def test_wrong_secret_raises() -> None:
    ts = datetime(2026, 4, 20, 12, 0, 0, tzinfo=UTC)
    body = b'{"a":1}'
    header = _sign("right", ts, body)
    with pytest.raises(WebhookSignatureError):
        verify_webhook_signature(
            header=header,
            secret="wrong",  # pragma: allowlist secret
            body=body,
            now=ts,
            skew_seconds=300,
        )
