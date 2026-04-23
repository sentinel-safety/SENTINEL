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


async def test_get_action_config_auto_creates(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    uid = await seed_user(admin_engine, tid, role="admin")
    token = make_access_token(uid, uuid.UUID(tid), role="admin")
    app = create_app(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.get("/dashboard/api/tenant/action-config", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["mode"] == "advisory"


async def test_put_action_config_updates_mode(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    uid = await seed_user(admin_engine, tid, role="admin")
    token = make_access_token(uid, uuid.UUID(tid), role="admin")
    app = create_app(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        await client.get("/dashboard/api/tenant/action-config", headers=auth_headers(token))
        resp = await client.put(
            "/dashboard/api/tenant/action-config",
            headers=auth_headers(token),
            json={"mode": "auto_enforce", "action_overrides": {}},
        )
    assert resp.status_code == 200
    assert resp.json()["mode"] == "auto_enforce"
