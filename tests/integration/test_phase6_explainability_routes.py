# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from services.explainability.app.main import create_app
from shared.config import Settings
from shared.db.session import tenant_session
from shared.explainability.reasoning_repository import insert_reasoning
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


async def test_get_reasoning_by_actor(admin_engine: AsyncEngine, clean_tables: None) -> None:
    tid = str(uuid.uuid4())
    aid = str(uuid.uuid4())
    await _seed(admin_engine, tid, aid)
    async with tenant_session(uuid.UUID(tid)) as session:
        await insert_reasoning(
            session,
            reasoning=_reasoning(uuid.UUID(tid), uuid.UUID(aid)),
            event_id=None,
        )
    app = create_app(Settings(env="dev"))
    headers = {"x-sentinel-tenant-id": tid}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.get(f"/internal/reasoning/actor/{aid}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["reasoning"][0]["new_score"] == 55


async def test_get_reasoning_by_event_returns_404_when_missing(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tid = str(uuid.uuid4())
    aid = str(uuid.uuid4())
    await _seed(admin_engine, tid, aid)
    app = create_app(Settings(env="dev"))
    headers = {"x-sentinel-tenant-id": tid}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.get(f"/internal/reasoning/event/{uuid.uuid4()}", headers=headers)
    assert resp.status_code == 404
