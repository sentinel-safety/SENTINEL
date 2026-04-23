# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from services.dashboard_bff.app.user_repository import (
    create_user,
    get_by_email,
    update_last_login,
)
from shared.db.session import tenant_session

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def _seed_tenant(admin_engine: AsyncEngine, tid: str) -> None:
    async with admin_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, "
                "data_retention_days, feature_flags) "
                "VALUES (:t, 'acme', 'free', '{}', 30, '{}'::jsonb)"
            ),
            {"t": tid},
        )


async def test_create_and_lookup_by_email(admin_engine: AsyncEngine, clean_tables: None) -> None:
    tid = str(uuid.uuid4())
    await _seed_tenant(admin_engine, tid)
    async with tenant_session(uuid.UUID(tid)) as session:
        created = await create_user(
            session,
            tenant_id=uuid.UUID(tid),
            email="alice@example.com",
            password_hash="$argon2id$fake",
            role="admin",
            display_name="Alice",
        )
    async with tenant_session(uuid.UUID(tid)) as session:
        found = await get_by_email(session, tenant_id=uuid.UUID(tid), email="alice@example.com")
    assert found is not None
    assert found.id == created.id
    assert found.role == "admin"


async def test_get_by_email_returns_none_for_missing(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tid = str(uuid.uuid4())
    await _seed_tenant(admin_engine, tid)
    async with tenant_session(uuid.UUID(tid)) as session:
        assert await get_by_email(session, tenant_id=uuid.UUID(tid), email="nobody@x.com") is None


async def test_update_last_login_sets_timestamp(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tid = str(uuid.uuid4())
    await _seed_tenant(admin_engine, tid)
    async with tenant_session(uuid.UUID(tid)) as session:
        user = await create_user(
            session,
            tenant_id=uuid.UUID(tid),
            email="bob@example.com",
            password_hash="$argon2id$fake",
            role="mod",
            display_name="Bob",
        )
    now = datetime.now(UTC)
    async with tenant_session(uuid.UUID(tid)) as session:
        await update_last_login(session, user_id=user.id, now=now)
    async with tenant_session(uuid.UUID(tid)) as session:
        fresh = await get_by_email(session, tenant_id=uuid.UUID(tid), email="bob@example.com")
    assert fresh is not None
    assert fresh.last_login_at is not None


async def test_tenant_isolation_on_lookup(admin_engine: AsyncEngine, clean_tables: None) -> None:
    ta = str(uuid.uuid4())
    tb = str(uuid.uuid4())
    await _seed_tenant(admin_engine, ta)
    await _seed_tenant(admin_engine, tb)
    async with tenant_session(uuid.UUID(ta)) as session:
        await create_user(
            session,
            tenant_id=uuid.UUID(ta),
            email="shared@x.com",
            password_hash="$argon2id$fake",
            role="admin",
            display_name="A",
        )
    async with tenant_session(uuid.UUID(tb)) as session:
        found = await get_by_email(session, tenant_id=uuid.UUID(ta), email="shared@x.com")
    assert found is None
