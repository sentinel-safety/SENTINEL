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
    seed_actor,
    seed_suspicion_profile,
    seed_tenant,
    seed_user,
)

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def test_alerts_filters_by_tier(admin_engine: AsyncEngine, clean_tables: None) -> None:
    tid = str(uuid.uuid4())
    a_hi = str(uuid.uuid4())
    a_lo = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    await seed_actor(admin_engine, tid, a_hi)
    await seed_actor(admin_engine, tid, a_lo)
    await seed_suspicion_profile(admin_engine, tid, a_hi, tier=3, score=70)
    await seed_suspicion_profile(admin_engine, tid, a_lo, tier=0, score=5)
    uid = await seed_user(admin_engine, tid, role="mod")
    token = make_access_token(uid, uuid.UUID(tid), role="mod")
    app = create_app(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.get(
            "/dashboard/api/alerts?min_tier=2&limit=10", headers=auth_headers(token)
        )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["alerts"]) == 1
    assert body["alerts"][0]["actor_id"] == a_hi


async def test_alerts_denied_for_viewer(admin_engine: AsyncEngine, clean_tables: None) -> None:
    tid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    uid = await seed_user(admin_engine, tid, role="viewer")
    token = make_access_token(uid, uuid.UUID(tid), role="viewer")
    app = create_app(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.get("/dashboard/api/alerts", headers=auth_headers(token))
    assert resp.status_code == 403


async def test_alerts_requires_bearer(admin_engine: AsyncEngine, clean_tables: None) -> None:
    app = create_app(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.get("/dashboard/api/alerts")
    assert resp.status_code == 401


async def test_alerts_tenant_isolated(admin_engine: AsyncEngine, clean_tables: None) -> None:
    ta = str(uuid.uuid4())
    tb = str(uuid.uuid4())
    actor_in_b = str(uuid.uuid4())
    await seed_tenant(admin_engine, ta)
    await seed_tenant(admin_engine, tb)
    await seed_actor(admin_engine, tb, actor_in_b)
    await seed_suspicion_profile(admin_engine, tb, actor_in_b, tier=4, score=80)
    uid = await seed_user(admin_engine, ta, role="mod")
    token = make_access_token(uid, uuid.UUID(ta), role="mod")
    app = create_app(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.get("/dashboard/api/alerts?min_tier=2", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["alerts"] == []
