from __future__ import annotations

import hashlib
import hmac
from datetime import UTC, datetime


class WebhookSignatureError(Exception):
    pass


def verify_webhook_signature(
    *,
    header: str,
    secret: str,
    body: bytes,
    now: datetime,
    skew_seconds: int = 300,
) -> None:
    parts = dict(p.split("=", 1) for p in header.split(",") if "=" in p)
    if "t" not in parts or "v1" not in parts:
        raise WebhookSignatureError("malformed signature header")
    try:
        ts = datetime.fromtimestamp(int(parts["t"]), tz=UTC)
    except (ValueError, OverflowError) as exc:
        raise WebhookSignatureError("invalid timestamp") from exc
    if abs((now - ts).total_seconds()) > skew_seconds:
        raise WebhookSignatureError("timestamp outside allowed skew")
    message = f"{int(ts.timestamp())}.".encode() + body
    expected = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, parts["v1"]):
        raise WebhookSignatureError("signature mismatch")
