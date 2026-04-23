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

from services.scoring.app.main import create_app
from shared.audit.chain import verify_chain
from shared.config import Settings
from shared.db.session import tenant_session
from shared.schemas.enums import EventType

pytestmark = pytest.mark.integration


async def _seed(
    engine: AsyncEngine,
    tenant_id: object,
    actor_id: object,
    conversation_id: object,
    event_id: object,
) -> None:
    now = datetime.now(UTC)
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, "
                "data_retention_days, feature_flags) "
                "VALUES (:tid, 'acme', 'free', '{}', 30, '{}'::jsonb) ON CONFLICT DO NOTHING"
            ),
            {"tid": str(tenant_id)},
        )
        await conn.execute(
            text(
                "INSERT INTO actor (id, tenant_id, external_id_hash, claimed_age_band) "
                "VALUES (:aid, :tid, :h, 'under_13') ON CONFLICT DO NOTHING"
            ),
            {"aid": str(actor_id), "tid": str(tenant_id), "h": "a" * 64},
        )
        await conn.execute(
            text(
                "INSERT INTO conversation (id, tenant_id, participant_actor_ids, "
                "started_at, last_message_at, channel_type) "
                "VALUES (:cid, :tid, '{}', :now, :now, 'dm') ON CONFLICT DO NOTHING"
            ),
            {"cid": str(conversation_id), "tid": str(tenant_id), "now": now},
        )
        await conn.execute(
            text(
                "INSERT INTO event (id, tenant_id, conversation_id, actor_id, "
                "target_actor_ids, timestamp, type, content_hash, idempotency_key) "
                "VALUES (:eid, :tid, :cid, :aid, '{}', :now, 'message', :hash, :ikey) "
                "ON CONFLICT DO NOTHING"
            ),
            {
                "eid": str(event_id),
                "tid": str(tenant_id),
                "cid": str(conversation_id),
                "aid": str(actor_id),
                "now": now,
                "hash": "a" * 64,
                "ikey": str(event_id),
            },
        )


async def test_score_route_persists_profile_and_writes_audit(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tenant_id = uuid4()
    actor_id = uuid4()
    conversation_id = uuid4()
    event_id = uuid4()
    await _seed(admin_engine, tenant_id, actor_id, conversation_id, event_id)

    app = create_app(Settings(env="test"))
    body = {
        "event": {
            "id": str(event_id),
            "tenant_id": str(tenant_id),
            "conversation_id": str(conversation_id),
            "actor_id": str(actor_id),
            "target_actor_ids": [],
            "timestamp": datetime.now(UTC).isoformat(),
            "type": EventType.MESSAGE.value,
            "content_hash": "a" * 64,
        },
        "signals": [
            {"kind": "isolation", "confidence": 1.0, "evidence": "test"},
        ],
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/internal/score", json=body)
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["previous_score"] == 5
    assert payload["current_score"] == 17
    assert payload["tier"] == "trusted"

    async with tenant_session(tenant_id) as session:
        count = await verify_chain(session, tenant_id)
    assert count == 2


async def test_score_route_writes_tier_changed_when_tier_crosses(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tenant_id = uuid4()
    actor_id = uuid4()
    conversation_id = uuid4()
    event_id = uuid4()
    await _seed(admin_engine, tenant_id, actor_id, conversation_id, event_id)

    app = create_app(Settings(env="test"))
    body = {
        "event": {
            "id": str(event_id),
            "tenant_id": str(tenant_id),
            "conversation_id": str(conversation_id),
            "actor_id": str(actor_id),
            "target_actor_ids": [],
            "timestamp": datetime.now(UTC).isoformat(),
            "type": EventType.MESSAGE.value,
            "content_hash": "a" * 64,
        },
        "signals": [
            {"kind": "sexual_escalation", "confidence": 1.0, "evidence": "test"},
            {"kind": "secrecy_request", "confidence": 1.0, "evidence": "test"},
        ],
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/internal/score", json=body)
    assert resp.status_code == 200

    async with tenant_session(tenant_id) as session:
        count = await verify_chain(session, tenant_id)
    assert count == 3  # event.scored + score.changed + tier.changed
