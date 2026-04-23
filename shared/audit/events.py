# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from shared.audit.chain import append_entry
from shared.db.models import AuditLogEntry
from shared.schemas.audit_log import AuditEventType


async def record_event_scored(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    actor_id: UUID,
    event_id: UUID,
    signal_count: int,
    timestamp: datetime,
) -> AuditLogEntry:
    return await append_entry(
        session,
        tenant_id=tenant_id,
        event_type=AuditEventType.EVENT_SCORED.value,
        actor_id=actor_id,
        timestamp=timestamp,
        details={
            "event_id": str(event_id),
            "signal_count": signal_count,
        },
    )


async def record_score_changed(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    actor_id: UUID,
    previous_score: int,
    new_score: int,
    delta: int,
    cause: str,
    event_id: UUID | None,
    timestamp: datetime,
) -> AuditLogEntry:
    return await append_entry(
        session,
        tenant_id=tenant_id,
        event_type=AuditEventType.SCORE_CHANGED.value,
        actor_id=actor_id,
        timestamp=timestamp,
        details={
            "previous_score": previous_score,
            "new_score": new_score,
            "delta": delta,
            "cause": cause,
            "event_id": str(event_id) if event_id is not None else None,
        },
    )


async def record_tier_changed(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    actor_id: UUID,
    previous_tier: int,
    new_tier: int,
    triggering_score: int,
    timestamp: datetime,
) -> AuditLogEntry:
    return await append_entry(
        session,
        tenant_id=tenant_id,
        event_type=AuditEventType.TIER_CHANGED.value,
        actor_id=actor_id,
        timestamp=timestamp,
        details={
            "previous_tier": previous_tier,
            "new_tier": new_tier,
            "triggering_score": triggering_score,
        },
    )


async def record_pattern_matched(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    actor_id: UUID,
    pattern_name: str,
    confidence: float,
    event_id: UUID,
    pattern_match_id: UUID,
    timestamp: datetime,
) -> AuditLogEntry:
    return await append_entry(
        session,
        tenant_id=tenant_id,
        event_type=AuditEventType.PATTERN_MATCHED.value,
        actor_id=actor_id,
        timestamp=timestamp,
        details={
            "pattern_name": pattern_name,
            "confidence": confidence,
            "event_id": str(event_id),
            "pattern_match_id": str(pattern_match_id),
        },
    )


async def record_honeypot_activated(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    actor_id: UUID,
    persona_id: str,
    activation_id: UUID,
    timestamp: datetime,
) -> AuditLogEntry:
    return await append_entry(
        session,
        tenant_id=tenant_id,
        event_type=AuditEventType.HONEYPOT_ACTIVATED.value,
        actor_id=actor_id,
        timestamp=timestamp,
        details={
            "persona_id": persona_id,
            "activation_id": str(activation_id),
        },
    )


async def record_honeypot_denied(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    actor_id: UUID,
    reasons: tuple[str, ...],
    activation_id: UUID,
    timestamp: datetime,
) -> AuditLogEntry:
    return await append_entry(
        session,
        tenant_id=tenant_id,
        event_type=AuditEventType.HONEYPOT_DENIED.value,
        actor_id=actor_id,
        timestamp=timestamp,
        details={
            "reasons": list(reasons),
            "activation_id": str(activation_id),
        },
    )


async def record_honeypot_evidence_packaged(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    actor_id: UUID,
    evidence_package_id: UUID,
    content_hash: str,
    activation_id: UUID,
    timestamp: datetime,
) -> AuditLogEntry:
    return await append_entry(
        session,
        tenant_id=tenant_id,
        event_type=AuditEventType.HONEYPOT_EVIDENCE_PACKAGED.value,
        actor_id=actor_id,
        timestamp=timestamp,
        details={
            "evidence_package_id": str(evidence_package_id),
            "content_hash": content_hash,
            "activation_id": str(activation_id),
        },
    )


async def record_federation_published(
    session: AsyncSession,
    *,
    publisher_tenant_id: UUID,
    signal_id: UUID,
    actor_hash: str,
    signal_kinds: tuple[str, ...],
    flagged_at: datetime,
) -> AuditLogEntry:
    return await append_entry(
        session,
        tenant_id=publisher_tenant_id,
        event_type=AuditEventType.FEDERATION_PUBLISHED.value,
        details={
            "signal_id": str(signal_id),
            "actor_hash": actor_hash,
            "signal_kinds": list(signal_kinds),
            "flagged_at": flagged_at.isoformat(),
        },
    )


async def record_federation_received(
    session: AsyncSession,
    *,
    receiver_tenant_id: UUID,
    publisher_tenant_id: UUID,
    signal_id: UUID,
    actor_hash: str,
) -> AuditLogEntry:
    return await append_entry(
        session,
        tenant_id=receiver_tenant_id,
        event_type=AuditEventType.FEDERATION_RECEIVED.value,
        details={
            "signal_id": str(signal_id),
            "publisher_tenant_id": str(publisher_tenant_id),
            "actor_hash": actor_hash,
        },
    )
