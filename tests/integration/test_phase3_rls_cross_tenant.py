# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from services.patterns.app.repositories.pattern_match_writes import persist_pattern_matches
from shared.db.models import PatternMatch as PatternMatchRow
from shared.patterns.matches import DetectionMode, PatternMatch
from shared.scoring.signals import SignalKind

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def _seed(engine: AsyncEngine, tenant_id, actor_id, hash_char) -> None:  # type: ignore[no-untyped-def]
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
            {"a": str(actor_id), "t": str(tenant_id), "h": hash_char * 64},
        )


async def test_tenant_a_cannot_see_tenant_b_pattern_matches(
    admin_engine: AsyncEngine, app_engine: AsyncEngine, clean_tables: None
) -> None:
    tenant_a = uuid4()
    actor_a = uuid4()
    tenant_b = uuid4()
    actor_b = uuid4()
    await _seed(admin_engine, tenant_a, actor_a, "8")
    await _seed(admin_engine, tenant_b, actor_b, "9")

    factory = async_sessionmaker(bind=app_engine, expire_on_commit=False, autoflush=False)
    match_sample = PatternMatch(
        pattern_name="secrecy_request",
        signal_kind=SignalKind.SECRECY_REQUEST,
        confidence=1.0,
        evidence_excerpts=("sample",),
        detection_mode=DetectionMode.RULE,
        prompt_version=None,
    )
    async with factory() as s, s.begin():
        await s.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(tenant_b)})
        await persist_pattern_matches(
            s,
            tenant_id=tenant_b,
            actor_id=actor_b,
            event_id=uuid4(),
            matches=(match_sample,),
            matched_at=datetime.now(UTC),
        )

    async with factory() as s, s.begin():
        await s.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(tenant_a)})
        rows = (await s.execute(select(PatternMatchRow))).scalars().all()
    assert len(rows) == 0
