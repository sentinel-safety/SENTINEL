# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from services.response.app.config_repository import load_or_create_config
from shared.db.session import tenant_session

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def _seed_two_tenants(admin_engine: AsyncEngine) -> tuple[UUID, UUID]:
    a = uuid4()
    b = uuid4()
    async with admin_engine.begin() as conn:
        for t in (a, b):
            await conn.execute(
                text(
                    "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, "
                    "data_retention_days, feature_flags) VALUES (:t, 't', 'free', '{}', 30, '{}'::jsonb)"
                ),
                {"t": str(t)},
            )
    return a, b


async def test_tenant_a_cannot_read_tenant_b_config(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    a, b = await _seed_two_tenants(admin_engine)
    async with tenant_session(a) as session:
        await load_or_create_config(session, tenant_id=a)
    async with tenant_session(b) as session:
        await load_or_create_config(session, tenant_id=b)
    async with tenant_session(a) as session:
        row = await session.execute(text("SELECT count(*) FROM tenant_action_config"))
        assert row.scalar_one() == 1
