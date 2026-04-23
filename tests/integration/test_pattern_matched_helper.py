# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from shared.audit.events import record_pattern_matched

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
            {"a": str(actor_id), "t": str(tenant_id), "h": "e" * 64},
        )


async def test_record_pattern_matched_writes_audit_entry(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tenant_id = uuid4()
    actor_id = uuid4()
    event_id = uuid4()
    match_id = uuid4()
    await _seed(admin_engine, tenant_id, actor_id)

    factory = async_sessionmaker(bind=admin_engine, expire_on_commit=False, autoflush=False)
    async with factory() as s, s.begin():
        await s.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(tenant_id)})
        entry = await record_pattern_matched(
            s,
            tenant_id=tenant_id,
            actor_id=actor_id,
            pattern_name="secrecy_request",
            confidence=0.95,
            event_id=event_id,
            pattern_match_id=match_id,
            timestamp=datetime.now(UTC),
        )
    assert entry.event_type == "pattern.matched"
    assert entry.details["pattern_name"] == "secrecy_request"
    assert entry.details["confidence"] == 0.95
    assert entry.details["event_id"] == str(event_id)
    assert entry.details["pattern_match_id"] == str(match_id)
