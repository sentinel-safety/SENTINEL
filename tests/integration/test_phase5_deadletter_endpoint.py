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
from shared.contracts.response import DeadLetterEntry
from shared.response.envelope import WebhookEventKind

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


async def test_dead_letter_endpoint_returns_entries(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tid = str(uuid4())
    await _seed(admin_engine, tid)
    settings = Settings(env="dev")
    app = create_app(settings)
    fake_entries = (
        DeadLetterEntry(
            entry_id="1-0",
            tenant_id=UUID(tid),
            actor_id=uuid4(),
            event_kind=WebhookEventKind.TIER_CHANGED.value,
            attempt=5,
            reason="retries_exhausted",
            enqueued_at=datetime.now(UTC),
        ),
    )
    with patch(
        "services.response.app.routes.list_dead_letters", AsyncMock(return_value=fake_entries)
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
            resp = await client.get(f"/internal/response/dead-letters/{tid}")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["entries"]) == 1
    assert body["entries"][0]["reason"] == "retries_exhausted"
