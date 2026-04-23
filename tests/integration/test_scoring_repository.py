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

from services.scoring.app.repository import (
    load_or_initialize,
    persist,
)
from shared.db.session import tenant_session
from shared.schemas.enums import ResponseTier
from shared.schemas.suspicion_profile import ScoreHistoryEntry, SuspicionProfile

pytestmark = pytest.mark.integration


async def _seed_tenant_and_actor(engine: AsyncEngine, tenant_id: UUID, actor_id: UUID) -> None:
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, "
                "data_retention_days, feature_flags) "
                "VALUES (:tid, 'acme', 'free', '{}', 30, '{}'::jsonb) ON CONFLICT DO NOTHING"
            ),
            {"tid": str(tenant_id)},
        )
        await conn.execute(
            text(
                "INSERT INTO actor (id, tenant_id, external_id_hash, claimed_age_band) "
                "VALUES (:aid, :tid, :h, 'unknown') ON CONFLICT DO NOTHING"
            ),
            {"aid": str(actor_id), "tid": str(tenant_id), "h": "a" * 64},
        )


async def test_load_or_initialize_returns_baseline_when_absent(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tenant_id = uuid4()
    actor_id = uuid4()
    await _seed_tenant_and_actor(admin_engine, tenant_id, actor_id)

    async with tenant_session(tenant_id) as session:
        profile = await load_or_initialize(
            session, tenant_id=tenant_id, actor_id=actor_id, now=datetime.now(UTC)
        )
    assert profile.current_score == 5
    assert profile.tier is ResponseTier.TRUSTED


async def test_persist_then_load_roundtrips_history_and_score(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tenant_id = uuid4()
    actor_id = uuid4()
    await _seed_tenant_and_actor(admin_engine, tenant_id, actor_id)
    now = datetime.now(UTC)

    entry = ScoreHistoryEntry(at=now, delta=15, cause="signal:secrecy_request", new_score=20)
    profile = SuspicionProfile(
        actor_id=actor_id,
        tenant_id=tenant_id,
        current_score=20,
        tier=ResponseTier.WATCH,
        tier_entered_at=now,
        last_updated=now,
        last_decay_applied=now,
        score_history=(entry,),
    )

    async with tenant_session(tenant_id) as session:
        await persist(session, profile=profile, new_history=(entry,))

    async with tenant_session(tenant_id) as session:
        reloaded = await load_or_initialize(
            session, tenant_id=tenant_id, actor_id=actor_id, now=now
        )
    assert reloaded.current_score == 20
    assert reloaded.tier is ResponseTier.WATCH
