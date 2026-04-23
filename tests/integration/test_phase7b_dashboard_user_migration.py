# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def test_dashboard_user_table_exists(admin_engine: AsyncEngine) -> None:
    async with admin_engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT column_name, data_type, is_nullable "
                "FROM information_schema.columns WHERE table_name='dashboard_user' "
                "ORDER BY ordinal_position"
            )
        )
        cols = {row.column_name: (row.data_type, row.is_nullable) for row in result}
    assert cols["id"][0] == "uuid"
    assert cols["tenant_id"][0] == "uuid"
    assert cols["email"][0].startswith("character")
    assert cols["password_hash"][0].startswith("character")
    assert cols["role"][0].startswith("character")
    assert cols["display_name"][0].startswith("character")
    assert cols["last_login_at"][1] == "YES"


async def test_dashboard_user_has_rls_enabled(admin_engine: AsyncEngine) -> None:
    async with admin_engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT relrowsecurity, relforcerowsecurity FROM pg_class "
                "WHERE relname='dashboard_user'"
            )
        )
        row = result.one()
    assert row.relrowsecurity is True
    assert row.relforcerowsecurity is True


async def test_dashboard_user_role_check(admin_engine: AsyncEngine) -> None:
    async with admin_engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT conname FROM pg_constraint "
                "WHERE conrelid='dashboard_user'::regclass AND contype='c'"
            )
        )
        names = {r.conname for r in result}
    assert "ck_dashboard_user_role_valid" in names


async def test_dashboard_user_unique_tenant_email(admin_engine: AsyncEngine) -> None:
    async with admin_engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT conname FROM pg_constraint "
                "WHERE conrelid='dashboard_user'::regclass AND contype='u'"
            )
        )
        names = {r.conname for r in result}
    assert "uq_dashboard_user_tenant_id_email" in names
