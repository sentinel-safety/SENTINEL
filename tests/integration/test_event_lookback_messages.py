# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from services.patterns.app.repositories.event_lookback import EventLookback

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
            {"a": str(actor_id), "t": str(tenant_id), "h": "a" * 64},
        )


async def _insert_event(  # type: ignore[no-untyped-def]
    engine, tenant_id, actor_id, conv_id, normalized, timestamp
) -> None:
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO conversation (id, tenant_id, participant_actor_ids, started_at, "
                "last_message_at, channel_type) VALUES (:c, :t, :p, :s, :l, 'dm') "
                "ON CONFLICT DO NOTHING"
            ),
            {
                "c": str(conv_id),
                "t": str(tenant_id),
                "p": [str(actor_id)],
                "s": timestamp,
                "l": timestamp,
            },
        )
        await conn.execute(
            text(
                "INSERT INTO event (id, tenant_id, conversation_id, actor_id, target_actor_ids, "
                "timestamp, type, content_hash, content_features, idempotency_key) "
                "VALUES (:i, :t, :c, :a, :tg, :ts, 'message', :h, CAST(:cf AS jsonb), :k)"
            ),
            {
                "i": str(uuid4()),
                "t": str(tenant_id),
                "c": str(conv_id),
                "a": str(actor_id),
                "tg": [],
                "ts": timestamp,
                "h": "b" * 64,
                "cf": f'{{"normalized_content": "{normalized}"}}' if normalized else "{}",
                "k": str(uuid4()),
            },
        )


async def test_fetch_recent_messages_returns_normalized_content(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tenant_id = uuid4()
    actor_id = uuid4()
    await _seed(admin_engine, tenant_id, actor_id)
    now = datetime.now(UTC)
    conv_id = uuid4()
    await _insert_event(
        admin_engine, tenant_id, actor_id, conv_id, "hello friend", now - timedelta(days=1)
    )
    await _insert_event(
        admin_engine, tenant_id, actor_id, conv_id, "only i get you", now - timedelta(days=2)
    )
    await _insert_event(admin_engine, tenant_id, actor_id, conv_id, "", now - timedelta(days=3))

    factory = async_sessionmaker(bind=admin_engine, expire_on_commit=False, autoflush=False)
    async with factory() as s, s.begin():
        await s.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(tenant_id)})
        lookback = EventLookback(session=s)
        messages = await lookback.fetch_recent_messages_for_actor(
            tenant_id=tenant_id, actor_id=actor_id, limit=10
        )
    assert "hello friend" in messages
    assert "only i get you" in messages
    assert "" not in messages


async def test_fetch_recent_messages_respects_limit(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tenant_id = uuid4()
    actor_id = uuid4()
    await _seed(admin_engine, tenant_id, actor_id)
    now = datetime.now(UTC)
    conv_id = uuid4()
    for i in range(6):
        await _insert_event(
            admin_engine, tenant_id, actor_id, conv_id, f"msg {i}", now - timedelta(days=i)
        )
    factory = async_sessionmaker(bind=admin_engine, expire_on_commit=False, autoflush=False)
    async with factory() as s, s.begin():
        await s.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(tenant_id)})
        lookback = EventLookback(session=s)
        messages = await lookback.fetch_recent_messages_for_actor(
            tenant_id=tenant_id, actor_id=actor_id, limit=3
        )
    assert len(messages) == 3
