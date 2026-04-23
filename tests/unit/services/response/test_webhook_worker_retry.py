# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from uuid import UUID, uuid4

import fakeredis.aioredis as fakeredis
import pytest
import respx
from httpx import Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from services.response.app.stream_producer import enqueue_tier_change
from services.response.app.webhook_worker import run_webhook_worker
from shared.response.tier_change import TierChangeEvent
from shared.schemas.enums import ResponseTier

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]

_URL = "https://flaky.example/hook"


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


async def test_503_enqueues_to_retry_stream(admin_engine: AsyncEngine, clean_tables: None) -> None:
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
    await enqueue_tier_change(redis, stream_name="response:tier_changes", event=event)
    stop = asyncio.Event()
    with respx.mock() as mock:
        mock.post(_URL).mock(return_value=Response(503))
        await run_webhook_worker(redis, stop_event=stop, iteration_limit=1)
    retry_entries = await redis.xrange("response:retry_queue")
    assert len(retry_entries) == 1
    fields = retry_entries[0][1]
    assert fields[b"attempt"] == b"2"
    dl_entries = await redis.xrange("response:dead_letter")
    assert dl_entries == []
