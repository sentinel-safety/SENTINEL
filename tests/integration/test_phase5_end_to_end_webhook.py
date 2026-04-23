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
from shared.webhook.signing import verify_signature

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

_URL = "https://tenant.example/hook"
_SECRET = "a" * 64  # pragma: allowlist secret


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
            {"id": str(uuid4()), "t": tid, "u": _URL, "sh": _SECRET},
        )
        await conn.execute(
            text(
                "INSERT INTO tenant_action_config (tenant_id, mode, action_overrides, "
                "webhook_secret_hash) VALUES (:t, 'auto_enforce', '{}'::jsonb, :s)"
            ),
            {"t": tid, "s": _SECRET},
        )


async def test_tier_change_fires_hmac_signed_webhook(
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
        new_tier=ResponseTier.RESTRICT,
        new_score=80,
        triggered_at=datetime.now(UTC),
    )
    await enqueue_tier_change(redis, stream_name="response:tier_changes", event=event)
    stop = asyncio.Event()
    received_headers: list[dict[str, str]] = []
    received_bodies: list[bytes] = []
    with respx.mock() as mock:
        route = mock.post(_URL).mock(return_value=Response(200))
        await run_webhook_worker(redis, stop_event=stop, iteration_limit=1)
        for call in route.calls:
            received_headers.append(dict(call.request.headers))
            received_bodies.append(call.request.content)
    assert len(received_headers) == 1
    sig_header = received_headers[0]["x-sentinel-signature"]
    verify_signature(
        header=sig_header,
        secret=_SECRET,
        body=received_bodies[0],
        now=datetime.now(UTC),
        skew_seconds=300,
    )
