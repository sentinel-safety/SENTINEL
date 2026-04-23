# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from shared.memory.repository import get_actor_memory
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
            {"a": str(actor_id), "t": str(tenant_id), "h": "f" * 64},
        )


async def _insert_event(  # type: ignore[no-untyped-def]
    engine, tenant_id, actor_id, conv_id, target_hashes, content_features, timestamp
) -> None:
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO conversation (id, tenant_id, participant_actor_ids, started_at, "
                "last_message_at, channel_type) VALUES (:c, :t, :p, :s, :l, 'dm') ON CONFLICT DO NOTHING"
            ),
            {
                "c": str(conv_id),
                "t": str(tenant_id),
                "p": [str(actor_id)],
                "s": timestamp,
                "l": timestamp,
            },
        )
        await conn.execute(
            text(
                "INSERT INTO event (id, tenant_id, conversation_id, actor_id, target_actor_ids, "
                "timestamp, type, content_hash, content_features, idempotency_key) "
                "VALUES (:i, :t, :c, :a, :tg, :ts, 'message', :h, CAST(:cf AS jsonb), :k)"
            ),
            {
                "i": str(uuid4()),
                "t": str(tenant_id),
                "c": str(conv_id),
                "a": str(actor_id),
                "tg": list(target_hashes),
                "ts": timestamp,
                "h": "1" * 64,
                "cf": '{"minor_recipient": true}' if content_features else "{}",
                "k": str(uuid4()),
            },
        )


async def _insert_pattern_match(  # type: ignore[no-untyped-def]
    engine, tenant_id, actor_id, pattern_id, stage, matched_at
) -> None:
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO pattern_match (id, tenant_id, actor_id, pattern_id, pattern_version, "
                "confidence, event_ids, matched_at, evidence_summary, stage) "
                "VALUES (:i, :t, :a, :p, 'v1', 0.9, :ev, :m, 'x', :s)"
            ),
            {
                "i": str(uuid4()),
                "t": str(tenant_id),
                "a": str(actor_id),
                "p": pattern_id,
                "ev": [str(uuid4())],
                "m": matched_at,
                "s": stage,
            },
        )


async def test_get_actor_memory_aggregates_events_and_matches(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tenant_id = uuid4()
    actor_id = uuid4()
    now = datetime.now(UTC)
    await _seed(admin_engine, tenant_id, actor_id)

    conv_1 = uuid4()
    conv_2 = uuid4()
    target_a = str(uuid4())
    target_b = str(uuid4())
    await _insert_event(
        admin_engine, tenant_id, actor_id, conv_1, [target_a], True, now - timedelta(days=5)
    )
    await _insert_event(
        admin_engine, tenant_id, actor_id, conv_2, [target_b], True, now - timedelta(days=2)
    )
    await _insert_pattern_match(
        admin_engine, tenant_id, actor_id, "secrecy_request", None, now - timedelta(days=4)
    )
    await _insert_pattern_match(
        admin_engine, tenant_id, actor_id, "isolation", "isolation", now - timedelta(days=1)
    )

    factory = async_sessionmaker(bind=admin_engine, expire_on_commit=False, autoflush=False)
    async with factory() as s, s.begin():
        await s.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(tenant_id)})
        view = await get_actor_memory(
            s, tenant_id=tenant_id, actor_id=actor_id, now=now, lookback=timedelta(days=21)
        )
    assert view.distinct_conversations_last_window == 2
    assert view.distinct_minor_targets_last_window == 2
    assert view.total_events_last_window == 2
    assert view.pattern_counts_by_kind[SignalKind.SECRECY_REQUEST] == 1
    assert view.pattern_counts_by_kind[SignalKind.ISOLATION] == 1
    assert "isolation" in view.stages_observed
    assert view.first_contact_at is not None
    assert view.most_recent_contact_at is not None
    assert view.first_contact_at <= view.most_recent_contact_at


async def test_get_actor_memory_returns_empty_when_no_data(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tenant_id = uuid4()
    actor_id = uuid4()
    now = datetime.now(UTC)
    await _seed(admin_engine, tenant_id, actor_id)

    factory = async_sessionmaker(bind=admin_engine, expire_on_commit=False, autoflush=False)
    async with factory() as s, s.begin():
        await s.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(tenant_id)})
        view = await get_actor_memory(
            s, tenant_id=tenant_id, actor_id=actor_id, now=now, lookback=timedelta(days=21)
        )
    assert view.distinct_conversations_last_window == 0
    assert view.distinct_minor_targets_last_window == 0
    assert view.total_events_last_window == 0
    assert view.pattern_counts_by_kind == {}
    assert view.stages_observed == ()
    assert view.first_contact_at is None
    assert view.most_recent_contact_at is None
