# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from shared.federation.signals import FederationSignal, FederationSignalEnvelope, canonical_bytes

pytestmark = pytest.mark.unit

_FINGERPRINT = tuple(float(i) * 0.1 for i in range(16))
_NOW = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)


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


def test_signal_round_trip_via_json() -> None:
    signal = _make_signal()
    data = signal.model_dump(mode="json")
    restored = FederationSignal.model_validate(data)
    assert restored == signal


def test_canonical_bytes_is_stable() -> None:
    signal = _make_signal()
    assert canonical_bytes(signal) == canonical_bytes(signal)


def test_canonical_bytes_differs_on_changed_fingerprint() -> None:
    s1 = _make_signal()
    s2 = _make_signal(fingerprint=tuple(float(i) * 0.2 for i in range(16)))
    assert canonical_bytes(s1) != canonical_bytes(s2)


def test_fingerprint_must_be_16_dims() -> None:
    with pytest.raises(ValidationError):
        _make_signal(fingerprint=tuple(0.1 for _ in range(15)))
    with pytest.raises(ValidationError):
        _make_signal(fingerprint=tuple(0.1 for _ in range(17)))


def test_schema_version_must_be_1() -> None:
    with pytest.raises(ValidationError):
        FederationSignal(
            publisher_tenant_id=uuid4(),
            actor_hash=b"\x00" * 32,
            fingerprint=_FINGERPRINT,
            signal_kinds=("isolation",),
            flagged_at=_NOW,
            schema_version=2,
        )


def test_signal_kinds_must_be_non_empty() -> None:
    with pytest.raises(ValidationError):
        _make_signal(signal_kinds=())


def test_envelope_wraps_signal_and_commit() -> None:
    signal = _make_signal()
    commit = b"\xab" * 32
    envelope = FederationSignalEnvelope(signal=signal, commit=commit)
    assert envelope.signal == signal
    assert envelope.commit == commit
