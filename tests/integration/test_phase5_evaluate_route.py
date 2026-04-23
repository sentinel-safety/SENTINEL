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

from services.response.app.main import create_app
from shared.config import Settings
from shared.response.tier_change import TierChangeEvent
from shared.schemas.enums import ResponseTier

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def _seed(admin_engine: AsyncEngine, tid: str) -> None:
    async with admin_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, "
                "data_retention_days, feature_flags) VALUES (:t, 'acme', 'free', '{}', 30, '{}'::jsonb)"
            ),
            {"t": tid},
        )
        await conn.execute(
            text(
                "INSERT INTO tenant_action_config (tenant_id, mode, action_overrides, "
                "webhook_secret_hash) VALUES (:t, 'advisory', '{}'::jsonb, :s)"
            ),
            {"t": tid, "s": "a" * 64},
        )


async def test_evaluate_enqueues_and_returns_actions(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tid = str(uuid4())
    await _seed(admin_engine, tid)
    settings = Settings(env="dev")
    app = create_app(settings)
    event = TierChangeEvent(
        tenant_id=UUID(tid),
        actor_id=uuid4(),
        event_id=uuid4(),
        previous_tier=ResponseTier.ACTIVE_MONITOR,
        new_tier=ResponseTier.THROTTLE,
        new_score=65,
        triggered_at=datetime.now(UTC),
    )
    enqueue = AsyncMock()
    with patch("services.response.app.routes.enqueue_tier_change", enqueue):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
            resp = await client.post(
                "/internal/response/evaluate",
                json={"tier_change": event.model_dump(mode="json")},
            )
    assert resp.status_code == 200
    body = resp.json()
    assert body["enqueued"] is True
    assert "throttle_dm_to_minors" in body["recommended_action_kinds"]
    enqueue.assert_awaited()
