# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from services.dashboard_bff.app.main import create_app
from shared.db.session import tenant_session

from ._phase7b_helpers import fast_settings, issue_admin_token, seed_user

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def _seed_actor_with_history(
    admin_engine: AsyncEngine, tenant_id: str, actor_id: str
) -> None:
    async with admin_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO actor (id, tenant_id, external_id_hash, claimed_age_band) "
                "VALUES (:a, :t, :h, 'unknown')"
            ),
            {"a": actor_id, "t": tenant_id, "h": "f" * 64},
        )
        conversation_id = str(uuid.uuid4())
        await conn.execute(
            text(
                "INSERT INTO conversation (id, tenant_id, participant_actor_ids, "
                "started_at, last_message_at, channel_type) "
                "VALUES (:c, :t, ARRAY[:a], now(), now(), 'dm')"
            ),
            {"c": conversation_id, "t": tenant_id, "a": actor_id},
        )
        await conn.execute(
            text(
                "INSERT INTO event (id, tenant_id, conversation_id, actor_id, "
                "target_actor_ids, timestamp, type, content_hash, content_features, "
                "idempotency_key) VALUES (:e, :t, :c, :a, ARRAY[]::uuid[], now(), "
                "'message', :h, '{}'::jsonb, :k)"
            ),
            {
                "e": str(uuid.uuid4()),
                "t": tenant_id,
                "c": conversation_id,
                "a": actor_id,
                "h": "c" * 64,
                "k": "gdpr-test-1",
            },
        )
        await conn.execute(
            text(
                "INSERT INTO suspicion_profile (actor_id, tenant_id, current_score, "
                "tier, tier_entered_at, last_updated, last_decay_applied) "
                "VALUES (:a, :t, 55, 2, now(), now(), now())"
            ),
            {"a": actor_id, "t": tenant_id},
        )
        await conn.execute(
            text(
                "INSERT INTO audit_log_entry (id, tenant_id, actor_id, sequence, "
                "event_type, details, timestamp, previous_entry_hash, entry_hash) "
                "VALUES (:id, :t, :a, 999999, 'actor.test', '{}'::jsonb, now(), "
                ":prev, :hash)"
            ),
            {
                "id": str(uuid.uuid4()),
                "t": tenant_id,
                "a": actor_id,
                "prev": "0" * 64,
                "hash": "1" * 64,
            },
        )


async def test_gdpr_erasure_removes_actor_data_and_pseudonymises_audit(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tenant_id = str(uuid.uuid4())
    actor_id = str(uuid.uuid4())
    async with admin_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, "
                "data_retention_days, feature_flags) "
                "VALUES (:t, 'gdpr-test', 'free', ARRAY['EU']::varchar[], 90, '{}'::jsonb)"
            ),
            {"t": tenant_id},
        )
    await seed_user(admin_engine, tenant_id, role="admin")
    await _seed_actor_with_history(admin_engine, tenant_id, actor_id)

    settings = fast_settings()
    app = create_app(settings)
    token = issue_admin_token(settings=settings, tenant_id=uuid.UUID(tenant_id))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.post(
            "/dashboard/api/compliance/gdpr/erasure",
            json={
                "actor_id": actor_id,
                "requester_email": "data-subject@example.com",
                "request_reference": "gdpr-req-0001",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["events_removed"] >= 1
    assert body["suspicion_profile_removed"] is True
    assert body["audit_entries_pseudonymised"] >= 1

    async with tenant_session(uuid.UUID(tenant_id)) as session:
        actor_row = await session.execute(
            text("SELECT count(*) FROM actor WHERE id = :a"), {"a": actor_id}
        )
        assert actor_row.scalar_one() == 0
        event_row = await session.execute(
            text("SELECT count(*) FROM event WHERE actor_id = :a"), {"a": actor_id}
        )
        assert event_row.scalar_one() == 0
        audit_row = await session.execute(
            text(
                "SELECT count(*) FROM audit_log_entry " "WHERE tenant_id = :t AND actor_id IS NULL"
            ),
            {"t": tenant_id},
        )
        assert audit_row.scalar_one() >= 1


async def test_gdpr_erasure_rejects_unknown_actor(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tenant_id = str(uuid.uuid4())
    async with admin_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, "
                "data_retention_days, feature_flags) "
                "VALUES (:t, 'gdpr-test', 'free', ARRAY['EU']::varchar[], 90, '{}'::jsonb)"
            ),
            {"t": tenant_id},
        )
    await seed_user(admin_engine, tenant_id, role="admin")
    settings = fast_settings()
    app = create_app(settings)
    token = issue_admin_token(settings=settings, tenant_id=uuid.UUID(tenant_id))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.post(
            "/dashboard/api/compliance/gdpr/erasure",
            json={
                "actor_id": str(uuid.uuid4()),
                "requester_email": "data-subject@example.com",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 404
