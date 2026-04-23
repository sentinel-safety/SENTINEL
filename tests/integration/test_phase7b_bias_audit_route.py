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


async def test_bias_audit_by_age_band(admin_engine: AsyncEngine, clean_tables: None) -> None:
    tid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    a1 = str(uuid.uuid4())
    a2 = str(uuid.uuid4())
    a3 = str(uuid.uuid4())
    await seed_actor(admin_engine, tid, a1, age_band="13_15")
    await seed_actor(admin_engine, tid, a2, age_band="13_15")
    await seed_actor(admin_engine, tid, a3, age_band="18_plus")
    await seed_suspicion_profile(admin_engine, tid, a1, tier=3, score=60)
    await seed_suspicion_profile(admin_engine, tid, a2, tier=0, score=5)
    await seed_suspicion_profile(admin_engine, tid, a3, tier=0, score=5)
    uid = await seed_user(admin_engine, tid, role="admin")
    token = make_access_token(uid, uuid.UUID(tid), role="admin")
    app = create_app(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.get(
            "/dashboard/api/bias-audit?group_by=age_band", headers=auth_headers(token)
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["group_by"] == "age_band"
    by_group = {r["group"]: r for r in body["rows"]}
    assert by_group["13_15"]["total_actors"] == 2
    assert by_group["13_15"]["total_flagged"] == 1
    assert abs(by_group["13_15"]["flag_rate"] - 0.5) < 1e-6
    assert by_group["18_plus"]["total_flagged"] == 0


async def test_bias_audit_rejects_unknown_group(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    uid = await seed_user(admin_engine, tid, role="admin")
    token = make_access_token(uid, uuid.UUID(tid), role="admin")
    app = create_app(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.get(
            "/dashboard/api/bias-audit?group_by=ethnicity", headers=auth_headers(token)
        )
    assert resp.status_code == 422 or resp.status_code == 400


async def test_bias_audit_denies_mod(admin_engine: AsyncEngine, clean_tables: None) -> None:
    tid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    uid = await seed_user(admin_engine, tid, role="mod")
    token = make_access_token(uid, uuid.UUID(tid), role="mod")
    app = create_app(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.get(
            "/dashboard/api/bias-audit?group_by=age_band", headers=auth_headers(token)
        )
    assert resp.status_code == 403
