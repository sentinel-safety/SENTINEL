# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import httpx
import pytest
from httpx import ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from services.dashboard_bff.app.main import create_app
from shared.db.session import tenant_session
from shared.honeypot.evidence import build_evidence_package
from shared.honeypot.repository import persist_evidence_package
from tests.integration._phase7b_helpers import fast_settings, issue_admin_token

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def test_toggle_honeypot_requires_admin_and_legal_ack(
    clean_tables: None, admin_engine: AsyncEngine
) -> None:
    tenant_id = uuid4()
    async with admin_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, data_retention_days) VALUES (:t, 'x', 'free', 30)"
            ),
            {"t": str(tenant_id)},
        )
    settings = fast_settings()
    token = issue_admin_token(tenant_id=tenant_id, settings=settings)
    app = create_app(settings)
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        r = await client.put(
            "/dashboard/api/tenant/honeypot",
            json={"honeypot_enabled": True, "legal_review_acknowledged": False},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r.status_code == 400
    assert "legal_review_acknowledged" in r.text


async def test_toggle_honeypot_enables_when_legal_ack_true(
    clean_tables: None, admin_engine: AsyncEngine
) -> None:
    tenant_id = uuid4()
    async with admin_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, data_retention_days) VALUES (:t, 'x', 'free', 30)"
            ),
            {"t": str(tenant_id)},
        )
    settings = fast_settings()
    token = issue_admin_token(tenant_id=tenant_id, settings=settings)
    app = create_app(settings)
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        r = await client.put(
            "/dashboard/api/tenant/honeypot",
            json={"honeypot_enabled": True, "legal_review_acknowledged": True},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r.status_code == 200
    async with tenant_session(tenant_id) as s:
        row = (
            await s.execute(
                text("SELECT feature_flags FROM tenant WHERE id=:t"), {"t": str(tenant_id)}
            )
        ).one()
    assert row.feature_flags.get("honeypot_enabled") is True
    assert row.feature_flags.get("honeypot_legal_review_acknowledged") is True


async def test_list_evidence_admin_only(clean_tables: None, admin_engine: AsyncEngine) -> None:
    tenant_id = uuid4()
    actor_id = uuid4()
    async with admin_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, data_retention_days) VALUES (:t, 'x', 'free', 30)"
            ),
            {"t": str(tenant_id)},
        )
        await conn.execute(
            text(
                "INSERT INTO actor (id, tenant_id, external_id_hash, claimed_age_band) "
                "VALUES (:a, :t, :h, 'unknown')"
            ),
            {"a": str(actor_id), "t": str(tenant_id), "h": "7" * 64},
        )
    pkg = build_evidence_package(
        tenant_id=tenant_id,
        actor_id=actor_id,
        persona_id="emma",
        activated_at=datetime.now(UTC),
        deactivated_at=datetime.now(UTC),
        conversation_excerpts=("actor:hi",),
        pattern_matches=(),
        reasoning_snapshot={},
        activation_audit_trail=(),
    )
    async with tenant_session(tenant_id) as s:
        await persist_evidence_package(s, package=pkg)
    settings = fast_settings()
    token = issue_admin_token(tenant_id=tenant_id, settings=settings)
    app = create_app(settings)
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        r = await client.get(
            "/dashboard/api/honeypot/evidence",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r.status_code == 200
    body = r.json()
    assert len(body["evidence"]) == 1
    assert body["evidence"][0]["persona_id"] == "emma"
