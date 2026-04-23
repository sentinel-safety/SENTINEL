# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from shared.audit import (
    GENESIS_HASH,
    HASH_HEX_LEN,
    AuditEntryPayload,
    compute_entry_hash,
)

_TENANT = UUID("11111111-1111-1111-1111-111111111111")
_OTHER = UUID("22222222-2222-2222-2222-222222222222")
_WHEN = datetime(2025, 4, 19, 12, 0, 0, tzinfo=UTC)


def _payload(**overrides: Any) -> AuditEntryPayload:
    data: dict[str, Any] = {
        "tenant_id": _TENANT,
        "sequence": 1,
        "actor_id": None,
        "event_type": "tenant.created",
        "details": {"k": "v"},
        "timestamp": _WHEN,
        "previous_entry_hash": GENESIS_HASH,
    }
    data.update(overrides)
    return AuditEntryPayload(**data)


class TestGenesisHash:
    def test_is_sixty_four_zero_chars(self) -> None:
        assert GENESIS_HASH == "0" * 64
        assert len(GENESIS_HASH) == HASH_HEX_LEN


class TestComputeEntryHash:
    def test_is_deterministic(self) -> None:
        assert compute_entry_hash(_payload()) == compute_entry_hash(_payload())

    def test_output_is_sixty_four_hex_chars(self) -> None:
        digest = compute_entry_hash(_payload())
        assert len(digest) == HASH_HEX_LEN
        int(digest, 16)

    def test_changes_when_tenant_id_changes(self) -> None:
        assert compute_entry_hash(_payload(tenant_id=_TENANT)) != compute_entry_hash(
            _payload(tenant_id=_OTHER)
        )

    def test_changes_when_sequence_changes(self) -> None:
        assert compute_entry_hash(_payload(sequence=1)) != compute_entry_hash(_payload(sequence=2))

    def test_changes_when_actor_id_changes(self) -> None:
        assert compute_entry_hash(_payload(actor_id=None)) != compute_entry_hash(
            _payload(actor_id=uuid4())
        )

    def test_changes_when_event_type_changes(self) -> None:
        assert compute_entry_hash(_payload(event_type="a")) != compute_entry_hash(
            _payload(event_type="b")
        )

    def test_changes_when_details_change(self) -> None:
        assert compute_entry_hash(_payload(details={"k": 1})) != compute_entry_hash(
            _payload(details={"k": 2})
        )

    def test_changes_when_timestamp_changes(self) -> None:
        later = _WHEN + timedelta(microseconds=1)
        assert compute_entry_hash(_payload(timestamp=_WHEN)) != compute_entry_hash(
            _payload(timestamp=later)
        )

    def test_changes_when_previous_hash_changes(self) -> None:
        assert compute_entry_hash(_payload(previous_entry_hash=GENESIS_HASH)) != (
            compute_entry_hash(_payload(previous_entry_hash="a" * 64))
        )

    def test_detail_key_order_does_not_change_hash(self) -> None:
        assert compute_entry_hash(_payload(details={"a": 1, "b": 2})) == compute_entry_hash(
            _payload(details={"b": 2, "a": 1})
        )

    def test_nested_detail_key_order_does_not_change_hash(self) -> None:
        assert compute_entry_hash(
            _payload(details={"outer": {"a": 1, "b": 2}})
        ) == compute_entry_hash(_payload(details={"outer": {"b": 2, "a": 1}}))

    def test_non_utc_aware_timestamp_hashes_same_as_utc(self) -> None:
        plus_two = timezone(timedelta(hours=2))
        shifted = _payload(timestamp=datetime(2025, 4, 19, 14, 0, 0, tzinfo=plus_two))
        canonical = _payload(timestamp=_WHEN)
        assert compute_entry_hash(shifted) == compute_entry_hash(canonical)


class TestPayloadValidation:
    def test_rejects_naive_timestamp(self) -> None:
        with pytest.raises(ValidationError):
            _payload(timestamp=datetime(2025, 1, 1))  # noqa: DTZ001

    def test_rejects_sequence_below_one(self) -> None:
        with pytest.raises(ValidationError):
            _payload(sequence=0)

    def test_rejects_empty_event_type(self) -> None:
        with pytest.raises(ValidationError):
            _payload(event_type="")

    def test_rejects_event_type_over_one_hundred_chars(self) -> None:
        with pytest.raises(ValidationError):
            _payload(event_type="x" * 101)

    def test_rejects_short_previous_hash(self) -> None:
        with pytest.raises(ValidationError):
            _payload(previous_entry_hash="0" * 63)

    def test_rejects_long_previous_hash(self) -> None:
        with pytest.raises(ValidationError):
            _payload(previous_entry_hash="0" * 65)

    def test_rejects_unknown_field(self) -> None:
        with pytest.raises(ValidationError):
            AuditEntryPayload(
                tenant_id=_TENANT,
                sequence=1,
                actor_id=None,
                event_type="t",
                details={},
                timestamp=_WHEN,
                previous_entry_hash=GENESIS_HASH,
                nonsense="x",  # type: ignore[call-arg]
            )
