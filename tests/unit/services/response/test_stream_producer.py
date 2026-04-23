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

from services.response.app.stream_producer import enqueue_tier_change
from shared.response.tier_change import TierChangeEvent
from shared.schemas.enums import ResponseTier

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


async def test_enqueue_writes_single_entry() -> None:
    redis = fakeredis.FakeRedis(decode_responses=False)
    event = TierChangeEvent(
        tenant_id=uuid4(),
        actor_id=uuid4(),
        event_id=uuid4(),
        previous_tier=ResponseTier.WATCH,
        new_tier=ResponseTier.ACTIVE_MONITOR,
        new_score=45,
        triggered_at=datetime.now(UTC),
    )
    await enqueue_tier_change(redis, stream_name="response:tier_changes", event=event)
    entries = await redis.xrange("response:tier_changes")
    assert len(entries) == 1
    body = orjson.loads(entries[0][1][b"data"])
    assert body["new_score"] == 45
    assert body["new_tier"] == int(ResponseTier.ACTIVE_MONITOR)
