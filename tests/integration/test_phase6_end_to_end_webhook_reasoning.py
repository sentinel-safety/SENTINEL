# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from unittest.mock import patch

import fakeredis.aioredis as fakeredis
import orjson
import pytest
import respx
from httpx import ASGITransport, AsyncClient, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from services.response.app.webhook_worker import run_webhook_worker
from services.scoring.app.main import create_app
from shared.config import Settings
from shared.db.session import tenant_session
from shared.explainability.reasoning_repository import get_reasoning_for_event
from shared.response.tier_change import TierChangeEvent
from shared.schemas.enums import EventType

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

_URL = "https://tenant.example/hook"
_SECRET = "a" * 64  # pragma: allowlist secret


async def _seed(admin_engine: AsyncEngine, tid: str, aid: str) -> None:
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
                "INSERT INTO actor (id, tenant_id, external_id_hash, claimed_age_band) "
                "VALUES (:a, :t, :h, 'unknown')"
            ),
            {"a": aid, "t": tid, "h": "d" * 64},
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


async def test_flagged_actor_webhook_body_matches_stored_reasoning(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tid = str(uuid.uuid4())
    aid = str(uuid.uuid4())
    await _seed(admin_engine, tid, aid)
    event_id = str(uuid.uuid4())
    app = create_app(Settings(env="dev"))
    redis = fakeredis.FakeRedis(decode_responses=False)
    body = {
        "event": {
            "id": event_id,
            "tenant_id": tid,
            "actor_id": aid,
            "conversation_id": str(uuid.uuid4()),
            "target_actor_ids": [],
            "timestamp": datetime.now(UTC).isoformat(),
            "type": EventType.MESSAGE.value,
            "content_hash": "c" * 64,
            "content_features": {},
        },
        "signals": [{"kind": "sexual_escalation", "confidence": 1.0, "evidence": "x"}],
    }

    async def _fake_enqueue(_redis: object, *, stream_name: str, event: TierChangeEvent) -> None:
        payload = orjson.dumps(event.model_dump(mode="json"))
        await redis.xadd(stream_name, {"data": payload})

    with patch("services.scoring.app.routes.enqueue_tier_change", _fake_enqueue):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
            resp = await client.post("/internal/score", json=body)
    assert resp.status_code == 200

    stop = asyncio.Event()
    bodies: list[bytes] = []
    with respx.mock() as mock:
        route = mock.post(_URL).mock(return_value=Response(200))
        await run_webhook_worker(redis, stop_event=stop, iteration_limit=1)
        for call in route.calls:
            bodies.append(call.request.content)

    assert bodies, "webhook should have been delivered"
    delivered = orjson.loads(bodies[0])
    webhook_reasoning = delivered["payload"]["reasoning"]
    assert webhook_reasoning is not None
    assert webhook_reasoning["new_tier"] == "watch"
    assert webhook_reasoning["primary_drivers"]

    async with tenant_session(uuid.UUID(tid)) as session:
        stored = await get_reasoning_for_event(
            session, tenant_id=uuid.UUID(tid), event_id=uuid.UUID(event_id)
        )
    assert stored is not None
    assert stored.new_tier.name.lower() == webhook_reasoning["new_tier"]
    assert (
        stored.primary_drivers[0].pattern_id
        == (webhook_reasoning["primary_drivers"][0]["pattern_id"])
    )
