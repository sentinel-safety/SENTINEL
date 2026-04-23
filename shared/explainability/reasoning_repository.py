# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.db.models import Reasoning as ReasoningRow
from shared.schemas.reasoning import Reasoning


async def insert_reasoning(
    session: AsyncSession,
    *,
    reasoning: Reasoning,
    event_id: UUID | None,
) -> UUID:
    row_id = uuid4()
    row = ReasoningRow(
        id=row_id,
        tenant_id=reasoning.tenant_id,
        actor_id=reasoning.actor_id,
        event_id=event_id,
        reasoning_json=reasoning.model_dump(mode="json"),
    )
    session.add(row)
    await session.flush()
    return row_id


async def list_reasoning_for_actor(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    actor_id: UUID,
    limit: int,
) -> tuple[Reasoning, ...]:
    stmt = (
        select(ReasoningRow)
        .where(
            ReasoningRow.tenant_id == tenant_id,
            ReasoningRow.actor_id == actor_id,
        )
        .order_by(desc(ReasoningRow.created_at))
        .limit(limit)
    )
    rows = (await session.execute(stmt)).scalars().all()
    return tuple(Reasoning.model_validate(r.reasoning_json) for r in rows)


async def get_reasoning_for_event(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    event_id: UUID,
) -> Reasoning | None:
    stmt = (
        select(ReasoningRow)
        .where(
            ReasoningRow.tenant_id == tenant_id,
            ReasoningRow.event_id == event_id,
        )
        .order_by(desc(ReasoningRow.created_at))
        .limit(1)
    )
    row = (await session.execute(stmt)).scalar_one_or_none()
    if row is None:
        return None
    return Reasoning.model_validate(row.reasoning_json)
