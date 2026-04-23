# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from shared.db.models import PatternMatch as PatternMatchRow
from shared.patterns.matches import PatternMatch
from shared.schemas.enums import GroomingStage

_GROOMING_STAGES = frozenset(stage.value for stage in GroomingStage)
_MAX_SUMMARY = 2000


def _stage_for(match: PatternMatch) -> str | None:
    value = match.signal_kind.value
    if value in _GROOMING_STAGES:
        return value
    return None


async def persist_pattern_matches(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    actor_id: UUID,
    event_id: UUID,
    matches: tuple[PatternMatch, ...],
    matched_at: datetime,
) -> tuple[UUID, ...]:
    if not matches:
        return ()
    assigned: list[UUID] = []
    for match in matches:
        row_id = uuid4()
        summary = " | ".join(match.evidence_excerpts)[:_MAX_SUMMARY]
        stmt = pg_insert(PatternMatchRow).values(
            id=row_id,
            tenant_id=tenant_id,
            actor_id=actor_id,
            pattern_id=match.pattern_name,
            pattern_version=match.prompt_version or "v1",
            confidence=match.confidence,
            event_ids=[str(event_id)],
            matched_at=matched_at,
            evidence_summary=summary,
            stage=_stage_for(match),
        )
        await session.execute(stmt)
        assigned.append(row_id)
    return tuple(assigned)
