# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from services.dashboard_bff.app.main import create_app
from shared.db.session import tenant_session
from shared.explainability.reasoning_repository import insert_reasoning
from shared.schemas.enums import ResponseTier
from shared.schemas.reasoning import PrimaryDriver, Reasoning
from tests.integration._phase7b_helpers import (
    auth_headers,
    fast_settings,
    make_access_token,
    seed_actor,
    seed_suspicion_profile,
    seed_tenant,
    seed_user,
)

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def _seed_event(
    admin_engine: AsyncEngine,
    *,
    tenant_id: str,
    actor_id: str,
    event_id: str,
    conversation_id: str,
) -> None:
    async with admin_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO conversation "
                "(id, tenant_id, participant_actor_ids, started_at, last_message_at, channel_type) "
                "VALUES (:c, :t, :p, now(), now(), 'dm')"
            ),
            {"c": conversation_id, "t": tenant_id, "p": [actor_id]},
        )
        await conn.execute(
            text(
                "INSERT INTO event "
                "(id, tenant_id, conversation_id, actor_id, target_actor_ids, timestamp, "
                "type, content_hash, content_features, idempotency_key) "
                "VALUES (:e, :t, :c, :a, '{}', now(), 'message', :h, '{}'::jsonb, :i)"
            ),
            {
                "e": event_id,
                "t": tenant_id,
                "c": conversation_id,
                "a": actor_id,
                "h": "a" * 64,
                "i": f"idem-{event_id}",
            },
        )


async def test_actor_detail(admin_engine: AsyncEngine, clean_tables: None) -> None:
    tid = str(uuid.uuid4())
    aid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    await seed_actor(admin_engine, tid, aid, age_band="13_15")
    await seed_suspicion_profile(admin_engine, tid, aid, tier=2, score=40)
    uid = await seed_user(admin_engine, tid, role="admin")
    token = make_access_token(uid, uuid.UUID(tid), role="admin")
    app = create_app(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.get(f"/dashboard/api/actors/{aid}", headers=auth_headers(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["actor_id"] == aid
    assert body["claimed_age_band"] == "13_15"
    assert body["current_score"] == 40
    assert body["tier"] == 2


async def test_actor_events(admin_engine: AsyncEngine, clean_tables: None) -> None:
    tid = str(uuid.uuid4())
    aid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    await seed_actor(admin_engine, tid, aid)
    eid = str(uuid.uuid4())
    cid = str(uuid.uuid4())
    await _seed_event(admin_engine, tenant_id=tid, actor_id=aid, event_id=eid, conversation_id=cid)
    uid = await seed_user(admin_engine, tid, role="mod")
    token = make_access_token(uid, uuid.UUID(tid), role="mod")
    app = create_app(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.get(
            f"/dashboard/api/actors/{aid}/events?limit=10", headers=auth_headers(token)
        )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["events"]) == 1
    assert body["events"][0]["id"] == eid


async def test_actor_reasoning(admin_engine: AsyncEngine, clean_tables: None) -> None:
    tid = str(uuid.uuid4())
    aid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    await seed_actor(admin_engine, tid, aid)
    async with tenant_session(uuid.UUID(tid)) as session:
        await insert_reasoning(
            session,
            reasoning=Reasoning(
                actor_id=uuid.UUID(aid),
                tenant_id=uuid.UUID(tid),
                score_change=10,
                new_score=40,
                new_tier=ResponseTier.WATCH,
                primary_drivers=(
                    PrimaryDriver(
                        pattern="p",
                        pattern_id="p",
                        confidence=0.7,
                        evidence="e",
                    ),
                ),
                generated_at=datetime.now(UTC),
            ),
            event_id=None,
        )
    uid = await seed_user(admin_engine, tid, role="admin")
    token = make_access_token(uid, uuid.UUID(tid), role="admin")
    app = create_app(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.get(
            f"/dashboard/api/actors/{aid}/reasoning", headers=auth_headers(token)
        )
    assert resp.status_code == 200
    assert len(resp.json()["reasoning"]) == 1


async def test_actor_detail_denies_viewer(admin_engine: AsyncEngine, clean_tables: None) -> None:
    tid = str(uuid.uuid4())
    aid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    await seed_actor(admin_engine, tid, aid)
    uid = await seed_user(admin_engine, tid, role="viewer")
    token = make_access_token(uid, uuid.UUID(tid), role="viewer")
    app = create_app(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.get(f"/dashboard/api/actors/{aid}", headers=auth_headers(token))
    assert resp.status_code == 403
