# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def test_reasoning_table_exists(admin_engine: AsyncEngine) -> None:
    async with admin_engine.begin() as conn:
        rows = (
            await conn.execute(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = 'reasoning' ORDER BY ordinal_position"
                )
            )
        ).fetchall()
    names = [r[0] for r in rows]
    assert "id" in names
    assert "tenant_id" in names
    assert "actor_id" in names
    assert "event_id" in names
    assert "reasoning_json" in names
    assert "created_at" in names


async def test_reasoning_rls_enabled(admin_engine: AsyncEngine) -> None:
    async with admin_engine.begin() as conn:
        row = (
            await conn.execute(
                text(
                    "SELECT relrowsecurity, relforcerowsecurity FROM pg_class "
                    "WHERE relname = 'reasoning'"
                )
            )
        ).one()
    assert row[0] is True
    assert row[1] is True
