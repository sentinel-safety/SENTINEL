# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import hashlib
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from shared.contracts.ingest import IngestEventRequest
from shared.db.models import Actor as ActorRow
from shared.db.models import Conversation as ConversationRow
from shared.db.models import Event as EventRow
from shared.schemas.base import FrozenModel
from shared.schemas.enums import AgeBand
from shared.schemas.event import Event

_MINOR_BANDS: frozenset[str] = frozenset(
    {AgeBand.UNDER_13.value, AgeBand.BAND_13_15.value, AgeBand.BAND_16_17.value}
)


class IntakeOutcome(FrozenModel):
    event: Event
    actor_id: UUID
    deduplicated: bool


def _content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _minor_recipient_from_metadata(metadata: dict[str, object]) -> bool:
    bands = metadata.get("recipient_age_bands")
    if not isinstance(bands, list | tuple):
        return False
    return any(isinstance(b, str) and b in _MINOR_BANDS for b in bands)


async def _upsert_actor(session: AsyncSession, *, tenant_id: UUID, external_id_hash: str) -> UUID:
    existing = await session.execute(
        select(ActorRow.id).where(
            ActorRow.tenant_id == tenant_id,
            ActorRow.external_id_hash == external_id_hash,
        )
    )
    row_id = existing.scalar_one_or_none()
    if row_id is not None:
        return row_id
    new_id = uuid4()
    stmt = pg_insert(ActorRow).values(
        id=new_id,
        tenant_id=tenant_id,
        external_id_hash=external_id_hash,
        claimed_age_band="unknown",
    )
    stmt = stmt.on_conflict_do_nothing(index_elements=["tenant_id", "external_id_hash"])
    await session.execute(stmt)
    result = await session.execute(
        select(ActorRow.id).where(
            ActorRow.tenant_id == tenant_id,
            ActorRow.external_id_hash == external_id_hash,
        )
    )
    return result.scalar_one()


async def _ensure_conversation(
    session: AsyncSession,
    *,
    conversation_id: UUID,
    tenant_id: UUID,
    actor_id: UUID,
    target_actor_ids: tuple[UUID, ...],
    timestamp: datetime,
) -> None:
    stmt = pg_insert(ConversationRow).values(
        id=conversation_id,
        tenant_id=tenant_id,
        participant_actor_ids=[str(actor_id)] + [str(a) for a in target_actor_ids],
        started_at=timestamp,
        last_message_at=timestamp,
        channel_type="dm",
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=[ConversationRow.id],
        set_={"last_message_at": timestamp},
    )
    await session.execute(stmt)


async def intake_event(session: AsyncSession, payload: IngestEventRequest) -> IntakeOutcome:
    existing = await session.execute(
        select(EventRow).where(
            EventRow.tenant_id == payload.tenant_id,
            EventRow.idempotency_key == payload.idempotency_key,
        )
    )
    existing_row = existing.scalar_one_or_none()
    if existing_row is not None:
        return IntakeOutcome(
            event=_to_schema(existing_row),
            actor_id=existing_row.actor_id,
            deduplicated=True,
        )

    actor_id = await _upsert_actor(
        session, tenant_id=payload.tenant_id, external_id_hash=payload.actor_external_id_hash
    )
    target_ids: tuple[UUID, ...] = tuple(
        [
            await _upsert_actor(session, tenant_id=payload.tenant_id, external_id_hash=h)
            for h in payload.target_actor_external_id_hashes
        ]
    )
    await _ensure_conversation(
        session,
        conversation_id=payload.conversation_id,
        tenant_id=payload.tenant_id,
        actor_id=actor_id,
        target_actor_ids=target_ids,
        timestamp=payload.timestamp,
    )

    event_id = uuid4()
    row = EventRow(
        id=event_id,
        tenant_id=payload.tenant_id,
        conversation_id=payload.conversation_id,
        actor_id=actor_id,
        target_actor_ids=[str(t) for t in target_ids],
        timestamp=payload.timestamp,
        type=payload.event_type.value,
        content_hash=_content_hash(payload.content),
        content_features={"minor_recipient": _minor_recipient_from_metadata(payload.metadata)},
        score_delta=0,
        pattern_match_ids=[],
        idempotency_key=payload.idempotency_key,
    )
    session.add(row)
    await session.flush()
    return IntakeOutcome(event=_to_schema(row), actor_id=actor_id, deduplicated=False)


def _to_schema(row: EventRow) -> Event:
    return Event(
        id=row.id,
        tenant_id=row.tenant_id,
        conversation_id=row.conversation_id,
        actor_id=row.actor_id,
        target_actor_ids=tuple(UUID(a) for a in (row.target_actor_ids or [])),
        timestamp=row.timestamp,
        type=row.type,
        content_hash=row.content_hash,
        content_features=dict(row.content_features or {}),
        processed_at=row.processed_at,
        score_delta=row.score_delta,
        pattern_match_ids=tuple(UUID(p) for p in (row.pattern_match_ids or [])),
    )
