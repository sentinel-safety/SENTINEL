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
            {"a": str(actor_id), "t": str(tenant_id), "h": "d" * 64},
        )


async def test_persist_pattern_matches_writes_rows_and_returns_ids(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tenant_id = uuid4()
    actor_id = uuid4()
    event_id = uuid4()
    await _seed(admin_engine, tenant_id, actor_id)

    rule = PatternMatch(
        pattern_name="secrecy_request",
        signal_kind=SignalKind.SECRECY_REQUEST,
        confidence=1.0,
        evidence_excerpts=("don't tell",),
        detection_mode=DetectionMode.RULE,
        prompt_version=None,
    )
    llm = PatternMatch(
        pattern_name="isolation",
        signal_kind=SignalKind.ISOLATION,
        confidence=0.8,
        evidence_excerpts=("only i understand you",),
        detection_mode=DetectionMode.LLM,
        prompt_version="v1",
    )
    now = datetime.now(UTC)

    factory = async_sessionmaker(bind=admin_engine, expire_on_commit=False, autoflush=False)
    async with factory() as s, s.begin():
        await s.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(tenant_id)})
        ids = await persist_pattern_matches(
            s,
            tenant_id=tenant_id,
            actor_id=actor_id,
            event_id=event_id,
            matches=(rule, llm),
            matched_at=now,
        )
    assert len(ids) == 2

    async with factory() as s, s.begin():
        await s.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(tenant_id)})
        rows = (
            (await s.execute(select(PatternMatchRow).where(PatternMatchRow.actor_id == actor_id)))
            .scalars()
            .all()
        )
    by_pid = {r.pattern_id: r for r in rows}
    assert by_pid["secrecy_request"].pattern_version == "v1"
    assert by_pid["secrecy_request"].stage is None
    assert by_pid["isolation"].pattern_version == "v1"
    assert by_pid["isolation"].stage == "isolation"
    assert by_pid["secrecy_request"].event_ids == [str(event_id)]
    assert by_pid["secrecy_request"].evidence_summary == "don't tell"


async def test_persist_pattern_matches_empty_is_noop(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tenant_id = uuid4()
    actor_id = uuid4()
    await _seed(admin_engine, tenant_id, actor_id)
    factory = async_sessionmaker(bind=admin_engine, expire_on_commit=False, autoflush=False)
    async with factory() as s, s.begin():
        await s.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(tenant_id)})
        ids = await persist_pattern_matches(
            s,
            tenant_id=tenant_id,
            actor_id=actor_id,
            event_id=uuid4(),
            matches=(),
            matched_at=datetime.now(UTC),
        )
    assert ids == ()
