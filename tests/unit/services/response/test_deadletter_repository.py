# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import fakeredis.aioredis as fakeredis
import orjson
import pytest

from services.response.app.deadletter_repository import list_dead_letters
from shared.response.tier_change import TierChangeEvent
from shared.schemas.enums import ResponseTier

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


async def test_lists_entries_for_tenant() -> None:
    redis = fakeredis.FakeRedis(decode_responses=False)
    tenant_a = uuid4()
    tenant_b = uuid4()
    event_a = TierChangeEvent(
        tenant_id=tenant_a,
        actor_id=uuid4(),
        event_id=uuid4(),
        previous_tier=ResponseTier.WATCH,
        new_tier=ResponseTier.ACTIVE_MONITOR,
        new_score=45,
        triggered_at=datetime.now(UTC),
    )
    event_b = TierChangeEvent(
        tenant_id=tenant_b,
        actor_id=uuid4(),
        event_id=uuid4(),
        previous_tier=ResponseTier.WATCH,
        new_tier=ResponseTier.ACTIVE_MONITOR,
        new_score=45,
        triggered_at=datetime.now(UTC),
    )
    await redis.xadd(
        "response:dead_letter",
        {
            "data": orjson.dumps(event_a.model_dump(mode="json")),
            "attempt": b"5",
            "reason": b"retries_exhausted",
        },
    )
    await redis.xadd(
        "response:dead_letter",
        {
            "data": orjson.dumps(event_b.model_dump(mode="json")),
            "attempt": b"5",
            "reason": b"retries_exhausted",
        },
    )
    entries = await list_dead_letters(
        redis, stream_name="response:dead_letter", tenant_id=tenant_a, limit=100
    )
    assert len(entries) == 1
    assert entries[0].tenant_id == tenant_a
