# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.db.models import Event as EventRow

_MAX_SNIPPET = 500


@dataclass
class EventLookback:
    session: AsyncSession

    async def count_distinct_minor_targets(
        self, *, tenant_id: UUID, actor_id: UUID, window: timedelta
    ) -> int:
        since = datetime.now(UTC) - window
        stmt = select(EventRow.target_actor_ids, EventRow.content_features).where(
            EventRow.tenant_id == tenant_id,
            EventRow.actor_id == actor_id,
            EventRow.timestamp >= since,
        )
        distinct: set[str] = set()
        for row in (await self.session.execute(stmt)).all():
            if not (row.content_features or {}).get("minor_recipient"):
                continue
            for target in row.target_actor_ids or ():
                distinct.add(target)
        return len(distinct)

    async def fetch_recent_messages_for_actor(
        self, *, tenant_id: UUID, actor_id: UUID, limit: int = 10
    ) -> tuple[str, ...]:
        stmt = (
            select(EventRow.content_features)
            .where(
                EventRow.tenant_id == tenant_id,
                EventRow.actor_id == actor_id,
            )
            .order_by(EventRow.timestamp.desc())
            .limit(limit * 4)
        )
        seen: set[str] = set()
        ordered: list[str] = []
        for row in (await self.session.execute(stmt)).all():
            content_features = row.content_features or {}
            normalized = content_features.get("normalized_content")
            if not isinstance(normalized, str):
                continue
            snippet = normalized.strip()[:_MAX_SNIPPET]
            if not snippet or snippet in seen:
                continue
            seen.add(snippet)
            ordered.append(snippet)
            if len(ordered) == limit:
                break
        return tuple(ordered)
