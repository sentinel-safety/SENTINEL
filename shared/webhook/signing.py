# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import hmac
from datetime import UTC, datetime
from hashlib import sha256


class SignatureVerificationError(Exception):
    pass


def sign_body(*, secret: str, timestamp: datetime, body: bytes) -> str:
    message = f"{int(timestamp.timestamp())}.".encode() + body
    return hmac.new(secret.encode(), message, sha256).hexdigest()


def build_signature_header(*, secret: str, timestamp: datetime, body: bytes) -> str:
    sig = sign_body(secret=secret, timestamp=timestamp, body=body)
    return f"t={int(timestamp.timestamp())},v1={sig}"


def verify_signature(
    *,
    header: str,
    secret: str,
    body: bytes,
    now: datetime,
    skew_seconds: int,
) -> None:
    parts = dict(p.split("=", 1) for p in header.split(",") if "=" in p)
    if "t" not in parts or "v1" not in parts:
        raise SignatureVerificationError("malformed signature header")
    try:
        ts = datetime.fromtimestamp(int(parts["t"]), tz=UTC)
    except (ValueError, OverflowError) as exc:
        raise SignatureVerificationError("invalid timestamp") from exc
    age = abs((now - ts).total_seconds())
    if age > skew_seconds:
        raise SignatureVerificationError("timestamp outside allowed skew")
    expected = sign_body(secret=secret, timestamp=ts, body=body)
    if not hmac.compare_digest(expected, parts["v1"]):
        raise SignatureVerificationError("signature mismatch")
