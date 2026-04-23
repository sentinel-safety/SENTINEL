# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def test_tenant_action_config_table_exists(admin_engine: AsyncEngine) -> None:
    async with admin_engine.begin() as conn:
        row = await conn.execute(
            text(
                "SELECT count(*) FROM information_schema.tables "
                "WHERE table_name = 'tenant_action_config'"
            )
        )
        assert row.scalar_one() == 1


async def test_tenant_action_config_has_rls(admin_engine: AsyncEngine) -> None:
    async with admin_engine.begin() as conn:
        row = await conn.execute(
            text("SELECT relrowsecurity FROM pg_class WHERE relname = 'tenant_action_config'")
        )
        assert row.scalar_one() is True


async def test_tenant_action_config_policy_present(admin_engine: AsyncEngine) -> None:
    async with admin_engine.begin() as conn:
        row = await conn.execute(
            text(
                "SELECT count(*) FROM pg_policies "
                "WHERE tablename = 'tenant_action_config' AND policyname = 'tenant_isolation'"
            )
        )
        assert row.scalar_one() == 1
