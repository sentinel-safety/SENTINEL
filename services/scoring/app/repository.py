# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from shared.db.event_writes import ensure_event_rows
from shared.db.models import ScoreHistory as ScoreHistoryRow
from shared.db.models import SuspicionProfile as SuspicionProfileRow
from shared.schemas.enums import ResponseTier
from shared.schemas.event import Event
from shared.schemas.suspicion_profile import ScoreHistoryEntry, SuspicionProfile

_BASELINE_SCORE: int = 5


async def load_or_initialize(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    actor_id: UUID,
    now: datetime,
) -> SuspicionProfile:
    result = await session.execute(
        select(SuspicionProfileRow).where(
            SuspicionProfileRow.tenant_id == tenant_id,
            SuspicionProfileRow.actor_id == actor_id,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        return SuspicionProfile(
            actor_id=actor_id,
            tenant_id=tenant_id,
            current_score=_BASELINE_SCORE,
            tier=ResponseTier.TRUSTED,
            tier_entered_at=now,
            last_updated=now,
            last_decay_applied=now,
        )
    return SuspicionProfile(
        actor_id=row.actor_id,
        tenant_id=row.tenant_id,
        current_score=row.current_score,
        tier=ResponseTier(row.tier),
        tier_entered_at=row.tier_entered_at,
        last_updated=row.last_updated,
        last_decay_applied=row.last_decay_applied,
        escalation_markers=tuple(row.escalation_markers or ()),
        network_signals=dict(row.network_signals or {}),
    )


async def persist(
    session: AsyncSession,
    *,
    event: Event | None = None,
    profile: SuspicionProfile,
    new_history: tuple[ScoreHistoryEntry, ...],
) -> None:
    if event is not None:
        await ensure_event_rows(session, event)
    stmt = pg_insert(SuspicionProfileRow).values(
        tenant_id=profile.tenant_id,
        actor_id=profile.actor_id,
        current_score=profile.current_score,
        tier=int(profile.tier),
        tier_entered_at=profile.tier_entered_at,
        last_updated=profile.last_updated,
        last_decay_applied=profile.last_decay_applied or profile.last_updated,
        escalation_markers=list(profile.escalation_markers),
        network_signals=profile.network_signals,
        notes=[],
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=[SuspicionProfileRow.tenant_id, SuspicionProfileRow.actor_id],
        set_={
            "current_score": stmt.excluded.current_score,
            "tier": stmt.excluded.tier,
            "tier_entered_at": stmt.excluded.tier_entered_at,
            "last_updated": stmt.excluded.last_updated,
            "last_decay_applied": stmt.excluded.last_decay_applied,
            "escalation_markers": stmt.excluded.escalation_markers,
            "network_signals": stmt.excluded.network_signals,
        },
    )
    await session.execute(stmt)

    for entry in new_history:
        session.add(
            ScoreHistoryRow(
                tenant_id=profile.tenant_id,
                actor_id=profile.actor_id,
                delta=entry.delta,
                previous_score=entry.new_score - entry.delta,
                new_score=entry.new_score,
                cause=entry.cause,
                event_id=entry.source_event_id,
                pattern_match_id=entry.pattern_match_id,
                recorded_at=entry.at,
            )
        )
    await session.flush()
