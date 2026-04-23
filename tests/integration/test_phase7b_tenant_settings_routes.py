# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine

from services.dashboard_bff.app.main import create_app
from tests.integration._phase7b_helpers import (
    auth_headers,
    fast_settings,
    make_access_token,
    seed_tenant,
    seed_user,
)

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def test_get_tenant_settings(admin_engine: AsyncEngine, clean_tables: None) -> None:
    tid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    uid = await seed_user(admin_engine, tid, role="admin")
    token = make_access_token(uid, uuid.UUID(tid), role="admin")
    app = create_app(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.get("/dashboard/api/tenant/settings", headers=auth_headers(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "acme"
    assert body["data_retention_days"] == 30


async def test_put_tenant_settings_updates_name_and_retention(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    uid = await seed_user(admin_engine, tid, role="admin")
    token = make_access_token(uid, uuid.UUID(tid), role="admin")
    app = create_app(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.put(
            "/dashboard/api/tenant/settings",
            headers=auth_headers(token),
            json={
                "name": "acme-prime",
                "tier": "pro",
                "compliance_jurisdictions": ["US", "EU"],
                "data_retention_days": 180,
            },
        )
        assert resp.status_code == 200
        resp2 = await client.get("/dashboard/api/tenant/settings", headers=auth_headers(token))
    body = resp2.json()
    assert body["name"] == "acme-prime"
    assert body["data_retention_days"] == 180


async def test_tenant_settings_denies_mod(admin_engine: AsyncEngine, clean_tables: None) -> None:
    tid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    uid = await seed_user(admin_engine, tid, role="mod")
    token = make_access_token(uid, uuid.UUID(tid), role="mod")
    app = create_app(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.get("/dashboard/api/tenant/settings", headers=auth_headers(token))
    assert resp.status_code == 403
