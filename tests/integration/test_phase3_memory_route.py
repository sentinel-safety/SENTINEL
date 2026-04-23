# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from services.memory.app.main import create_app
from shared.config import Settings

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def _seed(engine: AsyncEngine, tenant_id, actor_id) -> None:  # type: ignore[no-untyped-def]
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, "
                "data_retention_days, feature_flags) VALUES (:t, 'acme', 'free', '{}', 30, "
                "'{}'::jsonb) ON CONFLICT DO NOTHING"
            ),
            {"t": str(tenant_id)},
        )
        await conn.execute(
            text(
                "INSERT INTO actor (id, tenant_id, external_id_hash, claimed_age_band, metadata) "
                "VALUES (:a, :t, :h, 'unknown', '{}'::jsonb) ON CONFLICT DO NOTHING"
            ),
            {"a": str(actor_id), "t": str(tenant_id), "h": "2" * 64},
        )


async def test_actor_memory_endpoint_returns_view(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tenant_id = uuid4()
    actor_id = uuid4()
    await _seed(admin_engine, tenant_id, actor_id)

    now = datetime.now(UTC)
    conv_id = uuid4()
    async with admin_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO conversation (id, tenant_id, participant_actor_ids, started_at, "
                "last_message_at, channel_type) VALUES (:c, :t, :p, :s, :l, 'dm')"
            ),
            {
                "c": str(conv_id),
                "t": str(tenant_id),
                "p": [str(actor_id)],
                "s": now - timedelta(days=5),
                "l": now - timedelta(days=5),
            },
        )
        await conn.execute(
            text(
                "INSERT INTO event (id, tenant_id, conversation_id, actor_id, target_actor_ids, "
                "timestamp, type, content_hash, content_features, idempotency_key) "
                "VALUES (:i, :t, :c, :a, :tg, :ts, 'message', :h, CAST('{}' AS jsonb), :k)"
            ),
            {
                "i": str(uuid4()),
                "t": str(tenant_id),
                "c": str(conv_id),
                "a": str(actor_id),
                "tg": [str(uuid4())],
                "ts": now - timedelta(days=5),
                "h": "3" * 64,
                "k": str(uuid4()),
            },
        )

    app = create_app(Settings(env="test"))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/internal/actor-memory",
            json={
                "tenant_id": str(tenant_id),
                "actor_id": str(actor_id),
                "lookback_days": 21,
            },
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["view"]["distinct_conversations_last_window"] == 1
    assert body["view"]["total_events_last_window"] == 1
