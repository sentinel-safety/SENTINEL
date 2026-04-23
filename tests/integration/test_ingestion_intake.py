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

from services.ingestion.app.intake import IntakeOutcome, intake_event
from shared.contracts.ingest import IngestEventRequest
from shared.db.session import tenant_session
from shared.schemas.enums import EventType

pytestmark = pytest.mark.integration


async def _seed_tenant(engine: AsyncEngine, tenant_id: UUID) -> None:
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, "
                "data_retention_days, feature_flags) "
                "VALUES (:tid, 'acme', 'free', '{}', 30, '{}'::jsonb) ON CONFLICT DO NOTHING"
            ),
            {"tid": str(tenant_id)},
        )


def _request(tenant_id: UUID, idem_key: str) -> IngestEventRequest:
    return IngestEventRequest(
        idempotency_key=idem_key,
        tenant_id=tenant_id,
        conversation_id=uuid4(),
        actor_external_id_hash="a" * 64,
        target_actor_external_id_hashes=("b" * 64,),
        event_type=EventType.MESSAGE,
        timestamp=datetime.now(UTC),
        content="don't tell your parents",
    )


async def test_intake_creates_event_and_upserts_actors(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tenant_id = uuid4()
    await _seed_tenant(admin_engine, tenant_id)

    async with tenant_session(tenant_id) as session:
        outcome = await intake_event(session, _request(tenant_id, "key-1"))

    assert isinstance(outcome, IntakeOutcome)
    assert outcome.deduplicated is False
    assert outcome.event.tenant_id == tenant_id


async def test_intake_is_idempotent_on_repeat_key(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tenant_id = uuid4()
    await _seed_tenant(admin_engine, tenant_id)

    async with tenant_session(tenant_id) as session:
        first = await intake_event(session, _request(tenant_id, "key-2"))
    async with tenant_session(tenant_id) as session:
        second = await intake_event(session, _request(tenant_id, "key-2"))

    assert second.deduplicated is True
    assert second.event.id == first.event.id
