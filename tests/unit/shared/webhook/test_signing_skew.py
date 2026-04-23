# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from shared.webhook.signing import (
    SignatureVerificationError,
    build_signature_header,
    verify_signature,
)

pytestmark = pytest.mark.unit


def test_skew_rejects_old_timestamp() -> None:
    signed_at = datetime(2026, 4, 20, 12, 0, 0, tzinfo=UTC)
    now = signed_at + timedelta(seconds=400)
    header = build_signature_header(secret="a" * 64, timestamp=signed_at, body=b"x")
    with pytest.raises(SignatureVerificationError):
        verify_signature(header=header, secret="a" * 64, body=b"x", now=now, skew_seconds=300)


def test_skew_accepts_fresh_timestamp() -> None:
    signed_at = datetime(2026, 4, 20, 12, 0, 0, tzinfo=UTC)
    now = signed_at + timedelta(seconds=60)
    header = build_signature_header(secret="a" * 64, timestamp=signed_at, body=b"x")
    verify_signature(header=header, secret="a" * 64, body=b"x", now=now, skew_seconds=300)
