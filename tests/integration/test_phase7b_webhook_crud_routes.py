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


async def test_create_then_list_then_delete_webhook(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    uid = await seed_user(admin_engine, tid, role="admin")
    token = make_access_token(uid, uuid.UUID(tid), role="admin")
    app = create_app(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        create = await client.post(
            "/dashboard/api/tenant/webhooks",
            headers=auth_headers(token),
            json={"url": "https://example.com/wh", "events": ["tier_changed"]},
        )
        assert create.status_code == 201
        secret = create.json()["secret"]
        assert len(secret) >= 32
        wh_id = create.json()["webhook"]["id"]
        listed = await client.get("/dashboard/api/tenant/webhooks", headers=auth_headers(token))
        assert listed.status_code == 200
        assert any(w["id"] == wh_id for w in listed.json()["webhooks"])
        deleted = await client.delete(
            f"/dashboard/api/tenant/webhooks/{wh_id}", headers=auth_headers(token)
        )
        assert deleted.status_code == 204
        listed_after = await client.get(
            "/dashboard/api/tenant/webhooks", headers=auth_headers(token)
        )
        assert all(w["id"] != wh_id for w in listed_after.json()["webhooks"])


async def test_webhook_crud_denies_mod(admin_engine: AsyncEngine, clean_tables: None) -> None:
    tid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    uid = await seed_user(admin_engine, tid, role="mod")
    token = make_access_token(uid, uuid.UUID(tid), role="mod")
    app = create_app(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.get("/dashboard/api/tenant/webhooks", headers=auth_headers(token))
    assert resp.status_code == 403
