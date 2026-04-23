# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from shared.db.models import Conversation as ConversationRow
from shared.db.models import Event as EventRow
from shared.schemas.event import Event


async def ensure_event_rows(session: AsyncSession, event: Event) -> None:
    conv_stmt = pg_insert(ConversationRow).values(
        id=event.conversation_id,
        tenant_id=event.tenant_id,
        participant_actor_ids=[str(event.actor_id)] + [str(t) for t in event.target_actor_ids],
        started_at=event.timestamp,
        last_message_at=event.timestamp,
        channel_type="dm",
    )
    conv_stmt = conv_stmt.on_conflict_do_update(
        index_elements=[ConversationRow.id],
        set_={"last_message_at": event.timestamp},
    )
    await session.execute(conv_stmt)

    ev_stmt = pg_insert(EventRow).values(
        id=event.id,
        tenant_id=event.tenant_id,
        conversation_id=event.conversation_id,
        actor_id=event.actor_id,
        target_actor_ids=[str(t) for t in event.target_actor_ids],
        timestamp=event.timestamp,
        type=event.type.value,
        content_hash=event.content_hash,
        content_features=event.content_features,
        score_delta=event.score_delta,
        pattern_match_ids=[str(p) for p in event.pattern_match_ids],
        idempotency_key=str(event.id),
    )
    if event.pattern_match_ids:
        ev_stmt = ev_stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={"pattern_match_ids": ev_stmt.excluded.pattern_match_ids},
        )
    else:
        ev_stmt = ev_stmt.on_conflict_do_nothing(index_elements=["id"])
    await session.execute(ev_stmt)
