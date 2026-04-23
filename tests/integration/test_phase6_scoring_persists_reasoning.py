# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from services.scoring.app.main import create_app
from shared.config import Settings
from shared.db.session import tenant_session
from shared.explainability.reasoning_repository import list_reasoning_for_actor
from shared.schemas.enums import EventType

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


async def test_reasoning_row_is_persisted_on_tier_change(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tid = str(uuid4())
    aid = str(uuid4())
    await _seed(admin_engine, tid, aid)
    app = create_app(Settings(env="dev"))
    body = {
        "event": {
            "id": str(uuid4()),
            "tenant_id": tid,
            "actor_id": aid,
            "conversation_id": str(uuid4()),
            "target_actor_ids": [],
            "timestamp": datetime.now(UTC).isoformat(),
            "type": EventType.MESSAGE.value,
            "content_hash": "c" * 64,
            "content_features": {},
        },
        "signals": [{"kind": "sexual_escalation", "confidence": 1.0, "evidence": "x"}],
    }
    with patch("services.scoring.app.routes.enqueue_tier_change", new=AsyncMock()):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
            resp = await client.post("/internal/score", json=body)
    assert resp.status_code == 200
    async with tenant_session(UUID(tid)) as session:
        rows = await list_reasoning_for_actor(
            session, tenant_id=UUID(tid), actor_id=UUID(aid), limit=5
        )
    assert len(rows) == 1
    assert rows[0].primary_drivers[0].pattern_id
