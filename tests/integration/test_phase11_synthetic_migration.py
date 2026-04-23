# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = pytest.mark.integration


@pytest.fixture
def _tables(clean_tables: None) -> None:
    pass


async def _table_exists(engine: AsyncEngine, name: str) -> bool:
    async with engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name = :name"
            ),
            {"name": name},
        )
        return result.scalar() is not None


async def _rls_enabled(engine: AsyncEngine, name: str) -> bool:
    async with engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT rowsecurity FROM pg_tables "
                "WHERE schemaname = 'public' AND tablename = :name"
            ),
            {"name": name},
        )
        return bool(result.scalar())


@pytest.mark.usefixtures("_tables")
async def test_synthetic_run_table_exists(admin_engine: AsyncEngine) -> None:
    assert await _table_exists(admin_engine, "synthetic_run")


@pytest.mark.usefixtures("_tables")
async def test_synthetic_conversation_table_exists(admin_engine: AsyncEngine) -> None:
    assert await _table_exists(admin_engine, "synthetic_conversation")


@pytest.mark.usefixtures("_tables")
async def test_synthetic_run_rls_enabled(admin_engine: AsyncEngine) -> None:
    assert await _rls_enabled(admin_engine, "synthetic_run")


@pytest.mark.usefixtures("_tables")
async def test_synthetic_conversation_rls_enabled(admin_engine: AsyncEngine) -> None:
    assert await _rls_enabled(admin_engine, "synthetic_conversation")
