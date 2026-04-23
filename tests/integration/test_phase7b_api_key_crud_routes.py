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


async def test_create_api_key_returns_full_secret_once(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    uid = await seed_user(admin_engine, tid, role="admin")
    token = make_access_token(uid, uuid.UUID(tid), role="admin")
    app = create_app(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        create = await client.post(
            "/dashboard/api/tenant/api-keys",
            headers=auth_headers(token),
            json={"name": "CI", "scope": "read"},
        )
        assert create.status_code == 201
        body = create.json()
        secret = body["secret"]
        assert secret.startswith(body["api_key"]["prefix"])
        key_id = body["api_key"]["id"]
        listed = await client.get("/dashboard/api/tenant/api-keys", headers=auth_headers(token))
    assert listed.status_code == 200
    match = next(k for k in listed.json()["api_keys"] if k["id"] == key_id)
    assert "secret" not in match
    assert match["prefix"] == body["api_key"]["prefix"]


async def test_delete_api_key(admin_engine: AsyncEngine, clean_tables: None) -> None:
    tid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    uid = await seed_user(admin_engine, tid, role="admin")
    token = make_access_token(uid, uuid.UUID(tid), role="admin")
    app = create_app(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        create = await client.post(
            "/dashboard/api/tenant/api-keys",
            headers=auth_headers(token),
            json={"name": "temp", "scope": "write"},
        )
        key_id = create.json()["api_key"]["id"]
        deleted = await client.delete(
            f"/dashboard/api/tenant/api-keys/{key_id}", headers=auth_headers(token)
        )
    assert deleted.status_code == 204


async def test_api_key_crud_denies_mod(admin_engine: AsyncEngine, clean_tables: None) -> None:
    tid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    uid = await seed_user(admin_engine, tid, role="mod")
    token = make_access_token(uid, uuid.UUID(tid), role="mod")
    app = create_app(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.get("/dashboard/api/tenant/api-keys", headers=auth_headers(token))
    assert resp.status_code == 403
