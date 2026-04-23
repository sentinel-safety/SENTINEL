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
from services.response.app.stream_producer import enqueue_tier_change
from services.response.app.webhook_worker import run_webhook_worker
from shared.response.tier_change import TierChangeEvent
from shared.schemas.enums import ResponseTier

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

_URL_FLAKY = "https://flaky.example/hook"
_URL_DEAD = "https://dead.example/hook"


async def _seed(admin_engine: AsyncEngine, tid: str, url: str) -> None:
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
            {"id": str(uuid4()), "t": tid, "u": url, "sh": "a" * 64},
        )
        await conn.execute(
            text(
                "INSERT INTO tenant_action_config (tenant_id, mode, action_overrides, "
                "webhook_secret_hash) VALUES (:t, 'advisory', '{}'::jsonb, :s)"
            ),
            {"t": tid, "s": "a" * 64},
        )


def _change(tid: str) -> TierChangeEvent:
    return TierChangeEvent(
        tenant_id=UUID(tid),
        actor_id=uuid4(),
        event_id=uuid4(),
        previous_tier=ResponseTier.ACTIVE_MONITOR,
        new_tier=ResponseTier.THROTTLE,
        new_score=65,
        triggered_at=datetime.now(UTC),
    )


async def test_503_then_success(admin_engine: AsyncEngine, clean_tables: None) -> None:
    tid = str(uuid4())
    await _seed(admin_engine, tid, _URL_FLAKY)
    redis = fakeredis.FakeRedis(decode_responses=False)
    await enqueue_tier_change(redis, stream_name="response:tier_changes", event=_change(tid))
    stop = asyncio.Event()
    with respx.mock() as mock:
        mock.post(_URL_FLAKY).mock(return_value=Response(503))
        await run_webhook_worker(redis, stop_event=stop, iteration_limit=1)
    retry_entries = await redis.xrange("response:retry_queue")
    assert len(retry_entries) == 1
    entry_id, fields = retry_entries[0]
    fields[b"next_attempt_at"] = str(time.time() - 1).encode()
    await redis.xdel("response:retry_queue", entry_id)
    await redis.xadd("response:retry_queue", dict(fields))
    with respx.mock() as mock:
        mock.post(_URL_FLAKY).mock(return_value=Response(200))
        await run_retry_worker(redis, stop_event=stop, iteration_limit=1)
    dl = await redis.xrange("response:dead_letter")
    assert dl == []


async def test_500_forever_deadletters(admin_engine: AsyncEngine, clean_tables: None) -> None:
    tid = str(uuid4())
    await _seed(admin_engine, tid, _URL_DEAD)
    redis = fakeredis.FakeRedis(decode_responses=False)
    event = _change(tid)
    await redis.xadd(
        "response:tier_changes",
        {
            "data": orjson.dumps(event.model_dump(mode="json")),
            "attempt": b"5",
        },
    )
    stop = asyncio.Event()
    with respx.mock() as mock:
        mock.post(_URL_DEAD).mock(return_value=Response(500))
        await run_webhook_worker(redis, stop_event=stop, iteration_limit=1)
    dl = await redis.xrange("response:dead_letter")
    assert len(dl) == 1
    assert dl[0][1][b"reason"] == b"retries_exhausted"
