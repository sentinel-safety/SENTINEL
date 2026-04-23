# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime

import fakeredis.aioredis as fakeredis
import orjson
import pytest
import respx
from httpx import Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from services.response.app.stream_producer import enqueue_tier_change
from services.response.app.webhook_worker import run_webhook_worker
from shared.response.tier_change import TierChangeEvent
from shared.schemas.enums import ResponseTier
from shared.schemas.reasoning import PrimaryDriver, Reasoning

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

_URL = "https://tenant.example/hook"
_SECRET = "a" * 64  # pragma: allowlist secret


async def _seed(admin_engine: AsyncEngine, tid: str) -> None:
    async with admin_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, "
                "data_retention_days, feature_flags) "
                "VALUES (:t, 'acme', 'free', '{}', 30, '{}'::jsonb)"
            ),
            {"t": tid},
        )
        await conn.execute(
            text(
                "INSERT INTO webhook_endpoint (id, tenant_id, url, secret_hash, "
                "subscribed_topics, active) VALUES (:id, :t, :u, :sh, ARRAY['tier.changed'], true)"
            ),
            {"id": str(uuid.uuid4()), "t": tid, "u": _URL, "sh": _SECRET},
        )
        await conn.execute(
            text(
                "INSERT INTO tenant_action_config (tenant_id, mode, action_overrides, "
                "webhook_secret_hash) VALUES (:t, 'auto_enforce', '{}'::jsonb, :s)"
            ),
            {"t": tid, "s": _SECRET},
        )


async def test_webhook_body_includes_reasoning(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tid = str(uuid.uuid4())
    await _seed(admin_engine, tid)
    tenant = uuid.UUID(tid)
    actor = uuid.uuid4()
    reasoning = Reasoning(
        actor_id=actor,
        tenant_id=tenant,
        score_change=15,
        new_score=80,
        new_tier=ResponseTier.RESTRICT,
        primary_drivers=(
            PrimaryDriver(
                pattern="Platform Migration Request",
                pattern_id="platform_migration",
                confidence=0.9,
                evidence="Actor asked to move to Telegram.",
            ),
        ),
        generated_at=datetime.now(UTC),
    )
    event = TierChangeEvent(
        tenant_id=tenant,
        actor_id=actor,
        event_id=uuid.uuid4(),
        previous_tier=ResponseTier.ACTIVE_MONITOR,
        new_tier=ResponseTier.RESTRICT,
        new_score=80,
        triggered_at=datetime.now(UTC),
        reasoning=reasoning,
    )
    redis = fakeredis.FakeRedis(decode_responses=False)
    await enqueue_tier_change(redis, stream_name="response:tier_changes", event=event)
    stop = asyncio.Event()
    bodies: list[bytes] = []
    with respx.mock() as mock:
        route = mock.post(_URL).mock(return_value=Response(200))
        await run_webhook_worker(redis, stop_event=stop, iteration_limit=1)
        for call in route.calls:
            bodies.append(call.request.content)
    assert bodies
    payload = orjson.loads(bodies[0])
    assert payload["payload"]["reasoning"]["new_tier"] == "restrict"
    assert (
        payload["payload"]["reasoning"]["primary_drivers"][0]["pattern_id"] == "platform_migration"
    )
