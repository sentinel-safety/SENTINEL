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

from services.scoring.app.main import create_app as create_scoring
from shared.audit.chain import verify_chain
from shared.config import Settings
from shared.db.session import tenant_session
from shared.schemas.enums import EventType

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
                "VALUES (:aid, :tid, :h, 'under_13') ON CONFLICT DO NOTHING"
            ),
            {"aid": str(actor_id), "tid": str(tenant_id), "h": "a" * 64},
        )


async def test_hash_chain_unbroken_after_100_events(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tenant_id = uuid4()
    actor_id = uuid4()
    await _seed(admin_engine, tenant_id, actor_id)

    app = create_scoring(Settings(env="test"))
    start = datetime.now(UTC)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        for i in range(100):
            body = {
                "event": {
                    "id": str(uuid4()),
                    "tenant_id": str(tenant_id),
                    "conversation_id": str(uuid4()),
                    "actor_id": str(actor_id),
                    "target_actor_ids": [],
                    "timestamp": (start + timedelta(seconds=i)).isoformat(),
                    "type": EventType.MESSAGE.value,
                    "content_hash": "a" * 64,
                },
                "signals": [
                    {"kind": "personal_info_probe", "confidence": 0.5, "evidence": "x"},
                ],
            }
            resp = await client.post("/internal/score", json=body)
            assert resp.status_code == 200

    async with tenant_session(tenant_id) as session:
        count = await verify_chain(session, tenant_id)
    assert count >= 100
