# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine

from services.dashboard_bff.app.main import create_app
from shared.audit.chain import append_entry
from shared.db.session import tenant_session
from tests.integration._phase7b_helpers import (
    auth_headers,
    fast_settings,
    make_access_token,
    seed_tenant,
    seed_user,
)

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def _add_audit(tenant_id: str, event_type: str) -> None:
    async with tenant_session(uuid.UUID(tenant_id)) as session:
        await append_entry(
            session,
            tenant_id=uuid.UUID(tenant_id),
            event_type=event_type,
            timestamp=datetime.now(UTC),
            details={"note": "test"},
        )


async def test_audit_log_returns_entries_for_auditor(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    await _add_audit(tid, "event.scored")
    await _add_audit(tid, "score.changed")
    uid = await seed_user(admin_engine, tid, role="auditor")
    token = make_access_token(uid, uuid.UUID(tid), role="auditor")
    app = create_app(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.get("/dashboard/api/audit-log?limit=10", headers=auth_headers(token))
    assert resp.status_code == 200
    assert len(resp.json()["entries"]) == 2


async def test_audit_log_filters_by_event_type(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    await _add_audit(tid, "event.scored")
    await _add_audit(tid, "score.changed")
    uid = await seed_user(admin_engine, tid, role="admin")
    token = make_access_token(uid, uuid.UUID(tid), role="admin")
    app = create_app(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.get(
            "/dashboard/api/audit-log?event_type=score.changed",
            headers=auth_headers(token),
        )
    assert resp.status_code == 200
    entries = resp.json()["entries"]
    assert len(entries) == 1
    assert entries[0]["event_type"] == "score.changed"


async def test_audit_log_denies_mod(admin_engine: AsyncEngine, clean_tables: None) -> None:
    tid = str(uuid.uuid4())
    await seed_tenant(admin_engine, tid)
    uid = await seed_user(admin_engine, tid, role="mod")
    token = make_access_token(uid, uuid.UUID(tid), role="mod")
    app = create_app(fast_settings())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.get("/dashboard/api/audit-log", headers=auth_headers(token))
    assert resp.status_code == 403
