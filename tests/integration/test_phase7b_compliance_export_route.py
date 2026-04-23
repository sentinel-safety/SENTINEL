# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import io
import uuid
import zipfile

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
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


async def test_export_zip_contains_audit_log(admin_engine: AsyncEngine, clean_tables: None) -> None:
    tid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    uid = await seed_user(admin_engine, tid, role="admin")
    token = make_access_token(uid, uuid.UUID(tid), role="admin")
    app = create_app(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.post(
            "/dashboard/api/compliance/export",
            headers=auth_headers(token),
            json={
                "from": "2026-01-01T00:00:00+00:00",
                "to": "2026-12-31T23:59:59+00:00",
                "categories": ["audit_log"],
                "format": "zip",
            },
        )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"
    assert "attachment" in resp.headers.get("content-disposition", "")
    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
        names = set(z.namelist())
    assert "audit_log.csv" in names
    assert "audit_log.jsonl" in names


async def test_export_writes_audit_entry(admin_engine: AsyncEngine, clean_tables: None) -> None:
    tid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    uid = await seed_user(admin_engine, tid, role="auditor")
    token = make_access_token(uid, uuid.UUID(tid), role="auditor")
    app = create_app(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.post(
            "/dashboard/api/compliance/export",
            headers=auth_headers(token),
            json={
                "from": "2026-01-01T00:00:00+00:00",
                "to": "2026-12-31T23:59:59+00:00",
                "categories": ["audit_log"],
                "format": "zip",
            },
        )
    assert resp.status_code == 200
    async with admin_engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT count(*) AS c FROM audit_log_entry "
                "WHERE tenant_id=:t AND event_type='compliance.exported'"
            ),
            {"t": tid},
        )
    assert result.scalar() == 1


async def test_export_denies_mod(admin_engine: AsyncEngine, clean_tables: None) -> None:
    tid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    uid = await seed_user(admin_engine, tid, role="mod")
    token = make_access_token(uid, uuid.UUID(tid), role="mod")
    app = create_app(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.post(
            "/dashboard/api/compliance/export",
            headers=auth_headers(token),
            json={
                "from": "2026-01-01T00:00:00+00:00",
                "to": "2026-12-31T23:59:59+00:00",
                "categories": ["audit_log"],
                "format": "zip",
            },
        )
    assert resp.status_code == 403
