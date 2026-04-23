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


async def _seed_conv_with_event(
    admin_engine: AsyncEngine, *, tenant_id: str, actor_id: str
) -> tuple[str, str]:
    cid = str(uuid.uuid4())
    eid = str(uuid.uuid4())
    now = datetime.now(UTC)
    async with admin_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO conversation "
                "(id, tenant_id, participant_actor_ids, started_at, last_message_at, channel_type) "
                "VALUES (:c, :t, :p, :now, :now, 'dm')"
            ),
            {"c": cid, "t": tenant_id, "p": [actor_id], "now": now},
        )
        await conn.execute(
            text(
                "INSERT INTO event "
                "(id, tenant_id, conversation_id, actor_id, target_actor_ids, timestamp, "
                "type, content_hash, content_features, idempotency_key) "
                "VALUES (:e, :t, :c, :a, '{}', :now, 'message', :h, '{}'::jsonb, :i)"
            ),
            {
                "e": eid,
                "t": tenant_id,
                "c": cid,
                "a": actor_id,
                "now": now,
                "h": "a" * 64,
                "i": f"idem-{eid}",
            },
        )
    return cid, eid


async def test_investigation_returns_messages_and_writes_audit(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tid = str(uuid.uuid4())
    aid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    await seed_actor(admin_engine, tid, aid)
    await seed_suspicion_profile(admin_engine, tid, aid, tier=4, score=80)
    cid, _ = await _seed_conv_with_event(admin_engine, tenant_id=tid, actor_id=aid)
    uid = await seed_user(admin_engine, tid, role="mod")
    token = make_access_token(uid, uuid.UUID(tid), role="mod")
    app = create_app(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.get(
            f"/dashboard/api/conversations/{cid}/messages",
            headers={**auth_headers(token), "X-Investigation-Reason": "NCMEC-2026-0001"},
        )
    assert resp.status_code == 200
    assert len(resp.json()["messages"]) == 1
    async with admin_engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT event_type, details FROM audit_log_entry "
                "WHERE tenant_id=:t AND event_type='investigation.content_access'"
            ),
            {"t": tid},
        )
        row = result.one()
    assert row.details["break_glass"] is True
    assert row.details["reason"] == "NCMEC-2026-0001"


async def test_investigation_rejects_empty_reason(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tid = str(uuid.uuid4())
    aid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    await seed_actor(admin_engine, tid, aid)
    await seed_suspicion_profile(admin_engine, tid, aid, tier=4, score=80)
    cid, _ = await _seed_conv_with_event(admin_engine, tenant_id=tid, actor_id=aid)
    uid = await seed_user(admin_engine, tid, role="mod")
    token = make_access_token(uid, uuid.UUID(tid), role="mod")
    app = create_app(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.get(
            f"/dashboard/api/conversations/{cid}/messages",
            headers={**auth_headers(token), "X-Investigation-Reason": "  "},
        )
    assert resp.status_code == 400


async def test_investigation_forbidden_when_no_participant_at_tier3(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tid = str(uuid.uuid4())
    aid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    await seed_actor(admin_engine, tid, aid)
    await seed_suspicion_profile(admin_engine, tid, aid, tier=1, score=15)
    cid, _ = await _seed_conv_with_event(admin_engine, tenant_id=tid, actor_id=aid)
    uid = await seed_user(admin_engine, tid, role="mod")
    token = make_access_token(uid, uuid.UUID(tid), role="mod")
    app = create_app(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.get(
            f"/dashboard/api/conversations/{cid}/messages",
            headers={**auth_headers(token), "X-Investigation-Reason": "routine"},
        )
    assert resp.status_code == 403


async def test_investigation_denies_auditor_role(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tid = str(uuid.uuid4())
    aid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    await seed_actor(admin_engine, tid, aid)
    await seed_suspicion_profile(admin_engine, tid, aid, tier=4, score=80)
    cid, _ = await _seed_conv_with_event(admin_engine, tenant_id=tid, actor_id=aid)
    uid = await seed_user(admin_engine, tid, role="auditor")
    token = make_access_token(uid, uuid.UUID(tid), role="auditor")
    app = create_app(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.get(
            f"/dashboard/api/conversations/{cid}/messages",
            headers={**auth_headers(token), "X-Investigation-Reason": "r"},
        )
    assert resp.status_code == 403
