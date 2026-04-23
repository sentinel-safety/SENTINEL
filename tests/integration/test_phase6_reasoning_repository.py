# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from shared.db.session import tenant_session
from shared.explainability.reasoning_repository import (
    get_reasoning_for_event,
    insert_reasoning,
    list_reasoning_for_actor,
)
from shared.schemas.enums import ResponseTier
from shared.schemas.reasoning import PrimaryDriver, Reasoning

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


def _reasoning(tenant: uuid.UUID, actor: uuid.UUID) -> Reasoning:
    return Reasoning(
        actor_id=actor,
        tenant_id=tenant,
        score_change=15,
        new_score=55,
        new_tier=ResponseTier.ACTIVE_MONITOR,
        primary_drivers=(
            PrimaryDriver(
                pattern="Platform Migration Request",
                pattern_id="platform_migration",
                confidence=0.9,
                evidence="Actor asked to move to Telegram.",
            ),
        ),
        generated_at=datetime.now(UTC),
    )


async def test_insert_and_list_for_actor(admin_engine: AsyncEngine, clean_tables: None) -> None:
    tid = str(uuid.uuid4())
    aid = str(uuid.uuid4())
    await _seed(admin_engine, tid, aid)
    async with tenant_session(uuid.UUID(tid)) as session:
        await insert_reasoning(
            session,
            reasoning=_reasoning(uuid.UUID(tid), uuid.UUID(aid)),
            event_id=None,
        )
    async with tenant_session(uuid.UUID(tid)) as session:
        rows = await list_reasoning_for_actor(
            session, tenant_id=uuid.UUID(tid), actor_id=uuid.UUID(aid), limit=5
        )
    assert len(rows) == 1
    assert rows[0].new_score == 55
    assert rows[0].primary_drivers[0].pattern_id == "platform_migration"


async def test_fetch_by_event_id(admin_engine: AsyncEngine, clean_tables: None) -> None:
    tid = str(uuid.uuid4())
    aid = str(uuid.uuid4())
    await _seed(admin_engine, tid, aid)
    event_id = uuid.uuid4()
    async with admin_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO conversation (id, tenant_id, participant_actor_ids, "
                "started_at, last_message_at, channel_type) VALUES "
                "(:c, :t, ARRAY[:a], now(), now(), 'dm')"
            ),
            {"c": str(uuid.uuid4()), "t": tid, "a": aid},
        )
    async with admin_engine.begin() as conn:
        conv = (
            await conn.execute(
                text("SELECT id FROM conversation WHERE tenant_id = :t LIMIT 1"),
                {"t": tid},
            )
        ).scalar_one()
        await conn.execute(
            text(
                "INSERT INTO event (id, tenant_id, conversation_id, actor_id, target_actor_ids, "
                "timestamp, type, content_hash, content_features, idempotency_key) "
                "VALUES (:e, :t, :c, :a, '{}', now(), 'message', :h, '{}'::jsonb, 'k')"
            ),
            {"e": str(event_id), "t": tid, "c": str(conv), "a": aid, "h": "c" * 64},
        )
    async with tenant_session(uuid.UUID(tid)) as session:
        await insert_reasoning(
            session,
            reasoning=_reasoning(uuid.UUID(tid), uuid.UUID(aid)),
            event_id=event_id,
        )
    async with tenant_session(uuid.UUID(tid)) as session:
        fetched = await get_reasoning_for_event(
            session, tenant_id=uuid.UUID(tid), event_id=event_id
        )
    assert fetched is not None
    assert fetched.new_score == 55
