# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from services.ingestion.app.main import create_app
from shared.config import Settings

pytestmark = pytest.mark.integration


async def _seed(engine: AsyncEngine, tenant_id: object, actor_id: object) -> None:
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
        await conn.execute(
            text(
                "INSERT INTO suspicion_profile (tenant_id, actor_id, current_score, tier, "
                "tier_entered_at, last_updated, last_decay_applied, escalation_markers, "
                "network_signals, notes) "
                "VALUES (:tid, :aid, 42, 2, :now, :now, :now, '[]'::jsonb, '{}'::jsonb, '[]'::jsonb)"
            ),
            {"tid": str(tenant_id), "aid": str(actor_id), "now": datetime.now(UTC)},
        )


async def test_actor_lookup_returns_current_state(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tenant_id = uuid4()
    actor_id = uuid4()
    await _seed(admin_engine, tenant_id, actor_id)
    app = create_app(Settings(env="test"))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(f"/v1/actors/{actor_id}", headers={"x-tenant-id": str(tenant_id)})
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["current_score"] == 42
    assert payload["tier"] == "active_monitor"


async def test_actor_lookup_404_when_unknown(admin_engine: AsyncEngine, clean_tables: None) -> None:
    tenant_id = uuid4()
    await _seed(admin_engine, tenant_id, uuid4())
    app = create_app(Settings(env="test"))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(f"/v1/actors/{uuid4()}", headers={"x-tenant-id": str(tenant_id)})
    assert resp.status_code == 404
