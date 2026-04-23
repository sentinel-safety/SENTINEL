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

from services.patterns.app.main import create_app
from shared.contracts.patterns import DetectRequest, DetectResponse
from shared.contracts.preprocess import ExtractedFeatures
from shared.schemas.enums import EventType
from shared.schemas.event import Event

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def _seed(engine: AsyncEngine, tenant_id, actor_id) -> None:  # type: ignore[no-untyped-def]
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, "
                "data_retention_days, feature_flags) VALUES (:t, 'acme', 'free', '{}', 30, "
                "'{}'::jsonb) ON CONFLICT DO NOTHING"
            ),
            {"t": str(tenant_id)},
        )
        await conn.execute(
            text(
                "INSERT INTO actor (id, tenant_id, external_id_hash, claimed_age_band, metadata) "
                "VALUES (:a, :t, :h, 'unknown', '{}'::jsonb) ON CONFLICT DO NOTHING"
            ),
            {"a": str(actor_id), "t": str(tenant_id), "h": "5" * 64},
        )


async def test_detect_returns_empty_matches_when_no_patterns_fire(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tenant_id = uuid4()
    actor_id = uuid4()
    await _seed(admin_engine, tenant_id, actor_id)

    request = DetectRequest(
        event=Event(
            id=uuid4(),
            tenant_id=tenant_id,
            actor_id=actor_id,
            target_actor_ids=(uuid4(),),
            conversation_id=uuid4(),
            content_hash="a" * 64,
            timestamp=datetime.now(UTC),
            type=EventType.MESSAGE,
        ),
        features=ExtractedFeatures(
            normalized_content="hello",
            language="en",
            token_count=1,
            contains_url=False,
            contains_contact_request=False,
            minor_recipient=False,
            late_night_local=False,
        ),
    )

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/internal/detect",
            json=request.model_dump(mode="json"),
        )
    assert response.status_code == 200
    parsed = DetectResponse.model_validate(response.json())
    assert parsed.matches == ()
    assert parsed.matched_ids == ()
