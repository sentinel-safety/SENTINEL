# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def test_sentinel_graph_exists(admin_engine: AsyncEngine) -> None:
    async with admin_engine.begin() as conn:
        row = await conn.execute(
            text("SELECT count(*) FROM ag_catalog.ag_graph WHERE name = 'sentinel_graph'")
        )
        assert row.scalar_one() == 1


async def test_actor_label_exists(admin_engine: AsyncEngine) -> None:
    async with admin_engine.begin() as conn:
        row = await conn.execute(
            text(
                "SELECT count(*) FROM ag_catalog.ag_label "
                "WHERE graph = (SELECT graphid FROM ag_catalog.ag_graph WHERE name = 'sentinel_graph') "
                "AND name = 'Actor'"
            )
        )
        assert row.scalar_one() == 1


async def test_interacted_with_label_exists(admin_engine: AsyncEngine) -> None:
    async with admin_engine.begin() as conn:
        row = await conn.execute(
            text(
                "SELECT count(*) FROM ag_catalog.ag_label "
                "WHERE graph = (SELECT graphid FROM ag_catalog.ag_graph WHERE name = 'sentinel_graph') "
                "AND name = 'INTERACTED_WITH'"
            )
        )
        assert row.scalar_one() == 1


async def test_app_role_has_usage_on_ag_catalog(admin_engine: AsyncEngine) -> None:
    async with admin_engine.begin() as conn:
        row = await conn.execute(
            text("SELECT has_schema_privilege('sentinel_app', 'ag_catalog', 'USAGE')")
        )
        assert row.scalar_one() is True
