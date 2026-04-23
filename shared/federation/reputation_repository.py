# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.db.models import FederationReputationEvent


async def insert_reputation_event(
    session: AsyncSession,
    *,
    publisher_tenant_id: UUID,
    reporter_tenant_id: UUID,
    delta: int,
    reason: str,
) -> FederationReputationEvent:
    event = FederationReputationEvent(
        publisher_tenant_id=publisher_tenant_id,
        reporter_tenant_id=reporter_tenant_id,
        delta=delta,
        reason=reason,
    )
    session.add(event)
    await session.flush()
    return event


async def list_events_for_publisher(
    session: AsyncSession,
    *,
    publisher_tenant_id: UUID,
) -> tuple[FederationReputationEvent, ...]:
    result = await session.execute(
        select(FederationReputationEvent).where(
            FederationReputationEvent.publisher_tenant_id == publisher_tenant_id
        )
    )
    return tuple(result.scalars().all())
