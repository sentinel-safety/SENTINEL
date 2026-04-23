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


async def test_anonymous_post_bug_report_succeeds(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    app = create_app(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.post(
            "/dashboard/api/security/bug-reports",
            json={
                "reporter_email": "researcher@example.com",
                "summary": "XSS in dashboard search",
                "details": "Input is reflected without escaping.",
                "severity": "high",
            },
            headers={"X-Sentinel-Tenant-Id": tid},
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "new"
    assert body["severity"] == "high"
    assert body["reporter_email"] == "researcher@example.com"


async def test_admin_can_list_bug_reports(admin_engine: AsyncEngine, clean_tables: None) -> None:
    tid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    user_id = await seed_user(admin_engine, tid, role="admin")
    token = make_access_token(user_id, uuid.UUID(tid), role="admin")
    app = create_app(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        await client.post(
            "/dashboard/api/security/bug-reports",
            json={
                "reporter_email": "r@example.com",
                "summary": "CSRF token missing",
                "details": "Found on the login form.",
                "severity": "medium",
            },
            headers={"X-Sentinel-Tenant-Id": tid},
        )
        resp = await client.get(
            "/dashboard/api/security/bug-reports",
            headers=auth_headers(token),
        )
    assert resp.status_code == 200
    assert len(resp.json()["reports"]) == 1


async def test_non_admin_get_bug_reports_is_403(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    user_id = await seed_user(admin_engine, tid, role="mod")
    token = make_access_token(user_id, uuid.UUID(tid), role="mod")
    app = create_app(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.get(
            "/dashboard/api/security/bug-reports",
            headers=auth_headers(token),
        )
    assert resp.status_code == 403


async def test_cross_tenant_bug_report_not_visible(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tid_a = str(uuid.uuid4())
    tid_b = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid_a)
    await seed_tenant(admin_engine, tid_b)
    user_b_id = await seed_user(admin_engine, tid_b, role="admin")
    token_b = make_access_token(user_b_id, uuid.UUID(tid_b), role="admin")
    app = create_app(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        await client.post(
            "/dashboard/api/security/bug-reports",
            json={
                "reporter_email": "a@example.com",
                "summary": "SQL injection in actors endpoint",
                "details": "Parameter not sanitised.",
                "severity": "critical",
            },
            headers={"X-Sentinel-Tenant-Id": tid_a},
        )
        resp = await client.get(
            "/dashboard/api/security/bug-reports",
            headers=auth_headers(token_b),
        )
    assert resp.status_code == 200
    assert resp.json()["reports"] == []


async def test_admin_patch_updates_status(admin_engine: AsyncEngine, clean_tables: None) -> None:
    tid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    user_id = await seed_user(admin_engine, tid, role="admin")
    token = make_access_token(user_id, uuid.UUID(tid), role="admin")
    app = create_app(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        post_resp = await client.post(
            "/dashboard/api/security/bug-reports",
            json={
                "reporter_email": "r@example.com",
                "summary": "Rate limit bypass",
                "details": "No throttle on password reset.",
                "severity": "low",
            },
            headers={"X-Sentinel-Tenant-Id": tid},
        )
        assert post_resp.status_code == 201
        report_id = post_resp.json()["id"]
        patch_resp = await client.patch(
            f"/dashboard/api/security/bug-reports/{report_id}",
            json={"status": "triaging"},
            headers=auth_headers(token),
        )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "triaging"
