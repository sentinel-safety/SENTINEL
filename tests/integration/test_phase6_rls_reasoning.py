# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from shared.db.session import tenant_session
from shared.explainability.reasoning_repository import (
    insert_reasoning,
    list_reasoning_for_actor,
)
from shared.schemas.enums import ResponseTier
from shared.schemas.reasoning import PrimaryDriver, Reasoning

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


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


def _reasoning(tenant: uuid.UUID, actor: uuid.UUID) -> Reasoning:
    return Reasoning(
        actor_id=actor,
        tenant_id=tenant,
        score_change=15,
        new_score=55,
        new_tier=ResponseTier.ACTIVE_MONITOR,
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


async def test_tenant_cannot_read_other_tenants_reasoning(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tenant_a = str(uuid.uuid4())
    tenant_b = str(uuid.uuid4())
    actor_a = str(uuid.uuid4())
    actor_b = str(uuid.uuid4())
    await _seed(admin_engine, tenant_a, actor_a)
    await _seed(admin_engine, tenant_b, actor_b)
    async with tenant_session(uuid.UUID(tenant_a)) as session:
        await insert_reasoning(
            session,
            reasoning=_reasoning(uuid.UUID(tenant_a), uuid.UUID(actor_a)),
            event_id=None,
        )
    async with tenant_session(uuid.UUID(tenant_b)) as session:
        rows = await list_reasoning_for_actor(
            session, tenant_id=uuid.UUID(tenant_a), actor_id=uuid.UUID(actor_a), limit=5
        )
    assert rows == ()
