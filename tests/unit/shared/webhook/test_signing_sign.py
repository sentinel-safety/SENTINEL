# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime

import pytest

from shared.webhook.signing import build_signature_header, sign_body

pytestmark = pytest.mark.unit


def test_sign_produces_64_hex_chars() -> None:
    ts = datetime(2026, 4, 20, tzinfo=UTC)
    sig = sign_body(secret="a" * 64, timestamp=ts, body=b"hello")
    assert len(sig) == 64
    assert all(c in "0123456789abcdef" for c in sig)


def test_header_format_includes_timestamp_and_v1_signature() -> None:
    ts = datetime(2026, 4, 20, tzinfo=UTC)
    header = build_signature_header(secret="a" * 64, timestamp=ts, body=b"hello")
    assert header.startswith("t=")
    assert ",v1=" in header
