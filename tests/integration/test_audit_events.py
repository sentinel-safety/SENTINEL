# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from shared.audit.chain import verify_chain
from shared.audit.events import record_score_changed, record_tier_changed
from shared.db.session import tenant_session

pytestmark = pytest.mark.integration


async def _seed_tenant(engine: AsyncEngine, tenant_id: UUID) -> None:
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, "
                "data_retention_days, feature_flags) "
                "VALUES (:tid, 'acme', 'free', '{}', 30, '{}'::jsonb) ON CONFLICT DO NOTHING"
            ),
            {"tid": str(tenant_id)},
        )


async def _seed_actor(engine: AsyncEngine, tenant_id: UUID, actor_id: UUID) -> None:
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO actor (id, tenant_id, external_id_hash, claimed_age_band) "
                "VALUES (:aid, :tid, :hash, 'unknown') ON CONFLICT DO NOTHING"
            ),
            {
                "aid": str(actor_id),
                "tid": str(tenant_id),
                "hash": str(actor_id).replace("-", "") + "0" * 32,
            },
        )


async def test_score_changed_records_previous_and_new(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tenant_id = uuid4()
    actor_id = uuid4()
    await _seed_tenant(admin_engine, tenant_id)
    await _seed_actor(admin_engine, tenant_id, actor_id)

    async with tenant_session(tenant_id) as session:
        entry = await record_score_changed(
            session,
            tenant_id=tenant_id,
            actor_id=actor_id,
            previous_score=5,
            new_score=20,
            delta=15,
            cause="signal:secrecy_request",
            event_id=uuid4(),
            timestamp=datetime.now(UTC),
        )
    assert entry.event_type == "score.changed"
    assert entry.details["previous_score"] == 5
    assert entry.details["new_score"] == 20

    async with tenant_session(tenant_id) as session:
        count = await verify_chain(session, tenant_id)
    assert count == 1


async def test_tier_changed_emits_separate_entry(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tenant_id = uuid4()
    actor_id = uuid4()
    await _seed_tenant(admin_engine, tenant_id)
    await _seed_actor(admin_engine, tenant_id, actor_id)

    async with tenant_session(tenant_id) as session:
        await record_score_changed(
            session,
            tenant_id=tenant_id,
            actor_id=actor_id,
            previous_score=5,
            new_score=30,
            delta=25,
            cause="signal:isolation",
            event_id=uuid4(),
            timestamp=datetime.now(UTC),
        )
        await record_tier_changed(
            session,
            tenant_id=tenant_id,
            actor_id=actor_id,
            previous_tier=0,
            new_tier=1,
            triggering_score=30,
            timestamp=datetime.now(UTC),
        )

    async with tenant_session(tenant_id) as session:
        count = await verify_chain(session, tenant_id)
    assert count == 2
