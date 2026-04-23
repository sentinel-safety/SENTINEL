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
from shared.schemas.enums import ActionMode

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def _seed_tenant(admin_engine: AsyncEngine) -> UUID:
    tenant_id = uuid4()
    async with admin_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, "
                "data_retention_days, feature_flags) VALUES (:t, 'acme', 'free', '{}', 30, '{}'::jsonb)"
            ),
            {"t": str(tenant_id)},
        )
    return tenant_id


async def test_first_load_seeds_default_advisory_config(
    admin_engine: AsyncEngine,
    clean_tables: None,
) -> None:
    tid = await _seed_tenant(admin_engine)
    async with tenant_session(tid) as session:
        cfg = await load_or_create_config(session, tenant_id=tid)
    assert cfg.mode == ActionMode.ADVISORY
    assert len(cfg.webhook_secret) >= 32


async def test_second_load_returns_same_secret(
    admin_engine: AsyncEngine,
    clean_tables: None,
) -> None:
    tid = await _seed_tenant(admin_engine)
    async with tenant_session(tid) as session:
        first = await load_or_create_config(session, tenant_id=tid)
    async with tenant_session(tid) as session:
        second = await load_or_create_config(session, tenant_id=tid)
    assert first.webhook_secret == second.webhook_secret
