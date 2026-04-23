# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from shared.schemas import GENESIS_HASH, AuditEventType, AuditLogEntry

pytestmark = pytest.mark.unit


def test_genesis_hash_is_sha256_zero() -> None:
    assert len(GENESIS_HASH) == 64
    assert GENESIS_HASH == "0" * 64


def test_audit_entry_accepts_null_actor_for_tenant_events() -> None:
    e = AuditLogEntry(
        id=uuid4(),
        tenant_id=uuid4(),
        actor_id=None,
        event_type=AuditEventType.TENANT_SETTING_CHANGED,
        timestamp=datetime.now(UTC),
        previous_entry_hash=GENESIS_HASH,
        entry_hash="a" * 64,
    )
    assert e.actor_id is None


def test_audit_entry_rejects_non_hex_hashes() -> None:
    with pytest.raises(ValidationError):
        AuditLogEntry(
            id=uuid4(),
            tenant_id=uuid4(),
            event_type=AuditEventType.SCORE_CHANGED,
            timestamp=datetime.now(UTC),
            previous_entry_hash="not-a-hash",
            entry_hash="a" * 64,
        )


def test_audit_entry_roundtrip() -> None:
    e = AuditLogEntry(
        id=uuid4(),
        tenant_id=uuid4(),
        actor_id=uuid4(),
        event_type=AuditEventType.SCORE_CHANGED,
        details={"old_score": 20, "new_score": 45, "cause": "pattern:isolation"},
        timestamp=datetime.now(UTC),
        previous_entry_hash="b" * 64,
        entry_hash="c" * 64,
    )
    restored = AuditLogEntry.model_validate(e.model_dump(mode="json"))
    assert restored == e
