# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime
from uuid import UUID, uuid4

import fakeredis.aioredis as fakeredis
import orjson
import pytest
import respx
from httpx import Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from services.response.app.retry_worker import run_retry_worker
from shared.response.tier_change import TierChangeEvent
from shared.schemas.enums import ResponseTier

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]

_URL = "https://recovered.example/hook"


async def _seed(admin_engine: AsyncEngine, tid: str) -> None:
    async with admin_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, "
                "data_retention_days, feature_flags) VALUES (:t, 'acme', 'free', '{}', 30, '{}'::jsonb)"
            ),
            {"t": tid},
        )
        await conn.execute(
            text(
                "INSERT INTO webhook_endpoint (id, tenant_id, url, secret_hash, "
                "subscribed_topics, active) VALUES (:id, :t, :u, :sh, ARRAY['tier.changed'], true)"
            ),
            {"id": str(uuid4()), "t": tid, "u": _URL, "sh": "a" * 64},
        )
        await conn.execute(
            text(
                "INSERT INTO tenant_action_config (tenant_id, mode, action_overrides, "
                "webhook_secret_hash) VALUES (:t, 'advisory', '{}'::jsonb, :s)"
            ),
            {"t": tid, "s": "a" * 64},
        )


async def test_retry_worker_redelivers_when_ready(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tid = str(uuid4())
    await _seed(admin_engine, tid)
    redis = fakeredis.FakeRedis(decode_responses=False)
    event = TierChangeEvent(
        tenant_id=UUID(tid),
        actor_id=uuid4(),
        event_id=uuid4(),
        previous_tier=ResponseTier.ACTIVE_MONITOR,
        new_tier=ResponseTier.THROTTLE,
        new_score=65,
        triggered_at=datetime.now(UTC),
    )
    await redis.xadd(
        "response:retry_queue",
        {
            "data": orjson.dumps(event.model_dump(mode="json")),
            "attempt": b"2",
            "next_attempt_at": str(time.time() - 1).encode(),
        },
    )
    stop = asyncio.Event()
    with respx.mock() as mock:
        route = mock.post(_URL).mock(return_value=Response(200))
        await run_retry_worker(redis, stop_event=stop, iteration_limit=1)
    assert route.called
    remaining = await redis.xrange("response:retry_queue")
    assert remaining == []
