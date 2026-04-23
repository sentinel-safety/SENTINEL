# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import orjson
import redis.asyncio as aioredis

from shared.contracts.response import DeadLetterEntry
from shared.response.tier_change import TierChangeEvent


def _stream_id_to_timestamp(entry_id: bytes) -> datetime:
    ms = int(entry_id.split(b"-")[0])
    return datetime.fromtimestamp(ms / 1000, tz=UTC)


async def list_dead_letters(
    redis: aioredis.Redis,  # type: ignore[type-arg]
    *,
    stream_name: str,
    tenant_id: UUID,
    limit: int,
) -> tuple[DeadLetterEntry, ...]:
    raw = await redis.xrevrange(stream_name, count=limit)
    out: list[DeadLetterEntry] = []
    for entry_id, fields in raw:
        payload = TierChangeEvent.model_validate(orjson.loads(fields[b"data"]))
        if payload.tenant_id != tenant_id:
            continue
        out.append(
            DeadLetterEntry(
                entry_id=entry_id.decode(),
                tenant_id=payload.tenant_id,
                actor_id=payload.actor_id,
                event_kind="tier.changed",
                attempt=int(fields.get(b"attempt", b"1")),
                reason=fields.get(b"reason", b"unknown").decode(),
                enqueued_at=_stream_id_to_timestamp(entry_id),
            )
        )
    return tuple(out)
