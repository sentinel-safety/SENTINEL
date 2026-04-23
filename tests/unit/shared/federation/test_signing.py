# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from shared.federation.signals import FederationSignal
from shared.federation.signing import sign_signal, verify_signal

pytestmark = pytest.mark.unit

_FINGERPRINT = tuple(float(i) * 0.1 for i in range(16))
_NOW = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
_SECRET = b"super-secret-32-bytes-padding!!!"


def _make_signal(**overrides: object) -> FederationSignal:
    defaults: dict[str, object] = {
        "publisher_tenant_id": uuid4(),
        "actor_hash": b"\x00" * 32,
        "fingerprint": _FINGERPRINT,
        "signal_kinds": ("isolation",),
        "flagged_at": _NOW,
    }
    defaults.update(overrides)
    return FederationSignal(**defaults)


def test_sign_returns_32_bytes() -> None:
    signal = _make_signal()
    commit = sign_signal(secret=_SECRET, signal=signal)
    assert isinstance(commit, bytes)
    assert len(commit) == 32


def test_verify_round_trip() -> None:
    signal = _make_signal()
    commit = sign_signal(secret=_SECRET, signal=signal)
    assert verify_signal(secret=_SECRET, signal=signal, commit=commit)


def test_tampered_fingerprint_fails() -> None:
    signal = _make_signal()
    commit = sign_signal(secret=_SECRET, signal=signal)
    tampered = _make_signal(fingerprint=tuple(0.9 for _ in range(16)))
    assert not verify_signal(secret=_SECRET, signal=tampered, commit=commit)


def test_tampered_commit_fails() -> None:
    signal = _make_signal()
    commit = sign_signal(secret=_SECRET, signal=signal)
    bad_commit = bytes(b ^ 0xFF for b in commit)
    assert not verify_signal(secret=_SECRET, signal=signal, commit=bad_commit)


def test_wrong_secret_fails() -> None:
    signal = _make_signal()
    commit = sign_signal(secret=_SECRET, signal=signal)
    assert not verify_signal(
        secret=b"wrong-secret-32-bytes-padding!!!", signal=signal, commit=commit
    )
