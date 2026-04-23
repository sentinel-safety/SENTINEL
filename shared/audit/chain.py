# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from shared.audit.hashing import (
    GENESIS_HASH,
    AuditEntryPayload,
    compute_entry_hash,
)
from shared.db.models import AuditLogEntry
from shared.errors.exceptions import AuditChainBrokenError, AuditTamperedError

_LOCK_SQL = text("SELECT pg_advisory_xact_lock(hashtext('audit:' || :tid)::bigint)")


async def append_entry(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    event_type: str,
    details: dict[str, Any] | None = None,
    actor_id: UUID | None = None,
    timestamp: datetime | None = None,
) -> AuditLogEntry:
    await session.execute(_LOCK_SQL, {"tid": str(tenant_id)})

    tail = (
        await session.execute(
            select(AuditLogEntry.sequence, AuditLogEntry.entry_hash)
            .where(AuditLogEntry.tenant_id == tenant_id)
            .order_by(AuditLogEntry.sequence.desc())
            .limit(1)
        )
    ).first()

    if tail is None:
        next_sequence = 1
        previous_hash = GENESIS_HASH
    else:
        next_sequence = tail.sequence + 1
        previous_hash = tail.entry_hash

    payload = AuditEntryPayload(
        tenant_id=tenant_id,
        sequence=next_sequence,
        actor_id=actor_id,
        event_type=event_type,
        details=details or {},
        timestamp=timestamp or datetime.now(UTC),
        previous_entry_hash=previous_hash,
    )
    entry = AuditLogEntry(
        tenant_id=payload.tenant_id,
        actor_id=payload.actor_id,
        sequence=payload.sequence,
        event_type=payload.event_type,
        details=payload.details,
        timestamp=payload.timestamp,
        previous_entry_hash=payload.previous_entry_hash,
        entry_hash=compute_entry_hash(payload),
    )
    session.add(entry)
    await session.flush()
    return entry


async def verify_chain(session: AsyncSession, tenant_id: UUID) -> int:
    result = await session.execute(
        select(AuditLogEntry)
        .where(AuditLogEntry.tenant_id == tenant_id)
        .order_by(AuditLogEntry.sequence.asc())
    )
    expected_previous = GENESIS_HASH
    expected_sequence = 1
    count = 0
    for entry in result.scalars():
        if entry.sequence != expected_sequence:
            raise AuditChainBrokenError(
                f"sequence gap: expected {expected_sequence}, got {entry.sequence}",
                details={
                    "tenant_id": str(tenant_id),
                    "expected_sequence": expected_sequence,
                    "actual_sequence": entry.sequence,
                },
            )
        if entry.previous_entry_hash != expected_previous:
            raise AuditChainBrokenError(
                f"previous hash mismatch at sequence {entry.sequence}",
                details={"tenant_id": str(tenant_id), "sequence": entry.sequence},
            )
        recomputed = compute_entry_hash(
            AuditEntryPayload(
                tenant_id=entry.tenant_id,
                sequence=entry.sequence,
                actor_id=entry.actor_id,
                event_type=entry.event_type,
                details=entry.details,
                timestamp=entry.timestamp,
                previous_entry_hash=entry.previous_entry_hash,
            )
        )
        if recomputed != entry.entry_hash:
            raise AuditTamperedError(
                f"entry hash mismatch at sequence {entry.sequence}",
                details={"tenant_id": str(tenant_id), "sequence": entry.sequence},
            )
        expected_previous = entry.entry_hash
        expected_sequence += 1
        count += 1
    return count
