# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncEngine

from services.patterns.app.main import create_app
from shared.config import Settings
from shared.contracts.patterns import DetectRequest, DetectResponse
from shared.contracts.preprocess import ExtractedFeatures
from shared.db.models import AuditLogEntry
from shared.db.models import PatternMatch as PatternMatchRow
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


async def test_detect_persists_pattern_match_rows_and_audit(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tenant_id = uuid4()
    actor_id = uuid4()
    await _seed(admin_engine, tenant_id, actor_id)

    event = Event(
        id=uuid4(),
        tenant_id=tenant_id,
        conversation_id=uuid4(),
        actor_id=actor_id,
        timestamp=datetime.now(UTC),
        type=EventType.MESSAGE,
        content_hash="7" * 64,
    )
    features = ExtractedFeatures(
        normalized_content="don't tell your parents",
        language="en",
        token_count=4,
        contains_url=False,
        contains_contact_request=False,
        minor_recipient=True,
        late_night_local=False,
    )
    body = DetectRequest(event=event, features=features).model_dump(mode="json")

    app = create_app(Settings(env="test"))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/internal/detect", json=body)
    assert resp.status_code == 200
    parsed = DetectResponse.model_validate(resp.json())
    assert len(parsed.matches) >= 1
    assert len(parsed.matched_ids) == len(parsed.matches)

    async with admin_engine.begin() as conn:
        rows = (
            (
                await conn.execute(
                    select(PatternMatchRow).where(PatternMatchRow.actor_id == actor_id)
                )
            )
            .scalars()
            .all()
        )
    assert len(rows) == len(parsed.matches)

    async with admin_engine.begin() as conn:
        audits = (
            (
                await conn.execute(
                    select(AuditLogEntry).where(
                        AuditLogEntry.tenant_id == tenant_id,
                        AuditLogEntry.event_type == "pattern.matched",
                    )
                )
            )
            .scalars()
            .all()
        )
    assert len(audits) == len(parsed.matches)
