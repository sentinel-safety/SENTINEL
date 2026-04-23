# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime

import pytest

from shared.webhook.signing import (
    SignatureVerificationError,
    build_signature_header,
    verify_signature,
)

pytestmark = pytest.mark.unit


def test_verify_accepts_valid_signature() -> None:
    now = datetime.now(UTC)
    secret = "a" * 64
    body = b"{'hello':'world'}"
    header = build_signature_header(secret=secret, timestamp=now, body=body)
    verify_signature(header=header, secret=secret, body=body, now=now, skew_seconds=300)


def test_verify_rejects_tampered_body() -> None:
    now = datetime.now(UTC)
    secret = "a" * 64
    body = b"{'hello':'world'}"
    header = build_signature_header(secret=secret, timestamp=now, body=body)
    with pytest.raises(SignatureVerificationError):
        verify_signature(
            header=header, secret=secret, body=b"{'hello':'evil'}", now=now, skew_seconds=300
        )


def test_verify_rejects_wrong_secret() -> None:
    now = datetime.now(UTC)
    body = b"payload"
    header = build_signature_header(secret="a" * 64, timestamp=now, body=body)
    with pytest.raises(SignatureVerificationError):
        verify_signature(header=header, secret="b" * 64, body=body, now=now, skew_seconds=300)


def test_verify_rejects_malformed_header() -> None:
    now = datetime.now(UTC)
    with pytest.raises(SignatureVerificationError):
        verify_signature(header="garbage", secret="a" * 64, body=b"x", now=now, skew_seconds=300)
