# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import UUID

import pytest
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from shared.db import Actor, Tenant, tenant_session

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def _seed_two_tenants_with_actors(
    admin_engine: AsyncEngine,
) -> tuple[UUID, UUID, UUID, UUID]:
    factory = async_sessionmaker(bind=admin_engine, expire_on_commit=False, autoflush=False)
    async with factory() as s, s.begin():
        t1 = Tenant(name="alpha", tier="free")
        t2 = Tenant(name="beta", tier="free")
        s.add_all([t1, t2])
        await s.flush()
        a1 = Actor(tenant_id=t1.id, external_id_hash="a" * 64, claimed_age_band="unknown")
        a2 = Actor(tenant_id=t2.id, external_id_hash="b" * 64, claimed_age_band="unknown")
        s.add_all([a1, a2])
        await s.flush()
        return t1.id, t2.id, a1.id, a2.id


async def test_tenant_session_sees_only_its_own_rows(
    clean_tables: None, admin_engine: AsyncEngine
) -> None:
    t1_id, t2_id, a1_id, a2_id = await _seed_two_tenants_with_actors(admin_engine)

    async with tenant_session(t1_id) as s:
        result = await s.execute(text("SELECT id FROM actor"))
        assert {row[0] for row in result} == {a1_id}

    async with tenant_session(t2_id) as s:
        result = await s.execute(text("SELECT id FROM actor"))
        assert {row[0] for row in result} == {a2_id}


async def test_session_without_tenant_id_sees_nothing(
    clean_tables: None, admin_engine: AsyncEngine
) -> None:
    await _seed_two_tenants_with_actors(admin_engine)

    from sqlalchemy.ext.asyncio import create_async_engine

    from shared.config import get_settings

    app_engine = create_async_engine(get_settings().postgres_dsn, echo=False)
    try:
        async with app_engine.connect() as conn:
            assert (await conn.execute(text("SELECT count(*) FROM actor"))).scalar() == 0
            assert (await conn.execute(text("SELECT count(*) FROM tenant"))).scalar() == 0
    finally:
        await app_engine.dispose()


async def _insert_actor_for_other_tenant(owner_tenant: UUID, target_tenant: UUID) -> None:
    async with tenant_session(owner_tenant) as s:
        s.add(
            Actor(
                tenant_id=target_tenant,
                external_id_hash="c" * 64,
                claimed_age_band="unknown",
            )
        )
        await s.flush()


async def test_insert_with_wrong_tenant_id_is_blocked(
    clean_tables: None, admin_engine: AsyncEngine
) -> None:
    t1_id, t2_id, _a1, _a2 = await _seed_two_tenants_with_actors(admin_engine)

    with pytest.raises(ProgrammingError):
        await _insert_actor_for_other_tenant(t1_id, t2_id)


async def test_tenant_row_visible_only_to_self(
    clean_tables: None, admin_engine: AsyncEngine
) -> None:
    t1_id, _t2, _a1, _a2 = await _seed_two_tenants_with_actors(admin_engine)

    async with tenant_session(t1_id) as s:
        rows = (await s.execute(text("SELECT id FROM tenant"))).all()
        assert [r[0] for r in rows] == [t1_id]
