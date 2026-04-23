# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from shared.db.event_writes import ensure_event_rows
from shared.db.models import Actor as ActorRow
from shared.schemas.enums import EventType
from shared.schemas.event import Event

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def _seed_tenant_and_actor(engine: AsyncEngine, tenant_id, actor_id) -> None:  # type: ignore[no-untyped-def]
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, "
                "data_retention_days, feature_flags) "
                "VALUES (:t, 'acme', 'free', '{}', 30, '{}'::jsonb) ON CONFLICT DO NOTHING"
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


async def test_ensure_event_rows_idempotent(admin_engine: AsyncEngine, clean_tables: None) -> None:
    tenant_id = uuid4()
    actor_id = uuid4()
    await _seed_tenant_and_actor(admin_engine, tenant_id, actor_id)

    now = datetime.now(UTC)
    conversation_id = uuid4()
    event_id = uuid4()
    event = Event(
        id=event_id,
        tenant_id=tenant_id,
        conversation_id=conversation_id,
        actor_id=actor_id,
        timestamp=now,
        type=EventType.MESSAGE,
        content_hash="c" * 64,
    )

    factory = async_sessionmaker(bind=admin_engine, expire_on_commit=False, autoflush=False)
    async with factory() as s, s.begin():
        await s.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(tenant_id)})
        await ensure_event_rows(s, event)
        await ensure_event_rows(s, event)
    async with admin_engine.begin() as conn:
        rows = (
            await conn.execute(
                text("SELECT count(*) FROM event WHERE id = :e"), {"e": str(event_id)}
            )
        ).scalar_one()
    assert rows == 1
    _ = ActorRow
