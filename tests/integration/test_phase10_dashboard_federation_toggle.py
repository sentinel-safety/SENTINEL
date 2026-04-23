# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import uuid4

import httpx
import pytest
from httpx import ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from services.dashboard_bff.app.main import create_app
from tests.integration._phase7b_helpers import fast_settings, issue_admin_token

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def _seed(engine: AsyncEngine, tenant_id: object) -> None:
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, "
                "data_retention_days, feature_flags) "
                f"VALUES ('{tenant_id}', 'fed-bff', 'free', '{{}}', 30, '{{}}'::jsonb)"
                " ON CONFLICT DO NOTHING"
            )
        )


async def test_put_federation_rejects_when_not_acknowledged(
    clean_tables: None, admin_engine: AsyncEngine
) -> None:
    tenant_id = uuid4()
    await _seed(admin_engine, tenant_id)
    settings = fast_settings()
    token = issue_admin_token(tenant_id=tenant_id, settings=settings)
    app = create_app(settings)
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.put(
            "/dashboard/api/tenant/federation",
            json={
                "enabled": True,
                "publish": True,
                "subscribe": False,
                "jurisdictions_filter": [],
                "federation_acknowledgment": False,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r.status_code == 400
    assert "federation_acknowledgment" in r.text


async def test_put_federation_enables_with_ack(
    clean_tables: None, admin_engine: AsyncEngine
) -> None:
    tenant_id = uuid4()
    await _seed(admin_engine, tenant_id)
    settings = fast_settings()
    token = issue_admin_token(tenant_id=tenant_id, settings=settings)
    app = create_app(settings)
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.put(
            "/dashboard/api/tenant/federation",
            json={
                "enabled": True,
                "publish": True,
                "subscribe": False,
                "jurisdictions_filter": ["US"],
                "federation_acknowledgment": True,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r.status_code == 200
    data = r.json()
    assert data["enabled"] is True
    assert data["publish"] is True
    assert "US" in data["jurisdictions_filter"]


async def test_get_federation_settings(clean_tables: None, admin_engine: AsyncEngine) -> None:
    tenant_id = uuid4()
    await _seed(admin_engine, tenant_id)
    settings = fast_settings()
    token = issue_admin_token(tenant_id=tenant_id, settings=settings)
    app = create_app(settings)
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        await c.put(
            "/dashboard/api/tenant/federation",
            json={
                "enabled": True,
                "publish": False,
                "subscribe": True,
                "jurisdictions_filter": ["EU"],
                "federation_acknowledgment": True,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        r = await c.get(
            "/dashboard/api/tenant/federation",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r.status_code == 200
    data = r.json()
    assert data["enabled"] is True
    assert data["subscribe"] is True
    assert "EU" in data["jurisdictions_filter"]


async def test_put_disabled_without_ack_allowed(
    clean_tables: None, admin_engine: AsyncEngine
) -> None:
    tenant_id = uuid4()
    await _seed(admin_engine, tenant_id)
    settings = fast_settings()
    token = issue_admin_token(tenant_id=tenant_id, settings=settings)
    app = create_app(settings)
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.put(
            "/dashboard/api/tenant/federation",
            json={
                "enabled": False,
                "publish": False,
                "subscribe": False,
                "jurisdictions_filter": [],
                "federation_acknowledgment": False,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r.status_code == 200
